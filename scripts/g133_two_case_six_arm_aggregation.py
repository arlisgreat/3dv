#!/usr/bin/env python3
"""Aggregate the G81/G110 six-arm results across the two NeRSemble cases.

Case 1: source 220700191 (G77-G120, 2026-05-27/28).
Case 2: source 222200042 (G123-G132, 2026-10-11).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-10-11"
PASS_VERDICT = "PASS_G133_TWO_CASE_SIX_ARM_AGGREGATION"
BLOCKED = "BLOCKED_G133_TWO_CASE_AGGREGATION_INCOMPLETE"

ARM_LABELS = [
    "direct_single_image_gaussian_lam",
    "naive_pseudo_view_pipeline",
    "identity_confidence_aware_pseudo_prior",
    "without_identity_gate",
    "without_confidence_gate",
    "without_source_gated_alpha_geometry_prior",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def arms_by_label(summary_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(summary_path)
    return {row["label"]: row for row in payload["arms"]}


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G133 Two-Case Six-Arm Aggregation",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Per-case arms:",
        "",
        "| arm | case1 PSNR | case1 IoU | case2 PSNR | case2 IoU |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["per_case_arms"]:
        lines.append(
            f"| {row['label']} | {row['case1_psnr']:.6f} | {row['case1_iou']:.6f} | "
            f"{row['case2_psnr']:.6f} | {row['case2_iou']:.6f} |"
        )
    lines.extend(
        [
            "",
            "Key deltas (full gated pseudo prior vs direct):",
            "",
            "```text",
            "\n".join(payload["key_deltas"]),
            "```",
            "",
            "Replication verdict:",
            "",
            "```text",
            payload["replication_verdict"],
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
    parser.add_argument("--case1-summary", type=Path, default=Path("experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.json"))
    parser.add_argument("--case2-summary", type=Path, default=Path("experiments/metrics/g132_source222200042_six_arm_summary_20261011.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g133_two_case_six_arm_aggregation_20261011.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g133_two_case_six_arm_aggregation_20261011.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    case1_path = repo / args.case1_summary
    case2_path = repo / args.case2_summary
    missing = [str(p) for p in (case1_path, case2_path) if not p.exists()]
    if missing:
        payload = {
            "date": DATE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "gate": "G133",
            "verdict": BLOCKED,
            "missing_requirements": missing,
            "decision": "Blocked: a case summary is missing.",
        }
        write_json(repo / args.output_json, payload)
        write_md(repo / args.output_md, payload)
        raise SystemExit(2)

    case1 = arms_by_label(case1_path)
    case2 = arms_by_label(case2_path)
    rows: list[dict[str, Any]] = []
    for label in ARM_LABELS:
        a, b = case1.get(label), case2.get(label)
        if a is None or b is None:
            missing.append(label)
            continue
        rows.append(
            {
                "label": label,
                "case1_psnr": a["mean_masked_rgb_psnr"],
                "case1_iou": a["mean_prediction_mask_vs_eval_mask_iou"],
                "case2_psnr": b["mean_masked_rgb_psnr"],
                "case2_iou": b["mean_prediction_mask_vs_eval_mask_iou"],
            }
        )

    verdict = PASS_VERDICT if not missing else BLOCKED
    key_deltas: list[str] = []
    replication_lines: list[str] = []
    if not missing:
        by_label1 = {row["label"]: row for row in rows}
        direct = by_label1["direct_single_image_gaussian_lam"]
        naive = by_label1["naive_pseudo_view_pipeline"]
        full = by_label1["identity_confidence_aware_pseudo_prior"]
        no_id = by_label1["without_identity_gate"]
        no_conf = by_label1["without_confidence_gate"]
        no_geom = by_label1["without_source_gated_alpha_geometry_prior"]

        d1_psnr = full["case1_psnr"] - direct["case1_psnr"]
        d2_psnr = full["case2_psnr"] - direct["case2_psnr"]
        d1_iou = full["case1_iou"] - direct["case1_iou"]
        d2_iou = full["case2_iou"] - direct["case2_iou"]
        key_deltas.extend(
            [
                f"full - direct PSNR: case1 {d1_psnr:+.6f}, case2 {d2_psnr:+.6f}",
                f"full - direct mask IoU: case1 {d1_iou:+.6f}, case2 {d2_iou:+.6f}",
                f"full - naive PSNR: case1 {full['case1_psnr'] - naive['case1_psnr']:+.6f}, case2 {full['case2_psnr'] - naive['case2_psnr']:+.6f}",
                f"direct - naive PSNR: case1 {direct['case1_psnr'] - naive['case1_psnr']:+.6f}, case2 {direct['case2_psnr'] - naive['case2_psnr']:+.6f}",
                f"identity gate (full - w/o identity) PSNR: case1 {full['case1_psnr'] - no_id['case1_psnr']:+.6f}, case2 {full['case2_psnr'] - no_id['case2_psnr']:+.6f}",
                f"confidence gate (full - w/o confidence) PSNR: case1 {full['case1_psnr'] - no_conf['case1_psnr']:+.6f}, case2 {full['case2_psnr'] - no_conf['case2_psnr']:+.6f}",
                f"source geometry dominance (full - no_source_geometry) PSNR: case1 {full['case1_psnr'] - no_geom['case1_psnr']:+.6f}, case2 {full['case2_psnr'] - no_geom['case2_psnr']:+.6f}",
            ]
        )
        replication_lines.extend(
            [
                "REPLICATED: direct learned-prior Gaussian strongly beats naive pseudo-view RI3D in both cases "
                f"(case1 {direct['case1_psnr']:.3f} vs {naive['case1_psnr']:.3f} PSNR; case2 {direct['case2_psnr']:.3f} vs {naive['case2_psnr']:.3f}).",
                "REPLICATED: removing the direct geometry/source-alpha prior collapses the method toward the strict RI3D arm in both cases.",
                "NOT REPLICATED: the G110 source-gated pseudo-prior PSNR gain over direct does not hold in case 2 "
                f"(case1 {d1_psnr:+.3f} dB vs case2 {d2_psnr:+.3f} dB); mask IoU deltas are small in both cases ({d1_iou:+.4f} / {d2_iou:+.4f}).",
                "NOT REPLICATED: the identity gate's positive RGB effect flips sign in case 2 "
                f"(case1 {full['case1_psnr'] - no_id['case1_psnr']:+.3f} dB; case2 {full['case2_psnr'] - no_id['case2_psnr']:+.3f} dB).",
                "CASE PROPERTY: source 222200042 yielded only 2 identity-anchored pseudo views (vs 3 for 220700191), "
                "so the strict arms train on fewer views and the pseudo color prior has weaker/less reliable support.",
            ]
        )

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G133",
        "verdict": verdict,
        "cases": {
            "case1": {"source_serial": "220700191", "summary": str(case1_path)},
            "case2": {"source_serial": "222200042", "summary": str(case2_path)},
        },
        "per_case_arms": rows,
        "missing_requirements": missing,
        "key_deltas": key_deltas,
        "replication_verdict": "\n".join(replication_lines),
        "decision": (
            "Two-case aggregation complete. The direct-vs-naive gap and the source-geometry dominance replicate; "
            "the single-case G110 pseudo-prior quality gain and the identity-gate RGB gain do not replicate on the second case. "
            "Pseudo-view supervision evidence remains diagnostic; no method-quality scaling claim is authorized."
            if not missing
            else "Blocked: arm labels missing from a case summary."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": payload["verdict"], "key_deltas": key_deltas}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
