#!/usr/bin/env python3
"""Export G81 pseudo-supervision manifests to a private RI3D-readable pool."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps


DATE = "2026-05-28"
GATE = "G86"
PASS_VERDICT = "PASS_G81_RI3D_PRIVATE_POOL_READY"
BLOCKED_VERDICT = "BLOCKED_G81_RI3D_PRIVATE_POOL"
BACKGROUND = np.array([127, 127, 127], dtype=np.int16)


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


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def load_image(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def source_square_mask(image_path: Path, output_path: Path, threshold: float) -> float:
    image = load_image(image_path)
    arr = np.asarray(image).astype(np.int16)
    dist = np.linalg.norm(arr - BACKGROUND[None, None, :], axis=2)
    mask = (dist > threshold).astype(np.uint8) * 255
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask, mode="L").save(output_path)
    return float((mask > 0).mean())


def mask_coverage(path: Path) -> float:
    mask = np.asarray(Image.open(path).convert("L"))
    return float((mask > 127).mean())


def resolve(path: str, repo: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo / candidate


def clean_or_create(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} exists. Use --overwrite to rebuild.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def make_sheet(arm_rows: list[dict[str, Any]], output: Path) -> None:
    tile_w, tile_h = 170, 210
    max_views = max(len(row["views"]) for row in arm_rows)
    sheet = Image.new("RGB", ((max_views + 1) * tile_w, len(arm_rows) * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    for row_i, arm in enumerate(arm_rows):
        y0 = row_i * tile_h
        draw.text((8, y0 + 8), arm["arm"], fill=(0, 0, 0))
        for col, view in enumerate(arm["views"]):
            image = load_image(Path(view["image_abs"]))
            image.thumbnail((tile_w - 10, tile_w - 52), Image.Resampling.LANCZOS)
            x0 = col * tile_w
            sheet.paste(image, (x0 + (tile_w - image.width) // 2, y0 + 28))
            label = f"{view['view_index']} {view['supervision_role']}\nconf={view['confidence_score']:.1f}"
            draw.multiline_text((x0 + 8, y0 + tile_h - 38), label[:80], fill=(0, 0, 0), spacing=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def export_arm(
    *,
    repo: Path,
    arm_name: str,
    variant: str,
    sample_id: str,
    manifest_path: Path,
    source_prep: dict[str, Any],
    candidate_root: Path,
    include_source_anchor: bool,
    source_mask_threshold: float,
    heldout_paths: set[str],
    overwrite: bool,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    scene = candidate_root / variant / sample_id
    clean_or_create(scene, overwrite=overwrite)
    images_dir = scene / "images"
    masks_dir = scene / "masks"
    views: list[dict[str, Any]] = []
    leakage_paths: list[str] = []

    source_image = Path(source_prep["private_outputs"]["masked_square_input"])
    if include_source_anchor:
        src_dst = images_dir / "000_source_identity_anchor.png"
        mask_dst = masks_dir / "000_source_identity_anchor_mask.png"
        copy_file(source_image, src_dst)
        source_coverage = source_square_mask(src_dst, mask_dst, source_mask_threshold)
        views.append(
            {
                "view_index": -1,
                "image": f"images/{src_dst.name}",
                "image_sha256": sha256_file(src_dst),
                "mask": f"masks/{mask_dst.name}",
                "mask_sha256": sha256_file(mask_dst),
                "mask_coverage": source_coverage,
                "azimuth": 0.0,
                "elevation": 0.0,
                "source_image": str(source_image),
                "identity_anchor_score": 1.0,
                "confidence_score": 100.0,
                "supervision_role": "source_identity_anchor",
                "ri3d_train_candidate": True,
                "rgb_weight": 1.0,
                "depth_weight": 1.0,
                "mask_weight": 1.0,
                "confidence_multiplier": 1.0,
            }
        )

    for order, view in enumerate(manifest.get("pseudo_views", []), start=1 if include_source_anchor else 0):
        image_src = resolve(str(view["image_path"]), repo)
        mask_src = resolve(str(view["trusted_region_mask"]), repo)
        image_dst = images_dir / f"{order:03d}_view{int(view['view_index']):02d}.png"
        mask_dst = masks_dir / f"{order:03d}_view{int(view['view_index']):02d}_trusted_mask.png"
        copy_file(image_src, image_dst)
        copy_file(mask_src, mask_dst)
        for candidate in (str(image_src), str(mask_src)):
            if candidate in heldout_paths:
                leakage_paths.append(candidate)
        confidence = float(view.get("confidence_score", 100.0))
        views.append(
            {
                "view_index": int(view["view_index"]),
                "image": f"images/{image_dst.name}",
                "image_sha256": sha256_file(image_dst),
                "mask": f"masks/{mask_dst.name}",
                "mask_sha256": sha256_file(mask_dst),
                "mask_coverage": mask_coverage(mask_dst),
                "azimuth": float(view.get("azimuth", 0.0)),
                "elevation": float(view.get("elevation", 0.0)),
                "source_image": str(source_image),
                "identity_anchor_score": view.get("identity_anchor_score"),
                "confidence_score": confidence,
                "supervision_role": view.get("supervision_role", "naive_rgb"),
                "ri3d_train_candidate": bool(view.get("ri3d_train_candidate", True)),
                "rgb_weight": float(view.get("rgb_weight", 1.0)),
                "depth_weight": float(view.get("depth_weight", 1.0)),
                "mask_weight": float(view.get("mask_weight", 1.0)),
                "confidence_multiplier": confidence / 100.0,
            }
        )

    metadata = {
        "semantic_type": "g81_private_ri3d_pseudo_supervision_pool",
        "validated_training_dataset": False,
        "candidate_pool_not_groundtruth": True,
        "arm": arm_name,
        "variant": variant,
        "sample_id": sample_id,
        "source_serial": source_prep["source_serial"],
        "source_anchor_included": include_source_anchor,
        "no_leakage_rule": "Uses only the single source image, source mask, and generated pseudo views; held-out RGB/masks are evaluation-only.",
        "source_prep_json": str(source_prep["private_outputs"]["private_manifest"]),
        "pseudo_manifest": str(manifest_path),
        "views": views,
    }
    write_json(scene / "metadata.json", metadata)
    role_counts = Counter(str(view["supervision_role"]) for view in views if view.get("ri3d_train_candidate", True))
    return {
        "arm": arm_name,
        "variant": variant,
        "sample_id": sample_id,
        "scene_dir": str(scene),
        "metadata": str(scene / "metadata.json"),
        "view_count": len(views),
        "trainable_view_count": sum(bool(view.get("ri3d_train_candidate", True)) for view in views),
        "role_counts": dict(role_counts),
        "heldout_path_leakage": sorted(set(leakage_paths)),
        "views": [{**view, "image_abs": str(scene / view["image"])} for view in views],
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G86 G81 Private RI3D Pool Export",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Scenes:",
        "",
        "| arm | variant | views | trainable | roles | metadata |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in payload["scenes"]:
        lines.append(
            f"| {row['arm']} | {row['variant']} | {row['view_count']} | {row['trainable_view_count']} | "
            f"{json.dumps(row['role_counts'], sort_keys=True)} | {row['metadata']} |"
        )
    lines.extend(
        [
            "",
            "Private contact sheet:",
            "",
            "```text",
            payload["private_outputs"]["contact_sheet"],
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
    parser.add_argument("--source-prep-json", type=Path, default=Path("experiments/metrics/g83_nersemble_source220700191_pseudo_input_prep_20260528.json"))
    parser.add_argument("--naive-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/naive_pseudo_supervision_manifest.json"))
    parser.add_argument("--aware-manifest", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/identity_confidence_aware_pseudo_supervision_manifest.json"))
    parser.add_argument("--candidate-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g86_g81_nersemble_pseudo_ri3d_pool/candidate_pools"))
    parser.add_argument("--sample-id", default="source220700191")
    parser.add_argument("--source-mask-threshold", type=float, default=22.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g86_g81_private_ri3d_pool_export_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g86_g81_private_ri3d_pool_export_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    adapter = load_json(args.adapter_manifest)
    source_prep_path = args.source_prep_json if args.source_prep_json.is_absolute() else repo / args.source_prep_json
    source_prep = load_json(source_prep_path)
    eval_serials = set(adapter["split"]["local_eval_serials"])
    heldout_paths = {
        str(row.get(key))
        for row in adapter["views"]
        if row["serial"] in eval_serials
        for key in ("rgb_path", "mask_path")
        if row.get(key)
    }

    arm_specs = [
        ("naive_pseudo_view_supervision", "g81_naive_pseudo_source_anchor", args.naive_manifest),
        ("identity_confidence_aware_pseudo_view_supervision", "g81_identity_confidence_aware_source_anchor", args.aware_manifest),
    ]
    scenes = [
        export_arm(
            repo=repo,
            arm_name=arm_name,
            variant=variant,
            sample_id=args.sample_id,
            manifest_path=manifest_path,
            source_prep=source_prep,
            candidate_root=args.candidate_root,
            include_source_anchor=True,
            source_mask_threshold=args.source_mask_threshold,
            heldout_paths=heldout_paths,
            overwrite=args.overwrite,
        )
        for arm_name, variant, manifest_path in arm_specs
    ]
    contact_sheet = args.candidate_root.parent / "g86_private_ri3d_pool_sheet.png"
    make_sheet(scenes, contact_sheet)
    missing = [
        f"{row['arm']}: only {row['trainable_view_count']} trainable views"
        for row in scenes
        if row["trainable_view_count"] < 4
    ]
    for row in scenes:
        if row["heldout_path_leakage"]:
            missing.append(f"{row['arm']}: held-out leakage {row['heldout_path_leakage']}")
    verdict = PASS_VERDICT if not missing else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "verdict": verdict,
        "case": adapter["case"],
        "split": adapter["split"],
        "candidate_root": str(args.candidate_root),
        "scenes": [
            {key: value for key, value in row.items() if key != "views"}
            for row in scenes
        ],
        "missing_requirements": missing,
        "private_outputs": {
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256_file(contact_sheet),
        },
        "artifact_policy": "Private source/pseudo-view images and masks stay under 3dv_work; commit repo-safe metrics and hashes only.",
        "decision": (
            "Private RI3D-readable naive and identity/confidence-aware scene pools are ready for scene conversion."
            if verdict == PASS_VERDICT
            else "Blocked: scene pool export failed leakage or trainable-view requirements."
        ),
        "next_gate": "Run scripts/prepare_ri3d_dataset.py on this private candidate root, then train/render both arms.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "candidate_root": str(args.candidate_root), "missing": missing}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
