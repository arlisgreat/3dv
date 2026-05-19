#!/usr/bin/env python3
"""Make a visual audit sheet for pseudo-view candidate pools."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_thumb(path: Path, size: int) -> Image.Image:
    if not path.is_file():
        return Image.new("RGB", (size, size), (220, 220, 220))
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (245, 245, 245))
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def sample_images(repo: Path, root: Path, variant: str, sample_id: str, max_views: int) -> list[Path]:
    images_dir = repo / root / variant / sample_id / "images"
    if not images_dir.exists():
        return []
    return sorted(images_dir.glob("*.png"))[:max_views]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("experiments/inputs/first10/manifest.csv"))
    parser.add_argument("--candidate-root", type=Path, default=Path("experiments/downstream_datasets"))
    parser.add_argument("--variants", nargs="+", default=["raw75_budget4", "cutout75_budget4_masked"])
    parser.add_argument("--max-views", type=int, default=4)
    parser.add_argument("--thumb", type=int, default=84)
    parser.add_argument("--output", type=Path, default=Path("experiments/figures/first10_candidate_pool_visual_audit_20260519.png"))
    args = parser.parse_args()

    repo = Path.cwd()
    rows = read_csv(repo / args.manifest)
    label_w = 160
    pad = 8
    group_gap = 14
    header_h = 54
    thumb = args.thumb
    cols_per_variant = args.max_views
    width = label_w + len(args.variants) * cols_per_variant * thumb + (len(args.variants) + 2) * pad
    row_h = thumb + 26
    height = header_h + len(rows) * row_h + 40
    sheet = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(sheet)
    font = choose_font(12)
    small = choose_font(10)

    draw.text((pad, 8), "first10 candidate pool visual audit", fill=(20, 20, 20), font=font)
    draw.text(
        (pad, 28),
        "These are candidate pools, not validated training data. Many cells show split bodies, rotated photo cards, and cropped fragments.",
        fill=(65, 65, 65),
        font=small,
    )
    x = label_w + pad
    for variant in args.variants:
        draw.text((x, header_h - 18), variant, fill=(20, 20, 20), font=small)
        x += cols_per_variant * thumb + pad

    y = header_h
    for row in rows:
        sample_id = row["sample_id"]
        group = row.get("group", "")
        draw.text((pad, y + 24), sample_id, fill=(15, 15, 15), font=small)
        draw.text((pad, y + 40), group, fill=(80, 80, 80), font=small)
        x = label_w + pad
        for variant in args.variants:
            paths = sample_images(repo, args.candidate_root, variant, sample_id, args.max_views)
            for idx in range(args.max_views):
                image_path = paths[idx] if idx < len(paths) else Path()
                thumb_img = load_thumb(image_path, thumb)
                sheet.paste(thumb_img, (x + idx * thumb, y))
            x += cols_per_variant * thumb + pad
        y += row_h
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(repo / args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
