#!/usr/bin/env python3
"""Open the learned-prior/head-anchored Gaussian route under real-GT gates.

This gate is deliberately conservative. It authorizes only local smoke tests or
repo-safe positive controls until a method can render camera-aligned held-out
views or export geometry for GT evaluation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
PASS_VERDICT = "PASS_REAL_GT_DATA_VLM_METHOD_GATE_LOCAL_ONLY"
BLOCKED_VERDICT = "BLOCKED_LEARNED_PRIOR_METHOD_GATE"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path_exists(repo: Path, value: str) -> bool:
    return (repo / value).exists()


def first_case(real_gt_manifest: dict[str, Any]) -> dict[str, Any]:
    cases = real_gt_manifest.get("benchmark_cases") or []
    if cases and isinstance(cases[0], dict):
        return cases[0]
    return {}


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G39 Learned-Prior / Feed-Forward / Head-Anchored Gaussian Method Gate",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Application alignment:",
        "",
        "```text",
        payload["application_alignment"],
        "```",
        "",
        "Method positioning:",
        "",
        "| item | status | implication |",
        "| --- | --- | --- |",
    ]
    for item in payload["method_positioning"]:
        lines.append(f"| {item['item']} | {item['status']} | {item['implication']} |")
    lines.extend(
        [
            "",
            "Gate checks:",
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
            "Distribution statement:",
            "",
            "```text",
            payload["distribution_statement"],
            "```",
            "",
            "Authorized next experiments:",
            "",
            "```text",
            "\n".join(payload["authorized_next_experiments"]),
            "```",
            "",
            "Blocked actions:",
            "",
            "```text",
            "\n".join(payload["blocked_actions"]),
            "```",
            "",
            "Literature anchors:",
            "",
            "| work | date | source | signal |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload["literature_anchors"]:
        lines.append(f"| {item['work']} | {item['date']} | {item['source']} | {item['signal']} |")
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
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g39_learned_prior_method_gate_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g39_learned_prior_method_gate_20260520.md"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    real_gt_manifest = load_json(repo / "experiments/real_gt_benchmark/data_audit.json", {})
    g21_debug = load_json(repo / "experiments/metrics/g21_multiface_debug_gate_20260520.json", {})
    g36 = load_json(repo / "experiments/metrics/g36_method_redesign_direction_20260520.json", {})
    g37 = load_json(repo / "experiments/metrics/g37_model_data_distribution_audit_20260520.json", {})
    g38 = load_json(repo / "experiments/metrics/g38_artifact_sync_gate_20260520.json", {})
    case = first_case(real_gt_manifest)

    lam_files = {
        "lam_weights": "external/LAM/model_zoo/lam_models/releases/lam/lam-20k/step_045500/model.safetensors",
        "lam_config": "external/LAM/configs/inference/lam-20k-8gpu.yaml",
        "lam_flame_template": "external/LAM/model_zoo/human_parametric_models/flame_vhap/head_template_mesh.obj",
        "lam_runner": "scripts/server/03_run_lam_sample.sh",
    }
    lam_ready = all(path_exists(repo, value) for value in lam_files.values())

    checks = {
        "real_gt_case_status": case.get("status") == "PASS_REAL_GT_BENCHMARK",
        "real_gt_view_count_6_to_12": 6 <= int(case.get("view_count", 0) or 0) <= 12,
        "g21_vlm_manual_gate_passed": g21_debug.get("verdict") == "PASS_REAL_GT_BENCHMARK",
        "g36_method_redesign_gate_passed": g36.get("verdict") == "PASS_METHOD_REDESIGN_DIRECTION_NO_LONGER_RI3D_SCALING",
        "g37_distribution_audit_passed": g37.get("verdict") == "PASS_DISTRIBUTION_AUDIT_NO_NEW_QUALITY_CLAIM",
        "g38_artifact_sync_gate_passed": g38.get("verdict") == "PASS_ARTIFACT_SYNC_GATE_READY",
        "lam_feed_forward_baseline_available_locally": lam_ready,
        "pseudo_view_training_blocked": True,
        "private_multiface_media_export_blocked": True,
    }
    verdict = PASS_VERDICT if all(checks.values()) else BLOCKED_VERDICT

    payload = {
        "date": DATE,
        "gate": "G39",
        "verdict": verdict,
        "premise": (
            "The next credible method route is learned-prior / feed-forward / head-anchored Gaussian head "
            "reconstruction, not longer RI3D optimization over pseudo-view candidates."
        ),
        "application_alignment": (
            "The application proposal targets single-image full-head modeling by replacing PanoHead's NeRF "
            "rendering with Gaussian representation, using diffusion only as an audited prior for invisible "
            "regions, using Transformer-style consistency, and anchoring geometry with FLAME/FaceVerse/3DMM."
        ),
        "checks": checks,
        "case_summary": {
            "dataset": case.get("dataset"),
            "case_id": case.get("case_id"),
            "view_count": case.get("view_count"),
            "license": case.get("license"),
            "privacy_status": case.get("privacy_status"),
            "repo_policy": case.get("repo_policy"),
        },
        "lam_files": lam_files,
        "method_positioning": [
            {
                "item": "LAM-20K",
                "status": "local_runnable_feed_forward_head_anchored_gaussian_baseline",
                "implication": (
                    "Use only as a baseline/smoke until camera-aligned held-out rendering or geometry export is "
                    "available; LAM uses FLAME canonical points as Transformer queries for Gaussian attributes."
                ),
            },
            {
                "item": "PanoLAM / OMEGA / FFAvatar / Any3DAvatar",
                "status": "latest_method_direction_not_locally_integrated",
                "implication": (
                    "They define the correct scientific direction: feed-forward full-head priors, FLAME/UV or "
                    "structured Gaussian scaffolds, dense multi-view supervision, and benchmark metrics."
                ),
            },
            {
                "item": "RI3D G21-G33",
                "status": "closed_numerical_plumbing_route",
                "implication": "Keep as diagnostic evidence only; do not scale training without a new method premise.",
            },
            {
                "item": "Zero123++ downstream candidate pools",
                "status": "diagnostic_candidate_pool_only",
                "implication": "May inform failure taxonomy or conditional priors after VLM audit, never GT training views.",
            },
        ],
        "distribution_statement": (
            "LAM-20K is documented as trained on VFHQ + NeRSemble. The current real-GT case is Multiface: "
            "a nearby multi-view head-capture domain but not proven in-distribution for the released LAM weights. "
            "Therefore LAM-on-Multiface can be interpreted only as local qualitative or plumbing evidence unless "
            "we obtain camera-aligned render/geometry outputs and compare against held-out views/GT geometry."
        ),
        "authorized_next_experiments": [
            "G40a: optional local-only LAM smoke on one Multiface train view; record command, hashes, timing, and manual/VLM notes only; no identifiable media sync.",
            "G40b: repo-safe LAM smoke on the CC0 synthetic positive-control front view; sync MP4/PNG/JSON/MD, but label it positive-control only.",
            "G41: design a true head-anchored Gaussian scaffold/adapter that can render held-out cameras or export mesh/point-cloud for GT metrics before any quality claim.",
        ],
        "blocked_actions": [
            "Do not train or evaluate reconstruction quality on experiments/downstream_datasets.",
            "Do not use Multiface GT mesh as input to a single-image method; it is evaluation geometry only.",
            "Do not publish identifiable Multiface RGB, generated avatar videos, meshes, or textured assets without artifact/privacy review.",
            "Do not claim learned-prior quality from LAM videos alone; require held-out camera-aligned metrics or geometry metrics.",
            "Do not restart longer RI3D training from G33 as a method milestone.",
        ],
        "literature_anchors": [
            {
                "work": "LAM",
                "date": "2025-02-25 / revised 2025-04-04",
                "source": "https://arxiv.org/abs/2502.17796",
                "signal": "Single-forward-pass Gaussian head; FLAME canonical points query Transformer image features.",
            },
            {
                "work": "PanoLAM",
                "date": "2025-09-09 / revised 2025-10-10",
                "source": "https://arxiv.org/abs/2509.07552",
                "signal": "One-shot full-head Gaussian synthesis; FLAME sparse points plus transformer, synthetic 3D-GAN priors.",
            },
            {
                "work": "SEGA",
                "date": "2025-04-19 / revised 2026-03-11",
                "source": "https://arxiv.org/abs/2504.14373",
                "signal": "Single-image drivable Gaussian head avatar with FLAME-based hierarchical UV Gaussian splatting.",
            },
            {
                "work": "OMEGA-Avatar",
                "date": "2026-02-12",
                "source": "https://arxiv.org/abs/2602.11693",
                "signal": "Feed-forward 360 full-head animatable Gaussian avatar with semantic-aware mesh deformation and UV fusion.",
            },
            {
                "work": "Any3DAvatar",
                "date": "2026-04-15",
                "source": "https://arxiv.org/abs/2604.13856",
                "signal": "Structured Plucker-aware Gaussian scaffold and one-step conditional denoising for single-image full-head reconstruction.",
            },
            {
                "work": "MeshLAM",
                "date": "2026-04-23",
                "source": "https://arxiv.org/abs/2604.22865",
                "signal": "Feed-forward one-shot animatable mesh head; useful successor signal for topology and texture anchoring.",
            },
            {
                "work": "FFAvatar",
                "date": "2026-05-14",
                "source": "https://arxiv.org/abs/2605.15320",
                "signal": "Few-shot feed-forward Gaussian head reconstruction with multi-view fusion, FLAME prediction, and NeRSemble metrics.",
            },
        ],
        "decision": (
            "Open G40 only as gated learned-prior smoke/positive-control work. The real-GT/data/VLM premise is "
            "satisfied locally, but model-quality claims remain blocked until a head-anchored method produces "
            "held-out camera-aligned renders or GT geometry metrics."
        ),
    }

    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
