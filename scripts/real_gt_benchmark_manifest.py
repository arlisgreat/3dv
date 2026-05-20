#!/usr/bin/env python3
"""Build a repo-safe real-GT benchmark audit and manifest.

This script intentionally does not consume experiments/downstream_datasets.
It records only already-audited real-GT routes and local metadata/hash summaries;
raw recognizable RGB, masks, meshes, and contact sheets remain outside the repo.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zlib
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:
    Image = None
    ImageDraw = None
    ImageFont = None


DATE = "2026-05-20"
PASS = "PASS_REAL_GT_BENCHMARK"
BLOCKED_NO_NEW = "BLOCKED_NO_ADDITIONAL_READY_REAL_GT_BENCHMARK"
BLOCKED = "BLOCKED_REAL_GT_BENCHMARK_MANIFEST"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def camera_entries(cameras: Any) -> list[dict[str, Any]]:
    if isinstance(cameras, dict):
        entries = cameras.get("cameras", cameras.get("views", []))
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
    if isinstance(cameras, list):
        return [entry for entry in cameras if isinstance(entry, dict)]
    return []


def has_intrinsics(entry: dict[str, Any]) -> bool:
    return any(key in entry for key in ("K", "intrinsics", "fx", "focal_length", "camera_matrix"))


def has_extrinsics(entry: dict[str, Any]) -> bool:
    return any(key in entry for key in ("extrinsics", "camera_to_world", "world_to_camera")) or (
        any(key in entry for key in ("R", "rotation")) and any(key in entry for key in ("T", "t", "translation"))
    )


def rel_or_abs(repo: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def summarize_multiface_case(repo: Path, case_dir: Path, g21: dict[str, Any]) -> dict[str, Any]:
    rows = read_csv(case_dir / "manifest.csv")
    cameras = load_json(case_dir / "cameras.json", {})
    metadata = load_json(case_dir / "real_gt_case.json", {})
    entries = camera_entries(cameras)
    mesh_path = Path(str(metadata.get("gt_mesh") or rows[0].get("mesh", "") if rows else ""))

    view_rows: list[dict[str, Any]] = []
    for row in rows:
        rgb_path = Path(row.get("rgb", ""))
        mask_path = Path(row.get("mask", ""))
        view_rows.append(
            {
                "camera": row.get("camera"),
                "frame": row.get("frame"),
                "width": int(row.get("width", "0") or 0),
                "height": int(row.get("height", "0") or 0),
                "mask_coverage": float(row.get("mask_coverage", "nan")),
                "projected_faces": int(row.get("projected_faces", "0") or 0),
                "rgb_basename": rgb_path.name,
                "mask_basename": mask_path.name,
                "rgb_sha256": row.get("rgb_sha256") or sha256_file(rgb_path),
                "mask_sha256": row.get("mask_sha256") or sha256_file(mask_path),
                "rgb_exists_local": rgb_path.is_file(),
                "mask_exists_local": mask_path.is_file(),
            }
        )

    checks = {
        "g21_gate_passed": g21.get("verdict") == PASS,
        "manifest_exists": (case_dir / "manifest.csv").is_file(),
        "view_count_6_to_12": 6 <= len(rows) <= 12,
        "rgb_files_exist_local": bool(rows) and all(Path(row.get("rgb", "")).is_file() for row in rows),
        "mask_files_exist_local": bool(rows) and all(Path(row.get("mask", "")).is_file() for row in rows),
        "cameras_json_exists": (case_dir / "cameras.json").is_file(),
        "camera_count_matches_views": len(entries) == len(rows) and bool(rows),
        "camera_intrinsics_present": bool(entries) and all(has_intrinsics(entry) for entry in entries),
        "camera_extrinsics_present": bool(entries) and all(has_extrinsics(entry) for entry in entries),
        "mesh_exists_local": mesh_path.is_file(),
        "real_capture": bool(metadata.get("real_capture")),
        "not_generated_candidate": metadata.get("generated_candidate") is False,
        "same_identity_static": bool(metadata.get("same_identity_static") or metadata.get("same_identity_static_frame")),
        "license_recorded": bool(metadata.get("license") or metadata.get("license_name")),
        "privacy_policy_recorded": bool(metadata.get("privacy_status")),
        "repo_policy_keeps_raw_assets_out": "remain in 3dv_work" in str(metadata.get("artifact_policy", ""))
        or "remain in 3dv_work" in str(metadata.get("repo_policy", "")),
        "downstream_datasets_not_used": True,
    }
    failed = [key for key, ok in checks.items() if not ok]
    coverage = [row["mask_coverage"] for row in view_rows]

    return {
        "dataset": "Multiface",
        "case_id": metadata.get("case_id", case_dir.name),
        "status": PASS if not failed else BLOCKED,
        "role": "current_local_real_gt_route",
        "source_case_dir": str(case_dir),
        "artifact_policy": metadata.get("artifact_policy"),
        "repo_policy": metadata.get("repo_policy"),
        "privacy_status": metadata.get("privacy_status"),
        "license": metadata.get("license_name") or metadata.get("license"),
        "capture_type": metadata.get("capture_type"),
        "frame": metadata.get("frame"),
        "expression": metadata.get("expression"),
        "identity_redacted": True,
        "view_count": len(rows),
        "camera_count": len(entries),
        "mesh_basename": mesh_path.name if str(mesh_path) else None,
        "mesh_sha256": sha256_file(mesh_path),
        "mask_coverage_min": min(coverage) if coverage else None,
        "mask_coverage_mean": mean(coverage) if coverage else None,
        "mask_coverage_max": max(coverage) if coverage else None,
        "checks": checks,
        "failed_checks": failed,
        "views": view_rows,
    }


def summarize_routes(repo: Path, g35: dict[str, Any], facescape: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for item in g35.get("routes", []):
        routes.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "source": item.get("source"),
                "ready_for_manifest": item.get("status") == "current_route_only",
            }
        )
    if facescape:
        routes.append(
            {
                "name": "FaceScape sample local metadata",
                "status": "metadata_access_only",
                "reason": facescape.get("gate_implication"),
                "source": "external/facescape/samples",
                "sample_root": facescape.get("sample_root"),
                "mview_valid_views": facescape.get("mview_valid_views"),
                "mview_available_images": len(facescape.get("mview_available_images", [])),
                "ready_for_manifest": False,
                "blocker": "sample readme says do not distribute; full licensed case required",
            }
        )
    return routes


def choose_font(size: int) -> Any:
    if ImageFont is None:
        return None
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_summary_png(path: Path, case: dict[str, Any], verdict: str) -> None:
    if Image is None:
        make_summary_png_fallback(path, case, verdict)
        return
    width, height = 1120, 560
    img = Image.new("RGB", (width, height), (248, 248, 246))
    draw = ImageDraw.Draw(img)
    title = choose_font(24)
    font = choose_font(16)
    small = choose_font(13)
    draw.text((32, 24), "Real-GT Benchmark Manifest Audit", fill=(20, 20, 20), font=title)
    draw.text((32, 62), f"Date: {DATE}    Verdict: {verdict}", fill=(75, 45, 20), font=font)
    draw.text((32, 96), "No RGB, masks, mesh, or downstream_datasets candidate media are embedded in this artifact.", fill=(110, 50, 50), font=small)

    checks = case.get("checks", {})
    items = [
        ("G21 gate", checks.get("g21_gate_passed")),
        ("6-12 real views", checks.get("view_count_6_to_12")),
        ("RGB local only", checks.get("rgb_files_exist_local")),
        ("Masks local only", checks.get("mask_files_exist_local")),
        ("Cameras", checks.get("camera_count_matches_views") and checks.get("camera_intrinsics_present") and checks.get("camera_extrinsics_present")),
        ("GT mesh local only", checks.get("mesh_exists_local")),
        ("Real capture", checks.get("real_capture")),
        ("Not pseudo views", checks.get("not_generated_candidate") and checks.get("downstream_datasets_not_used")),
        ("License/policy", checks.get("license_recorded") and checks.get("privacy_policy_recorded") and checks.get("repo_policy_keeps_raw_assets_out")),
    ]
    x0, y0 = 32, 150
    for idx, (label, ok) in enumerate(items):
        x = x0 + (idx % 3) * 350
        y = y0 + (idx // 3) * 72
        color = (38, 128, 78) if ok else (170, 65, 50)
        draw.rectangle((x, y, x + 24, y + 24), fill=color)
        draw.text((x + 36, y + 2), f"{label}: {'PASS' if ok else 'FAIL'}", fill=(25, 25, 25), font=font)

    draw.text((32, 395), f"Case: {case.get('dataset')} / {case.get('case_id')}", fill=(25, 25, 25), font=font)
    draw.text((32, 425), f"Views: {case.get('view_count')}    Cameras: {case.get('camera_count')}    Mesh hash recorded: {bool(case.get('mesh_sha256'))}", fill=(25, 25, 25), font=font)
    draw.text((32, 455), f"Mask coverage min/mean/max: {case.get('mask_coverage_min'):.3f} / {case.get('mask_coverage_mean'):.3f} / {case.get('mask_coverage_max'):.3f}", fill=(25, 25, 25), font=font)
    draw.text((32, 495), "Use this manifest to authorize only local real-GT benchmark/eval plumbing, not pseudo-view training.", fill=(95, 45, 45), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def make_summary_png_fallback(path: Path, case: dict[str, Any], verdict: str) -> None:
    """Write a simple standards-compliant PNG when Pillow is unavailable."""
    width, height = 960, 360
    bg = (248, 248, 246)
    pixels = bytearray()
    checks = list(case.get("checks", {}).items())
    failed = set(case.get("failed_checks", []))
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            color = bg
            if 24 <= x < width - 24 and 24 <= y < 72:
                color = (48, 72, 92) if "PASS_CURRENT" in verdict else (120, 68, 55)
            elif 24 <= x < width - 24 and 96 <= y < 310:
                idx = (x - 24) // 104
                band_y = (y - 96) // 54
                check_idx = band_y * 8 + idx
                if 0 <= check_idx < len(checks):
                    key, ok = checks[check_idx]
                    color = (44, 132, 86) if ok and key not in failed else (174, 70, 54)
                    if (x - 24) % 104 > 92 or (y - 96) % 54 > 42:
                        color = bg
            elif 24 <= x < width - 24 and 326 <= y < 342:
                color = (92, 92, 92)
            row.extend(color)
        pixels.extend(row)
    raw = bytes(pixels)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"tEXt", b"Title\x00Real-GT benchmark manifest audit; green=pass, red=fail; no RGB/mask/mesh media embedded")
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_manifest_csv(path: Path, case: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dataset",
        "case_id",
        "camera",
        "frame",
        "width",
        "height",
        "mask_coverage",
        "projected_faces",
        "rgb_basename",
        "mask_basename",
        "rgb_sha256",
        "mask_sha256",
        "role",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in case.get("views", []):
            writer.writerow(
                {
                    "dataset": case.get("dataset"),
                    "case_id": case.get("case_id"),
                    "role": case.get("role"),
                    **{key: row.get(key) for key in fields if key in row},
                }
            )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    case = payload["benchmark_cases"][0]
    lines = [
        "# Real-GT Benchmark Manifest Audit",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Scope:",
        "",
        "```text",
        payload["scope"],
        "```",
        "",
        "Current usable case:",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| dataset | {case['dataset']} |",
        f"| case_id | {case['case_id']} |",
        f"| status | {case['status']} |",
        f"| views | {case['view_count']} |",
        f"| cameras | {case['camera_count']} |",
        f"| license | {case['license']} |",
        f"| raw artifact policy | {case['artifact_policy']} |",
        "",
        "Gate checks:",
        "",
        "| check | status |",
        "| --- | --- |",
    ]
    for key, ok in case["checks"].items():
        lines.append(f"| {key} | {'PASS' if ok else 'FAIL'} |")
    lines.extend(
        [
            "",
            "Other routes:",
            "",
            "| route | status | ready | reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for route in payload["route_audit"]:
        reason = str(route.get("reason") or route.get("blocker") or "").replace("\n", " ")
        lines.append(f"| {route.get('name')} | {route.get('status')} | {route.get('ready_for_manifest')} | {reason} |")
    lines.extend(
        [
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
            "",
            "Artifacts:",
            "",
            "```text",
            "\n".join(payload["artifacts"]),
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--case-dir", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view/gate_case"))
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/real_gt_benchmark"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    out_dir = repo / args.output_dir
    g21 = load_json(repo / "experiments/metrics/g21_multiface_debug_gate_20260520.json", {})
    g35 = load_json(repo / "experiments/metrics/g35_public_benchmark_availability_20260520.json", {})
    facescape = load_json(repo / "experiments/metrics/facescape_sample_access_audit_20260519.json", {})
    case = summarize_multiface_case(repo, args.case_dir, g21)
    route_audit = summarize_routes(repo, g35, facescape)

    route_verdict = g35.get("verdict") == BLOCKED_NO_NEW
    verdict = "PASS_CURRENT_LOCAL_MANIFEST_BLOCKED_FOR_ADDITIONAL_BENCHMARKS" if case["status"] == PASS and route_verdict else BLOCKED
    payload = {
        "date": DATE,
        "verdict": verdict,
        "scope": (
            "Repo-safe data audit plus benchmark manifest for the current local Multiface real-GT route. "
            "This confirms a current local benchmark exists, while additional public/licensed benchmarks remain blocked. "
            "experiments/downstream_datasets is not read and is not a verified training set."
        ),
        "benchmark_cases": [case],
        "route_audit": route_audit,
        "gates": {
            "current_multiface_case": case["status"],
            "additional_benchmark_availability": g35.get("verdict"),
            "facescape_sample": "PASS_METADATA_ACCESS_ONLY_BLOCKED_REPO_IMAGE_EXPORT" if facescape else "NOT_FOUND",
            "downstream_datasets": "NOT_USED_NOT_VALIDATED_TRAINING_SET",
        },
        "decision": (
            "Use the local Multiface compact case only for auditable real-GT benchmark plumbing and held-out evaluation gates. "
            "Do not claim method quality from this manifest alone, do not train from experiments/downstream_datasets, "
            "and do not treat FaceScape sample metadata or the synthetic CC0 positive control as a ready real-capture benchmark."
        ),
        "artifacts": [
            str(args.output_dir / "benchmark_manifest.json"),
            str(args.output_dir / "benchmark_manifest.csv"),
            str(args.output_dir / "data_audit.json"),
            str(args.output_dir / "data_audit.md"),
            str(args.output_dir / "data_audit_summary.png"),
        ],
    }

    write_json(out_dir / "benchmark_manifest.json", {"date": DATE, "benchmark_cases": [case]})
    write_manifest_csv(out_dir / "benchmark_manifest.csv", case)
    write_json(out_dir / "data_audit.json", payload)
    write_md(out_dir / "data_audit.md", payload)
    make_summary_png(out_dir / "data_audit_summary.png", case, verdict)
    print(f"verdict={verdict}")
    print(f"output_dir={rel_or_abs(repo, out_dir)}")
    for artifact in payload["artifacts"]:
        print(f"artifact={artifact}")


if __name__ == "__main__":
    main()
