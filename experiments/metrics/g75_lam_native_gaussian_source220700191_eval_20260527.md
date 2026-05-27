# G75 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G74 LAM native Gaussian true-KRT renders using a frontal NeRSemble source camera 220700191 and local held-out cameras 222200042/222200041/222200047. This tests whether G70 crop risk was caused mainly by the side-view source.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_NATIVE_GAUSSIAN_SOURCE220700191_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 222200042 | 5.137898 | 0.217843 | 0.491954 | 0.326161 | 0.270110 |
| 222200041 | 6.175000 | 0.063576 | 0.409627 | 0.571201 | 0.382873 |
| 222200047 | 6.344122 | 0.003719 | 0.395338 | 0.479368 | 0.561120 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 5.885673 |
| mean_masked_rgb_ssim_global_luma | 0.095046 |
| mean_masked_rgb_mae | 0.432306 |
| mean_prediction_mask_vs_eval_mask_iou | 0.458910 |
| mean_prediction_foreground_coverage | 0.404701 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_native_Gaussian_true_KRT_source220700191_source_mask_aligned
```

Interpretation:

```text
G74 uses a real captured frontal source, LAM native Gaussian output, source-mask-only alignment, and official NeRSemble K/R/T held-out cameras. It remains diagnostic until the visual gate confirms non-cropped held-out views.
```

Decision:

```text
Held-out metrics are finite; visual/mask gate determines whether this source choice improves the method direction enough to scale.
```

Next gate:

```text
Run visual/mask audit. If one or more held-out cameras remain cropped, G74 is a diagnostic positive only and G77 must address source-only pose alignment or use native camera-conditioned inference.
```
