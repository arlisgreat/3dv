# G23 Multiface Real-Camera Adapter

Date: 2026-05-20

Verdict:

```text
PASS_REAL_CAMERA_ADAPTER_PREFLIGHT
NO_GPU_TRAINING_STARTED
```

Purpose:

```text
Convert the G21 Multiface debug real-GT case into a local-only adapter that
RI3D can read without silently dropping per-view real-camera assumptions.
Raw RGB and OBJ stay under 3dv_work; repo output is metrics plus a
mask/depth-only PNG.
```

Adapter output:

```text
/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102
/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_manifest.json
experiments/figures/g23_multiface_adapter_depth_mask_summary_20260520.png
```

Checks:

| Check | Result |
| --- | --- |
| train_view_count_6_plus | PASS |
| heldout_views_defined | PASS |
| centered_principal_point | PASS |
| focal_residual_small | PASS |
| depth_conf_generated | PASS |
| train_crop_risk_reduced | PASS |
| local_only_artifact_policy | PASS |

Camera split:

```text
train: 400017, 400023, 400050, 400055, 400067, 400070
heldout: 400012, 400041, 400042
target_focal: 640.0
```

Train mask coverage:

| camera | coverage | projected faces | depth median |
| --- | ---: | ---: | ---: |
| 400017 | 0.2231 | 5944 | 1019.647 |
| 400023 | 0.2721 | 6431 | 1044.087 |
| 400050 | 0.2081 | 3571 | 1042.474 |
| 400055 | 0.1861 | 5068 | 1053.263 |
| 400067 | 0.2026 | 6677 | 1050.632 |
| 400070 | 0.1714 | 5600 | 1052.644 |

Closure:

```text
PASS_REAL_CAMERA_ADAPTER_PREFLIGHT: local-only normalized camera/depth/conf adapter is ready for a final dry-run gate before GPU.
```

Next gate:

```text
G24 should run a CPU-only dry-run over the generated adapter, checking RI3D
file contracts and held-out metric definitions. Select an idle GPU only if
G24 passes.
```
