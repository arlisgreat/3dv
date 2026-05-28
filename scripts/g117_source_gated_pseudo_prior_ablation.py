#!/usr/bin/env python3
"""Generate source-only ablations for the G110 pseudo-prior refinement.

The script keeps the G110 no-leakage rule: held-out RGB/masks are never read.
It only consumes the source render/mask, direct LAM renders, and generated
pseudo-view manifests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G117_SOURCE_GATED_PSEUDO_PRIOR_ABLATIONS_READY"
BLOCKED = "BLOCKED_G117_SOURCE_GATED_PSEUDO_PRIOR_ABLATIONS"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rgba(path: Path) -> tuple[np.ndarray, np.ndarray]:
    rgba = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0
    return rgba[..., :3], rgba[..., 3]


def read_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0


def read_mask(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L")) > 8


def resize_rgb(image: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if image.shape[:2] == shape:
        return image
    pil = Image.fromarray(np.clip(image * 255.0, 0, 255).astype(np.uint8), mode="RGB")
    pil = pil.resize((shape[1], shape[0]), Image.Resampling.BILINEAR)
    return np.asarray(pil).astype(np.float32) / 255.0


def resize_alpha(alpha: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if alpha.shape == shape:
        return alpha
    pil = Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), mode="L")
    pil = pil.resize((shape[1], shape[0]), Image.Resampling.BILINEAR)
    return np.asarray(pil).astype(np.float32) / 255.0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def moments(pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return pixels.mean(axis=0), pixels.std(axis=0)


def select_source_alpha_threshold(source_alpha: np.ndarray, source_mask: np.ndarray) -> dict[str, Any]:
    thresholds = [1, 4, 8, 16, 24, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240]
    candidates: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for value in thresholds:
        threshold = float(value / 255.0)
        pred = source_alpha > threshold
        row = {
            "threshold": threshold,
            "threshold_u8": value,
            "source_mask_iou": mask_iou(pred, source_mask),
            "prediction_coverage": float(pred.mean()),
            "target_coverage": float(source_mask.mean()),
            "coverage_error": float(abs(float(pred.mean()) - float(source_mask.mean()))),
        }
        candidates.append(row)
        key = (row["source_mask_iou"], -row["coverage_error"])
        if best is None or key > (best["source_mask_iou"], -best["coverage_error"]):
            best = row
    if best is None:
        raise RuntimeError("no alpha threshold candidates produced")
    return {"selected": best, "candidates": candidates}


def selected_pseudo_views(manifest: dict[str, Any], policy: str) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]], float]:
    means: list[np.ndarray] = []
    variances: list[np.ndarray] = []
    weights: list[float] = []
    selected: list[dict[str, Any]] = []
    confidence_blends: list[float] = []
    for view in manifest.get("pseudo_views", []):
        if not view.get("ri3d_train_candidate"):
            continue
        identity_raw = view.get("identity_anchor_score")
        identity = None if identity_raw is None else float(identity_raw)
        confidence = float(view.get("confidence_score", 0.0)) / 100.0
        rgb_weight = float(view.get("rgb_weight", 0.0))
        if rgb_weight <= 0.0:
            continue
        if policy in {"full", "no_confidence", "no_source_alpha"} and identity is None:
            continue
        if policy == "full":
            weight = float(identity) * confidence * rgb_weight
            blend_component = confidence * rgb_weight
        elif policy == "no_identity":
            weight = confidence * rgb_weight
            blend_component = confidence * rgb_weight
        elif policy == "no_confidence":
            weight = float(identity) * rgb_weight
            blend_component = rgb_weight
        elif policy == "no_source_alpha":
            weight = float(identity) * confidence * rgb_weight
            blend_component = confidence * rgb_weight
        else:
            raise ValueError(f"unknown policy {policy}")
        if weight <= 0.0 or blend_component <= 0.0:
            continue
        image = read_rgb(Path(view["image_path"]))
        trusted_mask = read_mask(Path(view["trusted_region_mask"]))
        pixels = image[trusted_mask]
        if len(pixels) < 100:
            continue
        mean, std = moments(pixels)
        means.append(mean)
        variances.append(std * std)
        weights.append(weight)
        confidence_blends.append(blend_component)
        selected.append(
            {
                "view_index": view.get("view_index"),
                "supervision_role": view.get("supervision_role"),
                "identity_anchor_score": identity,
                "confidence_score": view.get("confidence_score"),
                "rgb_weight": rgb_weight,
                "moment_weight": weight,
                "pixel_count": int(len(pixels)),
                "image_sha256": view.get("image_sha256"),
                "trusted_region_mask_sha256": view.get("trusted_region_mask_sha256"),
            }
        )
    if not selected:
        raise RuntimeError(f"no pseudo views selected for policy {policy}")
    means_np = np.stack(means, axis=0)
    variances_np = np.stack(variances, axis=0)
    weights_np = np.asarray(weights, dtype=np.float32)
    target_mean = (means_np * weights_np[:, None]).sum(axis=0) / weights_np.sum()
    target_second = ((variances_np + means_np * means_np) * weights_np[:, None]).sum(axis=0) / weights_np.sum()
    target_std = np.sqrt(np.maximum(target_second - target_mean * target_mean, 1e-8))
    blend = float(min(confidence_blends))
    return target_mean.astype(np.float32), target_std.astype(np.float32), selected, blend


def write_rgba(path: Path, rgb: np.ndarray, alpha_mask: np.ndarray) -> None:
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    rgba[..., 3] = alpha_mask.astype(np.uint8) * 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(path)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G117 Source-Gated Pseudo Prior Ablations",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "No-leakage policy:",
        "",
        "```text",
        payload["no_leakage_policy"],
        "```",
        "",
        "Variants:",
        "",
        "| variant | policy | manifest | selected views | blend | alpha threshold u8 | prediction root |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["variants"]:
        lines.append(
            f"| {row['variant']} | {row['policy']} | {row['manifest_role']} | {len(row['selected_pseudo_views'])} | "
            f"{row['blend']:.6f} | {row['alpha_threshold_u8']} | {row['prediction_root']} |"
        )
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
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"))
    parser.add_argument("--direct-render-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard"))
    parser.add_argument("--strict-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g100_g81_strict_aware_manifest/identity_confidence_strict_pseudo_supervision_manifest.json"))
    parser.add_argument("--aware-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/identity_confidence_aware_pseudo_supervision_manifest.json"))
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g117_source_gated_pseudo_prior_ablation"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g117_source_gated_pseudo_prior_ablation_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g117_source_gated_pseudo_prior_ablation_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    strict_manifest = load_json(args.strict_manifest)
    aware_manifest = load_json(args.aware_manifest)
    views = {row["serial"]: row for row in adapter["views"]}
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]

    source_rgb, source_alpha = read_rgba(args.direct_render_root / "all_rendered_frames" / f"cam_{source_serial}_frame_00000.png")
    source_target = read_rgb(Path(views[source_serial]["rgb_path"]))
    source_mask = read_mask(Path(views[source_serial]["mask_path"]))
    source_rgb = resize_rgb(source_rgb, source_target.shape[:2])
    source_alpha = resize_alpha(source_alpha, source_target.shape[:2])
    alpha_gate = select_source_alpha_threshold(source_alpha, source_mask)
    source_threshold = float(alpha_gate["selected"]["threshold"])
    fixed_threshold = 8.0 / 255.0
    source_mean, source_std = moments(source_rgb[source_mask])

    variant_specs = [
        {
            "variant": "full_identity_confidence",
            "policy": "full",
            "manifest": strict_manifest,
            "manifest_role": "strict_identity_confidence",
            "threshold": source_threshold,
            "alpha_threshold_u8": int(alpha_gate["selected"]["threshold_u8"]),
        },
        {
            "variant": "without_identity_gate",
            "policy": "no_identity",
            "manifest": aware_manifest,
            "manifest_role": "aware_manifest_all_train_candidates_no_identity_weight",
            "threshold": source_threshold,
            "alpha_threshold_u8": int(alpha_gate["selected"]["threshold_u8"]),
        },
        {
            "variant": "without_confidence_gate",
            "policy": "no_confidence",
            "manifest": strict_manifest,
            "manifest_role": "strict_identity_no_confidence_weight",
            "threshold": source_threshold,
            "alpha_threshold_u8": int(alpha_gate["selected"]["threshold_u8"]),
        },
        {
            "variant": "without_source_alpha_gate",
            "policy": "no_source_alpha",
            "manifest": strict_manifest,
            "manifest_role": "strict_identity_confidence_fixed_alpha_u8_8",
            "threshold": fixed_threshold,
            "alpha_threshold_u8": 8,
        },
    ]
    variants: list[dict[str, Any]] = []
    missing: list[str] = []
    for spec in variant_specs:
        try:
            pseudo_mean, pseudo_std, selected, blend = selected_pseudo_views(spec["manifest"], spec["policy"])
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{spec['variant']}: {exc}")
            continue
        variant_root = args.output_root / spec["variant"]
        prediction_root = variant_root / "predictions"
        all_root = variant_root / "all_rendered_frames"
        render_rows: list[dict[str, Any]] = []
        for serial in [source_serial] + eval_serials:
            input_root = "all_rendered_frames" if serial == source_serial else "predictions"
            direct_path = args.direct_render_root / input_root / f"cam_{serial}_frame_00000.png"
            target_shape = (int(views[serial]["image_height"]), int(views[serial]["image_width"]))
            rgb, alpha = read_rgba(direct_path)
            rgb = resize_rgb(rgb, target_shape)
            alpha = resize_alpha(alpha, target_shape)
            calibrated = (rgb - source_mean) * pseudo_std / np.maximum(source_std, 1e-4) + pseudo_mean
            refined_rgb = np.clip((1.0 - blend) * rgb + blend * calibrated, 0.0, 1.0)
            refined_alpha = alpha > float(spec["threshold"])
            all_path = all_root / f"cam_{serial}_frame_00000.png"
            write_rgba(all_path, refined_rgb, refined_alpha)
            row = {
                "serial": serial,
                "role": "source_render" if serial == source_serial else "heldout_prediction",
                "direct_input": str(direct_path),
                "render_path": str(all_path),
                "render_sha256": sha256_file(all_path),
                "alpha_coverage": float(refined_alpha.mean()),
            }
            if serial in eval_serials:
                pred_path = prediction_root / f"cam_{serial}_frame_00000.png"
                write_rgba(pred_path, refined_rgb, refined_alpha)
                row["prediction_path"] = str(pred_path)
                row["prediction_sha256"] = sha256_file(pred_path)
            render_rows.append(row)
        variants.append(
            {
                "variant": spec["variant"],
                "policy": spec["policy"],
                "manifest_role": spec["manifest_role"],
                "prediction_root": str(prediction_root),
                "all_rendered_root": str(all_root),
                "blend": blend,
                "alpha_threshold_u8": spec["alpha_threshold_u8"],
                "selected_pseudo_views": selected,
                "renders": render_rows,
            }
        )
    verdict = PASS_VERDICT if not missing and len(variants) == len(variant_specs) else BLOCKED
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G117",
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "no_leakage_policy": (
            "Ablation parameter selection uses only direct source render/source mask and generated pseudo-view manifests. "
            "Held-out RGB/masks are not read by this script."
        ),
        "source_alpha_gate": alpha_gate,
        "direct_render_root": str(args.direct_render_root),
        "strict_manifest": str(args.strict_manifest),
        "aware_manifest": str(args.aware_manifest),
        "source_color_moments": {
            "source_direct_mean_rgb": source_mean.astype(float).tolist(),
            "source_direct_std_rgb": source_std.astype(float).tolist(),
        },
        "variants": variants,
        "missing_requirements": missing,
        "artifact_policy": "Identifiable RGBA predictions stay under 3dv_work; commit metrics/hashes and repo-safe mask audits only.",
        "decision": (
            "Ablation predictions are ready for original G55 held-out evaluation."
            if verdict == PASS_VERDICT
            else "Blocked: at least one ablation could not be generated."
        ),
        "next_gate": "Evaluate each G117 prediction root with the original G55 evaluator and aggregate direct/naive/G110/ablation results.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "variants": {row["variant"]: row["prediction_root"] for row in variants}, "missing": missing}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
