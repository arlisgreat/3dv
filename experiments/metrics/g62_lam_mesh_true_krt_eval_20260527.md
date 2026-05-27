# G62 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G61 LAM textured-mesh true-KRT renders on the G54 visible held-out cameras. The run is diagnostic-only because GT pointcloud bbox alignment was used.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_MESH_TRUE_KRT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 7.237724 | -0.045876 | 0.322602 | 0.726350 | 0.521005 |
| 222200041 | 6.560705 | -0.133027 | 0.347348 | 0.684402 | 0.506629 |
| 222200047 | 6.884558 | -0.102381 | 0.333345 | 0.716098 | 0.464947 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 6.894329 |
| mean_masked_rgb_ssim_global_luma | -0.093761 |
| mean_masked_rgb_mae | 0.334432 |
| mean_prediction_mask_vs_eval_mask_iou | 0.708950 |
| mean_prediction_foreground_coverage | 0.497527 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_mesh_true_KRT_GT_bbox_aligned_diagnostic
```

Interpretation:

```text
These metrics are not a method-quality result. They test whether LAM mesh output can be routed through the true NeRSemble camera renderer after weak GT-geometry alignment; visual audit shows broken texture/appearance.
```

Decision:

```text
Finite metrics are recorded, but the visual result is broken and GT-aligned; this does not validate the single-image learned-prior method idea.
```

Next gate:

```text
Replace GT-bbox alignment with source-camera/model-derived alignment, or switch to a method with native NeRSemble-camera output before making a main experiment claim.
```
