#!/usr/bin/env python3
"""Run a weak, privacy-safe geometry sanity check for LAM export vs local GT."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


DATE = "2026-05-20"
VERDICT = "PASS_NORMALIZED_GEOMETRY_SANITY_NOT_QUALITY_METRIC"


def read_obj_vertices(path: Path) -> np.ndarray:
    vertices: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.startswith("v "):
                continue
            parts = line.split()
            if len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.asarray(vertices, dtype=np.float64)


def bbox_stats(vertices: np.ndarray) -> dict[str, Any]:
    mn = vertices.min(axis=0)
    mx = vertices.max(axis=0)
    ext = mx - mn
    return {
        "min": [float(x) for x in mn],
        "max": [float(x) for x in mx],
        "extent": [float(x) for x in ext],
        "diag": float(np.linalg.norm(ext)),
        "vertex_count": int(vertices.shape[0]),
    }


def normalize(vertices: np.ndarray) -> np.ndarray:
    mn = vertices.min(axis=0)
    mx = vertices.max(axis=0)
    center = (mn + mx) * 0.5
    scale = np.linalg.norm(mx - mn)
    if scale <= 0:
        raise ValueError("degenerate geometry scale")
    return (vertices - center) / scale


def sample_vertices(vertices: np.ndarray, max_points: int, seed: int) -> np.ndarray:
    if vertices.shape[0] <= max_points:
        return vertices
    rng = np.random.default_rng(seed)
    idx = rng.choice(vertices.shape[0], max_points, replace=False)
    return vertices[idx]


def nearest_mean(a: np.ndarray, b: np.ndarray, chunk: int = 512) -> float:
    vals = []
    for start in range(0, a.shape[0], chunk):
        aa = a[start : start + chunk]
        d2 = ((aa[:, None, :] - b[None, :, :]) ** 2).sum(axis=-1)
        vals.append(np.sqrt(d2.min(axis=1)))
    return float(np.concatenate(vals).mean())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G43 LAM Geometry Sanity Gate",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Scope:",
        "",
        "```text",
        payload["scope"],
        "```",
        "",
        "Geometry stats:",
        "",
        "| field | LAM shaped mesh | Multiface GT mesh |",
        "| --- | ---: | ---: |",
        f"| vertex_count | {payload['lam_bbox']['vertex_count']} | {payload['gt_bbox']['vertex_count']} |",
        f"| bbox_diag | {payload['lam_bbox']['diag']:.6f} | {payload['gt_bbox']['diag']:.6f} |",
        "",
        "Normalized nearest-neighbor sanity:",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| lam_to_gt_mean | {payload['normalized_nn']['lam_to_gt_mean']:.6f} |",
        f"| gt_to_lam_mean | {payload['normalized_nn']['gt_to_lam_mean']:.6f} |",
        f"| symmetric_mean | {payload['normalized_nn']['symmetric_mean']:.6f} |",
        "",
        "Latest literature monitor:",
        "",
        "| work | date | signal |",
        "| --- | --- | --- |",
    ]
    for item in payload["literature_monitor"]:
        lines.append(f"| {item['work']} | {item['date']} | {item['signal']} |")
    lines.extend(
        [
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
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g43_lam_geometry_sanity_gate_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g43_lam_geometry_sanity_gate_20260520.md"),
    )
    args = parser.parse_args()

    lam = read_obj_vertices(args.lam_mesh)
    gt = read_obj_vertices(args.gt_mesh)
    lam_n = sample_vertices(normalize(lam), args.sample_count, seed=0)
    gt_n = sample_vertices(normalize(gt), args.sample_count, seed=1)
    lam_to_gt = nearest_mean(lam_n, gt_n)
    gt_to_lam = nearest_mean(gt_n, lam_n)
    payload = {
        "date": DATE,
        "gate": "G43",
        "verdict": VERDICT,
        "scope": (
            "Weak normalized geometry sanity only. The LAM shaped mesh and Multiface tracked mesh are compared "
            "after independent bbox normalization, with no camera alignment, no scale recovery, and no held-out "
            "rendering. This can catch catastrophic shape/export failure but cannot support a quality claim."
        ),
        "lam_mesh": str(args.lam_mesh),
        "gt_mesh": str(args.gt_mesh),
        "lam_bbox": bbox_stats(lam),
        "gt_bbox": bbox_stats(gt),
        "normalized_nn": {
            "lam_to_gt_mean": lam_to_gt,
            "gt_to_lam_mean": gt_to_lam,
            "symmetric_mean": (lam_to_gt + gt_to_lam) * 0.5,
            "sample_count": args.sample_count,
        },
        "literature_monitor": [
            {
                "work": "FFAvatar",
                "date": "2026-05-14",
                "source": "https://arxiv.org/abs/2605.15320",
                "signal": "Few-shot feed-forward Gaussian heads report NeRSemble metrics and a 5.5 PSNR gain over LAM, so LAM should be treated as baseline/export probe, not final method.",
            },
            {
                "work": "Any3DAvatar",
                "date": "2026-04-15",
                "source": "https://arxiv.org/abs/2604.13856",
                "signal": "Single-image full-head work uses a structured Plucker-aware Gaussian scaffold and dense multi-view supervision.",
            },
            {
                "work": "MATCH",
                "date": "2026-03-16",
                "source": "https://arxiv.org/abs/2603.15811",
                "signal": "Recent feed-forward Gaussian registration predicts in a fixed UV/template correspondence layout from calibrated multi-view images.",
            },
            {
                "work": "FastGHA",
                "date": "2026-01-30",
                "source": "https://arxiv.org/abs/2601.13837",
                "signal": "Uses feed-forward per-pixel Gaussians, transformer multi-view aggregation, and explicit geometry supervision from point maps.",
            },
            {
                "work": "PanoLAM",
                "date": "2025-10-10",
                "source": "https://arxiv.org/abs/2509.07552",
                "signal": "Full-head Gaussian one-shot direction relies on FLAME sparse points, transformers, and synthetic 3D-GAN priors.",
            },
        ],
        "blocked_interpretations": [
            "Do not report the normalized nearest-neighbor value as reconstruction accuracy.",
            "Do not compare this weak mesh sanity to RI3D held-out PSNR/SSIM/LPIPS.",
            "Do not publish the private LAM/Multiface OBJ, PLY, PNG, or MP4 artifacts without review.",
            "Do not reintroduce pseudo-view candidate pools as training or evaluation data.",
        ],
        "decision": (
            "G43 passes as an export/geometry sanity check: LAM emits a non-degenerate head-shaped mesh near the "
            "local GT shape after scale-free normalization. The next real milestone remains camera-aligned "
            "held-out rendering or an explicitly aligned GT geometry metric."
        ),
    }
    write_json(args.repo / args.output_json, payload)
    write_md(args.repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])


if __name__ == "__main__":
    main()
