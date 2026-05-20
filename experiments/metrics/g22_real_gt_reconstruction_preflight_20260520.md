# G22 Real-GT Reconstruction/Evaluation Preflight

Date: 2026-05-20

Verdict:

```text
BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER
NO_GPU_TRAINING_STARTED
```

Premise:

```text
G21 passed a local real-capture benchmark case. G22 may only start
training if the current reconstruction/evaluation adapter preserves the
real camera model, geometry/depth priors, artifact policy, and metrics.
```

Checks:

| Check | Result | Detail |
| --- | --- | --- |
| g21_real_gt_gate_passed | PASS | PASS_REAL_GT_BENCHMARK |
| raw_assets_remain_local_only | PASS | Raw RGB/OBJ/contact sheet stay under 3dv_work; repo contains metrics/hash/mask-only PNG. |
| manifest_cameras_masks_mesh_present | PASS | 9 rows, 9 cameras, mesh_present=True |
| ri3d_current_adapter_preserves_per_view_intrinsics | BLOCK | 256px effective principal point ranges: cx=42.43px, cy=26.91px; current RI3D exports use one global intrinsics block. |
| real_camera_depth_priors_available | BLOCK | No real-camera z-buffer depth/conf maps exist in the G21 manifest. |
| evaluation_metrics_adapter_available | BLOCK | No committed adapter yet for held-out view metrics or mesh/point-cloud distance on Multiface. |
| crop_risk_acceptable_for_training_start | BLOCK | High mask coverage/crop-risk views: 400012, 400017, 400041, 400042 |

Effective intrinsics after 256px letterbox resize:

| Component | min | max | range | mean |
| --- | ---: | ---: | ---: | ---: |
| fx | 633.662 | 970.338 | 336.676 | 929.283 |
| fy | 633.587 | 969.507 | 335.920 | 929.169 |
| cx | 107.143 | 149.578 | 42.435 | 131.102 |
| cy | 100.573 | 127.486 | 26.913 | 117.199 |

Closure:

```text
BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER: G21 benchmark premise passes, but current RI3D/evaluation plumbing does not yet preserve Multiface real-camera intrinsics/depth/metric assumptions. Do not start GPU training.
```

Required unblock items:

```text
1. Add a local-only real-GT adapter that preserves per-frame intrinsics/extrinsics or applies a documented recenter/undistort transform.
2. Generate real-camera mesh z-buffer depth/confidence maps from the tracked OBJ; do not use pseudo/synthetic depth priors.
3. Define train/test split and metrics: silhouette IoU, novel-view RGB/LPIPS where held-out views exist, and mesh/point-cloud distance if aligned geometry is exported.
4. Re-run G21/G22 VLM and distribution gates after conversion.
5. Only then select an idle GPU and start the smallest real-GT training run.
```
