#!/usr/bin/env python3
"""Prepare a local-only RI3D-readable adapter for the G21 Multiface case.

The script keeps identifiable RGB/mesh artifacts under 3dv_work. Repo outputs
are limited to compact metrics and a mask/depth-only audit figure.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DATE = "2026-05-20"
PASS_VERDICT = "PASS_REAL_CAMERA_ADAPTER_PREFLIGHT"
BLOCKED_VERDICT = "BLOCKED_REAL_CAMERA_ADAPTER"
COORD_TRANS = np.diag([1.0, -1.0, -1.0, 1.0])


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} exists; pass --overwrite to rebuild")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def load_obj(path: Path) -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    vertices: list[list[float]] = []
    faces: list[tuple[int, int, int]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                _, x, y, z, *_ = line.split()
                vertices.append([float(x), float(y), float(z)])
            elif line.startswith("f "):
                raw = [int(part.split("/")[0]) - 1 for part in line.split()[1:]]
                for idx in range(1, len(raw) - 1):
                    faces.append((raw[0], raw[idx], raw[idx + 1]))
    return np.asarray(vertices, dtype=np.float64), faces


def camera_entries(cameras: Any) -> list[dict[str, Any]]:
    if isinstance(cameras, dict):
        entries = cameras.get("cameras", cameras.get("views", []))
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
    if isinstance(cameras, list):
        return [entry for entry in cameras if isinstance(entry, dict)]
    return []


def view_id(entry: dict[str, Any]) -> str:
    return str(entry.get("view_id", entry.get("camera", "")))


def affine_params(entry: dict[str, Any], target_focal: float, image_size: int) -> dict[str, float]:
    k = np.asarray(entry.get("K", entry.get("intrinsics")), dtype=np.float64)
    fx, fy, cx, cy = float(k[0, 0]), float(k[1, 1]), float(k[0, 2]), float(k[1, 2])
    scale = target_focal / ((fx + fy) * 0.5)
    tx = image_size / 2.0 - scale * cx
    ty = image_size / 2.0 - scale * cy
    return {
        "scale": scale,
        "tx": tx,
        "ty": ty,
        "fx_out": scale * fx,
        "fy_out": scale * fy,
        "cx_out": scale * cx + tx,
        "cy_out": scale * cy + ty,
    }


def warp_image(src: Path, dst: Path, params: dict[str, float], image_size: int, mode: str, fill: int | tuple[int, int, int]) -> Image.Image:
    image = Image.open(src).convert(mode)
    inv = (
        1.0 / params["scale"],
        0.0,
        -params["tx"] / params["scale"],
        0.0,
        1.0 / params["scale"],
        -params["ty"] / params["scale"],
    )
    resample = Image.Resampling.NEAREST if mode == "L" else Image.Resampling.BICUBIC
    warped = image.transform((image_size, image_size), Image.Transform.AFFINE, inv, resample=resample, fillcolor=fill)
    dst.parent.mkdir(parents=True, exist_ok=True)
    warped.save(dst)
    return warped


def project_vertices(vertices: np.ndarray, entry: dict[str, Any], params: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    rt = np.asarray(entry["extrinsics"], dtype=np.float64)
    k = np.asarray(entry.get("K", entry.get("intrinsics")), dtype=np.float64)
    xyz = vertices @ rt[:, :3].T + rt[:, 3]
    z = xyz[:, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        xy = xyz[:, :2] / z[:, None]
    uv = xy @ np.asarray([[k[0, 0], 0.0], [0.0, k[1, 1]]], dtype=np.float64).T
    uv[:, 0] += k[0, 2]
    uv[:, 1] += k[1, 2]
    uv[:, 0] = params["scale"] * uv[:, 0] + params["tx"]
    uv[:, 1] = params["scale"] * uv[:, 1] + params["ty"]
    return uv, z


def rasterize_depth(uv: np.ndarray, z: np.ndarray, faces: list[tuple[int, int, int]], size: int) -> tuple[np.ndarray, np.ndarray, int]:
    depth = np.full((size, size), np.inf, dtype=np.float64)
    projected = 0
    for i0, i1, i2 in faces:
        if z[i0] <= 1e-6 or z[i1] <= 1e-6 or z[i2] <= 1e-6:
            continue
        pts = uv[[i0, i1, i2]]
        if not np.isfinite(pts).all():
            continue
        min_x = max(0, int(math.floor(float(np.min(pts[:, 0])))))
        max_x = min(size - 1, int(math.ceil(float(np.max(pts[:, 0])))))
        min_y = max(0, int(math.floor(float(np.min(pts[:, 1])))))
        max_y = min(size - 1, int(math.ceil(float(np.max(pts[:, 1])))))
        if max_x < min_x or max_y < min_y:
            continue
        x0, y0 = pts[0]
        x1, y1 = pts[1]
        x2, y2 = pts[2]
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-8:
            continue
        xs = np.arange(min_x, max_x + 1, dtype=np.float64) + 0.5
        ys = np.arange(min_y, max_y + 1, dtype=np.float64) + 0.5
        grid_x, grid_y = np.meshgrid(xs, ys)
        w0 = ((y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)) / denom
        w1 = ((y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)) / denom
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        tri_depth = w0 * z[i0] + w1 * z[i1] + w2 * z[i2]
        patch = depth[min_y : max_y + 1, min_x : max_x + 1]
        update = inside & (tri_depth < patch)
        if update.any():
            patch[update] = tri_depth[update]
            projected += 1
    finite = np.isfinite(depth)
    return depth, finite, projected


def depth_to_rel(depth: np.ndarray, finite: np.ndarray, mask: Image.Image) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    mask_arr = np.asarray(mask.convert("L")) > 127
    valid = finite & mask_arr
    if not valid.any():
        valid = finite
    vals = depth[valid]
    med = float(np.median(vals))
    dmin = float(np.min(vals))
    dmax = float(np.max(vals))
    rel = np.full(depth.shape, dmax / med, dtype=np.float32)
    rel[finite] = (depth[finite] / med).astype(np.float32)
    conf = np.zeros(depth.shape, dtype=np.float32)
    conf[valid] = 1.0
    return rel, conf, {"depth_min": dmin, "depth_max": dmax, "depth_median": med}


def w2c_to_ri3d_transform(entry: dict[str, Any]) -> list[list[float]]:
    w2c = np.eye(4, dtype=np.float64)
    w2c[:3, :] = np.asarray(entry["extrinsics"], dtype=np.float64)
    c2w = np.linalg.inv(w2c)
    transform = c2w @ COORD_TRANS
    return transform.tolist()


def choose_font(size: int) -> Any:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_audit_figure(rows: list[dict[str, Any]], output: Path) -> None:
    thumb = 112
    pad = 12
    cols = len(rows)
    width = pad + cols * thumb + (cols - 1) * pad + pad
    height = 84 + thumb * 2 + 64
    sheet = Image.new("RGB", (width, height), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)
    font = choose_font(14)
    small = choose_font(10)
    draw.text((pad, 10), "G23 Multiface real-camera adapter: masks and mesh z-buffer depth only", fill=(20, 20, 20), font=font)
    draw.text((pad, 34), "No identifiable RGB or mesh is committed; local adapter outputs remain under 3dv_work.", fill=(100, 45, 45), font=small)
    draw.text((pad, 54), "Top: normalized projected mask. Bottom: normalized mesh depth.", fill=(55, 55, 55), font=small)
    for idx, row in enumerate(rows):
        x = pad + idx * (thumb + pad)
        y = 84
        mask = Image.open(row["mask_path"]).convert("L")
        mask.thumbnail((thumb, thumb), Image.Resampling.NEAREST)
        mask_tile = Image.new("RGB", (thumb, thumb), (24, 24, 24))
        mask_tile.paste(Image.new("RGB", mask.size, (245, 245, 245)), ((thumb - mask.width) // 2, (thumb - mask.height) // 2), mask)
        sheet.paste(mask_tile, (x, y))
        depth = np.load(row["depth_rel_path"])
        valid = depth[np.isfinite(depth)]
        lo, hi = float(np.percentile(valid, 2)), float(np.percentile(valid, 98))
        norm = np.clip((depth - lo) / max(1e-6, hi - lo), 0.0, 1.0)
        depth_img = Image.fromarray((255 * (1.0 - norm)).astype(np.uint8), mode="L").convert("RGB")
        depth_img.thumbnail((thumb, thumb), Image.Resampling.BILINEAR)
        sheet.paste(depth_img, (x, y + thumb + pad))
        draw.rectangle((x, y, x + thumb, y + thumb), outline=(185, 185, 185))
        draw.rectangle((x, y + thumb + pad, x + thumb, y + 2 * thumb + pad), outline=(185, 185, 185))
        draw.text((x, height - 36), str(row["camera"]), fill=(35, 35, 35), font=small)
        draw.text((x, height - 20), f"cov={row['mask_coverage']:.2f}", fill=(65, 65, 65), font=small)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def camera_lookup(cameras: Any) -> dict[str, dict[str, Any]]:
    return {view_id(entry): entry for entry in camera_entries(cameras)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view"))
    parser.add_argument("--case-id", default="gate_case")
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102"))
    parser.add_argument("--train-cameras", default="400017,400023,400050,400055,400067,400070")
    parser.add_argument("--test-cameras", default="400012,400041,400042")
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--target-focal", type=float, default=640.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g23_multiface_real_camera_adapter_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g23_multiface_real_camera_adapter_20260520.md"))
    parser.add_argument("--output-figure", type=Path, default=Path("experiments/figures/g23_multiface_adapter_depth_mask_summary_20260520.png"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    case_dir = args.case_root / args.case_id
    source_rows = read_csv(case_dir / "manifest.csv")
    source_by_camera = {row["camera"]: row for row in source_rows}
    cameras = load_json(case_dir / "cameras.json")
    camera_by_id = camera_lookup(cameras)
    metadata = load_json(case_dir / "real_gt_case.json")
    mesh_path = Path(metadata["gt_mesh"])
    vertices, faces = load_obj(mesh_path)
    train_cams = [item.strip() for item in args.train_cameras.split(",") if item.strip()]
    test_cams = [item.strip() for item in args.test_cameras.split(",") if item.strip()]
    all_cams = train_cams + test_cams
    if len(train_cams) < 6:
        raise ValueError("G23 adapter requires at least 6 train cameras")
    missing = [cam for cam in all_cams if cam not in source_by_camera or cam not in camera_by_id]
    if missing:
        raise ValueError(f"Missing cameras in source case: {missing}")

    clean_dir(args.output_root, overwrite=args.overwrite)
    images_dir = args.output_root / "images"
    masks_dir = args.output_root / "masks"
    depth_rel_dir = images_dir / "depth_rel"
    depth_raw_dir = args.output_root / "depth_raw_mm"
    conf_dir = args.output_root / "confidence"
    for path in (images_dir, masks_dir, depth_rel_dir, depth_raw_dir, conf_dir):
        path.mkdir(parents=True, exist_ok=True)

    frames: list[dict[str, Any]] = []
    adapter_rows: list[dict[str, Any]] = []
    depths: list[np.ndarray] = []
    confs: list[np.ndarray] = []
    for idx, cam in enumerate(all_cams):
        source = source_by_camera[cam]
        entry = camera_by_id[cam]
        params = affine_params(entry, args.target_focal, args.image_size)
        stem = f"{idx:03d}_{cam}"
        rgb_path = images_dir / f"{stem}.png"
        mask_path = masks_dir / f"{stem}_mask.png"
        depth_rel_path = depth_rel_dir / f"inpv2{stem}_{len(train_cams)}.npy"
        depth_dust3r_path = depth_rel_dir / f"inp_dust3r{stem}_{len(train_cams)}.npy"
        depth_raw_path = depth_raw_dir / f"{stem}_zbuffer_mm.npy"
        conf_path = conf_dir / f"{stem}_confidence.npy"
        warp_image(Path(source["rgb"]), rgb_path, params, args.image_size, "RGB", (127, 127, 127))
        warped_mask = warp_image(Path(source["mask"]), mask_path, params, args.image_size, "L", 0)
        uv, z = project_vertices(vertices, entry, params)
        depth_raw, finite, projected_faces = rasterize_depth(uv, z, faces, args.image_size)
        depth_rel, conf, depth_stats = depth_to_rel(depth_raw, finite, warped_mask)
        np.save(depth_rel_path, depth_rel)
        np.save(depth_dust3r_path, depth_rel)
        np.save(depth_raw_path, depth_raw.astype(np.float32))
        np.save(conf_path, conf)
        if idx < len(train_cams):
            depths.append(depth_rel)
            confs.append(conf)
        mask_coverage = float((np.asarray(warped_mask.convert("L")) > 127).mean())
        role = "real_gt_train" if idx < len(train_cams) else "heldout_eval"
        frames.append(
            {
                "file_path": f"images/{rgb_path.name}",
                "mask_path": f"masks/{mask_path.name}",
                "source_image": str(source["rgb"]),
                "source_mask": str(source["mask"]),
                "source_mesh": str(mesh_path),
                "transform_matrix": w2c_to_ri3d_transform(entry),
                "view_index": idx,
                "view_id": cam,
                "supervision_role": role,
                "role_rgb_weight": 1.0 if role == "real_gt_train" else 0.0,
                "role_depth_weight": 1.0 if role == "real_gt_train" else 0.0,
                "ri3d_train_candidate": role == "real_gt_train",
                "gate_scope": "real_gt_local_adapter",
            }
        )
        adapter_rows.append(
            {
                "camera": cam,
                "role": role,
                "rgb_path": str(rgb_path),
                "mask_path": str(mask_path),
                "depth_rel_path": str(depth_rel_path),
                "depth_raw_path": str(depth_raw_path),
                "confidence_path": str(conf_path),
                "mask_coverage": mask_coverage,
                "projected_faces": projected_faces,
                **params,
                **depth_stats,
            }
        )

    transforms = {
        "camera_model": "PINHOLE_CENTERED_BY_AFFINE_NORMALIZATION",
        "fl_x": args.target_focal,
        "fl_y": args.target_focal,
        "cx": args.image_size / 2.0,
        "cy": args.image_size / 2.0,
        "w": args.image_size,
        "h": args.image_size,
        "aabb_scale": 1,
        "frames": frames,
        "adapter_note": (
            "Images were affine-normalized from Multiface KRT cameras so the "
            "principal point is centered and focal length is approximately "
            "shared. This avoids feeding raw off-center intrinsics into RI3D's "
            "single-global-intrinsics transforms reader."
        ),
    }
    write_json(args.output_root / "transforms.json", transforms)
    write_json(args.output_root / f"train_test_split_{len(train_cams)}.json", {"train_ids": list(range(len(train_cams))), "test_ids": list(range(len(train_cams), len(all_cams)))})
    np.save(args.output_root / f"depths{len(train_cams)}.npy", np.stack(depths, axis=0))
    np.save(args.output_root / f"confs{len(train_cams)}.npy", np.stack(confs, axis=0))
    write_json(
        args.output_root / "source_metadata.json",
        {
            "date": DATE,
            "semantic_type": "local_only_multiface_real_camera_adapter",
            "source_case": str(case_dir),
            "view_count": len(all_cams),
            "train_cameras": train_cams,
            "test_cameras": test_cams,
            "image_size": args.image_size,
            "target_focal": args.target_focal,
            "license": metadata.get("license"),
            "privacy_status": metadata.get("privacy_status"),
            "artifact_policy": "local-only RGB/mesh/depth adapter under 3dv_work; commit metrics and mask/depth-only summaries only",
        },
    )
    manifest_row = {
        "variant": "multiface_real_camera_affine",
        "sample_id": "multiface_debug_000102",
        "scene_dir": str(args.output_root),
        "view_count": len(train_cams),
        "train_cameras": train_cams,
        "test_cameras": test_cams,
        "image_size": args.image_size,
        "target_focal": args.target_focal,
    }
    write_json(args.output_root.parent / "ri3d_real_camera_adapter_manifest.json", [manifest_row])

    make_audit_figure(adapter_rows, repo / args.output_figure)
    fx_residual = [abs(row["fx_out"] - args.target_focal) for row in adapter_rows]
    fy_residual = [abs(row["fy_out"] - args.target_focal) for row in adapter_rows]
    train_cov = [row["mask_coverage"] for row in adapter_rows if row["role"] == "real_gt_train"]
    checks = {
        "train_view_count_6_plus": len(train_cams) >= 6,
        "heldout_views_defined": len(test_cams) >= 2,
        "centered_principal_point": all(abs(row["cx_out"] - args.image_size / 2.0) < 1e-6 and abs(row["cy_out"] - args.image_size / 2.0) < 1e-6 for row in adapter_rows),
        "focal_residual_small": max(fx_residual + fy_residual) < 0.5,
        "depth_conf_generated": all(Path(row["depth_rel_path"]).is_file() and Path(row["confidence_path"]).is_file() for row in adapter_rows),
        "train_crop_risk_reduced": max(train_cov) < 0.72,
        "local_only_artifact_policy": str(args.output_root).startswith("/data1/workspace/airulan/3dv_work/"),
    }
    verdict = PASS_VERDICT if all(checks.values()) else BLOCKED_VERDICT
    repo_safe_rows = [
        {
            "camera": row["camera"],
            "role": row["role"],
            "mask_coverage": row["mask_coverage"],
            "projected_faces": row["projected_faces"],
            "depth_min": row["depth_min"],
            "depth_max": row["depth_max"],
            "depth_median": row["depth_median"],
            "scale": row["scale"],
            "fx_out": row["fx_out"],
            "fy_out": row["fy_out"],
            "cx_out": row["cx_out"],
            "cy_out": row["cy_out"],
        }
        for row in adapter_rows
    ]
    summary = {
        "date": DATE,
        "gate": "G23",
        "verdict": verdict,
        "checks": checks,
        "failed_checks": [key for key, ok in checks.items() if not ok],
        "adapter_root": str(args.output_root),
        "repo_safe_figure": str(args.output_figure),
        "manifest": manifest_row,
        "adapter_rows": repo_safe_rows,
        "raw_path_policy": "repo JSON redacts local RGB/mask/depth file paths; full local manifest remains under 3dv_work",
        "no_gpu_training_started": True,
        "closure": (
            "PASS_REAL_CAMERA_ADAPTER_PREFLIGHT: local-only normalized camera/depth/conf adapter is ready for a final dry-run gate before GPU."
            if all(checks.values())
            else "BLOCKED_REAL_CAMERA_ADAPTER: adapter generated, but at least one structural/crop/camera check failed; do not start GPU."
        ),
    }
    write_json(repo / args.output_json, summary)
    lines = [
        "# G23 Multiface Real-Camera Adapter",
        "",
        f"Date: {DATE}",
        "",
        "Verdict:",
        "",
        "```text",
        verdict,
        "NO_GPU_TRAINING_STARTED",
        "```",
        "",
        "Purpose:",
        "",
        "```text",
        "Convert the G21 Multiface debug real-GT case into a local-only adapter that",
        "RI3D can read without silently dropping per-view real-camera assumptions.",
        "Raw RGB and OBJ stay under 3dv_work; repo output is metrics plus a",
        "mask/depth-only PNG.",
        "```",
        "",
        "Adapter output:",
        "",
        "```text",
        str(args.output_root),
        str(args.output_root.parent / "ri3d_real_camera_adapter_manifest.json"),
        str(args.output_figure),
        "```",
        "",
        "Checks:",
        "",
        "| Check | Result |",
        "| --- | --- |",
        *[f"| {key} | {'PASS' if ok else 'BLOCK'} |" for key, ok in checks.items()],
        "",
        "Camera split:",
        "",
        "```text",
        f"train: {', '.join(train_cams)}",
        f"heldout: {', '.join(test_cams)}",
        f"target_focal: {args.target_focal}",
        "```",
        "",
        "Train mask coverage:",
        "",
        "| camera | coverage | projected faces | depth median |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in adapter_rows:
        if row["role"] == "real_gt_train":
            lines.append(f"| {row['camera']} | {row['mask_coverage']:.4f} | {row['projected_faces']} | {row['depth_median']:.3f} |")
    lines.extend(
        [
            "",
            "Closure:",
            "",
            "```text",
            summary["closure"],
            "```",
            "",
            "Next gate:",
            "",
            "```text",
            "G24 should run a CPU-only dry-run over the generated adapter, checking RI3D",
            "file contracts and held-out metric definitions. Select an idle GPU only if",
            "G24 passes.",
            "```",
            "",
        ]
    )
    (repo / args.output_md).parent.mkdir(parents=True, exist_ok=True)
    (repo / args.output_md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote adapter to {args.output_root}")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.output_figure}")
    print(verdict)


if __name__ == "__main__":
    main()
