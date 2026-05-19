#!/usr/bin/env python3
"""Create head-centered first10 inputs for candidate-pool recovery."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def detect_faces(image: Image.Image) -> list[dict[str, Any]]:
    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    detections: list[dict[str, Any]] = []
    cascades = [
        ("frontal", "haarcascade_frontalface_default.xml"),
        ("profile", "haarcascade_profileface.xml"),
    ]
    for kind, name in cascades:
        cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / name))
        rects = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
        for x, y, w, h in rects:
            detections.append({"kind": kind, "x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        if kind == "profile":
            flipped = cv2.flip(gray, 1)
            rects_flip = cascade.detectMultiScale(flipped, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
            width = gray.shape[1]
            for x, y, w, h in rects_flip:
                detections.append(
                    {"kind": "profile_flipped", "x": int(width - x - w), "y": int(y), "w": int(w), "h": int(h)}
                )
    detections.sort(key=lambda item: item["w"] * item["h"], reverse=True)
    return detections


def crop_box_from_face(
    face: dict[str, Any],
    *,
    image_w: int,
    image_h: int,
    scale: float,
    y_shift: float,
) -> tuple[int, int, int, int]:
    x = float(face["x"])
    y = float(face["y"])
    w = float(face["w"])
    h = float(face["h"])
    cx = x + w / 2.0
    cy = y + h * y_shift
    side = max(w, h) * scale
    left = int(round(cx - side / 2.0))
    top = int(round(cy - side / 2.0))
    right = int(round(cx + side / 2.0))
    bottom = int(round(cy + side / 2.0))
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > image_w:
        left -= right - image_w
        right = image_w
    if bottom > image_h:
        top -= bottom - image_h
        bottom = image_h
    left = max(0, left)
    top = max(0, top)
    return left, top, right, bottom


def fallback_box(image_w: int, image_h: int) -> tuple[int, int, int, int]:
    side = min(image_w, image_h)
    left = max(0, (image_w - side) // 2)
    top = max(0, int((image_h - side) * 0.22))
    return left, top, left + side, top + side


def fit_square(image: Image.Image, box: tuple[int, int, int, int], target_size: int) -> Image.Image:
    crop = image.crop(box)
    crop = ImageOps.contain(crop, (target_size, target_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (target_size, target_size), (127, 127, 127))
    canvas.paste(crop, ((target_size - crop.width) // 2, (target_size - crop.height) // 2))
    return canvas


def make_contact_sheet(rows: list[dict[str, str]], repo: Path, output: Path) -> None:
    tile = 128
    label_h = 34
    pad = 8
    cols = 5
    sheet_rows = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (tile + pad), pad + sheet_rows * (tile + label_h + pad)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, row in enumerate(rows):
        r = idx // cols
        c = idx % cols
        x = pad + c * (tile + pad)
        y = pad + r * (tile + label_h + pad)
        draw.text((x, y), row["sample_id"], fill=(0, 0, 0))
        draw.text((x, y + 15), row.get("head_crop_gate_note", ""), fill=(80, 80, 80))
        image = Image.open(repo / row["input_path"]).convert("RGB")
        sheet.paste(image.resize((tile, tile), Image.Resampling.LANCZOS), (x, y + label_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--manifest", default="experiments/inputs/first10/manifest.csv")
    parser.add_argument("--out-dir", default="experiments/inputs/first10/head_crops")
    parser.add_argument("--out-manifest", default="experiments/inputs/first10/head_crops_manifest.csv")
    parser.add_argument("--contact-sheet", default="experiments/figures/first10_head_crop_inputs.png")
    parser.add_argument("--target-size", type=int, default=512)
    parser.add_argument("--face-scale", type=float, default=3.4)
    parser.add_argument("--face-y-shift", type=float, default=0.70)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    rows = read_rows(repo / args.manifest)
    out_dir = repo / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_rows: list[dict[str, str]] = []
    for row in rows:
        image = ImageOps.exif_transpose(Image.open(repo / row["input_path"])).convert("RGB")
        faces = detect_faces(image)
        if faces:
            face = faces[0]
            box = crop_box_from_face(
                face,
                image_w=image.width,
                image_h=image.height,
                scale=args.face_scale,
                y_shift=args.face_y_shift,
            )
            gate_note = f"{face['kind']}_face"
        else:
            face = {}
            box = fallback_box(image.width, image.height)
            gate_note = "fallback_crop"
        cropped = fit_square(image, box, args.target_size)
        out_path = out_dir / f"{row['sample_id']}.png"
        cropped.save(out_path)
        out_row = dict(row)
        out_row["original_input_path"] = row["input_path"]
        out_row["input_path"] = str(out_path.relative_to(repo))
        out_row["head_crop_box"] = ";".join(str(v) for v in box)
        out_row["head_crop_face"] = json_like(face)
        out_row["head_crop_gate_note"] = gate_note
        out_rows.append(out_row)
        print(f"saved {out_path.relative_to(repo)} ({gate_note})")

    columns = list(rows[0].keys())
    columns.insert(columns.index("input_path") + 1, "original_input_path")
    columns.extend(["head_crop_box", "head_crop_face", "head_crop_gate_note"])
    write_rows(repo / args.out_manifest, out_rows, columns)
    make_contact_sheet(out_rows, repo, repo / args.contact_sheet)
    (out_dir / "README.md").write_text(
        "# First10 Head Crops\n\n"
        "Head-centered crops for candidate-pool recovery. These inputs must pass "
        "visual/VLM audit before being used for new Zero123++ generation.\n",
        encoding="utf-8",
    )
    print(f"manifest={args.out_manifest}")
    print(f"contact_sheet={args.contact_sheet}")


def json_like(value: dict[str, Any]) -> str:
    if not value:
        return ""
    return ";".join(f"{key}={value[key]}" for key in sorted(value))


if __name__ == "__main__":
    main()
