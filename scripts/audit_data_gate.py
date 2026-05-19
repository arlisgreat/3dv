#!/usr/bin/env python3
"""Audit pseudo-view candidate pools before starting a milestone.

This is a premise gate. It does not validate candidates as reconstruction
training data. It checks whether the available candidate pools are structurally
usable for the stated milestone and records what claim they can support.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def resolve_record_path(repo: Path, sample_dir: Path, value: str | None, subdir: str) -> tuple[bool, bool]:
    """Return (exists, stale_absolute_ref)."""
    if not value:
        return False, False
    raw = Path(value)
    stale_absolute = raw.is_absolute() and not raw.exists()
    candidates = [raw]
    if not raw.is_absolute():
        candidates.append(repo / raw)
    candidates.append(sample_dir / subdir / raw.name)
    return any(path.exists() for path in candidates), stale_absolute


def manifest_maps(manifest: Path) -> tuple[list[str], dict[str, str]]:
    rows = read_csv(manifest)
    samples = [row["sample_id"] for row in rows]
    groups = {row["sample_id"]: row.get("group", "") for row in rows}
    return samples, groups


def variant_dirs(root: Path, variants: list[str] | None) -> list[Path]:
    if variants:
        return [root / variant for variant in variants]
    return sorted(path for path in root.iterdir() if path.is_dir())


def audit_variant(
    *,
    repo: Path,
    variant_dir: Path,
    expected_samples: list[str],
    groups: dict[str, str],
    min_candidate_views: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample_id in expected_samples:
        sample_dir = variant_dir / sample_id
        metadata_path = sample_dir / "metadata.json"
        if not metadata_path.exists():
            rows.append(
                {
                    "variant": variant_dir.name,
                    "sample_id": sample_id,
                    "group": groups.get(sample_id, ""),
                    "metadata_exists": False,
                    "semantic_type": "missing_candidate_pool",
                    "validated_training_dataset": False,
                    "view_count": 0,
                    "candidate_view_count": 0,
                    "identity_supervision": 0,
                    "geometry_only": 0,
                    "identity_reject": 0,
                    "mask_reject": 0,
                    "uniform_rgb": 0,
                    "trusted_accepted": 0,
                    "mask_accepted": 0,
                    "mean_mask_coverage": "",
                    "mean_trusted_score": "",
                    "mean_reliability_score": "",
                    "mean_identity_cosine": "",
                    "missing_file_refs": 1,
                    "stale_absolute_refs": 0,
                    "candidate_gate_status": "blocked",
                    "training_gate_status": "blocked_unvalidated",
                    "notes": "missing metadata.json",
                }
            )
            continue

        metadata = load_json(metadata_path)
        views = list(metadata.get("views", []))
        role_counts = Counter(str(view.get("supervision_role", "uniform_rgb")) for view in views)
        trusted_accepted = sum(bool(view.get("trusted_accepted")) for view in views)
        mask_accepted = sum(bool(view.get("mask_accepted", view.get("trusted_accepted", False))) for view in views)
        train_candidates = sum(bool(view.get("ri3d_train_candidate", True)) for view in views)
        mask_coverages = [v for v in (as_float(view.get("mask_coverage")) for view in views) if v is not None]
        trusted_scores = [v for v in (as_float(view.get("trusted_score")) for view in views) if v is not None]
        reliability_scores = [v for v in (as_float(view.get("reliability_score")) for view in views) if v is not None]
        identity_cosines = [v for v in (as_float(view.get("face_embedding_cosine")) for view in views) if v is not None]

        missing_refs = 0
        stale_abs = 0
        for view in views:
            for key, subdir in (("image", "images"), ("mask", "masks")):
                exists, stale = resolve_record_path(repo, sample_dir, view.get(key), subdir)
                missing_refs += 0 if exists else 1
                stale_abs += 1 if stale else 0
            src_value = view.get("source_image")
            if src_value:
                src = repo / src_value
                missing_refs += 0 if src.exists() else 1

        notes: list[str] = []
        if stale_abs:
            notes.append("stale absolute paths recovered from current tree")
        if missing_refs:
            notes.append("missing image/mask/source refs")
        if len(views) < min_candidate_views:
            notes.append(f"fewer than {min_candidate_views} candidate views")
        if not metadata.get("semantic_type"):
            notes.append("legacy metadata lacks explicit candidate semantic tag")

        candidate_status = "pass_for_candidate_diagnostics"
        if missing_refs or len(views) < min_candidate_views:
            candidate_status = "blocked"
        elif stale_abs or not metadata.get("semantic_type"):
            candidate_status = "pass_with_warnings"

        rows.append(
            {
                "variant": metadata.get("variant", variant_dir.name),
                "sample_id": sample_id,
                "group": metadata.get("group", groups.get(sample_id, "")),
                "metadata_exists": True,
                "semantic_type": metadata.get("semantic_type", "legacy_candidate_pool"),
                "validated_training_dataset": bool(metadata.get("validated_training_dataset", False)),
                "view_count": int(metadata.get("view_count", len(views))),
                "candidate_view_count": train_candidates,
                "identity_supervision": role_counts.get("identity_supervision", 0),
                "geometry_only": role_counts.get("geometry_only", 0),
                "identity_reject": role_counts.get("identity_reject", 0),
                "mask_reject": role_counts.get("mask_reject", 0),
                "uniform_rgb": role_counts.get("uniform_rgb", 0),
                "trusted_accepted": trusted_accepted,
                "mask_accepted": mask_accepted,
                "mean_mask_coverage": f"{mean(mask_coverages):.6f}" if mask_coverages else "",
                "mean_trusted_score": f"{mean(trusted_scores):.3f}" if trusted_scores else "",
                "mean_reliability_score": f"{mean(reliability_scores):.3f}" if reliability_scores else "",
                "mean_identity_cosine": f"{mean(identity_cosines):.6f}" if identity_cosines else "",
                "missing_file_refs": missing_refs,
                "stale_absolute_refs": stale_abs,
                "candidate_gate_status": candidate_status,
                "training_gate_status": "blocked_unvalidated",
                "notes": "; ".join(notes) if notes else "candidate pool structurally usable for diagnostics",
            }
        )
    return rows


def summarize_by_variant(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["variant"])].append(row)
    summary: list[dict[str, Any]] = []
    for variant, items in sorted(grouped.items()):
        present = [row for row in items if row["metadata_exists"]]
        statuses = Counter(str(row["candidate_gate_status"]) for row in items)
        view_counts = [int(row["view_count"]) for row in present]
        verdict = "pass_for_diagnostic_candidate_pool"
        if statuses.get("blocked"):
            verdict = "blocked_until_data_fixed"
        elif statuses.get("pass_with_warnings"):
            verdict = "pass_with_warnings_for_diagnostics"
        summary.append(
            {
                "variant": variant,
                "samples_present": len(present),
                "samples_expected": len(items),
                "min_views": min(view_counts) if view_counts else 0,
                "mean_views": f"{mean(view_counts):.2f}" if view_counts else "0.00",
                "missing_file_refs": sum(int(row["missing_file_refs"]) for row in items),
                "stale_absolute_refs": sum(int(row["stale_absolute_refs"]) for row in items),
                "identity_supervision": sum(int(row["identity_supervision"]) for row in items),
                "geometry_only": sum(int(row["geometry_only"]) for row in items),
                "uniform_rgb": sum(int(row["uniform_rgb"]) for row in items),
                "candidate_gate_verdict": verdict,
                "training_gate_verdict": "blocked_unvalidated",
            }
        )
    return summary


def write_markdown(
    *,
    path: Path,
    milestone: str,
    premise: str,
    visual_verdict: str,
    visual_notes: str,
    csv_path: Path,
    figure_path: Path,
    summary: list[dict[str, Any]],
) -> None:
    blocked = any(row["candidate_gate_verdict"] == "blocked_until_data_fixed" for row in summary)
    candidate_verdict = "BLOCKED" if blocked else "PASS FOR DIAGNOSTICS ONLY"
    lines = [
        f"# {milestone} Data Audit Gate",
        "",
        "Date: 2026-05-19",
        "",
        "Premise under audit:",
        "",
        "```text",
        premise,
        "```",
        "",
        "Gate verdict:",
        "",
        "```text",
        f"Candidate-pool diagnostic gate: {candidate_verdict}",
        "Reconstruction-training gate: BLOCKED_UNVALIDATED",
        f"Visual/VLM gate: {visual_verdict}",
        "```",
        "",
        "Interpretation:",
        "",
        "```text",
        "The audited directories are pseudo-view candidate pools and RI3D-readable candidate exports.",
        "They are structurally usable for diagnostic and failure-taxonomy work only.",
        "They are not validated reconstruction training datasets.",
        "No milestone should start training/reconstruction from them unless the milestone premise explicitly states this risk.",
        "```",
        "",
        "Artifacts:",
        "",
        "```text",
        str(csv_path),
        str(figure_path),
        "```",
        "",
        "Visual/VLM notes:",
        "",
        "```text",
        visual_notes,
        "```",
        "",
        "Variant summary:",
        "",
        "| variant | samples | min views | mean views | missing refs | stale abs refs | roles | candidate gate | training gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary:
        roles = (
            f"id:{row['identity_supervision']}, geom:{row['geometry_only']}, "
            f"uniform:{row['uniform_rgb']}"
        )
        lines.append(
            f"| {row['variant']} | {row['samples_present']}/{row['samples_expected']} | "
            f"{row['min_views']} | {row['mean_views']} | {row['missing_file_refs']} | "
            f"{row['stale_absolute_refs']} | {roles} | {row['candidate_gate_verdict']} | "
            f"{row['training_gate_verdict']} |"
        )
    lines.extend(
        [
            "",
            "Required before the next milestone:",
            "",
            "```text",
            "1. State the experimental premise in falsifiable terms.",
            "2. Run this data audit gate and publish CSV/MD/PNG outputs.",
            "3. If the gate only passes for diagnostics, do not describe candidates as training data.",
            "4. If reconstruction training is attempted, add a separate positive-control or manual-quality gate.",
            "5. Record any blocked or warning state in MILESTONES.md before running GPU jobs.",
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def make_figure(path: Path, rows: list[dict[str, Any]], expected_samples: list[str]) -> None:
    variants = sorted({str(row["variant"]) for row in rows})
    cell_w = 86
    cell_h = 42
    left = 220
    top = 70
    width = left + len(expected_samples) * cell_w + 30
    height = top + len(variants) * cell_h + 70
    image = Image.new("RGB", (width, height), (246, 246, 246))
    draw = ImageDraw.Draw(image)
    font = choose_font(12)
    small = choose_font(10)
    draw.text((12, 12), "Data audit gate: candidate views per sample", fill=(20, 20, 20), font=font)
    draw.text((12, 34), "Green is diagnostic-usable; amber has warnings; red is blocked/missing.", fill=(70, 70, 70), font=small)
    for col, sample in enumerate(expected_samples):
        label = sample.replace("web_", "").replace("_", "\n")
        draw.multiline_text((left + col * cell_w + 4, top - 42), label, fill=(40, 40, 40), font=small, spacing=0)
    row_map = {(str(row["variant"]), str(row["sample_id"])): row for row in rows}
    for ridx, variant in enumerate(variants):
        y = top + ridx * cell_h
        draw.text((12, y + 12), variant, fill=(25, 25, 25), font=small)
        for col, sample in enumerate(expected_samples):
            x = left + col * cell_w
            row = row_map.get((variant, sample))
            if row is None:
                color = (210, 70, 70)
                text = "NA"
            else:
                status = str(row["candidate_gate_status"])
                if status == "blocked":
                    color = (210, 70, 70)
                elif status == "pass_with_warnings":
                    color = (226, 177, 78)
                else:
                    color = (100, 174, 112)
                text = str(row["view_count"])
            draw.rectangle((x, y, x + cell_w - 4, y + cell_h - 6), fill=color, outline=(240, 240, 240))
            draw.text((x + 34, y + 11), text, fill=(0, 0, 0), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("experiments/inputs/first10/manifest.csv"))
    parser.add_argument("--candidate-root", type=Path, default=Path("experiments/downstream_datasets"))
    parser.add_argument("--variants", nargs="*", default=None)
    parser.add_argument("--milestone", default="G15")
    parser.add_argument(
        "--premise",
        default=(
            "first10 pseudo-view candidate pools are usable for diagnostic "
            "failure taxonomy, but are not validated reconstruction training data"
        ),
    )
    parser.add_argument("--min-candidate-views", type=int, default=2)
    parser.add_argument("--visual-verdict", default="MANUAL_REVIEW_REQUIRED")
    parser.add_argument(
        "--visual-notes",
        default="Generated candidate PNGs still require VLM/manual visual inspection before reconstruction.",
    )
    parser.add_argument("--output-csv", type=Path, default=Path("experiments/metrics/first10_candidate_pool_audit_gate_20260519.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/first10_candidate_pool_audit_gate_20260519.md"))
    parser.add_argument("--figure", type=Path, default=Path("experiments/figures/first10_candidate_pool_audit_gate_20260519.png"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    expected_samples, groups = manifest_maps(repo / args.manifest)
    all_rows: list[dict[str, Any]] = []
    for variant_dir in variant_dirs(repo / args.candidate_root, args.variants):
        all_rows.extend(
            audit_variant(
                repo=repo,
                variant_dir=variant_dir,
                expected_samples=expected_samples,
                groups=groups,
                min_candidate_views=args.min_candidate_views,
            )
        )
    fieldnames = [
        "variant",
        "sample_id",
        "group",
        "metadata_exists",
        "semantic_type",
        "validated_training_dataset",
        "view_count",
        "candidate_view_count",
        "identity_supervision",
        "geometry_only",
        "identity_reject",
        "mask_reject",
        "uniform_rgb",
        "trusted_accepted",
        "mask_accepted",
        "mean_mask_coverage",
        "mean_trusted_score",
        "mean_reliability_score",
        "mean_identity_cosine",
        "missing_file_refs",
        "stale_absolute_refs",
        "candidate_gate_status",
        "training_gate_status",
        "notes",
    ]
    write_csv(repo / args.output_csv, all_rows, fieldnames)
    summary = summarize_by_variant(all_rows)
    write_markdown(
        path=repo / args.output_md,
        milestone=args.milestone,
        premise=args.premise,
        visual_verdict=args.visual_verdict,
        visual_notes=args.visual_notes,
        csv_path=args.output_csv,
        figure_path=args.figure,
        summary=summary,
    )
    make_figure(repo / args.figure, all_rows, expected_samples)
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.figure}")


if __name__ == "__main__":
    main()
