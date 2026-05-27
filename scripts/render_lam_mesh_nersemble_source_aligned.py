#!/usr/bin/env python3
"""Render LAM mesh into NeRSemble cameras after source-mask-only alignment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np

from render_lam_mesh_nersemble_true_krt import load_colored_obj, sample_mesh_points  # type: ignore
from render_nersemble_pointcloud_heldout import (  # type: ignore
    load_json,
    make_sheet,
    sha256_file,
    write_json,
    write_rgba,
    zbuffer_points,
)


DATE = "2026-05-27"
GATE = "G63"
PASS_VERDICT = "PASS_LAM_MESH_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC"
BLOCKED_VERDICT = "BLOCKED_LAM_MESH_TRUE_KRT_SOURCE_MASK_ALIGNMENT"


def read_mask(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"could not read {path}")
    return mask > 8


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / max(union, 1))


def project_mask(
    xyz: np.ndarray,
    intrinsic: np.ndarray,
    world_to_camera: np.ndarray,
    width: int,
    height: int,
    scale: float,
    translation: np.ndarray,
    radius: int,
) -> np.ndarray:
    points = xyz * scale + translation[None, :]
    points_h = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
    camera = (world_to_camera.astype(np.float32) @ points_h.T).T[:, :3]
    z = camera[:, 2]
    valid = z > 1e-6
    u = intrinsic[0, 0] * (camera[:, 0] / z) + intrinsic[0, 2]
    v = intrinsic[1, 1] * (camera[:, 1] / z) + intrinsic[1, 2]
    u_i = np.rint(u).astype(np.int32)
    v_i = np.rint(v).astype(np.int32)
    valid &= (u_i >= 0) & (u_i < width) & (v_i >= 0) & (v_i < height)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[v_i[valid], u_i[valid]] = 255
    if radius > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
        mask = cv2.dilate(mask, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask > 0


def rasterize_colored_mesh(
    vertices: np.ndarray,
    colors: np.ndarray,
    faces: np.ndarray,
    intrinsic: np.ndarray,
    world_to_camera: np.ndarray,
    width: int,
    height: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    points_h = np.concatenate([vertices, np.ones((len(vertices), 1), dtype=np.float32)], axis=1)
    camera = (world_to_camera.astype(np.float32) @ points_h.T).T[:, :3]
    z = camera[:, 2]
    valid_z = z > 1e-6
    u = intrinsic[0, 0] * (camera[:, 0] / np.maximum(z, 1e-6)) + intrinsic[0, 2]
    v = intrinsic[1, 1] * (camera[:, 1] / np.maximum(z, 1e-6)) + intrinsic[1, 2]

    image = np.full((height, width, 3), 255, dtype=np.uint8)
    alpha = np.zeros((height, width), dtype=np.uint8)
    depth = np.full((height, width), np.inf, dtype=np.float32)
    rasterized_faces = 0

    for face in faces:
        if not bool(np.all(valid_z[face])):
            continue
        xs = u[face].astype(np.float32)
        ys = v[face].astype(np.float32)
        zs = z[face].astype(np.float32)
        if np.max(xs) < 0 or np.min(xs) >= width or np.max(ys) < 0 or np.min(ys) >= height:
            continue
        x0 = max(int(np.floor(float(np.min(xs)))), 0)
        x1 = min(int(np.ceil(float(np.max(xs)))), width - 1)
        y0 = max(int(np.floor(float(np.min(ys)))), 0)
        y1 = min(int(np.ceil(float(np.max(ys)))), height - 1)
        if x1 < x0 or y1 < y0:
            continue

        denom = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(float(denom)) < 1e-8:
            continue

        yy, xx = np.mgrid[y0 : y1 + 1, x0 : x1 + 1].astype(np.float32)
        px = xx + 0.5
        py = yy + 0.5
        w0 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / denom
        w1 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / denom
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not bool(np.any(inside)):
            continue

        tri_z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        patch_depth = depth[y0 : y1 + 1, x0 : x1 + 1]
        update = inside & (tri_z > 1e-6) & (tri_z < patch_depth)
        if not bool(np.any(update)):
            continue

        tri_colors = colors[face].astype(np.float32)
        patch_rgb = (
            w0[..., None] * tri_colors[0][None, None, :]
            + w1[..., None] * tri_colors[1][None, None, :]
            + w2[..., None] * tri_colors[2][None, None, :]
        )
        patch_image = image[y0 : y1 + 1, x0 : x1 + 1]
        patch_alpha = alpha[y0 : y1 + 1, x0 : x1 + 1]
        patch_image[update] = np.clip(patch_rgb[update], 0, 255).astype(np.uint8)
        patch_alpha[update] = 255
        patch_depth[update] = tri_z[update]
        rasterized_faces += 1

    in_frame = valid_z & (u >= 0) & (u < width) & (v >= 0) & (v < height)
    finite_depth = depth[np.isfinite(depth)]
    stats = {
        "projected_points": int(np.count_nonzero(in_frame)),
        "rasterized_faces": int(rasterized_faces),
        "rasterized_pixels": int(np.count_nonzero(alpha)),
        "coverage": float(np.count_nonzero(alpha) / alpha.size),
        "z_min": float(np.min(finite_depth)) if finite_depth.size else None,
        "z_max": float(np.max(finite_depth)) if finite_depth.size else None,
    }
    return image, alpha, stats


def optimize_source_alignment(
    xyz: np.ndarray,
    intrinsic: np.ndarray,
    world_to_camera: np.ndarray,
    target_mask: np.ndarray,
    radius: int,
) -> tuple[float, np.ndarray, list[dict[str, Any]]]:
    height, width = target_mask.shape
    scale = 1.0
    translation = np.zeros(3, dtype=np.float32)
    steps = [0.12, 0.06, 0.03, 0.015, 0.0075]
    trace: list[dict[str, Any]] = []

    def score(s: float, t: np.ndarray) -> float:
        pred = project_mask(xyz, intrinsic, world_to_camera, width, height, s, t, radius)
        return mask_iou(pred, target_mask)

    best = score(scale, translation)
    trace.append({"scale": scale, "translation": translation.astype(float).tolist(), "source_mask_iou": best})
    for step in steps:
        improved = True
        while improved:
            improved = False
            candidates: list[tuple[float, np.ndarray]] = []
            for ds in (-step, step):
                candidates.append((max(0.2, scale + ds), translation.copy()))
            for axis in range(3):
                for sign in (-1.0, 1.0):
                    t = translation.copy()
                    t[axis] += sign * step
                    candidates.append((scale, t))
            for cand_scale, cand_t in candidates:
                cand_score = score(cand_scale, cand_t)
                if cand_score > best + 1e-4:
                    scale, translation, best = cand_scale, cand_t, cand_score
                    improved = True
                    trace.append({"scale": scale, "translation": translation.astype(float).tolist(), "source_mask_iou": best})
                    break
    return scale, translation, trace


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} LAM Mesh Source-Aligned True-KRT Render",
        "",
        f"Date: {payload['date']}",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Alignment:",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in payload["alignment"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            f"| render_mode | {payload['render_mode']} |",
            f"| camera_contract | {payload['camera_contract']} |",
        ]
    )
    lines.extend(
        [
            "",
            "Render summary:",
            "",
            "| serial | role | projected points | coverage | output |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in payload["renders"]:
        lines.append(
            f"| {row['serial']} | {row['role']} | {row['stats']['projected_points']} | "
            f"{row['stats']['coverage']:.6f} | {row['render_path']} |"
        )
    lines.extend(
        [
            "",
            "Private contact sheet:",
            "",
            "```text",
            payload["private_outputs"]["contact_sheet"],
            "```",
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
            "",
            "Next gate:",
            "",
            "```text",
            payload["next_gate"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--mesh", type=Path, default=Path("external/LAM/exps/cano_gs/cam_222200042_frame_00000_textured_mesh.obj"))
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned"))
    parser.add_argument("--surface-samples", type=int, default=250000)
    parser.add_argument("--optimize-subsample", type=int, default=50000)
    parser.add_argument("--optimize-radius", type=int, default=9)
    parser.add_argument("--splat-radius", type=int, default=4)
    parser.add_argument("--seed", type=int, default=60527)
    parser.add_argument("--gate", default=GATE)
    parser.add_argument("--render-mode", choices=["point", "triangle"], default="point")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g63_lam_mesh_true_krt_source_aligned_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g63_lam_mesh_true_krt_source_aligned_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    mesh_path = args.mesh if args.mesh.is_absolute() else repo / args.mesh
    vertices, colors, faces = load_colored_obj(mesh_path)
    sampled_xyz, sampled_rgb = sample_mesh_points(vertices, colors, faces, args.surface_samples, args.seed)

    source_serial = adapter["split"]["source_serial"]
    source_view = next(row for row in adapter["views"] if row["serial"] == source_serial)
    source_mask = read_mask(Path(source_view["mask_path"]))
    source_intrinsic = np.asarray(calibration["intrinsics"][source_serial], dtype=np.float32)
    source_w2c = np.asarray(calibration["world_2_cam"][source_serial], dtype=np.float32)
    rng = np.random.default_rng(args.seed)
    if len(sampled_xyz) > args.optimize_subsample:
        opt_ids = rng.choice(len(sampled_xyz), size=args.optimize_subsample, replace=False)
        opt_xyz = sampled_xyz[opt_ids]
    else:
        opt_xyz = sampled_xyz
    scale, translation, trace = optimize_source_alignment(opt_xyz, source_intrinsic, source_w2c, source_mask, args.optimize_radius)
    aligned_xyz = sampled_xyz * scale + translation[None, :]
    aligned_vertices = vertices * scale + translation[None, :]

    prediction_root = args.output_root / "predictions"
    all_root = args.output_root / "all_rendered_frames"
    all_root.mkdir(parents=True, exist_ok=True)
    prediction_root.mkdir(parents=True, exist_ok=True)
    eval_serials = adapter["split"]["local_eval_serials"]
    serials = [source_serial] + [serial for serial in eval_serials if serial != source_serial]

    renders: list[dict[str, Any]] = []
    for serial in serials:
        view = next(row for row in adapter["views"] if row["serial"] == serial)
        width = int(view["image_width"])
        height = int(view["image_height"])
        intrinsic = np.asarray(calibration["intrinsics"][serial], dtype=np.float32)
        world_to_camera = np.asarray(calibration["world_2_cam"][serial], dtype=np.float32)
        if args.render_mode == "triangle":
            image, alpha, stats = rasterize_colored_mesh(aligned_vertices, colors, faces, intrinsic, world_to_camera, width, height)
        else:
            image, alpha, stats = zbuffer_points(aligned_xyz, sampled_rgb, intrinsic, world_to_camera, width, height, args.splat_radius)
        role = "source_render" if serial == source_serial else "heldout_prediction"
        out_path = all_root / f"cam_{serial}_frame_00000.png"
        write_rgba(out_path, image, alpha)
        row = {
            "serial": serial,
            "role": role,
            "render_path": str(out_path),
            "render_sha256": sha256_file(out_path),
            "target_rgb_path": view["rgb_path"],
            "target_mask_path": view["mask_path"],
            "stats": stats,
        }
        if serial in eval_serials:
            pred_path = prediction_root / f"cam_{serial}_frame_00000.png"
            write_rgba(pred_path, image, alpha)
            row["prediction_path"] = str(pred_path)
            row["prediction_sha256"] = sha256_file(pred_path)
        renders.append(row)

    sheet_path = args.output_root / "g63_private_lam_mesh_source_aligned_sheet.png"
    make_sheet(renders, sheet_path)
    source_iou = trace[-1]["source_mask_iou"]
    passed = source_iou >= 0.45 and all(row["stats"]["projected_points"] > 1000 for row in renders)
    verdict = PASS_VERDICT if passed else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": (
            "Align LAM textured mesh output to the G54 NeRSemble source view using only source camera intrinsics/extrinsics and source alpha mask, "
            "then render that fixed mesh into held-out cameras with true K/R/T. This avoids held-out and GT pointcloud alignment but remains diagnostic if appearance is broken."
        ),
        "verdict": verdict,
        "method": "LAM-20K textured mesh",
        "camera_mode": "nersemble_krt",
        "camera_contract_verified": True,
        "render_mode": args.render_mode,
        "case": adapter["case"],
        "split": adapter["split"],
        "mesh": {
            "path": str(mesh_path),
            "vertices": int(len(vertices)),
            "faces": int(len(faces)),
            "surface_samples": int(args.surface_samples),
            "sampled_points_total": int(len(aligned_xyz)),
            "vertices_after_alignment": int(len(aligned_vertices)),
        },
        "alignment": {
            "alignment": "source_mask_coordinate_descent_similarity_no_rotation",
            "uses_gt_geometry_for_alignment": False,
            "uses_heldout_views_for_alignment": False,
            "source_serial": source_serial,
            "source_mask_iou": source_iou,
            "scale": scale,
            "translation": translation.astype(float).tolist(),
            "trace": trace,
        },
        "camera_contract": "official_nersemble_world_2_cam_and_intrinsics",
        "prediction_root": str(prediction_root),
        "renders": renders,
        "private_outputs": {
            "contact_sheet": str(sheet_path),
            "contact_sheet_sha256": sha256_file(sheet_path),
        },
        "artifact_policy": "Identifiable source/eval RGB and LAM renders stay under 3dv_work; commit repo-safe metrics/hashes/mask-only figures unless user reviews redistribution.",
        "decision": (
            "Source-mask-only alignment produced nonempty true-KRT LAM mesh renders. Interpretation still depends on visual/evaluator gates."
            if passed
            else "Blocked: source-mask-only alignment did not produce a usable source silhouette or true-camera renders."
        ),
        "next_gate": (
            "Run the held-out evaluator and visual gate. If appearance remains broken, switch to a method with native camera-aligned output or implement a better source-derived pose/scale solver."
        ),
    }
    write_json(args.output_root / "render_manifest.json", payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "source_mask_iou": source_iou, "prediction_root": str(prediction_root), "sheet": str(sheet_path)}, indent=2))
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
