#!/usr/bin/env python3
"""Dry-run/check a compact real-GT benchmark case before reconstruction.

The gate is intentionally stricter than the synthetic positive-control gates:
it only emits PASS_REAL_GT_BENCHMARK for licensed real-capture cases with
6-12 RGB views, cameras, masks, GT geometry, distribution notes, and an
explicit visual/manual audit pass.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:  # Keep the structural gate runnable in minimal Python envs.
    Image = None
    ImageDraw = None
    ImageFont = None


DATE = "2026-05-20"
PASS_VERDICT = "PASS_REAL_GT_BENCHMARK"
BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL_ACCESS"
BLOCKED_INCOMPLETE = "BLOCKED_CASE_INCOMPLETE"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def choose_font(size: int) -> Any:
    if ImageFont is None:
        return None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def repo_path(repo: Path, case_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    raw = Path(value)
    if raw.is_absolute():
        return raw
    candidates = [repo / raw, case_dir / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def existing_path_count(repo: Path, case_dir: Path, rows: list[dict[str, str]], keys: tuple[str, ...]) -> int:
    count = 0
    for row in rows:
        for key in keys:
            path = repo_path(repo, case_dir, row.get(key))
            if path and path.is_file():
                count += 1
                break
    return count


def listed_paths(repo: Path, case_dir: Path, rows: list[dict[str, str]], keys: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for row in rows:
        for key in keys:
            path = repo_path(repo, case_dir, row.get(key))
            if path and path.is_file():
                paths.append(path)
                break
    return paths


def load_case_metadata(case_dir: Path, cameras: dict[str, Any]) -> dict[str, Any]:
    for name in ("real_gt_case.json", "case_metadata.json", "source_metadata.json"):
        path = case_dir / name
        if path.is_file():
            data = load_json(path)
            return data if isinstance(data, dict) else {}
    return cameras if isinstance(cameras, dict) else {}


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


def geometry_paths(repo: Path, case_dir: Path, rows: list[dict[str, str]], metadata: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for key in ("mesh", "point_cloud", "geometry", "gt_mesh", "gt_point_cloud"):
        value = metadata.get(key)
        if isinstance(value, str):
            path = repo_path(repo, case_dir, value)
            if path and path.is_file():
                paths.append(path)
    for row in rows:
        for key in ("mesh", "point_cloud", "geometry", "gt_mesh", "gt_point_cloud"):
            path = repo_path(repo, case_dir, row.get(key))
            if path and path.is_file():
                paths.append(path)
    for suffix in ("*.ply", "*.obj", "*.stl", "*.npz"):
        paths.extend(case_dir.glob(suffix))
    return sorted(set(paths))


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}
    return False


def metadata_text(metadata: dict[str, Any], *keys: str) -> str:
    values: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, sort_keys=True))
        else:
            values.append(str(value))
    return " ".join(values).strip()


def check_case(repo: Path, case_dir: Path, visual_verdict: str) -> dict[str, Any]:
    manifest_path = case_dir / "manifest.csv"
    cameras_path = case_dir / "cameras.json"
    rows = read_csv(manifest_path) if manifest_path.is_file() else []
    cameras = load_json(cameras_path) if cameras_path.is_file() else {}
    metadata = load_case_metadata(case_dir, cameras if isinstance(cameras, dict) else {})
    entries = camera_entries(cameras)
    rgb_paths = listed_paths(repo, case_dir, rows, ("rgb", "image", "image_path"))
    mask_paths = listed_paths(repo, case_dir, rows, ("mask", "mask_path"))
    geom_paths = geometry_paths(repo, case_dir, rows, metadata)

    capture_text = metadata_text(metadata, "capture_type", "semantic_type", "gate_scope", "source_dataset")
    synthetic_or_positive = any(token in capture_text.lower() for token in ("synthetic", "positive_control", "rendered"))
    real_capture = truthy(metadata.get("real_capture")) or "real_capture" in capture_text.lower()
    no_generated_views = not any(
        token in capture_text.lower() for token in ("pseudo", "diffusion", "zero123", "generated_candidate")
    )
    same_identity_static = truthy(metadata.get("same_identity_static")) or truthy(metadata.get("same_identity_static_frame"))
    license_text = metadata_text(metadata, "license", "license_name")
    artifact_policy_text = metadata_text(metadata, "redistribution_policy", "repo_policy", "artifact_policy")
    distribution_text = metadata_text(metadata, "distribution_audit", "benchmark_distribution", "distribution_notes")
    privacy_text = metadata_text(metadata, "privacy_status", "subject_privacy", "consent_status")

    checks = {
        "manifest_exists": manifest_path.is_file(),
        "view_count_6_to_12": 6 <= len(rows) <= 12,
        "rgb_images_exist": len(rgb_paths) == len(rows) and bool(rows),
        "cameras_json_exists": cameras_path.is_file(),
        "camera_count_matches_views": len(entries) == len(rows) and bool(rows),
        "camera_intrinsics_present": bool(entries) and all(has_intrinsics(entry) for entry in entries),
        "camera_extrinsics_present": bool(entries) and all(has_extrinsics(entry) for entry in entries),
        "masks_exist": len(mask_paths) == len(rows) and bool(rows),
        "mesh_or_point_cloud_exists": bool(geom_paths),
        "license_recorded": bool(license_text),
        "compact_artifact_policy_recorded": bool(artifact_policy_text)
        and not any(token in artifact_policy_text.lower() for token in ("forbidden", "not allowed", "blocked")),
        "distribution_audit_recorded": bool(distribution_text),
        "privacy_or_subject_policy_recorded": bool(privacy_text),
        "same_identity_static_frame_recorded": same_identity_static,
        "real_capture_not_synthetic": real_capture and not synthetic_or_positive,
        "not_diffusion_or_pseudoview": no_generated_views,
        "visual_audit_sheet_passed": visual_verdict == "PASS",
    }
    failed = [key for key, ok in checks.items() if not ok]
    verdict = PASS_VERDICT if not failed else BLOCKED_INCOMPLETE
    if failed and not checks["real_capture_not_synthetic"]:
        verdict = BLOCKED_EXTERNAL

    return {
        "case_id": case_dir.name,
        "case_dir": str(case_dir),
        "verdict": verdict,
        "view_count": len(rows),
        "rgb_image_count": len(rgb_paths),
        "mask_count": len(mask_paths),
        "camera_count": len(entries),
        "geometry_count": len(geom_paths),
        "visual_verdict": visual_verdict,
        "checks": checks,
        "failed_checks": failed,
        "license_text": license_text,
        "artifact_policy_text": artifact_policy_text,
        "distribution_text": distribution_text,
        "privacy_text": privacy_text,
        "geometry_paths": [str(path) for path in geom_paths],
    }


def svg_href(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base.parent))
    except ValueError:
        return str(path)


def make_svg_audit_sheet(repo: Path, case_dir: Path, rows: list[dict[str, str]], output: Path, title: str) -> None:
    thumb = 104
    pad = 10
    max_cols = max(1, min(12, len(rows)))
    width = pad + max_cols * thumb + (max_cols - 1) * pad + pad
    height = 92 + thumb * 2 + pad * 3
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8f8f8"/>',
        f'<text x="{pad}" y="22" font-family="DejaVu Sans, Arial, sans-serif" font-size="13" fill="#141414">{title}</text>',
        f'<text x="{pad}" y="44" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#464646">Top: RGB views. Bottom: masks. Reviewer checks subject, view, crop, mask, and geometry consistency.</text>',
        f'<text x="{pad}" y="66" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#6e3232">Dry-run sheet is not a PASS unless visual_verdict=PASS and all structural checks pass.</text>',
    ]
    if not rows:
        lines.append(f'<text x="{pad}" y="112" font-family="DejaVu Sans, Arial, sans-serif" font-size="12" fill="#6e3232">No compact real-GT manifest rows available.</text>')
    for idx, row in enumerate(rows[:max_cols]):
        x = pad + idx * (thumb + pad)
        label = row.get("view_id", f"view_{idx:02d}")[:16]
        lines.append(f'<text x="{x}" y="96" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#2d2d2d">{label}</text>')
        for y, keys in ((104, ("rgb", "image", "image_path")), (104 + thumb + pad, ("mask", "mask_path"))):
            path = None
            for key in keys:
                path = repo_path(repo, case_dir, row.get(key))
                if path and path.is_file():
                    break
            lines.append(f'<rect x="{x}" y="{y}" width="{thumb}" height="{thumb}" fill="#e1e1e1" stroke="#bebebe"/>')
            if path and path.is_file():
                lines.append(
                    f'<image x="{x}" y="{y}" width="{thumb}" height="{thumb}" preserveAspectRatio="xMidYMid meet" href="{svg_href(path, output)}"/>'
                )
            else:
                lines.append(f'<text x="{x + 24}" y="{y + 56}" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#6e3232">missing</text>')
    lines.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_audit_sheet(repo: Path, case_dir: Path, rows: list[dict[str, str]], output: Path, title: str) -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        make_svg_audit_sheet(repo, case_dir, rows, output.with_suffix(".svg"), title)
        return
    thumb = 104
    pad = 10
    label_h = 34
    max_cols = max(1, min(12, len(rows)))
    width = pad + max_cols * thumb + (max_cols - 1) * pad + pad
    height = 92 + label_h + thumb * 2 + pad * 3
    sheet = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(sheet)
    font = choose_font(13)
    small = choose_font(10)
    draw.text((pad, 10), title, fill=(20, 20, 20), font=font)
    draw.text(
        (pad, 32),
        "Top: RGB views. Bottom: masks. VLM/manual reviewer must check subject, view, crop, mask, and geometry consistency.",
        fill=(70, 70, 70),
        font=small,
    )
    draw.text((pad, 54), "Dry-run sheet is not a PASS unless visual_verdict=PASS and all structural checks pass.", fill=(110, 50, 50), font=small)
    for idx, row in enumerate(rows[:max_cols]):
        x = pad + idx * (thumb + pad)
        label = row.get("view_id", f"view_{idx:02d}")
        draw.text((x, 86), label[:16], fill=(45, 45, 45), font=small)
        for y, keys in ((104, ("rgb", "image", "image_path")), (104 + thumb + pad, ("mask", "mask_path"))):
            path = None
            for key in keys:
                path = repo_path(repo, case_dir, row.get(key))
                if path and path.is_file():
                    break
            tile = Image.new("RGB", (thumb, thumb), (225, 225, 225))
            if path and path.is_file():
                image = Image.open(path).convert("RGB")
                image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                tile.paste(image, ((thumb - image.width) // 2, (thumb - image.height) // 2))
            draw.rectangle((x, y, x + thumb, y + thumb), outline=(190, 190, 190))
            sheet.paste(tile, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any], figure: Path) -> None:
    cases = payload["cases"]
    verdict = payload["verdict"]
    lines = [
        "# G21 Real GT Benchmark Gate",
        "",
        f"Date: {DATE}",
        "",
        "Gate verdict:",
        "",
        "```text",
        verdict,
        "NO_GPU_TRAINING_STARTED",
        "```",
        "",
        "Minimum executable checks:",
        "",
        "| Check | Requirement |",
        "| --- | --- |",
        "| Images | 6-12 same-identity, same static expression/frame real captured RGB views. |",
        "| Cameras | `cameras.json` covers every view and records intrinsics plus extrinsics. |",
        "| Masks | One foreground mask per selected view. |",
        "| GT geometry | Mesh or point cloud exists for the same frame/identity. |",
        "| License/privacy | License, redistribution policy, and subject/privacy policy are recorded. |",
        "| Distribution | Model/data distribution audit is recorded before interpreting results. |",
        "| VLM/manual audit sheet | Contact sheet exists and reviewer records `PASS` only if subject/view/crop/mask/geometry are coherent. |",
        "",
        "Artifacts:",
        "",
        "```text",
        str(payload["output_json"]),
        str(payload["output_md"]),
        str(figure),
        "```",
        "",
        "Case results:",
        "",
        "| case | verdict | views | rgb | masks | cameras | geometry | failed checks |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in cases:
        failed = ", ".join(case["failed_checks"]) if case["failed_checks"] else "none"
        lines.append(
            f"| {case['case_id']} | {case['verdict']} | {case['view_count']} | "
            f"{case['rgb_image_count']} | {case['mask_count']} | {case['camera_count']} | "
            f"{case['geometry_count']} | {failed} |"
        )
    if not cases:
        lines.append("| none | BLOCKED_EXTERNAL_ACCESS | 0 | 0 | 0 | 0 | 0 | no compact real-capture case found |")
    lines.extend(
        [
            "",
            "Current G21 closure:",
            "",
            "```text",
            payload["closure"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=Path("experiments/gt_cases"))
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--visual-verdict", choices=["PASS", "MANUAL_REVIEW_REQUIRED", "FAIL"], default="MANUAL_REVIEW_REQUIRED")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g21_real_gt_benchmark_gate_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g21_real_gt_benchmark_gate_20260520.md"))
    parser.add_argument("--audit-sheet", type=Path, default=Path("experiments/figures/g21_real_gt_benchmark_audit_sheet_20260520.svg"))
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    case_root = repo / args.case_root
    if args.case_id:
        case_dirs = [case_root / args.case_id]
    elif case_root.is_dir():
        case_dirs = sorted(path for path in case_root.iterdir() if path.is_dir())
    else:
        case_dirs = []

    cases = [check_case(repo, case_dir, args.visual_verdict) for case_dir in case_dirs if case_dir.is_dir()]
    pass_cases = [case for case in cases if case["verdict"] == PASS_VERDICT]
    verdict = PASS_VERDICT if pass_cases else BLOCKED_EXTERNAL
    closure = (
        "BLOCKED_EXTERNAL_ACCESS: no local compact licensed real-capture case has passed images/cameras/"
        "masks/geometry/license/distribution/VLM checks. Synthetic positive controls remain diagnostic only."
    )
    if pass_cases:
        closure = "PASS_REAL_GT_BENCHMARK: at least one compact real-capture case passed the gate."

    sheet_rows: list[dict[str, str]] = []
    sheet_case_dir = case_dirs[0] if case_dirs else case_root
    if case_dirs and (case_dirs[0] / "manifest.csv").is_file():
        sheet_rows = read_csv(case_dirs[0] / "manifest.csv")
    audit_sheet = args.audit_sheet.with_suffix(".svg") if Image is None else args.audit_sheet
    make_audit_sheet(
        repo=repo,
        case_dir=sheet_case_dir,
        rows=sheet_rows,
        output=repo / audit_sheet,
        title="G21 real-GT benchmark VLM/manual audit sheet",
    )

    payload = {
        "date": DATE,
        "gate": "G21",
        "verdict": verdict,
        "required_verdict": PASS_VERDICT,
        "closure": closure,
        "case_root": str(args.case_root),
        "cases": cases,
        "output_json": str(args.output_json),
        "output_md": str(args.output_md),
        "audit_sheet": str(audit_sheet),
    }
    write_json(repo / args.output_json, payload)
    write_markdown(repo / args.output_md, payload, audit_sheet)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {audit_sheet}")
    print(verdict)
    if args.fail_on_blocked and verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
