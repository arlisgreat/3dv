# G106 G81 Real-GT Iteration Summary

Date: 2026-05-28

Verdict:

```text
FAIL_G81_CURRENT_PSEUDO_VIEW_SUPERVISION_HYPOTHESIS_NOT_VALIDATED
```

Metric summary:

| label | PSNR | mask IoU | coverage |
| --- | ---: | ---: | ---: |
| direct_single_image_gaussian | 12.690455 | 0.900017 | 0.669642 |
| iter80_splat3_naive | 4.677511 | 0.275241 | 0.271843 |
| iter80_splat3_aware | 4.692126 | 0.277022 | 0.273063 |
| iter80_splat8_naive | 4.582829 | 0.264548 | 0.295674 |
| iter80_splat8_aware | 4.795571 | 0.292328 | 0.295789 |
| iter1500_splat8_naive | 4.905284 | 0.309674 | 0.323703 |
| iter1500_splat8_aware | 4.737665 | 0.287835 | 0.323394 |
| strict_iter1500_splat8_naive | 4.904916 | 0.309712 | 0.324068 |
| strict_iter1500_splat8_aware | 4.778723 | 0.306522 | 0.252817 |

Contract gates:

| gate | verdict | file |
| --- | --- | --- |
| G84 | FAIL_G81_IDENTITY_CONFIDENCE_AWARE_DOES_NOT_BEAT_BASELINES | experiments/metrics/g84_g81_three_arm_contract_gate_20260528.json |
| G84 | FAIL_G81_IDENTITY_CONFIDENCE_AWARE_DOES_NOT_BEAT_BASELINES | experiments/metrics/g94_g81_three_arm_contract_splat8_gate_20260528.json |
| G99 | FAIL_G81_IDENTITY_CONFIDENCE_AWARE_DOES_NOT_BEAT_BASELINES | experiments/metrics/g99_g81_three_arm_contract_iter1500_splat8_gate_20260528.json |
| G105 | FAIL_G81_IDENTITY_CONFIDENCE_AWARE_DOES_NOT_BEAT_BASELINES | experiments/metrics/g105_g81_three_arm_contract_strict_aware_iter1500_splat8_gate_20260528.json |

Findings:

- The pipeline is now real-GT gated: source-only pseudo-view generation, private pseudo supervision manifests, RI3D training, NeRSemble true-KRT held-out rendering, and G55/G84 evaluator contract all ran.
- Identity/confidence-aware supervision gave only a small short-train improvement over naive at iter80, but did not beat direct.
- After 1500-step densification, naive exceeded aware; rejecting geometry_only views improved conceptual cleanliness but still did not beat naive or direct.
- The direct LAM single-image Gaussian baseline remains far stronger: PSNR 12.690455 / mask IoU 0.900017 versus best pseudo-view RI3D PSNR 4.905284 / mask IoU 0.309711.
- Current evidence supports a negative result for naive pseudo-view-to-3DGS supervision under this NeRSemble case, not a positive method claim.

Risks and limits:

- G88/G91/G96/G102 use a point-splat diagnostic renderer for RI3D PLYs, not the exact differentiable Gaussian renderer.
- No manual/VLM visual gate was completed inside this sandbox; private contact sheets exist under 3dv_work and need human/VLM review.
- This is a single source case; it is sufficient to block the current positive claim, not sufficient for broad statistical conclusions.
- The direct LAM baseline is likely in or near LAM training distribution for NeRSemble, so it should be labeled an in-domain diagnostic baseline.

Recommended next milestone:

```text
Do not continue the current from-scratch RI3D pseudo-view route as a positive claim. The next credible attempt should be a head-anchored learned-prior refinement: start from a strong direct Gaussian/mesh prior, apply source/identity-only pseudo-view constraints with exact renderer support, and keep the same G84 contract. If that cannot beat direct, reposition the project as a real-GT evaluator/protocol and negative pseudo-view supervision study.
```

Decision:

```text
Current G81 hypothesis is not validated; repository should preserve the negative evidence and prevent qualitative pseudo-view renders from being reported as success.
```
