# G27 RI3D Train10 Numerical Gate

Date: 2026-05-20

Verdict:

```text
BLOCKED_RI3D_TRAINING_NUMERICAL_HEALTH_NAN
NO_QUALITY_CLAIM
```

Scope:

```text
Run a tiny real-GT RI3D training smoke from the G25 initialization. This gate
checks whether training loss is numerically valid before any longer run.
```

Runs:

| Run | Exit | Loss | Test PSNR | Train PSNR | Meaning |
| --- | ---: | --- | ---: | ---: | --- |
| G27 mask + depth + silhouette | 0 | nan | 4.2685 | 3.5273 | Executes, but fails numerical-health gate. |
| G27b mask RGB-only | 0 | nan | 4.2685 | 3.5273 | NaN is not isolated to depth/silhouette. |
| G27c plain RGB | 0 | nan | 4.2685 | 3.5272 | NaN persists without mask or random background. |
| G27d L1-only | 0 | nan | 4.2685 | 3.5268 | NaN persists even with `lambda_dssim=0`. |

Finite artifact check:

```text
G25 iteration-1 PLY nonfinite_total: 0
G27 iteration-10 PLY nonfinite_total: 0
G27c iteration-10 PLY nonfinite_total: 0
point_count: 67410
```

Interpretation:

```text
The adapter, initialization, and held-out eval plumbing pass, but small-step
training does not. RI3D reports NaN training loss even in the plain L1-only
configuration. Because held-out PSNR remains equal to the init-only result, G27
must block any longer training or reconstruction-quality claim.
```

Artifact policy:

```text
All point clouds, cfg_args, cameras.json, and logs remain under 3dv_work. The
repo records only compact metrics and the blocker.
```

Next gate:

```text
G28 should be a loss-path numerical diagnostic: inspect the render/loss tensors
for the first training step before any further RI3D training.
```
