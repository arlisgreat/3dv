#!/usr/bin/env python3
"""Evaluate NeRSemble held-out metrics.

By default this smoke-tests the metric chain with a trivial source-copy
baseline. Pass --prediction-root to evaluate real method predictions named
cam_<serial>_frame_00000.png.
"""

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
PASS_COPY_VERDICT = "PASS_NERSEMBLE_HELDOUT_EVAL_HARNESS_SMOKE_COPY_BASELINE"
PASS_METHOD_VERDICT = "PASS_NERSEMBLE_HELDOUT_METHOD_EVAL"
BLOCKED = "BLOCKED_NERSEMBLE_HELDOUT_EVAL"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_rgb_with_alpha(path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError(f"could not read {path}")
    alpha = None
    if image.ndim == 2:
        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        rgb = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = image[:, :, 3].astype(np.float32) / 255.0
    else:
        rgb = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB)
    return rgb.astype(np.float32) / 255.0, alpha


def read_rgb(path: Path) -> np.ndarray:
    return read_rgb_with_alpha(path)[0]


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


def estimate_prediction_mask(pred: np.ndarray, alpha: np.ndarray | None = None) -> tuple[np.ndarray, str]:
    if alpha is not None:
        return alpha > 8.0 / 255.0, "alpha_channel"

    height, width = pred.shape[:2]
    border = max(4, min(height, width) // 20)
    border_pixels = np.concatenate(
        [
            pred[:border, :, :].reshape(-1, 3),
            pred[-border:, :, :].reshape(-1, 3),
            pred[:, :border, :].reshape(-1, 3),
            pred[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    quantized = np.clip(border_pixels * 255.0, 0, 255).astype(np.uint8) // 16
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    mode = colors[int(np.argmax(counts))]
    background = (mode.astype(np.float32) * 16.0 + 8.0) / 255.0
    distance = np.linalg.norm(pred - background[None, None, :], axis=-1)
    mask = distance > 0.08
    mask_u8 = (mask.astype(np.uint8) * 255)
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    return mask_u8 > 0, "border_mode_rgb_distance"


def write_md(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]
    lines = [
        f"# {payload['gate']} NeRSemble Held-Out Eval",
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
        "| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics["per_eval_serial"]:
        lines.append(
            f"| {row['eval_serial']} | {row['masked_rgb_psnr']:.6f} | "
            f"{row['masked_rgb_ssim_global_luma']:.6f} | {row['masked_rgb_mae']:.6f} | "
            f"{row['prediction_mask_vs_eval_mask_iou']:.6f} | {row['prediction_foreground_coverage']:.6f} |"
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
            f"| mean_prediction_mask_vs_eval_mask_iou | {metrics['mean_prediction_mask_vs_eval_mask_iou']:.6f} |",
            f"| mean_prediction_foreground_coverage | {metrics['mean_prediction_foreground_coverage']:.6f} |",
            "",
            "Evaluation mode:",
            "",
            "```text",
            payload["evaluation_mode"],
            "```",
            "",
            "Method label:",
            "",
            "```text",
            payload["method_label"],
            "```",
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
    parser.add_argument("--prediction-root", type=Path, default=None)
    parser.add_argument("--gate", default=GATE)
    parser.add_argument("--method-label", default=None)
    parser.add_argument("--pass-prediction-verdict", default=PASS_METHOD_VERDICT)
    parser.add_argument("--premise", default=None)
    parser.add_argument("--prediction-interpretation", default=None)
    parser.add_argument("--prediction-decision", default=None)
    parser.add_argument("--next-gate", default=None)
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
    prediction_root = args.prediction_root
    evaluation_mode = "method_predictions" if prediction_root is not None else "copy_source_baseline"
    per_eval: list[dict[str, Any]] = []
    for row in eval_views:
        target_rgb = read_rgb(Path(row["rgb_path"]))
        target_mask = read_mask(Path(row["mask_path"]))
        if prediction_root is not None:
            pred_path = prediction_root / f"cam_{row['serial']}_frame_00000.png"
            pred, pred_alpha = read_rgb_with_alpha(pred_path)
            pred_mask, pred_mask_source = estimate_prediction_mask(pred, pred_alpha)
        else:
            pred_path = None
            pred = source_rgb
            pred_mask = source_mask
            pred_mask_source = "source_adapter_alpha"
        if pred.shape != target_rgb.shape:
            pred = cv2.resize(pred, (target_rgb.shape[1], target_rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
            pred_mask = cv2.resize(pred_mask.astype(np.uint8), (target_mask.shape[1], target_mask.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        valid = target_mask
        rgb = masked_metrics(pred, target_rgb, valid)
        per_eval.append(
            {
                "eval_serial": row["serial"],
                "prediction_path": str(pred_path) if pred_path is not None else "copy_source_baseline",
                "masked_rgb_psnr": rgb["psnr"],
                "masked_rgb_ssim_global_luma": rgb["ssim_global_luma"],
                "masked_rgb_mae": rgb["mae"],
                "masked_rgb_mse": rgb["mse"],
                "prediction_mask_source": pred_mask_source,
                "prediction_mask_vs_eval_mask_iou": mask_iou(pred_mask, target_mask),
                "source_mask_vs_eval_mask_iou": mask_iou(pred_mask, target_mask),
                "prediction_foreground_coverage": float(pred_mask.mean()),
                "target_alpha_coverage": row["alpha_coverage"],
            }
        )

    metrics = {
        "per_eval_serial": per_eval,
        "mean_masked_rgb_psnr": mean([row["masked_rgb_psnr"] for row in per_eval]),
        "mean_masked_rgb_ssim_global_luma": mean([row["masked_rgb_ssim_global_luma"] for row in per_eval]),
        "mean_masked_rgb_mae": mean([row["masked_rgb_mae"] for row in per_eval]),
        "mean_prediction_mask_vs_eval_mask_iou": mean([row["prediction_mask_vs_eval_mask_iou"] for row in per_eval]),
        "mean_source_mask_vs_eval_mask_iou": mean([row["source_mask_vs_eval_mask_iou"] for row in per_eval]),
        "mean_prediction_foreground_coverage": mean([row["prediction_foreground_coverage"] for row in per_eval]),
        "lpips": "not_run_in_smoke_no_dependency_loaded",
    }
    passed = len(per_eval) >= 3 and all(np.isfinite(row["masked_rgb_psnr"]) for row in per_eval)
    verdict = (args.pass_prediction_verdict if prediction_root is not None else PASS_COPY_VERDICT) if passed else BLOCKED
    default_premise = (
        "Exercise the NeRSemble held-out metric chain. In copy-source mode this is a deliberately weak "
        "baseline; in prediction-root mode it evaluates rendered outputs for each local held-out camera."
    )
    default_interpretation = (
        "The copy-source baseline is expected to be low because target cameras see different viewpoints. "
        "Prediction-root mode can support a method-quality discussion only after model distribution, renderer-contract, "
        "visual, and artifact gates pass."
    )
    default_next_gate = (
        "Run a real method output through this exact source/eval split, then report RGB/mask/geometry metrics "
        "only after model distribution and artifact/privacy gates pass."
    )
    if prediction_root is not None:
        passed_decision = args.prediction_decision or "Held-out RGB/mask prediction files produced finite metrics on the audited NeRSemble split."
    else:
        passed_decision = "Held-out RGB/mask metric plumbing is ready for a real learned-prior/feed-forward method output."
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": args.premise or default_premise,
        "verdict": verdict,
        "case": manifest["case"],
        "split": manifest["split"],
        "source_serial": source["serial"],
        "evaluation_mode": evaluation_mode,
        "method_label": args.method_label or ("copy_source_baseline" if prediction_root is None else "method_predictions"),
        "prediction_root": str(prediction_root) if prediction_root is not None else None,
        "metrics": metrics,
        "interpretation": args.prediction_interpretation or default_interpretation,
        "decision": passed_decision if passed else "Blocked: held-out metric plumbing did not produce finite metrics.",
        "next_gate": args.next_gate or default_next_gate,
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
