#!/usr/bin/env bash
set -euo pipefail

METHOD="${1:-hf}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAM_DIR="$ROOT/external/LAM"
CACHE="${CACHE_ROOT:-$ROOT/.cache}"

if [[ "$METHOD" != "hf" && "$METHOD" != "modelscope" ]]; then
  echo "Usage: $0 <hf|modelscope>"
  exit 1
fi

if [[ ! -d "$LAM_DIR" ]]; then
  echo "Missing $LAM_DIR. Run: bash scripts/clone_external.sh P0"
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate lam

export HF_HOME="$CACHE/huggingface"
export TORCH_HOME="$CACHE/torch"
mkdir -p "$HF_HOME" "$TORCH_HOME"

cd "$LAM_DIR"
mkdir -p tmp

if [[ "$METHOD" == "hf" ]]; then
  pip install -U "huggingface_hub[cli]"
  huggingface-cli download 3DAIGC/LAM-assets --local-dir ./tmp
  tar -xf ./tmp/LAM_assets.tar
  tar -xf ./tmp/thirdparty_models.tar
  rm -rf ./tmp
  huggingface-cli download 3DAIGC/LAM-20K --local-dir ./model_zoo/lam_models/releases/lam/lam-20k/step_045500/
else
  pip install -U modelscope
  modelscope download --model "Damo_XR_Lab/LAM-assets" --local_dir "./tmp/"
  tar -xf ./tmp/LAM_assets.tar
  tar -xf ./tmp/thirdparty_models.tar
  rm -rf ./tmp
  modelscope download "Damo_XR_Lab/LAM-20K" --local_dir "./model_zoo/lam_models/releases/lam/lam-20k/step_045500/"
fi

echo "== LAM assets check =="
test -e assets/sample_input/status.png
test -d assets/sample_motion
test -d model_zoo/lam_models/releases/lam/lam-20k/step_045500
find assets/sample_input model_zoo/lam_models/releases/lam/lam-20k/step_045500 -maxdepth 2 -type f | sed -n '1,40p'

