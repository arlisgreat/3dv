# G33 Combined Guarded Train10 Eval

Date: 2026-05-20

Verdict:

```text
PASS_COMBINED_GUARDED_TRAIN10_EVAL_NO_QUALITY_GAIN
```

Scope:

```text
Run combined guarded SSIM, silhouette, and mono-depth train10 after G29 and G32
numerical guards, then evaluate held-out views without saving images/video.
```

Run:

```text
run_root=/data1/workspace/airulan/3dv_work/runs/g33_ri3d_combined_guarded_train10_20260520
iterations=10
lambda_dssim=0.2
lambda_silhouette=0.01
mono_depth_weight=0.01
use_mask=true
selected_gpu=0
exit_code=0
final_progress_loss=0.5910920
```

Train-log metrics:

| Split | L1 | PSNR |
| --- | ---: | ---: |
| test | 0.5926034251848856 | 4.268513361612955 |
| train | 0.6414348959922791 | 3.5272224426269534 |

Held-out eval metrics:

| Metric | Value |
| --- | ---: |
| SSIM | 0.5905788938204447 |
| PSNR | 4.268513361612956 |
| LPIPS | 0.5011390447616577 |

Interpretation:

```text
Combined guarded train10 is numerically finite, but held-out metrics match G26
and G30 init-level eval. This closes the numerical-smoke loop, not the
reconstruction-quality loop.
```

Artifact policy:

```text
The iteration-10 PLY and logs remain local under 3dv_work. Eval output contains
only results.json. No PNG/JPG/JPEG/MP4 files were generated or committed.
```

Stop condition:

```text
No longer/default-loss training milestone is authorized from the current evidence.
The next scientific step is method redesign or a stronger public real-GT
benchmark, not scaling RI3D iterations on this setup.
```
