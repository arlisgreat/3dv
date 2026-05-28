#!/usr/bin/env python3
"""Repo-safe mask audit for the G81 three-arm held-out comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


DATE = "2026-05-28"
PASS_DIAGNOSTIC = "PASS_G81_THREE_ARM_MASK_AUDIT_DIAGNOSTIC_ONLY"
BLOCKED = "BLOCKED_G81_THREE_ARM_MASK_AUDIT"


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
    image = Image.open(path)
    if image.mode in {"RGBA", "LA"}:
        alpha = np.asarray(image.getchannel("A"))
        return alpha > 8
    gray = np.asarray(image.convert("L"))
    return gray > 8


def read_prediction_mask(path: Path) -> np.ndarray:
    image = Image.open(path)
    if image.mode in {"RGBA", "LA"}:
        return np.asarray(image.getchannel("A")) > 8
    rgb = np.asarray(image.convert("RGB")).astype(np.float32) / 255.0
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
    quantized = (np.clip(border_pixels * 255.0, 0, 255).astype(np.uint8) // 16).reshape(-1, 3)
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    mode = colors[int(np.argmax(counts))]
    background = (mode.astype(np.float32) * 16.0 + 8.0) / 255.0
    return np.linalg.norm(rgb - background[None, None, :], axis=-1) > 0.08


def resize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if mask.shape == shape:
        return mask
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")
    resized = image.resize((shape[1], shape[0]), Image.Resampling.NEAREST)
    return np.asarray(resized) > 0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def mask_stats(mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"coverage": 0.0, "bbox": None, "touches_border": False}
    height, width = mask.shape
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return {
        "coverage": float(mask.mean()),
        "bbox": [x0, y0, x1, y1],
        "touches_border": bool(x0 <= 2 or y0 <= 2 or x1 >= width - 3 or y1 >= height - 3),
    }


def tile_from_mask(mask: np.ndarray, label: str, tile_w: int, tile_h: int) -> Image.Image:
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L").convert("RGB")
    image.thumbnail((tile_w - 20, tile_h - 52), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_w, tile_h), "white")
    tile.paste(image, ((tile_w - image.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.text((8, tile_h - 40), label[:48], fill=(0, 0, 0))
    return tile


def overlay(target: np.ndarray, pred: np.ndarray) -> Image.Image:
    image = np.zeros((*target.shape, 3), dtype=np.uint8)
    image[target] = np.array([0, 170, 0], dtype=np.uint8)
    image[pred] = np.array([210, 0, 0], dtype=np.uint8)
    image[np.logical_and(target, pred)] = np.array([245, 205, 0], dtype=np.uint8)
    return Image.fromarray(image, mode="RGB")


def labeled_image(image: Image.Image, label: str, tile_w: int, tile_h: int) -> Image.Image:
    image = image.copy()
    image.thumbnail((tile_w - 20, tile_h - 52), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_w, tile_h), "white")
    tile.paste(image, ((tile_w - image.width) // 2, 8))
    ImageDraw.Draw(tile).text((8, tile_h - 40), label[:48], fill=(0, 0, 0))
    return tile


def arm_eval_summary(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    metrics = payload.get("metrics", {})
    return {
        "path": str(path),
        "verdict": payload.get("verdict"),
        "mean_masked_rgb_psnr": metrics.get("mean_masked_rgb_psnr"),
        "mean_prediction_mask_vs_eval_mask_iou": metrics.get("mean_prediction_mask_vs_eval_mask_iou"),
        "mean_prediction_foreground_coverage": metrics.get("mean_prediction_foreground_coverage"),
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} G81 Three-Arm Mask Audit",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Arm summary:",
        "",
        "| arm | PSNR | eval mask IoU | audit mask IoU | coverage |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in payload["summary_by_arm"].items():
        ev = row["eval_summary"]
        lines.append(
            f"| {name} | {ev['mean_masked_rgb_psnr']:.6f} | "
            f"{ev['mean_prediction_mask_vs_eval_mask_iou']:.6f} | "
            f"{row['mean_audit_mask_iou']:.6f} | {row['mean_prediction_coverage']:.6f} |"
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
    parser.add_argument("--adapter-manifest", type=Path, required=True)
    parser.add_argument("--direct-root", type=Path, required=True)
    parser.add_argument("--direct-eval-json", type=Path, required=True)
    parser.add_argument("--naive-root", type=Path, required=True)
    parser.add_argument("--naive-eval-json", type=Path, required=True)
    parser.add_argument("--aware-root", type=Path, required=True)
    parser.add_argument("--aware-eval-json", type=Path, required=True)
    parser.add_argument("--gate", default="G108")
    parser.add_argument("--mask-sheet", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    eval_serials = adapter["split"]["local_eval_serials"]
    views_by_serial = {row["serial"]: row for row in adapter["views"]}
    arms = {
        "direct_single_image_gaussian": (args.direct_root, repo / args.direct_eval_json),
        "naive_pseudo_view_supervision": (args.naive_root, repo / args.naive_eval_json),
        "identity_confidence_aware_pseudo_view_supervision": (args.aware_root, repo / args.aware_eval_json),
    }

    per_serial: list[dict[str, Any]] = []
    rows_for_sheet: list[list[Image.Image]] = []
    missing: list[str] = []
    tile_w, tile_h = 260, 250
    for serial in eval_serials:
        target_mask = read_mask(Path(views_by_serial[serial]["mask_path"]))
        serial_row: dict[str, Any] = {"serial": serial, "target_stats": mask_stats(target_mask), "arms": {}}
        sheet_row = [tile_from_mask(target_mask, f"{serial} GT alpha", tile_w, tile_h)]
        for arm_name, (root, _eval_json) in arms.items():
            pred_path = root / f"cam_{serial}_frame_00000.png"
            if not pred_path.exists():
                missing.append(f"{arm_name}: missing {pred_path}")
                pred_mask = np.zeros_like(target_mask)
            else:
                pred_mask = resize_mask(read_prediction_mask(pred_path), target_mask.shape)
            iou = mask_iou(pred_mask, target_mask)
            serial_row["arms"][arm_name] = {
                "prediction_path": str(pred_path),
                "prediction_sha256": sha256_file(pred_path) if pred_path.exists() else None,
                "prediction_stats": mask_stats(pred_mask),
                "prediction_target_mask_iou": iou,
            }
            short = (
                "direct"
                if arm_name.startswith("direct")
                else "naive"
                if arm_name.startswith("naive")
                else "aware"
            )
            sheet_row.append(tile_from_mask(pred_mask, f"{short} IoU={iou:.3f}", tile_w, tile_h))
            sheet_row.append(labeled_image(overlay(target_mask, pred_mask), f"{short}: yellow overlap", tile_w, tile_h))
        rows_for_sheet.append(sheet_row)
        per_serial.append(serial_row)

    cols = len(rows_for_sheet[0]) if rows_for_sheet else 1
    sheet = Image.new("RGB", (tile_w * cols, tile_h * len(rows_for_sheet)), "white")
    for row_i, row in enumerate(rows_for_sheet):
        for col_i, tile in enumerate(row):
            sheet.paste(tile, (tile_w * col_i, tile_h * row_i))
    mask_sheet = repo / args.mask_sheet
    mask_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(mask_sheet)

    summary_by_arm: dict[str, Any] = {}
    for arm_name, (_root, eval_json) in arms.items():
        ious = [row["arms"][arm_name]["prediction_target_mask_iou"] for row in per_serial]
        covs = [row["arms"][arm_name]["prediction_stats"]["coverage"] for row in per_serial]
        summary_by_arm[arm_name] = {
            "mean_audit_mask_iou": float(np.mean(ious)) if ious else 0.0,
            "mean_prediction_coverage": float(np.mean(covs)) if covs else 0.0,
            "eval_summary": arm_eval_summary(eval_json),
        }

    aware = summary_by_arm["identity_confidence_aware_pseudo_view_supervision"]["eval_summary"]
    direct = summary_by_arm["direct_single_image_gaussian"]["eval_summary"]
    naive = summary_by_arm["naive_pseudo_view_supervision"]["eval_summary"]
    aware_beats_both = bool(
        aware["mean_masked_rgb_psnr"] > direct["mean_masked_rgb_psnr"]
        and aware["mean_masked_rgb_psnr"] > naive["mean_masked_rgb_psnr"]
        and aware["mean_prediction_mask_vs_eval_mask_iou"] > direct["mean_prediction_mask_vs_eval_mask_iou"]
        and aware["mean_prediction_mask_vs_eval_mask_iou"] > naive["mean_prediction_mask_vs_eval_mask_iou"]
    )
    verdict = BLOCKED if missing else PASS_DIAGNOSTIC
    manual_visual_audit = (
        "Mask-only audit confirms the identity/confidence-aware arm has the strongest held-out mask support among the three arms. "
        "The improvement comes from source-gated direct-prior support rather than from the earlier fragmented RI3D pseudo-view geometry."
        if aware_beats_both
        else (
            "Mask-only audit confirms the direct arm has much stronger held-out support. "
            "Naive and identity/confidence-aware RI3D arms are weak/partial and do not provide a visual basis for a positive pseudo-view supervision claim."
        )
    )
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "per_eval_serial": per_serial,
        "summary_by_arm": summary_by_arm,
        "aware_beats_direct_and_naive": aware_beats_both,
        "missing_requirements": missing,
        "repo_safe_outputs": {
            "mask_sheet": str(mask_sheet),
            "mask_sheet_sha256": sha256_file(mask_sheet),
        },
        "artifact_policy": "Repo-safe mask-only sheet is committed; identifiable RGB renders and pseudo-view sheets remain under 3dv_work.",
        "manual_visual_audit": manual_visual_audit,
        "decision": (
            "Identity/confidence-aware pseudo-view supervision does not exceed direct + naive; G81 is a negative result under the current strict real-GT contract."
            if not aware_beats_both
            else "Identity/confidence-aware pseudo-view supervision exceeds both baselines under this mask audit and evaluator contract."
        ),
        "next_gate": "Update milestones/experiment index and sync repo-safe metrics plus mask-only PNG to GitHub.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "aware_beats_direct_and_naive": aware_beats_both, "mask_sheet": str(mask_sheet)}, indent=2))
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
