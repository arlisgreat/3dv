#!/usr/bin/env python3
"""Smoke-test NeRSemble held-out metrics with a trivial source-copy baseline."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np


DATE = "2026-05-27"
GATE = "G55"
PASS_VERDICT = "PASS_NERSEMBLE_HELDOUT_EVAL_HARNESS_SMOKE_COPY_BASELINE"
BLOCKED = "BLOCKED_NERSEMBLE_HELDOUT_EVAL_HARNESS_SMOKE"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_rgb(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"could not read {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def read_mask(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"could not read {path}")
    return mask > 8


def masked_metrics(pred: np.ndarray, target: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    valid = mask.astype(bool)
    if not valid.any():
        return {"mse": math.nan, "mae": math.nan, "psnr": math.nan, "ssim_global_luma": math.nan}
    diff = pred[valid] - target[valid]
    mse = float(np.mean(diff * diff))
    mae = float(np.mean(np.abs(diff)))
    psnr = float(-10.0 * math.log10(max(mse, 1e-12)))
    pred_luma = (0.299 * pred[..., 0] + 0.587 * pred[..., 1] + 0.114 * pred[..., 2])[valid]
    target_luma = (0.299 * target[..., 0] + 0.587 * target[..., 1] + 0.114 * target[..., 2])[valid]
    mu_x = float(pred_luma.mean())
    mu_y = float(target_luma.mean())
    var_x = float(pred_luma.var())
    var_y = float(target_luma.var())
    cov_xy = float(((pred_luma - mu_x) * (target_luma - mu_y)).mean())
    c1 = 0.01**2
    c2 = 0.03**2
    ssim = ((2 * mu_x * mu_y + c1) * (2 * cov_xy + c2)) / ((mu_x**2 + mu_y**2 + c1) * (var_x + var_y + c2))
    return {"mse": mse, "mae": mae, "psnr": psnr, "ssim_global_luma": float(ssim)}


def mask_iou(source: np.ndarray, target: np.ndarray) -> float:
    inter = np.logical_and(source, target).sum()
    union = np.logical_or(source, target).sum()
    return float(inter / max(union, 1))


def write_md(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]
    lines = [
        "# G55 NeRSemble Held-Out Eval Harness Smoke",
        "",
        f"Date: {payload['date']}",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Metrics:",
        "",
        "| eval serial | PSNR mask | SSIM global luma | MAE mask | copy mask IoU |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics["per_eval_serial"]:
        lines.append(
            f"| {row['eval_serial']} | {row['masked_rgb_psnr']:.6f} | "
            f"{row['masked_rgb_ssim_global_luma']:.6f} | {row['masked_rgb_mae']:.6f} | {row['source_mask_vs_eval_mask_iou']:.6f} |"
        )
    lines.extend(
        [
            "",
            "Mean metrics:",
            "",
            "| field | value |",
            "| --- | ---: |",
            f"| mean_masked_rgb_psnr | {metrics['mean_masked_rgb_psnr']:.6f} |",
            f"| mean_masked_rgb_ssim_global_luma | {metrics['mean_masked_rgb_ssim_global_luma']:.6f} |",
            f"| mean_masked_rgb_mae | {metrics['mean_masked_rgb_mae']:.6f} |",
            f"| mean_source_mask_vs_eval_mask_iou | {metrics['mean_source_mask_vs_eval_mask_iou']:.6f} |",
            "",
            "Interpretation:",
            "",
            "```text",
            payload["interpretation"],
            "```",
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
            "",
            "Next gate:",
            "",
            "```text",
            payload["next_gate"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g55_nersemble_heldout_eval_harness_smoke_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g55_nersemble_heldout_eval_harness_smoke_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    manifest = load_json(args.adapter_manifest)
    views = manifest["views"]
    source = next(row for row in views if row["role"] == "source_single_image")
    eval_views = [row for row in views if row["role"] == "local_heldout_eval"]

    source_rgb = read_rgb(Path(source["rgb_path"]))
    source_mask = read_mask(Path(source["mask_path"]))
    per_eval: list[dict[str, Any]] = []
    for row in eval_views:
        target_rgb = read_rgb(Path(row["rgb_path"]))
        target_mask = read_mask(Path(row["mask_path"]))
        if source_rgb.shape != target_rgb.shape:
            pred = cv2.resize(source_rgb, (target_rgb.shape[1], target_rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
            pred_mask = cv2.resize(source_mask.astype(np.uint8), (target_mask.shape[1], target_mask.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        else:
            pred = source_rgb
            pred_mask = source_mask
        valid = target_mask
        rgb = masked_metrics(pred, target_rgb, valid)
        per_eval.append(
            {
                "eval_serial": row["serial"],
                "masked_rgb_psnr": rgb["psnr"],
                "masked_rgb_ssim_global_luma": rgb["ssim_global_luma"],
                "masked_rgb_mae": rgb["mae"],
                "masked_rgb_mse": rgb["mse"],
                "source_mask_vs_eval_mask_iou": mask_iou(pred_mask, target_mask),
                "target_alpha_coverage": row["alpha_coverage"],
            }
        )

    metrics = {
        "per_eval_serial": per_eval,
        "mean_masked_rgb_psnr": mean([row["masked_rgb_psnr"] for row in per_eval]),
        "mean_masked_rgb_ssim_global_luma": mean([row["masked_rgb_ssim_global_luma"] for row in per_eval]),
        "mean_masked_rgb_mae": mean([row["masked_rgb_mae"] for row in per_eval]),
        "mean_source_mask_vs_eval_mask_iou": mean([row["source_mask_vs_eval_mask_iou"] for row in per_eval]),
        "lpips": "not_run_in_smoke_no_dependency_loaded",
    }
    passed = len(per_eval) >= 3 and all(np.isfinite(row["masked_rgb_psnr"]) for row in per_eval)
    verdict = PASS_VERDICT if passed else BLOCKED
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "Exercise the NeRSemble held-out metric chain with a deliberately weak copy-source baseline. "
            "The source image is pasted as the prediction for each local held-out camera; this validates metric IO only."
        ),
        "verdict": verdict,
        "case": manifest["case"],
        "split": manifest["split"],
        "source_serial": source["serial"],
        "metrics": metrics,
        "interpretation": (
            "The low copy-baseline numbers are expected because the target cameras see different viewpoints. "
            "This is a harness smoke and lower-bound sanity check, not a method-quality result."
        ),
        "decision": (
            "Held-out RGB/mask metric plumbing is ready for a real learned-prior/feed-forward method output."
            if passed
            else "Blocked: held-out metric plumbing did not produce finite metrics."
        ),
        "next_gate": (
            "Run a real method output through this exact source/eval split, then report RGB/mask/geometry metrics "
            "only after model distribution and artifact/privacy gates pass."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
