#!/usr/bin/env python3
"""Run LAM baseline over a manifest and export compact MP4 results."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def run_one(row: dict[str, str], repo: Path, args: argparse.Namespace) -> dict[str, object]:
    sample_id = row["sample_id"]
    input_path = repo / row["input_path"]
    outdir = repo / args.out_root / f"{sample_id}_look_in_my_eyes"
    outdir.mkdir(parents=True, exist_ok=True)
    metadata_path = outdir / "metadata.json"
    if args.skip_existing and (outdir / f"{sample_id}.mp4").exists() and metadata_path.exists():
        print(f"Skip existing: {outdir}")
        return {"sample_id": sample_id, "status": "skipped", "outdir": str(outdir)}

    cmd = [
        "bash",
        str(repo / "scripts/server/03_run_lam_sample.sh"),
        str(input_path),
        args.config,
        args.model,
        args.motion,
    ]
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(repo),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    elapsed = time.time() - start

    log_root = Path(args.log_root)
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"{sample_id}.log"
    log_path.write_text(proc.stdout, encoding="utf-8")

    stem = input_path.stem
    lam_video_root = repo / "external/LAM/exps/videos/lam/lam_20k"
    copied = []
    for suffix, name in [(".mp4", f"{sample_id}.mp4"), ("_audio.mp4", f"{sample_id}_audio.mp4")]:
        src = lam_video_root / f"{stem}{suffix}"
        dst = outdir / name
        if copy_if_exists(src, dst):
            copied.append(str(dst.relative_to(repo)))

    status = "success" if proc.returncode == 0 and copied else "missing_output" if proc.returncode == 0 else "failed"
    metadata = {
        "sample_id": sample_id,
        "input": str(input_path),
        "source": row,
        "status": status,
        "returncode": proc.returncode,
        "elapsed_sec": round(elapsed, 3),
        "command": cmd,
        "config": args.config,
        "model": args.model,
        "motion": args.motion,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "copied_files": copied,
        "log": str(log_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"{sample_id}: {status} -> {outdir}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="data_manifest.csv")
    parser.add_argument("--out-root", default="experiments/reconstructions/lam_first10")
    parser.add_argument("--config", default="configs/inference/lam-20k-8gpu.yaml")
    parser.add_argument("--model", default="model_zoo/lam_models/releases/lam/lam-20k/step_045500/")
    parser.add_argument("--motion", default="assets/sample_motion/export/Look_In_My_Eyes/")
    parser.add_argument("--log-root", default="/data1/workspace/airulan/3dv_work/logs/lam_first10")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    rows = load_rows(repo / args.manifest)
    if args.limit > 0:
        rows = rows[: args.limit]

    results = []
    for row in rows:
        result = run_one(row, repo, args)
        results.append(result)
        if args.stop_on_failure and result.get("status") not in {"success", "skipped"}:
            raise SystemExit(f"LAM failed for {row['sample_id']}")

    summary_path = repo / args.out_root / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
