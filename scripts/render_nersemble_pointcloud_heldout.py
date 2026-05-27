#!/usr/bin/env python3
"""Render the G54 NeRSemble GT pointcloud into visible held-out cameras."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
from PIL import Image, ImageDraw  # type: ignore


DATE = "2026-05-27"
GATE = "G59"
PASS_VERDICT = "PASS_NERSEMBLE_TRUE_KRT_POINTCLOUD_RENDERER_POSITIVE_CONTROL"
BLOCKED_VERDICT = "BLOCKED_NERSEMBLE_TRUE_KRT_POINTCLOUD_RENDERER"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_pcd_binary(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    raw = path.read_bytes()
    marker = b"DATA binary\n"
    data_offset = raw.find(marker)
    if data_offset < 0:
        raise RuntimeError(f"{path} is not a binary PCD with DATA binary")
    data_offset += len(marker)
    header_text = raw[:data_offset].decode("utf-8", errors="replace")
    header: dict[str, Any] = {"path": str(path), "header": header_text.splitlines()}
    for line in header["header"]:
        if " " in line:
            key, value = line.split(" ", 1)
            header[key.lower()] = value
    point_count = int(header.get("points", header.get("width", "0")))
    dtype = np.dtype(
        [
            ("x", "<f4"),
            ("y", "<f4"),
            ("z", "<f4"),
            ("normal_x", "<f4"),
            ("normal_y", "<f4"),
            ("normal_z", "<f4"),
            ("rgb", "<f4"),
        ]
    )
    cloud = np.frombuffer(raw, dtype=dtype, count=point_count, offset=data_offset)
    xyz = np.stack([cloud["x"], cloud["y"], cloud["z"]], axis=1).astype(np.float32)
    packed = cloud["rgb"].copy().view("<u4")
    rgb = np.stack(
        [
            ((packed >> 16) & 255),
            ((packed >> 8) & 255),
            (packed & 255),
        ],
        axis=1,
    ).astype(np.uint8)
    header["loaded_points"] = int(len(xyz))
    return xyz, rgb, header


def zbuffer_points(
    xyz: np.ndarray,
    rgb: np.ndarray,
    intrinsic: np.ndarray,
    world_to_camera: np.ndarray,
    width: int,
    height: int,
    splat_radius: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    ones = np.ones((xyz.shape[0], 1), dtype=np.float32)
    xyz_h = np.concatenate([xyz, ones], axis=1)
    camera = (world_to_camera.astype(np.float32) @ xyz_h.T).T[:, :3]
    z = camera[:, 2]
    valid_z = z > 1e-6
    x = camera[:, 0]
    y = camera[:, 1]
    u = intrinsic[0, 0] * (x / z) + intrinsic[0, 2]
    v = intrinsic[1, 1] * (y / z) + intrinsic[1, 2]
    u_i = np.rint(u).astype(np.int32)
    v_i = np.rint(v).astype(np.int32)
    in_frame = valid_z & (u_i >= 0) & (u_i < width) & (v_i >= 0) & (v_i < height)
    if not np.any(in_frame):
        image = np.full((height, width, 3), 255, dtype=np.uint8)
        alpha = np.zeros((height, width), dtype=np.uint8)
        return image, alpha, {"projected_points": 0, "coverage": 0.0, "z_min": None, "z_max": None}

    u_i = u_i[in_frame]
    v_i = v_i[in_frame]
    z = z[in_frame]
    rgb = rgb[in_frame]
    if splat_radius > 0:
        offsets = [(du, dv) for dv in range(-splat_radius, splat_radius + 1) for du in range(-splat_radius, splat_radius + 1)]
        us, vs, zs, rgbs = [], [], [], []
        for du, dv in offsets:
            uu = u_i + du
            vv = v_i + dv
            ok = (uu >= 0) & (uu < width) & (vv >= 0) & (vv < height)
            if np.any(ok):
                us.append(uu[ok])
                vs.append(vv[ok])
                zs.append(z[ok])
                rgbs.append(rgb[ok])
        u_i = np.concatenate(us)
        v_i = np.concatenate(vs)
        z = np.concatenate(zs)
        rgb = np.concatenate(rgbs)

    linear = v_i.astype(np.int64) * width + u_i.astype(np.int64)
    order = np.lexsort((z, linear))
    linear_sorted = linear[order]
    first = np.unique(linear_sorted, return_index=True)[1]
    chosen = order[first]
    image = np.full((height * width, 3), 255, dtype=np.uint8)
    alpha = np.zeros((height * width,), dtype=np.uint8)
    image[linear[chosen]] = rgb[chosen]
    alpha[linear[chosen]] = 255
    image = image.reshape(height, width, 3)
    alpha = alpha.reshape(height, width)
    stats = {
        "projected_points": int(np.count_nonzero(in_frame)),
        "rasterized_pixels": int(np.count_nonzero(alpha)),
        "coverage": float(np.count_nonzero(alpha) / alpha.size),
        "z_min": float(np.min(z)),
        "z_max": float(np.max(z)),
    }
    return image, alpha, stats


def write_rgba(path: Path, rgb: np.ndarray, alpha: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgba = np.dstack([rgb, alpha])
    cv2.imwrite(str(path), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))


def make_sheet(rows: list[dict[str, Any]], output: Path) -> None:
    tile_w, tile_h = 260, 250
    cols = 3
    sheet = Image.new("RGB", (cols * tile_w, len(rows) * tile_h), "white")
    for row_i, row in enumerate(rows):
        items = [
            ("GT RGB", Path(row["target_rgb_path"])),
            ("GT mask", Path(row["target_mask_path"])),
            ("PCD render", Path(row["render_path"])),
        ]
        for col, (label, path) in enumerate(items):
            tile = Image.new("RGB", (tile_w, tile_h), "white")
            image = Image.open(path).convert("RGB")
            image.thumbnail((tile_w - 20, tile_h - 45), Image.Resampling.LANCZOS)
            tile.paste(image, ((tile_w - image.width) // 2, 8))
            draw = ImageDraw.Draw(tile)
            draw.text((8, tile_h - 32), f"{row['serial']} {label}", fill=(0, 0, 0))
            sheet.paste(tile, (col * tile_w, row_i * tile_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G59 NeRSemble True-KRT Pointcloud Renderer Positive Control",
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
        "Render summary:",
        "",
        "| serial | role | projected points | coverage | output |",
        "| --- | --- | ---: | ---: | --- |",
    ]
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
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer"))
    parser.add_argument("--splat-radius", type=int, default=2)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g59_nersemble_pointcloud_true_krt_renderer_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g59_nersemble_pointcloud_true_krt_renderer_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    xyz, rgb, pcd_header = read_pcd_binary(Path(adapter["pointcloud"]["path"]))
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
        image, alpha, stats = zbuffer_points(xyz, rgb, intrinsic, world_to_camera, width, height, args.splat_radius)
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

    sheet_path = args.output_root / "g59_private_pointcloud_true_krt_sheet.png"
    make_sheet(renders, sheet_path)
    passed = all(row["stats"]["projected_points"] > 1000 and row["stats"]["coverage"] > 0.01 for row in renders)
    verdict = PASS_VERDICT if passed else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "Render the official NeRSemble frame-0 GT pointcloud through the exact G54 visible-camera K/R/T. "
            "This is an oracle renderer positive control for camera/evaluator plumbing, not a learned-prior method result."
        ),
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "pointcloud": {
            "path": adapter["pointcloud"]["path"],
            "loaded_points": pcd_header["loaded_points"],
            "header_points": pcd_header.get("points"),
        },
        "camera_contract": "official_nersemble_world_2_cam_and_intrinsics",
        "prediction_root": str(prediction_root),
        "renders": renders,
        "private_outputs": {
            "contact_sheet": str(sheet_path),
            "contact_sheet_sha256": sha256_file(sheet_path),
        },
        "artifact_policy": "Identifiable GT RGB and pointcloud renders stay under 3dv_work; commit repo-safe metrics/hashes unless user reviews redistribution.",
        "decision": (
            "The true K/R/T pointcloud renderer produced nonempty source/eval renders and can be used as the camera-contract positive control."
            if passed
            else "Blocked: pointcloud projection produced empty or near-empty renders, so the camera convention is still unresolved."
        ),
        "next_gate": (
            "Run the G55 evaluator on these pointcloud renders as an oracle local-visible held-out baseline, then connect method mesh/Gaussian output "
            "to this same camera contract without using GT geometry for method alignment unless explicitly labeled diagnostic."
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
