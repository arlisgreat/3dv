#!/usr/bin/env python3
"""Build downstream-readable pseudo-view candidate pools.

The output is intentionally simple and tool-agnostic:

experiments/downstream_datasets/<variant>/<sample_id>/
  images/
  masks/
  metadata.json

The directory name is historical. These outputs are candidate pools for
controlled downstream ablations, not validated reconstruction training sets.

Variants:
  raw75_all6                 all raw Zero123++ steps75 views
  raw75_budget4              CLIP/reliability selected raw steps75 views
  cutout75_budget4_masked    CLIP/reliability selected cutout steps75 views,
                              keeping only trusted-mask accepted views
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageOps


VIEW_RE = re.compile(r"view_(?P<idx>\d+)_az(?P<az>\d+)_el(?P<el>[+-]\d+)\.png$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_view_file(path: Path) -> dict[str, int | None]:
    match = VIEW_RE.match(path.name)
    if not match:
        return {"view_index": None, "azimuth": None, "elevation": None}
    return {
        "view_index": int(match.group("idx")),
        "azimuth": int(match.group("az")),
        "elevation": int(match.group("el")),
    }


def make_foreground_mask(image_path: Path, out_path: Path, bg_rgb: tuple[int, int, int] = (127, 127, 127), threshold: int = 18) -> float:
    """Create a simple mask by thresholding distance from Zero123++ gray background."""
    image = Image.open(image_path).convert("RGB")
    bg = Image.new("RGB", image.size, bg_rgb)
    diff = ImageChops.difference(image, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > threshold else 0)
    mask = ImageOps.autocontrast(mask)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mask.save(out_path)
    nonzero = sum(1 for v in mask.getdata() if v > 0)
    return nonzero / float(mask.width * mask.height)


def clean_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} already exists. Use --overwrite to rebuild.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def budget_rows(path: Path, budget: int) -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(path)
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if int(row["budget"]) == budget:
            selected[(row["sample_id"], row["run"])] = row
    return selected


def trusted_manifest_map(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Return sample_id -> view_index string -> trusted manifest item."""
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for manifest_path in root.glob("*/manifest.json"):
        sample_id = manifest_path.parent.name
        items = load_json(manifest_path)
        result[sample_id] = {str(item["view_index"]): item for item in items}
    return result


def copy_view(
    src: Path,
    dst_images: Path,
    dst_masks: Path,
    name_prefix: str,
    trusted_item: dict[str, Any] | None,
    require_accepted: bool,
) -> dict[str, Any] | None:
    view_info = parse_view_file(src)
    view_index = str(view_info["view_index"])

    if require_accepted:
        if trusted_item is None or not trusted_item.get("accepted", False):
            return None

    image_name = f"{name_prefix}_{src.name}"
    mask_name = f"{name_prefix}_{src.stem}_mask.png"
    image_dst = dst_images / image_name
    mask_dst = dst_masks / mask_name
    shutil.copy2(src, image_dst)
    mask_coverage = make_foreground_mask(src, mask_dst)

    record = {
        "view_index": view_info["view_index"],
        "azimuth": view_info["azimuth"],
        "elevation": view_info["elevation"],
        "image": str(image_dst),
        "mask": str(mask_dst),
        "source_image": str(src),
        "mask_coverage": mask_coverage,
    }
    if trusted_item is not None:
        record.update(
            {
                "trusted_accepted": bool(trusted_item.get("accepted", False)),
                "trusted_score": trusted_item.get("trusted_score"),
                "reliability_score": trusted_item.get("reliability_score"),
                "reject_reasons": trusted_item.get("reject_reasons", []),
                "trusted_manifest_item": trusted_item,
            }
        )
    else:
        record["trusted_accepted"] = None
    return record


