#!/usr/bin/env python3
"""Evaluate a face-embedding identity filter for selected pseudo views."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class FaceEmbedding:
    embedding: np.ndarray | None
    detected: bool
    detection_prob: float
    box: tuple[float, float, float, float] | None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def normalize(vector: np.ndarray) -> np.ndarray:
    denom = float(np.linalg.norm(vector))
    if denom == 0:
        return vector
    return vector / denom


def detect_and_embed(
    image: Image.Image,
    detector: MTCNN,
    embedder: InceptionResnetV1,
    device: str,
) -> FaceEmbedding:
    boxes, probs = detector.detect(image)
    if boxes is None or len(boxes) == 0 or probs is None:
        return FaceEmbedding(None, False, 0.0, None)

    valid = [(idx, float(prob)) for idx, prob in enumerate(probs) if prob is not None and not np.isnan(prob)]
    if not valid:
        return FaceEmbedding(None, False, 0.0, None)
    best_idx, best_prob = max(valid, key=lambda item: item[1])
    box = boxes[best_idx]
    face = detector.extract(image, np.asarray([box]), save_path=None)
    if face is None:
        return FaceEmbedding(None, False, best_prob, tuple(float(x) for x in box))
    if face.ndim == 3:
        face = face.unsqueeze(0)
    face = face.to(device)
    with torch.inference_mode():
        embedding = embedder(face).detach().cpu().numpy()[0]
    return FaceEmbedding(normalize(embedding), True, best_prob, tuple(float(x) for x in box))


def identity_decision(
    cosine: float | None,
    view_detected: bool,
    mask_accepted: bool,
    trusted_score: float,
    strict_threshold: float,
    weak_threshold: float,
) -> tuple[str, list[str], bool, bool]:
    labels: list[str] = []
    identity_supervision = False
    geometry_candidate = False

    if not mask_accepted:
        labels.append("mask_rejected")
        return "mask_rejected", labels, identity_supervision, geometry_candidate

    if not view_detected or cosine is None:
        labels.append("no_detected_face")
        if trusted_score >= 70:
            geometry_candidate = True
            labels.append("geometry_only_candidate")
        return "identity_unverified", labels, identity_supervision, geometry_candidate

    if cosine >= strict_threshold:
        labels.append("strong_identity")
        identity_supervision = True
        return "identity_accept", labels, identity_supervision, geometry_candidate
    if cosine >= weak_threshold:
        labels.append("weak_identity")
        identity_supervision = True
        return "identity_accept_weak", labels, identity_supervision, geometry_candidate

    labels.append("identity_reject")
    return "identity_reject", labels, identity_supervision, geometry_candidate


def selected_budget_rows(budget_rows: list[dict[str, str]], run: str, budget: str) -> list[dict[str, str]]:
    rows = [row for row in budget_rows if row["run"] == run and row["budget"] == budget]
    expanded: list[dict[str, str]] = []
    for row in rows:
        indices = row["selected_view_indices"].split(";")
        files = row["selected_view_files"].split(";")
        for tile_index, (view_index, view_file) in enumerate(zip(indices, files)):
            expanded.append(
                {
                    "sample_id": row["sample_id"],
                    "group": row["group"],
                    "run": row["run"],
                    "steps": row["steps"],
                    "budget": row["budget"],
                    "tile_index": str(tile_index),
                    "view_index": view_index,
                    "view_file": view_file,
                    "budget_mean_trusted_score": row["mean_trusted_score"],
                    "budget_min_trusted_score": row["min_trusted_score"],
                }
            )
    return expanded


def make_rows(
    repo: Path,
    selected: list[dict[str, str]],
    mask_rows: list[dict[str, str]],
    detector: MTCNN,
    embedder: InceptionResnetV1,
    device: str,
    strict_threshold: float,
    weak_threshold: float,
) -> list[dict[str, str]]:
    mask_by_key = {
        (row["sample_id"], row["run"], row["view_index"]): row
        for row in mask_rows
    }
    input_embeddings: dict[Path, FaceEmbedding] = {}
    rows: list[dict[str, str]] = []
    for row in selected:
        key = (row["sample_id"], row["run"], row["view_index"])
        mask = mask_by_key[key]
        view_path = repo / row["view_file"]
        input_path = view_path.parent / "input_square.png"
        if input_path not in input_embeddings:
            input_embeddings[input_path] = detect_and_embed(load_image(input_path), detector, embedder, device)
        input_face = input_embeddings[input_path]
        view_face = detect_and_embed(load_image(view_path), detector, embedder, device)

        cosine: float | None = None
        if input_face.embedding is not None and view_face.embedding is not None:
            cosine = float(np.dot(input_face.embedding, view_face.embedding))

        mask_accepted = mask["accepted"] == "true"
        trusted_score = float(mask["trusted_score"])
        decision, labels, identity_supervision, geometry_candidate = identity_decision(
            cosine,
            view_face.detected,
            mask_accepted,
            trusted_score,
            strict_threshold,
            weak_threshold,
        )
        if not input_face.detected:
            labels.append("input_face_missing")

        rows.append(
            {
                "sample_id": row["sample_id"],
                "group": row["group"],
                "run": row["run"],
                "steps": row["steps"],
                "budget": row["budget"],
                "tile_index": row["tile_index"],
                "view_index": row["view_index"],
                "view_file": row["view_file"],
                "mask_accepted": mask["accepted"],
                "mask_reject_reasons": mask["reject_reasons"],
                "trusted_score": mask["trusted_score"],
                "reliability_score": mask["reliability_score"],
                "input_face_detected": str(input_face.detected).lower(),
                "input_face_prob": f"{input_face.detection_prob:.6f}",
                "view_face_detected": str(view_face.detected).lower(),
                "view_face_prob": f"{view_face.detection_prob:.6f}",
                "face_embedding_cosine": "" if cosine is None else f"{cosine:.6f}",
                "identity_decision": decision,
                "identity_labels": ";".join(labels),
                "identity_supervision_candidate": str(identity_supervision).lower(),
                "geometry_only_candidate": str(geometry_candidate).lower(),
            }
        )
    return rows


def summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_id"]].append(row)
    summaries: list[dict[str, str]] = []
    for sample_id, recs in sorted(grouped.items()):
        labels = Counter(label for row in recs for label in row["identity_labels"].split(";") if label)
        cosines = [float(row["face_embedding_cosine"]) for row in recs if row["face_embedding_cosine"]]
        summaries.append(
            {
                "sample_id": sample_id,
                "group": recs[0]["group"],
                "run": recs[0]["run"],
                "steps": recs[0]["steps"],
                "budget": recs[0]["budget"],
                "selected_view_count": str(len(recs)),
                "mask_accepted_count": str(sum(row["mask_accepted"] == "true" for row in recs)),
                "view_face_detected_count": str(sum(row["view_face_detected"] == "true" for row in recs)),
                "identity_supervision_count": str(
                    sum(row["identity_supervision_candidate"] == "true" for row in recs)
                ),
                "geometry_only_count": str(sum(row["geometry_only_candidate"] == "true" for row in recs)),
                "identity_reject_count": str(sum(row["identity_decision"] == "identity_reject" for row in recs)),
                "mean_detected_face_cosine": "" if not cosines else f"{np.mean(cosines):.6f}",
                "min_detected_face_cosine": "" if not cosines else f"{min(cosines):.6f}",
                "dominant_identity_labels": ";".join(f"{k}:{v}" for k, v in labels.most_common(6)),
            }
        )
    return summaries


def fit_on_canvas(image: Image.Image, size: tuple[int, int], bg: tuple[int, int, int] | str = "white") -> Image.Image:
    canvas = Image.new("RGB", size, bg)
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def draw_figure(repo: Path, rows: list[dict[str, str]], out_path: Path) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_id"]].append(row)
    tile_w, tile_h = 120, 150
    pad, label_h, sample_w = 10, 42, 178
    cols = max(len(recs) for recs in grouped.values()) + 1
    row_h = tile_h + label_h + pad
    sheet = Image.new(
        "RGB",
        (sample_w + cols * (tile_w + pad) + pad, pad + len(grouped) * row_h),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    status_color = {
        "identity_accept": (35, 145, 70),
        "identity_accept_weak": (120, 120, 40),
        "identity_unverified": (40, 80, 170),
        "identity_reject": (190, 40, 40),
        "mask_rejected": (120, 120, 120),
    }
    for r, (sample_id, recs) in enumerate(sorted(grouped.items())):
        y = pad + r * row_h
        draw.text((pad, y + 48), sample_id, fill=(0, 0, 0))
        input_path = repo / recs[0]["view_file"]
        input_path = input_path.parent / "input_square.png"
        sheet.paste(fit_on_canvas(load_image(input_path), (tile_w, tile_h)), (sample_w, y + label_h))
        draw.text((sample_w, y), "input", fill=(0, 0, 0))
        for c, row in enumerate(recs, 1):
            x = sample_w + c * (tile_w + pad)
            image = fit_on_canvas(load_image(repo / row["view_file"]), (tile_w, tile_h), bg=(245, 245, 245))
            sheet.paste(image, (x, y + label_h))
            decision = row["identity_decision"]
            color = status_color.get(decision, (0, 0, 0))
            score = row["face_embedding_cosine"][:5] if row["face_embedding_cosine"] else "n/a"
            draw.text((x, y), f"v{row['view_index']} {score}", fill=color)
            draw.text((x, y + 17), decision.replace("identity_", "id_")[:18], fill=color)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--run", default="cutout75")
    parser.add_argument("--budget", default="4")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--strict-threshold", type=float, default=0.50)
    parser.add_argument("--weak-threshold", type=float, default=0.35)
    parser.add_argument(
        "--budget-csv",
        default="experiments/metrics/view_budget_clip_selection_raw_vs_cutout_steps75.csv",
    )
    parser.add_argument(
        "--mask-csv",
        default="experiments/metrics/trusted_region_masks_first10_cutout75_budget4.csv",
    )
    parser.add_argument(
        "--view-output",
        default="experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv",
    )
    parser.add_argument(
        "--summary-output",
        default="experiments/metrics/face_identity_filter_summary_first10_cutout75_budget4.csv",
    )
    parser.add_argument(
        "--figure-output",
        default="experiments/figures/face_identity_filter_first10_cutout75_budget4.png",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    detector = MTCNN(image_size=160, margin=20, keep_all=False, device=device)
    embedder = InceptionResnetV1(pretrained="vggface2", device=device).eval()

    selected = selected_budget_rows(read_csv(repo / args.budget_csv), args.run, args.budget)
    rows = make_rows(
        repo,
        selected,
        read_csv(repo / args.mask_csv),
        detector,
        embedder,
        device,
        args.strict_threshold,
        args.weak_threshold,
    )
    summaries = summary_rows(rows)

    view_columns = [
        "sample_id",
        "group",
        "run",
        "steps",
        "budget",
        "tile_index",
        "view_index",
        "view_file",
        "mask_accepted",
        "mask_reject_reasons",
        "trusted_score",
        "reliability_score",
        "input_face_detected",
        "input_face_prob",
        "view_face_detected",
        "view_face_prob",
        "face_embedding_cosine",
        "identity_decision",
        "identity_labels",
        "identity_supervision_candidate",
        "geometry_only_candidate",
    ]
    summary_columns = [
        "sample_id",
        "group",
        "run",
        "steps",
        "budget",
        "selected_view_count",
        "mask_accepted_count",
        "view_face_detected_count",
        "identity_supervision_count",
        "geometry_only_count",
        "identity_reject_count",
        "mean_detected_face_cosine",
        "min_detected_face_cosine",
        "dominant_identity_labels",
    ]
    write_csv(repo / args.view_output, rows, view_columns)
    write_csv(repo / args.summary_output, summaries, summary_columns)
    draw_figure(repo, rows, repo / args.figure_output)

    print(json.dumps(
        {
            "view_rows": len(rows),
            "summary_rows": len(summaries),
            "mask_accepted": sum(row["mask_accepted"] == "true" for row in rows),
            "view_face_detected": sum(row["view_face_detected"] == "true" for row in rows),
            "identity_supervision": sum(row["identity_supervision_candidate"] == "true" for row in rows),
            "geometry_only": sum(row["geometry_only_candidate"] == "true" for row in rows),
            "identity_reject": sum(row["identity_decision"] == "identity_reject" for row in rows),
            "device": device,
        },
        indent=2))


if __name__ == "__main__":
    main()
