# G74 LAM Native Gaussian Source-Aligned True-KRT Render

Date: 2026-05-27

Premise:

```text
Use LAM's native diff-gaussian rasterizer to render the LAM head-anchored Gaussian PLY into the G54 NeRSemble source and held-out K/R/T cameras after source-mask-only alignment.
```

Verdict:

```text
PASS_LAM_NATIVE_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC
```

Alignment:

| field | value |
| --- | --- |
| alignment | source_mask_coordinate_descent_similarity_no_rotation |
| alignment_mode | source_mask_only |
| prealign | {'prealign': 'none'} |
| uses_gt_geometry_for_alignment | False |
| uses_heldout_views_for_alignment | False |
| source_serial | 220700191 |
| source_mask_iou | 0.8974266973050599 |
| scale | 1.5700000000000005 |
| translation | [0.0, -0.11999999731779099, -0.23249998688697815] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5529599774777573}, {'scale': 1.12, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6056824840759274}, {'scale': 1.2400000000000002, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6433956547984657}, {'scale': 1.3600000000000003, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.674225952699932}, {'scale': 1.4800000000000004, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6871766891731304}, {'scale': 1.4800000000000004, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7344923243199968}, {'scale': 1.6000000000000005, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7526590312254552}, {'scale': 1.7200000000000006, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7580894169679628}, {'scale': 1.7200000000000006, 'translation': [0.0, -0.11999999731779099, -0.11999999731779099], 'source_mask_iou': 0.8132665431645889}, {'scale': 1.6000000000000005, 'translation': [0.0, -0.11999999731779099, -0.11999999731779099], 'source_mask_iou': 0.8314784873109805}, {'scale': 1.6000000000000005, 'translation': [0.0, -0.11999999731779099, -0.23999999463558197], 'source_mask_iou': 0.8947265456090371}, {'scale': 1.5700000000000005, 'translation': [0.0, -0.11999999731779099, -0.23999999463558197], 'source_mask_iou': 0.895607052853907}, {'scale': 1.5700000000000005, 'translation': [0.0, -0.11999999731779099, -0.22499999403953552], 'source_mask_iou': 0.8957939812464033}, {'scale': 1.5700000000000005, 'translation': [0.0, -0.11999999731779099, -0.23249998688697815], 'source_mask_iou': 0.8974266973050599}] |
| render_max_size | 768 |
| native_rasterizer | diff_gaussian_rasterization |

Render summary:

| serial | role | coverage | output |
| --- | --- | ---: | --- |
| 220700191 | source_render | 0.679917 | /data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200042 | heldout_prediction | 0.270685 | /data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/all_rendered_frames/cam_222200042_frame_00000.png |
| 222200041 | heldout_prediction | 0.383079 | /data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 0.561027 | /data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g74_lam_native_gaussian_source220700191_true_krt/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Decision:

```text
Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim.
```

Next gate:

```text
Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions.
```
