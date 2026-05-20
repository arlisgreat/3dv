# G28 RI3D Loss-Path Diagnosis

Date: 2026-05-20

Seed:

```text
0
```

Verdict:

```text
BLOCKED_RI3D_LOSS_PATH_NUMERICAL_HEALTH
```

Checks:

| Check | Result |
| --- | --- |
| all_train_view_losses_finite | PASS |
| all_train_loop_losses_finite | BLOCK |
| all_train_loop_render_finite | PASS |
| any_train_loop_loss_nonfinite_after_step | PASS |
| first_view_render_finite | PASS |
| first_view_gt_finite | PASS |
| first_view_mono_depth_present | PASS |
| first_view_mono_depth_finite | PASS |
| first_view_l1_finite | PASS |
| first_view_ssim_finite | PASS |
| first_view_ssim_clamped_finite | PASS |
| first_view_depth_loss_finite | PASS |
| first_view_default_loss_finite | PASS |
| first_view_lambda_zero_current_loss_finite | PASS |
| first_view_lambda_zero_guarded_loss_finite | PASS |
| first_view_current_formula_with_zero_depth_weight_finite | PASS |
| first_view_alpha_finite | PASS |
| first_view_depth_finite | PASS |

Loss terms:

| Term | Finite | Value |
| --- | --- | ---: |
| l1 | yes | 0.5528423190116882 |
| lssim | yes | 0.4022095203399658 |
| lssim_clamped_render | yes | 0.4022095203399658 |
| depth_loss_monodisp | yes | 2.0 |
| loss_default_lambda_0_2 | yes | 0.5227157473564148 |
| loss_lambda_zero_current_formula | yes | 0.5528423190116882 |
| loss_lambda_zero_guarded_l1_only | yes | 0.5528423190116882 |
| loss_current_formula_with_zero_depth_weight | yes | 0.5528423190116882 |

Train loop probe:

| Iter | View | Loss finite | Render finite | L1 | Depth loss |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | 003_400055 | yes | yes | 0.570713222026825 | 2.0 |
| 2 | 004_400067 | yes | yes | 0.565009355545044 | 2.0 |
| 3 | 000_400017 | yes | yes | 0.5528423190116882 | 2.0 |
| 4 | 002_400050 | yes | yes | 0.5614609122276306 | 2.0 |
| 5 | 005_400070 | yes | yes | 0.5714933276176453 | 2.0 |
| 6 | 001_400023 | yes | yes | 0.7141036987304688 | 1.9999995231628418 |
| 7 | 002_400050 | yes | yes | 0.6046016216278076 | 1.9999998807907104 |
| 8 | 004_400067 | no | yes | 0.6098822355270386 | nan |
| 9 | 003_400055 | no | yes | 0.6167763471603394 | nan |
| 10 | 005_400070 | no | yes | 0.6170558929443359 | nan |

Render range:

```text
render min=0.7226554751396179 max=1.0 nonfinite=0
gt min=0.0 max=1.0 nonfinite=0
rendered_depth min=0.0 max=0.33337870240211487 nonfinite=0
mono_depth min=0.9616005420684814 max=1.14766526222229 nonfinite=0
```

Likely source:

```text
Training loop becomes non-finite at iteration 8 on view 004_400067.
```

Artifact policy:

```text
No RGB renders, PLYs, or raw media are written by this diagnosis; only compact metrics are committed.
```

Next gate:

```text
G29 should patch the RI3D loss path to skip zero-weight non-finite terms, especially mono-depth loss when mono_depth_weight=0, then rerun the G27 tiny training gate.
```
