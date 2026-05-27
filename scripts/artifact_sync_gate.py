#!/usr/bin/env python3
"""Check that experiment artifacts are repo-syncable before pushing.

The gate distinguishes allowed compact experiment outputs from raw/private
assets. It intentionally treats newly generated repo-safe artifacts as sync
candidates instead of silently ignoring them.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
PASS_VERDICT = "PASS_ARTIFACT_SYNC_GATE_READY"
BLOCKED_VERDICT = "BLOCKED_ARTIFACT_SYNC_GATE"
RESULT_SUFFIXES = {".csv", ".json", ".md", ".mp4", ".png", ".svg", ".tsv"}
ALLOWED_PREFIXES = (
    "experiments/inputs/",
    "experiments/pseudo_views/",
    "experiments/reconstructions/",
    "experiments/metrics/",
    "experiments/figures/",
    "experiments/gt_cases/",
    "experiments/real_gt_benchmark/",
    "experiments/ri3d_datasets/",
    "patches/",
    "skills/",
    "scripts/",
    "docs/",
)
PRIVATE_TOKENS = (
    "/raw_extract/",
    "3dv_work/datasets",
)


def run_git(repo: Path, *args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=repo, check=True, text=True, stdout=subprocess.PIPE)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def is_result_artifact(path: str) -> bool:
    return Path(path).suffix.lower() in RESULT_SUFFIXES


def is_allowed_path(path: str) -> bool:
    return path in {
        "README.md",
        "MILESTONES.md",
        "EXPERIMENTS.md",
        ".gitignore",
        "datasets/README.md",
        "datasets/access_manifest.tsv",
        "external/repos.tsv",
        "external/repos.lock.tsv",
    } or path.startswith(ALLOWED_PREFIXES)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} Artifact Sync Gate",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Counts:",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| tracked_result_artifacts | {payload['counts']['tracked_result_artifacts']} |",
        f"| untracked_allowed_sync_candidates | {payload['counts']['untracked_allowed_sync_candidates']} |",
        f"| blocked_untracked_paths | {payload['counts']['blocked_untracked_paths']} |",
        f"| oversized_sync_candidates | {payload['counts']['oversized_sync_candidates']} |",
        "",
        "Untracked allowed sync candidates:",
        "",
        "```text",
        "\n".join(payload["untracked_allowed_sync_candidates"]) or "none",
        "```",
        "",
        "Blocked paths:",
        "",
        "```text",
        "\n".join(payload["blocked_untracked_paths"]) or "none",
        "```",
        "",
        "Decision:",
        "",
        "```text",
        payload["decision"],
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--gate", default="G38")
    parser.add_argument("--date", default=DATE)
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g38_artifact_sync_gate_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g38_artifact_sync_gate_20260520.md"))
    parser.add_argument("--max-size-mb", type=float, default=100.0)
    args = parser.parse_args()

    repo = args.repo.resolve()
    tracked = run_git(repo, "ls-files")
    untracked = run_git(repo, "ls-files", "--others", "--exclude-standard")

    tracked_results = [path for path in tracked if path.startswith("experiments/") and is_result_artifact(path)]
    untracked_result_like = [path for path in untracked if is_result_artifact(path) or is_allowed_path(path)]
    untracked_allowed = [path for path in untracked_result_like if is_allowed_path(path)]
    blocked = [path for path in untracked_result_like if not is_allowed_path(path)]
    private_hits = [path for path in tracked + untracked_allowed if any(token in path for token in PRIVATE_TOKENS)]
    oversized: list[dict[str, Any]] = []
    max_bytes = int(args.max_size_mb * 1024 * 1024)
    for path in untracked_allowed:
        full = repo / path
        if full.is_file() and full.stat().st_size > max_bytes:
            oversized.append({"path": path, "size_bytes": full.stat().st_size})

    failed = blocked + private_hits + [item["path"] for item in oversized]
    verdict = PASS_VERDICT if not failed else BLOCKED_VERDICT
    if verdict == PASS_VERDICT and untracked_allowed:
        decision = "All current untracked result artifacts are repo-safe sync candidates. Stage them with the milestone docs, commit, and push."
    elif verdict == PASS_VERDICT:
        decision = "All current repo-safe result artifacts are tracked or staged; commit and push this checkpoint."
    else:
        decision = "Blocked: remove private/raw paths from repo sync or move them under 3dv_work before commit."
    payload = {
        "date": args.date,
        "gate": args.gate,
        "verdict": verdict,
        "counts": {
            "tracked_result_artifacts": len(tracked_results),
            "untracked_allowed_sync_candidates": len(untracked_allowed),
            "blocked_untracked_paths": len(blocked) + len(private_hits),
            "oversized_sync_candidates": len(oversized),
        },
        "untracked_allowed_sync_candidates": sorted(untracked_allowed),
        "blocked_untracked_paths": sorted(set(blocked + private_hits)),
        "oversized_sync_candidates": oversized,
        "decision": decision,
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
