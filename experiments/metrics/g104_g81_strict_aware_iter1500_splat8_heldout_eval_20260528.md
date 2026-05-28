# G104 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the strict identity/confidence-aware arm after rejecting geometry-only pseudo views, G101 training, and G102 rendering.
```

Verdict:

```text
PASS_G81_STRICT_AWARE_ITER1500_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 5.117449 | -0.044936 | 0.463160 | 0.405764 | 0.307055 |
| 222200041 | 3.991451 | -0.086391 | 0.557599 | 0.188800 | 0.212984 |
| 222200047 | 5.227268 | 0.162929 | 0.467448 | 0.325003 | 0.238412 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.778723 |
| mean_masked_rgb_ssim_global_luma | 0.010534 |
| mean_masked_rgb_mae | 0.496069 |
| mean_prediction_mask_vs_eval_mask_iou | 0.306522 |
| mean_prediction_foreground_coverage | 0.252817 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_strict_identity_confidence_aware_pseudo_view_supervision_iter1500_point_splat8
```

Interpretation:

```text
Strict-aware G81 ablation: source anchor plus identity/weak-identity pseudo views only.
```

Decision:

```text
Strict-aware predictions produced finite held-out metrics.
```

Next gate:

```text
Rerun G105 three-arm contract.
```
