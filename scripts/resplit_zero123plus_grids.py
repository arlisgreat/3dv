#!/usr/bin/env python3
"""Re-split existing Zero123++ grids into correct per-view tiles.

Historical repo outputs used rows=2, cols=3, but the saved Zero123++ v1.2 grids
are 3 rows x 2 columns. This script preserves the original grid/metadata and
writes corrected view_*.png files into a new output root.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

from zero123plus_generate import split_grid


def resplit_scene(src_dir: Path, dst_dir: Path, *, rows: int, cols: int, overwrite: bool) -> None:
    if dst_dir.exists():
        if not overwrite:
            raise FileExistsError(f"{dst_dir} exists. Use --overwrite.")
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in ("grid.png", "input_square.png"):
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, dst_dir / name)

    metadata_path = src_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    grid = Image.open(src_dir / "grid.png").convert("RGB")
    tiles = split_grid(grid, rows, cols)
    azimuths = [30, 90, 150, 210, 270, 330]
    elevations = [20, -10, 20, -10, 20, -10]
    view_records = []
    for idx, tile in enumerate(tiles):
        az = azimuths[idx] if idx < len(azimuths) else None
        el = elevations[idx] if idx < len(elevations) else None
        if az is not None and el is not None:
            name = f"view_{idx:02d}_az{az:03d}_el{el:+03d}.png"
        else:
            name = f"view_{idx:02d}.png"
        tile.save(dst_dir / name)
        view_records.append({"index": idx, "file": name, "azimuth": az, "elevation": el})

    metadata["views"] = view_records
    metadata["grid"]["rows"] = rows
    metadata["grid"]["cols"] = cols
    metadata["resplit_from"] = str(src_dir)
    metadata["resplit_note"] = "Corrected Zero123++ grid split from historical rows=2, cols=3 to rows=3, cols=2."
    (dst_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    source_root = repo / args.source_root
    output_root = repo / args.output_root
    count = 0
    for src_dir in sorted(source_root.glob("*_steps*")):
        if not (src_dir / "grid.png").exists():
            continue
        dst_dir = output_root / src_dir.name
        resplit_scene(src_dir, dst_dir, rows=args.rows, cols=args.cols, overwrite=args.overwrite)
        count += 1
        print(f"resplit {src_dir.relative_to(repo)} -> {dst_dir.relative_to(repo)}")
    print(f"resplit_scenes={count}")


if __name__ == "__main__":
    main()
