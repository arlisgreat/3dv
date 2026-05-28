#!/usr/bin/env python3
"""Build naive and identity/confidence-aware pseudo-view manifests for G81."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN  # type: ignore
from PIL import Image, ImageDraw, ImageOps


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G81_NERSEMBLE_PSEUDO_MANIFESTS_READY_PRIVATE"
BLOCKED_VERDICT = "BLOCKED_G81_NERSEMBLE_PSEUDO_MANIFESTS"
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


def load_image(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def normalize(vec: np.ndarray | None) -> np.ndarray | None:
    if vec is None:
        return None
    denom = float(np.linalg.norm(vec))
    return vec if denom < 1e-8 else vec / denom


def face_embedding(image: Image.Image, detector: MTCNN, embedder: InceptionResnetV1, device: str) -> dict[str, Any]:
    boxes, probs = detector.detect(image)
    if boxes is None or probs is None or len(boxes) == 0:
        return {"detected": False, "prob": 0.0, "box": None, "embedding": None}
    valid = [(idx, float(prob)) for idx, prob in enumerate(probs) if prob is not None and not math.isnan(float(prob))]
    if not valid:
        return {"detected": False, "prob": 0.0, "box": None, "embedding": None}
    best_idx, prob = max(valid, key=lambda item: item[1])
    box = boxes[best_idx]
    face = detector.extract(image, np.asarray([box]), save_path=None)
    if face is None:
        return {"detected": False, "prob": prob, "box": [float(x) for x in box], "embedding": None}
    if face.ndim == 3:
        face = face.unsqueeze(0)
    with torch.inference_mode():
        emb = embedder(face.to(device)).detach().cpu().numpy()[0]
    return {"detected": True, "prob": prob, "box": [float(x) for x in box], "embedding": normalize(emb)}


def foreground_mask(image: Image.Image, threshold: float) -> np.ndarray:
    arr = np.asarray(image).astype(np.int16)
    dist = np.linalg.norm(arr - BACKGROUND, axis=2)
    raw = dist > threshold
    mask_u8 = (raw.astype(np.uint8) * 255)
    kernel = np.ones((5, 5), np.uint8)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel, iterations=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8)
    keep = np.zeros_like(mask_u8)
    min_area = max(16, int(mask_u8.size * 0.002))
    for idx in range(1, count):
        if int(stats[idx, cv2.CC_STAT_AREA]) >= min_area:
            keep[labels == idx] = 255
    return keep > 0


def mask_stats(mask: np.ndarray) -> dict[str, Any]:
    if not bool(mask.any()):
        return {"coverage": 0.0, "bbox_area": 0.0, "center_offset": 1.0, "bbox": None}
    height, width = mask.shape
    ys, xs = np.where(mask)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    bbox_area = ((x1 - x0 + 1) * (y1 - y0 + 1)) / float(width * height)
    cx = (x0 + x1) / 2.0 / max(width - 1, 1)
    cy = (y0 + y1) / 2.0 / max(height - 1, 1)
    return {
        "coverage": float(mask.mean()),
        "bbox_area": float(bbox_area),
        "center_offset": float(((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5),
        "bbox": [x0, y0, x1, y1],
    }


def confidence_score(stats: dict[str, Any], face_detected: bool, cosine: float | None) -> float:
    score = 100.0
    if stats["coverage"] < 0.04 or stats["coverage"] > 0.82:
        score -= 35.0
    if stats["bbox_area"] > 0.90:
        score -= 20.0
    score -= min(30.0, stats["center_offset"] * 70.0)
    if not face_detected:
        score -= 10.0
    if cosine is not None:
        score += max(-25.0, min(15.0, (cosine - 0.55) * 60.0))
    return float(max(0.0, min(100.0, score)))


def role_for(cosine: float | None, face_detected: bool, conf: float, strict: float, weak: float) -> tuple[str, float, float]:
    if conf < 45.0:
        return "reject", 0.0, 0.0
    if face_detected and cosine is not None and cosine >= strict:
        return "identity_supervision", 1.0, 1.0
    if face_detected and cosine is not None and cosine >= weak:
        return "identity_supervision_weak", 0.65, 0.8
    if conf >= 65.0:
        return "geometry_only", 0.20, 1.0
    return "reject", 0.0, 0.0


def save_mask(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(path)


def make_contact_sheet(source: Image.Image, rows: list[dict[str, Any]], output: Path) -> None:
    tile_w, tile_h = 170, 210
    cols = len(rows) + 1
    sheet = Image.new("RGB", (cols * tile_w, tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    source_thumb = source.copy()
    source_thumb.thumbnail((tile_w - 10, tile_w - 10), Image.Resampling.LANCZOS)
    sheet.paste(source_thumb, ((tile_w - source_thumb.width) // 2, 8))
    draw.text((8, tile_w + 12), "source", fill=(0, 0, 0))
    for idx, row in enumerate(rows, start=1):
        image = load_image(Path(row["image_path"]))
        image.thumbnail((tile_w - 10, tile_w - 10), Image.Resampling.LANCZOS)
        x = idx * tile_w
        sheet.paste(image, (x + (tile_w - image.width) // 2, 8))
        label = f"v{row['view_index']} {row['supervision_role']}\ncos={row['identity_anchor_score']} conf={row['confidence_score']:.1f}"
        draw.multiline_text((x + 8, tile_w + 12), label[:80], fill=(0, 0, 0), spacing=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} NeRSemble Pseudo-View Supervision Manifests",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Summary:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| pseudo_view_count | {payload['summary']['pseudo_view_count']} |",
        f"| aware_trainable_count | {payload['summary']['aware_trainable_count']} |",
        f"| aware_identity_count | {payload['summary']['aware_identity_count']} |",
        f"| aware_geometry_count | {payload['summary']['aware_geometry_count']} |",
        f"| aware_reject_count | {payload['summary']['aware_reject_count']} |",
        "",
        "Aware roles:",
        "",
        "| view | azimuth | elevation | role | cosine | confidence | rgb weight | depth weight |",
        "| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["aware_manifest_preview"]:
        lines.append(
            f"| {row['view_index']} | {row['azimuth']} | {row['elevation']} | {row['supervision_role']} | "
            f"{row['identity_anchor_score']} | {row['confidence_score']:.3f} | {row['rgb_weight']:.3f} | {row['depth_weight']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Private manifests:",
            "",
            "```text",
            payload["private_outputs"]["naive_manifest"],
            payload["private_outputs"]["aware_manifest"],
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
    parser.add_argument("--zero123-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75"))
    parser.add_argument("--source-prep-json", type=Path, default=Path("experiments/metrics/g83_nersemble_source220700191_pseudo_input_prep_20260528.json"))
    parser.add_argument("--work-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--mask-threshold", type=float, default=22.0)
    parser.add_argument("--identity-strict-threshold", type=float, default=0.68)
    parser.add_argument("--identity-weak-threshold", type=float, default=0.52)
    parser.add_argument("--gate", default="G85")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g85_nersemble_source220700191_pseudo_supervision_manifests_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g85_nersemble_source220700191_pseudo_supervision_manifests_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    zero_meta = load_json(args.zero123_root / "metadata.json")
    source_prep = load_json(repo / args.source_prep_json if not args.source_prep_json.is_absolute() else args.source_prep_json)
    source_path = Path(source_prep["private_outputs"]["masked_square_input"])
    source = load_image(source_path)

    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    detector = MTCNN(image_size=160, margin=0, post_process=True, device=device)
    embedder = InceptionResnetV1(pretrained="vggface2").eval().to(device)
    source_face = face_embedding(source, detector, embedder, device)

    rows: list[dict[str, Any]] = []
    for view in zero_meta["views"]:
        image_path = args.zero123_root / view["file"]
        image = load_image(image_path)
        mask = foreground_mask(image, args.mask_threshold)
        stats = mask_stats(mask)
        face = face_embedding(image, detector, embedder, device)
        cosine = None
        if source_face["embedding"] is not None and face["embedding"] is not None:
            cosine = float(np.dot(source_face["embedding"], face["embedding"]))
        conf = confidence_score(stats, bool(face["detected"]), cosine)
        role, rgb_weight, depth_weight = role_for(
            cosine,
            bool(face["detected"]),
            conf,
            args.identity_strict_threshold,
            args.identity_weak_threshold,
        )
        mask_path = args.work_root / "trusted_masks" / f"{Path(view['file']).stem}_trusted_mask.png"
        save_mask(mask if role != "reject" else np.zeros_like(mask), mask_path)
        rows.append(
            {
                "view_index": int(view["index"]),
                "azimuth": view["azimuth"],
                "elevation": view["elevation"],
                "image_path": str(image_path),
                "image_sha256": sha256_file(image_path),
                "trusted_region_mask": str(mask_path),
                "trusted_region_mask_sha256": sha256_file(mask_path),
                "identity_anchor_score": None if cosine is None else round(cosine, 6),
                "source_face_detected": bool(source_face["detected"]),
                "view_face_detected": bool(face["detected"]),
                "view_face_prob": float(face["prob"]),
                "confidence_score": conf,
                "mask_stats": stats,
                "supervision_role": role,
                "ri3d_train_candidate": role != "reject",
                "rgb_weight": rgb_weight,
                "depth_weight": depth_weight,
                "mask_weight": 1.0 if role != "reject" else 0.0,
            }
        )

    naive_rows = []
    for row in rows:
        naive = dict(row)
        naive.update(
            {
                "supervision_role": "naive_rgb",
                "ri3d_train_candidate": True,
                "rgb_weight": 1.0,
                "depth_weight": 1.0,
                "mask_weight": 1.0,
                "confidence_score": 100.0,
            }
        )
        naive_rows.append(naive)

    aware_rows = rows
    naive_manifest_path = args.work_root / "naive_pseudo_supervision_manifest.json"
    aware_manifest_path = args.work_root / "identity_confidence_aware_pseudo_supervision_manifest.json"
    contact_sheet = args.work_root / "g85_private_pseudo_view_identity_confidence_sheet.png"
    make_contact_sheet(source, aware_rows, contact_sheet)

    common = {
        "semantic_type": "g81_nersemble_source_pseudo_supervision_manifest",
        "source_image": str(source_path),
        "source_image_sha256": sha256_file(source_path),
        "zero123_root": str(args.zero123_root),
        "zero123_metadata": zero_meta,
        "no_leakage_rule": "Generated from one source image only; real held-out NeRSemble images/masks are not supervision.",
    }
    write_json(naive_manifest_path, {**common, "arm": "naive_pseudo_view_supervision", "pseudo_views": naive_rows})
    write_json(aware_manifest_path, {**common, "arm": "identity_confidence_aware_pseudo_view_supervision", "pseudo_views": aware_rows})

    role_counts: dict[str, int] = {}
    for row in aware_rows:
        role_counts[row["supervision_role"]] = role_counts.get(row["supervision_role"], 0) + 1
    verdict = PASS_VERDICT if any(row["ri3d_train_candidate"] for row in aware_rows) else BLOCKED_VERDICT
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "verdict": verdict,
        "summary": {
            "pseudo_view_count": len(rows),
            "aware_trainable_count": sum(bool(row["ri3d_train_candidate"]) for row in aware_rows),
            "aware_identity_count": sum(row["supervision_role"].startswith("identity") for row in aware_rows),
            "aware_geometry_count": role_counts.get("geometry_only", 0),
            "aware_reject_count": role_counts.get("reject", 0),
            "aware_role_counts": role_counts,
        },
        "private_outputs": {
            "naive_manifest": str(naive_manifest_path),
            "aware_manifest": str(aware_manifest_path),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256_file(contact_sheet),
        },
        "aware_manifest_preview": aware_rows,
        "artifact_policy": "Generated identifiable pseudo views and contact sheet remain private under 3dv_work; commit hashes/metrics only.",
        "decision": (
            "Naive and identity/confidence-aware pseudo-supervision manifests are ready for RI3D/3DGS arm construction."
            if verdict == PASS_VERDICT
            else "Blocked: no trainable identity/confidence-aware pseudo views remain after gating."
        ),
        "next_gate": "Prepare RI3D/3DGS scenes for naive and aware arms, train/render held-out predictions, then rerun G84.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": verdict, "role_counts": role_counts, "aware_manifest": str(aware_manifest_path)}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
