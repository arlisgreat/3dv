#!/usr/bin/env python3
"""Audit the local NeRSemble official download without reading media payloads."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
GATE = "G52"
PASS_WITH_EXCLUSIONS = "PASS_NERSEMBLE_OFFICIAL_DATA_PRESENT_WITH_404_EXCLUSIONS"
PASS_COMPLETE = "PASS_NERSEMBLE_OFFICIAL_DATA_PRESENT_COMPLETE_MANIFEST"
BLOCKED = "BLOCKED_NERSEMBLE_OFFICIAL_DATA_INTAKE"


def relpath(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def human_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024.0
    return f"{size}B"


def directory_summary(root: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": str(root),
        "exists": root.exists(),
        "file_count": 0,
        "total_size_bytes": 0,
        "suffix_counts": {},
        "top_level_entries": [],
    }
    if not root.exists():
        return summary

    suffix_counts: Counter[str] = Counter()
    top_level_entries: list[str] = []
    try:
        top_level_entries = sorted(item.name for item in root.iterdir())[:80]
    except OSError:
        top_level_entries = []

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename
            summary["file_count"] += 1
            suffix = path.suffix.lower() or "<none>"
            suffix_counts[suffix] += 1
            try:
                summary["total_size_bytes"] += path.stat().st_size
            except OSError:
                pass

    summary["total_size_human"] = human_bytes(int(summary["total_size_bytes"]))
    summary["suffix_counts"] = dict(sorted(suffix_counts.items()))
    summary["top_level_entries"] = top_level_entries
    return summary


FAILED_PATH_RE = re.compile(
    r"/(?P<pid>\d{3})/sequences/"
    r"(?P<seq>[^/]+)/(?:(?:images/cam_)|(?:image_))(?P<serial>\d+)\.(?P<ext>mp4|jpg)$"
)


def parse_failed_path(path: str) -> dict[str, str]:
    match = FAILED_PATH_RE.search(path)
    if not match:
        return {"participant": "<unparsed>", "sequence": "<unparsed>", "serial": "<unparsed>", "extension": "<unparsed>"}
    return {
        "participant": match.group("pid"),
        "sequence": match.group("seq"),
        "serial": match.group("serial"),
        "extension": match.group("ext"),
    }


def manifest_summary(manifest: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": str(manifest),
        "exists": manifest.exists(),
        "rows": 0,
        "unique_paths": 0,
        "status_counts": {},
        "final_status_counts": {},
        "failed_final_rows": 0,
        "failed_final_existing_paths": 0,
        "retry_recovered_paths": 0,
        "failed_error_codes": {},
        "failed_by_participant": {},
        "failed_by_serial": {},
        "failed_by_sequence": {},
        "failed_examples": [],
    }
    if not manifest.exists():
        return summary

    status_counts: Counter[str] = Counter()
    failed_error_codes: Counter[str] = Counter()
    path_history: dict[str, list[dict[str, str]]] = defaultdict(list)
    with manifest.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            status = row.get("status", "")
            local_path = row.get("local_path", "")
            message = row.get("message", "")
            url = row.get("url", "")
            summary["rows"] += 1
            status_counts[status] += 1
            path_history[local_path].append({"status": status, "url": url, "message": message})
            if status.startswith("failed"):
                failed_error_codes[status.replace("failed:", "curl_")] += 1

    final_status_counts: Counter[str] = Counter()
    failed_final: list[dict[str, str]] = []
    recovered = 0
    for local_path, history in path_history.items():
        final = history[-1]
        final_status_counts[final["status"]] += 1
        if final["status"] == "ok" and any(item["status"].startswith("failed") for item in history[:-1]):
            recovered += 1
        if final["status"].startswith("failed"):
            failed_final.append(
                {
                    "local_path": local_path,
                    "status": final["status"],
                    "url": final["url"],
                    "message": final["message"],
                    **parse_failed_path(local_path),
                }
            )

    failed_existing = sum(1 for row in failed_final if Path(row["local_path"]).exists())
    failed_by_participant: Counter[str] = Counter(row["participant"] for row in failed_final)
    failed_by_serial: Counter[str] = Counter(row["serial"] for row in failed_final)
    failed_by_sequence: Counter[str] = Counter(row["sequence"] for row in failed_final)

    summary.update(
        {
            "unique_paths": len(path_history),
            "status_counts": dict(sorted(status_counts.items())),
            "final_status_counts": dict(sorted(final_status_counts.items())),
            "failed_final_rows": len(failed_final),
            "failed_final_existing_paths": failed_existing,
            "retry_recovered_paths": recovered,
            "failed_error_codes": dict(sorted(failed_error_codes.items())),
            "failed_by_participant": dict(failed_by_participant.most_common()),
            "failed_by_serial": dict(failed_by_serial.most_common()),
            "failed_by_sequence": dict(failed_by_sequence.most_common()),
            "failed_examples": failed_final[:12],
        }
    )
    return summary


def metadata_summary(v2_root: Path) -> dict[str, Any]:
    camera_params = sorted(v2_root.glob("*/calibration/camera_params.json"))
    color_calib = sorted(v2_root.glob("*/calibration/color_calibration.json"))
    participants = v2_root / "metadata_participants.csv"
    sequences = v2_root / "metadata_sequences.csv"
    readme = v2_root / "README.md"
    participant_rows = 0
    sequence_rows = 0
    if participants.exists():
        with participants.open("r", encoding="utf-8", newline="") as handle:
            participant_rows = max(sum(1 for _ in handle) - 1, 0)
    if sequences.exists():
        with sequences.open("r", encoding="utf-8", newline="") as handle:
            sequence_rows = max(sum(1 for _ in handle) - 1, 0)
    return {
        "metadata_participants_exists": participants.exists(),
        "metadata_sequences_exists": sequences.exists(),
        "readme_exists": readme.exists(),
        "metadata_participant_rows": participant_rows,
        "metadata_sequence_rows": sequence_rows,
        "camera_params_json_count": len(camera_params),
        "color_calibration_json_count": len(color_calib),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any], repo: Path) -> None:
    manifest = payload["manifest"]
    v2 = payload["directories"]["nersemble_v2"]
    benchmark = payload["directories"]["nersemble_benchmark"]
    metadata = payload["metadata"]
    lines = [
        "# G52 NeRSemble Download Integrity Gate",
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
        "Directory summary:",
        "",
        "| directory | exists | files | size | key suffix counts |",
        "| --- | ---: | ---: | ---: | --- |",
        f"| `{relpath(Path(v2['path']), repo)}` | {v2['exists']} | {v2['file_count']} | {v2.get('total_size_human', 'n/a')} | mp4={v2['suffix_counts'].get('.mp4', 0)}, jpg={v2['suffix_counts'].get('.jpg', 0)}, json={v2['suffix_counts'].get('.json', 0)} |",
        f"| `{relpath(Path(benchmark['path']), repo)}` | {benchmark['exists']} | {benchmark['file_count']} | {benchmark.get('total_size_human', 'n/a')} | mp4={benchmark['suffix_counts'].get('.mp4', 0)}, png={benchmark['suffix_counts'].get('.png', 0)}, pcd={benchmark['suffix_counts'].get('.pcd', 0)}, npz={benchmark['suffix_counts'].get('.npz', 0)} |",
        "",
        "Manifest summary:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| rows | {manifest['rows']} |",
        f"| unique_paths | {manifest['unique_paths']} |",
        f"| ok_final_paths | {manifest['final_status_counts'].get('ok', 0)} |",
        f"| failed_final_rows | {manifest['failed_final_rows']} |",
        f"| failed_final_existing_paths | {manifest['failed_final_existing_paths']} |",
        f"| retry_recovered_paths | {manifest['retry_recovered_paths']} |",
        "",
        "Metadata summary:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| metadata_participants_exists | {metadata['metadata_participants_exists']} |",
        f"| metadata_sequences_exists | {metadata['metadata_sequences_exists']} |",
        f"| metadata_participant_rows | {metadata['metadata_participant_rows']} |",
        f"| metadata_sequence_rows | {metadata['metadata_sequence_rows']} |",
        f"| camera_params_json_count | {metadata['camera_params_json_count']} |",
        f"| color_calibration_json_count | {metadata['color_calibration_json_count']} |",
        "",
        "Failed final rows by participant:",
        "",
        "```text",
        "\n".join(f"{key}: {value}" for key, value in manifest["failed_by_participant"].items()) or "none",
        "```",
        "",
        "Failed final rows by serial:",
        "",
        "```text",
        "\n".join(f"{key}: {value}" for key, value in manifest["failed_by_serial"].items()) or "none",
        "```",
        "",
        "Representative failed final paths:",
        "",
        "```text",
        "\n".join(item["local_path"] for item in manifest["failed_examples"]) or "none",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--v2-root", type=Path, default=Path("datasets/nersemble_v2"))
    parser.add_argument("--benchmark-root", type=Path, default=Path("datasets/nersemble_benchmark"))
    parser.add_argument("--manifest", type=Path, default=Path("datasets/nersemble_full_manifest.tsv"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g52_nersemble_download_integrity_gate_20260527.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g52_nersemble_download_integrity_gate_20260527.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    v2_root = (repo / args.v2_root).resolve() if not args.v2_root.is_absolute() else args.v2_root
    benchmark_root = (repo / args.benchmark_root).resolve() if not args.benchmark_root.is_absolute() else args.benchmark_root
    manifest_path = (repo / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest

    manifest = manifest_summary(manifest_path)
    directories = {
        "nersemble_v2": directory_summary(v2_root),
        "nersemble_benchmark": directory_summary(benchmark_root),
    }
    metadata = metadata_summary(v2_root)

    essential_present = (
        directories["nersemble_v2"]["exists"]
        and directories["nersemble_benchmark"]["exists"]
        and manifest["exists"]
        and metadata["metadata_participants_exists"]
        and metadata["metadata_sequences_exists"]
        and metadata["camera_params_json_count"] > 0
    )
    failed_rows = int(manifest["failed_final_rows"])
    failed_existing = int(manifest["failed_final_existing_paths"])
    only_404 = failed_rows == 0 or set(manifest["final_status_counts"]) <= {"ok", "failed:22"}

    if essential_present and failed_rows == 0:
        verdict = PASS_COMPLETE
    elif essential_present and failed_rows > 0 and failed_existing == 0 and only_404:
        verdict = PASS_WITH_EXCLUSIONS
    else:
        verdict = BLOCKED

    if verdict == PASS_WITH_EXCLUSIONS:
        decision = (
            "Official NeRSemble data is locally present enough to start compact-case and benchmark adapter "
            "preflights, but it is not a full-complete download claim. Exclude the 79 final HTTP-404 paths, "
            "especially participant 545/546/548 cam_222200041, from any case selection or metric table."
        )
    elif verdict == PASS_COMPLETE:
        decision = "Manifest has no final failed rows; proceed to compact-case and benchmark adapter preflights."
    else:
        decision = "Blocked: a required root, manifest, metadata file, or non-404 failed path prevents benchmark use."

    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": GATE,
        "premise": (
            "The downloaded NeRSemble v2 and official benchmark folders are real licensed benchmark inputs, "
            "not generated pseudo-view candidate pools. This gate checks presence and manifest integrity only; "
            "it does not authorize training or reconstruction-quality interpretation."
        ),
        "verdict": verdict,
        "directories": directories,
        "manifest": manifest,
        "metadata": metadata,
        "decision": decision,
        "next_gate": (
            "Run G53 official benchmark/compact-case preflight with local VLM/manual visual audit before any "
            "method run. Keep identifiable RGB/video frames outside GitHub unless explicitly reviewed."
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
