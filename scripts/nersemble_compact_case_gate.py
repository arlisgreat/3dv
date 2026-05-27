#!/usr/bin/env python3
"""Preflight NeRSemble benchmark protocols and select compact local cases."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
GATE = "G53"
PASS_PREFLIGHT_PENDING_VISUAL = "PASS_NERSEMBLE_COMPACT_PREFLIGHT_PENDING_LOCAL_VISUAL_REVIEW"
PASS_VISUAL_LOCAL = "PASS_NERSEMBLE_COMPACT_CASE_LOCAL_VISUAL_AUDIT"
BLOCKED = "BLOCKED_NERSEMBLE_COMPACT_CASE_GATE"

SERIALS = [
    "222200042",
    "222200044",
    "222200046",
    "222200040",
    "222200036",
    "222200048",
    "220700191",
    "222200041",
    "222200037",
    "222200038",
    "222200047",
    "222200043",
    "222200049",
    "222200039",
    "222200045",
    "221501007",
]

NVS_CASES = [
    (388, "GLASSES"),
    (422, "EXP-2-eyes"),
    (443, "FREE"),
    (445, "EXP-6-tongue-1"),
    (475, "HAIR"),
]
NVS_HOLDOUT_SERIALS = ["222200046", "222200037", "222200039"]
NVS_TRAIN_SERIALS = [serial for serial in SERIALS if serial not in NVS_HOLDOUT_SERIALS]

MONO_IDS = [393, 404, 461, 477, 486]
MONO_TRAIN_SEQUENCES = [
    "EXP-1-head",
    "EXP-2-eyes",
    "EXP-3-cheeks+nose",
    "EXP-4-lips",
    "EXP-5-mouth",
    "EXP-8-jaw-1",
    "EXP-9-jaw-2",
    "EMO-2-surprise+fear",
    "EMO-3-angry+sad",
    "EMO-4-disgust+happy",
    "SEN-01-cramp_small_danger",
    "SEN-02-same_phrase_thirty_times",
    "SEN-03-pluck_bright_rose",
    "SEN-04-two_plus_seven",
    "SEN-05-glow_eyes_sweet_girl",
    "SEN-06-problems_wise_chief",
    "SEN-07-fond_note_fried",
    "SEN-08-clothes_and_lodging",
]
MONO_TEST_SEQUENCES = ["FREE", "EMO-1-shout+laugh", "SEN-09-frown_events_bad", "SEN-10-port_strong_smokey"]
MONO_TRAIN_SERIAL = "222200037"
MONO_EVAL_SERIALS = ["222200046", "220700191", "222200039"]

SVFR_IDS = [17, 60, 71, 102, 112, 123, 133, 139, 175, 178, 183, 194, 215, 226, 256, 266, 289, 310, 320, 372]


def relpath(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_files(root: Path, suffix: str | None = None) -> list[Path]:
    if not root.exists():
        return []
    matches: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename
            if suffix is None or path.suffix.lower() == suffix:
                matches.append(path)
    return matches


def audit_nvs(benchmark_root: Path) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    missing_total = 0
    for participant, sequence in NVS_CASES:
        base = benchmark_root / "nvs" / f"{participant:03d}"
        seq_base = base / "sequences" / sequence
        missing: list[str] = []
        required = [base / "calibration" / "camera_params.json", seq_base / "pointclouds" / "frame_00000.pcd"]
        for serial in NVS_TRAIN_SERIALS:
            required.append(seq_base / "images" / f"cam_{serial}.mp4")
            required.append(seq_base / "alpha_maps" / f"cam_{serial}.mp4")
        for path in required:
            if not path.exists():
                missing.append(str(path))
        missing_total += len(missing)
        cases.append(
            {
                "participant": f"{participant:03d}",
                "sequence": sequence,
                "train_serial_count": len(NVS_TRAIN_SERIALS),
                "hidden_holdout_serials": NVS_HOLDOUT_SERIALS,
                "required_files": len(required),
                "missing_files": missing,
                "has_first_pointcloud": (seq_base / "pointclouds" / "frame_00000.pcd").exists(),
            }
        )
    return {
        "task": "official_nvs",
        "cases": cases,
        "missing_files": missing_total,
        "interpretation": (
            "Official NVS train assets and first pointclouds can configure adapter development. "
            "The three official held-out cameras are hidden, so local metrics must not be presented as official leaderboard metrics."
        ),
    }


def audit_mono(benchmark_root: Path) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    missing_total = 0
    for participant in MONO_IDS:
        base = benchmark_root / "mono_flame_avatar" / f"{participant:03d}"
        missing: list[str] = []
        required = [base / "calibration" / "camera_params.json"]
        for sequence in MONO_TRAIN_SEQUENCES:
            seq_base = base / "sequences" / sequence
            required.extend(
                [
                    seq_base / "tracking" / "flame2023_tracking_v2.npz",
                    seq_base / "images" / f"cam_{MONO_TRAIN_SERIAL}.mp4",
                    seq_base / "alpha_maps" / f"cam_{MONO_TRAIN_SERIAL}.mp4",
                ]
            )
        for sequence in MONO_TEST_SEQUENCES:
            required.append(base / "sequences" / sequence / "tracking" / "flame2023_tracking_v2.npz")
        for path in required:
            if not path.exists():
                missing.append(str(path))
        missing_total += len(missing)
        cases.append(
            {
                "participant": f"{participant:03d}",
                "train_sequence_count": len(MONO_TRAIN_SEQUENCES),
                "test_sequence_count": len(MONO_TEST_SEQUENCES),
                "train_serial": MONO_TRAIN_SERIAL,
                "official_eval_serials": MONO_EVAL_SERIALS,
                "required_files": len(required),
                "missing_files": missing,
            }
        )
    return {
        "task": "official_mono_flame_avatar",
        "cases": cases,
        "missing_files": missing_total,
        "interpretation": (
            "Mono FLAME Avatar assets provide a single-camera train protocol plus FLAME tracking. "
            "This is the closest official protocol to the sprint's single-image/head-prior setting."
        ),
    }


def audit_svfr(benchmark_root: Path) -> dict[str, Any]:
    svfr_root = benchmark_root / "svfr"
    pngs = list_files(svfr_root, ".png")
    by_participant: Counter[str] = Counter()
    for path in pngs:
        try:
            by_participant[path.relative_to(svfr_root).parts[0]] += 1
        except Exception:
            by_participant["<unparsed>"] += 1
    missing_ids = [f"{participant:03d}" for participant in SVFR_IDS if by_participant.get(f"{participant:03d}", 0) == 0]
    return {
        "task": "official_svfr",
        "image_count": len(pngs),
        "participant_count": len(by_participant),
        "participants_with_images": dict(sorted(by_participant.items())),
        "missing_expected_participants": missing_ids,
        "interpretation": (
            "SVFR is the official single-view task, but GT geometry is hidden for submission metrics. "
            "It is suitable for input-distribution smoke tests and external benchmark submission packaging, not local GT metric claims."
        ),
    }


def load_sequence_rows(metadata_sequences: Path) -> list[dict[str, str]]:
    if not metadata_sequences.exists():
        return []
    with metadata_sequences.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def has_sequence(row: dict[str, str], sequence: str) -> bool:
    return row.get(sequence, "").strip().lower() == "x"


def compact_candidates(v2_root: Path, sequences: list[str], limit: int) -> dict[str, Any]:
    rows = load_sequence_rows(v2_root / "metadata_sequences.csv")
    candidates: list[dict[str, Any]] = []
    blocked_missing: list[dict[str, Any]] = []
    for row in rows:
        participant = int(row["ID"])
        participant_id = f"{participant:03d}"
        calib = v2_root / participant_id / "calibration" / "camera_params.json"
        color = v2_root / participant_id / "calibration" / "color_calibration.json"
        if not calib.exists() or not color.exists():
            blocked_missing.append({"participant": participant_id, "reason": "missing_calibration"})
            continue
        for sequence in sequences:
            if not has_sequence(row, sequence):
                continue
            missing: list[str] = []
            for serial in SERIALS:
                video = v2_root / participant_id / "sequences" / sequence / "images" / f"cam_{serial}.mp4"
                background = v2_root / participant_id / "sequences" / "BACKGROUND" / f"image_{serial}.jpg"
                if not video.exists():
                    missing.append(str(video))
                if not background.exists():
                    missing.append(str(background))
            if missing:
                blocked_missing.append(
                    {
                        "participant": participant_id,
                        "sequence": sequence,
                        "missing_count": len(missing),
                        "missing_examples": missing[:5],
                    }
                )
                continue
            candidates.append(
                {
                    "participant": participant_id,
                    "sequence": sequence,
                    "all_serial_count": len(SERIALS),
                    "single_image_input_serial": MONO_TRAIN_SERIAL,
                    "local_eval_serials": MONO_EVAL_SERIALS,
                    "official_nvs_holdout_serials": NVS_HOLDOUT_SERIALS,
                    "calibration": str(calib),
                    "color_calibration": str(color),
                    "video_dir": str(v2_root / participant_id / "sequences" / sequence / "images"),
                    "background_dir": str(v2_root / participant_id / "sequences" / "BACKGROUND"),
                }
            )
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "blocked_missing_examples": blocked_missing[:20],
        "selection_policy": (
            "Require one participant/sequence with all 16 camera videos, all 16 backgrounds, "
            "camera calibration, and color calibration. Use cam_222200037 as the single-image input "
            "for the Mono-FLAME-like setting and reserve cam_222200046/220700191/222200039 for local held-out RGB/mask audit."
        ),
    }


def make_audit_sheet(candidate: dict[str, Any], output: Path, frame_index: int) -> dict[str, Any]:
    import cv2  # type: ignore
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    video_dir = Path(candidate["video_dir"])
    serials = [candidate["single_image_input_serial"]] + [
        serial for serial in candidate["local_eval_serials"] if serial != candidate["single_image_input_serial"]
    ]
    serials.extend(serial for serial in SERIALS if serial not in serials)
    serials = serials[:16]

    thumbs: list[Image.Image] = []
    metadata: list[dict[str, Any]] = []
    for serial in serials:
        video = video_dir / f"cam_{serial}.mp4"
        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            raise RuntimeError(f"could not open {video}")
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        target = min(max(frame_index, 0), max(frame_count - 1, 0))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError(f"could not read frame {target} from {video}")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        image.thumbnail((220, 220), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (240, 270), "white")
        tile.paste(image, ((240 - image.width) // 2, 10))
        draw = ImageDraw.Draw(tile)
        label = serial
        if serial == candidate["single_image_input_serial"]:
            label += " input"
        elif serial in candidate["local_eval_serials"]:
            label += " eval"
        draw.text((10, 238), label, fill=(0, 0, 0))
        thumbs.append(tile)
        metadata.append({"serial": serial, "video": str(video), "frame_index": target, "frame_count": frame_count})

    sheet = Image.new("RGB", (4 * 240, 4 * 270), "white")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % 4) * 240, (index // 4) * 270))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "serials": metadata,
        "local_only_reason": "Contains licensed identifiable NeRSemble face frames; keep under 3dv_work and do not commit without explicit artifact review.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any], repo: Path) -> None:
    official = payload["official_benchmark"]
    compact = payload["compact_candidates"]
    candidates = compact["candidates"]
    top = candidates[0] if candidates else None
    lines = [
        "# G53 NeRSemble Benchmark And Compact Case Gate",
        "",
        f"Date: {payload['date']}",
        "",
        "Premise:",
        "",
        "```text",
        payload["premise"],
        "```",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Official benchmark protocol preflight:",
        "",
        "| task | status | local files checked | missing files | interpretation |",
        "| --- | --- | ---: | ---: | --- |",
        f"| NVS | {'pass' if official['nvs']['missing_files'] == 0 else 'blocked'} | {sum(case['required_files'] for case in official['nvs']['cases'])} | {official['nvs']['missing_files']} | train cameras + first pointcloud local; official holdouts hidden |",
        f"| Mono FLAME Avatar | {'pass' if official['mono']['missing_files'] == 0 else 'blocked'} | {sum(case['required_files'] for case in official['mono']['cases'])} | {official['mono']['missing_files']} | single-camera train + FLAME tracking local |",
        f"| SVFR | {'pass' if not official['svfr']['missing_expected_participants'] else 'blocked'} | {official['svfr']['image_count']} pngs | {len(official['svfr']['missing_expected_participants'])} participants missing | official single-view input; hidden GT metrics |",
        "",
        "Compact local candidates:",
        "",
        "| rank | participant | sequence | input serial | eval serials | all 16 cams |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for rank, candidate in enumerate(candidates[:10], start=1):
        lines.append(
            f"| {rank} | {candidate['participant']} | {candidate['sequence']} | "
            f"{candidate['single_image_input_serial']} | {', '.join(candidate['local_eval_serials'])} | {candidate['all_serial_count']} |"
        )
    if not candidates:
        lines.append("| n/a | none | none | none | none | 0 |")

    lines.extend(
        [
            "",
            "Local visual audit:",
            "",
            "```text",
            json.dumps(payload["local_visual_audit"], indent=2, sort_keys=True),
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
    if top:
        lines.extend(
            [
                "",
                "Selected first compact case:",
                "",
                "```text",
                f"participant={top['participant']} sequence={top['sequence']} input={top['single_image_input_serial']} eval={','.join(top['local_eval_serials'])}",
                "```",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--v2-root", type=Path, default=Path("datasets/nersemble_v2"))
    parser.add_argument("--benchmark-root", type=Path, default=Path("datasets/nersemble_benchmark"))
    parser.add_argument("--candidate-sequences", nargs="+", default=["EXP-1-head", "FREE", "EMO-1-shout+laugh", "SEN-09-frown_events_bad"])
    parser.add_argument("--max-candidates", type=int, default=20)
    parser.add_argument("--make-audit-sheet", action="store_true")
    parser.add_argument("--audit-output", type=Path, default=Path("/data1/workspace/airulan/3dv_work/nersemble_audits/g53_nersemble_compact_case_audit_20260527.png"))
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--visual-verdict", default="PENDING_LOCAL_VLM_MANUAL_REVIEW")
    parser.add_argument("--visual-notes", default="")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g53_nersemble_compact_case_gate_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g53_nersemble_compact_case_gate_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    v2_root = (repo / args.v2_root).resolve() if not args.v2_root.is_absolute() else args.v2_root
    benchmark_root = (repo / args.benchmark_root).resolve() if not args.benchmark_root.is_absolute() else args.benchmark_root

    official = {
        "nvs": audit_nvs(benchmark_root),
        "mono": audit_mono(benchmark_root),
        "svfr": audit_svfr(benchmark_root),
    }
    compact = compact_candidates(v2_root, args.candidate_sequences, args.max_candidates)
    local_visual_audit: dict[str, Any] = {
        "verdict": args.visual_verdict,
        "notes": args.visual_notes,
        "audit_sheet": None,
    }
    if args.make_audit_sheet:
        if not compact["candidates"]:
            raise SystemExit("cannot create audit sheet without a compact candidate")
        local_visual_audit["audit_sheet"] = make_audit_sheet(compact["candidates"][0], args.audit_output, args.frame_index)

    official_missing = (
        official["nvs"]["missing_files"]
        + official["mono"]["missing_files"]
        + len(official["svfr"]["missing_expected_participants"])
    )
    if official_missing or not compact["candidates"]:
        verdict = BLOCKED
    elif args.visual_verdict.startswith("PASS"):
        verdict = PASS_VISUAL_LOCAL
    else:
        verdict = PASS_PREFLIGHT_PENDING_VISUAL

    if verdict == PASS_VISUAL_LOCAL:
        decision = (
            "Official benchmark protocols are locally configured and the selected compact v2 case passed local visual audit. "
            "This authorizes adapter/dataloader implementation, not a reconstruction-quality result."
        )
    elif verdict == PASS_PREFLIGHT_PENDING_VISUAL:
        decision = (
            "Official benchmark protocols and compact candidates are structurally present. Complete local VLM/manual audit "
            "of the private sheet before any method run."
        )
    else:
        decision = "Blocked: missing official benchmark assets or no full 16-camera compact v2 candidate."

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "NeRSemble must enter the project as a real licensed benchmark with explicit protocol constraints. "
            "Official benchmark assets configure NVS/Mono/SVFR tasks; full v2 videos only provide compact local multi-view cases after a visual/VLM gate."
        ),
        "verdict": verdict,
        "official_benchmark": official,
        "compact_candidates": compact,
        "local_visual_audit": local_visual_audit,
        "decision": decision,
        "next_gate": (
            "Implement a NeRSemble adapter that consumes only the selected audited case/protocol, keeps raw RGB local, "
            "declares train/test distribution, and evaluates held-out cameras before any method-quality claim."
        ),
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload, repo)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    if verdict == BLOCKED:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
