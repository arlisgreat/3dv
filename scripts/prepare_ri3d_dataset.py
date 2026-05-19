#!/usr/bin/env python3
"""Convert downstream pseudo-view datasets into RI3D-compatible scene folders.

This script does the CPU-side preparation only. It creates the files that the
local RI3D checkout expects:

  transforms.json
  train_test_split_<N>.json
  depths<N>.npy
  confs<N>.npy
  images/*.png
  images/depth_rel/inpv2<image_stem>_<N>.npy
  images/depth_rel/inp_dust3r<image_stem>_<N>.npy

The generated depth maps are geometry priors for a controlled pilot run, not
ground-truth depth. They are deliberately simple so the first downstream test
can isolate whether filtered pseudo views are more stable than raw pseudo
views.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps


DEFAULT_VARIANTS = ("raw75_all6", "raw75_budget4", "cutout75_budget4_masked")
DEFAULT_SAMPLES = ("web_clean_frontal_03", "web_clean_frontal_01")
ROLE_CONFIDENCE_MULTIPLIERS = {
    "identity_supervision": 1.0,
    "geometry_only": 0.35,
    "identity_reject": 0.0,
    "mask_reject": 0.0,
}
ROLE_RGB_POLICIES = {
    "identity_supervision": "rgb",
    "geometry_only": "desaturated_rgb",
    "identity_reject": "excluded",
    "mask_reject": "excluded",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} exists. Use --overwrite to rebuild it.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def normalize_vec(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-8:
        raise ValueError(f"Cannot normalize near-zero vector: {v}")
    return v / norm


def camera_to_world(azimuth_deg: float, elevation_deg: float, radius: float) -> list[list[float]]:
    """Build an OpenGL-style camera-to-world matrix from Zero123++ view angles."""
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    center = np.array(
        [
            radius * math.sin(az) * math.cos(el),
            radius * math.sin(el),
            radius * math.cos(az) * math.cos(el),
        ],
        dtype=np.float64,
    )
    target = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    forward = normalize_vec(target - center)
    world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    right = normalize_vec(np.cross(forward, world_up))
    up = normalize_vec(np.cross(right, forward))

    c2w = np.eye(4, dtype=np.float64)
    c2w[:3, 0] = right
    c2w[:3, 1] = up
    c2w[:3, 2] = -forward
    c2w[:3, 3] = center
    return c2w.tolist()


def resize_rgb(src: Path, dst: Path, size: int, supervision_role: str | None = None) -> Image.Image:
    image = Image.open(src).convert("RGB")
    image = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (127, 127, 127))
    offset = ((size - image.width) // 2, (size - image.height) // 2)
    canvas.paste(image, offset)
    if supervision_role == "geometry_only":
        gray = ImageOps.grayscale(canvas).convert("RGB")
        canvas = Image.blend(canvas, gray, 0.85)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    return canvas


def simple_depth_prior(size: int, azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """Create a smooth positive inverse-depth-like prior for RI3D bootstrap."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (x - size / 2.0) / (size / 2.0)
    y = (y - size / 2.0) / (size / 2.0)
    radius2 = x * x + y * y
    face_bump = np.exp(-radius2 / 0.72)
    side_bias = 0.08 * math.sin(math.radians(azimuth_deg)) * x
    elev_bias = 0.04 * math.sin(math.radians(elevation_deg)) * y
    depth = 1.05 + 0.45 * face_bump + side_bias + elev_bias
    return np.clip(depth, 0.2, 4.0).astype(np.float32)


def simple_confidence(size: int) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (x - size / 2.0) / (size / 2.0)
    y = (y - size / 2.0) / (size / 2.0)
    conf = 5.0 * np.exp(-(x * x + y * y) / 1.4)
    return np.clip(conf, 0.0, 5.0).astype(np.float32)


def resolve_scene_image(src_scene: Path, image_ref: str) -> Path:
    path = Path(image_ref)
    if path.exists():
        return path
    fallback = src_scene / "images" / path.name
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"{image_ref} not found; also tried {fallback}")


