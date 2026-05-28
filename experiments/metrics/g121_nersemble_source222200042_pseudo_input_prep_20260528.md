# G121 NeRSemble Pseudo-View Source Prep

Date: 2026-05-28

Premise:

```text
Prepare the single real NeRSemble source image for pseudo-view generation. This uses only the source RGB/mask; held-out RGB/masks remain evaluation-only.
```

Verdict:

```text
PASS_G81_NERSEMBLE_SOURCE_PSEUDO_INPUT_READY_PRIVATE
```

Source:

| field | value |
| --- | --- |
| participant | 388 |
| sequence | GLASSES |
| timestep | 0 |
| source_serial | 222200042 |
| local_eval_serials | 220700191, 222200041, 222200047 |
| mask_coverage | 0.670186 |
| private_source_input | /data1/workspace/airulan/3dv_work/runs/g121_nersemble_source222200042_pseudo_input/cam_222200042_masked_square_512.png |
| private_source_input_sha256 | 45932f49c705fc9cbd18541da24f3713a35122e0844a2cb2f1a1f960ac2f47c0 |

Decision:

```text
Private masked-square source input is ready for Zero123++ or another pseudo-view generator.
```

Next gate:

```text
Run pseudo-view generation from this private source input, then build the G81 naive and identity/confidence-aware arms.
```
