# G117 Source-Gated Pseudo Prior Ablations

Date: 2026-05-28

Verdict:

```text
PASS_G117_SOURCE_GATED_PSEUDO_PRIOR_ABLATIONS_READY
```

No-leakage policy:

```text
Ablation parameter selection uses only direct source render/source mask and generated pseudo-view manifests. Held-out RGB/masks are not read by this script.
```

Variants:

| variant | policy | manifest | selected views | blend | alpha threshold u8 | prediction root |
| --- | --- | --- | ---: | ---: | ---: | --- |
| full_identity_confidence | full | strict_identity_confidence | 3 | 0.620152 | 48 | /data1/workspace/airulan/3dv_work/runs/g117_source_gated_pseudo_prior_ablation/full_identity_confidence/predictions |
| without_identity_gate | no_identity | aware_manifest_all_train_candidates_no_identity_weight | 6 | 0.169906 | 48 | /data1/workspace/airulan/3dv_work/runs/g117_source_gated_pseudo_prior_ablation/without_identity_gate/predictions |
| without_confidence_gate | no_confidence | strict_identity_no_confidence_weight | 3 | 0.650000 | 48 | /data1/workspace/airulan/3dv_work/runs/g117_source_gated_pseudo_prior_ablation/without_confidence_gate/predictions |
| without_source_alpha_gate | no_source_alpha | strict_identity_confidence_fixed_alpha_u8_8 | 3 | 0.620152 | 8 | /data1/workspace/airulan/3dv_work/runs/g117_source_gated_pseudo_prior_ablation/without_source_alpha_gate/predictions |

Decision:

```text
Ablation predictions are ready for original G55 held-out evaluation.
```

Next gate:

```text
Evaluate each G117 prediction root with the original G55 evaluator and aggregate direct/naive/G110/ablation results.
```
