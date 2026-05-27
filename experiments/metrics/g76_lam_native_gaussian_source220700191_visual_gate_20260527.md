# G76 NeRSemble Method Visual Gate

Date: 2026-05-27

Premise:

```text
Audit G74/G75 frontal-source native LAM Gaussian true-KRT predictions before any method-quality interpretation.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_NATIVE_GAUSSIAN_RENDERER_WITH_LIMITATIONS
```

Mask audit:

| serial | pred coverage | target coverage | pred/target IoU | touches border | decision |
| --- | ---: | ---: | ---: | --- | --- |
| 222200042 | 0.270110 | 0.670186 | 0.326161 | True | partial_or_cropped_prediction |
| 222200041 | 0.382873 | 0.601149 | 0.571201 | True | partial_or_cropped_prediction |
| 222200047 | 0.561120 | 0.594193 | 0.479368 | True | partial_or_cropped_prediction |

Mean summary:

| field | value |
| --- | ---: |
| mean_prediction_target_mask_iou | 0.458910 |
| mean_prediction_coverage | 0.404701 |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g76_lam_native_gaussian_source220700191_mask_audit_20260527.png
```

Private visual sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Manual/VLM audit note:

```text
Private sheet shows the frontal source render is plausible and two held-out views preserve recognizable identity/appearance, but the side held-out camera 222200042 is cropped toward the image border. This improves source clarity but does not eliminate camera-alignment risk.
```

Decision:

```text
G74 confirms the native Gaussian renderer/evaluator path works from a second real source camera, strengthening the overall method-direction evidence. It still does not pass the final quality gate because at least one held-out view is cropped/off-center.
```

Next gate:

```text
G77 must solve source-only pose/scale/crop alignment or move to a method that natively conditions on NeRSemble cameras; do not scale to a main table until visual gate passes across held-out views.
```
