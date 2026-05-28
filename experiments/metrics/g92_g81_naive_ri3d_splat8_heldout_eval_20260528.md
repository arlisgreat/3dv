# G92 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the naive pseudo-view RI3D arm with G91 splat8 NeRSemble held-out renders.
```

Verdict:

```text
PASS_G81_NAIVE_PSEUDO_VIEW_RI3D_SPLAT8_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 4.675717 | -0.043941 | 0.497852 | 0.297787 | 0.313957 |
| 222200041 | 4.338646 | 0.049271 | 0.529616 | 0.187179 | 0.294946 |
| 222200047 | 4.734122 | -0.035330 | 0.501050 | 0.308679 | 0.278118 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 4.582829 |
| mean_masked_rgb_ssim_global_luma | -0.010000 |
| mean_masked_rgb_mae | 0.509506 |
| mean_prediction_mask_vs_eval_mask_iou | 0.264548 |
| mean_prediction_foreground_coverage | 0.295674 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
g81_naive_pseudo_view_supervision_ri3d_iter80_point_splat8
```

Interpretation:

```text
Renderer-only splat radius ablation for the naive G81 baseline.
```

Decision:

```text
Naive splat8 RI3D predictions produced finite held-out metrics.
```

Next gate:

```text
Evaluate aware splat8 and rerun G84 if improved.
```
