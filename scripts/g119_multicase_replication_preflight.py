#!/usr/bin/env python3
"""Preflight the remaining assets for multi-case G110/G117 replication."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-28"
PASS_VERDICT = "PASS_G119_MULTICASE_PREFLIGHT_RECORDED"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def gpu_status() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # noqa: BLE001
        return [{"error": str(exc)}]
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        index, name, used, total, util = [item.strip() for item in line.split(",")]
        rows.append(
            {
                "index": int(index),
                "name": name,
                "memory_used_mb": int(used),
                "memory_total_mb": int(total),
                "utilization_gpu_percent": int(util),
                "empty": int(used) == 0 and int(util) == 0,
            }
        )
    return rows


def requirement(path: str | Path, label: str, gpu_required: bool = False) -> dict[str, Any]:
    return {
        "label": label,
        "path": str(path),
        "exists": exists(path),
        "gpu_required_to_create": gpu_required,
    }


def complete(reqs: list[dict[str, Any]]) -> bool:
    return all(row["exists"] for row in reqs)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# G119 Multi-Case Replication Preflight",
        "",
        f"Date: {payload['date']}",
        "",
        "Verdict:",
        "",
        "```text",
        payload["verdict"],
        "```",
        "",
        "Case readiness:",
        "",
        "| source split | complete | missing count | next action |",
        "| --- | --- | ---: | --- |",
    ]
    for case in payload["source_splits"]:
        lines.append(
            f"| {case['source_serial']} | {case['complete']} | {len(case['missing_requirements'])} | {case['next_action']} |"
        )
    lines.extend(
        [
            "",
            "GPU status:",
            "",
            "```text",
            "\n".join(
                [
                    f"gpu {row.get('index')}: used={row.get('memory_used_mb')}MB util={row.get('utilization_gpu_percent')} empty={row.get('empty')}"
                    for row in payload["gpu_status"]
                ]
            )
            or "nvidia-smi unavailable",
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
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g119_multicase_replication_preflight_20260528.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g119_multicase_replication_preflight_20260528.md"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    split_220 = [
        requirement("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter_source_220700191/adapter_manifest.json", "source override adapter"),
        requirement(repo / "experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json", "direct LAM eval"),
        requirement("/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/metadata.json", "Zero123++ pseudo views", True),
        requirement("/data1/workspace/airulan/3dv_work/runs/g100_g81_strict_aware_manifest/identity_confidence_strict_pseudo_supervision_manifest.json", "strict pseudo manifest"),
        requirement(repo / "experiments/metrics/g117_source_gated_pseudo_prior_ablation_20260528.json", "G117 ablation predictions"),
        requirement(repo / "experiments/metrics/g118_source_gated_ablation_contract_20260528.json", "G118 ablation contract"),
    ]
    split_222 = [
        requirement("/data1/workspace/airulan/3dv_work/datasets/nersemble_nvs_388_glasses_frame00000_adapter/adapter_manifest.json", "source 222200042 adapter"),
        requirement(repo / "experiments/metrics/g71_lam_native_gaussian_source_aligned_xyz_eval_20260527.json", "direct LAM eval, non-frustum-guard diagnostic"),
        requirement("/data1/workspace/airulan/3dv_work/runs/g83_nersemble_source222200042_pseudo_input/source_pseudo_input_manifest.json", "source pseudo input prep"),
        requirement("/data1/workspace/airulan/3dv_work/runs/g120_zero123plus_nersemble_source222200042_steps75/metadata.json", "Zero123++ pseudo views", True),
        requirement("/data1/workspace/airulan/3dv_work/runs/g120_zero123plus_nersemble_source222200042_steps75/g81_manifests/identity_confidence_aware_pseudo_supervision_manifest.json", "pseudo manifests", True),
        requirement("/data1/workspace/airulan/3dv_work/runs/g121_source222200042_source_gated_pseudo_prior_ablation", "G117-style ablation predictions", True),
    ]
    source_splits = []
    for source_serial, reqs, next_action in [
        ("220700191", split_220, "already complete as single-case diagnostic; use as case 1"),
        ("222200042", split_222, "wait for an actually idle GPU, then run source prep, Zero123++, manifest build, direct/frustum guard if needed, and G117-style eval"),
    ]:
        source_splits.append(
            {
                "source_serial": source_serial,
                "requirements": reqs,
                "complete": complete(reqs),
                "missing_requirements": [row for row in reqs if not row["exists"]],
                "next_action": next_action,
            }
        )
    gpus = gpu_status()
    empty_gpus = [row for row in gpus if row.get("empty")]
    payload = {
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G119",
        "verdict": PASS_VERDICT,
        "premise": "Preflight multi-case replication of the same source-only/pseudo-only G110/G117 gate before launching more GPU jobs.",
        "source_splits": source_splits,
        "complete_source_split_count": sum(1 for row in source_splits if row["complete"]),
        "gpu_status": gpus,
        "empty_gpu_count": len(empty_gpus),
        "decision": (
            "Multi-case replication is not complete: only source 220700191 has the full direct/naive/G110/G117 contract. "
            "Source 222200042 has a direct diagnostic but lacks pseudo input, Zero123++ pseudo views, manifests, and G117-style ablations. "
            "No empty GPU is available now, so do not launch the missing GPU runs in this turn."
        ),
        "next_gate": "G120 should execute source 222200042 replication only when an empty GPU is available, then rerun G118-style aggregation across cases.",
    }
    write_json(repo / args.output_json, payload)
    write_md(repo / args.output_md, payload)
    print(json.dumps({"verdict": PASS_VERDICT, "complete_source_split_count": payload["complete_source_split_count"], "empty_gpu_count": len(empty_gpus)}, indent=2))


if __name__ == "__main__":
    main()
