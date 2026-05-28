# G116 Naive Camera/Crop Audit

Date: 2026-05-28

Verdict:

```text
PASS_G116_NAIVE_CAMERA_CROP_AUDIT_DIAGNOSTIC
```

Key evidence:

| field | value |
| --- | ---: |
| direct_source_mask_iou | 0.889432 |
| naive_source_mask_iou | 0.323160 |
| direct_min_eval_inframe | 0.988460 |
| naive_min_eval_inframe | 0.482100 |
| direct_mean_eval_mask_iou | 0.900017 |
| naive_mean_eval_mask_iou | 0.309712 |

Per-eval masks:

| serial | target coverage | direct coverage | naive coverage | direct IoU | naive IoU | naive touches border |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 222200042 | 0.670186 | 0.722370 | 0.328742 | 0.886891 | 0.284254 | True |
| 222200041 | 0.601149 | 0.652058 | 0.320646 | 0.899205 | 0.266807 | True |
| 222200047 | 0.594193 | 0.635341 | 0.322816 | 0.913003 | 0.378074 | True |

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g116_naive_camera_crop_audit_20260528.png
```

Interpretation:

```text
The naive arm was rendered with the same NeRSemble eval cameras and an explicit eval-camera frustum guard. The frustum is not catastrophically empty (min in-frame 0.482), but source-mask alignment is poor (0.323) compared with direct (0.889). This supports source/crop/geometry collapse in the RI3D pseudo-geometry output as the primary failure, not a simple evaluator K/R/T wiring error. It still means naive is a weak baseline and should be reported with this caveat.
```
