#!/usr/bin/env bash
set -euo pipefail

# Render RGB/depth flythrough videos for the RI3D first2 downstream pilot.
#
# Usage:
#   DATA_ROOT=experiments/ri3d_datasets/first2_160 \
#   RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 \
#   ITERATION=50 GPU=0 bash scripts/render_ri3d_first2.sh
#
# Optional environment overrides:
#   VARIANTS_STR="roleaware_cutout75_budget4"
#   SAMPLES_STR="web_clean_frontal_03 web_clean_frontal_01"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RI3D_ROOT="${RI3D_ROOT:-$PROJECT_ROOT/external/ri3d}"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/experiments/ri3d_datasets/first2}"
RUN_ROOT="${RUN_ROOT:-$PROJECT_ROOT/experiments/downstream_3d/ri3d_first2}"
ITERATION="${ITERATION:-1500}"
GPU="${GPU:-0}"
SH_DEGREE="${SH_DEGREE:-2}"
POSTFIX="${POSTFIX:-}"
VARIANTS_INPUT="${VARIANTS_STR:-${VARIANTS:-raw75_all6 raw75_budget4 cutout75_budget4_masked}}"
SAMPLES_INPUT="${SAMPLES_STR:-${SAMPLES:-web_clean_frontal_03 web_clean_frontal_01}}"

case "$DATA_ROOT" in
  /*) ;;
  *) DATA_ROOT="$PROJECT_ROOT/$DATA_ROOT" ;;
esac

case "$RUN_ROOT" in
  /*) ;;
  *) RUN_ROOT="$PROJECT_ROOT/$RUN_ROOT" ;;
esac

read -r -a VARIANTS <<< "$VARIANTS_INPUT"
read -r -a SAMPLES <<< "$SAMPLES_INPUT"

if [[ ! -d "$RI3D_ROOT" ]]; then
  echo "Missing RI3D checkout: $RI3D_ROOT" >&2
  exit 1
fi

if [[ ! -f "$DATA_ROOT/manifest.json" ]]; then
  echo "Missing prepared RI3D data: $DATA_ROOT/manifest.json" >&2
  exit 1
fi

if [[ ! -d "$RUN_ROOT/output/gs_init" ]]; then
  echo "Missing RI3D training output: $RUN_ROOT/output/gs_init" >&2
  exit 1
fi

cd "$RI3D_ROOT"
export CUDA_VISIBLE_DEVICES="$GPU"
export PYTHONPATH="$RI3D_ROOT:${PYTHONPATH:-}"

for variant in "${VARIANTS[@]}"; do
  for sample in "${SAMPLES[@]}"; do
    scene="$DATA_ROOT/$variant/$sample"
    if [[ ! -d "$scene" ]]; then
      echo "Skip missing scene: $scene" >&2
      continue
    fi

    view_count="$(python -c "import json; print(len(json.load(open('$scene/transforms.json'))['frames']))")"
    tag="${sample}_${variant}_${view_count}v"
    model_out="$RUN_ROOT/output/gs_init/$tag"
    ply_path="$model_out/point_cloud/iteration_$ITERATION/point_cloud.ply"
    log_dir="$RUN_ROOT/logs"
    mkdir -p "$log_dir"

    if [[ ! -f "$ply_path" ]]; then
      echo "Missing trained point cloud: $ply_path" >&2
      exit 1
    fi

    echo "=== RI3D render: $tag ==="
    python scripts/render.py \
      -s "$scene" \
      -m "$model_out" \
      -r 1 \
      --sparse_view_num "$view_count" \
      --sh_degree "$SH_DEGREE" \
      --white_background \
      --iteration "$ITERATION" \
      --render_path \
      --postfix "$POSTFIX" \
      2>&1 | tee "$log_dir/${tag}_render.log"

    echo "Rendered: $tag"
  done
done

echo "All RI3D first2 renders finished. Results: $RUN_ROOT"
