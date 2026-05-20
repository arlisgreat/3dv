#!/usr/bin/env python3
"""Build the corrected first10 pseudo-view failure taxonomy artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


CORRECTED_ROOT = "experiments/pseudo_views/zero123plus_first10_head_cutout_steps75_resplit3x2"
LABELS = {
    "identity_drift",
    "geometry_drift",
    "viewpoint_pose_error",
    "card_or_billboard_artifact",
    "source_frame_or_background_leakage",
    "accessory_or_occlusion_instability",
    "hair_or_head_boundary_instability",
    "texture_style_drift",
    "face_detector_miss_nonfrontal",
    "low_information_or_ambiguous",
    "preprocess_or_split_artifact",
}
ROLE_COLORS = {
    "identity_supervision": (96, 174, 106),
    "geometry_only": (229, 176, 72),
    "reject": (210, 82, 82),
}
ABBR = {
    "identity_drift": "ID",
    "geometry_drift": "GEO",
    "viewpoint_pose_error": "POSE",
    "card_or_billboard_artifact": "CARD",
    "source_frame_or_background_leakage": "SRC",
    "accessory_or_occlusion_instability": "ACC",
    "hair_or_head_boundary_instability": "HAIR",
    "texture_style_drift": "STYLE",
    "face_detector_miss_nonfrontal": "FACE",
    "low_information_or_ambiguous": "LOW",
    "preprocess_or_split_artifact": "SPLIT",
}


PRIMARY_FAMILIES = {
    "web_clean_frontal_01": ("mostly_coherent_head_orbit", "best corrected first10 orbit, still diagnostic-only"),
    "web_clean_frontal_02": ("identity_drift_dominant", "side/profile identity and hair silhouette drift"),
    "web_clean_frontal_03": ("geometry_or_card_artifact_dominant", "beard/hair/neck geometry changes across orbit"),
    "web_complex_hair_01": ("style_or_source_artifact_dominant", "monochrome style and head-boundary drift dominate"),
    "web_complex_hair_02": ("accessory_occlusion_dominant", "cap, beard, glasses, and neck remain fragile"),
    "web_glasses_01": ("accessory_occlusion_dominant", "clothing/headwrap/glasses produce card and source-support artifacts"),
    "web_glasses_02": ("style_or_source_artifact_dominant", "grayscale glasses portrait becomes stylized and low-identity in back/profile views"),
    "web_mild_side_01": ("style_or_source_artifact_dominant", "line-art style transfer dominates all views"),
    "web_mild_side_02": ("geometry_or_card_artifact_dominant", "oval source-frame/card artifact dominates the orbit"),
    "web_occlusion_lowq_01": ("accessory_occlusion_dominant", "balaclava/hat/coat support makes identity supervision unsafe"),
}


ANNOTATIONS: dict[str, dict[int, tuple[str, int, list[str], str]]] = {
    "web_clean_frontal_01": {
        0: ("identity_supervision", 1, ["geometry_drift"], "near-frontal identity mostly coherent, neck/shoulder simplified"),
        1: ("geometry_only", 2, ["face_detector_miss_nonfrontal", "geometry_drift"], "profile has plausible head but weak identity check"),
        2: ("geometry_only", 2, ["face_detector_miss_nonfrontal", "geometry_drift"], "rear-oblique is useful only for coarse geometry"),
        3: ("geometry_only", 2, ["face_detector_miss_nonfrontal", "geometry_drift"], "rear view plausible but identity unavailable"),
        4: ("geometry_only", 2, ["face_detector_miss_nonfrontal", "geometry_drift"], "opposite rear view remains geometry-only"),
        5: ("identity_supervision", 1, ["geometry_drift"], "near-frontal identity coherent enough for diagnostics"),
    },
    "web_clean_frontal_02": {
        0: ("identity_supervision", 1, ["identity_drift", "hair_or_head_boundary_instability"], "near-frontal cues survive with expression/hair drift"),
        1: ("geometry_only", 2, ["identity_drift", "geometry_drift", "face_detector_miss_nonfrontal"], "profile changes face proportions"),
        2: ("geometry_only", 2, ["identity_drift", "geometry_drift", "face_detector_miss_nonfrontal"], "rear-oblique is geometry-only"),
        3: ("geometry_only", 2, ["hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "back hair is plausible but not identity evidence"),
        4: ("geometry_only", 2, ["hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "opposite back view changes hair mass"),
        5: ("geometry_only", 2, ["identity_drift", "hair_or_head_boundary_instability"], "front-oblique face drifts from input"),
    },
    "web_clean_frontal_03": {
        0: ("identity_supervision", 1, ["geometry_drift", "hair_or_head_boundary_instability"], "front-oblique preserves identity with stylized neck support"),
        1: ("geometry_only", 2, ["geometry_drift", "hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "profile head/hair shape changes"),
        2: ("geometry_only", 2, ["geometry_drift", "source_frame_or_background_leakage", "face_detector_miss_nonfrontal"], "rear-oblique jacket/neck support dominates"),
        3: ("geometry_only", 2, ["geometry_drift", "hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "back view loses identity and changes hair"),
        4: ("geometry_only", 2, ["geometry_drift", "hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "opposite back/profile has unstable skull shape"),
        5: ("identity_supervision", 1, ["geometry_drift"], "near-frontal identity mostly preserved but still stylized"),
    },
    "web_complex_hair_01": {
        0: ("geometry_only", 2, ["identity_drift", "texture_style_drift", "hair_or_head_boundary_instability"], "monochrome stylization changes identity cues"),
        1: ("geometry_only", 2, ["geometry_drift", "texture_style_drift", "face_detector_miss_nonfrontal"], "profile is a stylized shape, not identity evidence"),
        2: ("reject", 3, ["geometry_drift", "hair_or_head_boundary_instability", "low_information_or_ambiguous"], "rear-oblique lacks useful face and has unstable boundary"),
        3: ("reject", 3, ["geometry_drift", "low_information_or_ambiguous", "texture_style_drift"], "back view is low-information support"),
        4: ("geometry_only", 2, ["geometry_drift", "hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "profile/back shape changed"),
        5: ("identity_supervision", 1, ["texture_style_drift", "hair_or_head_boundary_instability"], "front view preserves strongest identity cues"),
    },
    "web_complex_hair_02": {
        0: ("identity_supervision", 1, ["accessory_or_occlusion_instability"], "cap/beard/glasses mostly preserved"),
        1: ("geometry_only", 2, ["accessory_or_occlusion_instability", "face_detector_miss_nonfrontal"], "profile preserves coarse head but identity weak"),
        2: ("geometry_only", 2, ["accessory_or_occlusion_instability", "hair_or_head_boundary_instability"], "rear-oblique cap/neck support fragile"),
        3: ("geometry_only", 2, ["accessory_or_occlusion_instability", "low_information_or_ambiguous"], "back view lacks identity evidence"),
        4: ("geometry_only", 2, ["accessory_or_occlusion_instability", "geometry_drift"], "opposite rear has beard/neck instability"),
        5: ("identity_supervision", 1, ["accessory_or_occlusion_instability"], "front-oblique retains most identity/accessory cues"),
    },
    "web_glasses_01": {
        0: ("geometry_only", 2, ["accessory_or_occlusion_instability", "source_frame_or_background_leakage"], "near-front still has clothing/headwrap support"),
        1: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "accessory_or_occlusion_instability"], "profile is supported by garment/card structure"),
        2: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "geometry_drift"], "rear-oblique is fragmented body/card support"),
        3: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "geometry_drift"], "back view contains split body/garment artifact"),
        4: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "accessory_or_occlusion_instability"], "opposite rear/profile is a card-like fragment"),
        5: ("geometry_only", 2, ["accessory_or_occlusion_instability", "identity_drift"], "front-oblique keeps cues but headwear/identity drift"),
    },
    "web_glasses_02": {
        0: ("identity_supervision", 1, ["texture_style_drift", "accessory_or_occlusion_instability"], "front-oblique glasses and hair mostly coherent"),
        1: ("geometry_only", 2, ["texture_style_drift", "hair_or_head_boundary_instability", "face_detector_miss_nonfrontal"], "profile is stylized and identity weak"),
        2: ("reject", 3, ["low_information_or_ambiguous", "hair_or_head_boundary_instability", "texture_style_drift"], "rear-oblique is low-information hair slab"),
        3: ("geometry_only", 2, ["low_information_or_ambiguous", "hair_or_head_boundary_instability"], "back view lacks face and has weak geometry"),
        4: ("geometry_only", 2, ["hair_or_head_boundary_instability", "accessory_or_occlusion_instability"], "opposite profile keeps glasses weakly"),
        5: ("identity_supervision", 1, ["texture_style_drift", "accessory_or_occlusion_instability"], "front view preserves strongest identity cues"),
    },
    "web_mild_side_01": {
        0: ("geometry_only", 2, ["texture_style_drift", "identity_drift"], "line-art style changes identity evidence"),
        1: ("geometry_only", 2, ["texture_style_drift", "geometry_drift", "face_detector_miss_nonfrontal"], "profile is stylized but coarse head-like"),
        2: ("geometry_only", 2, ["texture_style_drift", "geometry_drift", "hair_or_head_boundary_instability"], "rear-oblique remains drawing-like"),
        3: ("geometry_only", 2, ["texture_style_drift", "low_information_or_ambiguous"], "back view is low-information drawing"),
        4: ("geometry_only", 2, ["texture_style_drift", "geometry_drift"], "opposite profile is stylized"),
        5: ("geometry_only", 2, ["texture_style_drift", "identity_drift"], "front view retains pose but not reliable identity"),
    },
    "web_mild_side_02": {
        0: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "texture_style_drift"], "oval source frame is rotated with the subject"),
        1: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "viewpoint_pose_error"], "thin oval card side view"),
        2: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage"], "oval frame dominates rear-oblique"),
        3: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage"], "card-like oval remains"),
        4: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "viewpoint_pose_error"], "thin card is unusable"),
        5: ("reject", 3, ["card_or_billboard_artifact", "source_frame_or_background_leakage", "identity_drift"], "front view still framed as source oval"),
    },
    "web_occlusion_lowq_01": {
        0: ("geometry_only", 2, ["accessory_or_occlusion_instability", "low_information_or_ambiguous"], "face is visible but balaclava dominates identity"),
        1: ("geometry_only", 2, ["accessory_or_occlusion_instability", "face_detector_miss_nonfrontal"], "profile is plausible but occluded"),
        2: ("geometry_only", 2, ["accessory_or_occlusion_instability", "source_frame_or_background_leakage"], "rear-oblique coat/headwear support dominates"),
        3: ("geometry_only", 2, ["accessory_or_occlusion_instability", "low_information_or_ambiguous"], "back view is useful only for coarse occluder geometry"),
        4: ("geometry_only", 2, ["accessory_or_occlusion_instability", "source_frame_or_background_leakage"], "opposite rear has coat support"),
        5: ("geometry_only", 2, ["accessory_or_occlusion_instability", "low_information_or_ambiguous"], "front view is too occluded for identity supervision"),
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def budget4_selection(path: Path) -> dict[str, set[int]]:
    selections: dict[str, set[int]] = {}
    for row in read_csv(path):
        if int(row["budget"]) != 4:
            continue
        selections[row["sample_id"]] = {
            int(value) for value in row["selected_view_indices"].split(";") if value != ""
        }
    return selections


def validate_metadata(repo: Path, sample_ids: list[str]) -> None:
    for sample_id in sample_ids:
        metadata = load_json(repo / CORRECTED_ROOT / f"{sample_id}_steps75" / "metadata.json")
        grid = metadata.get("grid") or {}
        if grid.get("rows") != 3 or grid.get("cols") != 2:
            raise ValueError(f"{sample_id} grid is not 3x2: {grid}")


def build_rows(repo: Path, reliability_csv: Path, budget_csv: Path) -> list[dict[str, Any]]:
    reliability_rows = read_csv(reliability_csv)
    if len(reliability_rows) != 60:
        raise ValueError(f"Expected 60 corrected first10 rows, got {len(reliability_rows)}")
    selected = budget4_selection(budget_csv)
    sample_ids = sorted({row["sample_id"] for row in reliability_rows})
    validate_metadata(repo, sample_ids)
    output_rows: list[dict[str, Any]] = []
    for row in reliability_rows:
        sample_id = row["sample_id"]
        view_index = int(row["view_index"])
        if CORRECTED_ROOT not in row["view_file"]:
            raise ValueError(f"Non-corrected view path: {row['view_file']}")
        role, severity, labels, notes = ANNOTATIONS[sample_id][view_index]
        unknown = set(labels) - LABELS
        if unknown:
            raise ValueError(f"Unknown labels for {sample_id} view {view_index}: {sorted(unknown)}")
        primary_family, primary_notes = PRIMARY_FAMILIES[sample_id]
        output_rows.append(
            {
                "sample_id": sample_id,
                "group": row["group"],
                "view_index": view_index,
                "azimuth": row["azimuth"],
                "elevation": row["elevation"],
                "view_file": row["view_file"],
                "selected_budget4": view_index in selected.get(sample_id, set()),
                "metric_failure_labels": row.get("failure_labels", ""),
                "manual_failure_labels": ";".join(labels),
                "manual_role": role,
                "severity": severity,
                "sample_primary_family": primary_family,
                "sample_primary_notes": primary_notes,
                "reliability_score": row["reliability_score"],
                "notes": notes,
            }
        )
    return output_rows


def wrap_text(text: str, max_len: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(part) for part in current) + len(current) + len(word) > max_len and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def make_figure(repo: Path, rows: list[dict[str, Any]], output: Path) -> None:
    by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_sample[str(row["sample_id"])].append(row)
    sample_order = sorted(by_sample.keys())
    thumb = 112
    label_h = 46
    left_w = 160
    header_h = 34
    row_h = thumb + label_h + 18
    width = left_w + 6 * thumb + 24
    height = header_h + len(sample_order) * row_h + 20
    image = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(image)
    font = choose_font(12)
    small = choose_font(9)
    title = "G18 corrected 3x2 first10 pseudo-view failure taxonomy"
    draw.text((10, 8), title, fill=(20, 20, 20), font=font)
    for r, sample_id in enumerate(sample_order):
        y = header_h + r * row_h
        input_path = repo / "experiments" / "inputs" / "first10" / "head_cutouts" / f"{sample_id}.png"
        input_img = Image.open(input_path).convert("RGB").resize((96, 96), Image.Resampling.LANCZOS)
        draw.text((8, y), sample_id, fill=(20, 20, 20), font=small)
        family = PRIMARY_FAMILIES[sample_id][0].replace("_dominant", "").replace("_", " ")
        for i, line in enumerate(wrap_text(family, 22)[:2]):
            draw.text((8, y + 14 + i * 11), line, fill=(70, 70, 70), font=small)
        image.paste(input_img, (8, y + label_h))
        for row in sorted(by_sample[sample_id], key=lambda item: int(item["view_index"])):
            idx = int(row["view_index"])
            x = left_w + idx * thumb
            view = Image.open(repo / str(row["view_file"])).convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
            image.paste(view, (x, y + label_h))
            color = ROLE_COLORS[str(row["manual_role"])]
            draw.rectangle((x, y + label_h, x + thumb - 1, y + label_h + 14), fill=color)
            labels = str(row["manual_failure_labels"]).split(";")
            label_text = ",".join(ABBR[label] for label in labels[:3])
            if len(labels) > 3:
                label_text += "+"
            selected = "*" if row["selected_budget4"] else ""
            text = f"v{idx}{selected} s{row['severity']} {label_text}"
            draw.text((x + 2, y + label_h + 2), text, fill=(0, 0, 0), font=small)
            role_short = {"identity_supervision": "ID", "geometry_only": "GEOM", "reject": "REJ"}[str(row["manual_role"])]
            draw.text((x + 2, y + label_h + thumb + 2), role_short, fill=(30, 30, 30), font=small)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def write_md(path: Path, rows: list[dict[str, Any]], csv_path: Path, figure_path: Path) -> None:
    label_counts = Counter()
    role_counts = Counter(str(row["manual_role"]) for row in rows)
    family_counts = Counter(str(row["sample_primary_family"]) for row in rows[::6])
    group_label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    budget_selected = [row for row in rows if row["selected_budget4"]]
    budget_rejects = [row for row in budget_selected if row["manual_role"] == "reject"]
    severe_budget = [row for row in budget_selected if int(row["severity"]) >= 3]
    for row in rows:
        for label in str(row["manual_failure_labels"]).split(";"):
            label_counts[label] += 1
            group_label_counts[str(row["group"])][label] += 1

    lines = [
        "# G18 Corrected First10 Failure Taxonomy",
        "",
        "Date: 2026-05-20",
        "",
        "Gate verdict:",
        "",
        "```text",
        "PASS_DIAGNOSTIC_ONLY",
        "BLOCKED_RECONSTRUCTION_TRAINING",
        "```",
        "",
        "Premise:",
        "",
        "```text",
        "Only corrected Zero123++ 3x2 head-cutout pseudo views are audited here.",
        "The taxonomy explains pseudo-view failures; it does not validate web",
        "first10 as reconstruction-training data.",
        "```",
        "",
        "Artifacts:",
        "",
        "```text",
        str(csv_path),
        str(figure_path),
        "experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png",
        "experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png",
        "```",
        "",
        "Role counts:",
        "",
        "| role | count |",
        "| --- | ---: |",
    ]
    for role, count in sorted(role_counts.items()):
        lines.append(f"| {role} | {count} |")
    lines.extend(["", "Failure label counts:", "", "| label | count |", "| --- | ---: |"])
    for label, count in label_counts.most_common():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "Sample primary families:", "", "| family | samples |", "| --- | ---: |"])
    for family, count in sorted(family_counts.items()):
        lines.append(f"| {family} | {count} |")
    lines.extend(
        [
            "",
            "Budget4 audit:",
            "",
            "```text",
            f"selected_views: {len(budget_selected)}",
            f"selected_reject_views: {len(budget_rejects)}",
            f"selected_severity3_views: {len(severe_budget)}",
            "Reliability-selected budget4 still contains manual reject/severe views,",
            "so automatic ranking cannot certify reconstruction supervision.",
            "```",
            "",
            "Group-level dominant labels:",
            "",
            "| group | dominant labels |",
            "| --- | --- |",
        ]
    )
    for group, counts in sorted(group_label_counts.items()):
        dominant = ", ".join(f"{label}:{count}" for label, count in counts.most_common(4))
        lines.append(f"| {group} | {dominant} |")
    lines.extend(
        [
            "",
            "Allowed claim:",
            "",
            "```text",
            "The corrected first10 pseudo views reveal recurring identity, geometry,",
            "accessory, style, and card/source-frame failures. Budgeted candidate",
            "selection improves 2D hygiene in some cases but does not make the",
            "candidate pool valid reconstruction supervision.",
            "```",
            "",
            "Disallowed claim:",
            "",
            "```text",
            "Do not claim that corrected first10 pseudo views are a valid RI3D training",
            "dataset or that CLIP/reliability/budget4 proves 3D reconstruction quality.",
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reliability-csv",
        type=Path,
        default=Path("experiments/metrics/pseudo_view_reliability_first10_head_cutout_steps75_resplit3x2.csv"),
    )
    parser.add_argument(
        "--budget-csv",
        type=Path,
        default=Path("experiments/metrics/view_budget_selection_first10_head_cutout_steps75_resplit3x2.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.md"),
    )
    parser.add_argument(
        "--output-figure",
        type=Path,
        default=Path("experiments/figures/first10_failure_taxonomy_resplit3x2_20260520.png"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    rows = build_rows(repo, args.reliability_csv, args.budget_csv)
    fieldnames = [
        "sample_id",
        "group",
        "view_index",
        "azimuth",
        "elevation",
        "view_file",
        "selected_budget4",
        "metric_failure_labels",
        "manual_failure_labels",
        "manual_role",
        "severity",
        "sample_primary_family",
        "sample_primary_notes",
        "reliability_score",
        "notes",
    ]
    write_csv(args.output_csv, rows, fieldnames)
    make_figure(repo, rows, args.output_figure)
    write_md(args.output_md, rows, args.output_csv, args.output_figure)
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.output_figure}")


if __name__ == "__main__":
    main()
