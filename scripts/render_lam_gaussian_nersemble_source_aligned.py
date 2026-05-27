#!/usr/bin/env python3
"""Render LAM Gaussian PLY into NeRSemble cameras after source-mask alignment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from render_lam_mesh_nersemble_source_aligned import optimize_source_alignment, read_mask  # type: ignore
from render_nersemble_pointcloud_heldout import (  # type: ignore
    load_json,
    make_sheet,
    sha256_file,
    write_json,
    write_rgba,
    zbuffer_points,
)


DATE = "2026-05-27"
GATE = "G67"
PASS_VERDICT = "PASS_LAM_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC"
BLOCKED_VERDICT = "BLOCKED_LAM_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNMENT"


def load_lam_gaussian_ply(path: Path, color_mode: str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
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
    if count <= 0 or not properties:
        raise RuntimeError(f"{path} has no readable vertex properties")
    dtype = np.dtype([(name, "<f4") for name in properties])
    payload = np.frombuffer(raw, dtype=dtype, count=count, offset=data_offset)
    xyz = np.stack([payload["x"], payload["y"], payload["z"]], axis=1).astype(np.float32)
    dc = np.stack([payload["f_dc_0"], payload["f_dc_1"], payload["f_dc_2"]], axis=1).astype(np.float32)
    if color_mode == "sh_dc":
        colors = dc * 0.28209479177387814 + 0.5
    else:
        colors = dc
    rgb = np.clip(colors * 255.0, 0, 255).astype(np.uint8)
    opacity = payload["opacity"] if "opacity" in payload.dtype.names else np.ones((len(xyz),), dtype=np.float32)
    keep = np.isfinite(xyz).all(axis=1) & np.isfinite(rgb).all(axis=1) & (opacity > -8.0)
    metadata = {
        "path": str(path),
        "vertex_count": int(count),
        "loaded_points": int(np.count_nonzero(keep)),
        "properties": properties,
        "color_mode": color_mode,
        "opacity_min": float(np.min(opacity)),
        "opacity_mean": float(np.mean(opacity)),
        "opacity_max": float(np.max(opacity)),
    }
    return xyz[keep], rgb[keep], metadata


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} LAM Gaussian Source-Aligned True-KRT Render",
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
            f"| gaussian_points | {payload['gaussian']['loaded_points']} |",
            f"| splat_radius | {payload['splat_radius']} |",
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
    parser.add_argument("--gaussian", type=Path, default=Path("external/LAM/exps/cano_gs/cam_222200042_frame_00000_gs_offset.ply"))
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g67_lam_gaussian_true_krt_source_aligned"))
    parser.add_argument("--color-mode", choices=["direct", "sh_dc"], default="direct")
    parser.add_argument("--optimize-radius", type=int, default=12)
    parser.add_argument("--splat-radius", type=int, default=10)
    parser.add_argument("--gate", default=GATE)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g67_lam_gaussian_source_aligned_render_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g67_lam_gaussian_source_aligned_render_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    gaussian_path = args.gaussian if args.gaussian.is_absolute() else repo / args.gaussian
    xyz, rgb, gaussian_meta = load_lam_gaussian_ply(gaussian_path, args.color_mode)

    source_serial = adapter["split"]["source_serial"]
    source_view = next(row for row in adapter["views"] if row["serial"] == source_serial)
    source_mask = read_mask(Path(source_view["mask_path"]))
    source_intrinsic = np.asarray(calibration["intrinsics"][source_serial], dtype=np.float32)
    source_w2c = np.asarray(calibration["world_2_cam"][source_serial], dtype=np.float32)
    scale, translation, trace = optimize_source_alignment(
        xyz,
        source_intrinsic,
        source_w2c,
        source_mask,
        args.optimize_radius,
    )
    aligned_xyz = xyz * scale + translation[None, :]

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
        image, alpha, stats = zbuffer_points(aligned_xyz, rgb, intrinsic, world_to_camera, width, height, args.splat_radius)
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

    sheet_path = args.output_root / "g67_private_lam_gaussian_source_aligned_sheet.png"
    make_sheet(renders, sheet_path)
    source_iou = trace[-1]["source_mask_iou"]
    passed = source_iou >= 0.45 and all(row["stats"]["projected_points"] > 1000 for row in renders)
    verdict = PASS_VERDICT if passed else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": (
            "Align the LAM head-anchored Gaussian PLY to the G54 NeRSemble source view using only source camera and alpha mask, "
            "then render the same Gaussian points into held-out cameras with official NeRSemble K/R/T."
        ),
        "verdict": verdict,
        "method": "LAM-20K Gaussian PLY point approximation",
        "camera_mode": "nersemble_krt",
        "camera_contract_verified": True,
        "case": adapter["case"],
        "split": adapter["split"],
        "gaussian": gaussian_meta,
        "splat_radius": args.splat_radius,
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
            "The Gaussian PLY route produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before any method claim."
            if passed
            else "Blocked: source-only Gaussian alignment did not produce usable true-camera renders."
        ),
        "next_gate": "Run G55 held-out evaluator and visual/mask/appearance gate on these Gaussian predictions.",
    }
    write_json(args.output_root / "render_manifest.json", payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "source_mask_iou": source_iou, "prediction_root": str(prediction_root), "sheet": str(sheet_path)}, indent=2))
    if verdict == BLOCKED_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
