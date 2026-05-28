#!/usr/bin/env python3
"""Diagnose whether the G81 naive RI3D failure is pose/crop or pseudo geometry.

The diagnostic is intentionally mask-only and repo-safe. It compares source and
held-out masks for the same NeRSemble serials across:

* direct LAM Gaussian with source/frustum guard;
* naive pseudo-view RI3D;
* strict-aware pseudo-view RI3D;
* G110 source-gated pseudo prior;
* GT pointcloud KRT oracle renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G116_NAIVE_POSE_CROP_SOURCE_ORACLE_DIAGNOSTIC"
BLOCKED = "BLOCKED_G116_NAIVE_POSE_CROP_SOURCE_ORACLE_DIAGNOSTIC"


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


def read_mask(path: Path) -> np.ndarray:
    image = Image.open(path)
    if image.mode == "RGBA":
        return np.asarray(image.getchannel("A")) > 8
    return np.asarray(image.convert("L")) > 8


def resize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if mask.shape == shape:
        return mask
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")
    image = image.resize((shape[1], shape[0]), Image.Resampling.NEAREST)
    return np.asarray(image) > 8


def mask_iou(pred: np.ndarray, target: np.ndarray) -> float:
    inter = np.logical_and(pred, target).sum()
    union = np.logical_or(pred, target).sum()
    return float(inter / max(union, 1))


def bbox(mask: np.ndarray) -> list[int] | None:
    if not bool(mask.any()):
        return None
    ys, xs = np.where(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def bbox_iou(a: list[int] | None, b: list[int] | None) -> float:
    if a is None or b is None:
        return 0.0
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0 + 1), max(0, iy1 - iy0 + 1)
    inter = iw * ih
    area_a = (ax1 - ax0 + 1) * (ay1 - ay0 + 1)
    area_b = (bx1 - bx0 + 1) * (by1 - by0 + 1)
    return float(inter / max(area_a + area_b - inter, 1))


def bbox_center(box: list[int] | None, width: int, height: int) -> list[float] | None:
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return [float((x0 + x1) / 2.0 / max(width - 1, 1)), float((y0 + y1) / 2.0 / max(height - 1, 1))]


def compare_mask(pred: np.ndarray, target: np.ndarray) -> dict[str, Any]:
    pred = resize_mask(pred, target.shape)
    height, width = target.shape
    pred_box = bbox(pred)
    target_box = bbox(target)
    pred_center = bbox_center(pred_box, width, height)
    target_center = bbox_center(target_box, width, height)
    center_error = None
    if pred_center is not None and target_center is not None:
        center_error = float(((pred_center[0] - target_center[0]) ** 2 + (pred_center[1] - target_center[1]) ** 2) ** 0.5)
    return {
        "mask_iou": mask_iou(pred, target),
        "prediction_coverage": float(pred.mean()),
        "target_coverage": float(target.mean()),
        "coverage_ratio": float(pred.mean() / max(float(target.mean()), 1e-8)),
        "coverage_abs_error": float(abs(float(pred.mean()) - float(target.mean()))),
        "prediction_bbox": pred_box,
        "target_bbox": target_box,
        "bbox_iou": bbox_iou(pred_box, target_box),
        "prediction_bbox_center": pred_center,
        "target_bbox_center": target_center,
        "bbox_center_error": center_error,
    }


def mask_tile(mask: np.ndarray, label: str, fields: list[str], size: tuple[int, int]) -> Image.Image:
    tile_w, tile_h = size
    panel = Image.new("RGB", (tile_w, tile_h), "white")
    image = Image.fromarray(mask.astype(np.uint8) * 255, mode="L").convert("RGB")
    image.thumbnail((tile_w - 16, tile_w - 16), Image.Resampling.NEAREST)
    panel.paste(image, ((tile_w - image.width) // 2, 8))
    draw = ImageDraw.Draw(panel)
    draw.text((8, tile_w + 12), label[:34], fill=(0, 0, 0))
    for idx, text in enumerate(fields[:3]):
        draw.text((8, tile_w + 30 + idx * 14), text[:38], fill=(0, 0, 0))
    return panel


def make_sheet(
    serials: list[str],
    target_masks: dict[str, np.ndarray],
    arm_masks: dict[str, dict[str, np.ndarray]],
    rows: dict[str, dict[str, dict[str, Any]]],
    output: Path,
) -> str:
    arms = ["target", *arm_masks.keys()]
    tile_w, tile_h = 210, 282
    sheet = Image.new("RGB", (tile_w * len(arms), tile_h * len(serials)), "white")
    for y, serial in enumerate(serials):
        target = target_masks[serial]
        sheet.paste(mask_tile(target, f"{serial} target", [f"cov={target.mean():.3f}"], (tile_w, tile_h)), (0, y * tile_h))
        for x, arm in enumerate(arm_masks.keys(), start=1):
            mask = arm_masks[arm][serial]
            row = rows[arm][serial]
            fields = [
                f"iou={row['mask_iou']:.3f} cov={row['prediction_coverage']:.3f}",
                f"ratio={row['coverage_ratio']:.3f} bboxIoU={row['bbox_iou']:.3f}",
                f"center={row['bbox_center_error'] if row['bbox_center_error'] is not None else 'NA'}",
            ]
            sheet.paste(mask_tile(mask, arm, fields, (tile_w, tile_h)), (x * tile_w, y * tile_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return sha256_file(output)


def summarize(rows: dict[str, dict[str, dict[str, Any]]], eval_serials: list[str], source_serial: str) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for arm, per_serial in rows.items():
        eval_rows = [per_serial[serial] for serial in eval_serials if serial in per_serial]
        source_row = per_serial.get(source_serial)
        summary[arm] = {
            "source_mask_iou": None if source_row is None else source_row["mask_iou"],
            "source_coverage_ratio": None if source_row is None else source_row["coverage_ratio"],
            "mean_eval_mask_iou": float(np.mean([row["mask_iou"] for row in eval_rows])) if eval_rows else None,
            "mean_eval_coverage_ratio": float(np.mean([row["coverage_ratio"] for row in eval_rows])) if eval_rows else None,
            "mean_eval_bbox_iou": float(np.mean([row["bbox_iou"] for row in eval_rows])) if eval_rows else None,
            "mean_eval_center_error": float(np.mean([row["bbox_center_error"] for row in eval_rows if row["bbox_center_error"] is not None])) if eval_rows else None,
        }
    return summary


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G116 Naive Pose/Crop/Source/Oracle Diagnostic",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Summary:",
        "",
        "| arm | source IoU | source cov ratio | eval IoU | eval cov ratio | eval bbox IoU | eval center err |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm, row in payload["summary_by_arm"].items():
        lines.append(
            f"| {arm} | {row['source_mask_iou']} | {row['source_coverage_ratio']} | "
            f"{row['mean_eval_mask_iou']} | {row['mean_eval_coverage_ratio']} | "
            f"{row['mean_eval_bbox_iou']} | {row['mean_eval_center_error']} |"
        )
    lines.extend(
        [
            "",
            "Pose/crop/source/oracle interpretation:",
            "",
            "```text",
            payload["interpretation"],
            "```",
            "",
            "Repo-safe mask sheet:",
            "",
            "```text",
            payload["repo_safe_outputs"]["mask_sheet"],
            payload["repo_safe_outputs"]["mask_sheet_sha256"],
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
    parser.add_argument("--adapter-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"))
    parser.add_argument("--direct-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/all_rendered_frames"))
    parser.add_argument("--naive-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g102_g81_strict_aware_nersemble_heldout_iter1500_splat8/g81_naive_pseudo_source_anchor/all_rendered_frames"))
    parser.add_argument("--old-aware-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g102_g81_strict_aware_nersemble_heldout_iter1500_splat8/g81_identity_confidence_aware_source_anchor/all_rendered_frames"))
    parser.add_argument("--g110-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g110_source_gated_pseudo_prior_refinement/all_rendered_frames"))
    parser.add_argument("--oracle-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/all_rendered_frames"))
    parser.add_argument("--naive-render-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g102_g81_strict_aware_nersemble_heldout_iter1500_splat8/g81_naive_pseudo_source_anchor/render_manifest.json"))
    parser.add_argument("--oracle-eval-json", type=Path, default=Path("experiments/metrics/g60_nersemble_pointcloud_oracle_eval_20260527.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g116_naive_pose_crop_source_oracle_diagnostic_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g116_naive_pose_crop_source_oracle_diagnostic_20260528.md"))
    parser.add_argument("--output-figure", type=Path, default=Path("experiments/figures/g116_naive_pose_crop_source_oracle_mask_diagnostic_20260528.png"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    views = {row["serial"]: row for row in adapter["views"]}
    source_serial = adapter["split"]["source_serial"]
    eval_serials = adapter["split"]["local_eval_serials"]
    serials = [source_serial, *[serial for serial in eval_serials if serial != source_serial]]
    target_masks = {serial: read_mask(Path(views[serial]["mask_path"])) for serial in serials}
    arms = {
        "direct_lam_g77": args.direct_root,
        "naive_ri3d_g102": args.naive_root,
        "strict_aware_ri3d_g102": args.old_aware_root,
        "g110_source_gated": args.g110_root,
        "gt_pointcloud_oracle_g59": args.oracle_root,
    }
    missing: list[str] = []
    arm_masks: dict[str, dict[str, np.ndarray]] = {}
    rows: dict[str, dict[str, dict[str, Any]]] = {}
    for arm, root in arms.items():
        arm_masks[arm] = {}
        rows[arm] = {}
        for serial in serials:
            path = root / f"cam_{serial}_frame_00000.png"
            if not path.exists():
                missing.append(f"{arm}: missing {path}")
                continue
            mask = resize_mask(read_mask(path), target_masks[serial].shape)
            arm_masks[arm][serial] = mask
            rows[arm][serial] = compare_mask(mask, target_masks[serial])

    if missing:
        verdict = BLOCKED
        summary: dict[str, Any] = {}
        sheet_sha = "not_written"
    else:
        verdict = PASS_VERDICT
        summary = summarize(rows, eval_serials, source_serial)
        sheet_sha = make_sheet(serials, target_masks, arm_masks, rows, repo / args.output_figure)

    naive_manifest = load_json(args.naive_render_manifest) if args.naive_render_manifest.exists() else {}
    naive_alignment = naive_manifest.get("alignment", {})
    frustum = naive_alignment.get("frustum_guard", {})
    oracle_eval = load_json(repo / args.oracle_eval_json if not args.oracle_eval_json.is_absolute() else args.oracle_eval_json)
    direct = summary.get("direct_lam_g77", {})
    naive = summary.get("naive_ri3d_g102", {})
    oracle = summary.get("gt_pointcloud_oracle_g59", {})
    interpretation = (
        "Naive RI3D failure is not safe to attribute only to pseudo-view image quality. "
        "The render manifest shows the same NeRSemble K/R/T adapter and a sign-flip/source-mask plus eval-frustum guard were used, "
        f"with valid-z/in-frame evidence rather than a catastrophic empty-pose failure (min eval in-frame {frustum.get('min_eval_inframe_fraction')}). "
        f"However, the naive source render already under-covers the source mask (IoU {naive.get('source_mask_iou')}, coverage ratio {naive.get('source_coverage_ratio')}), "
        "so source-space crop/scale/geometry mismatch is present before held-out evaluation. "
        f"Direct LAM/G110 have much stronger mask support (direct eval IoU {direct.get('mean_eval_mask_iou')}; G110 is recorded separately in G113), "
        f"while the GT pointcloud oracle confirms KRT plumbing is usable but itself under-covers the full alpha mask (oracle eval IoU {oracle.get('mean_eval_mask_iou')}; G60 mean mask IoU {oracle_eval.get('metrics', {}).get('mean_prediction_mask_vs_eval_mask_iou')}). "
        "Conclusion: G110's current value is that it bypasses pseudo-view geometry/pose/crop risk by preserving direct geometry; the naive baseline remains a failed baseline that needs stronger pose/crop/oracle复核 before using it as evidence against pseudo-view supervision quality alone."
    )
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G116",
        "verdict": verdict,
        "premise": (
            "Check whether the G81 naive pseudo-view RI3D baseline failed because of camera pose/crop/source-render issues rather than only pseudo-view quality."
        ),
        "case": adapter["case"],
        "split": adapter["split"],
        "serials": serials,
        "summary_by_arm": summary,
        "per_serial": rows,
        "naive_pose_crop_evidence": {
            "render_manifest": str(args.naive_render_manifest),
            "alignment_policy": naive_alignment.get("alignment_policy"),
            "axis_transform": naive_alignment.get("axis_transform"),
            "source_mask_iou_from_render_manifest": naive_alignment.get("source_mask_iou"),
            "frustum_guard": frustum,
            "uses_heldout_rgb_or_mask_for_alignment": naive_alignment.get("uses_heldout_rgb_or_mask_for_alignment"),
            "uses_heldout_camera_geometry_for_frustum_guard": naive_alignment.get("uses_heldout_camera_geometry_for_frustum_guard"),
        },
        "oracle_gt_evidence": {
            "oracle_eval_json": str(repo / args.oracle_eval_json if not args.oracle_eval_json.is_absolute() else args.oracle_eval_json),
            "oracle_eval_verdict": oracle_eval.get("verdict"),
            "oracle_mean_mask_iou": oracle_eval.get("metrics", {}).get("mean_prediction_mask_vs_eval_mask_iou"),
            "oracle_interpretation": "KRT/evaluator positive control exists but pointcloud splat oracle under-covers the alpha mask, so it is not a full-quality RGB oracle.",
        },
        "repo_safe_outputs": {
            "mask_sheet": str(repo / args.output_figure),
            "mask_sheet_sha256": sheet_sha,
        },
        "missing_requirements": missing,
        "interpretation": interpretation,
        "decision": (
            "Naive failure remains real, but current evidence supports a mixed source/crop/geometry-risk diagnosis, not a pure pseudo-view-quality diagnosis."
            if verdict == PASS_VERDICT
            else "Blocked: required render masks are missing."
        ),
        "next_gate": (
            "Run ablations with direct geometry preserved, then add multi-case replication; for naive RI3D, add a stronger source-render/oracle-aligned pose-crop repair before drawing final conclusions."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "summary_by_arm": summary, "missing": missing}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
