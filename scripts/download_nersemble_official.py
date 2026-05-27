#!/usr/bin/env python3
import argparse
import csv
import json
import os
import runpy
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_CONSTANTS = ROOT / "external/nersemble-benchmark/src/nersemble_benchmark/constants.py"
DATA_CONSTANTS = ROOT / "external/nersemble-data/src/nersemble_data/constants.py"


def load_constants(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return runpy.run_path(str(path))


def curl_env() -> dict:
    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)
    env["NO_PROXY"] = "*"
    return env


def add(urls: list[tuple[str, Path]], root: Path, base_url: str, rel: str) -> None:
    urls.append((f"{base_url.rstrip('/')}/{rel}", root / rel))


def benchmark_svfr_urls(out: Path, base_url: str, constants: dict) -> list[tuple[str, Path]]:
    urls: list[tuple[str, Path]] = []
    root = out / "nersemble_benchmark/svfr"
    for p_id, image_keys in constants["BENCHMARK_SVFR_IMAGE_KEYS"].items():
        for seq_name, timestep, serial in image_keys:
            rel = f"{p_id:03d}/{seq_name}_{timestep}_{serial}/rgb.png"
            add(urls, root, f"{base_url}/svfr", rel)
    return urls


def benchmark_nvs_urls(out: Path, base_url: str, constants: dict) -> list[tuple[str, Path]]:
    urls: list[tuple[str, Path]] = []
    root = out / "nersemble_benchmark/nvs"
    metadata_url = f"{base_url.rstrip('/')}/nvs/metadata.json"
    add(urls, root, f"{base_url}/nvs", "metadata.json")
    with urlopen(metadata_url, timeout=30) as handle:
        metadata = json.load(handle)

    train_serials = constants["BENCHMARK_NVS_TRAIN_SERIALS"]
    for p_id, seq_name in constants["BENCHMARK_NVS_IDS_AND_SEQUENCES"]:
        add(urls, root, f"{base_url}/nvs", f"{p_id:03d}/calibration/camera_params.json")
        for serial in train_serials:
            add(urls, root, f"{base_url}/nvs", f"{p_id:03d}/sequences/{seq_name}/images/cam_{serial}.mp4")
            add(urls, root, f"{base_url}/nvs", f"{p_id:03d}/sequences/{seq_name}/alpha_maps/cam_{serial}.mp4")
        sequence_meta = metadata["sequences"][str(p_id)]
        first_timestep = sequence_meta["timesteps"][0]
        add(urls, root, f"{base_url}/nvs", f"{p_id:03d}/sequences/{seq_name}/pointclouds/frame_{first_timestep:05d}.pcd")
    return urls


def benchmark_mono_urls(out: Path, base_url: str, constants: dict) -> list[tuple[str, Path]]:
    urls: list[tuple[str, Path]] = []
    root = out / "nersemble_benchmark/mono_flame_avatar"
    add(urls, root, f"{base_url}/mono_flame_avatar", "metadata.json")
    train_serial = constants["BENCHMARK_MONO_FLAME_AVATAR_TRAIN_SERIAL"]
    for p_id in constants["BENCHMARK_MONO_FLAME_AVATAR_IDS"]:
        add(urls, root, f"{base_url}/mono_flame_avatar", f"{p_id:03d}/calibration/camera_params.json")
        for seq_name in constants["BENCHMARK_MONO_FLAME_AVATAR_SEQUENCES_TRAIN"]:
            add(urls, root, f"{base_url}/mono_flame_avatar", f"{p_id:03d}/sequences/{seq_name}/tracking/flame2023_tracking_v2.npz")
            add(urls, root, f"{base_url}/mono_flame_avatar", f"{p_id:03d}/sequences/{seq_name}/images/cam_{train_serial}.mp4")
            add(urls, root, f"{base_url}/mono_flame_avatar", f"{p_id:03d}/sequences/{seq_name}/alpha_maps/cam_{train_serial}.mp4")
        for seq_name in constants["BENCHMARK_MONO_FLAME_AVATAR_SEQUENCES_TEST"]:
            add(urls, root, f"{base_url}/mono_flame_avatar", f"{p_id:03d}/sequences/{seq_name}/tracking/flame2023_tracking_v2.npz")
    return urls


def v2_metadata_urls(out: Path, data_url: str) -> list[tuple[str, Path]]:
    root = out / "nersemble_v2"
    return [
        (f"{data_url.rstrip('/')}/README.md", root / "README.md"),
        (f"{data_url.rstrip('/')}/metadata_participants.csv", root / "metadata_participants.csv"),
        (f"{data_url.rstrip('/')}/metadata_sequences.csv", root / "metadata_sequences.csv"),
    ]


def v2_calibration_urls(out: Path, data_url: str) -> list[tuple[str, Path]]:
    root = out / "nersemble_v2"
    metadata_path = root / "metadata_sequences.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Download v2_metadata first: {metadata_path}")
    urls: list[tuple[str, Path]] = []
    with metadata_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            p_id = int(row["ID"])
            add(urls, root, data_url, f"{p_id:03d}/calibration/camera_params.json")
            add(urls, root, data_url, f"{p_id:03d}/calibration/color_calibration.json")
    return urls


def v2_compact_urls(out: Path, data_url: str, participant: int, sequence: str, cameras: list[str], constants: dict) -> list[tuple[str, Path]]:
    root = out / "nersemble_v2"
    urls: list[tuple[str, Path]] = []
    add(urls, root, data_url, f"{participant:03d}/calibration/camera_params.json")
    add(urls, root, data_url, f"{participant:03d}/calibration/color_calibration.json")
    for serial in cameras:
        add(urls, root, data_url, f"{participant:03d}/sequences/BACKGROUND/image_{serial}.jpg")
        add(urls, root, data_url, f"{participant:03d}/sequences/{sequence}/images/cam_{serial}.mp4")
    return urls


