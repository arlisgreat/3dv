#!/usr/bin/env python3
"""Evaluate the G15 head-cutout Zero123++ recovery probe."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from evaluate_pseudo_views import (
    VIEW_COLUMNS,
    budget_figure,
    budget_rows,
    fit_on_canvas,
    load_image,
    summary_rows,
    view_records,
    write_csv,
)


def grid_figure(repo: Path, records: list[dict[str, str]], out_path: Path) -> None:
    samples = sorted({record["sample_id"] for record in records})
    input_w = 112
    grid_w = 228
    grid_h = 342
    label_h = 28
    pad = 10
    row_h = grid_h + label_h + pad
    sheet = Image.new("RGB", (pad + input_w + grid_w + 3 * pad, pad + len(samples) * row_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, sample_id in enumerate(samples):
        y = pad + idx * row_h
        record = next(r for r in records if r["sample_id"] == sample_id)
        input_path = repo / record["view_file"]
        input_path = input_path.parent / "input_square.png"
        grid_path = input_path.parent / "grid.png"
        draw.text((pad, y), sample_id, fill=(0, 0, 0))
        sheet.paste(fit_on_canvas(load_image(input_path), (input_w, input_w)), (pad, y + label_h))
        x = pad + input_w + pad
        draw.text((x, y), "head_cutout75", fill=(0, 0, 0))
        sheet.paste(load_image(grid_path).resize((grid_w, grid_h), Image.Resampling.LANCZOS), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def write_observations(path: Path, summary: list[dict[str, str]], *, run_root: str, tag: str) -> None:
    good_counts = [int(row["good_view_count_score_ge_60"]) for row in summary]
    mean_scores = [float(row["mean_reliability_score"]) for row in summary]
    lines = [
        "# G15 Head-Cutout Zero123++ Probe",
        "",
        "Date: 2026-05-19",
        "",
        "Purpose:",
        "",
        "```text",
        "Test whether tighter gray-background head cutouts recover the pseudo-view candidate premise.",
        "This is a generation/candidate audit only; it does not approve reconstruction training.",
        "```",
        "",
        "Artifacts:",
        "",
        "```text",
        run_root,
        f"experiments/metrics/pseudo_view_reliability_first10_head_cutout_steps75{tag}.csv",
        f"experiments/metrics/view_budget_selection_first10_head_cutout_steps75{tag}.csv",
        f"experiments/metrics/pseudo_view_summary_first10_head_cutout_steps75{tag}.csv",
        f"experiments/figures/zero123plus_first10_head_cutout_steps75{tag}_grids.png",
        f"experiments/figures/view_budget_selection_head_cutout75{tag}_budget4.png",
        "```",
        "",
        "Metric summary:",
        "",
        "```text",
        f"mean reliability over samples: {np.mean(mean_scores):.3f}",
        f"mean views/sample with score >= 60: {np.mean(good_counts):.2f}",
        "```",
        "",
        "Gate note:",
        "",
        "```text",
        "Use the PNG grid and budget figures for VLM/manual inspection. The old metric",
        "is known to be weak, so a high score alone is not a pass.",
        "```",
        "",
        "| sample | group | mean score | good views >=60 | face views | dominant failures |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary:
        lines.append(
            f"| {row['sample_id']} | {row['group']} | {row['mean_reliability_score']} | "
            f"{row['good_view_count_score_ge_60']} | {row['face_view_count']} | {row['dominant_failure_labels']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="experiments/inputs/first10/head_cutouts_manifest.csv")
    parser.add_argument("--run-root", default="experiments/pseudo_views/zero123plus_first10_head_cutout_steps75")
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    records = view_records(repo, repo / args.manifest, [("head_cutout75", repo / args.run_root, 75)])
    budgets = budget_rows(records)
    summary = summary_rows(records)
    tag = args.tag
    write_csv(repo / f"experiments/metrics/pseudo_view_reliability_first10_head_cutout_steps75{tag}.csv", records, VIEW_COLUMNS)
    write_csv(
        repo / f"experiments/metrics/view_budget_selection_first10_head_cutout_steps75{tag}.csv",
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
        repo / f"experiments/metrics/pseudo_view_summary_first10_head_cutout_steps75{tag}.csv",
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
    grid_figure(repo, records, repo / f"experiments/figures/zero123plus_first10_head_cutout_steps75{tag}_grids.png")
    budget_figure(
        repo,
        budgets,
        repo / f"experiments/figures/view_budget_selection_head_cutout75{tag}_budget4.png",
        run="head_cutout75",
        budget="4",
    )
    write_observations(
        repo / f"experiments/metrics/head_cutout_probe_observations_20260519{tag}.md",
        summary,
        run_root=args.run_root,
        tag=tag,
    )
    print(f"view_records={len(records)}")
    print(f"budget_rows={len(budgets)}")
    print(f"summary_rows={len(summary)}")


if __name__ == "__main__":
    main()
