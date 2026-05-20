# G25 RI3D Multiface Init-Only Smoke

Date: 2026-05-20

Verdict:

```text
PASS_RI3D_INIT_ONLY_SMOKE
NO_FULL_TRAINING_STARTED
```

Scope:

```text
Load the G24 local-only Multiface adapter in RI3D, build the sparse-view point
cloud, and save iteration 1. This is a loader/initialization gate only.
```

Environment:

| Item | Value |
| --- | --- |
| GPU | 0, NVIDIA A800-SXM4-80GB |
| GPU state at launch | 0 MiB / 81920 MiB, 0% utilization |
| Conda env | lam |
| Python | 3.10.20 |
| Torch | 2.6.0+cu124 |
| CUDA env | `/data1/workspace/airulan/env124.sh` |
| RI3D commit | `506496a`, dirty local worktree |

Command:

```bash
PYTHONPATH=/data1/workspace/airulan/3dv/external/ri3d \
python scripts/train_gs_init.py \
  -s /data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102 \
  -m /data1/workspace/airulan/3dv_work/runs/g25_ri3d_multiface_init_smoke_20260520 \
  -r 1 --sparse_view_num 6 --sh_degree 2 --white_background --random_background \
  --iterations 1 --use_mask --pointcloud_mask_filter --pointcloud_conf_threshold 0.0 \
  --pointcloud_min_points 256 --pointcloud_points_per_view 0
```

Result:

| Check | Result |
| --- | --- |
| exit code | 0 |
| RI3D scene loads | PASS |
| training cameras | 6 |
| held-out cameras | 3 |
| point cloud saved | PASS |
| point count | 67410 |
| full training | NOT STARTED |

Artifact policy:

```text
All G25 run outputs stay under 3dv_work. The point cloud, cameras.json, logs,
adapter RGB, and any identifiable render artifacts must not be committed without
explicit artifact review.
```

Interpretation:

```text
G25 proves only that RI3D can load the G24 adapter and initialize/save a point
cloud. It does not prove reconstruction quality, held-out rendering, or
pseudo-view validity.
```

Next gate:

```text
G26 should attempt held-out render/evaluation from this local-only point cloud.
It must avoid committing identifiable PNGs and should publish only compact
numeric metrics or a failure tail.
```
