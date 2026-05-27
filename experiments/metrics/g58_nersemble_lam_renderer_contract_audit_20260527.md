# G58 NeRSemble LAM Renderer Contract Audit

Date: 2026-05-27

Premise:

```text
A method metric is interpretable only if the prediction PNGs are rendered by the same learned-prior/mesh/Gaussian representation into the audited G54 NeRSemble held-out K/R/T cameras and pass a visual nonblank/alignment gate.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_RENDERER_CONTRACT_FAILED
```

Renderer contract:

| field | value |
| --- | --- |
| method | LAM-20K |
| camera_mode | source_to_lam_sample |
| camera_contract_verified | False |
| prediction_root | /data1/workspace/airulan/3dv_work/runs/g56_nersemble_lam_eval/predictions |
| eval_json_verdict | PASS_NERSEMBLE_HELDOUT_METHOD_EVAL |
| eval_mean_psnr | 3.683666408260733 |
| eval_mean_ssim | 0.06345960967868051 |
| eval_mean_prediction_mask_iou | 0.035655711987431095 |

Visual and mask audit:

| serial | pred coverage | target coverage | pred/target IoU | touches border | decision |
| --- | ---: | ---: | ---: | --- | --- |
| 220700191 | 0.189952 | 0.645397 | 0.088408 | True | weak_or_misaligned_prediction |
| 222200041 | 0.106414 | 0.601149 | 0.018559 | True | weak_or_misaligned_prediction |
| 222200047 | 0.002952 | 0.594193 | 0.000000 | True | weak_or_misaligned_prediction |

Private audit sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g58_nersemble_lam_renderer_contract_audit/g58_private_lam_vs_gt_sheet.png
```

Manual/VLM audit note:

```text
The G57 private contact sheet shows a plausible source render but the three held-out predictions are mostly blank or cropped to image borders. This is not a verified NeRSemble held-out camera rendering.
```

Decision:

```text
G57 is downgraded to diagnostic-only. Finite evaluator metrics only prove that files were readable; they do not validate the learned-prior idea or a true held-out camera renderer.
```

Next gate:

```text
Implement a true G54 K/R/T renderer positive control first, preferably with the NeRSemble GT pointcloud, then route a method mesh/Gaussian through the same renderer and repeat this visual/mask/camera audit.
```
