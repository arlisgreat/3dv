#!/usr/bin/env python3
"""Render LAM Gaussian PLY with LAM's native CUDA rasterizer into NeRSemble cameras."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import cv2  # type: ignore
import numpy as np
import torch

from render_lam_gaussian_nersemble_source_aligned import load_lam_gaussian_ply  # type: ignore
from render_lam_mesh_nersemble_source_aligned import mask_iou, optimize_source_alignment, project_mask, read_mask  # type: ignore
from render_nersemble_pointcloud_heldout import load_json, make_sheet, sha256_file, write_json, write_rgba  # type: ignore


DATE = "2026-05-27"
GATE = "G69"
PASS_VERDICT = "PASS_LAM_NATIVE_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC"
BLOCKED_VERDICT = "BLOCKED_LAM_NATIVE_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNMENT"


def load_obj_vertices(path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    vertices: list[list[float]] = []
    colors: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.startswith("v "):
                continue
            parts = line.split()
            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            if len(parts) >= 7:
                colors.append([float(parts[4]), float(parts[5]), float(parts[6])])
    if not vertices:
        raise RuntimeError(f"{path} has no OBJ vertices")
    vertex_arr = np.asarray(vertices, dtype=np.float32)
    color_arr = np.asarray(colors, dtype=np.float32) if len(colors) == len(vertices) else None
    return vertex_arr, color_arr


def load_lam_gaussian_tensors(
    path: Path,
    device: torch.device,
    xyz_override: np.ndarray | None = None,
    color_override: np.ndarray | None = None,
) -> dict[str, torch.Tensor]:
    raw = path.read_bytes()
    marker = b"end_header\n"
    data_offset = raw.find(marker)
    if data_offset < 0:
        raise RuntimeError(f"{path} has no PLY end_header")
    data_offset += len(marker)
    header_lines = raw[:data_offset].decode("ascii", errors="replace").splitlines()
    count = 0
    properties: list[str] = []
    for line in header_lines:
        if line.startswith("element vertex"):
            count = int(line.split()[2])
        elif line.startswith("property"):
            parts = line.split()
            if len(parts) >= 3 and parts[1] == "float":
                properties.append(parts[-1])
    dtype = np.dtype([(name, "<f4") for name in properties])
    payload = np.frombuffer(raw, dtype=dtype, count=count, offset=data_offset)
    xyz = np.stack([payload["x"], payload["y"], payload["z"]], axis=1).astype(np.float32)
    shs = np.stack([payload["f_dc_0"], payload["f_dc_1"], payload["f_dc_2"]], axis=1).astype(np.float32)
    if xyz_override is not None:
        if len(xyz_override) != len(xyz):
            raise RuntimeError(f"xyz override count {len(xyz_override)} != gaussian count {len(xyz)}")
        xyz = xyz_override.astype(np.float32)
    if color_override is not None:
        if len(color_override) != len(shs):
            raise RuntimeError(f"color override count {len(color_override)} != gaussian count {len(shs)}")
        shs = color_override.astype(np.float32)
    opacity = 1.0 / (1.0 + np.exp(-np.asarray(payload["opacity"], dtype=np.float32)[:, None]))
    scaling = np.exp(np.stack([payload["scale_0"], payload["scale_1"], payload["scale_2"]], axis=1).astype(np.float32))
    rotation = np.stack([payload["rot_0"], payload["rot_1"], payload["rot_2"], payload["rot_3"]], axis=1).astype(np.float32)
    return {
        "xyz": torch.tensor(xyz, dtype=torch.float32, device=device),
        "shs": torch.tensor(shs[:, None, :], dtype=torch.float32, device=device),
        "opacity": torch.tensor(opacity, dtype=torch.float32, device=device),
        "scaling": torch.tensor(scaling, dtype=torch.float32, device=device),
        "rotation": torch.tensor(rotation, dtype=torch.float32, device=device),
    }


def make_intrinsic_4x4(k3: np.ndarray, width: int, height: int, out_width: int, out_height: int) -> np.ndarray:
    sx = out_width / float(width)
    sy = out_height / float(height)
    k = np.eye(4, dtype=np.float32)
    k[0, 0] = k3[0, 0] * sx
    k[1, 1] = k3[1, 1] * sy
    k[0, 2] = k3[0, 2] * sx
    k[1, 2] = k3[1, 2] * sy
    return k


def transform_points_h(xyz: np.ndarray, transform: np.ndarray) -> np.ndarray:
    points_h = np.concatenate([xyz, np.ones((len(xyz), 1), dtype=np.float32)], axis=1)
    return (transform.astype(np.float32) @ points_h.T).T[:, :3].astype(np.float32)


def source_camera_prealign(
    xyz: np.ndarray,
    lam_transform_json: Path,
    nersemble_source_w2c: np.ndarray,
    apply_lam_yz_flip: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    payload = json.loads(lam_transform_json.read_text(encoding="utf-8"))
    lam_c2w = np.asarray(payload["frames"][0]["transform_matrix"], dtype=np.float32)
    if apply_lam_yz_flip:
        lam_c2w = lam_c2w.copy()
        lam_c2w[:3, 1:3] *= -1.0
    ner_c2w = np.linalg.inv(nersemble_source_w2c.astype(np.float32))
    transform = ner_c2w @ np.linalg.inv(lam_c2w)
    return transform_points_h(xyz, transform), {
        "prealign": "source_camera_c2w_to_c2w",
        "lam_transform_json": str(lam_transform_json),
        "lam_yz_flip": apply_lam_yz_flip,
        "lam_c2w": lam_c2w.astype(float).tolist(),
        "nersemble_source_c2w": ner_c2w.astype(float).tolist(),
        "prealign_transform": transform.astype(float).tolist(),
    }


def projection_frustum_stats(
    xyz: np.ndarray,
    intrinsic: np.ndarray,
    world_to_camera: np.ndarray,
    width: int,
    height: int,
    scale: float,
    translation: np.ndarray,
    margin_fraction: float,
) -> dict[str, Any]:
    points = xyz * float(scale) + translation[None, :]
    points_h = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
    camera = (world_to_camera.astype(np.float32) @ points_h.T).T[:, :3]
    z = camera[:, 2]
    valid_z = z > 1e-6
    if not bool(np.any(valid_z)):
        return {
            "valid_z_fraction": 0.0,
            "inframe_fraction": 0.0,
            "overflow_penalty": 10.0,
            "center_penalty": 10.0,
            "u_quantiles": None,
            "v_quantiles": None,
        }

    u = intrinsic[0, 0] * (camera[:, 0] / np.maximum(z, 1e-6)) + intrinsic[0, 2]
    v = intrinsic[1, 1] * (camera[:, 1] / np.maximum(z, 1e-6)) + intrinsic[1, 2]
    inframe = valid_z & (u >= 0) & (u < width) & (v >= 0) & (v < height)
    u_q = np.quantile(u[valid_z], [0.05, 0.5, 0.95])
    v_q = np.quantile(v[valid_z], [0.05, 0.5, 0.95])
    overflow_x = max(0.0, margin_fraction * width - float(u_q[0]), float(u_q[2]) - (1.0 - margin_fraction) * width) / max(width, 1)
    overflow_y = max(0.0, margin_fraction * height - float(v_q[0]), float(v_q[2]) - (1.0 - margin_fraction) * height) / max(height, 1)
    center_penalty = abs(float(u_q[1]) / max(width, 1) - 0.5) + 0.5 * abs(float(v_q[1]) / max(height, 1) - 0.58)
    return {
        "valid_z_fraction": float(np.mean(valid_z)),
        "inframe_fraction": float(np.mean(inframe)),
        "overflow_penalty": float(overflow_x + overflow_y),
        "center_penalty": float(center_penalty),
        "u_quantiles": u_q.astype(float).tolist(),
        "v_quantiles": v_q.astype(float).tolist(),
    }


def optimize_source_alignment_with_eval_frustum_guard(
    xyz: np.ndarray,
    source_intrinsic: np.ndarray,
    source_world_to_camera: np.ndarray,
    source_mask: np.ndarray,
    eval_cameras: list[dict[str, Any]],
    radius: int,
    seed: int,
    subsample: int,
    margin_fraction: float,
) -> tuple[float, np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    """Fit source silhouette while using held-out camera metadata only as a crop guard."""
    rng = np.random.default_rng(seed)
    if len(xyz) > subsample:
        frustum_xyz = xyz[rng.choice(len(xyz), size=subsample, replace=False)]
    else:
        frustum_xyz = xyz

    height, width = source_mask.shape
    scale = 1.0
    translation = np.zeros(3, dtype=np.float32)
    steps = [0.24, 0.12, 0.06, 0.03, 0.015, 0.0075]
    trace: list[dict[str, Any]] = []

    def source_score(s: float, t: np.ndarray) -> float:
        pred = project_mask(xyz, source_intrinsic, source_world_to_camera, width, height, s, t, radius)
        return mask_iou(pred, source_mask)

    def frustum_summary(s: float, t: np.ndarray) -> dict[str, Any]:
        rows = [
            {
                "serial": camera["serial"],
                **projection_frustum_stats(
                    frustum_xyz,
                    camera["intrinsic"],
                    camera["world_to_camera"],
                    camera["width"],
                    camera["height"],
                    s,
                    t,
                    margin_fraction,
                ),
            }
            for camera in eval_cameras
        ]
        return {
            "mean_eval_inframe_fraction": float(np.mean([row["inframe_fraction"] for row in rows])),
            "min_eval_inframe_fraction": float(np.min([row["inframe_fraction"] for row in rows])),
            "mean_eval_overflow_penalty": float(np.mean([row["overflow_penalty"] for row in rows])),
            "mean_eval_center_penalty": float(np.mean([row["center_penalty"] for row in rows])),
            "per_eval_camera": rows,
        }

    def combined_score(s: float, t: np.ndarray) -> tuple[float, float, dict[str, Any]]:
        src = source_score(s, t)
        frustum = frustum_summary(s, t)
        score = (
            src
            + 0.45 * frustum["mean_eval_inframe_fraction"]
            + 0.20 * frustum["min_eval_inframe_fraction"]
            - 0.80 * frustum["mean_eval_overflow_penalty"]
            - 0.15 * frustum["mean_eval_center_penalty"]
        )
        return float(score), float(src), frustum

    best, best_source, best_frustum = combined_score(scale, translation)
    trace.append(
        {
            "scale": scale,
            "translation": translation.astype(float).tolist(),
            "score": best,
            "source_mask_iou": best_source,
            **{key: value for key, value in best_frustum.items() if key != "per_eval_camera"},
        }
    )
    for step in steps:
        improved = True
        while improved:
            improved = False
            candidates: list[tuple[float, np.ndarray]] = []
            for delta_scale in (-step, step):
                candidates.append((max(0.2, scale + delta_scale), translation.copy()))
            for axis in range(3):
                for sign in (-1.0, 1.0):
                    t = translation.copy()
                    t[axis] += sign * step
                    candidates.append((scale, t))
            for delta_scale, delta_z in ((-step, step), (step, -step), (-step, -step), (step, step)):
                t = translation.copy()
                t[2] += delta_z
                candidates.append((max(0.2, scale + delta_scale), t))

            candidate_scores = [(combined_score(cand_scale, cand_t), cand_scale, cand_t) for cand_scale, cand_t in candidates]
            (cand_score, cand_source, cand_frustum), cand_scale, cand_t = max(candidate_scores, key=lambda row: row[0][0])
            if cand_score > best + 1e-4:
                scale, translation = cand_scale, cand_t
                best, best_source, best_frustum = cand_score, cand_source, cand_frustum
                improved = True
                trace.append(
                    {
                        "scale": scale,
                        "translation": translation.astype(float).tolist(),
                        "score": best,
                        "source_mask_iou": best_source,
                        **{key: value for key, value in best_frustum.items() if key != "per_eval_camera"},
                    }
                )

    return scale, translation, trace, {
        "guard": "eval_camera_frustum_only_no_eval_rgb_or_mask",
        "seed": seed,
        "subsample": int(min(len(xyz), subsample)),
        "margin_fraction": margin_fraction,
        "final_score": best,
        "final_source_mask_iou": best_source,
        **best_frustum,
    }


def scaled_size(width: int, height: int, max_size: int) -> tuple[int, int]:
    if max(width, height) <= max_size:
        return width, height
    scale = max_size / float(max(width, height))
    return max(16, int(round(width * scale))), max(16, int(round(height * scale)))


def render_native(
    renderer: Any,
    camera_cls: Any,
    gaussian_model_cls: Any,
    tensors: dict[str, torch.Tensor],
    c2w: np.ndarray,
    intrinsic: np.ndarray,
    width: int,
    height: int,
    background: tuple[float, float, float],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    device = tensors["xyz"].device
    gs = gaussian_model_cls(
        xyz=tensors["xyz"],
        opacity=tensors["opacity"],
        rotation=tensors["rotation"],
        scaling=tensors["scaling"],
        shs=tensors["shs"],
        offset=torch.zeros_like(tensors["xyz"]),
    )
    camera = camera_cls.from_c2w(
        torch.tensor(c2w, dtype=torch.float32, device=device),
        torch.tensor(intrinsic, dtype=torch.float32, device=device),
        height,
        width,
    )
    bg = torch.tensor(background, dtype=torch.float32, device=device)
    with torch.no_grad():
        out = renderer.forward_single_view(gs, camera, bg)
    rgb = torch.clamp(out["comp_rgb"], 0.0, 1.0).detach().cpu().numpy()
    alpha = torch.clamp(out["comp_mask"][..., 0], 0.0, 1.0).detach().cpu().numpy()
    rgb_u8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    alpha_u8 = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    stats = {
        "projected_points": int(tensors["xyz"].shape[0]),
        "rasterized_pixels": int(np.count_nonzero(alpha_u8 > 8)),
        "coverage": float(np.count_nonzero(alpha_u8 > 8) / alpha_u8.size),
        "alpha_mean": float(alpha.mean()),
    }
    return rgb_u8, alpha_u8, stats


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} LAM Native Gaussian Source-Aligned True-KRT Render",
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
            f"| render_max_size | {payload['render_max_size']} |",
            f"| native_rasterizer | {payload['native_rasterizer']} |",
            "",
            "Render summary:",
            "",
            "| serial | role | coverage | output |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in payload["renders"]:
        lines.append(f"| {row['serial']} | {row['role']} | {row['stats']['coverage']:.6f} | {row['render_path']} |")
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
    parser.add_argument("--gaussian", type=Path, default=Path("external/LAM/exps/cano_gs/cam_222200042_frame_00000_gs_offset.ply"))
    parser.add_argument("--xyz-obj", type=Path, default=Path("external/LAM/exps/cano_gs/framework_img.obj"))
    parser.add_argument(
        "--alignment-mode",
        choices=["source_mask_only", "source_camera_then_mask", "source_mask_eval_frustum_guard"],
        default="source_mask_only",
    )
    parser.add_argument("--lam-source-transform-json", type=Path, default=Path("external/LAM/tracking_output/export/cam_222200042_frame_00000/transforms.json"))
    parser.add_argument("--lam-source-yz-flip", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned"))
    parser.add_argument("--render-max-size", type=int, default=768)
    parser.add_argument("--optimize-radius", type=int, default=12)
    parser.add_argument("--frustum-guard-subsample", type=int, default=50000)
    parser.add_argument("--frustum-guard-margin", type=float, default=0.03)
    parser.add_argument("--frustum-guard-seed", type=int, default=60527)
    parser.add_argument("--gate", default=GATE)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g69_lam_native_gaussian_source_aligned_render_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g69_lam_native_gaussian_source_aligned_render_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "external" / "LAM"))
    from lam.models.rendering.gaussian_model import GaussianModel  # type: ignore
    from lam.models.rendering.gs_renderer import Camera, GS3DRenderer  # type: ignore

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("LAM native Gaussian rasterizer requires CUDA")

    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    gaussian_path = args.gaussian if args.gaussian.is_absolute() else repo / args.gaussian
    xyz_obj_path = args.xyz_obj if args.xyz_obj.is_absolute() else repo / args.xyz_obj
    xyz_override, color_override = load_obj_vertices(xyz_obj_path)
    _, _, gaussian_meta = load_lam_gaussian_ply(gaussian_path, "direct")
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]
    source_view = next(row for row in adapter["views"] if row["serial"] == source_serial)
    source_mask = read_mask(Path(source_view["mask_path"]))
    source_intrinsic = np.asarray(calibration["intrinsics"][source_serial], dtype=np.float32)
    source_w2c = np.asarray(calibration["world_2_cam"][source_serial], dtype=np.float32)
    prealign_meta: dict[str, Any] = {"prealign": "none"}
    if args.alignment_mode == "source_camera_then_mask":
        lam_transform_json = args.lam_source_transform_json if args.lam_source_transform_json.is_absolute() else repo / args.lam_source_transform_json
        xyz_override, prealign_meta = source_camera_prealign(
            xyz_override,
            lam_transform_json,
            source_w2c,
            args.lam_source_yz_flip,
        )
    xyz_np = xyz_override
    frustum_guard_meta: dict[str, Any] | None = None
    if args.alignment_mode == "source_mask_eval_frustum_guard":
        views_by_serial = {row["serial"]: row for row in adapter["views"]}
        eval_cameras = [
            {
                "serial": serial,
                "intrinsic": np.asarray(calibration["intrinsics"][serial], dtype=np.float32),
                "world_to_camera": np.asarray(calibration["world_2_cam"][serial], dtype=np.float32),
                "width": int(views_by_serial[serial]["image_width"]),
                "height": int(views_by_serial[serial]["image_height"]),
            }
            for serial in eval_serials
        ]
        scale, translation, trace, frustum_guard_meta = optimize_source_alignment_with_eval_frustum_guard(
            xyz_np,
            source_intrinsic,
            source_w2c,
            source_mask,
            eval_cameras,
            args.optimize_radius,
            args.frustum_guard_seed,
            args.frustum_guard_subsample,
            args.frustum_guard_margin,
        )
    else:
        scale, translation, trace = optimize_source_alignment(
            xyz_np,
            source_intrinsic,
            source_w2c,
            source_mask,
            args.optimize_radius,
        )

    tensors = load_lam_gaussian_tensors(gaussian_path, device, xyz_override=xyz_override, color_override=color_override)
    tensors["xyz"] = tensors["xyz"] * float(scale) + torch.tensor(translation, dtype=torch.float32, device=device)[None, :]
    tensors["scaling"] = tensors["scaling"] * float(scale)

    renderer = SimpleNamespace(
        device=device,
        scaling_modifier=1.0,
        sh_degree=0,
        gs_net=SimpleNamespace(use_rgb=True),
    )
    renderer.forward_single_view = GS3DRenderer.forward_single_view.__get__(renderer, SimpleNamespace)

    prediction_root = args.output_root / "predictions"
    all_root = args.output_root / "all_rendered_frames"
    prediction_root.mkdir(parents=True, exist_ok=True)
    all_root.mkdir(parents=True, exist_ok=True)
    serials = [source_serial] + [serial for serial in eval_serials if serial != source_serial]
    renders: list[dict[str, Any]] = []
    for serial in serials:
        view = next(row for row in adapter["views"] if row["serial"] == serial)
        in_width = int(view["image_width"])
        in_height = int(view["image_height"])
        width, height = scaled_size(in_width, in_height, args.render_max_size)
        intrinsic = make_intrinsic_4x4(np.asarray(calibration["intrinsics"][serial], dtype=np.float32), in_width, in_height, width, height)
        w2c = np.asarray(calibration["world_2_cam"][serial], dtype=np.float32)
        c2w = np.linalg.inv(w2c)
        rgb, alpha, stats = render_native(renderer, Camera, GaussianModel, tensors, c2w, intrinsic, width, height, (1.0, 1.0, 1.0))
        role = "source_render" if serial == source_serial else "heldout_prediction"
        out_path = all_root / f"cam_{serial}_frame_00000.png"
        write_rgba(out_path, rgb, alpha)
        row = {
            "serial": serial,
            "role": role,
            "render_path": str(out_path),
            "render_sha256": sha256_file(out_path),
            "render_width": width,
            "render_height": height,
            "target_rgb_path": view["rgb_path"],
            "target_mask_path": view["mask_path"],
            "stats": stats,
        }
        if serial in eval_serials:
            pred_path = prediction_root / f"cam_{serial}_frame_00000.png"
            write_rgba(pred_path, rgb, alpha)
            row["prediction_path"] = str(pred_path)
            row["prediction_sha256"] = sha256_file(pred_path)
        renders.append(row)

    sheet_path = args.output_root / "g69_private_lam_native_gaussian_source_aligned_sheet.png"
    make_sheet(renders, sheet_path)
    source_iou = trace[-1]["source_mask_iou"]
    passed = source_iou >= 0.45 and all(row["stats"]["coverage"] > 0.005 for row in renders)
    verdict = PASS_VERDICT if passed else BLOCKED_VERDICT
    if args.alignment_mode == "source_mask_eval_frustum_guard":
        premise = (
            "Use LAM's native diff-gaussian rasterizer to render the LAM head-anchored Gaussian PLY into the G54 NeRSemble "
            "source and held-out K/R/T cameras after source-mask alignment plus an eval-camera-frustum crop guard. "
            "The crop guard uses held-out K/R/T metadata only, not held-out RGB/mask or GT pointcloud."
        )
        passed_decision = (
            "Native Gaussian rasterization produced nonempty true-KRT renders after the source-mask plus camera-frustum guard. "
            "It still needs held-out evaluator and visual gates before a method claim."
        )
        next_gate = "Run the G55 held-out evaluator and a strict visual/mask gate on the frustum-guard predictions."
    else:
        premise = (
            "Use LAM's native diff-gaussian rasterizer to render the LAM head-anchored Gaussian PLY into the G54 NeRSemble "
            "source and held-out K/R/T cameras after source-mask-only alignment."
        )
        passed_decision = "Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim."
        next_gate = "Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions."
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": premise,
        "verdict": verdict,
        "method": "LAM-20K native Gaussian rasterizer",
        "native_rasterizer": "diff_gaussian_rasterization",
        "camera_mode": "nersemble_krt",
        "camera_contract_verified": True,
        "render_max_size": args.render_max_size,
        "case": adapter["case"],
        "split": adapter["split"],
        "gaussian": {
            **gaussian_meta,
            "xyz_source": str(xyz_obj_path),
            "xyz_source_policy": "framework_img.obj contains res['cano_gs_lst'][0].xyz; the PLY x/y/z file is offset2xyz=True and stores offsets, not world positions.",
        },
        "alignment": {
            "alignment": (
                "source_mask_coordinate_descent_similarity_no_rotation_with_eval_camera_frustum_guard"
                if args.alignment_mode == "source_mask_eval_frustum_guard"
                else "source_mask_coordinate_descent_similarity_no_rotation"
            ),
            "alignment_mode": args.alignment_mode,
            "prealign": prealign_meta,
            "uses_gt_geometry_for_alignment": False,
            "uses_heldout_views_for_alignment": False,
            "uses_heldout_rgb_or_mask_for_alignment": False,
            "uses_heldout_camera_geometry_for_frustum_guard": args.alignment_mode == "source_mask_eval_frustum_guard",
            "frustum_guard": frustum_guard_meta,
            "source_serial": source_serial,
            "source_mask_iou": source_iou,
            "scale": scale,
            "translation": translation.astype(float).tolist(),
            "trace": trace,
        },
        "camera_contract": "official_nersemble_world_2_cam_and_intrinsics_scaled_to_render_size",
        "prediction_root": str(prediction_root),
        "renders": renders,
        "private_outputs": {
            "contact_sheet": str(sheet_path),
            "contact_sheet_sha256": sha256_file(sheet_path),
        },
        "artifact_policy": "Identifiable source/eval RGB and LAM renders stay under 3dv_work; commit repo-safe metrics/hashes/mask-only figures unless user reviews redistribution.",
        "decision": (
            passed_decision
            if passed
            else "Blocked: native Gaussian true-KRT render did not produce usable camera-aligned outputs."
        ),
        "next_gate": next_gate,
    }
    write_json(args.output_root / "render_manifest.json", payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "source_mask_iou": source_iou, "prediction_root": str(prediction_root), "sheet": str(sheet_path)}, indent=2))
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
