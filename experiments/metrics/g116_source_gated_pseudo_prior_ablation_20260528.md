# G116 Source-Gated Pseudo Prior Ablation

Date: 2026-05-28

Verdict:

```text
PASS_G116_SOURCE_GATED_PSEUDO_PRIOR_ABLATION_READY
```

No-leakage policy:

```text
Ablation generation reads only the direct source render, source RGB/mask, direct held-out predictions, and generated pseudo-view manifests/images. Held-out RGB/masks are not read by this script.
```

Shared source alpha gate:

| field | value |
| --- | ---: |
| threshold_u8 | 48 |
| source_mask_iou | 0.952514 |
| prediction_coverage | 0.644093 |
| target_coverage | 0.645397 |

Variants:

| variant | selected views | blend | prediction root |
| --- | ---: | ---: | --- |
| identity_confidence_aware_pseudo_prior | 3 | 0.620152 | /data1/workspace/airulan/3dv_work/runs/g116_source_gated_pseudo_prior_ablation/identity_confidence_aware_pseudo_prior/predictions |
| without_identity_gate | 6 | 0.169906 | /data1/workspace/airulan/3dv_work/runs/g116_source_gated_pseudo_prior_ablation/without_identity_gate/predictions |
| without_confidence_gate | 3 | 0.650000 | /data1/workspace/airulan/3dv_work/runs/g116_source_gated_pseudo_prior_ablation/without_confidence_gate/predictions |

Decision:

```text
Generated source-gated pseudo-prior ablation prediction roots for held-out evaluator runs.
```

Next gate:

```text
Evaluate each G116 ablation root with the original G55 held-out evaluator, then summarize six-arm results.
```