def build_variant(
    *,
    root: Path,
    variant: str,
    sample_rows: list[dict[str, str]],
    source_run: str,
    selected_rows: dict[tuple[str, str], dict[str, str]],
    trusted: dict[str, dict[str, dict[str, Any]]],
    raw_base: Path,
    cutout_base: Path,
    output_root: Path,
    budget: int,
    all_views: bool,
    require_accepted: bool,
    overwrite: bool,
) -> None:
    out_variant = output_root / variant
    clean_dir(out_variant, overwrite=overwrite)
    summary: list[dict[str, Any]] = []

    for sample in sample_rows:
        sample_id = sample["sample_id"]
        group = sample.get("group", "")
        sample_out = out_variant / sample_id
        images_dir = sample_out / "images"
        masks_dir = sample_out / "masks"
        images_dir.mkdir(parents=True, exist_ok=True)
        masks_dir.mkdir(parents=True, exist_ok=True)

        base = cutout_base if source_run == "cutout75" else raw_base
        view_dir = base / f"{sample_id}_steps75"
        if not view_dir.exists():
            raise FileNotFoundError(f"Missing view directory: {view_dir}")

        if all_views:
            view_files = sorted(view_dir.glob("view_*.png"))
            selection_row = None
        else:
            selection_row = selected_rows.get((sample_id, source_run))
            if selection_row is None:
                raise KeyError(f"Missing budget row for {(sample_id, source_run)}")
            view_files = [Path(p) for p in selection_row["selected_view_files"].split(";") if p]

        records: list[dict[str, Any]] = []
        sample_trusted = trusted.get(sample_id, {})
        for order, view_file in enumerate(view_files):
            view_info = parse_view_file(view_file)
            view_index = str(view_info["view_index"])
            trusted_item = sample_trusted.get(view_index)
            rec = copy_view(
                view_file,
                images_dir,
                masks_dir,
                f"{order:02d}",
                trusted_item,
                require_accepted=require_accepted,
            )
            if rec is not None:
                records.append(rec)

        metadata = {
            "semantic_type": "pseudo_view_candidate_pool",
            "validated_training_dataset": False,
            "semantic_note": (
                "This historical downstream_datasets path stores pseudo-view "
                "candidates exported for downstream diagnostics. It does not "
                "prove the views are suitable reconstruction supervision."
            ),
            "sample_id": sample_id,
            "group": group,
            "variant": variant,
            "source_run": source_run,
            "budget": "all6" if all_views else budget,
            "require_trusted_accepted": require_accepted,
            "input_path": sample.get("input_path"),
            "source_sample": sample,
            "selection_row": selection_row,
            "view_count": len(records),
            "views": records,
        }
        write_json(sample_out / "metadata.json", metadata)
        summary.append(
            {
                "sample_id": sample_id,
                "group": group,
                "variant": variant,
                "source_run": source_run,
                "view_count": len(records),
                "metadata": str(sample_out / "metadata.json"),
            }
        )

    with (out_variant / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "group", "variant", "source_run", "view_count", "metadata"])
        writer.writeheader()
        writer.writerows(summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build downstream-readable pseudo-view candidate pools.")
    parser.add_argument("--manifest", default="experiments/inputs/first10/manifest.csv")
    parser.add_argument("--budget-csv", default="experiments/metrics/view_budget_clip_selection_raw_vs_cutout_steps75.csv")
    parser.add_argument("--trusted-root", default="experiments/pseudo_views/trusted_region_masks_cutout75_budget4")
    parser.add_argument("--raw-base", default="experiments/pseudo_views/zero123plus_first10_steps75")
    parser.add_argument("--cutout-base", default="experiments/pseudo_views/zero123plus_first10_cutout_steps75")
    parser.add_argument("--output-root", default="experiments/downstream_datasets")
    parser.add_argument("--budget", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    sample_rows = read_csv(root / args.manifest)
    selected_rows = budget_rows(root / args.budget_csv, args.budget)
    trusted = trusted_manifest_map(root / args.trusted_root)

    output_root = root / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    common = {
        "root": root,
        "sample_rows": sample_rows,
        "selected_rows": selected_rows,
        "trusted": trusted,
        "raw_base": root / args.raw_base,
        "cutout_base": root / args.cutout_base,
        "output_root": output_root,
        "budget": args.budget,
        "overwrite": args.overwrite,
    }

    build_variant(variant="raw75_all6", source_run="raw75", all_views=True, require_accepted=False, **common)
    build_variant(variant="raw75_budget4", source_run="raw75", all_views=False, require_accepted=False, **common)
    build_variant(variant="cutout75_budget4_masked", source_run="cutout75", all_views=False, require_accepted=True, **common)

    print(f"Built downstream-readable pseudo-view candidate pools under {output_root}")
    print("Variants: raw75_all6, raw75_budget4, cutout75_budget4_masked")


if __name__ == "__main__":
    main()
