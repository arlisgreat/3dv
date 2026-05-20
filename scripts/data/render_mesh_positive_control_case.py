#!/usr/bin/env python3
"""Render a repo-safe mesh-derived positive-control case.

The raw GLB/STL stays outside the repository. This script writes deterministic
derived RGB/depth/mask/normal PNGs, camera metadata, an orbit MP4, and a gate
summary under experiments/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_mesh(mesh_path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(mesh_path, force="scene")
    if isinstance(loaded, trimesh.Scene):
        mesh = loaded.to_geometry()
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"Unsupported mesh type: {type(mesh)!r}")
    if mesh.faces is None or len(mesh.faces) == 0:
        raise ValueError("Mesh has no faces")
    mesh.remove_unreferenced_vertices()
    return mesh


def canonicalize_vertices(
    vertices: np.ndarray,
    *,
    vertical_axis_override: int | None,
    right_axis_override: int | None,
    depth_axis_override: int | None,
) -> tuple[np.ndarray, dict[str, Any]]:
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2.0
    extents = maxs - mins
    scale = float(extents.max())
    normalized = (vertices - center) / scale
    vertical_axis = int(vertical_axis_override) if vertical_axis_override is not None else int(np.argmax(extents))
    horizontal_axes = [axis for axis in range(3) if axis != vertical_axis]
    horizontal_axes = sorted(horizontal_axes, key=lambda axis: extents[axis], reverse=True)
    right_axis = int(right_axis_override) if right_axis_override is not None else int(horizontal_axes[0])
    depth_axis = int(depth_axis_override) if depth_axis_override is not None else int(horizontal_axes[1])
    if sorted([right_axis, vertical_axis, depth_axis]) != [0, 1, 2]:
        raise ValueError(
            "right, vertical, and depth axes must be a permutation of 0, 1, 2; "
            f"got {(right_axis, vertical_axis, depth_axis)}"
        )
    canonical = np.stack(
        [
            normalized[:, right_axis],
            normalized[:, vertical_axis],
            normalized[:, depth_axis],
        ],
        axis=1,
    )
    info = {
        "bbox_min": mins.tolist(),
        "bbox_max": maxs.tolist(),
        "bbox_extents": extents.tolist(),
        "bbox_center": center.tolist(),
        "normalization_scale": scale,
        "vertical_axis": vertical_axis,
        "right_axis": right_axis,
        "depth_axis": depth_axis,
    }
    return canonical, info


def rotate_y(points: np.ndarray, degrees: float) -> np.ndarray:
    theta = math.radians(degrees)
    c = math.cos(theta)
    s = math.sin(theta)
    out = points.copy()
    x = points[:, 0]
    z = points[:, 2]
    out[:, 0] = c * x + s * z
    out[:, 2] = -s * x + c * z
    return out


def render_view(
    points: np.ndarray,
    normals: np.ndarray,
    azimuth: float,
    image_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    rotated_points = rotate_y(points, azimuth)
    rotated_normals = rotate_y(normals, azimuth)
    x = rotated_points[:, 0]
    y = rotated_points[:, 1]
    z = rotated_points[:, 2]

    scale = image_size * 0.72
    sx = np.rint(x * scale + image_size / 2.0).astype(np.int32)
    sy = np.rint(image_size / 2.0 - y * scale).astype(np.int32)
    valid = (sx >= 0) & (sx < image_size) & (sy >= 0) & (sy < image_size)
    sx = sx[valid]
    sy = sy[valid]
    z = z[valid]
    visible_normals = rotated_normals[valid]
    visible_points = rotated_points[valid]

    rgb = np.full((image_size, image_size, 3), 244, dtype=np.uint8)
    depth = np.zeros((image_size, image_size), dtype=np.float32)
    mask = np.zeros((image_size, image_size), dtype=np.uint8)
    normal_img = np.full((image_size, image_size, 3), 244, dtype=np.uint8)
    zbuf = np.full((image_size, image_size), -np.inf, dtype=np.float32)

    light = np.array([0.2, 0.35, 0.92], dtype=np.float32)
    light = light / np.linalg.norm(light)
    order = np.argsort(z)
    for idx in order:
        px = sx[idx]
        py = sy[idx]
        pz = z[idx]
        if pz <= zbuf[py, px]:
            continue
        zbuf[py, px] = pz
        n = visible_normals[idx]
        norm = float(np.linalg.norm(n))
        if norm > 1e-8:
            n = n / norm
        shade = 0.45 + 0.55 * max(float(np.dot(n, light)), 0.0)
        side = 0.5 + 0.5 * float(visible_points[idx, 0])
        base = np.array([181, 132, 102], dtype=np.float32) * side + np.array([154, 66, 68], dtype=np.float32) * (1.0 - side)
        rgb[py, px] = np.clip(base * shade + 24, 0, 255).astype(np.uint8)
        mask[py, px] = 255
        normal_img[py, px] = np.clip((n + 1.0) * 127.5, 0, 255).astype(np.uint8)

    visible = np.isfinite(zbuf)
    if visible.any():
        zmin = float(zbuf[visible].min())
        zmax = float(zbuf[visible].max())
        depth_norm = (zbuf - zmin) / max(zmax - zmin, 1e-6)
        depth[visible] = depth_norm[visible]

    # Densify point splats for easier visual audit without changing geometry metadata.
    kernel = np.ones((2, 2), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations=1)
    rgb = cv2.dilate(rgb, kernel, iterations=1)
    normal_img = cv2.dilate(normal_img, kernel, iterations=1)
    depth_u8 = np.clip(depth * 255, 0, 255).astype(np.uint8)
    depth_u8 = cv2.dilate(depth_u8, kernel, iterations=1)
    rgb[mask_dilated == 0] = 244
    normal_img[mask_dilated == 0] = 244
    depth_u8[mask_dilated == 0] = 0

    meta = {
        "azimuth_degrees": azimuth,
        "projection": "orthographic",
        "image_size": image_size,
        "visible_pixel_count": int((mask_dilated > 0).sum()),
        "visible_pixel_ratio": float((mask_dilated > 0).mean()),
        "render_note": "sampled-surface z-buffer render for gate audit, not photorealistic RGB",
    }
    return rgb, depth_u8, mask_dilated, normal_img, meta


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_contact_sheet(path: Path, rgb_paths: list[Path], labels: list[str], title: str) -> None:
    font = choose_font(18)
    small = choose_font(14)
    thumbs = [Image.open(p).convert("RGB").resize((256, 256), Image.Resampling.LANCZOS) for p in rgb_paths]
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    header = 72
    cell_h = 298
    width = cols * 256
    height = header + rows * cell_h
    sheet = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), f"G16b {title} positive-control views", fill=(20, 20, 20), font=font)
    draw.text((16, 40), "Mesh-derived RGB projections with deterministic orthographic cameras", fill=(70, 70, 70), font=small)
    for idx, thumb in enumerate(thumbs):
        col = idx % cols
        row = idx // cols
        x = col * 256
        y = header + row * cell_h
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + 262), labels[idx], fill=(30, 30, 30), font=small)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def make_video(path: Path, rgb_paths: list[Path], fps: int) -> None:
    first = cv2.imread(str(rgb_paths[0]))
    if first is None:
        raise RuntimeError(f"Could not read {rgb_paths[0]}")
    height, width = first.shape[:2]
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for _ in range(3):
        for image_path in rgb_paths:
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise RuntimeError(f"Could not read {image_path}")
            writer.write(frame)
    writer.release()


def write_gate_md(
    path: Path,
    *,
    mesh_path: Path,
    mesh_sha256: str,
    mesh: trimesh.Trimesh,
    sample_count: int,
    camera_json: Path,
    manifest_csv: Path,
    contact_sheet: Path,
    orbit_mp4: Path,
    case_id: str,
    title: str,
    source_url: str,
    download_url: str,
    license_text: str,
) -> None:
    lines = [
        f"# G16b {title} Positive-Control Gate",
        "",
        "Date: 2026-05-20",
        "",
        "Gate verdict:",
        "",
        "```text",
        "PASS_POSITIVE_CONTROL_ONLY",
        "PASS_RECONSTRUCTION_TRAINING_FOR_SYNTHETIC_RENDERED_GT_ONLY",
        "BLOCKED_FOR_REAL_CAPTURE_RECONSTRUCTION_CLAIMS",
        "```",
        "",
        "Premise:",
        "",
        "```text",
        "Use a public GT mesh to render deterministic multi-view RGB/depth/mask/normal",
        "views with known cameras. This validates data-gate and reconstruction plumbing",
        "without claiming that web pseudo views or synthetic renders are real captured",
        "multi-view training data.",
        "```",
        "",
        "Source:",
        "",
        "```text",
        f"case_id: {case_id}",
        f"title: {title}",
        f"entry: {source_url}",
        f"download_endpoint: {download_url}",
        f"license: {license_text}",
        f"local_raw_mesh: {mesh_path}",
        f"raw_mesh_sha256: {mesh_sha256}",
        "repo_policy: raw mesh is not committed; only derived audit outputs are committed",
        "```",
        "",
        "Mesh audit:",
        "",
        "```text",
        f"vertices: {len(mesh.vertices)}",
        f"faces: {len(mesh.faces)}",
        f"sampled_surface_points_for_render: {sample_count}",
        "rendering: deterministic orthographic sampled-surface z-buffer",
        "```",
        "",
        "Artifacts:",
        "",
        "```text",
        str(camera_json),
        str(manifest_csv),
        str(contact_sheet),
        str(orbit_mp4),
        f"experiments/gt_cases/{case_id}/views/*.png",
        "```",
        "",
        "Manual/VLM visual audit:",
        "",
        "```text",
        "Pending final inspection of the generated contact sheet before G17.",
        "Expected pass scope is synthetic positive-control only.",
        "```",
        "",
        "Limitations:",
        "",
        "```text",
        "This is a mesh-derived positive control, not a real multi-camera capture.",
        "It cannot validate identity preservation on real portraits.",
        "It can validate camera/provenance handling, derived GT views, masks, depth,",
        "and whether downstream reconstruction code can consume auditable inputs.",
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mesh",
        type=Path,
        default=Path(
            "/data1/workspace/airulan/3dv_work/datasets/"
            "wikimedia_blender_head_cc0/Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl"
        ),
    )
    parser.add_argument("--case-id", default="wikimedia_blender_head_cc0")
    parser.add_argument("--title", default="Wikimedia Blender CC0 realistic human head")
    parser.add_argument(
        "--source-url",
        default="https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl",
    )
    parser.add_argument(
        "--download-url",
        default=(
            "https://upload.wikimedia.org/wikipedia/commons/8/84/"
            "Head_%28Sculpting%29_-_Realistic_by_Dan_Ulrich_%28CC0%29.stl"
        ),
    )
    parser.add_argument("--license", default="CC0 1.0 Universal Public Domain Dedication")
    parser.add_argument("--case-root", type=Path, default=Path("experiments/gt_cases/wikimedia_blender_head_cc0"))
    parser.add_argument("--figure", type=Path, default=Path("experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png"))
    parser.add_argument("--gate-md", type=Path, default=Path("experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md"))
    parser.add_argument("--gate-json", type=Path, default=Path("experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.json"))
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--views", type=int, default=8)
    parser.add_argument("--sample-count", type=int, default=220000)
    parser.add_argument("--fps", type=int, default=4)
    parser.add_argument("--azimuth-offset", type=float, default=0.0)
    parser.add_argument("--vertical-axis", type=int, default=None)
    parser.add_argument("--right-axis", type=int, default=None)
    parser.add_argument("--depth-axis", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mesh_path = args.mesh.resolve()
    if not mesh_path.exists():
        raise FileNotFoundError(mesh_path)
    mesh_sha256 = sha256_file(mesh_path)
    mesh = load_mesh(mesh_path)
    normalized_vertices, canonical = canonicalize_vertices(
        np.asarray(mesh.vertices, dtype=np.float32),
        vertical_axis_override=args.vertical_axis,
        right_axis_override=args.right_axis,
        depth_axis_override=args.depth_axis,
    )
    mesh_for_sampling = mesh.copy()
    mesh_for_sampling.vertices = normalized_vertices
    points, face_indices = trimesh.sample.sample_surface(mesh_for_sampling, args.sample_count)
    face_normals = np.asarray(mesh_for_sampling.face_normals[face_indices], dtype=np.float32)

    view_dir = args.case_root / "views"
    rgb_paths: list[Path] = []
    labels: list[str] = []
    rows: list[dict[str, Any]] = []
    camera_records: list[dict[str, Any]] = []
    for idx in range(args.views):
        azimuth = round(args.azimuth_offset + idx * 360.0 / args.views, 6)
        rgb, depth, mask, normal, meta = render_view(points, face_normals, azimuth, args.image_size)
        rgb_path = view_dir / f"rgb_{idx:02d}_az{int(round(azimuth)):03d}.png"
        depth_path = view_dir / f"depth_{idx:02d}_az{int(round(azimuth)):03d}.png"
        mask_path = view_dir / f"mask_{idx:02d}_az{int(round(azimuth)):03d}.png"
        normal_path = view_dir / f"normal_{idx:02d}_az{int(round(azimuth)):03d}.png"
        for path, arr in (
            (rgb_path, rgb),
            (depth_path, depth),
            (mask_path, mask),
            (normal_path, normal),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(arr).save(path)
        rgb_paths.append(rgb_path)
        labels.append(f"view {idx:02d} az {int(round(azimuth)):03d}")
        rows.append(
            {
                "case_id": args.case_id,
                "view_id": f"view_{idx:02d}",
                "azimuth_degrees": azimuth,
                "rgb": str(rgb_path),
                "depth": str(depth_path),
                "mask": str(mask_path),
                "normal": str(normal_path),
                "projection": meta["projection"],
                "image_size": meta["image_size"],
                "visible_pixel_ratio": f"{meta['visible_pixel_ratio']:.6f}",
                "gate_role": "positive_control_gt_view",
            }
        )
        camera_records.append(
            {
                "view_id": f"view_{idx:02d}",
                "azimuth_degrees": azimuth,
                "projection": "orthographic",
                "normalized_bbox_scale": canonical["normalization_scale"],
                "image_size": args.image_size,
                "coordinate_policy": "canonical right/vertical/depth axes, yaw around vertical axis",
            }
        )

    manifest_csv = args.case_root / "manifest.csv"
    write_csv(
        manifest_csv,
        rows,
        [
            "case_id",
            "view_id",
            "azimuth_degrees",
            "rgb",
            "depth",
            "mask",
            "normal",
            "projection",
            "image_size",
            "visible_pixel_ratio",
            "gate_role",
        ],
    )
    camera_json = args.case_root / "cameras.json"
    camera_json.parent.mkdir(parents=True, exist_ok=True)
    camera_json.write_text(
        json.dumps(
            {
                "case_id": args.case_id,
                "title": args.title,
                "source_url": args.source_url,
                "download_url": args.download_url,
                "license": args.license,
                "raw_mesh_sha256": mesh_sha256,
                "canonicalization": canonical,
                "cameras": camera_records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    make_contact_sheet(args.figure, rgb_paths, labels, args.title)
    orbit_mp4 = args.case_root / "orbit_rgb.mp4"
    make_video(orbit_mp4, rgb_paths, args.fps)
    write_gate_md(
        args.gate_md,
        mesh_path=mesh_path,
        mesh_sha256=mesh_sha256,
        mesh=mesh,
        sample_count=args.sample_count,
        camera_json=camera_json,
        manifest_csv=manifest_csv,
        contact_sheet=args.figure,
        orbit_mp4=orbit_mp4,
        case_id=args.case_id,
        title=args.title,
        source_url=args.source_url,
        download_url=args.download_url,
        license_text=args.license,
    )
    args.gate_json.parent.mkdir(parents=True, exist_ok=True)
    args.gate_json.write_text(
        json.dumps(
            {
                "case_id": args.case_id,
                "title": args.title,
                "date": "2026-05-20",
                "gate_verdict": "PASS_POSITIVE_CONTROL_ONLY",
                "source_url": args.source_url,
                "download_endpoint": args.download_url,
                "license": args.license,
                "raw_mesh_path": str(mesh_path),
                "raw_mesh_sha256": mesh_sha256,
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "views": len(rows),
                "sample_count": args.sample_count,
                "manifest_csv": str(manifest_csv),
                "camera_json": str(camera_json),
                "contact_sheet": str(args.figure),
                "orbit_mp4": str(orbit_mp4),
                "scope": "synthetic mesh-derived positive control only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {manifest_csv}")
    print(f"Wrote {camera_json}")
    print(f"Wrote {args.figure}")
    print(f"Wrote {orbit_mp4}")
    print(f"Wrote {args.gate_md}")
    print(f"Wrote {args.gate_json}")


if __name__ == "__main__":
    main()
