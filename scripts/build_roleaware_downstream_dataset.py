#!/usr/bin/env python3
"""Build a conservative role-aware downstream dataset from identity-filter CSVs.

Default output:

experiments/downstream_datasets/roleaware_cutout75_budget4/<sample_id>/
  images/
  masks/
  metadata.json

The builder is intentionally CSV-driven: it does not re-run identity models or
mask analysis, and it preserves reject decisions as metadata roles.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from build_downstream_dataset import (
    clean_dir,
    load_json,
    make_foreground_mask,
    parse_view_file,
    read_csv,
    write_json,
)


DEFAULT_SAMPLES = ("web_clean_frontal_03", "web_clean_frontal_01")
ROLE_VALUES = ("identity_supervision", "geometry_only", "identity_reject", "mask_reject")


def bool_cell(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def split_labels(value: str | None) -> list[str]:
    return [part for part in (value or "").split(";") if part]


def supervision_role(row: dict[str, str]) -> str:
    """Map existing identity-filter decisions into the four downstream roles."""
    if not bool_cell(row.get("mask_accepted")):
        return "mask_reject"
    if bool_cell(row.get("identity_supervision_candidate")):
        return "identity_supervision"
    if bool_cell(row.get("geometry_only_candidate")):
        return "geometry_only"
    if row.get("identity_decision") == "identity_reject" or "identity_reject" in split_labels(
        row.get("identity_labels")
    ):
        return "identity_reject"
    return "identity_reject"


def trusted_manifest_map(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for manifest_path in root.glob("*/manifest.json"):
        items = load_json(manifest_path)
        result[manifest_path.parent.name] = {str(item["view_index"]): item for item in items}
    return result


def sample_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def selected_identity_rows(
    rows: list[dict[str, str]],
    *,
    samples: tuple[str, ...],
    run: str,
    budget: int,
) -> dict[str, list[dict[str, str]]]:
    wanted = set(samples)
    grouped: dict[str, list[dict[str, str]]] = {sample_id: [] for sample_id in samples}
    for row in rows:
        if row["sample_id"] not in wanted:
            continue
        if row["run"] != run or int(row["budget"]) != budget:
            continue
        grouped[row["sample_id"]].append(row)

    for sample_id in samples:
        if not grouped[sample_id]:
            raise KeyError(f"No identity-filter rows found for {sample_id} run={run} budget={budget}")
        grouped[sample_id].sort(key=lambda row: int(row["tile_index"]))
    return grouped


def copy_role_view(
    *,
    repo: Path,
    row: dict[str, str],
    order: int,
    images_dir: Path,
    masks_dir: Path,
    trusted_item: dict[str, Any] | None,
) -> dict[str, Any]:
    src = repo / row["view_file"]
    if not src.exists():
        raise FileNotFoundError(src)

    view_info = parse_view_file(src)
    image_name = f"{order:02d}_{src.name}"
    mask_name = f"{order:02d}_{src.stem}_mask.png"
    image_dst = images_dir / image_name
    mask_dst = masks_dir / mask_name
    shutil.copy2(src, image_dst)
    mask_coverage = make_foreground_mask(src, mask_dst)

    role = supervision_role(row)
    record: dict[str, Any] = {
        "view_index": view_info["view_index"],
        "azimuth": view_info["azimuth"],
        "elevation": view_info["elevation"],
        "image": str(image_dst),
        "mask": str(mask_dst),
        "source_image": row["view_file"],
        "mask_coverage": mask_coverage,
        "supervision_role": role,
        "ri3d_train_candidate": role in {"identity_supervision", "geometry_only"},
        "identity_filter_row": row,
        "mask_accepted": bool_cell(row.get("mask_accepted")),
        "mask_reject_reasons": split_labels(row.get("mask_reject_reasons")),
        "trusted_score": float(row["trusted_score"]) if row.get("trusted_score") else None,
        "reliability_score": float(row["reliability_score"]) if row.get("reliability_score") else None,
        "identity_decision": row.get("identity_decision"),
        "identity_labels": split_labels(row.get("identity_labels")),
        "identity_supervision_candidate": bool_cell(row.get("identity_supervision_candidate")),
        "geometry_only_candidate": bool_cell(row.get("geometry_only_candidate")),
        "input_face_detected": bool_cell(row.get("input_face_detected")),
        "view_face_detected": bool_cell(row.get("view_face_detected")),
        "face_embedding_cosine": float(row["face_embedding_cosine"]) if row.get("face_embedding_cosine") else None,
    }
    if trusted_item is not None:
        record.update(
            {
                "trusted_accepted": bool(trusted_item.get("accepted", False)),
                "trusted_reject_reasons": trusted_item.get("reject_reasons", []),
                "trusted_manifest_item": trusted_item,
            }
        )
    else:
        record["trusted_accepted"] = None
    return record


def build_dataset(
    *,
    repo: Path,
    manifest_rows: list[dict[str, str]],
    identity_rows: dict[str, list[dict[str, str]]],
    trusted: dict[str, dict[str, dict[str, Any]]],
    output_root: Path,
    variant: str,
    samples: tuple[str, ...],
    run: str,
    budget: int,
    min_train_candidates: int,
    overwrite: bool,
) -> None:
    out_variant = output_root / variant
    clean_dir(out_variant, overwrite=overwrite)
    manifest_by_sample = sample_map(manifest_rows)
    summary_rows: list[dict[str, Any]] = []

    for sample_id in samples:
        sample = manifest_by_sample[sample_id]
        sample_out = out_variant / sample_id
        images_dir = sample_out / "images"
        masks_dir = sample_out / "masks"
        images_dir.mkdir(parents=True, exist_ok=True)
        masks_dir.mkdir(parents=True, exist_ok=True)

        views: list[dict[str, Any]] = []
        sample_trusted = trusted.get(sample_id, {})
        for order, row in enumerate(identity_rows[sample_id]):
            trusted_item = sample_trusted.get(str(row["view_index"]))
            views.append(
                copy_role_view(
                    repo=repo,
                    row=row,
                    order=order,
                    images_dir=images_dir,
                    masks_dir=masks_dir,
                    trusted_item=trusted_item,
                )
            )

        role_counts = Counter(view["supervision_role"] for view in views)
        train_candidate_count = sum(bool(view["ri3d_train_candidate"]) for view in views)
        if train_candidate_count < min_train_candidates:
            raise ValueError(
                f"{sample_id} has only {train_candidate_count} RI3D train candidates; "
                f"minimum is {min_train_candidates}."
            )

        metadata = {
            "sample_id": sample_id,
            "group": sample.get("group", ""),
            "variant": variant,
            "source_run": run,
            "budget": budget,
            "role_values": list(ROLE_VALUES),
            "role_policy": {
                "identity_supervision": "mask accepted and identity supervision candidate",
                "geometry_only": "mask accepted, identity unverified, trusted enough for geometry",
                "identity_reject": "mask accepted but identity is rejected or not trusted for supervision",
                "mask_reject": "trusted-mask stage rejected the pseudo view",
            },
            "input_path": sample.get("input_path"),
            "source_sample": sample,
            "view_count": len(views),
            "ri3d_train_candidate_count": train_candidate_count,
            "role_counts": dict(role_counts),
            "views": views,
        }
        write_json(sample_out / "metadata.json", metadata)
        summary_rows.append(
            {
                "sample_id": sample_id,
                "group": sample.get("group", ""),
                "variant": variant,
                "source_run": run,
                "budget": budget,
                "view_count": len(views),
                "ri3d_train_candidate_count": train_candidate_count,
                "identity_supervision": role_counts.get("identity_supervision", 0),
                "geometry_only": role_counts.get("geometry_only", 0),
                "identity_reject": role_counts.get("identity_reject", 0),
                "mask_reject": role_counts.get("mask_reject", 0),
                "metadata": str(sample_out / "metadata.json"),
            }
        )

    columns = [
        "sample_id",
        "group",
        "variant",
        "source_run",
        "budget",
        "view_count",
        "ri3d_train_candidate_count",
        "identity_supervision",
        "geometry_only",
        "identity_reject",
        "mask_reject",
        "metadata",
    ]
    with (out_variant / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(summary_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("experiments/inputs/first10/manifest.csv"))
    parser.add_argument(
        "--identity-csv",
        type=Path,
        default=Path("experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv"),
    )
    parser.add_argument(
        "--trusted-root",
        type=Path,
        default=Path("experiments/pseudo_views/trusted_region_masks_cutout75_budget4"),
    )
    parser.add_argument("--output-root", type=Path, default=Path("experiments/downstream_datasets"))
    parser.add_argument("--variant", default="roleaware_cutout75_budget4")
    parser.add_argument("--samples", nargs="+", default=list(DEFAULT_SAMPLES))
    parser.add_argument("--run", default="cutout75")
    parser.add_argument("--budget", type=int, default=4)
    parser.add_argument("--min-train-candidates", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    samples = tuple(args.samples)
    manifest_rows = read_csv(repo / args.manifest)
    identity_rows = selected_identity_rows(
        read_csv(repo / args.identity_csv),
        samples=samples,
        run=args.run,
        budget=args.budget,
    )
    trusted = trusted_manifest_map(repo / args.trusted_root)

    output_root = repo / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    build_dataset(
        repo=repo,
        manifest_rows=manifest_rows,
        identity_rows=identity_rows,
        trusted=trusted,
        output_root=output_root,
        variant=args.variant,
        samples=samples,
        run=args.run,
        budget=args.budget,
        min_train_candidates=args.min_train_candidates,
        overwrite=args.overwrite,
    )

    print(f"Built role-aware downstream dataset under {output_root / args.variant}")
    for sample_id in samples:
        roles = Counter(supervision_role(row) for row in identity_rows[sample_id])
        role_text = ", ".join(f"{role}={roles.get(role, 0)}" for role in ROLE_VALUES)
        print(f"- {sample_id}: {len(identity_rows[sample_id])} views ({role_text})")


if __name__ == "__main__":
    main()
