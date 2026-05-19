#!/usr/bin/env python3
"""Render simple FLAME OBJ depth/confidence priors into RI3D first2 scenes."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DEFAULT_SAMPLES = ("web_clean_frontal_03", "web_clean_frontal_01")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_obj(path: Path) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                _, x, y, z, *_ = line.split()
                vertices.append([float(x), float(y), float(z)])
            elif line.startswith("f "):
                parts = line.split()[1:]
                ids = [int(part.split("/")[0]) - 1 for part in parts]
                if len(ids) < 3:
                    continue
                for i in range(1, len(ids) - 1):
                    faces.append([ids[0], ids[i], ids[i + 1]])
    if not vertices or not faces:
        raise ValueError(f"OBJ has no usable vertices/faces: {path}")
    return np.asarray(vertices, dtype=np.float32), np.asarray(faces, dtype=np.int32)


def normalize_vertices(vertices: np.ndarray) -> np.ndarray:
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2.0
    scale = float((maxs - mins).max())
    if scale < 1e-6:
        raise ValueError("Cannot normalize degenerate mesh")
    return (vertices - center) / scale


def rotation_matrix(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    az = math.radians(-azimuth_deg)
    el = math.radians(elevation_deg)
    cy, sy = math.cos(az), math.sin(az)
    cx, sx = math.cos(el), math.sin(el)
    ry = np.asarray([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
    rx = np.asarray([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float32)
    return rx @ ry


def rasterize(vertices: np.ndarray, faces: np.ndarray, azimuth: float, elevation: float, size: int) -> tuple[np.ndarray, np.ndarray]:
    rot = vertices @ rotation_matrix(azimuth, elevation).T
    xy = rot[:, :2]
    z = rot[:, 2]
    xy_scale = max(float(np.abs(xy).max()), 1e-6)
    xy = xy / xy_scale * 0.42
    u = (xy[:, 0] + 0.5) * (size - 1)
    v = (0.5 - xy[:, 1]) * (size - 1)
    projected = np.stack([u, v, z], axis=1)
    zbuf = np.full((size, size), np.inf, dtype=np.float32)

    for face in faces:
        tri = projected[face]
        x0, y0, z0 = tri[0]
        x1, y1, z1 = tri[1]
        x2, y2, z2 = tri[2]
        xmin = max(0, int(math.floor(min(x0, x1, x2))))
        xmax = min(size - 1, int(math.ceil(max(x0, x1, x2))))
        ymin = max(0, int(math.floor(min(y0, y1, y2))))
        ymax = min(size - 1, int(math.ceil(max(y0, y1, y2))))
        if xmax < xmin or ymax < ymin:
            continue
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(float(denom)) < 1e-8:
            continue
        for yy in range(ymin, ymax + 1):
            py = yy + 0.5
            for xx in range(xmin, xmax + 1):
                px = xx + 0.5
                w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
                w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
                w2 = 1.0 - w0 - w1
                if w0 < -1e-4 or w1 < -1e-4 or w2 < -1e-4:
                    continue
                zz = w0 * z0 + w1 * z1 + w2 * z2
                if zz < zbuf[yy, xx]:
                    zbuf[yy, xx] = zz

    mask = np.isfinite(zbuf)
    if not mask.any():
        depth = np.ones((size, size), dtype=np.float32)
        return depth, np.zeros((size, size), dtype=np.float32)

    valid_z = zbuf[mask]
    z_norm = (zbuf - float(valid_z.min())) / max(float(valid_z.max() - valid_z.min()), 1e-6)
    depth = np.full((size, size), float(1.0 + 0.35 * np.median(z_norm[mask])), dtype=np.float32)
    depth[mask] = 1.0 + 0.35 * z_norm[mask]
    conf = np.zeros((size, size), dtype=np.float32)
    conf[mask] = 5.0
    return depth.astype(np.float32), conf


def find_tracking_obj(lam_root: Path, sample_id: str) -> Path:
    tracking_root = lam_root / "tracking_output" / "tracking"
    candidates: list[Path] = []
    for config in sorted(tracking_root.glob("*/config.yml")):
        text = config.read_text(encoding="utf-8", errors="ignore")
        if f"sequence: {sample_id}" not in text:
            continue
        obj = config.parent / "train" / "mesh" / "frame_00000_499_lmk_init_all.obj"
        if obj.exists():
            candidates.append(obj)
    if not candidates:
        raise FileNotFoundError(f"No LAM tracking OBJ found for {sample_id} under {tracking_root}")
    return candidates[-1]


def copy_scene(src: Path, dst: Path, overwrite: bool) -> None:
    if dst.exists():
        if not overwrite:
            raise FileExistsError(f"{dst} exists. Use --overwrite to rebuild it.")
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("point_cloud.ply"))


def save_depth_preview(depth: np.ndarray, conf: np.ndarray, path: Path) -> None:
    valid = conf > 0.5
    if valid.any():
        vals = depth[valid]
        norm = (depth - float(vals.min())) / max(float(vals.max() - vals.min()), 1e-6)
    else:
        norm = np.zeros_like(depth)
    rgb = np.zeros((*depth.shape, 3), dtype=np.uint8)
    rgb[..., 0] = np.clip(norm * 255, 0, 255).astype(np.uint8)
    rgb[..., 1] = np.clip((1.0 - norm) * 180, 0, 255).astype(np.uint8)
    rgb[..., 2] = np.clip(conf / 5.0 * 255, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(path)


def convert_scene(
    *,
    src_scene: Path,
    dst_scene: Path,
    prior_scene: Path,
    lam_root: Path,
    variant: str,
    sample_id: str,
    overwrite: bool,
) -> dict[str, Any]:
    copy_scene(src_scene, dst_scene, overwrite=overwrite)
    transforms = load_json(dst_scene / "transforms.json")
    image_size = int(transforms["w"])
    obj_path = find_tracking_obj(lam_root, sample_id)
    vertices, faces = parse_obj(obj_path)
    vertices = normalize_vertices(vertices)

    depth_dir = prior_scene / "depth"
    conf_dir = prior_scene / "conf"
    mask_dir = prior_scene / "mask"
    preview_dir = prior_scene / "preview"
    for path in (depth_dir, conf_dir, mask_dir, preview_dir):
        path.mkdir(parents=True, exist_ok=True)

    depths: list[np.ndarray] = []
    confs: list[np.ndarray] = []
    frame_rows: list[dict[str, Any]] = []
    n_views = len(transforms["frames"])
    for frame in transforms["frames"]:
        stem = Path(frame["file_path"]).stem
        depth, conf = rasterize(
            vertices,
            faces,
            azimuth=float(frame.get("azimuth") or 0.0),
            elevation=float(frame.get("elevation") or 0.0),
            size=image_size,
        )
        np.save(depth_dir / f"{stem}.npy", depth)
        np.save(conf_dir / f"{stem}.npy", conf)
        mask_image = Image.fromarray((conf > 0.5).astype(np.uint8) * 255, mode="L")
        mask_image.save(mask_dir / f"{stem}.png")
        save_depth_preview(depth, conf, preview_dir / f"{stem}.png")

        depth_rel = dst_scene / "images" / "depth_rel"
        np.save(depth_rel / f"inpv2{stem}_{n_views}.npy", depth)
        np.save(depth_rel / f"inp_dust3r{stem}_{n_views}.npy", depth)
        depths.append(depth)
        confs.append(conf)

        valid = conf > 0.5
        frame["geometry_prior"] = {
            "source": "lam_tracking_flame_obj",
            "mode": "replace_depth_and_conf",
            "obj_path": str(obj_path),
            "depth_path": str((depth_dir / f"{stem}.npy").relative_to(prior_scene)),
            "conf_path": str((conf_dir / f"{stem}.npy").relative_to(prior_scene)),
            "mask_path": str((mask_dir / f"{stem}.png").relative_to(prior_scene)),
            "valid_pixel_ratio": float(valid.mean()),
            "depth_min": float(depth[valid].min()) if valid.any() else None,
            "depth_max": float(depth[valid].max()) if valid.any() else None,
        }
        frame_rows.append(frame["geometry_prior"])

    np.save(dst_scene / f"depths{n_views}.npy", np.stack(depths, axis=0))
    np.save(dst_scene / f"confs{n_views}.npy", np.stack(confs, axis=0))
    write_json(dst_scene / "transforms.json", transforms)

    source_metadata = load_json(dst_scene / "source_metadata.json")
    source_metadata["geometry_prior"] = {
        "source": "lam_tracking_flame_obj",
        "mode": "replace_depth_and_conf",
        "obj_path": str(obj_path),
        "prior_scene": str(prior_scene),
        "frame_count": n_views,
        "mean_valid_pixel_ratio": float(np.mean([row["valid_pixel_ratio"] for row in frame_rows])),
    }
    write_json(dst_scene / "source_metadata.json", source_metadata)
    write_json(
        prior_scene / "metadata.json",
        {
            "variant": variant,
            "sample_id": sample_id,
            "source_scene": str(src_scene),
            "ri3d_scene": str(dst_scene),
            "obj_path": str(obj_path),
            "image_size": image_size,
            "frames": frame_rows,
        },
    )
    return {
        "variant": variant,
        "sample_id": sample_id,
        "source_scene": str(src_scene),
        "ri3d_scene": str(dst_scene),
        "prior_scene": str(prior_scene),
        "obj_path": str(obj_path),
        "view_count": n_views,
        "mean_valid_pixel_ratio": float(np.mean([row["valid_pixel_ratio"] for row in frame_rows])),
    }


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_proxy_sheet(rows: list[dict[str, Any]], output: Path, thumb: int = 96) -> None:
    font = choose_font(13)
    label_h = 36
    pad = 8
    cells: list[tuple[str, list[Image.Image]]] = []
    for row in rows:
        prior_scene = Path(row["prior_scene"])
        previews = [Image.open(path).convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS) for path in sorted((prior_scene / "preview").glob("*.png"))]
        cells.append((f"{row['sample_id']} | {row['variant']} | valid={row['mean_valid_pixel_ratio']:.3f}", previews))
    max_views = max(len(images) for _, images in cells)
    width = pad * 2 + max_views * thumb
    height = pad + len(cells) * (label_h + thumb + pad)
    sheet = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    y = pad
    for label, images in cells:
        draw.text((pad, y), label, fill=(20, 20, 20), font=font)
        y += label_h
        for idx, image in enumerate(images):
            sheet.paste(image, (pad + idx * thumb, y))
        y += thumb + pad
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ri3d-root", type=Path, default=Path("experiments/ri3d_datasets/first2_fghead_maskaware"))
    parser.add_argument("--output-ri3d-root", type=Path, default=Path("experiments/ri3d_datasets/first2_flame_proxy_pcdmask"))
    parser.add_argument("--prior-root", type=Path, default=Path("experiments/geometry_priors/flame_first2_proxy"))
    parser.add_argument("--lam-root", type=Path, default=Path("external/LAM"))
    parser.add_argument("--variants", nargs="+", default=["roleaware_cutout75_budget4"])
    parser.add_argument("--samples", nargs="+", default=list(DEFAULT_SAMPLES))
    parser.add_argument("--figure", type=Path, default=Path("experiments/figures/flame_geometry_prior_first2_proxy_sheet.png"))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for variant in args.variants:
        for sample_id in args.samples:
            src_scene = args.source_ri3d_root / variant / sample_id
            if not src_scene.exists():
                raise FileNotFoundError(src_scene)
            row = convert_scene(
                src_scene=src_scene,
                dst_scene=args.output_ri3d_root / variant / sample_id,
                prior_scene=args.prior_root / variant / sample_id,
                lam_root=args.lam_root,
                variant=variant,
                sample_id=sample_id,
                overwrite=args.overwrite,
            )
            rows.append(row)

    write_json(args.output_ri3d_root / "manifest.json", rows)
    write_json(args.prior_root / "manifest.json", rows)
    make_proxy_sheet(rows, args.figure)
    print(f"Wrote {args.output_ri3d_root}")
    print(f"Wrote {args.prior_root}")
    print(f"Wrote {args.figure}")


if __name__ == "__main__":
    main()
