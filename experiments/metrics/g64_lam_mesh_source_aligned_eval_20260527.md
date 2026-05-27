# G64 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Evaluate G63 source-mask-only aligned LAM textured-mesh true-KRT renders on the G54 NeRSemble visible held-out cameras. This tests the method-output-to-G55 evaluator path without GT pointcloud or held-out alignment, but remains diagnostic unless the visual gate passes.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_MESH_TRUE_KRT_SOURCE_MASK_ALIGNED_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 5.918724 | -0.082072 | 0.418372 | 0.493862 | 0.497442 |
| 222200041 | 5.609155 | 0.048631 | 0.437112 | 0.419514 | 0.415471 |
| 222200047 | 5.890752 | 0.191470 | 0.431025 | 0.354928 | 0.427952 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 5.806210 |
| mean_masked_rgb_ssim_global_luma | 0.052677 |
| mean_masked_rgb_mae | 0.428837 |
| mean_prediction_mask_vs_eval_mask_iou | 0.422768 |
| mean_prediction_foreground_coverage | 0.446955 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM_mesh_true_KRT_source_mask_aligned_diagnostic
```

Interpretation:

```text
G63 removes GT pointcloud alignment and uses the official NeRSemble K/R/T evaluator path. Metrics are interpretable only as a diagnostic of the current LAM mesh output because the private visual sheet shows severe texture/appearance corruption.
```

Decision:

```text
Held-out metrics are finite, but the G63 visual gate must decide whether this validates the overall learned-prior/feed-forward direction.
```

Next gate:

```text
Run a visual/mask renderer-contract gate for G63. If texture/appearance remains broken, mark the current LAM mesh route as diagnostic failure and switch to native NeRSemble-camera aligned feed-forward output.
```
