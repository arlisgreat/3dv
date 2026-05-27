#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${DATA_ROOT:-$ROOT/datasets}"
GHFAST="${GHFAST:-https://ghfast.top/}"
HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export DATA_ROOT

unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY="*"

mkdir -p \
  "$DATA_ROOT/nersemble_benchmark" \
  "$DATA_ROOT/nersemble_v2" \
  "$DATA_ROOT/h3ds_v2" \
  "$DATA_ROOT/hf_candidates" \
  "$DATA_ROOT/_tools" \
  "$ROOT/external"

clone_tool() {
  local name="$1"
  local url="$2"
  local dest="$ROOT/external/$name"
  if [[ -d "$dest/.git" ]]; then
    echo "[skip] $name already cloned at $dest"
    return
  fi
  git clone --depth 1 "${GHFAST}${url}" "$dest"
}

extract_zip() {
  local zip_path="$1"
  local out_dir="$2"
  if command -v unzip >/dev/null 2>&1; then
    unzip -n "$zip_path" -d "$out_dir"
  else
    python3 -m zipfile -e "$zip_path" "$out_dir"
  fi
}

clone_tool facescape https://github.com/zhuhao-nju/facescape.git
clone_tool nersemble-benchmark https://github.com/tobias-kirschstein/nersemble-benchmark.git
clone_tool nersemble-data https://github.com/tobias-kirschstein/nersemble-data.git
clone_tool h3ds https://github.com/CrisalixSA/h3ds.git

ln -sfn "$ROOT/external/facescape/benchmark/data" "$DATA_ROOT/facescape_benchmark"
ln -sfn "$ROOT/external/facescape/samples" "$DATA_ROOT/facescape_sample"
ln -sfn "$ROOT/external/nersemble-benchmark" "$DATA_ROOT/_tools/nersemble-benchmark"
ln -sfn "$ROOT/external/nersemble-data" "$DATA_ROOT/_tools/nersemble-data"
ln -sfn "$ROOT/external/h3ds" "$DATA_ROOT/_tools/h3ds"

if [[ ! -d "$ROOT/external/facescape/benchmark/data/lab_img" ]]; then
  echo "[download] FaceScape SVFR benchmark data"
  mkdir -p "$ROOT/external/facescape/benchmark/data"
  curl -fL --retry 10 --retry-delay 5 \
    "https://box.nju.edu.cn/f/5184eb3d6bab458c9aee/?dl=1" \
    -o "$ROOT/external/facescape/benchmark/data/data.zip"
  extract_zip "$ROOT/external/facescape/benchmark/data/data.zip" "$ROOT/external/facescape/benchmark/data"
else
  echo "[skip] FaceScape SVFR benchmark already extracted"
fi

export NERSEMBLE_BENCHMARK_URL="${NERSEMBLE_BENCHMARK_URL:-https://kaldir.vc.cit.tum.de/nersemble/benchmark_v1}"
export NERSEMBLE_DATA_URL="${NERSEMBLE_DATA_URL:-https://kaldir.vc.cit.tum.de/nersemble/v2}"

echo "[download] NeRSemble benchmark data and v2 metadata"
python3 "$ROOT/scripts/download_nersemble_official.py" \
  --out "$DATA_ROOT" \
  --benchmark-url "$NERSEMBLE_BENCHMARK_URL" \
  --data-url "$NERSEMBLE_DATA_URL" \
  --scope benchmark_svfr \
  --scope benchmark_nvs \
  --scope benchmark_mono \
  --scope v2_full \
  --manifest "$DATA_ROOT/nersemble_full_manifest.tsv" \
  --workers "${NERSEMBLE_WORKERS:-4}"

if [[ -n "${NERSEMBLE_DATA_URL:-}" && "${NERSEMBLE_DOWNLOAD_FULL:-0}" == "1" ]]; then
  echo "[download] NeRSemble v2 full data; this can exceed 1.5TB"
  printf 'y\n' | PYTHONPATH="$ROOT/external/nersemble-data/src:${PYTHONPATH:-}" \
    python3 "$ROOT/external/nersemble-data/scripts/manage_data.py" \
    download "$DATA_ROOT/nersemble_v2" --n-workers 4
else
  echo "[blocked] Set NERSEMBLE_DATA_URL and NERSEMBLE_DOWNLOAD_FULL=1 for full NeRSemble v2"
fi

if [[ -n "${H3DS_ACCESS_TOKEN:-}" ]]; then
  echo "[download] H3DS v2 data"
  PYTHONPATH="$ROOT/external/h3ds:${PYTHONPATH:-}" \
    python3 - <<'PY'
import os
from h3ds.dataset import H3DS

H3DS(path=os.environ["DATA_ROOT"] + "/h3ds_v2", config_id="config_v2").download(
    token=os.environ["H3DS_ACCESS_TOKEN"]
)
PY
else
  echo "[blocked] Set H3DS_ACCESS_TOKEN to download/extract official H3DS v2"
fi

if [[ "${INCLUDE_UNOFFICIAL_HF:-0}" == "1" ]]; then
  echo "[download] Optional unofficial HF rendered_mini_FaceScape_db"
  target="$DATA_ROOT/hf_candidates/rendered_mini_FaceScape_db"
  mkdir -p "$target"
  curl -fL -C - --retry 10 --retry-delay 5 \
    "$HF_ENDPOINT/datasets/MahdiGhafourian/rendered_mini_FaceScape_db/resolve/main/mini_Facescape_db.zip?download=true" \
    -o "$target/mini_Facescape_db.zip"
  extract_zip "$target/mini_Facescape_db.zip" "$target"
else
  echo "[skip] Unofficial HF candidates are listed in datasets/access_manifest.tsv but not downloaded"
fi
