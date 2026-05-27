#!/usr/bin/env python3
"""Gate a real method run on the audited NeRSemble split."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
GATE = "G56"
PASS_VERDICT = "PASS_NERSEMBLE_METHOD_READY_FOR_HELDOUT_EVAL"
BLOCKED_VERDICT = "BLOCKED_NERSEMBLE_METHOD_OUTPUT_CAMERA_RENDERER_MISSING"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G56 NeRSemble Method Readiness Gate",
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
        "Distribution audit:",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in payload["distribution_audit"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "Renderer/readiness checks:",
            "",
            "| check | value |",
            "| --- | --- |",
        ]
    )
    for key, value in payload["checks"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
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
    parser.add_argument("--prediction-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g56_nersemble_lam_eval/predictions"))
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g56_nersemble_method_readiness_gate_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g56_nersemble_method_readiness_gate_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    eval_serials = adapter.get("split", {}).get("local_eval_serials", [])
    expected_predictions = [args.prediction_root / f"cam_{serial}_frame_00000.png" for serial in eval_serials]
    present_predictions = [path for path in expected_predictions if path.exists()]

    required_gates = {
        "G52": load_json(repo / "experiments/metrics/g52_nersemble_download_integrity_gate_20260527.json").get("verdict"),
        "G53": load_json(repo / "experiments/metrics/g53_nersemble_compact_case_gate_20260527.json").get("verdict"),
        "G54": load_json(repo / "experiments/metrics/g54_nersemble_nvs_frame0_adapter_preflight_20260527.json").get("verdict"),
        "G55": load_json(repo / "experiments/metrics/g55_nersemble_heldout_eval_harness_smoke_20260527.json").get("verdict"),
    }
    gate_pass = all(str(value).startswith("PASS") for value in required_gates.values())
    camera_renderer_script = repo / "scripts/lam_render_nersemble_cameras.py"
    renderer_ready = camera_renderer_script.exists()
    predictions_ready = len(present_predictions) == len(expected_predictions) and bool(expected_predictions)
    verdict = PASS_VERDICT if gate_pass and renderer_ready and predictions_ready else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "Before running a learned-prior/feed-forward/head-anchored method on NeRSemble, the real-GT/data/VLM gates, "
            "model/test distribution statement, camera renderer, and held-out prediction files must all be explicit."
        ),
        "verdict": verdict,
        "required_gate_verdicts": required_gates,
        "distribution_audit": {
            "candidate_method": "LAM-20K baseline / learned-prior head-anchored Gaussian family",
            "test_data": "NeRSemble official NVS 388 GLASSES frame 0 local held-out split plus v2 017 compact visual gate",
            "training_distribution_statement": "LAM-20K is documented in prior project gates as trained on VFHQ + NeRSemble.",
            "in_distribution_status": "in-domain for NeRSemble; possible subject/dataset overlap cannot be ruled out from local metadata alone",
            "allowed_interpretation": "baseline sanity and in-distribution benchmark plumbing; not an unseen cross-dataset generalization claim",
        },
        "checks": {
            "g52_g55_required_gates_pass": gate_pass,
            "camera_renderer_script_present": renderer_ready,
            "camera_renderer_script": str(camera_renderer_script),
            "expected_eval_prediction_count": len(expected_predictions),
            "present_eval_prediction_count": len(present_predictions),
            "prediction_root": str(args.prediction_root),
            "raw_rgb_policy": "private local only under 3dv_work; commit metrics/hashes/mask-only figures unless user explicitly reviews identifiable media",
        },
        "decision": (
            "Blocked for method-quality evaluation: the data and metric gates pass, but no LAM-to-NeRSemble held-out camera renderer or prediction set is present. "
            "Do not substitute LAM motion-camera MP4s for held-out NeRSemble camera renders."
            if verdict == BLOCKED_VERDICT
            else "Ready to score method outputs on the audited NeRSemble held-out split."
        ),
        "next_gate": (
            "Implement or import a renderer that maps method output into the G54 NeRSemble camera intrinsics/extrinsics, "
            "then write predictions for each G55 eval serial and run the held-out evaluator."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
