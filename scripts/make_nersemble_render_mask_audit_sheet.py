#!/usr/bin/env python3
"""Create a repo-safe mask-only audit sheet for NeRSemble render milestones."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
from PIL import Image, ImageDraw  # type: ignore


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_mask(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"could not read {path}")
    return mask > 8


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
    distance = np.linalg.norm(rgb - background[None, None, :], axis=-1)
    mask = distance > 0.08
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx((mask.astype(np.uint8) * 255), cv2.MORPH_OPEN, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    return mask_u8 > 0


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def tile_from_mask(mask: np.ndarray, label: str, tile_w: int, tile_h: int) -> Image.Image:
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L").convert("RGB")
    image.thumbnail((tile_w - 20, tile_h - 48), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_w, tile_h), "white")
    tile.paste(image, ((tile_w - image.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.text((8, tile_h - 34), label[:45], fill=(0, 0, 0))
    return tile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--g57-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g56_nersemble_lam_eval/predictions"))
    parser.add_argument("--g59-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/predictions"))
    parser.add_argument("--g61-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/predictions"))
    parser.add_argument("--output", type=Path, default=Path("experiments/figures/g57_g61_nersemble_render_mask_audit_20260527.png"))
    args = parser.parse_args()

    adapter = load_json(args.adapter_manifest)
    serials = adapter["split"]["local_eval_serials"]
    views = {row["serial"]: row for row in adapter["views"]}
    rows: list[list[tuple[str, np.ndarray]]] = []
    for serial in serials:
        target_mask = read_mask(Path(views[serial]["mask_path"]))
        row: list[tuple[str, np.ndarray]] = [(f"{serial} GT alpha", target_mask)]
        for label, root in [
            ("G57 LAM source-sample", args.g57_root),
            ("G59 GT pointcloud", args.g59_root),
            ("G61 LAM mesh GT-bbox", args.g61_root),
        ]:
            mask = read_prediction_mask(root / f"cam_{serial}_frame_00000.png")
            if mask.shape != target_mask.shape:
                mask = cv2.resize(mask.astype(np.uint8), (target_mask.shape[1], target_mask.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
            row.append((f"{label} IoU={mask_iou(mask, target_mask):.3f}", mask))
        rows.append(row)

    tile_w, tile_h = 260, 250
    sheet = Image.new("RGB", (tile_w * 4, tile_h * len(rows)), "white")
    for row_i, row in enumerate(rows):
        for col_i, (label, mask) in enumerate(row):
            sheet.paste(tile_from_mask(mask, label, tile_w, tile_h), (col_i * tile_w, row_i * tile_h))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
