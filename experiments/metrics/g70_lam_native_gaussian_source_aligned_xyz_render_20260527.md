# G70 LAM Native Gaussian Source-Aligned True-KRT Render

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
| uses_gt_geometry_for_alignment | False |
| uses_heldout_views_for_alignment | False |
| source_serial | 222200042 |
| source_mask_iou | 0.9035881071108247 |
| scale | 1.5475000000000008 |
| translation | [-0.07499999552965164, -0.11999999731779099, 0.0] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6418880023119538}, {'scale': 1.12, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6700692258620548}, {'scale': 1.2400000000000002, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6792663224299201}, {'scale': 1.3600000000000003, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.682194851184621}, {'scale': 1.4800000000000004, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6990210417682363}, {'scale': 1.6000000000000005, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7211057026761751}, {'scale': 1.7200000000000006, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7340470819920366}, {'scale': 1.7200000000000006, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7762697379768868}, {'scale': 1.7200000000000006, 'translation': [-0.11999999731779099, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8051566740338798}, {'scale': 1.6000000000000005, 'translation': [-0.11999999731779099, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8422833265639647}, {'scale': 1.5400000000000005, 'translation': [-0.11999999731779099, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8522321644644499}, {'scale': 1.5400000000000005, 'translation': [-0.05999999865889549, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8903246579277799}, {'scale': 1.6000000000000005, 'translation': [-0.05999999865889549, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8919800796812749}, {'scale': 1.5700000000000005, 'translation': [-0.05999999865889549, -0.11999999731779099, 0.0], 'source_mask_iou': 0.8934128006114185}, {'scale': 1.5700000000000005, 'translation': [-0.07499999552965164, -0.11999999731779099, 0.0], 'source_mask_iou': 0.9007859912222637}, {'scale': 1.5550000000000006, 'translation': [-0.07499999552965164, -0.11999999731779099, 0.0], 'source_mask_iou': 0.9021424472409497}, {'scale': 1.5400000000000007, 'translation': [-0.07499999552965164, -0.11999999731779099, 0.0], 'source_mask_iou': 0.9029425216281788}, {'scale': 1.5475000000000008, 'translation': [-0.07499999552965164, -0.11999999731779099, 0.0], 'source_mask_iou': 0.9035881071108247}] |
| render_max_size | 768 |
| native_rasterizer | diff_gaussian_rasterization |

Render summary:

| serial | role | coverage | output |
| --- | --- | ---: | --- |
| 222200042 | source_render | 0.728855 | /data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 0.580830 | /data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 0.470939 | /data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 0.494100 | /data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g70_lam_native_gaussian_true_krt_source_aligned_xyz/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Decision:

```text
Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim.
```

Next gate:

```text
Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions.
```
