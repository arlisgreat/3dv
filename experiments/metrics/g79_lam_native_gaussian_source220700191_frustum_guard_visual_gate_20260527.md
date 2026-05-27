# G79 NeRSemble Method Visual Gate

Date: 2026-05-27

Premise:

```text
Audit G77/G78 frontal-source LAM native Gaussian true-KRT predictions after source-mask plus eval-camera-frustum crop guard alignment. This gate uses held-out masks only for post-hoc evaluation, not alignment.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_NATIVE_GAUSSIAN_RENDERER_WITH_LIMITATIONS
```

Mask audit:

| serial | pred coverage | target coverage | coverage ratio | pred/target IoU | touches border | decision |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 222200042 | 0.722149 | 0.670186 | 1.077534 | 0.887575 | True | nonblank_aligned_prediction |
| 222200041 | 0.651713 | 0.601149 | 1.084112 | 0.899471 | True | nonblank_aligned_prediction |
| 222200047 | 0.635064 | 0.594193 | 1.068783 | 0.913003 | True | nonblank_aligned_prediction |

Mean summary:

| field | value |
| --- | ---: |
| mean_prediction_target_mask_iou | 0.900017 |
| mean_prediction_coverage | 0.669642 |
| crop_risk_mode | mask_iou_coverage |
| min_mask_iou | 0.750000 |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g79_lam_native_gaussian_source220700191_frustum_guard_mask_audit_20260527.png
```

Private visual sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Manual/VLM audit note:

```text
Private sheet shows all three held-out predictions are nonblank and no longer suffer the severe side-view crop seen in G74/G76. Identity and glasses are preserved, poses follow the NeRSemble cameras, and mask overlap is high; remaining limitations are LAM Gaussian blur/smearing around hair, shoulder/background edges, and imperfect expression/illumination.
```

Decision:

```text
G77/G78/G79 are the current best method-direction positive: the learned-prior/head-anchored Gaussian renderer/evaluator path works under the real-GT gate and the previous gross crop failure is fixed without held-out RGB/mask or GT pointcloud alignment. It is still diagnostic rather than a final SOTA reconstruction claim because it uses in-domain LAM-20K and only one NeRSemble frame/case.
```

Next gate:

```text
Scale the same frozen protocol to additional NeRSemble cases/sources and compare against copy-source and prior G70/G75 diagnostics. Keep model/data-overlap and private-artifact restrictions in force.
```
