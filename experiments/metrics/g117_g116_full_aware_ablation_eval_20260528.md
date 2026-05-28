# G117 NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate the G116 full identity/confidence-aware source-gated pseudo-prior variant with the original G55 held-out evaluator.
```

Verdict:

```text
PASS_G116_FULL_AWARE_ABLATION_EVAL
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
g116_identity_confidence_aware_pseudo_prior
```

Interpretation:

```text
Full G116 variant repeats the G110 policy under the ablation runner: direct Gaussian geometry, source-only alpha, identity/confidence/rgb pseudo color prior.
```

Decision:

```text
Full G116 variant produced finite held-out metrics for six-arm ablation summary.
```

Next gate:

```text
Compare against direct, naive, w/o identity, w/o confidence, and no-direct-geometry pseudo arm.
```
