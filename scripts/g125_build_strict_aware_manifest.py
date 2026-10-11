#!/usr/bin/env python3
"""Build the strict identity/confidence-aware manifest for the G81-style arms.

Replicates the G100 policy: keep only identity_supervision and
identity_supervision_weak pseudo views; reject geometry_only views because G99
showed geometry-only hallucinations hurt real held-out metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASS_VERDICT = "PASS_G81_STRICT_AWARE_MANIFEST_READY_PRIVATE"
BLOCKED_VERDICT = "BLOCKED_G81_STRICT_AWARE_MANIFEST_EMPTY"
STRICT_POLICY = (
    "Keep only identity_supervision and identity_supervision_weak pseudo views; "
    "reject geometry_only views because G99 showed geometry-only hallucinations "
    "hurt real held-out metrics."
)


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


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['gate']} G81 Strict-Aware Manifest",
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
        f"| kept_count | {payload['summary']['kept_count']} |",
        f"| rejected_count | {payload['summary']['rejected_count']} |",
        "",
        "Kept views:",
        "",
        "```text",
        ", ".join(str(v) for v in payload["summary"]["kept_views"]),
        "```",
        "",
        "Rejected geometry-only views:",
        "",
        "```text",
        ", ".join(str(v) for v in payload["summary"]["rejected_views"]),
        "```",
        "",
        "Private manifest:",
        "",
        "```text",
        payload["private_outputs"]["strict_manifest"],
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
    parser.add_argument("--aware-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--gate", default="G125")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    aware = load_json(args.aware_manifest)

    strict_views: list[dict[str, Any]] = []
    kept: list[int] = []
    rejected: list[int] = []
    for view in aware.get("pseudo_views", []):
        row = dict(view)
        role = str(view.get("supervision_role", ""))
        if role.startswith("identity_supervision"):
            kept.append(int(view["view_index"]))
        else:
            rejected.append(int(view["view_index"]))
            row["supervision_role"] = "reject_geometry_only_no_identity_anchor"
            row["ri3d_train_candidate"] = False
            row["rgb_weight"] = 0.0
            row["depth_weight"] = 0.0
            row["mask_weight"] = 0.0
        strict_views.append(row)

    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    strict_path = output_root / "identity_confidence_strict_pseudo_supervision_manifest.json"
    manifest = {
        "semantic_type": aware.get("semantic_type"),
        "arm": "identity_confidence_strict_pseudo_view_supervision",
        "source_image": aware.get("source_image"),
        "source_image_sha256": aware.get("source_image_sha256"),
        "zero123_root": aware.get("zero123_root"),
        "zero123_metadata": aware.get("zero123_metadata"),
        "no_leakage_rule": aware.get("no_leakage_rule"),
        "strict_policy": STRICT_POLICY,
        "source_aware_manifest": str(args.aware_manifest),
        "pseudo_views": strict_views,
    }
    write_json(strict_path, manifest)

    verdict = PASS_VERDICT if kept else BLOCKED_VERDICT
    payload = {
        "date": args.date,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": args.gate,
        "verdict": verdict,
        "summary": {
            "kept_count": len(kept),
            "rejected_count": len(rejected),
            "kept_views": kept,
            "rejected_views": rejected,
        },
        "private_outputs": {
            "strict_manifest": str(strict_path),
            "strict_manifest_sha256": sha256_file(strict_path),
        },
        "artifact_policy": "Strict manifest stays under 3dv_work; commit hashes/metrics only.",
        "decision": (
            "Strict-aware manifest is ready for the same private RI3D export/training/render/eval pipeline."
            if kept
            else "Blocked: no identity-anchored pseudo views survived strict filtering."
        ),
    }
    write_json(repo / args.output_json if not args.output_json.is_absolute() else args.output_json, payload)
    write_md(repo / args.output_md if not args.output_md.is_absolute() else args.output_md, payload)
    print(json.dumps({"verdict": verdict, "kept": kept, "rejected": rejected, "strict_manifest": str(strict_path)}, indent=2))
    if verdict != PASS_VERDICT:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
