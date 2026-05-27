#!/usr/bin/env python3
"""Render a LAM mesh into G54 NeRSemble cameras with explicit diagnostic alignment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from render_nersemble_pointcloud_heldout import (  # type: ignore
    load_json,
    make_sheet,
    read_pcd_binary,
    sha256_file,
    write_json,
    write_md as write_pointcloud_md,
    write_rgba,
    zbuffer_points,
)


DATE = "2026-05-27"
GATE = "G61"
PASS_VERDICT = "PASS_DIAGNOSTIC_ONLY_LAM_MESH_TRUE_KRT_GT_BBOX_ALIGNED"
BLOCKED_VERDICT = "BLOCKED_LAM_MESH_TRUE_KRT_RENDER"


def load_colored_obj(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices: list[list[float]] = []
    colors: list[list[float]] = []
    faces: list[list[int]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("v "):
                parts = line.split()
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                if len(parts) >= 7:
                    colors.append([float(parts[4]), float(parts[5]), float(parts[6])])
                else:
                    colors.append([0.7, 0.7, 0.7])
            elif line.startswith("f "):
                items = line.split()[1:]
                face = [int(item.split("/")[0]) - 1 for item in items[:3]]
                faces.append(face)
    if not vertices or not faces:
        raise RuntimeError(f"could not load colored mesh vertices/faces from {path}")
    return (
        np.asarray(vertices, dtype=np.float32),
        np.clip(np.asarray(colors, dtype=np.float32) * 255.0, 0, 255).astype(np.uint8),
        np.asarray(faces, dtype=np.int32),
    )


def sample_mesh_points(
    vertices: np.ndarray,
    colors: np.ndarray,
    faces: np.ndarray,
    target_samples: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    tri = vertices[faces]
    tri_colors = colors[faces].astype(np.float32)
    areas = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    probs = areas / max(float(areas.sum()), 1e-12)
    face_ids = rng.choice(len(faces), size=target_samples, replace=True, p=probs)
    chosen = tri[face_ids]
    chosen_colors = tri_colors[face_ids]
    u = rng.random(target_samples, dtype=np.float32)
    v = rng.random(target_samples, dtype=np.float32)
    flip = u + v > 1.0
    u[flip] = 1.0 - u[flip]
    v[flip] = 1.0 - v[flip]
    w = 1.0 - u - v
    points = chosen[:, 0] * w[:, None] + chosen[:, 1] * u[:, None] + chosen[:, 2] * v[:, None]
    point_colors = chosen_colors[:, 0] * w[:, None] + chosen_colors[:, 1] * u[:, None] + chosen_colors[:, 2] * v[:, None]
    points = np.concatenate([vertices, points.astype(np.float32)], axis=0)
    point_colors = np.concatenate([colors, np.clip(point_colors, 0, 255).astype(np.uint8)], axis=0)
    return points, point_colors


def bbox_align_to_gt(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    src_min = source.min(axis=0)
    src_max = source.max(axis=0)
    tgt_min = target.min(axis=0)
    tgt_max = target.max(axis=0)
    src_center = (src_min + src_max) * 0.5
    tgt_center = (tgt_min + tgt_max) * 0.5
    src_extent = np.maximum(src_max - src_min, 1e-6)
    tgt_extent = np.maximum(tgt_max - tgt_min, 1e-6)
    scale = float(np.median(tgt_extent / src_extent))
    aligned = (source - src_center[None, :]) * scale + tgt_center[None, :]
    metadata = {
        "alignment": "gt_pointcloud_bbox_similarity_no_rotation",
        "uses_gt_geometry_for_alignment": True,
        "source_bbox_min": src_min.astype(float).tolist(),
        "source_bbox_max": src_max.astype(float).tolist(),
        "target_bbox_min": tgt_min.astype(float).tolist(),
        "target_bbox_max": tgt_max.astype(float).tolist(),
        "scale": scale,
        "translation_after_scale": (tgt_center - src_center * scale).astype(float).tolist(),
    }
    return aligned.astype(np.float32), metadata


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G61 LAM Mesh True-KRT Diagnostic Render",
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
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned"))
    parser.add_argument("--surface-samples", type=int, default=250000)
    parser.add_argument("--splat-radius", type=int, default=4)
    parser.add_argument("--seed", type=int, default=60527)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g61_lam_mesh_true_krt_bbox_aligned_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g61_lam_mesh_true_krt_bbox_aligned_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    gt_xyz, _, gt_header = read_pcd_binary(Path(adapter["pointcloud"]["path"]))
    mesh_path = args.mesh if args.mesh.is_absolute() else repo / args.mesh
    vertices, colors, faces = load_colored_obj(mesh_path)
    sampled_xyz, sampled_rgb = sample_mesh_points(vertices, colors, faces, args.surface_samples, args.seed)
    aligned_xyz, alignment = bbox_align_to_gt(sampled_xyz, gt_xyz)

    prediction_root = args.output_root / "predictions"
    all_root = args.output_root / "all_rendered_frames"
    all_root.mkdir(parents=True, exist_ok=True)
    prediction_root.mkdir(parents=True, exist_ok=True)
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]
    serials = [source_serial] + [serial for serial in eval_serials if serial != source_serial]

    renders: list[dict[str, Any]] = []
    for serial in serials:
        view = next(row for row in adapter["views"] if row["serial"] == serial)
        width = int(view["image_width"])
        height = int(view["image_height"])
        intrinsic = np.asarray(calibration["intrinsics"][serial], dtype=np.float32)
        world_to_camera = np.asarray(calibration["world_2_cam"][serial], dtype=np.float32)
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

    sheet_path = args.output_root / "g61_private_lam_mesh_true_krt_sheet.png"
    make_sheet(renders, sheet_path)
    passed = all(row["stats"]["projected_points"] > 1000 and row["stats"]["coverage"] > 0.005 for row in renders)
    verdict = PASS_VERDICT if passed else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "Render the LAM-20K textured mesh output into the G54 NeRSemble cameras after an explicit GT pointcloud bbox "
            "similarity alignment. This tests the renderer path for method-shaped geometry but is diagnostic-only because GT geometry is used for alignment."
        ),
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "mesh": {
            "path": str(mesh_path),
            "vertices": int(len(vertices)),
            "faces": int(len(faces)),
            "surface_samples": int(args.surface_samples),
            "sampled_points_total": int(len(aligned_xyz)),
        },
        "gt_pointcloud": {
            "path": adapter["pointcloud"]["path"],
            "loaded_points": gt_header["loaded_points"],
        },
        "alignment": alignment,
        "camera_contract": "official_nersemble_world_2_cam_and_intrinsics",
        "prediction_root": str(prediction_root),
        "renders": renders,
        "private_outputs": {
            "contact_sheet": str(sheet_path),
            "contact_sheet_sha256": sha256_file(sheet_path),
        },
        "artifact_policy": "Identifiable GT RGB and LAM renders stay under 3dv_work; commit repo-safe metrics/hashes unless user reviews redistribution.",
        "decision": (
            "LAM mesh renders are nonempty under the true NeRSemble K/R/T path, but this remains diagnostic-only because GT pointcloud bbox alignment was used."
            if passed
            else "Blocked: the aligned LAM mesh did not produce usable true-camera renders."
        ),
        "next_gate": (
            "Run the held-out evaluator on these diagnostic renders. A method-quality gate still requires a renderer alignment derived from the source image/camera "
            "or model output alone, not from GT pointcloud geometry."
        ),
    }
    write_json(args.output_root / "render_manifest.json", payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "prediction_root": str(prediction_root), "sheet": str(sheet_path)}, indent=2))
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