def convert_scene(
    *,
    src_scene: Path,
    dst_scene: Path,
    variant: str,
    sample_id: str,
    image_size: int,
    camera_radius: float,
    fov_deg: float,
    overwrite: bool,
) -> dict[str, Any]:
    metadata = load_json(src_scene / "metadata.json")
    all_views = metadata["views"]
    views = [view for view in all_views if view.get("ri3d_train_candidate", True)]
    if len(views) < 3:
        raise ValueError(f"{src_scene} has only {len(views)} trainable views; RI3D pilot needs at least 3.")

    clean_dir(dst_scene, overwrite=overwrite)
    images_dir = dst_scene / "images"
    depth_dir = images_dir / "depth_rel"
    images_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    focal = 0.5 * image_size / math.tan(math.radians(fov_deg) / 2.0)
    frames: list[dict[str, Any]] = []
    depths: list[np.ndarray] = []
    confs: list[np.ndarray] = []

    for order, view in enumerate(views):
        src_image = resolve_scene_image(src_scene, view["image"])
        supervision_role = view.get("supervision_role")
        confidence_multiplier = ROLE_CONFIDENCE_MULTIPLIERS.get(str(supervision_role), 1.0)
        rgb_policy = ROLE_RGB_POLICIES.get(str(supervision_role), "rgb")

        image_name = f"{order:03d}_view{int(view['view_index']):02d}.png"
        image_path = images_dir / image_name
        resize_rgb(src_image, image_path, image_size, supervision_role=supervision_role)

        azimuth = float(view.get("azimuth") or 0.0)
        elevation = float(view.get("elevation") or 0.0)
        depth = simple_depth_prior(image_size, azimuth, elevation)
        conf = simple_confidence(image_size) * float(confidence_multiplier)
        stem = image_path.stem
        np.save(depth_dir / f"inpv2{stem}_{len(views)}.npy", depth)
        np.save(depth_dir / f"inp_dust3r{stem}_{len(views)}.npy", depth)
        depths.append(depth)
        confs.append(conf)

        frames.append(
            {
                "file_path": f"images/{image_name}",
                "transform_matrix": camera_to_world(azimuth, elevation, camera_radius),
                "view_index": view.get("view_index"),
                "azimuth": azimuth,
                "elevation": elevation,
                "source_image": view.get("source_image"),
                "trusted_score": view.get("trusted_score"),
                "reliability_score": view.get("reliability_score"),
                "trusted_accepted": view.get("trusted_accepted"),
                "supervision_role": view.get("supervision_role"),
                "ri3d_train_candidate": view.get("ri3d_train_candidate", True),
                "identity_decision": view.get("identity_decision"),
                "identity_labels": view.get("identity_labels"),
                "identity_supervision_candidate": view.get("identity_supervision_candidate"),
                "geometry_only_candidate": view.get("geometry_only_candidate"),
                "face_embedding_cosine": view.get("face_embedding_cosine"),
                "role_confidence_multiplier": confidence_multiplier,
                "role_rgb_policy": rgb_policy,
            }
        )

    n_views = len(frames)
    transforms = {
        "camera_model": "OPENCV",
        "fl_x": focal,
        "fl_y": focal,
        "cx": image_size / 2.0,
        "cy": image_size / 2.0,
        "w": image_size,
        "h": image_size,
        "aabb_scale": 1,
        "frames": frames,
    }
    split = {"train_ids": list(range(n_views)), "test_ids": []}

    write_json(dst_scene / "transforms.json", transforms)
    write_json(dst_scene / f"train_test_split_{n_views}.json", split)
    np.save(dst_scene / f"depths{n_views}.npy", np.stack(depths, axis=0))
    np.save(dst_scene / f"confs{n_views}.npy", np.stack(confs, axis=0))
    write_json(
        dst_scene / "source_metadata.json",
        {
            "variant": variant,
            "sample_id": sample_id,
            "source_scene": str(src_scene),
            "image_size": image_size,
            "camera_radius": camera_radius,
            "fov_deg": fov_deg,
            "view_count": n_views,
            "source_view_count": len(all_views),
            "excluded_view_count": len(all_views) - n_views,
            "role_counts": dict(Counter(str(view.get("supervision_role", "uniform_rgb")) for view in views)),
            "role_confidence_multipliers": ROLE_CONFIDENCE_MULTIPLIERS,
            "role_rgb_policies": ROLE_RGB_POLICIES,
            "source_metadata": metadata,
        },
    )
    return {
        "variant": variant,
        "sample_id": sample_id,
        "scene_dir": str(dst_scene),
        "view_count": n_views,
        "image_size": image_size,
        "source_view_count": len(all_views),
        "excluded_view_count": len(all_views) - n_views,
        "role_counts": dict(Counter(str(view.get("supervision_role", "uniform_rgb")) for view in views)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downstream-root", type=Path, default=Path("experiments/downstream_datasets"))
    parser.add_argument("--output-root", type=Path, default=Path("experiments/ri3d_datasets/first2"))
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--samples", nargs="+", default=list(DEFAULT_SAMPLES))
    parser.add_argument("--image-size", type=int, default=320)
    parser.add_argument("--camera-radius", type=float, default=2.8)
    parser.add_argument("--fov-deg", type=float, default=40.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows: list[dict[str, Any]] = []

    for variant in args.variants:
        for sample_id in args.samples:
            src_scene = args.downstream_root / variant / sample_id
            if not src_scene.exists():
                raise FileNotFoundError(src_scene)
            dst_scene = args.output_root / variant / sample_id
            rows.append(
                convert_scene(
                    src_scene=src_scene,
                    dst_scene=dst_scene,
                    variant=variant,
                    sample_id=sample_id,
                    image_size=args.image_size,
                    camera_radius=args.camera_radius,
                    fov_deg=args.fov_deg,
                    overwrite=args.overwrite,
                )
            )

    write_json(args.output_root / "manifest.json", rows)
    print(f"Prepared {len(rows)} RI3D scenes under {args.output_root}")
    for row in rows:
        print(f"- {row['variant']}/{row['sample_id']}: {row['view_count']} views")


if __name__ == "__main__":
    main()
