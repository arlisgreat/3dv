#!/usr/bin/env python3
"""Audit a GT/positive-control case before reconstruction conversion."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


RAW_MESH_SUFFIXES = {".glb", ".gltf", ".obj", ".ply", ".stl", ".wrl", ".x3d"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def image_stats(path: Path) -> dict[str, Any]:
    image = Image.open(path)
    arr = np.array(image)
    stats: dict[str, Any] = {
        "path": str(path),
        "mode": image.mode,
        "width": image.width,
        "height": image.height,
    }
    if arr.ndim == 2:
        stats["nonzero_ratio"] = float((arr > 0).mean())
    else:
        stats["non_background_ratio"] = float((np.abs(arr.astype(np.int16) - 244).sum(axis=2) > 12).mean())
    return stats


def mp4_stats(path: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"path": str(path), "opened": False, "frame_count": 0, "width": 0, "height": 0}
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return {"path": str(path), "opened": True, "frame_count": frame_count, "width": width, "height": height}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, data: dict[str, Any]) -> None:
    lines = [
        f"# {data['case_id']} G17 Provenance Sanity Gate",
        "",
        "Date: 2026-05-20",
        "",
        "Gate verdict:",
        "",
        "```text",
        data["verdict"],
        data["scope"],
        "```",
        "",
        "Checks:",
        "",
        "```text",
        f"manifest_rows: {data['manifest_rows']}",
        f"camera_records: {data['camera_records']}",
        f"missing_files: {len(data['missing_files'])}",
        f"bad_dimensions: {len(data['bad_dimensions'])}",
        f"low_mask_coverage: {len(data['low_mask_coverage'])}",
        f"raw_mesh_files_inside_case: {len(data['raw_mesh_files_inside_case'])}",
        f"mp4_opened: {data['mp4']['opened']}",
        f"mp4_frames: {data['mp4']['frame_count']}",
        "```",
        "",
        "Artifacts:",
        "",
        "```text",
        str(data["case_root"]),
        str(data["manifest_csv"]),
        str(data["camera_json"]),
        str(data["orbit_mp4"]),
        "```",
        "",
        "Interpretation:",
        "",
        "```text",
        data["interpretation"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="wikimedia_blender_head_cc0")
    parser.add_argument("--case-root", type=Path, default=Path("experiments/gt_cases/wikimedia_blender_head_cc0"))
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.md"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.json"),
    )
    parser.add_argument("--expected-views", type=int, default=8)
    parser.add_argument("--expected-size", type=int, default=512)
    parser.add_argument("--min-mask-coverage", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_root = args.case_root
    manifest_csv = case_root / "manifest.csv"
    camera_json = case_root / "cameras.json"
    orbit_mp4 = case_root / "orbit_rgb.mp4"

    rows = read_csv(manifest_csv)
    cameras = load_json(camera_json)
    missing: list[str] = []
    bad_dimensions: list[dict[str, Any]] = []
    low_mask_coverage: list[dict[str, Any]] = []
    image_records: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_id") != args.case_id:
            missing.append(f"unexpected case_id in row {row.get('view_id')}: {row.get('case_id')}")
        for key in ("rgb", "depth", "mask", "normal"):
            path = Path(row[key])
            if not path.exists():
                missing.append(str(path))
                continue
            stats = image_stats(path)
            stats["view_id"] = row.get("view_id")
            stats["kind"] = key
            image_records.append(stats)
            if stats["width"] != args.expected_size or stats["height"] != args.expected_size:
                bad_dimensions.append(stats)
            if key == "mask" and float(stats.get("nonzero_ratio", 0.0)) < args.min_mask_coverage:
                low_mask_coverage.append(stats)

    raw_mesh_files = [
        str(path)
        for path in case_root.rglob("*")
        if path.is_file() and path.suffix.lower() in RAW_MESH_SUFFIXES
    ]
    mp4 = mp4_stats(orbit_mp4)
    camera_records = len(cameras.get("cameras", []))
    problems = (
        len(rows) != args.expected_views
        or camera_records != args.expected_views
        or missing
        or bad_dimensions
        or low_mask_coverage
        or raw_mesh_files
        or not mp4["opened"]
        or mp4["frame_count"] <= 0
    )
    verdict = "BLOCKED" if problems else "PASS_G17_PROVENANCE_SANITY"
    scope = "POSITIVE_CONTROL_ONLY"
    interpretation = (
        "The positive-control case is structurally ready for G17 conversion and no-training "
        "camera sanity checks. This does not authorize real-capture claims."
        if not problems
        else "Fix the blocked provenance issues before G17 conversion or reconstruction."
    )
    result = {
        "case_id": args.case_id,
        "date": "2026-05-20",
        "verdict": verdict,
        "scope": scope,
        "case_root": str(case_root),
        "manifest_csv": str(manifest_csv),
        "camera_json": str(camera_json),
        "orbit_mp4": str(orbit_mp4),
        "manifest_rows": len(rows),
        "camera_records": camera_records,
        "missing_files": missing,
        "bad_dimensions": bad_dimensions,
        "low_mask_coverage": low_mask_coverage,
        "raw_mesh_files_inside_case": raw_mesh_files,
        "mp4": mp4,
        "image_records": image_records,
        "interpretation": interpretation,
    }
    write_json(args.output_json, result)
    write_md(args.output_md, result)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Verdict: {verdict}")


if __name__ == "__main__":
    main()
