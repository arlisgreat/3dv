# G54 NeRSemble NVS Frame-0 Adapter Preflight

Date: 2026-05-27

Premise:

```text
Build the smallest real NeRSemble NVS local adapter from official benchmark data: one frame with real RGB, alpha maps, cameras, and a pointcloud. This preflight validates data plumbing only; official leaderboard hold-out cameras remain hidden.
```

Verdict:

```text
PASS_NERSEMBLE_NVS_FRAME0_ADAPTER_PREFLIGHT_LOCAL_ONLY
```

Case:

| field | value |
| --- | --- |
| participant | 388 |
| sequence | GLASSES |
| timestep | 0 |
| source_serial | 222200042 |
| local_eval_serials | 220700191, 222200041, 222200047 |
| official_hidden_holdout_serials | 222200046, 222200037, 222200039 |

Adapter summary:

| field | value |
| --- | ---: |
| local_views_written | 13 |
| calibration_serials | 16 |
| pointcloud_points | 673854 |
| min_alpha_coverage | 0.480988 |
| max_alpha_coverage | 0.670186 |
| mask_sheet_sha256 | 7205dec4f3945f204b07fa4ac51f208b5556b01751663d60bac5b35364c88bc9 |

Repo-safe mask audit figure:

```text
/data1/workspace/airulan/3dv/experiments/figures/g54_nersemble_nvs_frame0_mask_audit_20260527.png
```

Decision:

```text
The official NVS frame-0 adapter is ready for CPU/GPU evaluation harness work. Do not present metrics as official leaderboard metrics; use visible-camera local held-outs only until submission packaging exists.
```

Next gate:

```text
G55 should implement a model-agnostic held-out evaluation harness over this adapter: source view in, local eval cameras out, RGB PSNR/SSIM/LPIPS plus mask IoU/depth or pointcloud sanity where the method output supports it.
```
