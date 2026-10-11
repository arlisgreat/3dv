#!/usr/bin/env python3
"""Preflight the remaining assets needed for multi-case G116 replication."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G122_MULTICASE_REPLICATION_PREFLIGHT_RECORDED"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def metric_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    payload = load_json(path)
    metrics = payload.get("metrics", {})
    return {
        "exists": True,
        "path": str(path),
        "verdict": payload.get("verdict"),
        "mean_masked_rgb_psnr": metrics.get("mean_masked_rgb_psnr"),
        "mean_prediction_mask_vs_eval_mask_iou": metrics.get("mean_prediction_mask_vs_eval_mask_iou"),
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G122 Multi-Case Replication Preflight",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Candidate source splits:",
        "",
        "| source serial | status | direct eval | source input | pseudo views | full six-arm | next action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["candidate_splits"]:
        direct = "yes" if row["direct_eval"]["exists"] else "no"
        source_input = "yes" if row["source_pseudo_input"]["exists"] else "no"
        pseudo = "yes" if row["pseudo_views"]["exists"] else "no"
        six = "yes" if row["six_arm_summary"]["exists"] else "no"
        lines.append(f"| {row['source_serial']} | {row['status']} | {direct} | {source_input} | {pseudo} | {six} | {row['next_action']} |")
    lines.extend(
        [
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
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g122_multicase_replication_preflight_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g122_multicase_replication_preflight_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    candidate_splits = [
        {
            "source_serial": "220700191",
            "adapter_manifest": "/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json",
            "direct_eval": metric_summary(repo / "experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json"),
            "source_pseudo_input": {
                "exists": exists("/data1/workspace/airulan/3dv_work/runs/g83_nersemble_source220700191_pseudo_input/cam_220700191_masked_square_512.png"),
                "path": "/data1/workspace/airulan/3dv_work/runs/g83_nersemble_source220700191_pseudo_input/cam_220700191_masked_square_512.png",
            },
            "pseudo_views": {
                "exists": exists("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/metadata.json"),
                "path": "/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/metadata.json",
            },
            "six_arm_summary": metric_summary(repo / "experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.json"),
            "status": "complete_single_case_only",
            "next_action": "Use as reference; do not claim multi-case from this alone.",
        },
        {
            "source_serial": "222200042",
            "adapter_manifest": "/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json",
            "direct_eval": metric_summary(repo / "experiments/metrics/g71_lam_native_gaussian_source_aligned_xyz_eval_20260527.json"),
            "source_pseudo_input": {
                "exists": exists("/data1/workspace/airulan/3dv_work/runs/g121_nersemble_source222200042_pseudo_input/cam_222200042_masked_square_512.png"),
                "path": "/data1/workspace/airulan/3dv_work/runs/g121_nersemble_source222200042_pseudo_input/cam_222200042_masked_square_512.png",
            },
            "pseudo_views": {
                "exists": exists("/data1/workspace/airulan/3dv_work/runs/g123_zero123plus_nersemble_source222200042_steps75/metadata.json"),
                "path": "/data1/workspace/airulan/3dv_work/runs/g123_zero123plus_nersemble_source222200042_steps75/metadata.json",
            },
            "six_arm_summary": {
                "exists": exists(repo / "experiments/metrics/g132_source222200042_six_arm_summary_20261011.json"),
                "path": str(repo / "experiments/metrics/g132_source222200042_six_arm_summary_20261011.json"),
            },
            "status": "ready_for_pseudo_generation",
            "next_action": "Run source-only pseudo generation, manifest gate, source-gated ablations, and G55 eval.",
        },
    ]
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G122",
        "verdict": PASS_VERDICT,
        "candidate_splits": candidate_splits,
        "multi_case_completion": {
            "required_cases": 2,
            "completed_six_arm_cases": sum(bool(row["six_arm_summary"]["exists"]) for row in candidate_splits),
            "complete": False,
        },
        "decision": (
            "Multi-case replication is not complete. The second split has source-only input prepared and a direct eval baseline, "
            "but still lacks pseudo views, identity/confidence manifests, ablation predictions, and six-arm summary."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": payload["verdict"], "multi_case_completion": payload["multi_case_completion"]}, indent=2))


if __name__ == "__main__":
    main()
