# G60 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate the G59 GT pointcloud true-KRT renderer as an oracle local-visible held-out positive control for camera/evaluator plumbing.
```

Verdict:

```text
PASS_NERSEMBLE_POINTCLOUD_ORACLE_HELDOUT_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 5.680738 | -0.318929 | 0.349001 | 0.582903 | 0.380953 |
| 222200041 | 5.070267 | -0.340148 | 0.397270 | 0.536026 | 0.326258 |
| 222200047 | 5.280808 | -0.332333 | 0.380257 | 0.542842 | 0.327921 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 5.343938 |
| mean_masked_rgb_ssim_global_luma | -0.330470 |
| mean_masked_rgb_mae | 0.375509 |
| mean_prediction_mask_vs_eval_mask_iou | 0.553924 |
| mean_prediction_foreground_coverage | 0.345044 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
NeRSemble_GT_pointcloud_true_KRT_oracle
```

Interpretation:

```text
This is an oracle GT pointcloud render, not a learned-prior method result. It verifies the NeRSemble K/R/T projection and gives a sparse upper-bound sanity check for mask/RGB metrics.
```

Decision:

```text
The oracle pointcloud renderer produces finite metrics and plausible held-out camera views; the renderer contract is usable for subsequent method-output tests.
```

Next gate:

```text
Route a real method mesh/Gaussian through the same K/R/T renderer without using GT pointcloud alignment for method claims, or label any GT-aligned render as diagnostic-only.
```
