# G55 NeRSemble Held-Out Eval

Date: 2026-05-27

Premise:

```text
Exercise the NeRSemble held-out metric chain. In copy-source mode this is a deliberately weak baseline; in prediction-root mode it evaluates real method outputs for each local held-out camera.
```

Verdict:

```text
PASS_NERSEMBLE_HELDOUT_EVAL_HARNESS_SMOKE_COPY_BASELINE
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | prediction mask IoU | prediction coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 220700191 | 12.071801 | 0.462999 | 0.156714 | 0.836145 | 0.670186 |
| 222200041 | 11.442771 | 0.342381 | 0.184817 | 0.827324 | 0.670186 |
| 222200047 | 11.675924 | 0.288558 | 0.173916 | 0.841295 | 0.670186 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 11.730165 |
| mean_masked_rgb_ssim_global_luma | 0.364646 |
| mean_masked_rgb_mae | 0.171815 |
| mean_prediction_mask_vs_eval_mask_iou | 0.834921 |
| mean_prediction_foreground_coverage | 0.670186 |

Evaluation mode:

```text
copy_source_baseline
```

Method label:

```text
copy_source_baseline
```

Interpretation:

```text
The copy-source baseline is expected to be low because target cameras see different viewpoints. Prediction-root mode can support a method-quality discussion only after model distribution and artifact gates pass.
```

Decision:

```text
Held-out RGB/mask metric plumbing is ready for a real learned-prior/feed-forward method output.
```

Next gate:

```text
Run a real method output through this exact source/eval split, then report RGB/mask/geometry metrics only after model distribution and artifact/privacy gates pass.
```
