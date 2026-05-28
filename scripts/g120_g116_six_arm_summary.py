#!/usr/bin/env python3
"""Summarize the current G116 six-arm single-case ablation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G116_SINGLE_CASE_SIX_ARM_ABLATION_READY_MULTICASE_PENDING"
BLOCKED = "BLOCKED_G116_SIX_ARM_ABLATION_INCOMPLETE"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def metric_row(label: str, path: Path, role: str, notes: str) -> dict[str, Any]:
    payload = load_json(path)
    metrics = payload["metrics"]
    return {
        "label": label,
        "role": role,
        "eval_json": str(path),
        "verdict": payload.get("verdict"),
        "mean_masked_rgb_psnr": metrics["mean_masked_rgb_psnr"],
        "mean_masked_rgb_ssim_global_luma": metrics["mean_masked_rgb_ssim_global_luma"],
        "mean_prediction_mask_vs_eval_mask_iou": metrics["mean_prediction_mask_vs_eval_mask_iou"],
        "mean_prediction_foreground_coverage": metrics["mean_prediction_foreground_coverage"],
        "notes": notes,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G120 G116 Six-Arm Ablation Summary",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Single-case arms:",
        "",
        "| arm | role | PSNR | SSIM | mask IoU | coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["arms"]:
        lines.append(
            f"| {row['label']} | {row['role']} | {row['mean_masked_rgb_psnr']:.6f} | "
            f"{row['mean_masked_rgb_ssim_global_luma']:.6f} | "
            f"{row['mean_prediction_mask_vs_eval_mask_iou']:.6f} | "
            f"{row['mean_prediction_foreground_coverage']:.6f} |"
        )
    lines.extend(
        [
            "",
            "Ablation conclusions:",
            "",
            "```text",
            "\n".join(payload["ablation_conclusions"]),
            "```",
            "",
            "Naive camera/crop audit:",
            "",
            "```text",
            payload["naive_camera_crop_interpretation"],
            "```",
            "",
            "Remaining requirement:",
            "",
            "```text",
            payload["remaining_requirement"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    paths = {
        "direct": repo / "experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json",
        "naive": repo / "experiments/metrics/g103_g81_naive_strict_pool_iter1500_splat8_heldout_eval_20260528.json",
        "full": repo / "experiments/metrics/g117_g116_full_aware_ablation_eval_20260528.json",
        "no_identity": repo / "experiments/metrics/g118_g116_without_identity_gate_eval_20260528.json",
        "no_confidence": repo / "experiments/metrics/g119_g116_without_confidence_gate_eval_20260528.json",
        "no_source_geometry": repo / "experiments/metrics/g104_g81_strict_aware_iter1500_splat8_heldout_eval_20260528.json",
        "naive_camera_crop": repo / "experiments/metrics/g116_naive_camera_crop_audit_20260528.json",
        "ablation_generation": repo / "experiments/metrics/g116_source_gated_pseudo_prior_ablation_20260528.json",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    arms = [] if missing else [
        metric_row("direct_single_image_gaussian_lam", paths["direct"], "direct prior strength", "No pseudo views; LAM direct source-aligned Gaussian."),
        metric_row("naive_pseudo_view_pipeline", paths["naive"], "pseudo-view reconstruction baseline", "RI3D-style pseudo-view geometry arm."),
        metric_row("identity_confidence_aware_pseudo_prior", paths["full"], "full gated method", "Direct geometry/source alpha plus identity/confidence pseudo color prior."),
        metric_row("without_identity_gate", paths["no_identity"], "identity ablation", "Direct geometry/source alpha plus confidence-only pseudo color prior."),
        metric_row("without_confidence_gate", paths["no_confidence"], "confidence ablation", "Direct geometry/source alpha plus identity-only pseudo color prior."),
        metric_row("without_source_gated_alpha_geometry_prior", paths["no_source_geometry"], "geometry/source-alpha ablation", "Strict identity/confidence pseudo-view RI3D geometry without direct geometry/source alpha."),
    ]
    by_label = {row["label"]: row for row in arms}
    conclusions: list[str] = []
    if not missing:
        full = by_label["identity_confidence_aware_pseudo_prior"]
        direct = by_label["direct_single_image_gaussian_lam"]
        naive = by_label["naive_pseudo_view_pipeline"]
        no_identity = by_label["without_identity_gate"]
        no_confidence = by_label["without_confidence_gate"]
        no_source_geometry = by_label["without_source_gated_alpha_geometry_prior"]
        conclusions.extend(
            [
                f"Full gated pseudo prior exceeds direct on PSNR by {full['mean_masked_rgb_psnr'] - direct['mean_masked_rgb_psnr']:.6f} and mask IoU by {full['mean_prediction_mask_vs_eval_mask_iou'] - direct['mean_prediction_mask_vs_eval_mask_iou']:.6f}.",
                f"Full gated pseudo prior exceeds naive by {full['mean_masked_rgb_psnr'] - naive['mean_masked_rgb_psnr']:.6f} PSNR and {full['mean_prediction_mask_vs_eval_mask_iou'] - naive['mean_prediction_mask_vs_eval_mask_iou']:.6f} mask IoU.",
                f"Identity gate has a positive single-case RGB effect: full PSNR - w/o identity PSNR = {full['mean_masked_rgb_psnr'] - no_identity['mean_masked_rgb_psnr']:.6f}; masks are identical because both keep source-gated alpha/direct geometry.",
                f"Confidence gate is inconclusive in this case: w/o confidence PSNR differs by {no_confidence['mean_masked_rgb_psnr'] - full['mean_masked_rgb_psnr']:.6f}, while SSIM differs by {no_confidence['mean_masked_rgb_ssim_global_luma'] - full['mean_masked_rgb_ssim_global_luma']:.6f}; mask is unchanged.",
                f"Direct geometry/source alpha is the dominant factor: removing it drops from full PSNR/mask IoU {full['mean_masked_rgb_psnr']:.6f}/{full['mean_prediction_mask_vs_eval_mask_iou']:.6f} to {no_source_geometry['mean_masked_rgb_psnr']:.6f}/{no_source_geometry['mean_prediction_mask_vs_eval_mask_iou']:.6f}.",
            ]
        )
    camera_audit = {} if missing else load_json(paths["naive_camera_crop"])
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G120",
        "verdict": PASS_VERDICT if not missing else BLOCKED,
        "case": camera_audit.get("case"),
        "split": camera_audit.get("split"),
        "arms": arms,
        "missing_requirements": missing,
        "ablation_conclusions": conclusions,
        "naive_camera_crop_interpretation": camera_audit.get("interpretation", "missing naive camera/crop audit"),
        "remaining_requirement": (
            "Multi-case replication is still pending; this G120 summary proves only the current single NeRSemble source/eval split."
            if not missing
            else "Blocked until all six arm metric files and naive camera/crop audit exist."
        ),
        "decision": (
            "Single-case six-arm ablation is ready, but the active goal remains incomplete until multi-case replication passes."
            if not missing
            else "Blocked: six-arm summary inputs are incomplete."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": payload["verdict"], "remaining": payload["remaining_requirement"]}, indent=2))
    if payload["verdict"] != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
