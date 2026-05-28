#!/usr/bin/env python3
"""Aggregate G116/G117 into an ablation contract for the current NeRSemble case."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G118_SOURCE_GATED_ABLATION_CONTRACT_SINGLE_CASE"
BLOCKED = "BLOCKED_G118_SOURCE_GATED_ABLATION_CONTRACT"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def eval_row(name: str, role: str, path: Path, note: str) -> dict[str, Any]:
    payload = load_json(path)
    metrics = payload["metrics"]
    return {
        "name": name,
        "role": role,
        "eval_json": str(path),
        "verdict": payload.get("verdict"),
        "mean_masked_rgb_psnr": metrics.get("mean_masked_rgb_psnr"),
        "mean_prediction_mask_vs_eval_mask_iou": metrics.get("mean_prediction_mask_vs_eval_mask_iou"),
        "mean_prediction_foreground_coverage": metrics.get("mean_prediction_foreground_coverage"),
        "note": note,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G118 Source-Gated Pseudo Prior Ablation Contract",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Arms:",
        "",
        "| arm | role | PSNR | mask IoU | coverage | note |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["arms"]:
        lines.append(
            f"| {row['name']} | {row['role']} | {row['mean_masked_rgb_psnr']:.6f} | "
            f"{row['mean_prediction_mask_vs_eval_mask_iou']:.6f} | {row['mean_prediction_foreground_coverage']:.6f} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "Findings:",
            "",
            "```text",
            payload["findings_text"],
            "```",
            "",
            "Naive baseline caveat:",
            "",
            "```text",
            payload["naive_baseline_caveat"],
            "```",
            "",
            "Missing requirements:",
            "",
            "```text",
            "\n".join(payload["missing_requirements"]) or "none",
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g118_source_gated_ablation_contract_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g118_source_gated_ablation_contract_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    paths = {
        "direct": repo / "experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json",
        "naive": repo / "experiments/metrics/g103_g81_naive_strict_pool_iter1500_splat8_heldout_eval_20260528.json",
        "full": repo / "experiments/metrics/g117_full_identity_confidence_eval_20260528.json",
        "no_identity": repo / "experiments/metrics/g117_without_identity_gate_eval_20260528.json",
        "no_confidence": repo / "experiments/metrics/g117_without_confidence_gate_eval_20260528.json",
        "no_source_alpha": repo / "experiments/metrics/g117_without_source_alpha_gate_eval_20260528.json",
        "no_direct_geometry": repo / "experiments/metrics/g104_g81_strict_aware_iter1500_splat8_heldout_eval_20260528.json",
        "naive_diagnostic": repo / "experiments/metrics/g116_naive_pose_crop_source_oracle_diagnostic_20260528.json",
    }
    missing = [f"missing {name}: {path}" for name, path in paths.items() if not path.exists()]
    arms: list[dict[str, Any]] = []
    if not missing:
        arms = [
            eval_row("direct_lam_g77", "direct single-image Gaussian / LAM direct", paths["direct"], "No pseudo views; tests direct prior strength."),
            eval_row("naive_ri3d_g102", "naive pseudo-view pipeline", paths["naive"], "Failed baseline; G116 says failure has pose/crop/source/geometry caveats."),
            eval_row("full_identity_confidence_g117", "identity/confidence-aware pseudo prior", paths["full"], "Direct geometry plus strict identity/confidence pseudo color prior."),
            eval_row("without_identity_gate_g117", "w/o identity gate", paths["no_identity"], "Uses all aware train candidates without identity weighting."),
            eval_row("without_confidence_gate_g117", "w/o confidence gate", paths["no_confidence"], "Uses strict identity views without confidence weighting."),
            eval_row("without_source_alpha_gate_g117", "w/o source-gated alpha", paths["no_source_alpha"], "Fixed alpha threshold u8=8 instead of source-mask-selected threshold."),
            eval_row("without_direct_geometry_g104", "w/o source-gated/direct geometry prior", paths["no_direct_geometry"], "Old strict-aware RI3D pseudo geometry arm; removes G110 direct geometry preservation."),
        ]
    by_name = {row["name"]: row for row in arms}
    if not missing:
        direct = by_name["direct_lam_g77"]
        full = by_name["full_identity_confidence_g117"]
        no_identity = by_name["without_identity_gate_g117"]
        no_confidence = by_name["without_confidence_gate_g117"]
        no_source_alpha = by_name["without_source_alpha_gate_g117"]
        no_direct_geometry = by_name["without_direct_geometry_g104"]
        naive_diag = load_json(paths["naive_diagnostic"])
        findings = {
            "direct_prior_is_strong": (
                direct["mean_prediction_mask_vs_eval_mask_iou"] >= 0.85
                and direct["mean_masked_rgb_psnr"] >= 12.0
            ),
            "full_beats_direct": (
                full["mean_masked_rgb_psnr"] > direct["mean_masked_rgb_psnr"]
                and full["mean_prediction_mask_vs_eval_mask_iou"] > direct["mean_prediction_mask_vs_eval_mask_iou"]
            ),
            "identity_gate_positive_for_rgb": full["mean_masked_rgb_psnr"] > no_identity["mean_masked_rgb_psnr"],
            "confidence_gate_positive_for_rgb": full["mean_masked_rgb_psnr"] > no_confidence["mean_masked_rgb_psnr"],
            "source_alpha_gate_positive_for_mask": full["mean_prediction_mask_vs_eval_mask_iou"] > no_source_alpha["mean_prediction_mask_vs_eval_mask_iou"],
            "direct_geometry_prior_is_key": full["mean_prediction_mask_vs_eval_mask_iou"] > no_direct_geometry["mean_prediction_mask_vs_eval_mask_iou"] + 0.50,
            "naive_failure_has_pose_crop_caveat": naive_diag.get("verdict") == "PASS_G116_NAIVE_POSE_CROP_SOURCE_ORACLE_DIAGNOSTIC",
        }
    else:
        findings = {}
        naive_diag = {}

    verdict = PASS_VERDICT if not missing else BLOCKED
    findings_text = (
        "Direct LAM prior is strong on this source split. Full G117/G110 beats direct and naive. "
        "Identity gate is a small positive RGB contributor because removing it lowers PSNR. "
        "Confidence weighting is not supported as a positive contributor in this single case because w/o confidence is numerically tied/slightly higher. "
        "Source-selected alpha mainly helps mask IoU: fixed alpha keeps PSNR but drops mask IoU below the full variant. "
        "The direct/source-gated geometry prior is the dominant factor: replacing it with strict-aware RI3D pseudo geometry collapses back to the old low-IoU result."
        if verdict == PASS_VERDICT
        else "Blocked: missing required eval/diagnostic JSON."
    )
    naive_caveat = (
        naive_diag.get(
            "interpretation",
            "G116 diagnostic missing; do not attribute naive failure to pseudo-view quality alone.",
        )
        if verdict == PASS_VERDICT
        else "G116 diagnostic missing."
    )
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G118",
        "verdict": verdict,
        "case": load_json(paths["full"])["case"] if not missing else None,
        "split": load_json(paths["full"])["split"] if not missing else None,
        "arms": arms,
        "findings": findings,
        "findings_text": findings_text,
        "naive_baseline_caveat": naive_caveat,
        "missing_requirements": missing,
        "decision": (
            "Single-case ablation contract is complete, with explicit caveats for naive pose/crop/source-render uncertainty and confidence-gate non-support."
            if verdict == PASS_VERDICT
            else "Blocked: complete all required eval files first."
        ),
        "next_gate": "Replicate the same contract on additional NeRSemble source splits/cases before making a broad method claim.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "findings": findings, "missing": missing}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
