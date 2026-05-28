# G113 G81 Three-Arm Mask Audit

Date: 2026-05-28

Verdict:

```text
PASS_G81_THREE_ARM_MASK_AUDIT_DIAGNOSTIC_ONLY
```

Arm summary:

| arm | PSNR | eval mask IoU | audit mask IoU | coverage |
| --- | ---: | ---: | ---: | ---: |
| direct_single_image_gaussian | 12.690455 | 0.900017 | 0.899699 | 0.669923 |
| naive_pseudo_view_supervision | 4.904916 | 0.309712 | 0.309712 | 0.324068 |
| identity_confidence_aware_pseudo_view_supervision | 13.068552 | 0.915092 | 0.915092 | 0.626027 |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g113_source_gated_pseudo_prior_three_arm_mask_audit_g55_20260528.png
```

Manual/VLM audit note:

```text
Mask-only audit confirms the identity/confidence-aware arm has the strongest held-out mask support among the three arms. The improvement comes from source-gated direct-prior support rather than from the earlier fragmented RI3D pseudo-view geometry.
```

Decision:

```text
Identity/confidence-aware pseudo-view supervision exceeds both baselines under this mask audit and evaluator contract.
```

Next gate:

```text
Update milestones/experiment index and sync repo-safe metrics plus mask-only PNG to GitHub.
```
