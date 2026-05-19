#!/usr/bin/env python3
"""Evaluate pseudo-view consistency with the cached Zero123++ CLIP vision encoder."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from transformers import CLIPImageProcessor, CLIPVisionModelWithProjection


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def model_root(repo: Path) -> Path:
    root = repo / ".cache/huggingface/hub/models--sudo-ai--zero123plus-v1.2/snapshots"
    snapshots = sorted(root.glob("*"))
    if not snapshots:
        raise FileNotFoundError(f"Zero123++ v1.2 snapshot not found under {root}")
    return snapshots[-1]


def embed_images(
    image_paths: list[Path],
    processor: CLIPImageProcessor,
    model: CLIPVisionModelWithProjection,
    device: str,
    batch_size: int,
) -> dict[Path, np.ndarray]:
    out: dict[Path, np.ndarray] = {}
    model_dtype = next(model.parameters()).dtype
    for start in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[start : start + batch_size]
        images = [load_image(path) for path in batch_paths]
        inputs = processor(images=images, return_tensors="pt")
        inputs = {
            key: value.to(device=device, dtype=model_dtype if key == "pixel_values" else value.dtype)
            for key, value in inputs.items()
        }
        with torch.inference_mode():
            embeds = model(**inputs).image_embeds
            embeds = torch.nn.functional.normalize(embeds.float(), dim=-1)
        for path, embed in zip(batch_paths, embeds.detach().cpu().numpy()):
            out[path] = embed
    return out


def collect_paths(repo: Path, run_specs: list[tuple[str, Path, int]]) -> tuple[list[dict[str, object]], list[Path]]:
    manifest = repo / "experiments/inputs/first10/manifest.csv"
    rows = list(csv.DictReader(manifest.open("r", newline="", encoding="utf-8")))
    by_id = {row["sample_id"]: row for row in rows}
    records: list[dict[str, object]] = []
    paths: list[Path] = []
    for run_name, root, steps in run_specs:
        for sample_id, source in by_id.items():
            outdir = root / f"{sample_id}_steps{steps}"
            metadata = json.loads((outdir / "metadata.json").read_text(encoding="utf-8"))
            input_path = outdir / "input_square.png"
            paths.append(input_path)
            for view in metadata["views"]:
                view_path = outdir / view["file"]
                paths.append(view_path)
                records.append(
                    {
                        "sample_id": sample_id,
                        "group": source["group"],
                        "run": run_name,
                        "steps": steps,
                        "view_index": view["index"],
                        "view_file": str(view_path.relative_to(repo)),
                        "input_file": str(input_path.relative_to(repo)),
                    }
                )
    deduped = sorted(set(paths))
    return records, deduped


def load_reliability(repo: Path) -> dict[tuple[str, str, str], float]:
    path = repo / "experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv"
    rows = csv.DictReader(path.open("r", newline="", encoding="utf-8"))
    scores = {}
    for row in rows:
        scores[(row["sample_id"], row["run"], row["view_index"])] = float(row["reliability_score"])
    return scores


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def make_rows(repo: Path, records: list[dict[str, object]], embeds: dict[Path, np.ndarray]) -> list[dict[str, str]]:
    reliability = load_reliability(repo)
    rows = []
    for record in records:
        sample_id = str(record["sample_id"])
        run = str(record["run"])
        view_index = str(record["view_index"])
        view_path = repo / str(record["view_file"])
        input_path = repo / str(record["input_file"])
        cosine = float(np.dot(embeds[input_path], embeds[view_path]))
        learned_score = max(0.0, min(100.0, (cosine + 1.0) * 50.0))
        reliability_score = reliability[(sample_id, run, view_index)]
        trusted_score = 0.65 * reliability_score + 0.35 * learned_score
        labels = []
        if cosine < 0.72:
            labels.append("low_clip_consistency")
        elif cosine < 0.80:
            labels.append("weak_clip_consistency")
        if trusted_score < 60:
            labels.append("low_trusted_score")
        rows.append(
            {
                "sample_id": sample_id,
                "group": str(record["group"]),
                "run": run,
                "steps": str(record["steps"]),
                "view_index": view_index,
                "view_file": str(record["view_file"]),
                "clip_cosine_to_input": f"{cosine:.6f}",
                "clip_consistency_score": f"{learned_score:.3f}",
                "reliability_score": f"{reliability_score:.3f}",
                "trusted_score": f"{trusted_score:.3f}",
                "failure_labels": ";".join(labels),
            }
        )
    return rows


def summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["sample_id"], row["run"])].append(row)
    summary = []
    for (sample_id, run), recs in sorted(grouped.items()):
        labels = Counter(label for r in recs for label in r["failure_labels"].split(";") if label)
        trusted = [float(r["trusted_score"]) for r in recs]
        clip = [float(r["clip_cosine_to_input"]) for r in recs]
        summary.append(
            {
                "sample_id": sample_id,
                "group": recs[0]["group"],
                "run": run,
                "steps": recs[0]["steps"],
                "mean_clip_cosine": f"{np.mean(clip):.6f}",
                "mean_trusted_score": f"{np.mean(trusted):.3f}",
                "good_trusted_view_count_score_ge_60": str(sum(s >= 60 for s in trusted)),
                "dominant_failure_labels": ";".join(f"{k}:{v}" for k, v in labels.most_common(5)),
            }
        )
    return summary


def budget_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["sample_id"], row["run"])].append(row)
    out = []
    for (sample_id, run), recs in sorted(grouped.items()):
        ranked = sorted(recs, key=lambda row: float(row["trusted_score"]), reverse=True)
        for budget in [1, 2, 4, 6]:
            selected = ranked[:budget]
            labels = Counter(label for r in selected for label in r["failure_labels"].split(";") if label)
            out.append(
                {
                    "sample_id": sample_id,
                    "group": selected[0]["group"],
                    "run": run,
                    "steps": selected[0]["steps"],
                    "budget": str(budget),
                    "selected_view_indices": ";".join(r["view_index"] for r in selected),
                    "selected_view_files": ";".join(r["view_file"] for r in selected),
                    "mean_clip_cosine": f"{np.mean([float(r['clip_cosine_to_input']) for r in selected]):.6f}",
                    "mean_trusted_score": f"{np.mean([float(r['trusted_score']) for r in selected]):.3f}",
                    "min_trusted_score": f"{min(float(r['trusted_score']) for r in selected):.3f}",
                    "failure_labels": ";".join(sorted(labels)),
                }
            )
    return out


def fit_on_canvas(image: Image.Image, size: tuple[int, int], bg: tuple[int, int, int] | str = "white") -> Image.Image:
    canvas = Image.new("RGB", size, bg)
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def budget_figure(repo: Path, budgets: list[dict[str, str]], out_path: Path, run: str = "steps75", budget: str = "4") -> None:
    selected = [row for row in budgets if row["run"] == run and row["budget"] == budget]
    thumb_w, thumb_h = 112, 168
    pad, label_h = 10, 32
    cols = int(budget) + 1
    sheet = Image.new("RGB", (pad + cols * (thumb_w + pad), pad + len(selected) * (thumb_h + label_h + pad)), "white")
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
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=12)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    root = model_root(repo)
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    processor = CLIPImageProcessor.from_pretrained(root / "feature_extractor_clip")
    dtype = torch.float16 if device.startswith("cuda") else torch.float32
    model = CLIPVisionModelWithProjection.from_pretrained(root / "vision_encoder", torch_dtype=dtype)
    model.to(device)
    model.eval()

    run_specs = [
        ("steps20", repo / "experiments/pseudo_views/zero123plus_first10", 20),
        ("steps75", repo / "experiments/pseudo_views/zero123plus_first10_steps75", 75),
    ]
    records, paths = collect_paths(repo, run_specs)
    embeds = embed_images(paths, processor, model, device, args.batch_size)
    rows = make_rows(repo, records, embeds)
    summaries = summary_rows(rows)
    budgets = budget_rows(rows)

    write_csv(
        repo / "experiments/metrics/pseudo_view_clip_consistency_first10_steps20_75.csv",
        rows,
        [
            "sample_id",
            "group",
            "run",
            "steps",
            "view_index",
            "view_file",
            "clip_cosine_to_input",
            "clip_consistency_score",
            "reliability_score",
            "trusted_score",
            "failure_labels",
        ],
    )
    write_csv(
        repo / "experiments/metrics/clip_consistency_summary_first10_steps20_75.csv",
        summaries,
        [
            "sample_id",
            "group",
            "run",
            "steps",
            "mean_clip_cosine",
            "mean_trusted_score",
            "good_trusted_view_count_score_ge_60",
            "dominant_failure_labels",
        ],
    )
    write_csv(
        repo / "experiments/metrics/view_budget_clip_selection_first10_steps20_75.csv",
        budgets,
        [
            "sample_id",
            "group",
            "run",
            "steps",
            "budget",
            "selected_view_indices",
            "selected_view_files",
            "mean_clip_cosine",
            "mean_trusted_score",
            "min_trusted_score",
            "failure_labels",
        ],
    )
    budget_figure(repo, budgets, repo / "experiments/figures/view_budget_clip_selection_first10_steps75_budget4.png")
    print(f"view_rows={len(rows)}")
    print(f"summary_rows={len(summaries)}")
    print(f"budget_rows={len(budgets)}")
    print(f"device={device}")


if __name__ == "__main__":
    main()
