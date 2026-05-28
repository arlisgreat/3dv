# G90 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the identity/confidence-aware pseudo-view RI3D arm on the audited NeRSemble source220700191 held-out cameras using G88 point-splat predictions.
```

Verdict:

```text
PASS_G81_IDENTITY_CONFIDENCE_AWARE_RI3D_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.378417 | -0.066673 | 0.524952 | 0.250146 | 0.269503 |
| 222200041 | 4.572880 | 0.062085 | 0.500851 | 0.241737 | 0.263199 |
| 222200047 | 5.125081 | 0.061351 | 0.471370 | 0.339183 | 0.286487 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.692126 |
| mean_masked_rgb_ssim_global_luma | 0.018921 |
| mean_masked_rgb_mae | 0.499058 |
| mean_prediction_mask_vs_eval_mask_iou | 0.277022 |
| mean_prediction_foreground_coverage | 0.273063 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_identity_confidence_aware_pseudo_view_supervision_ri3d_iter80_point_splat
```

Interpretation:

```text
This is the G81 candidate arm. The claim is valid only if G84 shows it beats both direct single-image Gaussian and naive pseudo-view supervision.
```

Decision:

```text
Identity/confidence-aware pseudo-view RI3D predictions produced finite held-out metrics.
```

Next gate:

```text
Rerun G84 three-arm contract with direct, naive, and aware evaluator JSONs.
```
