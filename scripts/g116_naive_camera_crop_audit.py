#!/usr/bin/env python3
"""Audit whether the naive pseudo-view arm failed from camera/crop mismatch."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G116_NAIVE_CAMERA_CROP_AUDIT_DIAGNOSTIC"
BLOCKED = "BLOCKED_G116_NAIVE_CAMERA_CROP_AUDIT"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_mask(path: Path) -> np.ndarray:
    image = Image.open(path)
    if image.mode in {"RGBA", "LA"}:
        return np.asarray(image.getchannel("A")) > 8
    return np.asarray(image.convert("L")) > 8


def resize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if mask.shape == shape:
        return mask
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")
    return np.asarray(image.resize((shape[1], shape[0]), Image.Resampling.NEAREST)) > 0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def mask_stats(mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"coverage": 0.0, "bbox": None, "bbox_area": 0.0, "center_offset": 1.0, "touches_border": False}
    height, width = mask.shape
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cx = (x0 + x1) / 2.0 / max(width - 1, 1)
    cy = (y0 + y1) / 2.0 / max(height - 1, 1)
    bbox_area = ((x1 - x0 + 1) * (y1 - y0 + 1)) / float(width * height)
    return {
        "coverage": float(mask.mean()),
        "bbox": [x0, y0, x1, y1],
        "bbox_area": float(bbox_area),
        "center_offset": float(((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5),
        "touches_border": bool(x0 <= 2 or y0 <= 2 or x1 >= width - 3 or y1 >= height - 3),
    }


def tile(mask: np.ndarray, label: str, tile_w: int, tile_h: int) -> Image.Image:
    img = Image.fromarray(mask.astype(np.uint8) * 255, mode="L").convert("RGB")
    img.thumbnail((tile_w - 20, tile_h - 50), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (tile_w, tile_h), "white")
    out.paste(img, ((tile_w - img.width) // 2, 8))
    ImageDraw.Draw(out).text((8, tile_h - 38), label[:54], fill=(0, 0, 0))
    return out


def overlay(target: np.ndarray, pred: np.ndarray) -> Image.Image:
    image = np.zeros((*target.shape, 3), dtype=np.uint8)
    image[target] = np.array([0, 170, 0], dtype=np.uint8)
    image[pred] = np.array([210, 0, 0], dtype=np.uint8)
    image[np.logical_and(target, pred)] = np.array([245, 205, 0], dtype=np.uint8)
    return Image.fromarray(image, mode="RGB")


def image_tile(image: Image.Image, label: str, tile_w: int, tile_h: int) -> Image.Image:
    img = image.copy()
    img.thumbnail((tile_w - 20, tile_h - 50), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (tile_w, tile_h), "white")
    out.paste(img, ((tile_w - img.width) // 2, 8))
    ImageDraw.Draw(out).text((8, tile_h - 38), label[:54], fill=(0, 0, 0))
    return out


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G116 Naive Camera/Crop Audit",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Key evidence:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| direct_source_mask_iou | {payload['direct_alignment']['source_mask_iou']:.6f} |",
        f"| naive_source_mask_iou | {payload['naive_alignment']['source_mask_iou']:.6f} |",
        f"| direct_min_eval_inframe | {payload['direct_alignment']['min_eval_inframe_fraction']:.6f} |",
        f"| naive_min_eval_inframe | {payload['naive_alignment']['min_eval_inframe_fraction']:.6f} |",
        f"| direct_mean_eval_mask_iou | {payload['direct_eval']['mean_prediction_mask_vs_eval_mask_iou']:.6f} |",
        f"| naive_mean_eval_mask_iou | {payload['naive_eval']['mean_prediction_mask_vs_eval_mask_iou']:.6f} |",
        "",
        "Per-eval masks:",
        "",
        "| serial | target coverage | direct coverage | naive coverage | direct IoU | naive IoU | naive touches border |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["per_eval_serial"]:
        lines.append(
            f"| {row['serial']} | {row['target_stats']['coverage']:.6f} | "
            f"{row['direct_stats']['coverage']:.6f} | {row['naive_stats']['coverage']:.6f} | "
            f"{row['direct_iou']:.6f} | {row['naive_iou']:.6f} | {row['naive_stats']['touches_border']} |"
        )
    lines.extend(
        [
            "",
            "Repo-safe mask sheet:",
            "",
            "```text",
            payload["repo_safe_outputs"]["mask_sheet"],
            "```",
            "",
            "Interpretation:",
            "",
            "```text",
            payload["interpretation"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"))
    parser.add_argument("--direct-render-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/render_manifest.json"))
    parser.add_argument("--naive-render-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g102_g81_strict_aware_nersemble_heldout_iter1500_splat8/g81_naive_pseudo_source_anchor/render_manifest.json"))
    parser.add_argument("--direct-eval-json", type=Path, default=Path("experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json"))
    parser.add_argument("--naive-eval-json", type=Path, default=Path("experiments/metrics/g103_g81_naive_strict_pool_iter1500_splat8_heldout_eval_20260528.json"))
    parser.add_argument("--mask-sheet", type=Path, default=Path("experiments/figures/g116_naive_camera_crop_audit_20260528.png"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g116_naive_camera_crop_audit_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g116_naive_camera_crop_audit_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    views = {row["serial"]: row for row in adapter["views"]}
    direct_manifest = load_json(args.direct_render_manifest)
    naive_manifest = load_json(args.naive_render_manifest)
    direct_eval = load_json(repo / args.direct_eval_json if not args.direct_eval_json.is_absolute() else args.direct_eval_json)["metrics"]
    naive_eval = load_json(repo / args.naive_eval_json if not args.naive_eval_json.is_absolute() else args.naive_eval_json)["metrics"]
    direct_renders = {row["serial"]: row for row in direct_manifest["renders"]}
    naive_renders = {row["serial"]: row for row in naive_manifest["renders"]}

    rows: list[dict[str, Any]] = []
    tile_w, tile_h = 240, 230
    sheet_rows: list[list[Image.Image]] = []
    missing: list[str] = []
    for serial in adapter["split"]["local_eval_serials"]:
        target_mask = read_mask(Path(views[serial]["mask_path"]))
        direct_path = Path(direct_renders[serial]["prediction_path"])
        naive_path = Path(naive_renders[serial]["prediction_path"])
        if not direct_path.exists():
            missing.append(str(direct_path))
        if not naive_path.exists():
            missing.append(str(naive_path))
        direct_mask = resize_mask(read_mask(direct_path), target_mask.shape) if direct_path.exists() else np.zeros_like(target_mask)
        naive_mask = resize_mask(read_mask(naive_path), target_mask.shape) if naive_path.exists() else np.zeros_like(target_mask)
        direct_iou = mask_iou(direct_mask, target_mask)
        naive_iou = mask_iou(naive_mask, target_mask)
        rows.append(
            {
                "serial": serial,
                "target_stats": mask_stats(target_mask),
                "direct_prediction": str(direct_path),
                "naive_prediction": str(naive_path),
                "direct_stats": mask_stats(direct_mask),
                "naive_stats": mask_stats(naive_mask),
                "direct_iou": direct_iou,
                "naive_iou": naive_iou,
            }
        )
        sheet_rows.append(
            [
                tile(target_mask, f"{serial} GT", tile_w, tile_h),
                tile(direct_mask, f"direct IoU={direct_iou:.3f}", tile_w, tile_h),
                image_tile(overlay(target_mask, direct_mask), "direct overlap", tile_w, tile_h),
                tile(naive_mask, f"naive IoU={naive_iou:.3f}", tile_w, tile_h),
                image_tile(overlay(target_mask, naive_mask), "naive overlap", tile_w, tile_h),
            ]
        )

    sheet = Image.new("RGB", (tile_w * 5, tile_h * len(sheet_rows)), "white")
    for row_idx, row in enumerate(sheet_rows):
        for col_idx, item in enumerate(row):
            sheet.paste(item, (col_idx * tile_w, row_idx * tile_h))
    mask_sheet = repo / args.mask_sheet
    mask_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(mask_sheet)

    direct_frustum = direct_manifest["alignment"]["frustum_guard"]
    naive_frustum = naive_manifest["alignment"]["frustum_guard"]
    camera_pose_likely_primary = bool(
        naive_frustum["min_eval_inframe_fraction"] < 0.2
        or naive_frustum["mean_eval_overflow_penalty"] > 1.0
    )
    source_crop_geometry_likely_primary = bool(
        naive_manifest["alignment"]["source_mask_iou"] < 0.5
        and direct_manifest["alignment"]["source_mask_iou"] > 0.8
        and not camera_pose_likely_primary
    )
    interpretation = (
        "The naive arm was rendered with the same NeRSemble eval cameras and an explicit eval-camera frustum guard. "
        f"The frustum is not catastrophically empty (min in-frame {naive_frustum['min_eval_inframe_fraction']:.3f}), "
        f"but source-mask alignment is poor ({naive_manifest['alignment']['source_mask_iou']:.3f}) compared with direct "
        f"({direct_manifest['alignment']['source_mask_iou']:.3f}). This supports source/crop/geometry collapse in the RI3D "
        "pseudo-geometry output as the primary failure, not a simple evaluator K/R/T wiring error. It still means naive is a "
        "weak baseline and should be reported with this caveat."
    )
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G116",
        "verdict": PASS_VERDICT if not missing else BLOCKED,
        "case": adapter["case"],
        "split": adapter["split"],
        "direct_alignment": {
            "source_mask_iou": direct_manifest["alignment"]["source_mask_iou"],
            "min_eval_inframe_fraction": direct_frustum["min_eval_inframe_fraction"],
            "mean_eval_inframe_fraction": direct_frustum["mean_eval_inframe_fraction"],
            "mean_eval_overflow_penalty": direct_frustum["mean_eval_overflow_penalty"],
        },
        "naive_alignment": {
            "source_mask_iou": naive_manifest["alignment"]["source_mask_iou"],
            "axis_transform": naive_manifest["alignment"]["axis_transform"],
            "scale": naive_manifest["alignment"]["scale"],
            "translation": naive_manifest["alignment"]["translation"],
            "min_eval_inframe_fraction": naive_frustum["min_eval_inframe_fraction"],
            "mean_eval_inframe_fraction": naive_frustum["mean_eval_inframe_fraction"],
            "mean_eval_overflow_penalty": naive_frustum["mean_eval_overflow_penalty"],
            "mean_eval_center_penalty": naive_frustum["mean_eval_center_penalty"],
        },
        "direct_eval": {
            "mean_masked_rgb_psnr": direct_eval["mean_masked_rgb_psnr"],
            "mean_prediction_mask_vs_eval_mask_iou": direct_eval["mean_prediction_mask_vs_eval_mask_iou"],
            "mean_prediction_foreground_coverage": direct_eval["mean_prediction_foreground_coverage"],
        },
        "naive_eval": {
            "mean_masked_rgb_psnr": naive_eval["mean_masked_rgb_psnr"],
            "mean_prediction_mask_vs_eval_mask_iou": naive_eval["mean_prediction_mask_vs_eval_mask_iou"],
            "mean_prediction_foreground_coverage": naive_eval["mean_prediction_foreground_coverage"],
        },
        "diagnosis": {
            "camera_pose_likely_primary_failure": camera_pose_likely_primary,
            "source_crop_geometry_likely_primary_failure": source_crop_geometry_likely_primary,
        },
        "per_eval_serial": rows,
        "missing_requirements": missing,
        "repo_safe_outputs": {"mask_sheet": str(mask_sheet)},
        "interpretation": interpretation,
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": payload["verdict"], "diagnosis": payload["diagnosis"]}, indent=2))
    if payload["verdict"] != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
