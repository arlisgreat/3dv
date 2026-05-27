# G73 NeRSemble Method Visual Gate

Date: 2026-05-27

Premise:

```text
Audit the G70/G71 native LAM Gaussian true-KRT held-out predictions before any method-quality interpretation. The gate checks repo-safe mask alignment, private visual appearance, renderer contract, and crop risk.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_NATIVE_GAUSSIAN_RENDERER_WITH_LIMITATIONS
```

Mask audit:

| serial | pred coverage | target coverage | pred/target IoU | touches border | decision |
| --- | ---: | ---: | ---: | --- | --- |
| 220700191 | 0.580943 | 0.645397 | 0.586129 | True | partial_or_cropped_prediction |
| 222200041 | 0.470986 | 0.601149 | 0.482606 | True | partial_or_cropped_prediction |
| 222200047 | 0.494230 | 0.594193 | 0.425278 | True | partial_or_cropped_prediction |

Mean summary:

| field | value |
| --- | ---: |
| mean_prediction_target_mask_iou | 0.498004 |
| mean_prediction_coverage | 0.515386 |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g73_lam_native_gaussian_source_aligned_mask_audit_20260527.png
```

Private visual sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Manual/VLM audit note:

```text
Private sheet shows the source render is a plausible side-view head and held-out renders preserve recognizable identity/appearance better than mesh or point approximations. However, held-out views are still partially cropped or shifted, especially the frontal/upward cameras, so this is not yet a reconstruction-quality result.
```

Decision:

```text
The learned-prior/head-anchored Gaussian renderer path is now technically working: a LAM Gaussian output is rendered through official NeRSemble K/R/T into G55 evaluator without GT pointcloud or held-out alignment. The current run only partially validates the overall direction because held-out crop/alignment errors block a main quality claim.
```

Next gate:

```text
Keep G70/G71/G73 as the current best diagnostic positive. Next, either improve source-only pose/scale alignment without held-out leakage or switch to a method with native NeRSemble-camera-conditioned output; then repeat G54/G55/G73 on more cases.
```
