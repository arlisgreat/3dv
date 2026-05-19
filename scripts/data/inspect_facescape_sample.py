#!/usr/bin/env python3
"""Inspect local FaceScape sample structure without exporting face imagery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def jpeg_size(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None, None
    idx = 2
    while idx + 9 < len(data):
        if data[idx] != 0xFF:
            idx += 1
            continue
        marker = data[idx + 1]
        idx += 2
        while marker == 0xFF and idx < len(data):
            marker = data[idx]
            idx += 1
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if idx + 2 > len(data):
            break
        seg_len = int.from_bytes(data[idx : idx + 2], "big")
        if seg_len < 2 or idx + seg_len > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height = int.from_bytes(data[idx + 3 : idx + 5], "big")
            width = int.from_bytes(data[idx + 5 : idx + 7], "big")
            return width, height
        idx += seg_len
    return None, None


def image_info(path: Path) -> dict[str, object]:
    width, height = jpeg_size(path)
    return {
        "file": path.name,
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
    }


def inspect_sample(sample_root: Path) -> dict[str, object]:
    mview_root = sample_root / "sample_mview_data" / "4_anger"
    params_path = mview_root / "params.json"
    params = json.loads(params_path.read_text(encoding="utf-8"))
    views = sorted({int(key.split("_", 1)[0]) for key in params if key.split("_", 1)[0].isdigit()})
    valid_views = [view for view in views if params.get(f"{view}_valid")]
    available_images = sorted(mview_root.glob("*.jpg"))

    return {
        "sample_root": str(sample_root),
        "redistribution_note": "FaceScape sample readme says: do not distribute.",
        "sample_tar_bytes": (sample_root / "samples.tar.gz").stat().st_size
        if (sample_root / "samples.tar.gz").exists()
        else None,
        "mview_tuple": "4_anger",
        "mview_param_views": len(views),
        "mview_valid_views": len(valid_views),
        "mview_available_images": [image_info(path) for path in available_images],
        "mview_mesh": {
            "file": "4_anger.ply",
            "bytes": (sample_root / "sample_mview_data" / "4_anger.ply").stat().st_size,
        },
        "tu_model_files": sorted(path.name for path in (sample_root / "sample_tu_model").glob("1_neutral.*")),
        "keypoint3d_rows": sum(1 for _ in (sample_root / "sample_keypoint3d.txt").open("r", encoding="utf-8")),
        "gate_implication": (
            "Sample confirms FaceScape has calibrated multi-view params and a corresponding mesh, "
            "but the public sample exposes only two images and must not be committed or redistributed."
        ),
    }


def write_markdown(path: Path, audit: dict[str, object]) -> None:
    images = audit["mview_available_images"]
    lines = [
        "# FaceScape Sample Access Audit",
        "",
        "Date: 2026-05-19",
        "",
        "Gate verdict:",
        "",
        "```text",
        "PASS_METADATA_ACCESS",
        "BLOCKED_REPO_IMAGE_EXPORT",
        "BLOCKED_RECONSTRUCTION_CASE_UNTIL_LICENSED_DATA_OR_SAMPLE_POLICY_IS_RESOLVED",
        "```",
        "",
        "Local sample:",
        "",
        "```text",
        str(audit["sample_root"]),
        f"sample_tar_bytes: {audit['sample_tar_bytes']}",
        f"mview_tuple: {audit['mview_tuple']}",
        f"mview_param_views: {audit['mview_param_views']}",
        f"mview_valid_views: {audit['mview_valid_views']}",
        f"available_mview_images: {len(images)}",
        f"keypoint3d_rows: {audit['keypoint3d_rows']}",
        "```",
        "",
        "Available image metadata only:",
        "",
        "| file | width | height | bytes |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in images:
        lines.append(f"| {item['file']} | {item['width']} | {item['height']} | {item['bytes']} |")
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "```text",
            "The sample confirms the intended GT route: calibrated camera parameters, valid flags,",
            "high-resolution images, and a corresponding mesh are available in FaceScape format.",
            "However, the sample readme explicitly says not to distribute it, so raw images,",
            "mesh files, thumbnails, or rendered face figures stay out of git.",
            "```",
            "",
            "Next action:",
            "",
            "```text",
            "Use this only as a local parser/access check. For publishable reconstruction",
            "validation, obtain licensed FaceScape access and use publishable-list subjects,",
            "or use an alternate dataset with redistributable demo data.",
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--sample-root", default="external/facescape/samples")
    parser.add_argument("--json-out", default="experiments/metrics/facescape_sample_access_audit_20260519.json")
    parser.add_argument("--md-out", default="experiments/metrics/facescape_sample_access_audit_20260519.md")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    audit = inspect_sample(repo / args.sample_root)
    json_path = repo / args.json_out
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    write_markdown(repo / args.md_out, audit)
    print(f"json={json_path.relative_to(repo)}")
    print(f"md={Path(args.md_out)}")


if __name__ == "__main__":
    main()
