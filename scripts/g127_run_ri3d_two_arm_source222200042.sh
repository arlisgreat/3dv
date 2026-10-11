#!/usr/bin/env bash
# G127: RI3D two-arm iter1500 replication for NeRSemble source 222200042.
#
# Mirrors the g95 invocation recorded in
# 3dv_work/runs/g95_g81_ri3d_two_arm_iter1500/logs/*_train.log (Namespace dump):
# sh_degree=2, white_background, random_background, iterations=1500,
# use_mask=True, pointcloud_mask_filter=True, pointcloud_conf_threshold=0.0,
# pointcloud_min_points=512, pointcloud_points_per_view=0, mono_depth_weight=0.005
# (train_gs.py defaults), scaling_lr=0 (hardcoded in train_gs.py).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RI3D_ROOT="${RI3D_ROOT:-$REPO/external/ri3d}"
SCENE_ROOT="${SCENE_ROOT:-/data1/workspace/airulan/3dv_work/runs/g126_source222200042_ri3d_pool/ri3d_scenes}"
OUT_ROOT="${OUT_ROOT:-/data1/workspace/airulan/3dv_work/runs/g127_source222200042_ri3d_two_arm_iter1500}"
SAMPLE="${SAMPLE:-source222200042}"
ITERATIONS="${ITERATIONS:-1500}"
GPU="${GPU:-0}"

mkdir -p "$OUT_ROOT/logs"
cd "$RI3D_ROOT"
export CUDA_VISIBLE_DEVICES="$GPU"
export PYTHONPATH="$RI3D_ROOT:${PYTHONPATH:-}"

run_arm() {
  local variant="$1"
  local views="$2"
  local scene="$SCENE_ROOT/$variant/$SAMPLE"
  local tag="${SAMPLE}_${variant}_${views}v"
  local init_out="$OUT_ROOT/debug/gs_init/$tag"
  local train_out="$OUT_ROOT/output/gs_init/$tag"

  echo "=== RI3D init: $tag ==="
  python scripts/train_gs_init.py \
    -s "$scene" -m "$init_out" -r 1 \
    --sparse_view_num "$views" --sh_degree 2 \
    --white_background --random_background --iterations 1 \
    --use_mask --pointcloud_mask_filter \
    --pointcloud_conf_threshold 0.0 --pointcloud_min_points 512 \
    2>&1 | tee "$OUT_ROOT/logs/${tag}_init.log"

  local ply_path="$init_out/point_cloud/iteration_1/point_cloud.ply"
  if [[ ! -f "$ply_path" ]]; then
    echo "Missing init point cloud: $ply_path" >&2
    exit 1
  fi

  echo "=== RI3D train: $tag ==="
  python -W ignore scripts/train_gs.py \
    -s "$scene" -m "$train_out" -r 1 \
    --sparse_view_num "$views" --sh_degree 2 \
    --white_background --random_background \
    --iterations "$ITERATIONS" --save_iterations "$ITERATIONS" \
    --ply_path "$ply_path" \
    --use_mask --pointcloud_mask_filter \
    --pointcloud_conf_threshold 0.0 --pointcloud_min_points 512 \
    2>&1 | tee "$OUT_ROOT/logs/${tag}_train.log"

  echo "Finished: $tag"
}

run_arm g81_naive_pseudo_source_anchor 7
run_arm g81_identity_confidence_aware_source_anchor 3

echo "All G127 RI3D jobs finished. Results: $OUT_ROOT"
