#!/usr/bin/env python3
"""Summarize the private LAM export gate without syncing identifiable media."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
VERDICT = "PASS_LAM_EXPORT_LOCAL_ONLY_NO_QUALITY_CLAIM"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "basename": path.name,
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256(path) if path.is_file() else "",
    }


def ply_vertex_count(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open("rb") as f:
        for raw in f:
            line = raw.decode("ascii", errors="ignore").strip()
            if line.startswith("element vertex "):
                return int(line.split()[-1])
            if line == "end_header":
                break
    return 0


def obj_counts(path: Path) -> dict[str, int]:
    vertices = 0
    faces = 0
    if path.is_file():
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("v "):
                    vertices += 1
                elif line.startswith("f "):
                    faces += 1
    return {"vertices": vertices, "faces": faces}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G42 LAM Geometry/Frame Export Gate",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Purpose:",
        "",
        "```text",
        payload["purpose"],
        "```",
        "",
        "Export summary:",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in payload["export_summary"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "Key private output hashes:",
            "",
            "| basename | exists | size_bytes | sha256 |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for item in payload["key_private_outputs"]:
        lines.append(f"| {item['basename']} | {item['exists']} | {item['size_bytes']} | {item['sha256']} |")
    lines.extend(
        [
            "",
            "Manual/VLM-style visual audit:",
            "",
            "```text",
            payload["manual_visual_audit"],
            "```",
            "",
            "Environment notes:",
            "",
            "```text",
            "\n".join(payload["environment_notes"]),
            "```",
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--private-run-root",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/runs/g42_lam_export_multiface_local_20260520"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("experiments/metrics/g42_lam_export_gate_20260520.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/g42_lam_export_gate_20260520.md"),
    )
    args = parser.parse_args()

    root = args.private_run_root
    image_dir = root / "images/400017_000102"
    cano_dir = root / "cano_gs/cano_gs"
    video = root / "videos/400017_000102.mp4"
    audio_video = root / "videos/400017_000102_audio.mp4"
    sheet = root / "g42_private_render_frame_sheet.png"
    cano_ply = cano_dir / "400017_000102_gs_offset.ply"
    shaped_mesh = cano_dir / "400017_000102_shaped_mesh.obj"
    textured_mesh = cano_dir / "400017_000102_textured_mesh.obj"
    frame0 = image_dir / "0000.png"
    frame0_ply = image_dir / "0000.ply"
    png_count = len(list(image_dir.glob("*.png")))
    ply_count = len(list(image_dir.glob("*.ply")))

    payload = {
        "date": DATE,
        "gate": "G42",
        "verdict": VERDICT if png_count == 50 and ply_count == 50 and cano_ply.is_file() else "BLOCKED_LAM_EXPORT_INCOMPLETE",
        "purpose": (
            "Verify whether the learned-prior LAM route can export frames and geometry-like artifacts that could "
            "become inputs to a later held-out camera or geometry metric adapter."
        ),
        "command_summary": (
            "LAM-20K, Multiface E001 frame 000102 camera 400017, save_img=true, save_ply=true, "
            "test_sample=true, CUDA_VISIBLE_DEVICES=1."
        ),
        "export_summary": {
            "private_run_root": str(root),
            "render_png_count": png_count,
            "per_frame_ply_count": ply_count,
            "canonical_gaussian_vertices": ply_vertex_count(cano_ply),
            "frame0_gaussian_vertices": ply_vertex_count(frame0_ply),
            "shaped_mesh_counts": obj_counts(shaped_mesh),
            "textured_mesh_counts": obj_counts(textured_mesh),
            "repo_sync_policy": "hashes/metrics only; private RGB/PNG/MP4/PLY/OBJ remain under 3dv_work",
        },
        "key_private_outputs": [
            file_record(video),
            file_record(audio_video),
            file_record(sheet),
            file_record(cano_ply),
            file_record(shaped_mesh),
            file_record(textured_mesh),
            file_record(frame0),
            file_record(frame0_ply),
        ],
        "manual_visual_audit": (
            "PASS_LOCAL_EXPORT_ONLY. The private frame sheet shows a coherent animated head and exported frames, "
            "but it still has green color cast, blurred shoulder/neck support, and background residuals. These "
            "frames are not Multiface held-out camera renders."
        ),
        "environment_notes": [
            "A direct env-python command failed because torch was missing from base Python.",
            "A second direct command reached LAM but nvdiffrast JIT failed because ninja was not on PATH.",
            "The passing run used conda activate lam, env124.sh, CUDA_VISIBLE_DEVICES=1, and test_sample=true.",
        ],
        "decision": (
            "G42 proves LAM can export canonical Gaussian PLY, per-frame Gaussian PLYs, PNG frames, and mesh OBJs "
            "locally. It still does not prove reconstruction quality because the exported renders use LAM motion "
            "cameras, not held-out Multiface cameras, and the coordinate relation to GT geometry remains unvalidated."
        ),
    }
    write_json(args.repo / args.output_json, payload)
    write_md(args.repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(payload["verdict"])
    if payload["verdict"] != VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
