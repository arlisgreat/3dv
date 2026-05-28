# G111 NeRSemble Held-Out Eval

Date: 2026-05-28

Premise:

```text
Evaluate G110 source-gated identity/confidence pseudo-prior predictions with the original G55 NeRSemble held-out evaluator.
```

Verdict:

```text
PASS_G110_NERSEMBLE_HELDOUT_EVAL_G55
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
g110_source_gated_identity_confidence_pseudo_prior_refinement
```

Interpretation:

```text
G110 uses direct Gaussian geometry, source-only alpha threshold selection, and strict identity/confidence pseudo-view color prior. Held-out RGB/masks are evaluation-only.
```

Decision:

```text
G110 predictions produced finite original-G55 held-out metrics and should be compared by the three-arm contract.
```

Next gate:

```text
Rerun the three-arm contract against direct and naive baselines, then run a repo-safe mask audit.
```
