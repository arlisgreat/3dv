# G117_NO_SOURCE_ALPHA NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate G117 pseudo-prior ablation without source-selected alpha threshold with original G55 evaluator.
```

Verdict:

```text
PASS_G117_WITHOUT_SOURCE_ALPHA_GATE_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 12.817589 | 0.383811 | 0.146048 | 0.886841 | 0.722461 |
| 222200041 | 12.670524 | 0.445209 | 0.157875 | 0.899270 | 0.652360 |
| 222200047 | 13.717543 | 0.547164 | 0.131005 | 0.912862 | 0.635452 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 13.068552 |
| mean_masked_rgb_ssim_global_luma | 0.458728 |
| mean_masked_rgb_mae | 0.144976 |
| mean_prediction_mask_vs_eval_mask_iou | 0.899658 |
| mean_prediction_foreground_coverage | 0.670091 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g117_without_source_alpha_gate
```

Interpretation:

```text
This variant keeps direct geometry/color-prior mechanism but uses a fixed alpha threshold instead of source-mask-selected alpha.
```

Decision:

```text
Without-source-alpha ablation produced finite held-out metrics.
```

Next gate:

```text
Aggregate G117 ablations.
```
