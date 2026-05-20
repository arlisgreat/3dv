# G45 LAM Held-Out Camera Geometry Diagnostic

Date: 2026-05-20

Verdict:

```text
PASS_HELDOUT_CAMERA_RENDER_CONTRACT_DIAGNOSTIC_ONLY_NO_RECONSTRUCTION_QUALITY_CLAIM
```

Premise:

```text
Use the G44 similarity-aligned LAM shaped mesh and the G23 real-camera adapter to render geometry into held-out Multiface cameras, then compare silhouette and z-buffer depth against held-out GT masks/depth arrays without committing private images or meshes.
```

Data gate:

```text
PASS_REAL_GT_HELDOUT_DIAGNOSTIC. Inputs are G21/G23 Multiface real captured cameras/masks/depth, G42 private LAM shaped mesh, and G44 similarity transform. No pseudo-view candidate pool, experiments/downstream_datasets export, LAM motion-camera MP4, or held-out RGB image is used for training or committed output.
```

Held-out camera diagnostics:

| camera | mask_iou | pred_cov | gt_cov | depth_abs_mean_mm | depth_abs_mean_over_gt_median | projected_faces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 400012 | 0.718430 | 0.189987 | 0.230316 | 24.334179 | 0.023465 | 2667 |
| 400041 | 0.672901 | 0.197220 | 0.224579 | 49.089864 | 0.047229 | 2968 |
| 400042 | 0.732918 | 0.199677 | 0.224533 | 19.014323 | 0.018243 | 2808 |

Summary:

| metric | value | threshold |
| --- | ---: | ---: |
| mean_mask_iou | 0.708083 | 0.450000 |
| min_mask_iou | 0.672901 | 0.350000 |
| mean_depth_abs_over_gt_median | 0.029646 | 0.120000 |

Blocked interpretations:

```text
Do not report G45 as photometric reconstruction quality.
Do not compare G45 to RGB PSNR/SSIM/LPIPS or SOTA tables.
Do not treat similarity/ICP alignment as camera recovery or metric coordinate recovery.
Do not use held-out RGB pixels for training; this gate consumes only masks/depth arrays derived from the GT mesh.
Do not publish private Multiface/LAM PNG/MP4/PLY/OBJ outputs without explicit artifact review.
Do not reintroduce experiments/downstream_datasets as training or evaluation data.
```

Decision:

```text
G45 is the first held-out-camera geometry diagnostic for the learned-prior route. It checks whether the aligned LAM mesh projects into held-out Multiface cameras with non-catastrophic silhouette/depth agreement. It remains below a final method result because it uses similarity-aligned mesh geometry, not the native learned-prior camera frame or RGB held-out rendering.
```
