# G86 G81 Private RI3D Pool Export

Date: 2026-05-28

Verdict:

```text
PASS_G81_RI3D_PRIVATE_POOL_READY
```

Scenes:

| arm | variant | views | trainable | roles | metadata |
| --- | --- | ---: | ---: | --- | --- |
| naive_pseudo_view_supervision | g81_naive_pseudo_source_anchor | 7 | 7 | {"naive_rgb": 6, "source_identity_anchor": 1} | /data1/workspace/airulan/3dv_work/runs/g86_g81_nersemble_pseudo_ri3d_pool/candidate_pools/g81_naive_pseudo_source_anchor/source220700191/metadata.json |
| identity_confidence_aware_pseudo_view_supervision | g81_identity_confidence_aware_source_anchor | 7 | 7 | {"geometry_only": 3, "identity_supervision": 2, "identity_supervision_weak": 1, "source_identity_anchor": 1} | /data1/workspace/airulan/3dv_work/runs/g86_g81_nersemble_pseudo_ri3d_pool/candidate_pools/g81_identity_confidence_aware_source_anchor/source220700191/metadata.json |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g86_g81_nersemble_pseudo_ri3d_pool/g86_private_ri3d_pool_sheet.png
```

Decision:

```text
Private RI3D-readable naive and identity/confidence-aware scene pools are ready for scene conversion.
```

Next gate:

```text
Run scripts/prepare_ri3d_dataset.py on this private candidate root, then train/render both arms.
```
