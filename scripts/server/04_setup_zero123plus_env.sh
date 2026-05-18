#!/usr/bin/env bash
set -euo pipefail

CUDA_TAG="${1:-cu121}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ZERO_DIR="$ROOT/external/zero123plus"

if [[ "$CUDA_TAG" != "cu121" && "$CUDA_TAG" != "cu118" ]]; then
  echo "Usage: $0 <cu121|cu118>"
  exit 1
fi

if [[ ! -d "$ZERO_DIR" ]]; then
  echo "Missing $ZERO_DIR. Run: bash scripts/clone_external.sh P0"
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "zero123plus"; then
  conda create -y -n zero123plus python=3.10
fi

conda activate zero123plus

export PIP_CACHE_DIR="${CACHE_ROOT:-$ROOT/.cache}/pip"
mkdir -p "$PIP_CACHE_DIR"

if [[ "$CUDA_TAG" == "cu121" ]]; then
  pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu121
else
  pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118
fi

cd "$ZERO_DIR"
pip install -r requirements.txt

python - <<'PY'
import torch
import diffusers
import transformers
print("torch", torch.__version__)
print("diffusers", diffusers.__version__)
print("transformers", transformers.__version__)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

