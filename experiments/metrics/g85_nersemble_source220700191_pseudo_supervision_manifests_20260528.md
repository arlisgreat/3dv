# G85 NeRSemble Pseudo-View Supervision Manifests

Date: 2026-05-28

Verdict:

```text
PASS_G81_NERSEMBLE_PSEUDO_MANIFESTS_READY_PRIVATE
```

Summary:

| field | value |
| --- | ---: |
| pseudo_view_count | 6 |
| aware_trainable_count | 6 |
| aware_identity_count | 3 |
| aware_geometry_count | 3 |
| aware_reject_count | 0 |

Aware roles:

| view | azimuth | elevation | role | cosine | confidence | rgb weight | depth weight |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 30 | 20 | identity_supervision | 0.720435 | 100.000 | 1.000 | 1.000 |
| 1 | 90 | -10 | geometry_only | None | 86.773 | 0.200 | 1.000 |
| 2 | 150 | 20 | geometry_only | None | 84.953 | 0.200 | 1.000 |
| 3 | 210 | -10 | geometry_only | None | 85.868 | 0.200 | 1.000 |
| 4 | 270 | 20 | identity_supervision_weak | 0.567084 | 95.408 | 0.650 | 0.800 |
| 5 | 330 | -10 | identity_supervision | 0.875623 | 100.000 | 1.000 | 1.000 |

Private manifests:

```text
/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/naive_pseudo_supervision_manifest.json
/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/identity_confidence_aware_pseudo_supervision_manifest.json
/data1/workspace/airulan/3dv_work/runs/g85_zero123plus_nersemble_source220700191_steps75/g81_manifests/g85_private_pseudo_view_identity_confidence_sheet.png
```

Decision:

```text
Naive and identity/confidence-aware pseudo-supervision manifests are ready for RI3D/3DGS arm construction.
```

Next gate:

```text
Prepare RI3D/3DGS scenes for naive and aware arms, train/render held-out predictions, then rerun G84.
```
