# G97 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the naive pseudo-view RI3D arm after G95 1500-step training and G96 splat8 NeRSemble held-out rendering.
```

Verdict:

```text
PASS_G81_NAIVE_PSEUDO_VIEW_RI3D_ITER1500_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.675381 | -0.047599 | 0.498303 | 0.284267 | 0.327937 |
| 222200041 | 4.667557 | 0.023550 | 0.502535 | 0.266330 | 0.320213 |
| 222200047 | 5.372913 | 0.069687 | 0.442984 | 0.378426 | 0.322961 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.905284 |
| mean_masked_rgb_ssim_global_luma | 0.015213 |
| mean_masked_rgb_mae | 0.481274 |
| mean_prediction_mask_vs_eval_mask_iou | 0.309674 |
| mean_prediction_foreground_coverage | 0.323703 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_naive_pseudo_view_supervision_ri3d_iter1500_point_splat8
```

Interpretation:

```text
Densified naive pseudo-view supervision baseline for G81.
```

Decision:

```text
Naive iter1500 predictions produced finite held-out metrics.
```

Next gate:

```text
Evaluate aware iter1500 and rerun G84/G99 contract.
```
