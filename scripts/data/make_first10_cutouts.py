#!/usr/bin/env python3
"""Create gray-background subject cutouts for the first10 input manifest."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from rembg import new_session, remove


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def expand_bbox(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    pad_ratio: float,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    pad = int(max(x1 - x0, y1 - y0) * pad_ratio)
    return max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad)


def make_square_cutout(image: Image.Image, target_size: int, pad_ratio: float) -> tuple[Image.Image, dict[str, str]]:
    rgba = image.convert("RGBA")
    bbox = alpha_bbox(rgba)
    if bbox is None:
        bbox = (0, 0, rgba.width, rgba.height)
    padded = expand_bbox(bbox, rgba.width, rgba.height, pad_ratio)
    crop = rgba.crop(padded)
    scale = min((target_size * 0.86) / crop.width, (target_size * 0.92) / crop.height)
    new_size = (max(1, int(crop.width * scale)), max(1, int(crop.height * scale)))
    crop = crop.resize(new_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (127, 127, 127, 255))
    x = (target_size - crop.width) // 2
    y = int(target_size * 0.52 - crop.height / 2)
    y = max(0, min(target_size - crop.height, y))
    canvas.alpha_composite(crop, (x, y))
    alpha = np.asarray(rgba.getchannel("A"))
    stats = {
        "alpha_coverage": f"{float((alpha > 8).mean()):.6f}",
        "alpha_bbox": ";".join(str(v) for v in bbox),
        "padded_bbox": ";".join(str(v) for v in padded),
        "cutout_scale": f"{scale:.6f}",
    }
    return canvas.convert("RGB"), stats


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, "white")
    item = image.copy()
    item.thumbnail(size, Image.Resampling.LANCZOS)
    canvas.paste(item, ((size[0] - item.width) // 2, (size[1] - item.height) // 2))
    return canvas


def write_contact_sheet(paths: list[tuple[str, Path]], out_path: Path) -> None:
    tile = (132, 132)
    label_h = 30
    pad = 8
    cols = 5
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (tile[0] + pad), pad + rows * (tile[1] + label_h + pad)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (sample_id, path) in enumerate(paths):
        r = idx // cols
        c = idx % cols
        x = pad + c * (tile[0] + pad)
        y = pad + r * (tile[1] + label_h + pad)
        draw.text((x, y), sample_id, fill=(0, 0, 0))
        sheet.paste(fit(Image.open(path).convert("RGB"), tile), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--manifest", default="experiments/inputs/first10/manifest.csv")
    parser.add_argument("--out-dir", default="experiments/inputs/first10/cutouts")
    parser.add_argument("--out-manifest", default="experiments/inputs/first10/cutouts_manifest.csv")
    parser.add_argument("--contact-sheet", default="experiments/figures/first10_cutout_inputs.png")
    parser.add_argument("--target-size", type=int, default=512)
    parser.add_argument("--pad-ratio", type=float, default=0.10)
    parser.add_argument("--model", default="u2net")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    out_dir = repo / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(repo / args.manifest)
    session = new_session(args.model)
    out_rows: list[dict[str, str]] = []
    sheet_paths: list[tuple[str, Path]] = []
    for row in rows:
        input_path = repo / row["input_path"]
        source = ImageOps.exif_transpose(Image.open(input_path)).convert("RGB")
        cut = remove(source, session=session)
        square, stats = make_square_cutout(cut, args.target_size, args.pad_ratio)
        out_path = out_dir / f"{row['sample_id']}.png"
        square.save(out_path)
        out_row = dict(row)
        out_row["original_input_path"] = row["input_path"]
        out_row["input_path"] = str(out_path.relative_to(repo))
        out_row.update(stats)
        out_rows.append(out_row)
        sheet_paths.append((row["sample_id"], out_path))
        print(f"saved {out_path.relative_to(repo)}")

    columns = list(rows[0].keys())
    columns.insert(columns.index("input_path") + 1, "original_input_path")
    columns.extend(["alpha_coverage", "alpha_bbox", "padded_bbox", "cutout_scale"])
    write_rows(repo / args.out_manifest, out_rows, columns)
    write_contact_sheet(sheet_paths, repo / args.contact_sheet)
    readme = """# First10 Cutouts

Gray-background subject cutouts generated with `rembg` from the processed
first10 inputs. These are intended for the Zero123++ input-format ablation:
raw portrait crop versus subject-only cutout.

Contact sheet:

```text
experiments/figures/first10_cutout_inputs.png
```
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")
    print(f"manifest={args.out_manifest}")


if __name__ == "__main__":
    main()
