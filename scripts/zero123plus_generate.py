#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import torch
from PIL import Image, ImageOps
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler


def square_image(image: Image.Image, size: int | None) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGB", (side, side), (127, 127, 127))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2))
    if size is not None:
        canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
    return canvas


def split_grid(image: Image.Image, rows: int, cols: int) -> list[Image.Image]:
    width, height = image.size
    tile_w = width // cols
    tile_h = height // rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append(image.crop((c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h)))
    return tiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Zero123++ pseudo multi-view images.")
    parser.add_argument("--input", required=True, help="Input image path.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--model", default="sudo-ai/zero123plus-v1.2", help="HuggingFace model id.")
    parser.add_argument("--custom-pipeline", default="sudo-ai/zero123plus-pipeline")
    parser.add_argument("--steps", type=int, default=75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--input-size", type=int, default=512, help="Square input size. Use 0 to keep padded original size.")
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cols", type=int, default=2)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    input_path = Path(args.input)
    cond = square_image(Image.open(input_path), None if args.input_size <= 0 else args.input_size)
    cond.save(outdir / "input_square.png")

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

    generator = torch.Generator(device=args.device).manual_seed(args.seed)
    result = pipeline(cond, num_inference_steps=args.steps, generator=generator).images[0]
    result.save(outdir / "grid.png")

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
        "input": str(input_path),
        "model": args.model,
        "custom_pipeline": args.custom_pipeline,
        "steps": args.steps,
        "seed": args.seed,
        "device": args.device,
        "grid": {"rows": args.rows, "cols": args.cols, "file": "grid.png"},
        "views": view_records,
    }
    with open(outdir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved Zero123++ outputs to {outdir}")


if __name__ == "__main__":
    main()
