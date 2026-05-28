# G117_NO_CONFIDENCE NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate G117 pseudo-prior ablation without confidence weighting with original G55 evaluator.
```

Verdict:

```text
PASS_G117_WITHOUT_CONFIDENCE_GATE_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 12.830697 | 0.383424 | 0.146717 | 0.886793 | 0.670782 |
| 222200041 | 12.672484 | 0.445197 | 0.159003 | 0.927649 | 0.614360 |
| 222200047 | 13.703804 | 0.546517 | 0.132377 | 0.930835 | 0.592939 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 13.068995 |
| mean_masked_rgb_ssim_global_luma | 0.458379 |
| mean_masked_rgb_mae | 0.146032 |
| mean_prediction_mask_vs_eval_mask_iou | 0.915092 |
| mean_prediction_foreground_coverage | 0.626027 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g117_without_confidence_gate
```

Interpretation:

```text
This variant keeps source-gated direct geometry but removes confidence weighting from pseudo color moments.
```

Decision:

```text
Without-confidence ablation produced finite held-out metrics.
```

Next gate:

```text
Aggregate G117 ablations.
```
