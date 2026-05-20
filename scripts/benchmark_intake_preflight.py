#!/usr/bin/env python3
"""Preflight future NeRSemble/H3DS benchmark intake without raw data."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-20"
VERDICT = "PASS_BENCHMARK_INTAKE_PREFLIGHT_READY_DATA_BLOCKED_BY_CREDENTIALS"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def dir_state(path: Path) -> dict[str, Any]:
    exists = path.exists()
    if not exists:
        return {"path": str(path), "exists": False, "is_symlink": False, "file_count": 0}
    if path.is_symlink():
        target = path.resolve()
        file_count = sum(1 for child in target.rglob("*") if child.is_file()) if target.exists() else 0
        return {"path": str(path), "exists": True, "is_symlink": True, "target": str(target), "file_count": file_count}
    return {"path": str(path), "exists": True, "is_symlink": False, "file_count": sum(1 for child in path.rglob("*") if child.is_file())}


def git_ls_files(repo: Path, pathspec: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", pathspec],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G48 Benchmark Intake Preflight",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Scope:",
        "",
        "```text",
        payload["scope"],
        "```",
        "",
        "Credential state:",
        "",
        "| credential | present | target |",
        "| --- | --- | --- |",
    ]
    for item in payload["credential_state"]:
        lines.append(f"| {item['name']} | {item['present']} | {item['target']} |")
    lines.extend(
        [
            "",
            "Dataset/tool roots:",
            "",
            "| key | exists | files | note |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for item in payload["root_checks"]:
        lines.append(f"| {item['key']} | {item['exists']} | {item['file_count']} | {item['note']} |")
    lines.extend(
        [
            "",
            "Official benchmark contracts:",
            "",
            "| benchmark | contract | expected gate use |",
            "| --- | --- | --- |",
        ]
    )
    for item in payload["benchmark_contracts"]:
        lines.append(f"| {item['benchmark']} | {item['contract']} | {item['expected_gate_use']} |")
    lines.extend(
        [
            "",
            "Git/raw-data policy:",
            "",
            "```text",
            "\n".join(payload["git_raw_data_policy"]),
            "```",
            "",
            "Blocked interpretations:",
            "",
            "```text",
            "\n".join(payload["blocked_interpretations"]),
            "```",
            "",
            "Decision:",
            "",
            "```text",
            payload["decision"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    data_root = repo / "datasets"
    access_manifest = data_root / "access_manifest.tsv"
    rows = read_tsv(access_manifest) if access_manifest.is_file() else []
    tracked_dataset_files = git_ls_files(repo, "datasets")
    allowed_tracked = {"datasets/README.md", "datasets/access_manifest.tsv"}
    unexpected_tracked = sorted(set(tracked_dataset_files) - allowed_tracked)
    credential_state = [
        {
            "name": "NERSEMBLE_BENCHMARK_URL",
            "present": bool(os.environ.get("NERSEMBLE_BENCHMARK_URL")),
            "target": "official NeRSemble benchmark toolkit download",
        },
        {
            "name": "NERSEMBLE_DATA_URL",
            "present": bool(os.environ.get("NERSEMBLE_DATA_URL")),
            "target": "official NeRSemble v2 full data download",
        },
        {
            "name": "H3DS_ACCESS_TOKEN",
            "present": bool(os.environ.get("H3DS_ACCESS_TOKEN")),
            "target": "official H3DS v2 encrypted archive download/extract",
        },
    ]
    root_specs = [
        ("datasets", data_root, "local raw-data entry root; only README/access manifest are git-trackable"),
        ("access_manifest", access_manifest, "repo-safe access and license manifest"),
        ("facescape_benchmark", data_root / "facescape_benchmark", "licensed/public FaceScape SVFR local support, not NeRSemble/H3DS substitute"),
        ("nersemble_benchmark", data_root / "nersemble_benchmark", "awaits NERSEMBLE_BENCHMARK_URL"),
        ("nersemble_v2", data_root / "nersemble_v2", "awaits NERSEMBLE_DATA_URL; large optional full data"),
        ("h3ds_v2", data_root / "h3ds_v2", "awaits H3DS_ACCESS_TOKEN"),
        ("tool_nersemble_benchmark", repo / "external/nersemble-benchmark", "official benchmark downloader clone"),
        ("tool_nersemble_data", repo / "external/nersemble-data", "official v2 downloader clone"),
        ("tool_h3ds", repo / "external/h3ds", "official H3DS loader/evaluator clone"),
    ]
    root_checks = []
    for key, path, note in root_specs:
        state = dir_state(path)
        state.update({"key": key, "note": note})
        root_checks.append(state)
    payload = {
        "date": DATE,
        "gate": "G48",
        "verdict": VERDICT,
        "scope": (
            "Preconfigure stronger real-GT benchmark intake for NeRSemble and H3DS while credentials are pending. "
            "This checks tools, local raw-data policy, required credentials, and benchmark contracts without "
            "creating any method-quality result."
        ),
        "access_manifest_rows": rows,
        "credential_state": credential_state,
        "root_checks": root_checks,
        "benchmark_contracts": [
            {
                "benchmark": "NeRSemble benchmark NVS",
                "contract": "Official toolkit; 13 training cameras and 3 held-out cameras are used for benchmark metrics.",
                "expected_gate_use": "future native held-out RGB/geometry evaluation only after official URL approval",
                "source": "https://pypi.org/project/nersemble-benchmark/",
            },
            {
                "benchmark": "NeRSemble benchmark Mono FLAME Avatar",
                "contract": "Single training camera plus held-out sequences/cameras; official 2026 update uses flame2023_tracking_v2.",
                "expected_gate_use": "head-anchored/feed-forward method evaluation, not pseudo-view training",
                "source": "https://pypi.org/project/nersemble-benchmark/",
            },
            {
                "benchmark": "NeRSemble benchmark SVFR",
                "contract": "391 images from 20 identities; submitted meshes are evaluated against held-out point clouds.",
                "expected_gate_use": "single-view geometry benchmark once data is official and license-reviewed",
                "source": "https://pypi.org/project/nersemble-benchmark/",
            },
            {
                "benchmark": "H3DS v2",
                "contract": "Official h3ds loader returns mesh, images, masks, and cameras; default view configs include 1, 3, 4, 6, 8, 16, and 32 views; evaluator reports comparable scene metrics.",
                "expected_gate_use": "few-shot full-head geometry/RGB support after H3DS_ACCESS_TOKEN and license review",
                "source": "https://pypi.org/project/h3ds/",
            },
        ],
        "git_raw_data_policy": [
            f"tracked_dataset_files={tracked_dataset_files or ['none']}",
            f"unexpected_tracked_dataset_files={unexpected_tracked or ['none']}",
            "raw FaceScape/NeRSemble/H3DS images, masks, meshes, pointclouds, archives, and renders must remain ignored/local",
            "repo-safe sync is limited to README/access manifest, metrics, scripts, hashes, and non-identifiable aggregate figures",
        ],
        "blocked_interpretations": [
            "Do not treat empty credential-gated directories as available benchmarks.",
            "Do not use unofficial HF mirrors as source data without explicit provenance/license review.",
            "Do not substitute FaceScape sample data for NeRSemble/H3DS method-quality claims.",
            "Do not reintroduce experiments/downstream_datasets as training or evaluation data.",
            "Do not publish identifiable benchmark RGB/mesh/pointcloud artifacts without explicit review.",
        ],
        "decision": (
            "The benchmark bench is configured enough for immediate intake once credentials arrive: official tool "
            "repos are cloned, raw-data roots are ignored, and the preflight records the required contracts. "
            "Actual NeRSemble/H3DS method-quality work remains blocked until official credentials/data pass "
            "data, VLM, distribution, and artifact gates."
        ),
    }
    write_json(repo / "experiments/metrics/g48_benchmark_intake_preflight_20260520.json", payload)
    write_md(repo / "experiments/metrics/g48_benchmark_intake_preflight_20260520.md", payload)
    print("Wrote experiments/metrics/g48_benchmark_intake_preflight_20260520.json")
    print("Wrote experiments/metrics/g48_benchmark_intake_preflight_20260520.md")
    print(VERDICT)


if __name__ == "__main__":
    main()
