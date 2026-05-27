#!/usr/bin/env python3
"""Audit a NeRSemble method render with repo-safe masks and private visual notes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
from PIL import Image, ImageDraw  # type: ignore


DATE = "2026-05-27"
PASS_DIAGNOSTIC = "PASS_DIAGNOSTIC_ONLY_NATIVE_GAUSSIAN_RENDERER_WITH_LIMITATIONS"
BLOCKED = "BLOCKED_NERSEMBLE_METHOD_VISUAL_GATE"


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


def read_mask(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"could not read {path}")
    return image > 8


def read_prediction_mask(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError(f"could not read {path}")
    if image.ndim == 3 and image.shape[2] == 4:
        return image[:, :, 3] > 8
    rgb = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    height, width = rgb.shape[:2]
    border = max(4, min(height, width) // 20)
    border_pixels = np.concatenate(
        [
            rgb[:border, :, :].reshape(-1, 3),
            rgb[-border:, :, :].reshape(-1, 3),
            rgb[:, :border, :].reshape(-1, 3),
            rgb[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    quantized = np.clip(border_pixels * 255.0, 0, 255).astype(np.uint8) // 16
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    mode = colors[int(np.argmax(counts))]
    background = (mode.astype(np.float32) * 16.0 + 8.0) / 255.0
    mask = np.linalg.norm(rgb - background[None, None, :], axis=-1) > 0.08
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx((mask.astype(np.uint8) * 255), cv2.MORPH_OPEN, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    return mask_u8 > 0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def mask_stats(mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"coverage": 0.0, "bbox": None, "centroid_xy_norm": None, "touches_image_border": False}
    height, width = mask.shape
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return {
        "coverage": float(mask.mean()),
        "bbox": [x0, y0, x1, y1],
        "centroid_xy_norm": [float(xs.mean() / max(width - 1, 1)), float(ys.mean() / max(height - 1, 1))],
        "touches_image_border": bool(x0 <= 2 or y0 <= 2 or x1 >= width - 3 or y1 >= height - 3),
    }


def resize_mask(mask: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    height, width = target_shape
    if mask.shape == target_shape:
        return mask
    return cv2.resize(mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST) > 0


def tile_from_mask(mask: np.ndarray, label: str, tile_w: int, tile_h: int) -> Image.Image:
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L").convert("RGB")
    image.thumbnail((tile_w - 20, tile_h - 48), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_w, tile_h), "white")
    tile.paste(image, ((tile_w - image.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.text((8, tile_h - 34), label[:50], fill=(0, 0, 0))
    return tile


def overlap_mask(target: np.ndarray, pred: np.ndarray) -> np.ndarray:
    image = np.zeros((*target.shape, 3), dtype=np.uint8)
    image[target] = np.array([0, 180, 0], dtype=np.uint8)
    image[pred] = np.array([220, 0, 0], dtype=np.uint8)
    image[np.logical_and(target, pred)] = np.array([240, 210, 0], dtype=np.uint8)
    return image


def make_mask_sheet(rows: list[dict[str, Any]], output: Path) -> None:
    tile_w, tile_h = 260, 250
    cols = 3
    sheet = Image.new("RGB", (tile_w * cols, tile_h * len(rows)), "white")
    for row_i, row in enumerate(rows):
        target = row["_target_mask"]
        pred = row["_prediction_mask"]
        tiles = [
            tile_from_mask(target, f"{row['serial']} GT mask", tile_w, tile_h),
            tile_from_mask(pred, f"prediction IoU={row['prediction_target_mask_iou']:.3f}", tile_w, tile_h),
            tile_from_mask(np.zeros_like(target), "placeholder", tile_w, tile_h),
        ]
        tiles[2] = Image.fromarray(overlap_mask(target, pred), mode="RGB")
        tiles[2].thumbnail((tile_w - 20, tile_h - 48), Image.Resampling.LANCZOS)
        labeled = Image.new("RGB", (tile_w, tile_h), "white")
        labeled.paste(tiles[2], ((tile_w - tiles[2].width) // 2, 8))
        ImageDraw.Draw(labeled).text((8, tile_h - 34), "yellow=overlap green=GT red=pred", fill=(0, 0, 0))
        tiles[2] = labeled
        for col, tile in enumerate(tiles):
            sheet.paste(tile, (tile_w * col, tile_h * row_i))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} NeRSemble Method Visual Gate",
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
        "Mask audit:",
        "",
        "| serial | pred coverage | target coverage | coverage ratio | pred/target IoU | touches border | decision |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["per_eval_serial"]:
        lines.append(
            f"| {row['serial']} | {row['prediction_stats']['coverage']:.6f} | "
            f"{row['target_stats']['coverage']:.6f} | {row['prediction_target_coverage_ratio']:.6f} | "
            f"{row['prediction_target_mask_iou']:.6f} | "
            f"{row['prediction_stats']['touches_image_border']} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "Mean summary:",
            "",
            "| field | value |",
            "| --- | ---: |",
            f"| mean_prediction_target_mask_iou | {payload['summary']['mean_prediction_target_mask_iou']:.6f} |",
            f"| mean_prediction_coverage | {payload['summary']['mean_prediction_coverage']:.6f} |",
            f"| crop_risk_mode | {payload['crop_risk_policy']['mode']} |",
            f"| min_mask_iou | {payload['crop_risk_policy']['min_mask_iou']:.6f} |",
            "",
            "Repo-safe mask sheet:",
            "",
            "```text",
            payload["repo_safe_outputs"]["mask_sheet"],
            "```",
            "",
            "Private visual sheet:",
            "",
            "```text",
            payload["private_outputs"]["contact_sheet"],
            "```",
            "",
            "Manual/VLM audit note:",
            "",
            "```text",
            payload["manual_visual_audit"],
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
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--render-manifest", type=Path, required=True)
    parser.add_argument("--eval-json", type=Path, required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--mask-sheet", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--manual-visual-audit", required=True)
    parser.add_argument("--premise", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--next-gate", required=True)
    parser.add_argument("--crop-risk-mode", choices=["legacy_border_or_iou", "mask_iou_coverage"], default="legacy_border_or_iou")
    parser.add_argument("--min-mask-iou", type=float, default=0.45)
    parser.add_argument("--min-coverage-ratio", type=float, default=0.40)
    parser.add_argument("--max-coverage-ratio", type=float, default=1.70)
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    render_manifest = load_json(args.render_manifest)
    eval_payload = load_json(args.eval_json if args.eval_json.is_absolute() else repo / args.eval_json)
    prediction_root = Path(render_manifest["prediction_root"])
    eval_serials = adapter["split"]["local_eval_serials"]
    views = {row["serial"]: row for row in adapter["views"]}

    rows: list[dict[str, Any]] = []
    for serial in eval_serials:
        target_mask = read_mask(Path(views[serial]["mask_path"]))
        pred_path = prediction_root / f"cam_{serial}_frame_00000.png"
        pred_mask = resize_mask(read_prediction_mask(pred_path), target_mask.shape)
        pred_stats = mask_stats(pred_mask)
        target_stats = mask_stats(target_mask)
        iou = mask_iou(pred_mask, target_mask)
        target_coverage = max(float(target_stats["coverage"]), 1e-8)
        coverage_ratio = float(pred_stats["coverage"]) / target_coverage
        if args.crop_risk_mode == "mask_iou_coverage":
            crop_risk = iou < args.min_mask_iou or coverage_ratio < args.min_coverage_ratio or coverage_ratio > args.max_coverage_ratio
        else:
            crop_risk = bool(pred_stats["touches_image_border"]) or iou < args.min_mask_iou
        rows.append(
            {
                "serial": serial,
                "prediction_path": str(pred_path),
                "prediction_sha256": sha256_file(pred_path),
                "target_mask_path": views[serial]["mask_path"],
                "prediction_stats": pred_stats,
                "target_stats": target_stats,
                "prediction_target_mask_iou": iou,
                "prediction_target_coverage_ratio": coverage_ratio,
                "decision": "partial_or_cropped_prediction" if crop_risk else "nonblank_aligned_prediction",
                "_target_mask": target_mask,
                "_prediction_mask": pred_mask,
            }
        )

    make_mask_sheet(rows, repo / args.mask_sheet)
    mean_iou = float(np.mean([row["prediction_target_mask_iou"] for row in rows]))
    mean_cov = float(np.mean([row["prediction_stats"]["coverage"] for row in rows]))
    any_crop = any(row["decision"] == "partial_or_cropped_prediction" for row in rows)
    eval_pass = str(eval_payload.get("verdict", "")).startswith("PASS")
    verdict = PASS_DIAGNOSTIC if eval_pass and rows and mean_iou >= 0.25 and mean_cov >= 0.10 else BLOCKED
    if verdict == PASS_DIAGNOSTIC and any_crop:
        quality_claim = "blocked_by_crop_or_alignment"
    elif verdict == PASS_DIAGNOSTIC:
        quality_claim = "diagnostic_only_pending_multicase_validation"
    else:
        quality_claim = "blocked"

    for row in rows:
        row.pop("_target_mask")
        row.pop("_prediction_mask")

    contact_sheet = render_manifest.get("private_outputs", {}).get("contact_sheet")
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": args.premise,
        "verdict": verdict,
        "quality_claim_status": quality_claim,
        "case": adapter["case"],
        "split": adapter["split"],
        "method": render_manifest.get("method"),
        "render_manifest": str(args.render_manifest),
        "eval_json": str(args.eval_json),
        "eval_verdict": eval_payload.get("verdict"),
        "eval_mean_psnr": eval_payload.get("metrics", {}).get("mean_masked_rgb_psnr"),
        "eval_mean_prediction_mask_iou": eval_payload.get("metrics", {}).get("mean_prediction_mask_vs_eval_mask_iou"),
        "crop_risk_policy": {
            "mode": args.crop_risk_mode,
            "min_mask_iou": args.min_mask_iou,
            "min_coverage_ratio": args.min_coverage_ratio,
            "max_coverage_ratio": args.max_coverage_ratio,
        },
        "per_eval_serial": rows,
        "summary": {
            "mean_prediction_target_mask_iou": mean_iou,
            "mean_prediction_coverage": mean_cov,
            "any_crop_or_alignment_risk": any_crop,
        },
        "repo_safe_outputs": {
            "mask_sheet": str(repo / args.mask_sheet),
            "mask_sheet_sha256": sha256_file(repo / args.mask_sheet),
        },
        "private_outputs": {
            "contact_sheet": contact_sheet,
            "contact_sheet_sha256": render_manifest.get("private_outputs", {}).get("contact_sheet_sha256"),
        },
        "manual_visual_audit": args.manual_visual_audit,
        "decision": args.decision,
        "next_gate": args.next_gate,
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "quality_claim_status": quality_claim, "mean_iou": mean_iou, "mask_sheet": str(repo / args.mask_sheet)}, indent=2))
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
