# G112 G81 Three-Arm Pseudo-Supervision Contract

Date: 2026-05-28

Premise:

```text
Gate the actual G81 claim: identity/confidence-aware pseudo-view supervision must beat both direct single-image Gaussian and naive pseudo-view supervision on the same real held-out cameras.
```

Verdict:

```text
PASS_G81_IDENTITY_CONFIDENCE_AWARE_PSEUDO_SUPERVISION_BEATS_BASELINES
```

Arms:

| arm | predictions | eval | pseudo manifest | PSNR | mask IoU | ready |
| --- | --- | --- | --- | ---: | ---: | --- |
| direct_single_image_gaussian | True | True | None | 12.690454933591733 | 0.9000165206203238 | True |
| naive_pseudo_view_supervision | True | True | True | 4.904915857890938 | 0.30971166292766217 | True |
| identity_confidence_aware_pseudo_view_supervision | True | True | True | 13.06855187444915 | 0.9150921915885543 | True |

Missing Requirements:

```text
none
```

Decision:

```text
Three-arm comparison is ready and the identity/confidence-aware arm beats both baselines.
```

Next gate:

```text
Run visual/VLM gate and multi-case replication before making a paper claim.
```
