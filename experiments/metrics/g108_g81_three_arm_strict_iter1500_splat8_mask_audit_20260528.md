# G108 G81 Three-Arm Mask Audit

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
| identity_confidence_aware_pseudo_view_supervision | 4.778723 | 0.306522 | 0.306522 | 0.252817 |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g108_g81_three_arm_strict_iter1500_splat8_mask_audit_20260528.png
```

Manual/VLM audit note:

```text
Mask-only audit confirms the direct arm has much stronger held-out support. Naive and identity/confidence-aware RI3D arms are weak/partial and do not provide a visual basis for a positive pseudo-view supervision claim.
```

Decision:

```text
Identity/confidence-aware pseudo-view supervision does not exceed direct + naive; G81 is a negative result under the current strict real-GT contract.
```

Next gate:

```text
Update milestones/experiment index and sync repo-safe metrics plus mask-only PNG to GitHub.
```
