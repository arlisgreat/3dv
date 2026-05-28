#!/usr/bin/env python3
"""Render G81 RI3D Gaussian arms into NeRSemble held-out cameras."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np

from render_lam_gaussian_nersemble_source_aligned import load_lam_gaussian_ply  # type: ignore
from render_lam_mesh_nersemble_source_aligned import read_mask  # type: ignore
from render_lam_native_gaussian_nersemble_source_aligned import optimize_source_alignment_with_eval_frustum_guard  # type: ignore
from render_nersemble_pointcloud_heldout import load_json, make_sheet, sha256_file, write_json, write_rgba, zbuffer_points  # type: ignore


DATE = "2026-05-28"
GATE = "G88"
PASS_VERDICT = "PASS_G81_RI3D_GAUSSIAN_NERSEMBLE_HELDOUT_RENDER_READY"
BLOCKED_VERDICT = "BLOCKED_G81_RI3D_GAUSSIAN_NERSEMBLE_HELDOUT_RENDER"
DEFAULT_ARMS = {
    "naive_pseudo_view_supervision": "g81_naive_pseudo_source_anchor",
    "identity_confidence_aware_pseudo_view_supervision": "g81_identity_confidence_aware_source_anchor",
}


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G88 G81 RI3D Gaussian NeRSemble Held-Out Render",
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
        "Arms:",
        "",
        "| arm | variant | source IoU | mean eval coverage | prediction root |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for arm in payload["arms"]:
        lines.append(
            f"| {arm['arm']} | {arm['variant']} | {arm['alignment']['source_mask_iou']:.6f} | "
            f"{arm['mean_eval_coverage']:.6f} | {arm['prediction_root']} |"
        )
    lines.extend(
        [
            "",
            "Renderer contract:",
            "",
            "```text",
            payload["renderer_contract"],
            "```",
            "",
            "Missing requirements:",
            "",
            "```text",
            "\n".join(payload["missing_requirements"]) or "none",
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


def transform_points_h(xyz: np.ndarray, transform: np.ndarray) -> np.ndarray:
    points_h = np.concatenate([xyz, np.ones((len(xyz), 1), dtype=np.float32)], axis=1)
    return (transform.astype(np.float32) @ points_h.T).T[:, :3].astype(np.float32)


def source_frame_c2w(scene_root: Path) -> np.ndarray:
    transforms = load_json(scene_root / "transforms.json")
    frames = transforms["frames"]
    source = next((frame for frame in frames if int(frame.get("view_index", 0)) == -1), frames[0])
    return np.asarray(source["transform_matrix"], dtype=np.float32)


def sign_flip_candidates() -> list[tuple[str, np.ndarray]]:
    rows: list[tuple[str, np.ndarray]] = []
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            for sz in (1.0, -1.0):
                name = f"sign_{int(sx)}_{int(sy)}_{int(sz)}"
                mat = np.eye(4, dtype=np.float32)
                mat[0, 0] = sx
                mat[1, 1] = sy
                mat[2, 2] = sz
                rows.append((name, mat))
    return rows


def prealign_to_nersemble_source(
    xyz: np.ndarray,
    ri3d_source_c2w: np.ndarray,
    nersemble_source_c2w: np.ndarray,
    axis_transform: np.ndarray,
) -> np.ndarray:
    transform = nersemble_source_c2w.astype(np.float32) @ axis_transform.astype(np.float32) @ np.linalg.inv(ri3d_source_c2w.astype(np.float32))
    return transform_points_h(xyz, transform)


def choose_alignment(
    xyz: np.ndarray,
    source_intrinsic: np.ndarray,
    source_w2c: np.ndarray,
    source_mask: np.ndarray,
    eval_cameras: list[dict[str, Any]],
    ri3d_source_c2w: np.ndarray,
    nersemble_source_c2w: np.ndarray,
    radius: int,
    subsample: int,
    seed: int,
    margin_fraction: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    if len(xyz) > subsample:
        align_idx = rng.choice(len(xyz), size=subsample, replace=False)
        xyz_for_score = xyz[align_idx]
    else:
        xyz_for_score = xyz
    candidates: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    best_full_xyz: np.ndarray | None = None
    for name, axis_transform in sign_flip_candidates():
        prealigned_score_xyz = prealign_to_nersemble_source(xyz_for_score, ri3d_source_c2w, nersemble_source_c2w, axis_transform)
        scale, translation, trace, frustum = optimize_source_alignment_with_eval_frustum_guard(
            prealigned_score_xyz,
            source_intrinsic,
            source_w2c,
            source_mask,
            eval_cameras,
            radius,
            seed,
            min(len(prealigned_score_xyz), subsample),
            margin_fraction,
        )
        row = {
            "axis_transform": name,
            "scale": float(scale),
            "translation": translation.astype(float).tolist(),
            "source_mask_iou": float(trace[-1]["source_mask_iou"]),
            "score": float(trace[-1]["score"]),
            "mean_eval_inframe_fraction": frustum["mean_eval_inframe_fraction"],
            "min_eval_inframe_fraction": frustum["min_eval_inframe_fraction"],
            "trace": trace,
            "frustum_guard": frustum,
        }
        candidates.append({key: value for key, value in row.items() if key != "trace"})
        if best is None or (row["source_mask_iou"], row["min_eval_inframe_fraction"], row["score"]) > (
            best["source_mask_iou"],
            best["min_eval_inframe_fraction"],
            best["score"],
        ):
            best = row
            best_full_xyz = prealign_to_nersemble_source(xyz, ri3d_source_c2w, nersemble_source_c2w, axis_transform)
    if best is None or best_full_xyz is None:
        raise RuntimeError("no alignment candidates produced")
    aligned = best_full_xyz * float(best["scale"]) + np.asarray(best["translation"], dtype=np.float32)[None, :]
    best["candidate_summary"] = candidates
    best["alignment_policy"] = "ri3d_source_camera_to_nersemble_source_camera_plus_sign_flip_search_then_source_mask_and_eval_camera_frustum_guard"
    best["uses_heldout_rgb_or_mask_for_alignment"] = False
    best["uses_heldout_camera_geometry_for_frustum_guard"] = True
    best["alignment_subsample"] = int(min(len(xyz), subsample))
    return aligned, best


def render_arm(
    *,
    repo: Path,
    adapter: dict[str, Any],
    calibration: dict[str, Any],
    arm: str,
    variant: str,
    sample_id: str,
    scene_root: Path,
    ri3d_run_root: Path,
    output_root: Path,
    iteration: int,
    color_mode: str,
    splat_radius: int,
    optimize_radius: int,
    alignment_subsample: int,
    seed: int,
    frustum_guard_margin: float,
) -> dict[str, Any]:
    view_count = len(load_json(scene_root / "transforms.json")["frames"])
    tag = f"{sample_id}_{variant}_{view_count}v"
    gaussian = ri3d_run_root / "output" / "gs_init" / tag / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply"
    if not gaussian.exists():
        raise FileNotFoundError(gaussian)
    xyz, rgb, gaussian_meta = load_lam_gaussian_ply(gaussian, color_mode)
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]
    views_by_serial = {row["serial"]: row for row in adapter["views"]}
    source_view = views_by_serial[source_serial]
    source_mask = read_mask(Path(source_view["mask_path"]))
    source_intrinsic = np.asarray(calibration["intrinsics"][source_serial], dtype=np.float32)
    source_w2c = np.asarray(calibration["world_2_cam"][source_serial], dtype=np.float32)
    ner_source_c2w = np.linalg.inv(source_w2c.astype(np.float32))
    ri3d_c2w = source_frame_c2w(scene_root)
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
    aligned_xyz, alignment = choose_alignment(
        xyz,
        source_intrinsic,
        source_w2c,
        source_mask,
        eval_cameras,
        ri3d_c2w,
        ner_source_c2w,
        optimize_radius,
        alignment_subsample,
        seed,
        frustum_guard_margin,
    )

    arm_root = output_root / variant
    prediction_root = arm_root / "predictions"
    all_root = arm_root / "all_rendered_frames"
    prediction_root.mkdir(parents=True, exist_ok=True)
    all_root.mkdir(parents=True, exist_ok=True)
    serials = [source_serial] + [serial for serial in eval_serials if serial != source_serial]
    renders: list[dict[str, Any]] = []
    for serial in serials:
        view = views_by_serial[serial]
        width = int(view["image_width"])
        height = int(view["image_height"])
        intrinsic = np.asarray(calibration["intrinsics"][serial], dtype=np.float32)
        world_to_camera = np.asarray(calibration["world_2_cam"][serial], dtype=np.float32)
        image, alpha, stats = zbuffer_points(aligned_xyz, rgb, intrinsic, world_to_camera, width, height, splat_radius)
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

    sheet_path = arm_root / "g88_private_ri3d_gaussian_nersemble_sheet.png"
    make_sheet(renders, sheet_path)
    eval_coverages = [float(row["stats"]["coverage"]) for row in renders if row["role"] == "heldout_prediction"]
    payload = {
        "arm": arm,
        "variant": variant,
        "sample_id": sample_id,
        "scene_root": str(scene_root),
        "ri3d_training_root": str(ri3d_run_root),
        "gaussian": gaussian_meta,
        "iteration": iteration,
        "color_mode": color_mode,
        "splat_radius": splat_radius,
        "alignment": alignment,
        "prediction_root": str(prediction_root),
        "renders": renders,
        "mean_eval_coverage": float(np.mean(eval_coverages)) if eval_coverages else 0.0,
        "private_outputs": {
            "contact_sheet": str(sheet_path),
            "contact_sheet_sha256": sha256_file(sheet_path),
        },
    }
    write_json(arm_root / "render_manifest.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"))
    parser.add_argument("--ri3d-scene-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g86_g81_nersemble_pseudo_ri3d_pool/ri3d_scenes"))
    parser.add_argument("--ri3d-run-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g87_g81_ri3d_two_arm_iter80"))
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g88_g81_ri3d_nersemble_heldout_iter80"))
    parser.add_argument("--sample-id", default="source220700191")
    parser.add_argument("--iteration", type=int, default=80)
    parser.add_argument("--color-mode", choices=["direct", "sh_dc"], default="sh_dc")
    parser.add_argument("--splat-radius", type=int, default=3)
    parser.add_argument("--optimize-radius", type=int, default=10)
    parser.add_argument("--alignment-subsample", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=60528)
    parser.add_argument("--frustum-guard-margin", type=float, default=0.03)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g88_g81_ri3d_nersemble_heldout_render_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g88_g81_ri3d_nersemble_heldout_render_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    calibration = load_json(Path(adapter["calibration_path"]))
    arms: list[dict[str, Any]] = []
    missing: list[str] = []
    for arm, variant in DEFAULT_ARMS.items():
        scene_root = args.ri3d_scene_root / variant / args.sample_id
        try:
            arms.append(
                render_arm(
                    repo=repo,
                    adapter=adapter,
                    calibration=calibration,
                    arm=arm,
                    variant=variant,
                    sample_id=args.sample_id,
                    scene_root=scene_root,
                    ri3d_run_root=args.ri3d_run_root,
                    output_root=args.output_root,
                    iteration=args.iteration,
                    color_mode=args.color_mode,
                    splat_radius=args.splat_radius,
                    optimize_radius=args.optimize_radius,
                    alignment_subsample=args.alignment_subsample,
                    seed=args.seed,
                    frustum_guard_margin=args.frustum_guard_margin,
                )
            )
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{arm}: {exc}")
    for arm in arms:
        if arm["alignment"]["source_mask_iou"] < 0.10:
            missing.append(f"{arm['arm']}: weak source alignment IoU {arm['alignment']['source_mask_iou']:.6f}")
        if arm["mean_eval_coverage"] <= 0.001:
            missing.append(f"{arm['arm']}: near-empty held-out renders")
    verdict = PASS_VERDICT if not missing else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "verdict": verdict,
        "premise": (
            "Render RI3D Gaussian reconstructions trained from G81 pseudo-supervision arms into the exact NeRSemble source and local held-out K/R/T cameras. "
            "Alignment uses source RGB alpha/mask and held-out camera metadata as a frustum guard, but never held-out RGB/masks."
        ),
        "case": adapter["case"],
        "split": adapter["split"],
        "renderer_contract": "3DGS PLY point approximation rendered by z-buffer splats into official NeRSemble intrinsics/world_2_cam; this is a diagnostic renderer, not the RI3D differentiable Gaussian rasterizer.",
        "arms": arms,
        "missing_requirements": missing,
        "artifact_policy": "Identifiable renders/contact sheets stay under 3dv_work; commit metrics/hashes only unless reviewed.",
        "decision": (
            "Both G81 RI3D arms produced held-out camera prediction PNGs for G55 evaluation."
            if verdict == PASS_VERDICT
            else "Blocked: one or both RI3D arms failed the held-out render readiness checks."
        ),
        "next_gate": "Run G55 evaluator for naive and identity/confidence-aware prediction roots, then rerun G84 three-arm contract.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "missing": missing, "prediction_roots": {arm["arm"]: arm["prediction_root"] for arm in arms}}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