def v2_full_urls(out: Path, data_url: str, constants: dict) -> list[tuple[str, Path]]:
    root = out / "nersemble_v2"
    metadata_path = root / "metadata_sequences.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Download v2_metadata first: {metadata_path}")

    urls = v2_metadata_urls(out, data_url)
    cameras = constants["SERIALS"]
    with metadata_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            p_id = int(row["ID"])
            add(urls, root, data_url, f"{p_id:03d}/calibration/camera_params.json")
            add(urls, root, data_url, f"{p_id:03d}/calibration/color_calibration.json")
            for serial in cameras:
                add(urls, root, data_url, f"{p_id:03d}/sequences/BACKGROUND/image_{serial}.jpg")
            for seq_name, availability in row.items():
                if seq_name in ("ID", "wears_glasses", "BACKGROUND"):
                    continue
                if availability not in ("x", "m"):
                    continue
                for serial in cameras:
                    add(urls, root, data_url, f"{p_id:03d}/sequences/{seq_name}/images/cam_{serial}.mp4")
    return urls


def download_one(item: tuple[str, Path], env: dict) -> tuple[str, str, str]:
    url, target = item
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "curl",
        "-fL",
        "-C",
        "-",
        "--retry",
        "10",
        "--retry-delay",
        "5",
        "--speed-limit",
        "1024",
        "--speed-time",
        "120",
        "-o",
        str(target),
        url,
    ]
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    status = "ok" if result.returncode == 0 else f"failed:{result.returncode}"
    message = (result.stderr or result.stdout).strip().splitlines()[-1:] or [""]
    return status, url, str(target), message[0]


def init_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["status", "url", "local_path", "message"])


def append_manifest(path: Path, row: tuple[str, str, str, str]) -> None:
    with path.open("a", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(row)


def completed_targets(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("status") == "ok":
                done.add(row.get("local_path", ""))
    return done


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "datasets")
    parser.add_argument("--benchmark-url", default=os.environ.get("NERSEMBLE_BENCHMARK_URL", "https://kaldir.vc.cit.tum.de/nersemble/benchmark_v1"))
    parser.add_argument("--data-url", default=os.environ.get("NERSEMBLE_DATA_URL", "https://kaldir.vc.cit.tum.de/nersemble/v2"))
    parser.add_argument(
        "--scope",
        action="append",
        choices=["benchmark_svfr", "benchmark_nvs", "benchmark_mono", "v2_metadata", "v2_calibrations", "v2_compact", "v2_full"],
        default=[],
    )
    parser.add_argument("--v2-participant", type=int, default=17)
    parser.add_argument("--v2-sequence", default="EXP-1-head")
    parser.add_argument("--v2-cameras", default="222200037")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/nersemble_download_manifest.tsv")
    args = parser.parse_args()

    scopes = args.scope or ["benchmark_svfr", "benchmark_nvs", "benchmark_mono", "v2_metadata"]
    benchmark_constants = load_constants(BENCHMARK_CONSTANTS)
    data_constants = load_constants(DATA_CONSTANTS)
    urls: list[tuple[str, Path]] = []

    if "benchmark_svfr" in scopes:
        urls.extend(benchmark_svfr_urls(args.out, args.benchmark_url, benchmark_constants))
    if "benchmark_nvs" in scopes:
        urls.extend(benchmark_nvs_urls(args.out, args.benchmark_url, benchmark_constants))
    if "benchmark_mono" in scopes:
        urls.extend(benchmark_mono_urls(args.out, args.benchmark_url, benchmark_constants))
    if "v2_metadata" in scopes:
        urls.extend(v2_metadata_urls(args.out, args.data_url))
    if "v2_calibrations" in scopes:
        urls.extend(v2_calibration_urls(args.out, args.data_url))
    if "v2_compact" in scopes:
        cameras = [camera.strip() for camera in args.v2_cameras.split(",") if camera.strip()]
        urls.extend(v2_compact_urls(args.out, args.data_url, args.v2_participant, args.v2_sequence, cameras, data_constants))
    if "v2_full" in scopes:
        urls.extend(v2_full_urls(args.out, args.data_url, data_constants))

    seen: set[str] = set()
    unique_urls: list[tuple[str, Path]] = []
    for url, target in urls:
        key = str(target)
        if key not in seen:
            unique_urls.append((url, target))
            seen.add(key)

    already_done = completed_targets(args.manifest)
    if already_done:
        before = len(unique_urls)
        unique_urls = [(url, target) for url, target in unique_urls if str(target) not in already_done]
        print(f"Skipping {before - len(unique_urls)} files already marked ok in {args.manifest}")

    print(f"Downloading {len(unique_urls)} NeRSemble files into {args.out}")
    env = curl_env()
    init_manifest(args.manifest)
    failures = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        future_map = {pool.submit(download_one, item, env): item for item in unique_urls}
        for future in as_completed(future_map):
            status, url, target, message = future.result()
            completed += 1
            append_manifest(args.manifest, (status, url, target, message))
            if status != "ok":
                failures += 1
                print(f"[{status}] {url}", file=sys.stderr)
            elif completed % 25 == 0:
                print(f"completed {completed}/{len(unique_urls)}")

    print(f"Wrote manifest: {args.manifest}")
    if failures:
        print(f"{failures} downloads failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
