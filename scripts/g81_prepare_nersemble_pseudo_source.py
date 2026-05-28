#!/usr/bin/env python3
"""Prepare the private NeRSemble source image for G81 pseudo-view generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G81_NERSEMBLE_SOURCE_PSEUDO_INPUT_READY_PRIVATE"
BLOCKED_VERDICT = "BLOCKED_G81_NERSEMBLE_SOURCE_PSEUDO_INPUT"


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


def square_with_mask(rgb_path: Path, mask_path: Path, output_path: Path, size: int) -> dict[str, Any]:
    rgb = ImageOps.exif_transpose(Image.open(rgb_path)).convert("RGB")
    mask = Image.open(mask_path).convert("L")
    if mask.size != rgb.size:
        mask = mask.resize(rgb.size, Image.Resampling.NEAREST)
    mask_arr = np.asarray(mask) > 8
    bg = Image.new("RGB", rgb.size, (127, 127, 127))
    bg.paste(rgb, (0, 0), Image.fromarray(mask_arr.astype(np.uint8) * 255, mode="L"))

    side = max(bg.size)
    square = Image.new("RGB", (side, side), (127, 127, 127))
    square.paste(bg, ((side - bg.width) // 2, (side - bg.height) // 2))
    if size > 0:
        square = square.resize((size, size), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    square.save(output_path)
    return {
        "source_width": rgb.width,
        "source_height": rgb.height,
        "mask_coverage": float(mask_arr.mean()),
        "output_width": square.width,
        "output_height": square.height,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} NeRSemble Pseudo-View Source Prep",
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
        "Source:",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| participant | {payload['case'].get('participant')} |",
        f"| sequence | {payload['case'].get('sequence')} |",
        f"| timestep | {payload['case'].get('timestep')} |",
        f"| source_serial | {payload['source_serial']} |",
        f"| local_eval_serials | {', '.join(payload['split']['local_eval_serials'])} |",
        f"| mask_coverage | {payload['source_stats']['mask_coverage']:.6f} |",
        f"| private_source_input | {payload['private_outputs']['masked_square_input']} |",
        f"| private_source_input_sha256 | {payload['private_outputs']['masked_square_input_sha256']} |",
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
    parser.add_argument(
        "--adapter-manifest",
        type=Path,
        default=Path("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json"),
    )
    parser.add_argument("--work-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g83_nersemble_source220700191_pseudo_input"))
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--gate", default="G83")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g83_nersemble_source220700191_pseudo_input_prep_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g83_nersemble_source220700191_pseudo_input_prep_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    source = next(row for row in adapter["views"] if row["role"] == "source_single_image")
    rgb_path = Path(source["rgb_path"])
    mask_path = Path(source["mask_path"])
    output_path = args.work_root / f"cam_{source['serial']}_masked_square_{args.size}.png"
    private_manifest = args.work_root / "source_pseudo_input_manifest.json"

    missing = [str(path) for path in (rgb_path, mask_path) if not path.exists()]
    if missing:
        source_stats: dict[str, Any] = {}
        verdict = BLOCKED_VERDICT
    else:
        source_stats = square_with_mask(rgb_path, mask_path, output_path, args.size)
        verdict = PASS_VERDICT

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "premise": (
            "Prepare the single real NeRSemble source image for pseudo-view generation. "
            "This uses only the source RGB/mask; held-out RGB/masks remain evaluation-only."
        ),
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "source_serial": source["serial"],
        "source_rgb_path": str(rgb_path),
        "source_mask_path": str(mask_path),
        "source_stats": source_stats,
        "missing_inputs": missing,
        "private_outputs": {
            "masked_square_input": str(output_path) if output_path.exists() else None,
            "masked_square_input_sha256": sha256_file(output_path) if output_path.exists() else None,
            "private_manifest": str(private_manifest),
        },
        "artifact_policy": "Identifiable source RGB and generated pseudo views stay under 3dv_work; commit only hashes/metrics/gate docs.",
        "decision": (
            "Private masked-square source input is ready for Zero123++ or another pseudo-view generator."
            if verdict == PASS_VERDICT
            else "Blocked: source RGB/mask files are missing."
        ),
        "next_gate": "Run pseudo-view generation from this private source input, then build the G81 naive and identity/confidence-aware arms.",
    }
    if verdict == PASS_VERDICT:
        write_json(private_manifest, payload)
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "private_input": payload["private_outputs"]["masked_square_input"]}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
