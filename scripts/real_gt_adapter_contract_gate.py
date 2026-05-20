#!/usr/bin/env python3
"""CPU-only contract gate for a local real-GT RI3D adapter.

This G24 gate validates file contracts, shapes, local-only artifact policy, and
metric definitions before any GPU training is allowed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from PIL import Image


DATE = "2026-05-20"
PASS_VERDICT = "PASS_REAL_GT_ADAPTER_CONTRACT"
BLOCKED_VERDICT = "BLOCKED_REAL_GT_ADAPTER_CONTRACT"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finite_stats(arr: np.ndarray) -> dict[str, float]:
    vals = arr[np.isfinite(arr)]
    return {"min": float(vals.min()), "max": float(vals.max()), "mean": float(vals.mean())}


def shape_ok(path: Path, shape: tuple[int, int]) -> bool:
    arr = np.load(path)
    return arr.shape == shape and np.isfinite(arr).any()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102"))
    parser.add_argument("--g23-json", type=Path, default=Path("experiments/metrics/g23_multiface_real_camera_adapter_20260520.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g24_real_gt_adapter_contract_gate_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g24_real_gt_adapter_contract_gate_20260520.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    g23 = load_json(repo / args.g23_json if not args.g23_json.is_absolute() else args.g23_json)
    transforms = load_json(args.adapter_root / "transforms.json")
    split = load_json(args.adapter_root / "train_test_split_6.json")
    source_metadata = load_json(args.adapter_root / "source_metadata.json")
    frames = transforms["frames"]
    target_size = int(transforms["w"])
    expected_shape = (target_size, target_size)
    train_ids = split["train_ids"]
    test_ids = split["test_ids"]

    frame_checks: list[dict[str, Any]] = []
    train_coverages: list[float] = []
    for idx, frame in enumerate(frames):
        image_path = args.adapter_root / frame["file_path"]
        mask_path = args.adapter_root / frame["mask_path"]
        stem = image_path.stem
        depth_rel = image_path.parent / "depth_rel" / f"inpv2{stem}_{len(train_ids)}.npy"
        depth_dust3r = image_path.parent / "depth_rel" / f"inp_dust3r{stem}_{len(train_ids)}.npy"
        conf_path = args.adapter_root / "confidence" / f"{stem}_confidence.npy"
        depth_raw = args.adapter_root / "depth_raw_mm" / f"{stem}_zbuffer_mm.npy"
        mask = Image.open(mask_path).convert("L")
        coverage = float((np.asarray(mask) > 127).mean())
        if idx in train_ids:
            train_coverages.append(coverage)
        image_dims = tuple(int(v) for v in Image.open(image_path).size)
        frame_checks.append(
            {
                "idx": idx,
                "view_id": frame.get("view_id"),
                "role": frame.get("supervision_role"),
                "image_exists": bool(image_path.is_file()),
                "mask_exists": bool(mask_path.is_file()),
                "depth_rel_exists": bool(depth_rel.is_file()),
                "depth_dust3r_exists": bool(depth_dust3r.is_file()),
                "confidence_exists": bool(conf_path.is_file()),
                "depth_raw_exists": bool(depth_raw.is_file()),
                "image_size": image_dims,
                "mask_coverage": coverage,
                "depth_rel_shape_ok": bool(depth_rel.is_file() and shape_ok(depth_rel, expected_shape)),
                "confidence_shape_ok": bool(conf_path.is_file() and shape_ok(conf_path, expected_shape)),
                "depth_raw_stats": finite_stats(np.load(depth_raw)) if depth_raw.is_file() else {},
            }
        )

    checks = {
        "g23_adapter_passed": g23.get("verdict") == "PASS_REAL_CAMERA_ADAPTER_PREFLIGHT",
        "adapter_root_local_only": str(args.adapter_root).startswith("/data1/workspace/airulan/3dv_work/"),
        "transforms_global_centered_intrinsics": bool(transforms.get("fl_x") == transforms.get("fl_y") and transforms.get("cx") == target_size / 2 and transforms.get("cy") == target_size / 2),
        "train_test_split_valid": bool(len(train_ids) >= 6 and len(test_ids) >= 2 and not set(train_ids).intersection(test_ids)),
        "all_files_exist_and_shapes_ok": bool(all(
            item["image_exists"]
            and item["mask_exists"]
            and item["depth_rel_exists"]
            and item["depth_dust3r_exists"]
            and item["confidence_exists"]
            and item["depth_raw_exists"]
            and item["depth_rel_shape_ok"]
            and item["confidence_shape_ok"]
            for item in frame_checks
        )),
        "train_masks_not_extreme": bool(train_coverages and min(train_coverages) > 0.12 and max(train_coverages) < 0.35),
        "heldout_metrics_defined": bool(len(test_ids) >= 2 and all(frames[idx].get("supervision_role") == "heldout_eval" for idx in test_ids)),
        "raw_asset_policy_recorded": bool("local-only" in source_metadata.get("artifact_policy", "")),
    }
    failed = [key for key, ok in checks.items() if not ok]
    verdict = PASS_VERDICT if not failed else BLOCKED_VERDICT
    closure = (
        "PASS_REAL_GT_ADAPTER_CONTRACT: file contracts, local-only policy, train/heldout split, and depth/conf arrays pass CPU gate. GPU is still not started; next step must select an idle GPU and run the smallest smoke only."
        if not failed
        else "BLOCKED_REAL_GT_ADAPTER_CONTRACT: adapter file contract failed; do not start GPU."
    )
    payload = {
        "date": DATE,
        "gate": "G24",
        "verdict": verdict,
        "closure": closure,
        "adapter_root": str(args.adapter_root),
        "checks": checks,
        "failed_checks": failed,
        "train_ids": train_ids,
        "test_ids": test_ids,
        "frame_checks": frame_checks,
        "train_mask_coverage": {
            "min": min(train_coverages),
            "max": max(train_coverages),
            "mean": mean(train_coverages),
        },
        "metrics_contract": {
            "train": "6 normalized real-camera views with RGB/mask/depth/conf arrays.",
            "heldout": "3 held-out normalized real-camera views for silhouette IoU and later RGB/LPIPS after rendering.",
            "mesh": "tracked OBJ remains local; depth_raw z-buffer arrays are available for geometry sanity.",
        },
        "no_gpu_training_started": True,
        "next_allowed_action": "If PASS, choose idle GPU and run a minimal RI3D init-only smoke on the adapter; otherwise fix adapter.",
    }
    write_json(repo / args.output_json, payload)
    lines = [
        "# G24 Real-GT Adapter Contract Gate",
        "",
        f"Date: {DATE}",
        "",
        "Verdict:",
        "",
        "```text",
        verdict,
        "NO_GPU_TRAINING_STARTED",
        "```",
        "",
        "Checks:",
        "",
        "| Check | Result |",
        "| --- | --- |",
        *[f"| {key} | {'PASS' if ok else 'BLOCK'} |" for key, ok in checks.items()],
        "",
        "Train/heldout split:",
        "",
        "```text",
        f"train_ids: {train_ids}",
        f"test_ids: {test_ids}",
        "```",
        "",
        "Train mask coverage:",
        "",
        "```text",
        f"min={min(train_coverages):.4f} max={max(train_coverages):.4f} mean={mean(train_coverages):.4f}",
        "```",
        "",
        "Metrics contract:",
        "",
        "```text",
        "train: 6 normalized real-camera views with RGB/mask/depth/conf arrays",
        "heldout: 3 held-out views for silhouette IoU and later RGB/LPIPS after rendering",
        "mesh: tracked OBJ remains local; z-buffer depth arrays are available for geometry sanity",
        "```",
        "",
        "Closure:",
        "",
        "```text",
        closure,
        "```",
        "",
    ]
    (repo / args.output_md).parent.mkdir(parents=True, exist_ok=True)
    (repo / args.output_md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)


if __name__ == "__main__":
    main()
