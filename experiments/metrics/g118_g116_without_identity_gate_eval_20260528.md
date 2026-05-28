# G118 NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate the G116 w/o identity gate source-gated pseudo-prior ablation with the original G55 held-out evaluator.
```

Verdict:

```text
PASS_G116_WITHOUT_IDENTITY_GATE_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 12.523134 | 0.375970 | 0.144710 | 0.886793 | 0.670782 |
| 222200041 | 12.534951 | 0.438638 | 0.147773 | 0.927649 | 0.614360 |
| 222200047 | 13.710959 | 0.543463 | 0.120335 | 0.930835 | 0.592939 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 12.923015 |
| mean_masked_rgb_ssim_global_luma | 0.452690 |
| mean_masked_rgb_mae | 0.137606 |
| mean_prediction_mask_vs_eval_mask_iou | 0.915092 |
| mean_prediction_foreground_coverage | 0.626027 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g116_without_identity_gate
```

Interpretation:

```text
This ablation keeps direct Gaussian geometry and source-only alpha but removes identity-anchor selection/weighting from pseudo color moments.
```

Decision:

```text
w/o identity gate variant produced finite held-out metrics for six-arm ablation summary.
```

Next gate:

```text
Compare against full-aware and w/o confidence variants.
```
