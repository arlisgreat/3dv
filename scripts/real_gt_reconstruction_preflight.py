#!/usr/bin/env python3
"""Check whether a gate-passed real-GT case is ready for reconstruction training.

This is the G22 guardrail after G21. It deliberately checks model/data adapter
compatibility before any GPU run. A real captured benchmark pass is not enough
if the current training adapter cannot preserve the dataset's camera model,
depth/geometry priors, and evaluation contract.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


DATE = "2026-05-20"
PASS_VERDICT = "PASS_REAL_GT_RECONSTRUCTION_PREFLIGHT"
BLOCKED_VERDICT = "BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def camera_entries(cameras: Any) -> list[dict[str, Any]]:
    if isinstance(cameras, dict):
        entries = cameras.get("cameras", cameras.get("views", []))
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
    if isinstance(cameras, list):
        return [entry for entry in cameras if isinstance(entry, dict)]
    return []


def case_metadata(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "real_gt_case.json"
    if path.is_file():
        data = load_json(path)
        return data if isinstance(data, dict) else {}
    return {}


def effective_intrinsics(entry: dict[str, Any], width: int, height: int, image_size: int) -> dict[str, float]:
    k = entry.get("K", entry.get("intrinsics"))
    if not isinstance(k, list) or len(k) < 3:
        raise ValueError(f"Missing K/intrinsics for camera {entry.get('view_id')}")
    scale = min(image_size / width, image_size / height)
    resized_w = width * scale
    resized_h = height * scale
    x_offset = (image_size - resized_w) / 2.0
    y_offset = (image_size - resized_h) / 2.0
    return {
        "view_id": str(entry.get("view_id", "")),
        "fx": float(k[0][0]) * scale,
        "fy": float(k[1][1]) * scale,
        "cx": float(k[0][2]) * scale + x_offset,
        "cy": float(k[1][2]) * scale + y_offset,
        "scale": scale,
        "x_offset": x_offset,
        "y_offset": y_offset,
    }


def range_stats(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "range": max(values) - min(values),
    }


def analyze_intrinsics(rows: list[dict[str, str]], entries: list[dict[str, Any]], image_size: int) -> dict[str, Any]:
    rows_by_view = {row["camera"]: row for row in rows if row.get("camera")}
    effective: list[dict[str, float]] = []
    for entry in entries:
        view_id = str(entry.get("view_id", ""))
        row = rows_by_view.get(view_id)
        if not row:
            continue
        effective.append(effective_intrinsics(entry, int(row["width"]), int(row["height"]), image_size))
    return {
        "image_size": image_size,
        "effective_intrinsics": effective,
        "fx": range_stats([item["fx"] for item in effective]),
        "fy": range_stats([item["fy"] for item in effective]),
        "cx": range_stats([item["cx"] for item in effective]),
        "cy": range_stats([item["cy"] for item in effective]),
    }


def markdown_table(checks: dict[str, bool], details: dict[str, str]) -> list[str]:
    lines = ["| Check | Result | Detail |", "| --- | --- | --- |"]
    for key, ok in checks.items():
        lines.append(f"| {key} | {'PASS' if ok else 'BLOCK'} | {details.get(key, '')} |")
    return lines


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    intr = payload["intrinsics_audit"]
    lines = [
        "# G22 Real-GT Reconstruction/Evaluation Preflight",
        "",
        f"Date: {DATE}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "NO_GPU_TRAINING_STARTED",
        "```",
        "",
        "Premise:",
        "",
        "```text",
        "G21 passed a local real-capture benchmark case. G22 may only start",
        "training if the current reconstruction/evaluation adapter preserves the",
        "real camera model, geometry/depth priors, artifact policy, and metrics.",
        "```",
        "",
        "Checks:",
        "",
        *markdown_table(payload["checks"], payload["details"]),
        "",
        "Effective intrinsics after 256px letterbox resize:",
        "",
        "| Component | min | max | range | mean |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| fx | {intr['fx']['min']:.3f} | {intr['fx']['max']:.3f} | {intr['fx']['range']:.3f} | {intr['fx']['mean']:.3f} |",
        f"| fy | {intr['fy']['min']:.3f} | {intr['fy']['max']:.3f} | {intr['fy']['range']:.3f} | {intr['fy']['mean']:.3f} |",
        f"| cx | {intr['cx']['min']:.3f} | {intr['cx']['max']:.3f} | {intr['cx']['range']:.3f} | {intr['cx']['mean']:.3f} |",
        f"| cy | {intr['cy']['min']:.3f} | {intr['cy']['max']:.3f} | {intr['cy']['range']:.3f} | {intr['cy']['mean']:.3f} |",
        "",
        "Closure:",
        "",
        "```text",
        payload["closure"],
        "```",
        "",
        "Required unblock items:",
        "",
        "```text",
        "1. Add a local-only real-GT adapter that preserves per-frame intrinsics/extrinsics or applies a documented recenter/undistort transform.",
        "2. Generate real-camera mesh z-buffer depth/confidence maps from the tracked OBJ; do not use pseudo/synthetic depth priors.",
        "3. Define train/test split and metrics: silhouette IoU, novel-view RGB/LPIPS where held-out views exist, and mesh/point-cloud distance if aligned geometry is exported.",
        "4. Re-run G21/G22 VLM and distribution gates after conversion.",
        "5. Only then select an idle GPU and start the smallest real-GT training run.",
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view"))
    parser.add_argument("--case-id", default="gate_case")
    parser.add_argument("--g21-json", type=Path, default=Path("experiments/metrics/g21_multiface_debug_gate_20260520.json"))
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g22_real_gt_reconstruction_preflight_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g22_real_gt_reconstruction_preflight_20260520.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    case_dir = args.case_root / args.case_id
    rows = read_csv(case_dir / "manifest.csv")
    cameras = load_json(case_dir / "cameras.json")
    metadata = case_metadata(case_dir)
    g21 = load_json(repo / args.g21_json if not args.g21_json.is_absolute() else args.g21_json)
    entries = camera_entries(cameras)
    intrinsics = analyze_intrinsics(rows, entries, args.image_size)
    mask_coverages = [float(row["mask_coverage"]) for row in rows if row.get("mask_coverage")]
    has_depth_columns = all(row.get("depth") or row.get("depth_path") for row in rows)
    has_real_mesh = bool(metadata.get("gt_mesh")) or all(row.get("mesh") for row in rows)
    cx_range = intrinsics["cx"]["range"]
    cy_range = intrinsics["cy"]["range"]
    high_crop_views = [row["camera"] for row in rows if float(row.get("mask_coverage", 0.0)) > 0.75]

    checks = {
        "g21_real_gt_gate_passed": g21.get("verdict") == "PASS_REAL_GT_BENCHMARK",
        "raw_assets_remain_local_only": "3dv_work" in metadata.get("artifact_policy", "") + metadata.get("repo_policy", ""),
        "manifest_cameras_masks_mesh_present": len(rows) == len(entries) and len(rows) >= 6 and has_real_mesh,
        "ri3d_current_adapter_preserves_per_view_intrinsics": cx_range <= 8.0 and cy_range <= 8.0,
        "real_camera_depth_priors_available": has_depth_columns,
        "evaluation_metrics_adapter_available": False,
        "crop_risk_acceptable_for_training_start": not high_crop_views,
    }
    details = {
        "g21_real_gt_gate_passed": str(g21.get("verdict")),
        "raw_assets_remain_local_only": "Raw RGB/OBJ/contact sheet stay under 3dv_work; repo contains metrics/hash/mask-only PNG.",
        "manifest_cameras_masks_mesh_present": f"{len(rows)} rows, {len(entries)} cameras, mesh_present={has_real_mesh}",
        "ri3d_current_adapter_preserves_per_view_intrinsics": (
            f"256px effective principal point ranges: cx={cx_range:.2f}px, cy={cy_range:.2f}px; "
            "current RI3D exports use one global intrinsics block."
        ),
        "real_camera_depth_priors_available": "No real-camera z-buffer depth/conf maps exist in the G21 manifest.",
        "evaluation_metrics_adapter_available": "No committed adapter yet for held-out view metrics or mesh/point-cloud distance on Multiface.",
        "crop_risk_acceptable_for_training_start": (
            "High mask coverage/crop-risk views: " + ", ".join(high_crop_views) if high_crop_views else "No high crop-risk views."
        ),
    }
    failed = [key for key, ok in checks.items() if not ok]
    verdict = PASS_VERDICT if not failed else BLOCKED_VERDICT
    closure = (
        "PASS_REAL_GT_RECONSTRUCTION_PREFLIGHT: adapter and metrics are ready for a minimal GPU run."
        if not failed
        else "BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER: G21 benchmark premise passes, but current RI3D/evaluation plumbing does not yet preserve Multiface real-camera intrinsics/depth/metric assumptions. Do not start GPU training."
    )
    payload = {
        "date": DATE,
        "gate": "G22",
        "case_dir": str(case_dir),
        "verdict": verdict,
        "closure": closure,
        "checks": checks,
        "failed_checks": failed,
        "details": details,
        "intrinsics_audit": intrinsics,
        "mask_coverage": {
            "min": min(mask_coverages),
            "max": max(mask_coverages),
            "mean": mean(mask_coverages),
            "high_crop_risk_views": high_crop_views,
        },
        "no_gpu_training_started": True,
        "next_allowed_action": "Implement local-only real-camera adapter and metric preflight, then rerun G21/G22 before selecting an idle GPU.",
    }
    write_json(repo / args.output_json, payload)
    write_markdown(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)


if __name__ == "__main__":
    main()
