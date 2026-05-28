# G117_FULL NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate G117 full identity/confidence pseudo-prior ablation with original G55 evaluator.
```

Verdict:

```text
PASS_G117_FULL_IDENTITY_CONFIDENCE_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 12.817589 | 0.383811 | 0.146048 | 0.886793 | 0.670782 |
| 222200041 | 12.670524 | 0.445209 | 0.157875 | 0.927649 | 0.614360 |
| 222200047 | 13.717543 | 0.547164 | 0.131005 | 0.930835 | 0.592939 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 13.068552 |
| mean_masked_rgb_ssim_global_luma | 0.458728 |
| mean_masked_rgb_mae | 0.144976 |
| mean_prediction_mask_vs_eval_mask_iou | 0.915092 |
| mean_prediction_foreground_coverage | 0.626027 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g117_full_identity_confidence
```

Interpretation:

```text
Full G117 should reproduce G110 policy under the ablation runner.
```

Decision:

```text
Full identity/confidence ablation produced finite held-out metrics.
```

Next gate:

```text
Aggregate G117 ablations.
```
