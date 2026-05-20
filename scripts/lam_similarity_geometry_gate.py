#!/usr/bin/env python3
"""Similarity-align LAM mesh vertices to Multiface GT for a weak geometry diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


DATE = "2026-05-20"
PASS_VERDICT = "PASS_ALIGNED_GEOMETRY_DIAGNOSTIC_ONLY_NO_RECONSTRUCTION_QUALITY_CLAIM"
BLOCK_VERDICT = "BLOCKED_SIMILARITY_ALIGNED_GEOMETRY_DIAGNOSTIC"


def read_obj_vertices(path: Path) -> np.ndarray:
    vertices: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.startswith("v "):
                continue
            parts = line.split()
            if len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
    if not vertices:
        raise ValueError(f"no OBJ vertices found: {path}")
    return np.asarray(vertices, dtype=np.float64)


def bbox(vertices: np.ndarray) -> dict[str, Any]:
    mn = vertices.min(axis=0)
    mx = vertices.max(axis=0)
    extent = mx - mn
    return {
        "min": mn.tolist(),
        "max": mx.tolist(),
        "center": ((mn + mx) * 0.5).tolist(),
        "extent": extent.tolist(),
        "diag": float(np.linalg.norm(extent)),
        "vertex_count": int(vertices.shape[0]),
    }


def sample(vertices: np.ndarray, max_points: int, seed: int) -> np.ndarray:
    if vertices.shape[0] <= max_points:
        return vertices
    rng = np.random.default_rng(seed)
    return vertices[rng.choice(vertices.shape[0], max_points, replace=False)]


def nearest_indices(a: np.ndarray, b: np.ndarray, chunk: int = 512) -> np.ndarray:
    indices = []
    for start in range(0, a.shape[0], chunk):
        aa = a[start : start + chunk]
        d2 = ((aa[:, None, :] - b[None, :, :]) ** 2).sum(axis=-1)
        indices.append(np.argmin(d2, axis=1))
    return np.concatenate(indices)


def distance_stats(a: np.ndarray, b: np.ndarray, chunk: int = 512) -> dict[str, float]:
    distances = []
    for start in range(0, a.shape[0], chunk):
        aa = a[start : start + chunk]
        d2 = ((aa[:, None, :] - b[None, :, :]) ** 2).sum(axis=-1)
        distances.append(np.sqrt(d2.min(axis=1)))
    vals = np.concatenate(distances)
    return {
        "mean": float(vals.mean()),
        "median": float(np.median(vals)),
        "p95": float(np.percentile(vals, 95)),
        "max": float(vals.max()),
    }


def umeyama_similarity(source: np.ndarray, target: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    if source.shape != target.shape:
        raise ValueError("source and target correspondence arrays must have the same shape")
    src_mu = source.mean(axis=0)
    tgt_mu = target.mean(axis=0)
    src_c = source - src_mu
    tgt_c = target - tgt_mu
    cov = (tgt_c.T @ src_c) / source.shape[0]
    u, d, vt = np.linalg.svd(cov)
    sign = np.ones(3)
    if np.linalg.det(u @ vt) < 0:
        sign[-1] = -1
    s_mat = np.diag(sign)
    rotation = u @ s_mat @ vt
    variance = np.mean(np.sum(src_c * src_c, axis=1))
    scale = float(np.sum(d * sign) / variance)
    translation = tgt_mu - scale * (rotation @ src_mu)
    return scale, rotation, translation


def apply_similarity(vertices: np.ndarray, scale: float, rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    return scale * (vertices @ rotation.T) + translation


def bbox_initial_similarity(source: np.ndarray, target: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    src_box = bbox(source)
    tgt_box = bbox(target)
    source_diag = max(float(src_box["diag"]), 1e-12)
    scale = float(tgt_box["diag"]) / source_diag
    rotation = np.eye(3)
    src_center = np.asarray(src_box["center"], dtype=np.float64)
    tgt_center = np.asarray(tgt_box["center"], dtype=np.float64)
    translation = tgt_center - scale * src_center
    return scale, rotation, translation


def run_icp(source: np.ndarray, target: np.ndarray, max_iter: int) -> tuple[float, np.ndarray, np.ndarray, list[dict[str, float]]]:
    scale, rotation, translation = bbox_initial_similarity(source, target)
    trace = []
    for iteration in range(max_iter):
        transformed = apply_similarity(source, scale, rotation, translation)
        target_corr = target[nearest_indices(transformed, target)]
        scale, rotation, translation = umeyama_similarity(source, target_corr)
        transformed = apply_similarity(source, scale, rotation, translation)
        stats = distance_stats(transformed, target)
        trace.append(
            {
                "iteration": float(iteration + 1),
                "source_to_gt_mean": stats["mean"],
                "source_to_gt_median": stats["median"],
                "source_to_gt_p95": stats["p95"],
            }
        )
    return scale, rotation, translation, trace


def normalize_stats(stats: dict[str, float], diag: float) -> dict[str, float]:
    return {key: float(value / diag) for key, value in stats.items()}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["final_metrics"]
    norm = payload["normalized_by_gt_bbox_diag"]
    lines = [
        "# G44 Similarity-Aligned LAM Geometry Diagnostic",
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
        "Geometry inputs:",
        "",
        "| input | vertices | bbox_diag | private_path_policy |",
        "| --- | ---: | ---: | --- |",
        f"| LAM shaped mesh | {payload['lam_bbox']['vertex_count']} | {payload['lam_bbox']['diag']:.6f} | metrics/hashes only; OBJ remains under 3dv_work |",
        f"| Multiface GT mesh | {payload['gt_bbox']['vertex_count']} | {payload['gt_bbox']['diag']:.6f} | metrics only; OBJ remains under 3dv_work |",
        "",
        "Similarity/ICP alignment:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| sample_count | {payload['sample_count']} |",
        f"| icp_iterations | {payload['icp_iterations']} |",
        f"| final_scale_lam_to_gt | {payload['transform']['scale']:.6f} |",
        f"| determinant_rotation | {payload['transform']['determinant_rotation']:.6f} |",
        "",
        "Final nearest-neighbor diagnostic distances:",
        "",
        "| metric | raw GT units | normalized by GT bbox diag |",
        "| --- | ---: | ---: |",
        f"| lam_to_gt_mean | {metrics['lam_to_gt']['mean']:.6f} | {norm['lam_to_gt']['mean']:.6f} |",
        f"| lam_to_gt_median | {metrics['lam_to_gt']['median']:.6f} | {norm['lam_to_gt']['median']:.6f} |",
        f"| lam_to_gt_p95 | {metrics['lam_to_gt']['p95']:.6f} | {norm['lam_to_gt']['p95']:.6f} |",
        f"| gt_to_lam_mean | {metrics['gt_to_lam']['mean']:.6f} | {norm['gt_to_lam']['mean']:.6f} |",
        f"| gt_to_lam_median | {metrics['gt_to_lam']['median']:.6f} | {norm['gt_to_lam']['median']:.6f} |",
        f"| gt_to_lam_p95 | {metrics['gt_to_lam']['p95']:.6f} | {norm['gt_to_lam']['p95']:.6f} |",
        f"| symmetric_mean | {metrics['symmetric_mean']:.6f} | {norm['symmetric_mean']:.6f} |",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--lam-mesh",
        type=Path,
        default=Path(
            "/data1/workspace/airulan/3dv_work/runs/g42_lam_export_multiface_local_20260520/cano_gs/cano_gs/400017_000102_shaped_mesh.obj"
        ),
    )
    parser.add_argument(
        "--gt-mesh",
        type=Path,
        default=Path(
            "/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view/mesh/000102.obj"
        ),
    )
    parser.add_argument("--sample-count", type=int, default=3000)
    parser.add_argument("--icp-iterations", type=int, default=20)
    parser.add_argument(
        "--pass-threshold-normalized-symmetric-mean",
        type=float,
        default=0.08,
        help="Sanity-only pass threshold after similarity alignment, normalized by GT bbox diagonal.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g44_lam_similarity_geometry_gate_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g44_lam_similarity_geometry_gate_20260520.md"),
    )
    args = parser.parse_args()

    lam = read_obj_vertices(args.lam_mesh)
    gt = read_obj_vertices(args.gt_mesh)
    lam_sample = sample(lam, args.sample_count, seed=44)
    gt_sample = sample(gt, args.sample_count, seed=45)
    scale, rotation, translation, trace = run_icp(lam_sample, gt_sample, args.icp_iterations)
    lam_aligned = apply_similarity(lam_sample, scale, rotation, translation)
    lam_to_gt = distance_stats(lam_aligned, gt_sample)
    gt_to_lam = distance_stats(gt_sample, lam_aligned)
    gt_diag = bbox(gt)["diag"]
    symmetric_mean = (lam_to_gt["mean"] + gt_to_lam["mean"]) * 0.5
    normalized = {
        "lam_to_gt": normalize_stats(lam_to_gt, gt_diag),
        "gt_to_lam": normalize_stats(gt_to_lam, gt_diag),
        "symmetric_mean": float(symmetric_mean / gt_diag),
    }
    verdict = (
        PASS_VERDICT
        if normalized["symmetric_mean"] <= args.pass_threshold_normalized_symmetric_mean
        else BLOCK_VERDICT
    )
    payload = {
        "date": DATE,
        "gate": "G44",
        "verdict": verdict,
        "premise": (
            "Given the G42 local LAM export and G21 real-GT Multiface mesh, fit a similarity/ICP transform from "
            "the LAM shaped mesh to the Multiface GT mesh and record a weak aligned geometry diagnostic without "
            "publishing private mesh/media artifacts."
        ),
        "data_gate": (
            "PASS_REAL_GT_DIAGNOSTIC_ONLY. Inputs are the G42 private LAM shaped mesh and the G21 local Multiface "
            "GT mesh. No experiments/downstream_datasets candidate pool, generated pseudo-view training data, or "
            "held-out RGB media are consumed. G42 visual audit still applies."
        ),
        "lam_mesh": str(args.lam_mesh),
        "gt_mesh": str(args.gt_mesh),
        "sample_count": min(args.sample_count, int(lam.shape[0]), int(gt.shape[0])),
        "icp_iterations": args.icp_iterations,
        "pass_threshold_normalized_symmetric_mean": args.pass_threshold_normalized_symmetric_mean,
        "lam_bbox": bbox(lam),
        "gt_bbox": bbox(gt),
        "transform": {
            "scale": float(scale),
            "rotation": rotation.tolist(),
            "determinant_rotation": float(np.linalg.det(rotation)),
            "translation": translation.tolist(),
        },
        "icp_trace": trace,
        "final_metrics": {
            "lam_to_gt": lam_to_gt,
            "gt_to_lam": gt_to_lam,
            "symmetric_mean": float(symmetric_mean),
        },
        "normalized_by_gt_bbox_diag": normalized,
        "blocked_interpretations": [
            "Do not report this as final reconstruction quality.",
            "Do not compare this directly to held-out RGB PSNR/SSIM/LPIPS.",
            "Do not treat ICP alignment as proof that LAM recovered the real camera or metric coordinate frame.",
            "Do not ignore coverage/topology mismatch: LAM and Multiface meshes differ around hair, neck, shoulders, and boundary support.",
            "Do not publish the private Multiface or LAM OBJ/PLY/PNG/MP4 artifacts without explicit review.",
            "Do not use experiments/downstream_datasets as training or evaluation data.",
        ],
        "decision": (
            "G44 is an aligned geometry diagnostic only. It is stronger than G43's independent bbox-normalized "
            "sanity because one similarity/ICP transform is fit into the GT frame, but it still lacks held-out "
            "camera rendering, verified surface correspondence, coverage trimming, and a publishable benchmark "
            "artifact package."
        ),
    }
    write_json(args.repo / args.output_json, payload)
    write_md(args.repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])
    print(f"normalized_symmetric_mean={normalized['symmetric_mean']:.6f}")
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
