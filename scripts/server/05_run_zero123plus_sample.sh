#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

INPUT="${1:-$ROOT/external/LAM/assets/sample_input/status.png}"
OUTDIR="${2:-$ROOT/experiments/pseudo_views/zero123plus_sample}"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate zero123plus

export CACHE_ROOT="${CACHE_ROOT:-$ROOT/.cache}"
export HF_HOME="$CACHE_ROOT/huggingface"
export TORCH_HOME="$CACHE_ROOT/torch"

python "$ROOT/scripts/zero123plus_generate.py" \
  --input "$INPUT" \
  --outdir "$OUTDIR" \
  --steps 75 \
  --model sudo-ai/zero123plus-v1.2

