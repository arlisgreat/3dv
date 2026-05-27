# G66 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G65 triangle-rasterized source-mask-aligned LAM textured-mesh true-KRT renders on the G54 NeRSemble visible held-out cameras. This checks whether the previous point-splat artifact was the primary failure mode.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_MESH_TRUE_KRT_SOURCE_MASK_ALIGNED_TRIANGLE_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 5.973205 | -0.073613 | 0.414579 | 0.489269 | 0.495287 |
| 222200041 | 5.667932 | 0.061333 | 0.432505 | 0.414764 | 0.411378 |
| 222200047 | 5.939480 | 0.206004 | 0.428239 | 0.349271 | 0.425935 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 5.860206 |
| mean_masked_rgb_ssim_global_luma | 0.064575 |
| mean_masked_rgb_mae | 0.425108 |
| mean_prediction_mask_vs_eval_mask_iou | 0.417768 |
| mean_prediction_foreground_coverage | 0.444200 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_mesh_true_KRT_source_mask_aligned_triangle_diagnostic
```

Interpretation:

```text
G65 keeps the same source-only alignment and true NeRSemble K/R/T camera contract as G63, but replaces point splatting with triangle rasterization. Metrics remain diagnostic unless the visual gate confirms plausible appearance.
```

Decision:

```text
Held-out metrics are finite; visual gate decides whether the renderer fix validates the learned-prior/feed-forward method path.
```

Next gate:

```text
Run a visual/mask/appearance gate for G65. If texture remains swirled or identity/appearance is broken, stop the current LAM textured-mesh route and switch to a native NeRSemble-camera-aligned feed-forward avatar method.
```
