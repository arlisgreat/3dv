#!/usr/bin/env python3
"""Summarize G40 learned-prior LAM smoke runs without syncing private media."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
VERDICT = "PASS_LOCAL_LEARNED_PRIOR_SMOKE_NO_QUALITY_CLAIM"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "basename": path.name,
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256(path) if path.is_file() else "",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G40 Learned-Prior LAM Smoke",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Purpose:",
        "",
        "```text",
        payload["purpose"],
        "```",
        "",
        "G40a Multiface local-only smoke:",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in payload["g40a_multiface_local_smoke"].items():
        if key == "private_outputs":
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "Private output hashes:",
            "",
            "| basename | size_bytes | sha256 |",
            "| --- | ---: | --- |",
        ]
    )
    for item in payload["g40a_multiface_local_smoke"]["private_outputs"]:
        lines.append(f"| {item['basename']} | {item['size_bytes']} | {item['sha256']} |")
    lines.extend(
        [
            "",
            "Manual/VLM-style visual audit:",
            "",
            "```text",
            payload["g40a_multiface_local_smoke"]["manual_visual_audit"],
            "```",
            "",
            "G40b CC0 positive-control LAM smoke:",
            "",
            "| field | value |",
            "| --- | --- |",
        ]
    )
    for key, value in payload["g40b_cc0_positive_control_smoke"].items():
        lines.append(f"| {key} | {value} |")
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
    parser.add_argument(
        "--private-run-root",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/runs/g40a_lam_multiface_local_20260520"),
    )
    parser.add_argument(
        "--input-image",
        type=Path,
        default=Path(
            "/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view/views/400017_000102.png"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g40_learned_prior_lam_smoke_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g40_learned_prior_lam_smoke_20260520.md"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    private_root = args.private_run_root
    video = private_root / "videos/400017_000102.mp4"
    audio_video = private_root / "videos/400017_000102_audio.mp4"
    audit_sheet = private_root / "g40a_private_video_audit_sheet.png"
    patch_file = repo / "patches/lam/torch26_vgghead_torchscript_load.patch"

    outputs = [file_record(video), file_record(audio_video), file_record(audit_sheet)]
    success = video.is_file() and audio_video.is_file()
    payload = {
        "date": DATE,
        "gate": "G40",
        "verdict": VERDICT if success else "BLOCKED_LOCAL_LEARNED_PRIOR_SMOKE",
        "purpose": (
            "Run the first learned-prior/feed-forward/head-anchored Gaussian smoke after G39, while keeping "
            "real-GT privacy and distribution limits explicit."
        ),
        "g40a_multiface_local_smoke": {
            "status": "success_local_only" if success else "missing_private_outputs",
            "model": "LAM-20K",
            "model_family": "feed_forward_head_anchored_gaussian",
            "input": "Multiface debug E001 frame 000102 camera 400017 train view",
            "input_sha256": sha256(args.input_image) if args.input_image.is_file() else "",
            "gpu": "CUDA_VISIBLE_DEVICES=1",
            "command": (
                "bash scripts/server/03_run_lam_sample.sh <private_multiface_rgb> "
                "configs/inference/lam-20k-8gpu.yaml "
                "model_zoo/lam_models/releases/lam/lam-20k/step_045500/ "
                "assets/sample_motion/export/Look_In_My_Eyes/"
            ),
            "environment_patch": "patches/lam/torch26_vgghead_torchscript_load.patch",
            "environment_patch_exists": patch_file.is_file(),
            "artifact_policy": "private media moved to 3dv_work; repo sync includes hashes/metrics only",
            "private_outputs": outputs,
            "manual_visual_audit": (
                "PASS_LOCAL_SMOKE_ONLY. The private contact sheet shows a coherent animatable head across frames, "
                "but with visible green color cast, soft/blurred shoulder-neck support, and no held-out camera "
                "alignment. It is an execution/distribution smoke, not a reconstruction-quality result."
            ),
        },
        "g40b_cc0_positive_control_smoke": {
            "status": "blocked",
            "input": "experiments/gt_cases/wikimedia_blender_head_cc0/views/rgb_00_az000.png",
            "reason": (
                "The CC0 rendered point-splat head is repo-safe but outside LAM's natural portrait input "
                "distribution; LAM face tracking failed before avatar generation."
            ),
            "observed_error": "UnboundLocalError: local variable 'face_landmarks' referenced before assignment",
            "interpretation": "CC0 case remains useful for geometry/camera pipeline gates, not for LAM feed-forward input smoke.",
        },
        "decision": (
            "G40 confirms that the real-GT input can drive the available feed-forward Gaussian baseline locally, "
            "but it does not create a quality claim. Next work must build or integrate a method that can render "
            "held-out Multiface cameras or export geometry for GT metrics. Identifiable Multiface PNG/MP4 remain "
            "out of GitHub sync until explicit artifact review."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])
    if payload["verdict"] != VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
