# G69 LAM Native Gaussian Source-Aligned True-KRT Render

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
| source_mask_iou | 0.7395705171298469 |
| scale | 3.130000000000002 |
| translation | [-0.007499999832361937, -0.13499999046325684, 0.0] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.2780239907218941}, {'scale': 1.12, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.3121430655374614}, {'scale': 1.2400000000000002, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.34811719539300867}, {'scale': 1.3600000000000003, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.3868269337641773}, {'scale': 1.4800000000000004, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.4205038575216673}, {'scale': 1.6000000000000005, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.45399759162137754}, {'scale': 1.7200000000000006, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.4754644853506216}, {'scale': 1.8400000000000007, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.49151943571217277}, {'scale': 1.9600000000000009, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5038299455760499}, {'scale': 2.080000000000001, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5124161285885812}, {'scale': 2.200000000000001, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5160383826532766}, {'scale': 2.320000000000001, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5207010801092343}, {'scale': 2.4400000000000013, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.5244149770391181}, {'scale': 2.4400000000000013, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.653942054887715}, {'scale': 2.5600000000000014, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.6747009042046443}, {'scale': 2.6800000000000015, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.6959010602410801}, {'scale': 2.8000000000000016, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7131180713776823}, {'scale': 2.9200000000000017, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7260954028914901}, {'scale': 3.040000000000002, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7274848851842436}, {'scale': 3.100000000000002, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7294780573618572}, {'scale': 3.115000000000002, 'translation': [0.0, -0.11999999731779099, 0.0], 'source_mask_iou': 0.7304787434640356}, {'scale': 3.115000000000002, 'translation': [0.0, -0.13499999046325684, 0.0], 'source_mask_iou': 0.7387950689616976}, {'scale': 3.130000000000002, 'translation': [0.0, -0.13499999046325684, 0.0], 'source_mask_iou': 0.7389798195296877}, {'scale': 3.130000000000002, 'translation': [-0.007499999832361937, -0.13499999046325684, 0.0], 'source_mask_iou': 0.7395705171298469}] |
| render_max_size | 768 |
| native_rasterizer | diff_gaussian_rasterization |

Render summary:

| serial | role | coverage | output |
| --- | --- | ---: | --- |
| 222200042 | source_render | 0.901220 | /data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 0.941891 | /data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 0.944717 | /data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 0.869636 | /data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g69_lam_native_gaussian_true_krt_source_aligned/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Decision:

```text
Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim.
```

Next gate:

```text
Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions.
```
