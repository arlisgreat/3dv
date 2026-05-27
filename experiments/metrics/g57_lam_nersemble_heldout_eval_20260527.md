# G57 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Exercise the NeRSemble held-out metric chain. In copy-source mode this is a deliberately weak baseline; in prediction-root mode it evaluates rendered outputs for each local held-out camera.
```

Verdict:

```text
PASS_NERSEMBLE_HELDOUT_METHOD_EVAL
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 4.218603 | 0.207326 | 0.564127 | 0.088408 | 0.189952 |
| 222200041 | 3.375878 | -0.028911 | 0.635913 | 0.018559 | 0.106414 |
| 222200047 | 3.456518 | 0.011964 | 0.632095 | 0.000000 | 0.002952 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 3.683666 |
| mean_masked_rgb_ssim_global_luma | 0.063460 |
| mean_masked_rgb_mae | 0.610712 |
| mean_prediction_mask_vs_eval_mask_iou | 0.035656 |
| mean_prediction_foreground_coverage | 0.099773 |

Evaluation mode:

```text
method_predictions
```

Method label:

```text
LAM-20K_source_to_lam_sample_diagnostic
```

Interpretation:

```text
The copy-source baseline is expected to be low because target cameras see different viewpoints. Prediction-root mode can support a method-quality discussion only after model distribution, renderer-contract, visual, and artifact gates pass.
```

Decision:

```text
Prediction files produced finite metrics, but G58 renderer-contract and visual audit controls whether this can be interpreted; current G58 downgrades it to diagnostic-only.
```

Next gate:

```text
Use G59/G60 true-KRT pointcloud positive control, then connect method mesh/Gaussian outputs to the same camera contract.
```
