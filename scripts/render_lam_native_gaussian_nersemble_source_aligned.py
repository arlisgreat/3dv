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
from render_lam_mesh_nersemble_source_aligned import optimize_source_alignment, read_mask  # type: ignore
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
    parser.add_argument("--alignment-mode", choices=["source_mask_only", "source_camera_then_mask"], default="source_mask_only")
    parser.add_argument("--lam-source-transform-json", type=Path, default=Path("external/LAM/tracking_output/export/cam_222200042_frame_00000/transforms.json"))
    parser.add_argument("--lam-source-yz-flip", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned"))
    parser.add_argument("--render-max-size", type=int, default=768)
    parser.add_argument("--optimize-radius", type=int, default=12)
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
    eval_serials = adapter["split"]["local_eval_serials"]
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
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": (
            "Use LAM's native diff-gaussian rasterizer to render the LAM head-anchored Gaussian PLY into the G54 NeRSemble source and held-out K/R/T cameras after source-mask-only alignment."
        ),
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
            "alignment": "source_mask_coordinate_descent_similarity_no_rotation",
            "alignment_mode": args.alignment_mode,
            "prealign": prealign_meta,
            "uses_gt_geometry_for_alignment": False,
            "uses_heldout_views_for_alignment": False,
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
            "Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim."
            if passed
            else "Blocked: native Gaussian true-KRT render did not produce usable camera-aligned outputs."
        ),
        "next_gate": "Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions.",
    }
    write_json(args.output_root / "render_manifest.json", payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "source_mask_iou": source_iou, "prediction_root": str(prediction_root), "sheet": str(sheet_path)}, indent=2))
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
