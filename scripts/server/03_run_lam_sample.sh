#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAM_DIR="$ROOT/external/LAM"

IMAGE_INPUT="${1:-assets/sample_input/status.png}"
CONFIG="${2:-configs/inference/lam-20k-8gpu.yaml}"
MODEL_NAME="${3:-model_zoo/lam_models/releases/lam/lam-20k/step_045500/}"
MOTION_SEQS_DIR="${4:-assets/sample_motion/export/Look_In_My_Eyes/}"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate lam

export CACHE_ROOT="${CACHE_ROOT:-$ROOT/.cache}"
export HF_HOME="$CACHE_ROOT/huggingface"
export TORCH_HOME="$CACHE_ROOT/torch"

cd "$LAM_DIR"

if [[ ! -e "$IMAGE_INPUT" && -e "$ROOT/$IMAGE_INPUT" ]]; then
  IMAGE_INPUT="$ROOT/$IMAGE_INPUT"
fi

if [[ ! -e "$IMAGE_INPUT" ]]; then
  echo "Missing image input: $IMAGE_INPUT"
  exit 1
fi

if [[ ! -d "$MODEL_NAME" ]]; then
  echo "Missing LAM model directory: $MODEL_NAME"
  echo "Run: bash scripts/server/02_download_lam_assets.sh hf"
  exit 1
fi

if [[ ! -d "$MOTION_SEQS_DIR" ]]; then
  echo "Missing motion sequence directory: $MOTION_SEQS_DIR"
  echo "Run: bash scripts/server/02_download_lam_assets.sh hf"
  exit 1
fi

export PYTHONPATH="$LAM_DIR:${PYTHONPATH:-}"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" python -m lam.launch infer.lam --config "$CONFIG" \
  model_name="$MODEL_NAME" \
  image_input="$IMAGE_INPUT" \
  export_video=true \
  export_mesh=false \
  motion_seqs_dir="$MOTION_SEQS_DIR" \
  motion_img_dir=null \
  vis_motion=false \
  motion_img_need_mask=true \
  render_fps=30 \
  motion_video_read_fps=30 \
  save_ply=false \
  save_img=false \
  gaga_track_type="" \
  cross_id=false \
  test_sample=false \
  rank=0 \
  nodes=0

echo "LAM output is usually under:"
echo "  $LAM_DIR/exps/"
echo "  $LAM_DIR/dumps/"

