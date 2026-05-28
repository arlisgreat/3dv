# G103 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the matched naive arm from the G100 strict-aware pool after G101 training and G102 rendering.
```

Verdict:

```text
PASS_G81_NAIVE_STRICT_POOL_ITER1500_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.674427 | -0.047800 | 0.498218 | 0.284254 | 0.328742 |
| 222200041 | 4.670610 | 0.023011 | 0.502351 | 0.266807 | 0.320646 |
| 222200047 | 5.369710 | 0.070591 | 0.443342 | 0.378074 | 0.322816 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.904916 |
| mean_masked_rgb_ssim_global_luma | 0.015267 |
| mean_masked_rgb_mae | 0.481304 |
| mean_prediction_mask_vs_eval_mask_iou | 0.309712 |
| mean_prediction_foreground_coverage | 0.324068 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_naive_pseudo_view_supervision_strict_pool_iter1500_point_splat8
```

Interpretation:

```text
Matched naive baseline for the strict-aware ablation.
```

Decision:

```text
Matched naive strict-pool predictions produced finite held-out metrics.
```

Next gate:

```text
Evaluate strict-aware and rerun contract.
```
