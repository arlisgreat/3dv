#!/usr/bin/env python3
"""Render LAM predictions into the audited G54 NeRSemble cameras."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_silent_wav(path: Path, seconds: float = 1.0, rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(seconds * rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * n_frames)


def load_lam_internal_sample_c2w(sample_transforms: Path) -> np.ndarray:
    data = load_json(sample_transforms)
    frame = data["frames"][0]
    c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
    c2w[:3, 1:3] *= -1.0
    return c2w


def camera_to_world(world_to_camera: list[list[float]]) -> np.ndarray:
    return np.linalg.inv(np.asarray(world_to_camera, dtype=np.float32))


def build_c2w(
    calibration: dict[str, Any],
    serial: str,
    source_serial: str,
    mode: str,
    sample_source_c2w: np.ndarray,
) -> np.ndarray:
    c2w = camera_to_world(calibration["world_2_cam"][serial])
    if mode == "raw":
        return c2w
    if mode == "source_to_lam_sample":
        source_c2w = camera_to_world(calibration["world_2_cam"][source_serial])
        transform = sample_source_c2w @ np.linalg.inv(source_c2w)
        return transform @ c2w
    raise ValueError(f"unknown camera mode: {mode}")


def transform_for_lam_json(internal_c2w: np.ndarray) -> list[list[float]]:
    # LAM's head_utils._load_pose flips columns 1:3 after reading transform_matrix.
    stored = internal_c2w.copy()
    stored[:3, 1:3] *= -1.0
    return stored.astype(float).tolist()


def write_neutral_flame(path: Path, shape_dim: int = 300, expr_dim: int = 100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        translation=np.zeros((1, 3), dtype=np.float32),
        rotation=np.zeros((1, 3), dtype=np.float32),
        neck_pose=np.zeros((1, 3), dtype=np.float32),
        jaw_pose=np.zeros((1, 3), dtype=np.float32),
        eyes_pose=np.zeros((1, 6), dtype=np.float32),
        shape=np.zeros((shape_dim,), dtype=np.float32),
        expr=np.zeros((1, expr_dim), dtype=np.float32),
        static_offset=np.zeros((1, 5143, 3), dtype=np.float32),
        allow_pickle=np.asarray(True),
    )


def make_motion_sequence(
    repo: Path,
    adapter_manifest: dict[str, Any],
    output_root: Path,
    camera_mode: str,
    serials: list[str],
) -> Path:
    participant = adapter_manifest["case"]["participant"]
    calibration_path = repo / "datasets/nersemble_benchmark/nvs" / participant / "calibration/camera_params.json"
    calibration = load_json(calibration_path)
    source_serial = adapter_manifest["split"]["source_serial"]
    source_view = next(row for row in adapter_manifest["views"] if row["serial"] == source_serial)
    width = int(source_view["image_width"])
    height = int(source_view["image_height"])
    sample_source_c2w = load_lam_internal_sample_c2w(repo / "external/LAM/assets/sample_motion/export/Anti_Drugs/transforms.json")

    motion_root = output_root / "motion_sequence"
    export_dir = motion_root / "NeRSembleG54"
    export_dir.mkdir(parents=True, exist_ok=True)
    write_silent_wav(export_dir / "NeRSembleG54.wav")

    frames: list[dict[str, Any]] = []
    for index, serial in enumerate(serials):
        flame_rel = f"flame_param/{index:05d}.npz"
        write_neutral_flame(motion_root / flame_rel)
        k = np.asarray(calibration["intrinsics"][serial], dtype=np.float32)
        # prepare_motion_seqs halves intrinsics, so write doubled values here.
        fl_x = float(k[0, 0] * 2.0)
        fl_y = float(k[1, 1] * 2.0)
        # Use exact target dimensions as principal-point anchors after halving.
        cx = float(width)
        cy = float(height)
        c2w = build_c2w(calibration, serial, source_serial, camera_mode, sample_source_c2w)
        frames.append(
            {
                "timestep_index": index,
                "timestep_index_original": index,
                "timestep_id": f"{index:08d}",
                "camera_index": index,
                "camera_id": serial,
                "cx": cx,
                "cy": cy,
                "fl_x": fl_x,
                "fl_y": fl_y,
                "h": height,
                "w": width,
                "camera_angle_x": float(2.0 * np.arctan(width / (2.0 * k[0, 0]))),
                "camera_angle_y": float(2.0 * np.arctan(height / (2.0 * k[1, 1]))),
                "transform_matrix": transform_for_lam_json(c2w),
                "file_path": f"images/{index:05d}_{serial}.png",
                "fg_mask_path": f"fg_masks/{index:05d}_{serial}.png",
                "flame_param_path": flame_rel,
            }
        )
    transforms = {
        "frames": frames,
        "cx": float(width),
        "cy": float(height),
        "fl_x": float(frames[0]["fl_x"]),
        "fl_y": float(frames[0]["fl_y"]),
        "h": height,
        "w": width,
        "camera_angle_x": frames[0]["camera_angle_x"],
        "camera_angle_y": frames[0]["camera_angle_y"],
        "timestep_indices": list(range(len(frames))),
        "camera_indices": list(range(len(frames))),
    }
    write_json(motion_root / "transforms.json", transforms)
    np.savez(motion_root / "canonical_flame_param.npz", shape=np.zeros((300,), dtype=np.float32))
    return export_dir


def run_lam(repo: Path, source_image: Path, motion_dir: Path, log_path: Path, args: argparse.Namespace) -> int:
    lam_dir = repo / "external/LAM"
    conda = "/data1/workspace/airulan/conda/miniconda3/etc/profile.d/conda.sh"
    command = f"""
