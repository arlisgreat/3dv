# G110 Source-Gated Pseudo Prior Refinement

Date: 2026-05-28

Verdict:

```text
PASS_G110_SOURCE_GATED_PSEUDO_PRIOR_REFINEMENT_READY
```

No-leakage policy:

```text
Parameter selection uses only the direct source render, source RGB/mask, and generated pseudo views from the strict identity/confidence-aware manifest. Held-out RGB/masks are not read by this script.
```

Source gate:

| field | value |
| --- | ---: |
| selected_alpha_threshold_u8 | 48 |
| source_mask_iou | 0.952514 |
| source_prediction_coverage | 0.644093 |
| source_target_coverage | 0.645397 |
| pseudo_color_blend | 0.620152 |

Selected pseudo views:

| view | role | identity | confidence | rgb weight | moment weight | pixels |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | identity_supervision | 0.720435 | 100.000000 | 1.000000 | 0.720435 | 33771 |
| 4 | identity_supervision_weak | 0.567084 | 95.407947 | 0.650000 | 0.351678 | 29715 |
| 5 | identity_supervision | 0.875623 | 100.000000 | 1.000000 | 0.875623 | 34673 |

Prediction root:

```text
/data1/workspace/airulan/3dv_work/runs/g110_source_gated_pseudo_prior_refinement/predictions
```

Decision:

```text
Source-gated direct-prior refinement produced held-out prediction PNGs for evaluator comparison.
```

Next gate:

```text
Evaluate G110 predictions with the held-out evaluator, rerun the three-arm contract, and audit masks.
```
