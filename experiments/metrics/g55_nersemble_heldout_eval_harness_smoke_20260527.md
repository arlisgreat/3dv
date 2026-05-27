# G55 NeRSemble Held-Out Eval Harness Smoke

Date: 2026-05-27

Premise:

```text
Exercise the NeRSemble held-out metric chain with a deliberately weak copy-source baseline. The source image is pasted as the prediction for each local held-out camera; this validates metric IO only.
```

Verdict:

```text
PASS_NERSEMBLE_HELDOUT_EVAL_HARNESS_SMOKE_COPY_BASELINE
```

Metrics:

| eval serial | PSNR mask | SSIM global luma | MAE mask | copy mask IoU |
| --- | ---: | ---: | ---: | ---: |
| 220700191 | 12.071801 | 0.462999 | 0.156714 | 0.836145 |
| 222200041 | 11.442771 | 0.342381 | 0.184817 | 0.827324 |
| 222200047 | 11.675924 | 0.288558 | 0.173916 | 0.841295 |

Mean metrics:

| field | value |
| --- | ---: |
| mean_masked_rgb_psnr | 11.730165 |
| mean_masked_rgb_ssim_global_luma | 0.364646 |
| mean_masked_rgb_mae | 0.171815 |
| mean_source_mask_vs_eval_mask_iou | 0.834921 |

Interpretation:

```text
The low copy-baseline numbers are expected because the target cameras see different viewpoints. This is a harness smoke and lower-bound sanity check, not a method-quality result.
```

Decision:

```text
Held-out RGB/mask metric plumbing is ready for a real learned-prior/feed-forward method output.
```

Next gate:

```text
Run a real method output through this exact source/eval split, then report RGB/mask/geometry metrics only after model distribution and artifact/privacy gates pass.
```
