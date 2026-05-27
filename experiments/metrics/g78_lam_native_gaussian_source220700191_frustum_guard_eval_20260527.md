# G78 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G77 LAM native Gaussian true-KRT predictions after source-mask plus eval-camera-frustum crop guard alignment. The alignment uses no held-out RGB/mask or GT pointcloud.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_NATIVE_GAUSSIAN_FRUSTUM_GUARD_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 12.229035 | 0.373029 | 0.150720 | 0.887575 | 0.722149 |
| 222200041 | 12.318789 | 0.436214 | 0.149152 | 0.899471 | 0.651713 |
| 222200047 | 13.523541 | 0.541588 | 0.123405 | 0.913003 | 0.635064 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 12.690455 |
| mean_masked_rgb_ssim_global_luma | 0.450277 |
| mean_masked_rgb_mae | 0.141092 |
| mean_prediction_mask_vs_eval_mask_iou | 0.900017 |
| mean_prediction_foreground_coverage | 0.669642 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_native_Gaussian_true_KRT_source220700191_source_mask_eval_frustum_guard
```

Interpretation:

```text
G77 tests whether a source-only silhouette fit with camera-metadata crop guard improves the LAM head-anchored Gaussian path without held-out image leakage.
```

Decision:

```text
Held-out RGB/mask metrics are finite for G77; visual gate controls whether crop risk is sufficiently reduced for the method-direction claim.
```

Next gate:

```text
Run G79 visual/mask audit and private sheet review. Only if all held-out views are non-cropped should this become the current best method-direction positive.
```
