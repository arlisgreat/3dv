#!/usr/bin/env python3
"""Prepare a local-only NeRSemble NVS frame-0 adapter preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
GATE = "G54"
PASS_VERDICT = "PASS_NERSEMBLE_NVS_FRAME0_ADAPTER_PREFLIGHT_LOCAL_ONLY"
BLOCKED = "BLOCKED_NERSEMBLE_NVS_FRAME0_ADAPTER_PREFLIGHT"

NVS_HIDDEN_HOLDOUT_SERIALS = ["222200046", "222200037", "222200039"]
DEFAULT_LOCAL_EVAL_SERIALS = ["220700191", "222200041", "222200047"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_pcd_header(path: Path) -> dict[str, Any]:
    header: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return header
    lines: list[str] = []
    with path.open("rb") as handle:
        for raw in handle:
            line = raw.decode("utf-8", errors="replace").strip()
            lines.append(line)
            if line.startswith("DATA "):
                break
    for line in lines:
        if " " not in line:
            continue
        key, value = line.split(" ", 1)
        header[key.lower()] = value
    header["header_lines"] = lines
    return header


def extract_frame(video: Path, timestep: int) -> tuple[Any, dict[str, Any]]:
    import cv2  # type: ignore

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"could not open {video}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    target = min(max(timestep, 0), max(frame_count - 1, 0))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"could not read frame {target} from {video}")
    return frame, {"frame_count": frame_count, "width": width, "height": height, "frame_index": target}


def make_mask_sheet(rows: list[dict[str, Any]], output: Path) -> str:
    from PIL import Image, ImageDraw  # type: ignore

    tile_w, tile_h = 220, 250
    cols = 4
    rows_n = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows_n * tile_h), "white")
    for index, row in enumerate(rows):
        mask = Image.open(row["mask_path"]).convert("L")
        mask.thumbnail((190, 190), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (tile_w, tile_h), "white")
        tile.paste(Image.merge("RGB", (mask, mask, mask)), ((tile_w - mask.width) // 2, 10))
        draw = ImageDraw.Draw(tile)
        label = row["serial"]
        if row["role"] == "source_single_image":
            label += " source"
        elif row["role"] == "local_heldout_eval":
            label += " eval"
        draw.text((10, 210), label, fill=(0, 0, 0))
        draw.text((10, 228), f"alpha={row['alpha_coverage']:.3f}", fill=(0, 0, 0))
        sheet.paste(tile, ((index % cols) * tile_w, (index // cols) * tile_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return sha256_file(output)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G54 NeRSemble NVS Frame-0 Adapter Preflight",
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
        "Case:",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| participant | {payload['case']['participant']} |",
        f"| sequence | {payload['case']['sequence']} |",
        f"| timestep | {payload['case']['timestep']} |",
        f"| source_serial | {payload['split']['source_serial']} |",
        f"| local_eval_serials | {', '.join(payload['split']['local_eval_serials'])} |",
        f"| official_hidden_holdout_serials | {', '.join(payload['split']['official_hidden_holdout_serials'])} |",
        "",
        "Adapter summary:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| local_views_written | {len(payload['views'])} |",
        f"| calibration_serials | {payload['calibration']['serial_count']} |",
        f"| pointcloud_points | {payload['pointcloud'].get('points', 'unknown')} |",
        f"| min_alpha_coverage | {payload['checks']['min_alpha_coverage']:.6f} |",
        f"| max_alpha_coverage | {payload['checks']['max_alpha_coverage']:.6f} |",
        f"| mask_sheet_sha256 | {payload['repo_safe_outputs']['mask_sheet_sha256']} |",
        "",
        "Repo-safe mask audit figure:",
        "",
        "```text",
        payload["repo_safe_outputs"]["mask_sheet"],
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--benchmark-root", type=Path, default=Path("datasets/nersemble_benchmark/nvs"))
    parser.add_argument("--participant", type=int, default=388)
    parser.add_argument("--sequence", default="GLASSES")
    parser.add_argument("--timestep", type=int, default=0)
    parser.add_argument("--source-serial", default="222200042")
    parser.add_argument("--local-eval-serials", nargs="+", default=DEFAULT_LOCAL_EVAL_SERIALS)
    parser.add_argument("--output-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g54_nersemble_nvs_frame0_adapter_preflight_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g54_nersemble_nvs_frame0_adapter_preflight_20260527.md"))
    parser.add_argument("--output-figure", type=Path, default=Path("experiments/figures/g54_nersemble_nvs_frame0_mask_audit_20260527.png"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    root = (repo / args.benchmark_root).resolve() if not args.benchmark_root.is_absolute() else args.benchmark_root
    case_root = root / f"{args.participant:03d}"
    seq_root = case_root / "sequences" / args.sequence
    calib_path = case_root / "calibration" / "camera_params.json"
    pointcloud_path = seq_root / "pointclouds" / f"frame_{args.timestep:05d}.pcd"
    output_root = args.output_root
    rgb_root = output_root / "rgb"
    alpha_root = output_root / "alpha"
    mask_root = output_root / "masks"
    for item in (rgb_root, alpha_root, mask_root):
        item.mkdir(parents=True, exist_ok=True)

    import cv2  # type: ignore

    calibration = load_json(calib_path)
    available_serials = sorted(
        path.stem.split("_", 1)[1]
        for path in (seq_root / "images").glob("cam_*.mp4")
    )
    requested = [args.source_serial] + [serial for serial in args.local_eval_serials if serial != args.source_serial]
    remaining = [serial for serial in available_serials if serial not in requested]
    serials = requested + remaining

    views: list[dict[str, Any]] = []
    for serial in serials:
        image_video = seq_root / "images" / f"cam_{serial}.mp4"
        alpha_video = seq_root / "alpha_maps" / f"cam_{serial}.mp4"
        image_frame, image_meta = extract_frame(image_video, args.timestep)
        alpha_frame, alpha_meta = extract_frame(alpha_video, args.timestep)
        alpha_gray = alpha_frame[:, :, 0]
        mask = (alpha_gray > 8).astype("uint8") * 255
        rgb_path = rgb_root / f"cam_{serial}_frame_{args.timestep:05d}.png"
        alpha_path = alpha_root / f"cam_{serial}_frame_{args.timestep:05d}_alpha.png"
        mask_path = mask_root / f"cam_{serial}_frame_{args.timestep:05d}_mask.png"
        cv2.imwrite(str(rgb_path), image_frame)
        cv2.imwrite(str(alpha_path), alpha_gray)
        cv2.imwrite(str(mask_path), mask)
        role = "source_single_image" if serial == args.source_serial else (
            "local_heldout_eval" if serial in args.local_eval_serials else "visible_context_not_for_first_smoke"
        )
        views.append(
            {
                "serial": serial,
                "role": role,
                "rgb_path": str(rgb_path),
                "alpha_path": str(alpha_path),
                "mask_path": str(mask_path),
                "image_width": image_meta["width"],
                "image_height": image_meta["height"],
                "image_frame_count": image_meta["frame_count"],
                "alpha_frame_count": alpha_meta["frame_count"],
                "frame_index": image_meta["frame_index"],
                "alpha_coverage": float((mask > 0).mean()),
                "rgb_sha256": sha256_file(rgb_path),
                "alpha_sha256": sha256_file(alpha_path),
                "mask_sha256": sha256_file(mask_path),
                "has_calibration": serial in calibration.get("world_2_cam", {}) and serial in calibration.get("intrinsics", {}),
            }
        )

    mask_sheet_sha = make_mask_sheet(views, repo / args.output_figure)
    pointcloud = read_pcd_header(pointcloud_path)
    source_ok = any(row["serial"] == args.source_serial and row["role"] == "source_single_image" for row in views)
    eval_ok = all(any(row["serial"] == serial and row["role"] == "local_heldout_eval" for row in views) for serial in args.local_eval_serials)
    calibration_ok = all(row["has_calibration"] for row in views)
    alpha_coverages = [row["alpha_coverage"] for row in views]
    checks = {
        "source_serial_present": source_ok,
        "local_eval_serials_present": eval_ok,
        "all_views_have_calibration": calibration_ok,
        "pointcloud_exists": pointcloud_path.exists(),
        "all_views_same_resolution": len({(row["image_width"], row["image_height"]) for row in views}) == 1,
        "all_image_alpha_frame_counts_match": all(row["image_frame_count"] == row["alpha_frame_count"] for row in views),
        "min_alpha_coverage": min(alpha_coverages) if alpha_coverages else 0.0,
        "max_alpha_coverage": max(alpha_coverages) if alpha_coverages else 0.0,
    }
    passed = (
        source_ok
        and eval_ok
        and calibration_ok
        and checks["pointcloud_exists"]
        and checks["all_views_same_resolution"]
        and checks["all_image_alpha_frame_counts_match"]
        and checks["min_alpha_coverage"] > 0.01
    )
    verdict = PASS_VERDICT if passed else BLOCKED

    local_manifest = {
        "case": {
            "dataset": "NeRSemble benchmark NVS",
            "participant": f"{args.participant:03d}",
            "sequence": args.sequence,
            "timestep": args.timestep,
        },
        "split": {
            "source_serial": args.source_serial,
            "local_eval_serials": args.local_eval_serials,
            "official_hidden_holdout_serials": NVS_HIDDEN_HOLDOUT_SERIALS,
            "visible_serials": available_serials,
        },
        "views": views,
        "pointcloud": pointcloud,
        "calibration_path": str(calib_path),
        "artifact_policy": "local-only RGB/alpha/mask adapter under 3dv_work; commit metrics and mask-only figure only.",
    }
    write_json(output_root / "adapter_manifest.json", local_manifest)

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "Build the smallest real NeRSemble NVS local adapter from official benchmark data: one frame with "
            "real RGB, alpha maps, cameras, and a pointcloud. This preflight validates data plumbing only; "
            "official leaderboard hold-out cameras remain hidden."
        ),
        "verdict": verdict,
        "case": local_manifest["case"],
        "split": local_manifest["split"],
        "local_adapter_root": str(output_root),
        "views": [
            {
                "serial": row["serial"],
                "role": row["role"],
                "image_width": row["image_width"],
                "image_height": row["image_height"],
                "image_frame_count": row["image_frame_count"],
                "alpha_coverage": row["alpha_coverage"],
                "rgb_sha256": row["rgb_sha256"],
                "alpha_sha256": row["alpha_sha256"],
                "mask_sha256": row["mask_sha256"],
                "has_calibration": row["has_calibration"],
            }
            for row in views
        ],
        "pointcloud": pointcloud,
        "calibration": {
            "path": str(calib_path),
            "serial_count": len(calibration.get("world_2_cam", {})),
            "intrinsics_count": len(calibration.get("intrinsics", {})),
        },
        "checks": checks,
        "repo_safe_outputs": {
            "mask_sheet": str(repo / args.output_figure),
            "mask_sheet_sha256": mask_sheet_sha,
        },
        "decision": (
            "The official NVS frame-0 adapter is ready for CPU/GPU evaluation harness work. "
            "Do not present metrics as official leaderboard metrics; use visible-camera local held-outs only until submission packaging exists."
            if passed
            else "Blocked: required RGB/alpha/camera/pointcloud/frame consistency checks failed."
        ),
        "next_gate": (
            "G55 should implement a model-agnostic held-out evaluation harness over this adapter: source view in, local eval cameras out, "
            "RGB PSNR/SSIM/LPIPS plus mask IoU/depth or pointcloud sanity where the method output supports it."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote local adapter to {output_root}")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.output_figure}")
    print(verdict)
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
