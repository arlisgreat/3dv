# G31 Guarded Loss Component Audit

Date: 2026-05-20

Verdict:

```text
BLOCKED_MONODEPTH_COMPONENT_NUMERICAL_HEALTH
```

Scope:

```text
Audit RI3D loss components one at a time after the G29 zero-weight branch guard.
This is still a train10 numerical gate, not a quality result.
```

Results:

| Case | SSIM | Silhouette | Mono depth | Mask | Final loss | Finite | Test PSNR |
| --- | ---: | ---: | ---: | --- | ---: | --- | ---: |
| G31a SSIM-only | 0.2 | 0 | 0 | no | 0.5790529 | yes | 4.268513361612955 |
| G31b silhouette-only | 0 | 0.01 | 0 | yes | 0.6124692 | yes | 4.268513361612955 |
| G31c mono-depth-only | 0 | 0 | 0.01 | no | nan | no | 4.268513361612955 |
| G31d mono-depth-only masked | 0 | 0 | 0.01 | yes | nan | no | 4.268513361612955 |

Interpretation:

```text
SSIM-only train10 is finite. Silhouette-only train10 is finite but does not
produce a measurable held-out metric change versus L1-only. Mono-depth-only
train10 is non-finite with and without masks, so default/combined depth training
is blocked until the monodisp loss is numerically guarded.
```

Artifact policy:

```text
All PLYs and logs remain local under 3dv_work. No PNG/JPG/JPEG/MP4 files were
generated or committed.
```

Next gate:

```text
G32 monodisp scale guard. Do not run longer/default-loss training before depth
loss is finite.
```
