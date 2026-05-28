# G83 NeRSemble Pseudo-View Source Prep

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
| source_serial | 220700191 |
| local_eval_serials | 222200042, 222200041, 222200047 |
| mask_coverage | 0.645397 |
| private_source_input | /data1/workspace/airulan/3dv_work/runs/g83_nersemble_source220700191_pseudo_input/cam_220700191_masked_square_512.png |
| private_source_input_sha256 | eee9690ca2001a30966b4566758f97f7c9abe4159f66eb19d182725f5b34188d |

Decision:

```text
Private masked-square source input is ready for Zero123++ or another pseudo-view generator.
```

Next gate:

```text
Run pseudo-view generation from this private source input, then build the G81 naive and identity/confidence-aware arms.
```
