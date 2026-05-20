#!/usr/bin/env python3
"""Record the evaluation contract for learned-prior/head-anchored methods."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
VERDICT = "PASS_EVAL_CONTRACT_BLOCK_QUALITY_UNTIL_CAMERA_ALIGNED_EXPORT"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G41 Learned-Prior Evaluation Contract",
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
        payload["question"],
        "```",
        "",
        "Current LAM wrapper status:",
        "",
        "| item | value |",
        "| --- | --- |",
    ]
    for key, value in payload["current_lam_wrapper_status"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "Required outputs before any learned-prior quality claim:",
            "",
            "```text",
            "\n".join(payload["required_outputs_before_quality_claim"]),
            "```",
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
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g41_learned_prior_eval_contract_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g41_learned_prior_eval_contract_20260520.md"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    g39 = load_json(repo / "experiments/metrics/g39_learned_prior_method_gate_20260520.json", {})
    g40 = load_json(repo / "experiments/metrics/g40_learned_prior_lam_smoke_20260520.json", {})
    runner = repo / "scripts/server/03_run_lam_sample.sh"
    runner_text = runner.read_text(encoding="utf-8") if runner.is_file() else ""

    payload = {
        "date": DATE,
        "gate": "G41",
        "verdict": VERDICT,
        "question": (
            "Can the current learned-prior smoke be interpreted as reconstruction quality on the real-GT benchmark?"
        ),
        "inputs": {
            "g39_verdict": g39.get("verdict"),
            "g40_verdict": g40.get("verdict"),
        },
        "current_lam_wrapper_status": {
            "exports_animation_mp4": "true",
            "save_ply_enabled": "save_ply=true" in runner_text,
            "save_img_enabled": "save_img=true" in runner_text,
            "camera_aligned_multiface_render_available": "false",
            "heldout_metrics_available": "false",
            "geometry_metric_available": "false",
            "privacy_safe_media_sync": "false_for_multiface_identifiable_outputs",
        },
        "required_outputs_before_quality_claim": [
            "Render the predicted Gaussian/head representation under held-out Multiface K/R/T cameras.",
            "Compute held-out PSNR/SSIM/LPIPS against masked real GT views without using held-out images for supervision.",
            "Export or sample a geometry representation and compare to GT mesh/point cloud with scale/alignment recorded.",
            "Keep Multiface identifiable RGB/video/mesh artifacts local unless explicit artifact/privacy review approves sync.",
            "Record model training distribution and whether the benchmark is in-domain, near-domain, or out-of-domain.",
            "Run manual/VLM visual audit on private contact sheets before interpreting metrics.",
        ],
        "blocked_interpretations": [
            "A LAM animation MP4 is not a held-out reconstruction metric.",
            "A successful face tracker/FLAME fitting stage is not proof of 360 geometry quality.",
            "CC0 positive-control failure in LAM does not invalidate the CC0 geometry gate; it only blocks LAM input-distribution use.",
            "No pseudo-view candidate pool can be promoted into training/evaluation data from this smoke.",
        ],
        "decision": (
            "G41 closes the current learned-prior smoke loop: execution is proven locally, but quality evaluation is "
            "blocked until camera-aligned render or geometry export is integrated. The next milestone should be a "
            "method/adapter implementation milestone, not more ungated MP4 generation."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])


if __name__ == "__main__":
    main()
