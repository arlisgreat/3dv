# G98 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the identity/confidence-aware pseudo-view RI3D arm after G95 1500-step training and G96 splat8 NeRSemble held-out rendering.
```

Verdict:

```text
PASS_G81_IDENTITY_CONFIDENCE_AWARE_RI3D_ITER1500_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.823553 | -0.063281 | 0.483526 | 0.326799 | 0.343324 |
| 222200041 | 4.442090 | 0.032688 | 0.530800 | 0.206494 | 0.329887 |
| 222200047 | 4.947352 | -0.016853 | 0.480368 | 0.330213 | 0.296972 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.737665 |
| mean_masked_rgb_ssim_global_luma | -0.015815 |
| mean_masked_rgb_mae | 0.498231 |
| mean_prediction_mask_vs_eval_mask_iou | 0.287835 |
| mean_prediction_foreground_coverage | 0.323394 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_identity_confidence_aware_pseudo_view_supervision_ri3d_iter1500_point_splat8
```

Interpretation:

```text
Densified G81 candidate arm. The claim is valid only if G99 shows it beats direct and naive.
```

Decision:

```text
Aware iter1500 predictions produced finite held-out metrics.
```

Next gate:

```text
Rerun G99 three-arm contract.
```
