#!/usr/bin/env python3
"""Convert a gate-passed GT/positive-control case into RI3D-readable folders."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def resize_rgb(src: Path, dst: Path, size: int) -> Image.Image:
    image = Image.open(src).convert("RGB")
    image = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (244, 244, 244))
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    return canvas


def resize_mask(src: Path, dst: Path, size: int) -> Image.Image:
    image = Image.open(src).convert("L")
    image = ImageOps.contain(image, (size, size), Image.Resampling.NEAREST)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    return canvas


def resize_depth(src: Path, size: int) -> np.ndarray:
    image = Image.open(src).convert("L")
    image = ImageOps.contain(image, (size, size), Image.Resampling.BILINEAR)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    arr = np.asarray(canvas, dtype=np.float32) / 255.0
    # RI3D expects positive depth-like arrays. Keep background finite but low.
    return (0.35 + 1.65 * arr).astype(np.float32)


def mask_confidence(mask: Image.Image) -> np.ndarray:
    arr = np.asarray(mask, dtype=np.float32) / 255.0
    return (0.2 + 4.8 * arr).astype(np.float32)


def convert_case(
    *,
    case_root: Path,
    output_root: Path,
    variant: str,
    case_id: str,
    image_size: int,
    fov_deg: float,
    camera_radius: float,
    overwrite: bool,
) -> dict[str, Any]:
    manifest = read_csv(case_root / "manifest.csv")
    cameras = load_json(case_root / "cameras.json")
    if len(manifest) < 3:
        raise ValueError("RI3D positive-control conversion needs at least 3 views")

    scene_root = output_root / variant / case_id
    clean_dir(scene_root, overwrite=overwrite)
    images_dir = scene_root / "images"
    masks_dir = scene_root / "masks"
    depth_dir = images_dir / "depth_rel"
    images_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    focal = 0.5 * image_size / math.tan(math.radians(fov_deg) / 2.0)
    frames: list[dict[str, Any]] = []
    depths: list[np.ndarray] = []
    confs: list[np.ndarray] = []
    for order, row in enumerate(manifest):
        view_id = row["view_id"]
        rgb_src = Path(row["rgb"])
        depth_src = Path(row["depth"])
        mask_src = Path(row["mask"])
        image_name = f"{order:03d}_{view_id}.png"
        mask_name = f"{order:03d}_{view_id}_mask.png"
        image_path = images_dir / image_name
        mask_path = masks_dir / mask_name
        resize_rgb(rgb_src, image_path, image_size)
        mask = resize_mask(mask_src, mask_path, image_size)
        depth = resize_depth(depth_src, image_size)
        conf = mask_confidence(mask)
        stem = image_path.stem
        view_count = len(manifest)
        np.save(depth_dir / f"inpv2{stem}_{view_count}.npy", depth)
        np.save(depth_dir / f"inp_dust3r{stem}_{view_count}.npy", depth)
        depths.append(depth)
        confs.append(conf)
        azimuth = float(row["azimuth_degrees"])
        frames.append(
            {
                "file_path": f"images/{image_name}",
                "mask_path": f"masks/{mask_name}",
                "source_image": str(rgb_src),
                "source_depth": str(depth_src),
                "source_mask": str(mask_src),
                "transform_matrix": camera_to_world(azimuth, 0.0, camera_radius),
                "view_index": order,
                "azimuth": azimuth,
                "elevation": 0.0,
                "supervision_role": "positive_control_gt",
                "role_rgb_weight": 1.0,
                "role_depth_weight": 1.0,
                "ri3d_train_candidate": True,
                "gate_scope": "positive_control_only",
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
    write_json(scene_root / "transforms.json", transforms)
    write_json(scene_root / f"train_test_split_{n_views}.json", {"train_ids": list(range(n_views)), "test_ids": []})
    np.save(scene_root / f"depths{n_views}.npy", np.stack(depths, axis=0))
    np.save(scene_root / f"confs{n_views}.npy", np.stack(confs, axis=0))
    write_json(
        scene_root / "source_metadata.json",
        {
            "semantic_type": "ri3d_readable_positive_control_export",
            "case_id": case_id,
            "variant": variant,
            "source_case_root": str(case_root),
            "image_size": image_size,
            "view_count": n_views,
            "camera_radius": camera_radius,
            "fov_deg": fov_deg,
            "gate_scope": "positive_control_only",
            "validated_training_dataset": False,
            "validated_positive_control": True,
            "semantic_note": (
                "This is an RI3D-readable export of a mesh-derived positive-control "
                "case. It can validate plumbing and gate mechanics, but it is not "
                "a licensed real-capture reconstruction dataset."
            ),
            "source_cameras": cameras,
        },
    )
    return {
        "case_id": case_id,
        "variant": variant,
        "sample_id": case_id,
        "scene_dir": str(scene_root),
        "view_count": n_views,
        "image_size": image_size,
        "gate_scope": "positive_control_only",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="wikimedia_blender_head_cc0")
    parser.add_argument("--variant", default="mesh_rendered")
    parser.add_argument("--case-root", type=Path, default=Path("experiments/gt_cases/wikimedia_blender_head_cc0"))
    parser.add_argument("--output-root", type=Path, default=Path("experiments/ri3d_datasets/gt_positive_control"))
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--fov-deg", type=float, default=40.0)
    parser.add_argument("--camera-radius", type=float, default=2.8)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row = convert_case(
        case_root=args.case_root,
        output_root=args.output_root,
        variant=args.variant,
        case_id=args.case_id,
        image_size=args.image_size,
        fov_deg=args.fov_deg,
        camera_radius=args.camera_radius,
        overwrite=args.overwrite,
    )
    write_json(args.output_root / "manifest.json", [row])
    print(f"Prepared {row['scene_dir']} with {row['view_count']} views")


if __name__ == "__main__":
    main()
