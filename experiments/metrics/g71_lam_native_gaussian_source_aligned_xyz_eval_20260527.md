# G71 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G70 LAM native Gaussian true-KRT renders on the G54 NeRSemble visible held-out cameras. G70 fixes the earlier gs_offset coordinate bug by using framework_img.obj xyz with PLY opacity/scale/rotation, source-mask-only alignment, and LAM diff-gaussian rasterization.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_NATIVE_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNED_XYZ_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 6.534043 | -0.153598 | 0.371158 | 0.586129 | 0.580943 |
| 222200041 | 6.099380 | 0.041026 | 0.403439 | 0.482606 | 0.470986 |
| 222200047 | 6.321129 | 0.167884 | 0.397260 | 0.425278 | 0.494230 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 6.318184 |
| mean_masked_rgb_ssim_global_luma | 0.018438 |
| mean_masked_rgb_mae | 0.390619 |
| mean_prediction_mask_vs_eval_mask_iou | 0.498004 |
| mean_prediction_foreground_coverage | 0.515386 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_native_Gaussian_true_KRT_source_mask_aligned_xyz_diagnostic
```

Interpretation:

```text
This is the closest current test of the learned-prior/feed-forward/head-anchored Gaussian idea: a LAM Gaussian output rendered into real NeRSemble held-out cameras after source-only alignment. It is still an in-domain diagnostic baseline and must pass visual/mask gate before a quality claim.
```

Decision:

```text
Held-out metrics are finite; visual/mask/appearance gate determines whether the route validates the overall method direction or remains diagnostic.
```

Next gate:

```text
Run repo-safe mask audit and private VLM/manual visual audit for G70/G71. If visual appearance is plausible, extend to more NeRSemble cases; if not, switch to native camera-conditioned feed-forward avatar methods.
```
