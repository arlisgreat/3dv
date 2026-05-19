#!/usr/bin/env python3
"""Build trusted-region mask atlases for selected Zero123++ pseudo views."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


BACKGROUND_RGB = np.array([127, 127, 127], dtype=np.int16)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def raw_foreground_mask(image: Image.Image, threshold: float) -> np.ndarray:
    arr = np.asarray(image).astype(np.int16)
    dist = np.linalg.norm(arr - BACKGROUND_RGB, axis=2)
    return dist > threshold


def clean_foreground_mask(mask: np.ndarray, min_component_ratio: float = 0.002) -> np.ndarray:
    h, w = mask.shape
    mask_u8 = (mask.astype(np.uint8) * 255)
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel, iterations=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8)
    keep = np.zeros_like(mask_u8)
    min_area = max(16, int(h * w * min_component_ratio))
    for idx in range(1, count):
        area = int(stats[idx, cv2.CC_STAT_AREA])
        if area >= min_area:
            keep[labels == idx] = 255
    return keep > 0


def face_count(image: Image.Image) -> int:
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        return 0
    faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
    return int(len(faces))


def mask_stats(mask: np.ndarray) -> tuple[float, float, float]:
    h, w = mask.shape
    coverage = float(mask.mean())
    if not mask.any():
        return coverage, 0.0, 1.0
    ys, xs = np.where(mask)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    bbox_area = ((x1 - x0 + 1) * (y1 - y0 + 1)) / float(w * h)
    cx = (x0 + x1) / 2.0 / w
    cy = (y0 + y1) / 2.0 / h
    center_offset = float(((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5)
    return coverage, bbox_area, center_offset


def safety_decision(
    reliability_row: dict[str, str],
    clip_row: dict[str, str],
    coverage: float,
    bbox_area: float,
    bbox_occupancy: float,
    center_offset: float,
    faces: int,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    rel_labels = {x for x in reliability_row.get("failure_labels", "").split(";") if x}
    clip_labels = {x for x in clip_row.get("failure_labels", "").split(";") if x}
    reliability = float(reliability_row["reliability_score"])
    trusted = float(clip_row["trusted_score"])

    if reliability < 60:
        reasons.append("low_reliability")
    if trusted < 60:
        reasons.append("low_trusted_score")
    if "full_photo_or_background_rotation" in rel_labels:
        reasons.append("full_photo_or_background_rotation")
    if coverage < 0.04:
        reasons.append("tiny_or_empty_mask")
    if coverage > 0.82:
        reasons.append("overfull_mask")
    if bbox_area > 0.88 and faces == 0:
        reasons.append("overwide_mask_without_face")
    if faces == 0 and bbox_area > 0.68 and (coverage > 0.60 or bbox_occupancy < 0.45):
        reasons.append("photo_frame_geometry_risk")
    if center_offset > 0.34:
        reasons.append("off_center_mask")
    if "hair_hallucination_risk" in rel_labels and trusted < 65:
        reasons.append("hair_hallucination_risk")
    if "glasses_identity_risk" in rel_labels and trusted < 65:
        reasons.append("glasses_identity_risk")
    if "occlusion_identity_risk" in rel_labels and trusted < 65:
        reasons.append("occlusion_identity_risk")

    return len(reasons) == 0, reasons


def apply_mask_overlay(image: Image.Image, mask: np.ndarray, accepted: bool) -> Image.Image:
    arr = np.asarray(image).astype(np.float32)
    outside = arr * 0.25 + np.array([230, 230, 230], dtype=np.float32) * 0.75
    out = np.where(mask[..., None], arr, outside).clip(0, 255).astype(np.uint8)
    boundary = cv2.morphologyEx(mask.astype(np.uint8) * 255, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    color = np.array([40, 180, 90], dtype=np.uint8) if accepted else np.array([210, 45, 45], dtype=np.uint8)
    out[boundary > 0] = color
    return Image.fromarray(out)


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, "white")
    item = image.copy()
    item.thumbnail(size, Image.Resampling.LANCZOS)
    canvas.paste(item, ((size[0] - item.width) // 2, (size[1] - item.height) // 2))
    return canvas


def make_atlas(images: list[Image.Image], labels: list[str], tile_size: tuple[int, int]) -> Image.Image:
    label_h = 28
    pad = 8
    w = pad + len(images) * (tile_size[0] + pad)
    h = label_h + tile_size[1] + 2 * pad
    atlas = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(atlas)
    for idx, image in enumerate(images):
        x = pad + idx * (tile_size[0] + pad)
        draw.text((x, pad), labels[idx], fill=(0, 0, 0))
        atlas.paste(fit(image, tile_size), (x, pad + label_h))
    return atlas


def write_sample_outputs(
    repo: Path,
    out_root: Path,
    sample_id: str,
    rows: list[dict[str, str]],
    tile_size: tuple[int, int],
) -> tuple[Path, Path, list[dict[str, object]]]:
    sample_dir = out_root / sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    overlays: list[Image.Image] = []
    masks: list[Image.Image] = []
    labels: list[str] = []
    manifest_rows: list[dict[str, object]] = []
    for tile_idx, row in enumerate(rows):
        image = load_image(repo / row["view_file"])
        raw_mask = raw_foreground_mask(image, threshold=float(row["mask_threshold"]))
        mask = clean_foreground_mask(raw_mask)
        coverage, bbox_area, center_offset = mask_stats(mask)
        bbox_occupancy = coverage / bbox_area if bbox_area > 0 else 0.0
        faces = face_count(image)
        accepted, reasons = safety_decision(
            row["reliability_row"], row["clip_row"], coverage, bbox_area, bbox_occupancy, center_offset, faces
        )
        trusted_mask = mask if accepted else np.zeros_like(mask)
        overlays.append(apply_mask_overlay(image, trusted_mask, accepted))
        masks.append(Image.fromarray((trusted_mask.astype(np.uint8) * 255)).convert("RGB"))
        state = "ok" if accepted else "reject"
        labels.append(f"v{row['view_index']} {state}")
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "tile_index": tile_idx,
                "view_index": row["view_index"],
                "view_file": row["view_file"],
                "accepted": accepted,
                "reject_reasons": reasons,
                "mask_coverage": coverage,
                "mask_bbox_area": bbox_area,
                "mask_bbox_occupancy": bbox_occupancy,
                "mask_center_offset": center_offset,
                "face_count": faces,
                "reliability_score": float(row["reliability_row"]["reliability_score"]),
                "trusted_score": float(row["clip_row"]["trusted_score"]),
            }
        )

    overlay_atlas = make_atlas(overlays, labels, tile_size)
    mask_atlas = make_atlas(masks, labels, tile_size)
    overlay_path = sample_dir / "overlay_atlas.png"
    mask_path = sample_dir / "mask_atlas.png"
    overlay_atlas.save(overlay_path)
    mask_atlas.save(mask_path)
    (sample_dir / "manifest.json").write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
    return overlay_path, mask_path, manifest_rows


def aggregate_figure(sample_overlays: list[tuple[str, Path]], out_path: Path, tile_size: tuple[int, int]) -> None:
    rows = []
    for sample_id, path in sample_overlays:
        atlas = Image.open(path).convert("RGB")
        rows.append((sample_id, atlas))
    label_w = 180
    pad = 8
    w = label_w + max(row.width for _, row in rows) + 2 * pad
    h = pad + sum(row.height + pad for _, row in rows)
    sheet = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(sheet)
    y = pad
    for sample_id, atlas in rows:
        draw.text((pad, y + tile_size[1] // 2), sample_id, fill=(0, 0, 0))
        sheet.paste(atlas, (label_w, y))
        y += atlas.height + pad
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--run", default="steps75")
    parser.add_argument("--budget", default="4")
    parser.add_argument("--mask-threshold", default="22")
    parser.add_argument("--budget-csv", default="experiments/metrics/view_budget_clip_selection_first10_steps20_75.csv")
    parser.add_argument("--clip-csv", default="experiments/metrics/pseudo_view_clip_consistency_first10_steps20_75.csv")
    parser.add_argument("--reliability-csv", default="experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv")
    parser.add_argument("--out-root", default="")
    parser.add_argument("--view-output", default="")
    parser.add_argument("--summary-output", default="")
    parser.add_argument("--figure-output", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    budget_csv = repo / args.budget_csv
    clip_csv = repo / args.clip_csv
    reliability_csv = repo / args.reliability_csv

    clip_by_key = {
        (row["sample_id"], row["run"], row["view_index"]): row
        for row in read_csv(clip_csv)
    }
    reliability_by_key = {
        (row["sample_id"], row["run"], row["view_index"]): row
        for row in read_csv(reliability_csv)
    }
    selected = [
        row
        for row in read_csv(budget_csv)
        if row["run"] == args.run and row["budget"] == args.budget
    ]

    out_root = repo / (
        args.out_root
        if args.out_root
        else f"experiments/pseudo_views/trusted_region_masks_{args.run}_budget{args.budget}"
    )
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        for view_index, view_file in zip(row["selected_view_indices"].split(";"), row["selected_view_files"].split(";")):
            key = (row["sample_id"], row["run"], view_index)
            rows_by_sample[row["sample_id"]].append(
                {
                    "sample_id": row["sample_id"],
                    "group": row["group"],
                    "run": row["run"],
                    "steps": row["steps"],
                    "budget": row["budget"],
                    "view_index": view_index,
                    "view_file": view_file,
                    "mask_threshold": args.mask_threshold,
                    "clip_row": clip_by_key[key],
                    "reliability_row": reliability_by_key[key],
                }
            )

    tile_size = (144, 144)
    view_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []
    sample_overlays: list[tuple[str, Path]] = []
    for sample_id, sample_rows in sorted(rows_by_sample.items()):
        overlay_path, mask_path, manifest_rows = write_sample_outputs(repo, out_root, sample_id, sample_rows, tile_size)
        sample_overlays.append((sample_id, overlay_path))
        accepted_count = sum(1 for row in manifest_rows if row["accepted"])
        for row in manifest_rows:
            view_rows.append(
                {
                    "sample_id": str(row["sample_id"]),
                    "group": sample_rows[0]["group"],
                    "run": sample_rows[0]["run"],
                    "steps": sample_rows[0]["steps"],
                    "budget": sample_rows[0]["budget"],
                    "tile_index": str(row["tile_index"]),
                    "view_index": str(row["view_index"]),
                    "view_file": str(row["view_file"]),
                    "mask_atlas_file": str(mask_path.relative_to(repo)),
                    "overlay_atlas_file": str(overlay_path.relative_to(repo)),
                    "accepted": str(row["accepted"]).lower(),
                    "reject_reasons": ";".join(row["reject_reasons"]),
                    "mask_coverage": f"{float(row['mask_coverage']):.6f}",
                    "mask_bbox_area": f"{float(row['mask_bbox_area']):.6f}",
                    "mask_bbox_occupancy": f"{float(row['mask_bbox_occupancy']):.6f}",
                    "mask_center_offset": f"{float(row['mask_center_offset']):.6f}",
                    "face_count": str(row["face_count"]),
                    "reliability_score": f"{float(row['reliability_score']):.3f}",
                    "trusted_score": f"{float(row['trusted_score']):.3f}",
                }
            )
        summary_rows.append(
            {
                "sample_id": sample_id,
                "group": sample_rows[0]["group"],
                "run": sample_rows[0]["run"],
                "steps": sample_rows[0]["steps"],
                "budget": sample_rows[0]["budget"],
                "selected_view_count": str(len(manifest_rows)),
                "accepted_view_count": str(accepted_count),
                "accepted_ratio": f"{accepted_count / max(1, len(manifest_rows)):.3f}",
                "mean_trusted_score_selected": f"{np.mean([float(row['trusted_score']) for row in manifest_rows]):.3f}",
                "min_trusted_score_selected": f"{min(float(row['trusted_score']) for row in manifest_rows):.3f}",
                "manifest_file": str((out_root / sample_id / "manifest.json").relative_to(repo)),
                "mask_atlas_file": str((out_root / sample_id / "mask_atlas.png").relative_to(repo)),
                "overlay_atlas_file": str((out_root / sample_id / "overlay_atlas.png").relative_to(repo)),
            }
        )

    view_columns = [
        "sample_id",
        "group",
        "run",
        "steps",
        "budget",
        "tile_index",
        "view_index",
        "view_file",
        "mask_atlas_file",
        "overlay_atlas_file",
        "accepted",
        "reject_reasons",
        "mask_coverage",
        "mask_bbox_area",
        "mask_bbox_occupancy",
        "mask_center_offset",
        "face_count",
        "reliability_score",
        "trusted_score",
    ]
    summary_columns = [
        "sample_id",
        "group",
        "run",
        "steps",
        "budget",
        "selected_view_count",
        "accepted_view_count",
        "accepted_ratio",
        "mean_trusted_score_selected",
        "min_trusted_score_selected",
        "manifest_file",
        "mask_atlas_file",
        "overlay_atlas_file",
    ]
    view_output = repo / (
        args.view_output
        if args.view_output
        else f"experiments/metrics/trusted_region_masks_first10_{args.run}_budget{args.budget}.csv"
    )
    summary_output = repo / (
        args.summary_output
        if args.summary_output
        else f"experiments/metrics/trusted_region_mask_summary_first10_{args.run}_budget{args.budget}.csv"
    )
    figure_output = repo / (
        args.figure_output
        if args.figure_output
        else f"experiments/figures/trusted_region_masks_first10_{args.run}_budget{args.budget}.png"
    )
    write_csv(view_output, view_rows, view_columns)
    write_csv(
        summary_output,
        summary_rows,
        summary_columns,
    )
    aggregate_figure(
        sample_overlays,
        figure_output,
        tile_size,
    )
    readme = """# Trusted Region Masks

Mask atlases for the CLIP-ranked Zero123++ selected views.

The atlases are diagnostics for deciding which generated regions are safe
enough to pass into later Gaussian/PanoHead fusion. Rejected tiles are written
as empty masks and red overlays.
"""
    (out_root / "README.md").write_text(readme, encoding="utf-8")

    print(f"view_rows={len(view_rows)}")
    print(f"summary_rows={len(summary_rows)}")
    print(f"accepted_views={sum(row['accepted'] == 'true' for row in view_rows)}")
    print(f"out_root={out_root.relative_to(repo)}")


if __name__ == "__main__":
    main()
