# G89 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the naive pseudo-view RI3D arm on the audited NeRSemble source220700191 held-out cameras using G88 point-splat predictions.
```

Verdict:

```text
PASS_G81_NAIVE_PSEUDO_VIEW_RI3D_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.373218 | -0.067578 | 0.525447 | 0.249163 | 0.269485 |
| 222200041 | 4.549786 | 0.059247 | 0.502383 | 0.239715 | 0.261956 |
| 222200047 | 5.109528 | 0.061131 | 0.473088 | 0.336844 | 0.284089 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.677511 |
| mean_masked_rgb_ssim_global_luma | 0.017600 |
| mean_masked_rgb_mae | 0.500306 |
| mean_prediction_mask_vs_eval_mask_iou | 0.275241 |
| mean_prediction_foreground_coverage | 0.271843 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_naive_pseudo_view_supervision_ri3d_iter80_point_splat
```

Interpretation:

```text
This is the naive pseudo-view supervision baseline for G81. It can be compared only inside the same source split, renderer, and evaluator.
```

Decision:

```text
Naive pseudo-view RI3D predictions produced finite held-out metrics.
```

Next gate:

```text
Evaluate the identity/confidence-aware arm and rerun G84 three-arm contract.
```