set -euo pipefail
source /data1/workspace/airulan/env124.sh
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${{LD_LIBRARY_PATH#"$CUDA_HOME/lib64"}}"
export PATH=/data1/workspace/airulan/conda/miniconda3/bin:$PATH
source {conda}
conda activate lam
export CACHE_ROOT="{repo}/.cache"
export HF_HOME="$CACHE_ROOT/huggingface"
export TORCH_HOME="$CACHE_ROOT/torch"
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
export PYTHONPATH="{lam_dir}:${{PYTHONPATH:-}}"
cd "{lam_dir}"
CUDA_VISIBLE_DEVICES="{args.cuda_visible_devices}" python -m lam.launch infer.lam --config "{args.config}" \\
  model_name="{args.model}" \\
  image_input="{source_image}" \\
  export_video=true \\
  export_mesh=false \\
  motion_seqs_dir="{motion_dir}" \\
  motion_img_dir=null \\
  vis_motion=false \\
  motion_img_need_mask=false \\
  render_fps=1 \\
  motion_video_read_fps=1 \\
  save_ply=false \\
  save_img=true \\
  gaga_track_type="" \\
  cross_id=false \\
  test_sample=false \\
  rank=0 \\
  nodes=0
"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["bash", "-lc", command], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log_path.write_text(proc.stdout, encoding="utf-8")
    return proc.returncode


def find_lam_image_dir(repo: Path, source_stem: str) -> Path:
    root = repo / "external/LAM/exps/images/lam/lam_20k"
    candidates = [path for path in root.rglob(source_stem) if path.is_dir()]
    if not candidates:
        candidates = [path for path in root.rglob("*") if path.is_dir() and list(path.glob("*.png"))]
    if not candidates:
        raise FileNotFoundError(f"no LAM image output directory under {root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def make_contact_sheet(rows: list[dict[str, Any]], output: Path) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    tile_w, tile_h = 240, 280
    sheet = Image.new("RGB", (tile_w * len(rows), tile_h), "white")
    for index, row in enumerate(rows):
        image = Image.open(row["path"]).convert("RGB")
        image.thumbnail((220, 220), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (tile_w, tile_h), "white")
        tile.paste(image, ((tile_w - image.width) // 2, 10))
        draw = ImageDraw.Draw(tile)
        draw.text((10, 235), f"{row['serial']} {row['role']}", fill=(0, 0, 0))
        sheet.paste(tile, (tile_w * index, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json"))
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g57_nersemble_lam_camera_render"))
    parser.add_argument("--prediction-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g56_nersemble_lam_eval/predictions"))
    parser.add_argument("--camera-mode", choices=["source_to_lam_sample", "raw"], default="source_to_lam_sample")
    parser.add_argument("--config", default="configs/inference/lam-20k-8gpu.yaml")
    parser.add_argument("--model", default="model_zoo/lam_models/releases/lam/lam-20k/step_045500/")
    parser.add_argument("--cuda-visible-devices", default="0")
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]
    serials = [source_serial] + [serial for serial in eval_serials if serial != source_serial]
    source_view = next(row for row in adapter["views"] if row["serial"] == source_serial)
    source_image = Path(source_view["rgb_path"])

    motion_dir = make_motion_sequence(repo, adapter, args.output_root, args.camera_mode, serials)
    log_path = args.output_root / "lam_render.log"
    returncode = run_lam(repo, source_image, motion_dir, log_path, args)
    if returncode != 0:
        metadata = {
            "status": "failed",
            "returncode": returncode,
            "log": str(log_path),
            "motion_dir": str(motion_dir),
            "camera_mode": args.camera_mode,
        }
        write_json(args.output_root / "render_manifest.json", metadata)
        raise SystemExit(returncode)

    lam_image_dir = find_lam_image_dir(repo, source_image.stem)
    pngs = sorted(lam_image_dir.glob("*.png"))
    if len(pngs) < len(serials):
        raise RuntimeError(f"LAM output has {len(pngs)} pngs, expected at least {len(serials)} in {lam_image_dir}")

    args.prediction_root.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    all_frames_root = args.output_root / "all_rendered_frames"
    all_frames_root.mkdir(parents=True, exist_ok=True)
    for index, serial in enumerate(serials):
        role = "source_render" if serial == source_serial else "heldout_prediction"
        src = pngs[index]
        dst_all = all_frames_root / f"cam_{serial}_frame_00000.png"
        shutil.copy2(src, dst_all)
        row = {
            "serial": serial,
            "role": role,
            "source_lam_png": str(src),
            "path": str(dst_all),
            "sha256": sha256_file(dst_all),
        }
        if serial in eval_serials:
            dst_pred = args.prediction_root / f"cam_{serial}_frame_00000.png"
            shutil.copy2(src, dst_pred)
            row["prediction_path"] = str(dst_pred)
            row["prediction_sha256"] = sha256_file(dst_pred)
        copied.append(row)

    sheet_path = args.output_root / "g57_private_lam_nersemble_render_sheet.png"
    make_contact_sheet(copied, sheet_path)
    metadata = {
        "status": "success",
        "method": "LAM-20K",
        "camera_mode": args.camera_mode,
        "source_image": str(source_image),
        "source_serial": source_serial,
        "eval_serials": eval_serials,
        "motion_dir": str(motion_dir),
        "lam_image_dir": str(lam_image_dir),
        "prediction_root": str(args.prediction_root),
        "copied_frames": copied,
        "private_contact_sheet": str(sheet_path),
        "private_contact_sheet_sha256": sha256_file(sheet_path),
        "log": str(log_path),
        "artifact_policy": "Identifiable source/prediction RGB stays under 3dv_work; commit only metrics/hashes unless explicitly reviewed.",
    }
    write_json(args.output_root / "render_manifest.json", metadata)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
