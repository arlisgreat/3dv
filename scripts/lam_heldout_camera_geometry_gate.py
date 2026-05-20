#!/usr/bin/env python3
"""Render aligned LAM mesh into Multiface held-out cameras for geometry diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from prepare_multiface_real_camera_adapter import (
    affine_params,
    camera_lookup,
    load_json,
    load_obj,
    project_vertices,
    rasterize_depth,
)


DATE = "2026-05-20"
PASS_VERDICT = "PASS_HELDOUT_CAMERA_RENDER_CONTRACT_DIAGNOSTIC_ONLY_NO_RECONSTRUCTION_QUALITY_CLAIM"
BLOCK_VERDICT = "BLOCKED_HELDOUT_CAMERA_RENDER_CONTRACT_DIAGNOSTIC"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mask_from_depth(depth: np.ndarray) -> np.ndarray:
    return np.isfinite(depth)


def load_mask(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L")) > 127


def depth_stats(pred_depth: np.ndarray, gt_depth: np.ndarray, pred_mask: np.ndarray, gt_mask: np.ndarray) -> dict[str, float]:
    intersection = pred_mask & gt_mask & np.isfinite(pred_depth) & np.isfinite(gt_depth)
    union = pred_mask | gt_mask
    iou = float(intersection.sum() / max(1, int(union.sum())))
    if intersection.any():
        abs_mm = np.abs(pred_depth[intersection] - gt_depth[intersection])
        gt_vals = gt_depth[intersection]
        pred_vals = pred_depth[intersection]
        return {
            "mask_iou": iou,
            "intersection_pixels": int(intersection.sum()),
            "union_pixels": int(union.sum()),
            "pred_coverage": float(pred_mask.mean()),
            "gt_coverage": float(gt_mask.mean()),
            "depth_abs_mean_mm": float(abs_mm.mean()),
            "depth_abs_median_mm": float(np.median(abs_mm)),
            "depth_abs_p95_mm": float(np.percentile(abs_mm, 95)),
            "depth_abs_mean_over_gt_median": float(abs_mm.mean() / max(1e-6, float(np.median(gt_vals)))),
            "pred_depth_median_mm": float(np.median(pred_vals)),
            "gt_depth_median_mm": float(np.median(gt_vals)),
        }
    return {
        "mask_iou": iou,
        "intersection_pixels": 0,
        "union_pixels": int(union.sum()),
        "pred_coverage": float(pred_mask.mean()),
        "gt_coverage": float(gt_mask.mean()),
        "depth_abs_mean_mm": float("inf"),
        "depth_abs_median_mm": float("inf"),
        "depth_abs_p95_mm": float("inf"),
        "depth_abs_mean_over_gt_median": float("inf"),
        "pred_depth_median_mm": float("nan"),
        "gt_depth_median_mm": float("nan"),
    }


def apply_similarity(vertices: np.ndarray, transform: dict[str, Any]) -> np.ndarray:
    scale = float(transform["scale"])
    rotation = np.asarray(transform["rotation"], dtype=np.float64)
    translation = np.asarray(transform["translation"], dtype=np.float64)
    return scale * (vertices @ rotation.T) + translation


def mean_finite(values: list[float]) -> float:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else float("inf")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G45 LAM Held-Out Camera Geometry Diagnostic",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Data gate:",
        "",
        "```text",
        payload["data_gate"],
        "```",
        "",
        "Held-out camera diagnostics:",
        "",
        "| camera | mask_iou | pred_cov | gt_cov | depth_abs_mean_mm | depth_abs_mean_over_gt_median | projected_faces |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["heldout_results"]:
        lines.append(
            f"| {row['camera']} | {row['mask_iou']:.6f} | {row['pred_coverage']:.6f} | "
            f"{row['gt_coverage']:.6f} | {row['depth_abs_mean_mm']:.6f} | "
            f"{row['depth_abs_mean_over_gt_median']:.6f} | {row['projected_faces']} |"
        )
    summary = payload["summary"]
    lines.extend(
        [
            "",
            "Summary:",
            "",
            "| metric | value | threshold |",
            "| --- | ---: | ---: |",
            f"| mean_mask_iou | {summary['mean_mask_iou']:.6f} | {payload['thresholds']['min_mean_mask_iou']:.6f} |",
            f"| min_mask_iou | {summary['min_mask_iou']:.6f} | {payload['thresholds']['min_per_view_mask_iou']:.6f} |",
            f"| mean_depth_abs_over_gt_median | {summary['mean_depth_abs_over_gt_median']:.6f} | {payload['thresholds']['max_mean_depth_abs_over_gt_median']:.6f} |",
            "",
            "Blocked interpretations:",
            "",
            "```text",
            "\n".join(payload["blocked_interpretations"]),
            "```",
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--case-root",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view"),
    )
    parser.add_argument(
        "--adapter-root",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102"),
    )
    parser.add_argument(
        "--lam-mesh",
        type=Path,
        default=Path(
            "/data1/workspace/airulan/3dv_work/runs/g42_lam_export_multiface_local_20260520/cano_gs/cano_gs/400017_000102_shaped_mesh.obj"
        ),
    )
    parser.add_argument(
        "--g44-json",
        type=Path,
        default=Path("experiments/metrics/g44_lam_similarity_geometry_gate_20260520.json"),
    )
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--target-focal", type=float, default=640.0)
    parser.add_argument("--min-mean-mask-iou", type=float, default=0.45)
    parser.add_argument("--min-per-view-mask-iou", type=float, default=0.35)
    parser.add_argument("--max-mean-depth-abs-over-gt-median", type=float, default=0.12)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g45_lam_heldout_camera_geometry_gate_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g45_lam_heldout_camera_geometry_gate_20260520.md"),
    )
    args = parser.parse_args()

    repo = args.repo
    g44 = load_json(repo / args.g44_json)
    cameras = load_json(args.case_root / "cameras.json")
    camera_by_id = camera_lookup(cameras)
    split = load_json(args.adapter_root / "train_test_split_6.json")
    transforms = load_json(args.adapter_root / "transforms.json")
    index_to_camera = {int(frame["view_index"]): str(frame["view_id"]) for frame in transforms["frames"]}
    heldout_cameras = [index_to_camera[int(idx)] for idx in split["test_ids"]]
    lam_vertices, lam_faces = load_obj(args.lam_mesh)
    aligned_vertices = apply_similarity(lam_vertices, g44["transform"])

    heldout_results: list[dict[str, Any]] = []
    for idx in split["test_ids"]:
        view_index = int(idx)
        camera = index_to_camera[view_index]
        entry = camera_by_id[camera]
        params = affine_params(entry, args.target_focal, args.image_size)
        uv, z = project_vertices(aligned_vertices, entry, params)
        pred_depth, pred_mask, projected_faces = rasterize_depth(uv, z, lam_faces, args.image_size)
        gt_mask = load_mask(args.adapter_root / "masks" / f"{view_index:03d}_{camera}_mask.png")
        gt_depth = np.load(args.adapter_root / "depth_raw_mm" / f"{view_index:03d}_{camera}_zbuffer_mm.npy")
        stats = depth_stats(pred_depth, gt_depth, mask_from_depth(pred_depth), gt_mask)
        stats.update({"camera": camera, "view_index": view_index, "projected_faces": int(projected_faces)})
        heldout_results.append(stats)

    summary = {
        "mean_mask_iou": float(np.mean([row["mask_iou"] for row in heldout_results])),
        "min_mask_iou": float(np.min([row["mask_iou"] for row in heldout_results])),
        "mean_depth_abs_over_gt_median": mean_finite([row["depth_abs_mean_over_gt_median"] for row in heldout_results]),
    }
    thresholds = {
        "min_mean_mask_iou": args.min_mean_mask_iou,
        "min_per_view_mask_iou": args.min_per_view_mask_iou,
        "max_mean_depth_abs_over_gt_median": args.max_mean_depth_abs_over_gt_median,
    }
    passes = (
        summary["mean_mask_iou"] >= args.min_mean_mask_iou
        and summary["min_mask_iou"] >= args.min_per_view_mask_iou
        and summary["mean_depth_abs_over_gt_median"] <= args.max_mean_depth_abs_over_gt_median
    )
    payload = {
        "date": DATE,
        "gate": "G45",
        "verdict": PASS_VERDICT if passes else BLOCK_VERDICT,
        "premise": (
            "Use the G44 similarity-aligned LAM shaped mesh and the G23 real-camera adapter to render geometry "
            "into held-out Multiface cameras, then compare silhouette and z-buffer depth against held-out GT "
            "masks/depth arrays without committing private images or meshes."
        ),
        "data_gate": (
            "PASS_REAL_GT_HELDOUT_DIAGNOSTIC. Inputs are G21/G23 Multiface real captured cameras/masks/depth, "
            "G42 private LAM shaped mesh, and G44 similarity transform. No pseudo-view candidate pool, "
            "experiments/downstream_datasets export, LAM motion-camera MP4, or held-out RGB image is used for "
            "training or committed output."
        ),
        "case_root": str(args.case_root),
        "adapter_root": str(args.adapter_root),
        "lam_mesh": str(args.lam_mesh),
        "g44_json": str(repo / args.g44_json),
        "heldout_cameras": heldout_cameras,
        "thresholds": thresholds,
        "summary": summary,
        "heldout_results": heldout_results,
        "blocked_interpretations": [
            "Do not report G45 as photometric reconstruction quality.",
            "Do not compare G45 to RGB PSNR/SSIM/LPIPS or SOTA tables.",
            "Do not treat similarity/ICP alignment as camera recovery or metric coordinate recovery.",
            "Do not use held-out RGB pixels for training; this gate consumes only masks/depth arrays derived from the GT mesh.",
            "Do not publish private Multiface/LAM PNG/MP4/PLY/OBJ outputs without explicit artifact review.",
            "Do not reintroduce experiments/downstream_datasets as training or evaluation data.",
        ],
        "decision": (
            "G45 is the first held-out-camera geometry diagnostic for the learned-prior route. It checks whether "
            "the aligned LAM mesh projects into held-out Multiface cameras with non-catastrophic silhouette/depth "
            "agreement. It remains below a final method result because it uses similarity-aligned mesh geometry, "
            "not the native learned-prior camera frame or RGB held-out rendering."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])
    print(f"mean_mask_iou={summary['mean_mask_iou']:.6f}")
    print(f"mean_depth_abs_over_gt_median={summary['mean_depth_abs_over_gt_median']:.6f}")
    if payload["verdict"] != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
