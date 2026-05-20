# G32 Monodisp Scale Guard Train10

Date: 2026-05-20

Verdict:

```text
PASS_MONODISP_SCALE_GUARD_DEPTH_TRAIN10
```

Patch:

```text
patches/ri3d/g32_monodisp_scale_guard.patch
```

Patch summary:

```text
Clamp monodisp dynamic and GT median-absolute-deviation denominators to at least
1e-6, preventing constant or near-constant depth vectors from dividing by zero.
```

Results:

| Case | Mask | Final loss | Finite | Test PSNR |
| --- | --- | ---: | --- | ---: |
| G32a depth-only | no | 0.6245082 | yes | 4.268513361612955 |
| G32b depth-only | yes | 0.6245082 | yes | 4.268513361612955 |

Interpretation:

```text
G32 resolves the G31 mono-depth NaN class for train10, but held-out metrics stay
at init-level values. This is a numerical repair only.
```

Artifact policy:

```text
All PLYs and logs remain local under 3dv_work. No PNG/JPG/JPEG/MP4 files were
generated or committed.
```
