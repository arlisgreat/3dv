#!/usr/bin/env python3
"""Evaluate pseudo-view reliability and derive view-budget selections."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageStat


VIEW_COLUMNS = [
    "sample_id",
    "group",
    "run",
    "steps",
    "view_index",
    "view_file",
    "azimuth",
    "elevation",
    "sha256",
    "bytes",
    "nonblank",
    "foreground_area_ratio",
    "foreground_bbox_area_ratio",
    "foreground_center_offset",
    "face_count",
    "largest_face_area_ratio",
    "hist_corr_to_input",
    "reliability_score",
    "failure_labels",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def foreground_stats(image: Image.Image) -> tuple[float, float, float, np.ndarray]:
    arr = np.asarray(image).astype(np.int16)
    bg = np.array([127, 127, 127], dtype=np.int16)
    dist = np.linalg.norm(arr - bg, axis=2)
    mask = dist > 22
    area = float(mask.mean())
    if not mask.any():
        return area, 0.0, 1.0, mask
    ys, xs = np.where(mask)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    bbox_area = ((x1 - x0 + 1) * (y1 - y0 + 1)) / float(image.width * image.height)
    cx = (x0 + x1) / 2.0 / image.width
    cy = (y0 + y1) / 2.0 / image.height
    center_offset = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    return area, bbox_area, center_offset, mask


def face_stats(image: Image.Image) -> tuple[int, float]:
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        return 0, 0.0
    faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
    if len(faces) == 0:
        return 0, 0.0
    largest = max(int(w * h) for _, _, w, h in faces)
    return int(len(faces)), largest / float(image.width * image.height)


def hist_corr(a: Image.Image, b: Image.Image) -> float:
    a_arr = cv2.cvtColor(np.asarray(a.resize((128, 128), Image.Resampling.LANCZOS)), cv2.COLOR_RGB2HSV)
    b_arr = cv2.cvtColor(np.asarray(b.resize((128, 128), Image.Resampling.LANCZOS)), cv2.COLOR_RGB2HSV)
    a_hist = cv2.calcHist([a_arr], [0, 1], None, [32, 32], [0, 180, 0, 256])
    b_hist = cv2.calcHist([b_arr], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(a_hist, a_hist)
    cv2.normalize(b_hist, b_hist)
    return float(cv2.compareHist(a_hist, b_hist, cv2.HISTCMP_CORREL))


def reliability(
    group: str,
    nonblank: bool,
    fg_area: float,
    bbox_area: float,
    center_offset: float,
    face_count: int,
    face_area: float,
    corr: float,
) -> tuple[float, list[str]]:
    score = 100.0
    labels: list[str] = []
    if not nonblank:
        score -= 80
        labels.append("blank_or_flat")
    if face_count == 0:
        score -= 28
        labels.append("no_frontal_face_detected")
    elif face_area < 0.015:
        score -= 10
        labels.append("tiny_detected_face")
    if fg_area < 0.06:
        score -= 25
        labels.append("tiny_subject_or_overempty")
    if fg_area > 0.86:
        score -= 20
        labels.append("overfull_foreground")
    if bbox_area > 0.78 and face_count == 0:
        score -= 22
        labels.append("full_photo_or_background_rotation")
    if center_offset > 0.28:
        score -= min(20, center_offset * 45)
        labels.append("off_center_subject")
    if corr < 0.08:
        score -= 18
        labels.append("low_input_style_similarity")
    elif corr < 0.18:
        score -= 8
        labels.append("weak_input_style_similarity")
    if group == "glasses" and face_count == 0:
        labels.append("glasses_identity_risk")
    if group == "complex_hair" and (bbox_area > 0.78 or corr < 0.18):
        labels.append("hair_hallucination_risk")
    if group == "occlusion_lowq" and face_count == 0:
        labels.append("occlusion_identity_risk")
    return max(0.0, min(100.0, score)), labels


def view_records(repo: Path, manifest_path: Path, run_specs: list[tuple[str, Path, int]]) -> list[dict[str, str]]:
    rows = list(csv.DictReader(manifest_path.open("r", newline="", encoding="utf-8")))
    by_id = {row["sample_id"]: row for row in rows}
    records = []
    for run_name, root, steps in run_specs:
        for sample_id, source in by_id.items():
            outdir = root / f"{sample_id}_steps{steps}"
            metadata = json.loads((outdir / "metadata.json").read_text(encoding="utf-8"))
            input_img = load_image(outdir / "input_square.png")
            for view in metadata["views"]:
                path = outdir / view["file"]
                img = load_image(path)
                stat = ImageStat.Stat(img)
                nonblank = max(stat.stddev) > 1.0
                fg_area, bbox_area, center_offset, _ = foreground_stats(img)
                face_count, face_area = face_stats(img)
                corr = hist_corr(input_img, img)
                score, labels = reliability(
                    source["group"], nonblank, fg_area, bbox_area, center_offset, face_count, face_area, corr
                )
                records.append(
                    {
                        "sample_id": sample_id,
                        "group": source["group"],
                        "run": run_name,
                        "steps": str(steps),
                        "view_index": str(view["index"]),
                        "view_file": str(path.relative_to(repo)),
                        "azimuth": str(view["azimuth"]),
                        "elevation": str(view["elevation"]),
                        "sha256": sha256(path),
                        "bytes": str(path.stat().st_size),
                        "nonblank": str(nonblank).lower(),
                        "foreground_area_ratio": f"{fg_area:.6f}",
                        "foreground_bbox_area_ratio": f"{bbox_area:.6f}",
                        "foreground_center_offset": f"{center_offset:.6f}",
                        "face_count": str(face_count),
                        "largest_face_area_ratio": f"{face_area:.6f}",
                        "hist_corr_to_input": f"{corr:.6f}",
                        "reliability_score": f"{score:.3f}",
                        "failure_labels": ";".join(labels),
                    }
                )
    return records


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def budget_rows(records: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[(record["sample_id"], record["run"])].append(record)
    rows = []
    for (sample_id, run), group_records in sorted(grouped.items()):
        ranked = sorted(group_records, key=lambda r: float(r["reliability_score"]), reverse=True)
        for budget in [1, 2, 4, 6]:
            selected = ranked[:budget]
            labels = Counter(label for r in selected for label in r["failure_labels"].split(";") if label)
            rows.append(
                {
                    "sample_id": sample_id,
                    "group": selected[0]["group"],
                    "run": run,
                    "steps": selected[0]["steps"],
                    "budget": str(budget),
                    "selected_view_indices": ";".join(r["view_index"] for r in selected),
                    "selected_view_files": ";".join(r["view_file"] for r in selected),
                    "mean_reliability_score": f"{np.mean([float(r['reliability_score']) for r in selected]):.3f}",
                    "min_reliability_score": f"{min(float(r['reliability_score']) for r in selected):.3f}",
                    "face_view_count": str(sum(int(r["face_count"]) > 0 for r in selected)),
                    "failure_labels": ";".join(sorted(labels)),
                }
            )
    return rows


def summary_rows(records: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[(record["sample_id"], record["run"])].append(record)
    rows = []
    for (sample_id, run), recs in sorted(grouped.items()):
        labels = Counter(label for r in recs for label in r["failure_labels"].split(";") if label)
        scores = [float(r["reliability_score"]) for r in recs]
        rows.append(
            {
                "sample_id": sample_id,
                "group": recs[0]["group"],
                "run": run,
                "steps": recs[0]["steps"],
                "mean_reliability_score": f"{np.mean(scores):.3f}",
                "best_reliability_score": f"{max(scores):.3f}",
                "good_view_count_score_ge_60": str(sum(s >= 60 for s in scores)),
                "face_view_count": str(sum(int(r["face_count"]) > 0 for r in recs)),
                "dominant_failure_labels": ";".join(f"{k}:{v}" for k, v in labels.most_common(5)),
            }
        )
    return rows


def compare_rows(summary: list[dict[str, str]]) -> list[dict[str, str]]:
    by_sample: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in summary:
        by_sample[row["sample_id"]][row["run"]] = row
    rows = []
    for sample_id, runs in sorted(by_sample.items()):
        if "steps20" not in runs or "steps75" not in runs:
            continue
        r20 = runs["steps20"]
        r75 = runs["steps75"]
        delta_mean = float(r75["mean_reliability_score"]) - float(r20["mean_reliability_score"])
        delta_good = int(r75["good_view_count_score_ge_60"]) - int(r20["good_view_count_score_ge_60"])
        if delta_good > 0 or delta_mean > 5:
            verdict = "steps75_helped"
        elif delta_good < 0 or delta_mean < -5:
            verdict = "steps75_hurt"
        else:
            verdict = "steps75_neutral"
        rows.append(
            {
                "sample_id": sample_id,
                "group": r20["group"],
                "mean_score_steps20": r20["mean_reliability_score"],
                "mean_score_steps75": r75["mean_reliability_score"],
                "delta_mean_score": f"{delta_mean:.3f}",
                "good_views_steps20": r20["good_view_count_score_ge_60"],
                "good_views_steps75": r75["good_view_count_score_ge_60"],
                "delta_good_views": str(delta_good),
                "verdict": verdict,
            }
        )
    return rows


def comparison_figure(repo: Path, records: list[dict[str, str]], out_path: Path) -> None:
    samples = sorted({r["sample_id"] for r in records})
    cols = 1
    input_w = 120
    grid_w = 240
    grid_h = 360
    label_h = 28
    pad = 12
    row_h = grid_h + label_h + pad
    sheet = Image.new("RGB", (pad + cols * (input_w + 2 * grid_w + 3 * pad), pad + len(samples) * row_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, sample_id in enumerate(samples):
        y = pad + idx * row_h
        rec20 = next(r for r in records if r["sample_id"] == sample_id and r["run"] == "steps20")
        input_path = repo / rec20["view_file"]
        input_path = input_path.parent / "input_square.png"
        grid20 = input_path.parent / "grid.png"
        grid75 = repo / rec20["view_file"].replace("zero123plus_first10/", "zero123plus_first10_steps75/").replace("_steps20/", "_steps75/")
        grid75 = grid75.parent / "grid.png"
        x = pad
        inp = load_image(input_path).resize((input_w, input_w), Image.Resampling.LANCZOS)
        g20 = load_image(grid20).resize((grid_w, grid_h), Image.Resampling.LANCZOS)
        g75 = load_image(grid75).resize((grid_w, grid_h), Image.Resampling.LANCZOS)
        draw.text((x, y), sample_id, fill=(0, 0, 0))
        sheet.paste(inp, (x, y + label_h))
        draw.text((x + input_w + pad, y), "steps20", fill=(0, 0, 0))
        sheet.paste(g20, (x + input_w + pad, y + label_h))
        draw.text((x + input_w + grid_w + 2 * pad, y), "steps75", fill=(0, 0, 0))
        sheet.paste(g75, (x + input_w + grid_w + 2 * pad, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def fit_on_canvas(image: Image.Image, size: tuple[int, int], bg: str = "white") -> Image.Image:
    canvas = Image.new("RGB", size, bg)
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def budget_figure(repo: Path, budgets: list[dict[str, str]], out_path: Path, run: str = "steps75", budget: str = "4") -> None:
    selected = [row for row in budgets if row["run"] == run and row["budget"] == budget]
    thumb_w = 112
    thumb_h = 168
    pad = 10
    label_h = 26
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
    run_specs = [
        ("steps20", repo / "experiments/pseudo_views/zero123plus_first10", 20),
        ("steps75", repo / "experiments/pseudo_views/zero123plus_first10_steps75", 75),
    ]
    records = view_records(repo, repo / "experiments/inputs/first10/manifest.csv", run_specs)
    budgets = budget_rows(records)
    summary = summary_rows(records)
    comparison = compare_rows(summary)
    write_csv(repo / "experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv", records, VIEW_COLUMNS)
    write_csv(
        repo / "experiments/metrics/view_budget_selection_first10_steps20_75.csv",
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
        repo / "experiments/metrics/pseudo_view_summary_first10_steps20_75.csv",
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
        repo / "experiments/metrics/steps20_vs75_comparison_first10.csv",
        comparison,
        [
            "sample_id",
            "group",
            "mean_score_steps20",
            "mean_score_steps75",
            "delta_mean_score",
            "good_views_steps20",
            "good_views_steps75",
            "delta_good_views",
            "verdict",
        ],
    )
    comparison_figure(repo, records, repo / "experiments/figures/zero123plus_first10_steps20_vs75_grids.png")
    budget_figure(repo, budgets, repo / "experiments/figures/view_budget_selection_first10_steps75_budget4.png")
    print(f"view_records={len(records)}")
    print(f"budget_rows={len(budgets)}")
    print(f"summary_rows={len(summary)}")
    print(f"comparison_rows={len(comparison)}")


if __name__ == "__main__":
    main()
