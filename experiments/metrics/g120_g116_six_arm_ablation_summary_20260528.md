# G120 G116 Six-Arm Ablation Summary

Date: 2026-05-28

Verdict:

```text
PASS_G116_SINGLE_CASE_SIX_ARM_ABLATION_READY_MULTICASE_PENDING
```

Single-case arms:

| arm | role | PSNR | SSIM | mask IoU | coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| direct_single_image_gaussian_lam | direct prior strength | 12.690455 | 0.450277 | 0.900017 | 0.669642 |
| naive_pseudo_view_pipeline | pseudo-view reconstruction baseline | 4.904916 | 0.015267 | 0.309712 | 0.324068 |
| identity_confidence_aware_pseudo_prior | full gated method | 13.068552 | 0.458728 | 0.915092 | 0.626027 |
| without_identity_gate | identity ablation | 12.923015 | 0.452690 | 0.915092 | 0.626027 |
| without_confidence_gate | confidence ablation | 13.068995 | 0.458379 | 0.915092 | 0.626027 |
| without_source_gated_alpha_geometry_prior | geometry/source-alpha ablation | 4.778723 | 0.010534 | 0.306522 | 0.252817 |

Ablation conclusions:

```text
Full gated pseudo prior exceeds direct on PSNR by 0.378097 and mask IoU by 0.015076.
Full gated pseudo prior exceeds naive by 8.163636 PSNR and 0.605381 mask IoU.
Identity gate has a positive single-case RGB effect: full PSNR - w/o identity PSNR = 0.145537; masks are identical because both keep source-gated alpha/direct geometry.
Confidence gate is inconclusive in this case: w/o confidence PSNR differs by 0.000443, while SSIM differs by -0.000349; mask is unchanged.
Direct geometry/source alpha is the dominant factor: removing it drops from full PSNR/mask IoU 13.068552/0.915092 to 4.778723/0.306522.
```

Naive camera/crop audit:

```text
The naive arm was rendered with the same NeRSemble eval cameras and an explicit eval-camera frustum guard. The frustum is not catastrophically empty (min in-frame 0.482), but source-mask alignment is poor (0.323) compared with direct (0.889). This supports source/crop/geometry collapse in the RI3D pseudo-geometry output as the primary failure, not a simple evaluator K/R/T wiring error. It still means naive is a weak baseline and should be reported with this caveat.
```

Remaining requirement:

```text
Multi-case replication is still pending; this G120 summary proves only the current single NeRSemble source/eval split.
```
