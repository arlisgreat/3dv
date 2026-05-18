#!/usr/bin/env bash
set -euo pipefail

CUDA_TAG="${1:-cu121}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAM_DIR="$ROOT/external/LAM"

if [[ "$CUDA_TAG" != "cu121" && "$CUDA_TAG" != "cu118" ]]; then
  echo "Usage: $0 <cu121|cu118>"
  exit 1
fi

if [[ ! -d "$LAM_DIR" ]]; then
  echo "Missing $LAM_DIR. Run: bash scripts/clone_external.sh P0"
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "lam"; then
  conda create -y -n lam python=3.10
fi

conda activate lam

export PIP_CACHE_DIR="${CACHE_ROOT:-$ROOT/.cache}/pip"
mkdir -p "$PIP_CACHE_DIR"

cd "$LAM_DIR"

if [[ "$CUDA_TAG" == "cu121" ]]; then
  bash scripts/install/install_cu121.sh
else
  bash scripts/install/install_cu118.sh
fi

python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

