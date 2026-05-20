# G30 Post-Guard Held-Out Eval Smoke

Date: 2026-05-20

Verdict:

```text
PASS_POST_GUARD_HELDOUT_EVAL_SMOKE_NO_QUALITY_CLAIM
```

Scope:

```text
Confirm that held-out evaluation still runs after the G29 zero-weight loss guard
and the L1-only train10 checkpoint. This is an eval-plumbing gate, not a method
result.
```

Run:

```text
run_root=/data1/workspace/airulan/3dv_work/runs/g29_ri3d_multiface_train10_l1_guard_20260520
eval_output_root=/data1/workspace/airulan/3dv_work/runs/g29_ri3d_multiface_train10_l1_guard_20260520_g30_eval
log=/data1/workspace/airulan/3dv_work/runs/g29_ri3d_multiface_train10_l1_guard_20260520/g30_heldout_eval_no_media.log
selected_gpu=0
iteration=10
skip_train=true
not_saveimages=true
not_generate_video=true
exit_code=0
```

Metrics:

| Metric | Value |
| --- | ---: |
| SSIM | 0.5905788938204447 |
| PSNR | 4.268513361612956 |
| LPIPS | 0.5011390447616577 |

Interpretation:

```text
The metrics match the G26 init-only held-out eval smoke. G29 fixed numerical
execution for the L1-only train10 path, but it did not produce a reconstruction
quality improvement.
```

Artifact policy:

```text
The eval directory contains only results.json. No PNG/JPG/JPEG/MP4/PLY files
were generated or committed.
```

Follow-up gate:

```text
G31 was run as a guarded loss-component audit before any longer training:
SSIM-only and silhouette-only were finite, while mono-depth-only blocked until
the G32 monodisp scale guard.
```
