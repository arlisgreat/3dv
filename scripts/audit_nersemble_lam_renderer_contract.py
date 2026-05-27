#!/usr/bin/env python3
"""Audit the G57 LAM-to-NeRSemble renderer contract before interpreting metrics."""

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
GATE = "G58"
PASS_VERDICT = "PASS_NERSEMBLE_TRUE_CAMERA_RENDERER_CONTRACT"
DIAGNOSTIC_VERDICT = "PASS_DIAGNOSTIC_ONLY_RENDERER_CONTRACT_FAILED"
BLOCKED_VERDICT = "BLOCKED_NERSEMBLE_LAM_RENDERER_CONTRACT_AUDIT"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rgb(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"could not read {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def read_mask(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"could not read {path}")
    return mask > 8


def estimate_foreground_mask(rgb: np.ndarray) -> np.ndarray:
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
    distance = np.linalg.norm(rgb - background[None, None, :], axis=-1)
    mask = distance > 0.08
    mask_u8 = (mask.astype(np.uint8) * 255)
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    return mask_u8 > 0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def mask_stats(mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {
            "coverage": 0.0,
            "bbox": None,
            "centroid_xy_norm": None,
            "touches_image_border": False,
        }
    height, width = mask.shape
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return {
        "coverage": float(mask.mean()),
        "bbox": [x0, y0, x1, y1],
        "centroid_xy_norm": [float(xs.mean() / max(width - 1, 1)), float(ys.mean() / max(height - 1, 1))],
        "touches_image_border": bool(x0 <= 2 or y0 <= 2 or x1 >= width - 3 or y1 >= height - 3),
    }


def make_overlay(rgb: np.ndarray, target_mask: np.ndarray, pred_mask: np.ndarray) -> Image.Image:
    base = (np.clip(rgb, 0.0, 1.0) * 255).astype(np.uint8)
    overlay = base.copy()
    overlay[target_mask] = (0.65 * overlay[target_mask] + np.array([0, 255, 0]) * 0.35).astype(np.uint8)
    overlay[pred_mask] = (0.65 * overlay[pred_mask] + np.array([255, 0, 0]) * 0.35).astype(np.uint8)
    return Image.fromarray(overlay)


def paste_tile(sheet: Image.Image, image: Image.Image, col: int, row: int, label: str, tile_w: int, tile_h: int) -> None:
    tile = Image.new("RGB", (tile_w, tile_h), "white")
    image = image.convert("RGB")
    image.thumbnail((tile_w - 20, tile_h - 48), Image.Resampling.LANCZOS)
    tile.paste(image, ((tile_w - image.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.text((8, tile_h - 34), label[:44], fill=(0, 0, 0))
    sheet.paste(tile, (col * tile_w, row * tile_h))


def make_private_sheet(rows: list[dict[str, Any]], output: Path) -> None:
    tile_w, tile_h = 260, 260
    cols = 4
    sheet = Image.new("RGB", (cols * tile_w, len(rows) * tile_h), "white")
    for row_i, row in enumerate(rows):
        target_rgb = read_rgb(Path(row["target_rgb_path"]))
        target_mask = read_mask(Path(row["target_mask_path"]))
        pred_rgb = read_rgb(Path(row["prediction_path"]))
        pred_mask = estimate_foreground_mask(pred_rgb)
        mask_img = Image.fromarray((target_mask.astype(np.uint8) * 255), mode="L").convert("RGB")
        pred_mask_img = Image.fromarray((pred_mask.astype(np.uint8) * 255), mode="L").convert("RGB")
        paste_tile(sheet, Image.fromarray((target_rgb * 255).astype(np.uint8)), 0, row_i, f"{row['serial']} GT RGB", tile_w, tile_h)
        paste_tile(sheet, mask_img, 1, row_i, "GT alpha mask", tile_w, tile_h)
        paste_tile(sheet, Image.fromarray((pred_rgb * 255).astype(np.uint8)), 2, row_i, "LAM prediction", tile_w, tile_h)
        paste_tile(sheet, make_overlay(target_rgb, target_mask, pred_mask), 3, row_i, "overlay green=GT red=pred", tile_w, tile_h)
        _ = pred_mask_img
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G58 NeRSemble LAM Renderer Contract Audit",
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
        "Renderer contract:",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in payload["renderer_contract"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "Visual and mask audit:",
            "",
            "| serial | pred coverage | target coverage | pred/target IoU | touches border | decision |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in payload["per_eval_serial"]:
        lines.append(
            f"| {row['serial']} | {row['prediction_stats']['coverage']:.6f} | "
            f"{row['target_stats']['coverage']:.6f} | {row['prediction_target_mask_iou']:.6f} | "
            f"{row['prediction_stats']['touches_image_border']} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "Private audit sheet:",
            "",
            "```text",
            payload["private_outputs"]["audit_sheet"],
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
    parser.add_argument("--render-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g57_nersemble_lam_camera_render/render_manifest.json"))
    parser.add_argument("--eval-json", type=Path, default=Path("experiments/metrics/g57_lam_nersemble_heldout_eval_20260527.json"))
    parser.add_argument("--private-sheet", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g58_nersemble_lam_renderer_contract_audit/g58_private_lam_vs_gt_sheet.png"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g58_nersemble_lam_renderer_contract_audit_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g58_nersemble_lam_renderer_contract_audit_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    render_manifest = load_json(args.render_manifest)
    eval_payload = load_json(repo / args.eval_json if not args.eval_json.is_absolute() else args.eval_json)
    eval_serials = adapter.get("split", {}).get("local_eval_serials", [])
    prediction_root = Path(render_manifest.get("prediction_root", "/nonexistent"))

    copied_by_serial = {row.get("serial"): row for row in render_manifest.get("copied_frames", [])}
    per_eval: list[dict[str, Any]] = []
    sheet_rows: list[dict[str, Any]] = []
    for serial in eval_serials:
        target = next(row for row in adapter["views"] if row["serial"] == serial)
        pred_path = prediction_root / f"cam_{serial}_frame_00000.png"
        if not pred_path.exists():
            per_eval.append({"serial": serial, "decision": "missing_prediction"})
            continue
        pred_rgb = read_rgb(pred_path)
        pred_mask = estimate_foreground_mask(pred_rgb)
        target_mask = read_mask(Path(target["mask_path"]))
        pred_stats = mask_stats(pred_mask)
        target_stats = mask_stats(target_mask)
        iou = mask_iou(pred_mask, target_mask)
        weak_visual = (
            pred_stats["coverage"] < 0.05
            or iou < 0.10
            or bool(pred_stats["touches_image_border"])
        )
        per_eval.append(
            {
                "serial": serial,
                "prediction_path": str(pred_path),
                "prediction_sha256": sha256_file(pred_path),
                "source_lam_png": copied_by_serial.get(serial, {}).get("source_lam_png"),
                "target_rgb_path": target["rgb_path"],
                "target_mask_path": target["mask_path"],
                "prediction_stats": pred_stats,
                "target_stats": target_stats,
                "prediction_target_mask_iou": iou,
                "decision": "weak_or_misaligned_prediction" if weak_visual else "visually_nonempty_prediction",
            }
        )
        sheet_rows.append(
            {
                "serial": serial,
                "prediction_path": str(pred_path),
                "target_rgb_path": target["rgb_path"],
                "target_mask_path": target["mask_path"],
            }
        )

    if sheet_rows:
        make_private_sheet(sheet_rows, args.private_sheet)
        sheet_sha = sha256_file(args.private_sheet)
    else:
        sheet_sha = None

    camera_mode = render_manifest.get("camera_mode")
    camera_contract_verified = bool(render_manifest.get("camera_contract_verified")) and camera_mode in {
        "nersemble_krt",
        "raw_verified",
    }
    predictions_present = len([row for row in per_eval if row.get("prediction_path")]) == len(eval_serials) and bool(eval_serials)
    visual_gate_pass = predictions_present and all(row.get("decision") == "visually_nonempty_prediction" for row in per_eval)
    eval_finite = str(eval_payload.get("verdict", "")).startswith("PASS")

    if not predictions_present:
        verdict = BLOCKED_VERDICT
    elif camera_contract_verified and visual_gate_pass and eval_finite:
        verdict = PASS_VERDICT
    else:
        verdict = DIAGNOSTIC_VERDICT

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "A method metric is interpretable only if the prediction PNGs are rendered by the same learned-prior/mesh/Gaussian "
            "representation into the audited G54 NeRSemble held-out K/R/T cameras and pass a visual nonblank/alignment gate."
        ),
        "verdict": verdict,
        "case": adapter.get("case"),
        "split": adapter.get("split"),
        "renderer_contract": {
            "method": render_manifest.get("method"),
            "camera_mode": camera_mode,
            "camera_contract_verified": camera_contract_verified,
            "prediction_root": str(prediction_root),
            "eval_json_verdict": eval_payload.get("verdict"),
            "eval_mean_psnr": eval_payload.get("metrics", {}).get("mean_masked_rgb_psnr"),
            "eval_mean_ssim": eval_payload.get("metrics", {}).get("mean_masked_rgb_ssim_global_luma"),
            "eval_mean_prediction_mask_iou": eval_payload.get("metrics", {}).get("mean_prediction_mask_vs_eval_mask_iou", eval_payload.get("metrics", {}).get("mean_source_mask_vs_eval_mask_iou")),
        },
        "per_eval_serial": per_eval,
        "private_outputs": {
            "audit_sheet": str(args.private_sheet),
            "audit_sheet_sha256": sheet_sha,
            "existing_g57_private_sheet": render_manifest.get("private_contact_sheet"),
            "existing_g57_private_sheet_sha256": render_manifest.get("private_contact_sheet_sha256"),
        },
        "manual_visual_audit": (
            "The G57 private contact sheet shows a plausible source render but the three held-out predictions are mostly blank "
            "or cropped to image borders. This is not a verified NeRSemble held-out camera rendering."
        ),
        "decision": (
            "G57 is downgraded to diagnostic-only. Finite evaluator metrics only prove that files were readable; they do not validate "
            "the learned-prior idea or a true held-out camera renderer."
            if verdict == DIAGNOSTIC_VERDICT
            else (
                "Predictions are missing; rerun the renderer before any method evaluation."
                if verdict == BLOCKED_VERDICT
                else "Renderer contract and visual gate pass; method metrics may be interpreted within the stated distribution limits."
            )
        ),
        "next_gate": (
            "Implement a true G54 K/R/T renderer positive control first, preferably with the NeRSemble GT pointcloud, then route a "
            "method mesh/Gaussian through the same renderer and repeat this visual/mask/camera audit."
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
