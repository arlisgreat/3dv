# G93 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the identity/confidence-aware pseudo-view RI3D arm with G91 splat8 NeRSemble held-out renders.
```

Verdict:

```text
PASS_G81_IDENTITY_CONFIDENCE_AWARE_RI3D_SPLAT8_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.521878 | -0.039899 | 0.514244 | 0.262771 | 0.298008 |
| 222200041 | 4.657085 | 0.065516 | 0.493760 | 0.257513 | 0.284462 |
| 222200047 | 5.207749 | 0.055898 | 0.463674 | 0.356700 | 0.304898 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.795571 |
| mean_masked_rgb_ssim_global_luma | 0.027172 |
| mean_masked_rgb_mae | 0.490559 |
| mean_prediction_mask_vs_eval_mask_iou | 0.292328 |
| mean_prediction_foreground_coverage | 0.295789 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_identity_confidence_aware_pseudo_view_supervision_ri3d_iter80_point_splat8
```

Interpretation:

```text
Renderer-only splat radius ablation for the G81 candidate arm.
```

Decision:

```text
Aware splat8 RI3D predictions produced finite held-out metrics.
```

Next gate:

```text
Rerun G84 three-arm contract if splat8 improves over G89/G90.
```
