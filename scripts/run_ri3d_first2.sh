#!/usr/bin/env bash
set -euo pipefail

# Run the first downstream 3D pilot on a GPU server.
#
# Usage:
#   bash scripts/run_ri3d_first2.sh
#
# Optional environment overrides:
#   RI3D_ROOT=/path/to/ri3d
#   DATA_ROOT=/path/to/3dv/experiments/ri3d_datasets/first2
#   OUT_ROOT=/path/to/3dv/experiments/downstream_3d/ri3d_first2
#   ITERATIONS=1500
#   GPU=0
#   VARIANTS_STR="raw75_budget4 roleaware_cutout75_budget4"
#   SAMPLES_STR="web_clean_frontal_03 web_clean_frontal_01"
#   USE_MASK=1
#   PCD_MASK_FILTER=1

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RI3D_ROOT="${RI3D_ROOT:-$PROJECT_ROOT/external/ri3d}"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/experiments/ri3d_datasets/first2}"
OUT_ROOT="${OUT_ROOT:-$PROJECT_ROOT/experiments/downstream_3d/ri3d_first2}"
ITERATIONS="${ITERATIONS:-1500}"
GPU="${GPU:-0}"
SH_DEGREE="${SH_DEGREE:-2}"
USE_MASK="${USE_MASK:-0}"
PCD_MASK_FILTER="${PCD_MASK_FILTER:-0}"
PCD_CONF_THRESHOLD="${PCD_CONF_THRESHOLD:-0.0}"
PCD_MIN_POINTS="${PCD_MIN_POINTS:-256}"
PCD_POINTS_PER_VIEW="${PCD_POINTS_PER_VIEW:-0}"
VARIANTS_INPUT="${VARIANTS_STR:-${VARIANTS:-raw75_all6 raw75_budget4 cutout75_budget4_masked}}"
SAMPLES_INPUT="${SAMPLES_STR:-${SAMPLES:-web_clean_frontal_03 web_clean_frontal_01}}"

case "$DATA_ROOT" in
  /*) ;;
  *) DATA_ROOT="$PROJECT_ROOT/$DATA_ROOT" ;;
esac

case "$OUT_ROOT" in
  /*) ;;
  *) OUT_ROOT="$PROJECT_ROOT/$OUT_ROOT" ;;
esac

read -r -a VARIANTS <<< "$VARIANTS_INPUT"
read -r -a SAMPLES <<< "$SAMPLES_INPUT"

MASK_ARGS=()
case "${USE_MASK,,}" in
  1|true|yes|on) MASK_ARGS=(--use_mask) ;;
  0|false|no|off|"") ;;
  *)
    echo "Unsupported USE_MASK value: $USE_MASK" >&2
    exit 1
    ;;
esac

PCD_FILTER_ARGS=()
case "${PCD_MASK_FILTER,,}" in
  1|true|yes|on)
    PCD_FILTER_ARGS=(
      --pointcloud_mask_filter
      --pointcloud_conf_threshold "$PCD_CONF_THRESHOLD"
      --pointcloud_min_points "$PCD_MIN_POINTS"
      --pointcloud_points_per_view "$PCD_POINTS_PER_VIEW"
    )
    ;;
  0|false|no|off|"") ;;
  *)
    echo "Unsupported PCD_MASK_FILTER value: $PCD_MASK_FILTER" >&2
    exit 1
    ;;
esac

if [[ ! -d "$RI3D_ROOT" ]]; then
  echo "Missing RI3D checkout: $RI3D_ROOT" >&2
  exit 1
fi

if [[ ! -f "$DATA_ROOT/manifest.json" ]]; then
  echo "Missing prepared RI3D data: $DATA_ROOT/manifest.json" >&2
  echo "Run: python3 scripts/prepare_ri3d_dataset.py --overwrite" >&2
  exit 1
fi

mkdir -p "$OUT_ROOT"
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
    init_out="$OUT_ROOT/debug/gs_init/$tag"
    train_out="$OUT_ROOT/output/gs_init/$tag"
    log_dir="$OUT_ROOT/logs"
    mkdir -p "$log_dir"

    echo "=== RI3D init: $tag ==="
    python scripts/train_gs_init.py \
      -s "$scene" \
      -m "$init_out" \
      -r 1 \
      --sparse_view_num "$view_count" \
      --sh_degree "$SH_DEGREE" \
      --white_background \
      --random_background \
      --iterations 1 \
      "${MASK_ARGS[@]}" \
      "${PCD_FILTER_ARGS[@]}" \
      2>&1 | tee "$log_dir/${tag}_init.log"

    ply_path="$init_out/point_cloud/iteration_1/point_cloud.ply"
    if [[ ! -f "$ply_path" ]]; then
      echo "Missing init point cloud: $ply_path" >&2
      exit 1
    fi

    echo "=== RI3D train: $tag ==="
    python -W ignore scripts/train_gs.py \
      -s "$scene" \
      -m "$train_out" \
      -r 1 \
      --sparse_view_num "$view_count" \
      --sh_degree "$SH_DEGREE" \
      --white_background \
      --random_background \
      --iterations "$ITERATIONS" \
      --save_iterations "$ITERATIONS" \
      --ply_path "$ply_path" \
      "${MASK_ARGS[@]}" \
      "${PCD_FILTER_ARGS[@]}" \
      2>&1 | tee "$log_dir/${tag}_train.log"

    echo "Finished: $tag"
  done
done

echo "All RI3D first2 jobs finished. Results: $OUT_ROOT"
