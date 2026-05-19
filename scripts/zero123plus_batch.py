#!/usr/bin/env python3
"""Generate Zero123++ pseudo views for a manifest without reloading the model."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
from PIL import Image

from zero123plus_generate import split_grid, square_image


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_one(
    pipeline: DiffusionPipeline,
    row: dict[str, str],
    repo: Path,
    out_root: Path,
    args: argparse.Namespace,
) -> Path:
    input_path = repo / row["input_path"]
    outdir = out_root / f"{row['sample_id']}_steps{args.steps}"
    outdir.mkdir(parents=True, exist_ok=True)
    grid_path = outdir / "grid.png"
    if args.skip_existing and grid_path.exists():
        print(f"Skip existing: {outdir}")
        return outdir

    cond = square_image(Image.open(input_path), None if args.input_size <= 0 else args.input_size)
    cond.save(outdir / "input_square.png")

    generator = torch.Generator(device=args.device).manual_seed(args.seed)
    result = pipeline(cond, num_inference_steps=args.steps, generator=generator).images[0]
    result.save(grid_path)

    tiles = split_grid(result, args.rows, args.cols)
    azimuths = [30, 90, 150, 210, 270, 330]
    elevations = [20, -10, 20, -10, 20, -10] if "v1.2" in args.model else [30, -20, 30, -20, 30, -20]

    view_records = []
    for idx, tile in enumerate(tiles):
        az = azimuths[idx] if idx < len(azimuths) else None
        el = elevations[idx] if idx < len(elevations) else None
        if az is not None and el is not None:
            name = f"view_{idx:02d}_az{az:03d}_el{el:+03d}.png"
        else:
            name = f"view_{idx:02d}.png"
        tile.save(outdir / name)
        view_records.append({"index": idx, "file": name, "azimuth": az, "elevation": el})

    metadata = {
        "sample_id": row["sample_id"],
        "input": str(input_path),
        "source": row,
        "model": args.model,
        "custom_pipeline": args.custom_pipeline,
        "steps": args.steps,
        "seed": args.seed,
        "device": args.device,
        "grid": {"rows": args.rows, "cols": args.cols, "file": "grid.png"},
        "views": view_records,
    }
    with (outdir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved Zero123++ outputs to {outdir}")
    return outdir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="experiments/inputs/first10/manifest.csv")
    parser.add_argument("--out-root", default="experiments/pseudo_views/zero123plus_first10")
    parser.add_argument("--model", default="sudo-ai/zero123plus-v1.2")
    parser.add_argument("--custom-pipeline", default="sudo-ai/zero123plus-pipeline")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--input-size", type=int, default=512)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    rows = load_rows(repo / args.manifest)
    if args.limit > 0:
        rows = rows[: args.limit]

    dtype = torch.float16 if args.device.startswith("cuda") else torch.float32
    pipeline = DiffusionPipeline.from_pretrained(
        args.model,
        custom_pipeline=args.custom_pipeline,
        torch_dtype=dtype,
    )
    pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipeline.scheduler.config,
        timestep_spacing="trailing",
    )
    pipeline.to(args.device)

    out_root = repo / args.out_root
    for row in rows:
        generate_one(pipeline, row, repo, out_root, args)


if __name__ == "__main__":
    main()
