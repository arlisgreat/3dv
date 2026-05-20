#!/usr/bin/env python3
"""Audit whether current model/test pairs are interpretable.

This gate prevents a repeat of the earlier mistake where pseudo-view candidate
pools were treated as if they were validated reconstruction data. It records
which results can be analyzed, which are diagnostic only, and what distribution
statement is required before any next method run.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
PASS_VERDICT = "PASS_DISTRIBUTION_AUDIT_NO_NEW_QUALITY_CLAIM"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G37 Model/Data Distribution Audit",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Question:",
        "",
        "```text",
        "Are the models and test data close enough to the model/input premise that results can be interpreted?",
        "```",
        "",
        "Audit table:",
        "",
        "| route | data | distribution verdict | interpretation |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["routes"]:
        lines.append(
            "| {route} | {data} | {verdict} | {interpretation} |".format(
                route=row["route"],
                data=row["data"],
                verdict=row["distribution_verdict"],
                interpretation=row["interpretation"],
            )
        )
    lines.extend(
        [
            "",
            "Mandatory rule for the next milestone:",
            "",
            "```text",
            payload["next_milestone_rule"],
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
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g37_model_data_distribution_audit_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g37_model_data_distribution_audit_20260520.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    first10_rows = read_csv(repo / "data_manifest.csv")
    lam_summary = load_json(repo / "experiments/reconstructions/lam_first10/summary.json", [])
    real_gt = load_json(repo / "experiments/real_gt_benchmark/data_audit.json", {})
    g33 = load_json(repo / "experiments/metrics/g33_combined_guarded_train10_eval_20260520.json", {})
    g36 = load_json(repo / "experiments/metrics/g36_method_redesign_direction_20260520.json", {})

    lam_success = sum(1 for item in lam_summary if item.get("status") in {"success", "skipped"})
    real_gt_case = (real_gt.get("benchmark_cases") or [{}])[0]
    g33_metrics = g33.get("heldout_eval_metrics", g33.get("heldout_metrics", {}))

    routes = [
        {
            "route": "LAM first10 qualitative baseline",
            "data": f"{len(first10_rows)} web portraits, no GT cameras/mesh",
            "distribution_verdict": "IN_INPUT_FORM_BUT_NO_GT",
            "interpretation": (
                f"{lam_success}/{len(lam_summary)} LAM runs produced MP4s. This is a qualitative one-shot "
                "portrait baseline only; there is no held-out real-GT metric on first10."
            ),
        },
        {
            "route": "Zero123++ pseudo-view candidate pools",
            "data": "experiments/downstream_datasets/*",
            "distribution_verdict": "OUT_OF_RECONSTRUCTION_GT_DISTRIBUTION",
            "interpretation": (
                "Generated views are candidate priors with known identity/geometry/grid failures. They cannot be "
                "used as train/test data for a reconstruction-quality claim."
            ),
        },
        {
            "route": "RI3D on old pseudo-view exports",
            "data": "experiments/ri3d_datasets/first2*",
            "distribution_verdict": "MISMATCHED_INPUT_PREMISE",
            "interpretation": (
                "RI3D assumes coherent sparse views of a scene. Historical exports came from generated candidate "
                "views and are downgraded to diagnostic artifact/failure evidence."
            ),
        },
        {
            "route": "RI3D G21-G33 Multiface local compact case",
            "data": f"{real_gt_case.get('view_count', 0)} real captured views, cameras, masks, local mesh",
            "distribution_verdict": "REAL_GT_PREMISE_PASS_BUT_METHOD_QUALITY_NOT_SUPPORTED",
            "interpretation": (
                "The data premise is valid for local held-out benchmark plumbing. G33 held-out metrics remain "
                f"init-level ({g33_metrics or 'see g33 report'}), so results are numerical/plumbing evidence, not a "
                "method-quality win."
            ),
        },
        {
            "route": "Next learned-prior/feed-forward head method",
            "data": "LAM/PanoLAM/OMEGA/FFAvatar-style model on Multiface/H3DS/FaceScape/NeRSemble-style real GT",
            "distribution_verdict": "CONDITIONAL_ON_EXPLICIT_IN_OR_OUT_DISTRIBUTION_STATEMENT",
            "interpretation": (
                "Before running, record the model training/evaluation distribution, whether Multiface/H3DS/"
                "FaceScape/NeRSemble is in-distribution, and which held-out views/geometry metrics are used."
            ),
        },
    ]
    payload = {
        "date": DATE,
        "gate": "G37",
        "verdict": PASS_VERDICT,
        "inputs": {
            "first10_count": len(first10_rows),
            "lam_summary_count": len(lam_summary),
            "real_gt_manifest_verdict": real_gt.get("verdict"),
            "g33_verdict": g33.get("verdict"),
            "g36_verdict": g36.get("verdict"),
        },
        "routes": routes,
        "next_milestone_rule": (
            "Every method milestone must declare model training/evaluation distribution, test benchmark "
            "source, in/out-of-distribution status, held-out split, and visual/VLM gate before GPU work."
        ),
        "decision": (
            "Current results can be analyzed as qualitative baseline, diagnostic pseudo-view failure evidence, "
            "or real-GT plumbing/numerical smoke only. No existing result supports a reconstruction-quality claim."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(PASS_VERDICT)


if __name__ == "__main__":
    main()
