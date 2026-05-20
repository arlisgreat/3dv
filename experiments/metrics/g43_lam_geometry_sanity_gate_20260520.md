# G43 LAM Geometry Sanity Gate

Date: 2026-05-20

Verdict:

```text
PASS_NORMALIZED_GEOMETRY_SANITY_NOT_QUALITY_METRIC
```

Scope:

```text
Weak normalized geometry sanity only. The LAM shaped mesh and Multiface tracked mesh are compared after independent bbox normalization, with no camera alignment, no scale recovery, and no held-out rendering. This can catch catastrophic shape/export failure but cannot support a quality claim.
```

Geometry stats:

| field | LAM shaped mesh | Multiface GT mesh |
| --- | ---: | ---: |
| vertex_count | 5023 | 7306 |
| bbox_diag | 0.451613 | 462.264619 |

Normalized nearest-neighbor sanity:

| metric | value |
| --- | ---: |
| lam_to_gt_mean | 0.036199 |
| gt_to_lam_mean | 0.035110 |
| symmetric_mean | 0.035655 |

Latest literature monitor:

| work | date | signal |
| --- | --- | --- |
| FFAvatar | 2026-05-14 | Few-shot feed-forward Gaussian heads report NeRSemble metrics and a 5.5 PSNR gain over LAM, so LAM should be treated as baseline/export probe, not final method. |
| Any3DAvatar | 2026-04-15 | Single-image full-head work uses a structured Plucker-aware Gaussian scaffold and dense multi-view supervision. |
| MATCH | 2026-03-16 | Recent feed-forward Gaussian registration predicts in a fixed UV/template correspondence layout from calibrated multi-view images. |
| FastGHA | 2026-01-30 | Uses feed-forward per-pixel Gaussians, transformer multi-view aggregation, and explicit geometry supervision from point maps. |
| PanoLAM | 2025-10-10 | Full-head Gaussian one-shot direction relies on FLAME sparse points, transformers, and synthetic 3D-GAN priors. |

Blocked interpretations:

```text
Do not report the normalized nearest-neighbor value as reconstruction accuracy.
Do not compare this weak mesh sanity to RI3D held-out PSNR/SSIM/LPIPS.
Do not publish the private LAM/Multiface OBJ, PLY, PNG, or MP4 artifacts without review.
Do not reintroduce pseudo-view candidate pools as training or evaluation data.
```

Decision:

```text
G43 passes as an export/geometry sanity check: LAM emits a non-degenerate head-shaped mesh near the local GT shape after scale-free normalization. The next real milestone remains camera-aligned held-out rendering or an explicitly aligned GT geometry metric.
```
