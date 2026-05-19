#!/usr/bin/env python3
"""Evaluate raw portrait inputs against subject cutout inputs for Zero123++."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from evaluate_pseudo_views import (
    VIEW_COLUMNS,
    budget_rows,
    fit_on_canvas,
    load_image,
    summary_rows,
    view_records,
    write_csv,
)


def compare_rows(summary: list[dict[str, str]]) -> list[dict[str, str]]:
    by_sample: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in summary:
        by_sample[row["sample_id"]][row["run"]] = row
    rows = []
    for sample_id, runs in sorted(by_sample.items()):
        if "raw75" not in runs or "cutout75" not in runs:
            continue
        raw = runs["raw75"]
        cutout = runs["cutout75"]
        delta_mean = float(cutout["mean_reliability_score"]) - float(raw["mean_reliability_score"])
        delta_good = int(cutout["good_view_count_score_ge_60"]) - int(raw["good_view_count_score_ge_60"])
        delta_faces = int(cutout["face_view_count"]) - int(raw["face_view_count"])
        if delta_good > 0 or delta_mean > 5:
            verdict = "cutout_helped"
        elif delta_good < 0 or delta_mean < -5:
            verdict = "cutout_hurt"
        else:
            verdict = "cutout_neutral"
        rows.append(
            {
                "sample_id": sample_id,
                "group": raw["group"],
                "mean_score_raw75": raw["mean_reliability_score"],
                "mean_score_cutout75": cutout["mean_reliability_score"],
                "delta_mean_score": f"{delta_mean:.3f}",
                "good_views_raw75": raw["good_view_count_score_ge_60"],
                "good_views_cutout75": cutout["good_view_count_score_ge_60"],
                "delta_good_views": str(delta_good),
                "face_views_raw75": raw["face_view_count"],
                "face_views_cutout75": cutout["face_view_count"],
                "delta_face_views": str(delta_faces),
                "verdict": verdict,
            }
        )
    return rows


def comparison_figure(repo: Path, records: list[dict[str, str]], out_path: Path) -> None:
    samples = sorted({r["sample_id"] for r in records})
    input_w = 112
    grid_w = 228
    grid_h = 342
    label_h = 28
    pad = 10
    row_h = grid_h + label_h + pad
    sheet = Image.new("RGB", (pad + input_w + 2 * grid_w + 4 * pad, pad + len(samples) * row_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, sample_id in enumerate(samples):
        y = pad + idx * row_h
        raw = next(r for r in records if r["sample_id"] == sample_id and r["run"] == "raw75")
        cutout = next(r for r in records if r["sample_id"] == sample_id and r["run"] == "cutout75")
        raw_input = repo / raw["view_file"]
        raw_input = raw_input.parent / "input_square.png"
        raw_grid = raw_input.parent / "grid.png"
        cutout_grid = repo / cutout["view_file"]
        cutout_input = cutout_grid.parent / "input_square.png"
        cutout_grid = cutout_grid.parent / "grid.png"
        draw.text((pad, y), sample_id, fill=(0, 0, 0))
        sheet.paste(fit_on_canvas(load_image(cutout_input), (input_w, input_w)), (pad, y + label_h))
        x = pad + input_w + pad
        draw.text((x, y), "raw75", fill=(0, 0, 0))
        sheet.paste(load_image(raw_grid).resize((grid_w, grid_h), Image.Resampling.LANCZOS), (x, y + label_h))
        x += grid_w + pad
        draw.text((x, y), "cutout75", fill=(0, 0, 0))
        sheet.paste(load_image(cutout_grid).resize((grid_w, grid_h), Image.Resampling.LANCZOS), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def budget_figure(repo: Path, budgets: list[dict[str, str]], out_path: Path, run: str = "cutout75", budget: str = "4") -> None:
    selected = [row for row in budgets if row["run"] == run and row["budget"] == budget]
    thumb_w, thumb_h = 112, 168
    pad, label_h = 10, 26
    cols = int(budget) + 1
    sheet = Image.new(
        "RGB",
        (pad + cols * (thumb_w + pad), pad + len(selected) * (thumb_h + label_h + pad)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for r, row in enumerate(selected):
        y = pad + r * (thumb_h + label_h + pad)
        files = row["selected_view_files"].split(";")
        input_path = repo / files[0]
        input_path = input_path.parent / "input_square.png"
        draw.text((pad, y), row["sample_id"], fill=(0, 0, 0))
        sheet.paste(fit_on_canvas(load_image(input_path), (thumb_w, thumb_h)), (pad, y + label_h))
        for c, file in enumerate(files, 1):
            x = pad + c * (thumb_w + pad)
            sheet.paste(fit_on_canvas(load_image(repo / file), (thumb_w, thumb_h), bg=(245, 245, 245)), (x, y + label_h))
            draw.text((x, y), f"v{file.split('/view_')[-1][:2]}", fill=(0, 0, 0))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    raw = view_records(
        repo,
        repo / "experiments/inputs/first10/manifest.csv",
        [("raw75", repo / "experiments/pseudo_views/zero123plus_first10_steps75", 75)],
    )
    cutout = view_records(
        repo,
        repo / "experiments/inputs/first10/cutouts_manifest.csv",
        [("cutout75", repo / "experiments/pseudo_views/zero123plus_first10_cutout_steps75", 75)],
    )
    records = raw + cutout
    budgets = budget_rows(records)
    summary = summary_rows(records)
    comparison = compare_rows(summary)

    write_csv(repo / "experiments/metrics/pseudo_view_reliability_raw_vs_cutout_steps75.csv", records, VIEW_COLUMNS)
    write_csv(
        repo / "experiments/metrics/view_budget_selection_raw_vs_cutout_steps75.csv",
        budgets,
        [
            "sample_id",
            "group",
            "run",
            "steps",
            "budget",
            "selected_view_indices",
            "selected_view_files",
            "mean_reliability_score",
            "min_reliability_score",
            "face_view_count",
            "failure_labels",
        ],
    )
    write_csv(
        repo / "experiments/metrics/pseudo_view_summary_raw_vs_cutout_steps75.csv",
        summary,
        [
            "sample_id",
            "group",
            "run",
            "steps",
            "mean_reliability_score",
            "best_reliability_score",
            "good_view_count_score_ge_60",
            "face_view_count",
            "dominant_failure_labels",
        ],
    )
    write_csv(
        repo / "experiments/metrics/raw_vs_cutout_comparison_steps75.csv",
        comparison,
        [
            "sample_id",
            "group",
            "mean_score_raw75",
            "mean_score_cutout75",
            "delta_mean_score",
            "good_views_raw75",
            "good_views_cutout75",
            "delta_good_views",
            "face_views_raw75",
            "face_views_cutout75",
            "delta_face_views",
            "verdict",
        ],
    )
    comparison_figure(repo, records, repo / "experiments/figures/zero123plus_first10_raw_vs_cutout_steps75_grids.png")
    budget_figure(repo, budgets, repo / "experiments/figures/view_budget_selection_cutout75_budget4.png")
    print(f"view_records={len(records)}")
    print(f"budget_rows={len(budgets)}")
    print(f"summary_rows={len(summary)}")
    print(f"comparison_rows={len(comparison)}")
    print(f"mean_delta={np.mean([float(row['delta_mean_score']) for row in comparison]):.3f}")


if __name__ == "__main__":
    main()
