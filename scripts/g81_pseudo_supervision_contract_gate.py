#!/usr/bin/env python3
"""Gate the G81 three-arm pseudo-supervision experiment contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-28"
PASS_READY = "PASS_G81_THREE_ARM_CONTRACT_READY"
PASS_RESULT = "PASS_G81_IDENTITY_CONFIDENCE_AWARE_PSEUDO_SUPERVISION_BEATS_BASELINES"
FAIL_RESULT = "FAIL_G81_IDENTITY_CONFIDENCE_AWARE_DOES_NOT_BEAT_BASELINES"
BLOCKED = "BLOCKED_G81_THREE_ARM_CONTRACT_INCOMPLETE"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve(path: str | None, repo: Path) -> Path | None:
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else repo / p


def prediction_files(root: Path | None, serials: list[str]) -> dict[str, Any]:
    if root is None:
        return {"present": False, "missing": serials, "files": {}}
    files = {serial: root / f"cam_{serial}_frame_00000.png" for serial in serials}
    missing = [serial for serial, path in files.items() if not path.exists()]
    return {
        "present": root.exists() and not missing,
        "root": str(root),
        "missing": missing,
        "files": {serial: str(path) for serial, path in files.items()},
    }


def eval_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"present": False}
    payload = load_json(path)
    metrics = payload.get("metrics", {})
    return {
        "present": True,
        "path": str(path),
        "verdict": payload.get("verdict"),
        "mean_masked_rgb_psnr": metrics.get("mean_masked_rgb_psnr"),
        "mean_masked_rgb_ssim_global_luma": metrics.get("mean_masked_rgb_ssim_global_luma"),
        "mean_prediction_mask_vs_eval_mask_iou": metrics.get("mean_prediction_mask_vs_eval_mask_iou"),
        "mean_prediction_foreground_coverage": metrics.get("mean_prediction_foreground_coverage"),
    }


def pseudo_manifest_summary(path: Path | None, heldout_paths: set[str]) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"present": False, "required_fields_present": False}
    payload = load_json(path)
    views = payload.get("pseudo_views", payload.get("views", []))
    required = {"identity_anchor_score", "confidence_score", "trusted_region_mask", "supervision_role"}
    missing_fields: dict[str, list[str]] = {}
    leakage_paths: list[str] = []
    for idx, view in enumerate(views):
        missing = [field for field in required if field not in view]
        if missing:
            missing_fields[str(idx)] = missing
        for key in ("image", "image_path", "source_image", "mask", "trusted_region_mask"):
            value = str(view.get(key, ""))
            if value in heldout_paths:
                leakage_paths.append(value)
    return {
        "present": True,
        "path": str(path),
        "view_count": len(views),
        "required_fields_present": not missing_fields and bool(views),
        "missing_fields": missing_fields,
        "heldout_path_leakage": sorted(set(leakage_paths)),
    }


def arm(
    name: str,
    prediction_root: Path | None,
    eval_json: Path | None,
    eval_serials: list[str],
    pseudo_manifest: Path | None,
    heldout_paths: set[str],
) -> dict[str, Any]:
    predictions = prediction_files(prediction_root, eval_serials)
    evaluation = eval_summary(eval_json)
    pseudo = pseudo_manifest_summary(pseudo_manifest, heldout_paths) if pseudo_manifest is not None else {"present": None}
    return {
        "name": name,
        "prediction_files": predictions,
        "evaluation": evaluation,
        "pseudo_manifest": pseudo,
        "ready_for_comparison": bool(predictions["present"] and evaluation["present"]),
    }


def beats(candidate: dict[str, Any], baselines: list[dict[str, Any]]) -> bool:
    c_eval = candidate["evaluation"]
    if not c_eval.get("present"):
        return False
    for base in baselines:
        b_eval = base["evaluation"]
        if not b_eval.get("present"):
            return False
        if c_eval["mean_masked_rgb_psnr"] <= b_eval["mean_masked_rgb_psnr"]:
            return False
        if c_eval["mean_prediction_mask_vs_eval_mask_iou"] <= b_eval["mean_prediction_mask_vs_eval_mask_iou"]:
            return False
    return True


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} G81 Three-Arm Pseudo-Supervision Contract",
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
        "Arms:",
        "",
        "| arm | predictions | eval | pseudo manifest | PSNR | mask IoU | ready |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["arms"]:
        ev = row["evaluation"]
        lines.append(
            f"| {row['name']} | {row['prediction_files']['present']} | {ev.get('present')} | "
            f"{row['pseudo_manifest'].get('present')} | {ev.get('mean_masked_rgb_psnr', 'NA')} | "
            f"{ev.get('mean_prediction_mask_vs_eval_mask_iou', 'NA')} | {row['ready_for_comparison']} |"
        )
    lines.extend(
        [
            "",
            "Missing Requirements:",
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
    parser.add_argument(
        "--adapter-manifest",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"),
    )
    parser.add_argument("--direct-prediction-root", default="/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/predictions")
    parser.add_argument("--direct-eval-json", default="experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json")
    parser.add_argument("--naive-prediction-root", default="")
    parser.add_argument("--naive-eval-json", default="")
    parser.add_argument("--naive-pseudo-manifest", default="")
    parser.add_argument("--aware-prediction-root", default="")
    parser.add_argument("--aware-eval-json", default="")
    parser.add_argument("--aware-pseudo-manifest", default="")
    parser.add_argument("--gate", default="G84")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g84_g81_three_arm_contract_gate_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g84_g81_three_arm_contract_gate_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    eval_serials = adapter["split"]["local_eval_serials"]
    heldout_paths = {
        str(row.get(key))
        for row in adapter["views"]
        if row["serial"] in eval_serials
        for key in ("rgb_path", "mask_path")
        if row.get(key)
    }

    arms = [
        arm("direct_single_image_gaussian", resolve(args.direct_prediction_root, repo), resolve(args.direct_eval_json, repo), eval_serials, None, heldout_paths),
        arm("naive_pseudo_view_supervision", resolve(args.naive_prediction_root, repo), resolve(args.naive_eval_json, repo), eval_serials, resolve(args.naive_pseudo_manifest, repo), heldout_paths),
        arm("identity_confidence_aware_pseudo_view_supervision", resolve(args.aware_prediction_root, repo), resolve(args.aware_eval_json, repo), eval_serials, resolve(args.aware_pseudo_manifest, repo), heldout_paths),
    ]
    by_name = {row["name"]: row for row in arms}
    missing: list[str] = []
    for row in arms:
        if not row["prediction_files"]["present"]:
            missing.append(f"{row['name']}: missing prediction files for {row['prediction_files']['missing']}")
        if not row["evaluation"]["present"]:
            missing.append(f"{row['name']}: missing held-out evaluator JSON")
        if "pseudo" in row["name"]:
            pseudo = row["pseudo_manifest"]
            if not pseudo.get("present"):
                missing.append(f"{row['name']}: missing pseudo-view supervision manifest")
            elif not pseudo.get("required_fields_present"):
                missing.append(f"{row['name']}: pseudo manifest lacks required identity/confidence/trusted-region fields")
            if pseudo.get("heldout_path_leakage"):
                missing.append(f"{row['name']}: pseudo manifest references held-out RGB/mask paths")

    all_ready = not missing
    if all_ready:
        aware = by_name["identity_confidence_aware_pseudo_view_supervision"]
        passed = beats(aware, [by_name["direct_single_image_gaussian"], by_name["naive_pseudo_view_supervision"]])
        verdict = PASS_RESULT if passed else FAIL_RESULT
    else:
        verdict = BLOCKED

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": (
            "Gate the actual G81 claim: identity/confidence-aware pseudo-view supervision must beat "
            "both direct single-image Gaussian and naive pseudo-view supervision on the same real held-out cameras."
        ),
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "no_leakage_rule": "Pseudo-view supervision may use only the source image and generated pseudo views; real held-out RGB/masks are evaluation-only.",
        "arms": arms,
        "missing_requirements": missing,
        "decision": (
            "Three-arm comparison is ready and the identity/confidence-aware arm beats both baselines."
            if verdict == PASS_RESULT
            else "Three-arm comparison ran, but the identity/confidence-aware arm did not beat both baselines."
            if verdict == FAIL_RESULT
            else "Blocked: the direct baseline exists, but naive and/or identity-confidence pseudo-supervision arms are not yet generated, trained, evaluated, and audited."
        ),
        "next_gate": (
            "Generate NeRSemble-source pseudo views from the private G83 input, build naive and identity/confidence-aware supervision manifests, train/render both arms, then rerun this contract gate."
            if verdict == BLOCKED
            else "Run visual/VLM gate and multi-case replication before making a paper claim."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "missing": missing}, indent=2))
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
