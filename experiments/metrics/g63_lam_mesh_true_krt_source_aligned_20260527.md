# G63 LAM Mesh Source-Aligned True-KRT Render

Date: 2026-05-27

Premise:

```text
Align LAM textured mesh output to the G54 NeRSemble source view using only source camera intrinsics/extrinsics and source alpha mask, then render that fixed mesh into held-out cameras with true K/R/T. This avoids held-out and GT pointcloud alignment but remains diagnostic if appearance is broken.
```

Verdict:

```text
PASS_LAM_MESH_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC
```

Alignment:

| field | value |
| --- | --- |
| alignment | source_mask_coordinate_descent_similarity_no_rotation |
| uses_gt_geometry_for_alignment | False |
| uses_heldout_views_for_alignment | False |
| source_serial | 222200042 |
| source_mask_iou | 0.9288919925887952 |
| scale | 1.3900000000000003 |
| translation | [-0.07499999552965164, -0.08999999612569809, 0.0] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6655111719895}, {'scale': 1.12, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6969831734658326}, {'scale': 1.2400000000000002, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7134904091282148}, {'scale': 1.3600000000000003, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7263033325139586}, {'scale': 1.4800000000000004, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7469855957661039}, {'scale': 1.6000000000000005, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7644448210556919}, {'scale': 1.7200000000000006, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7709620494735444}, {'scale': 1.7800000000000007, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.7715600795063389}, {'scale': 1.7800000000000007, 'translation': [0.0, -0.05999999865889549, 0.0], 'source_mask_iou': 0.7720491414121045}, {'scale': 1.7200000000000006, 'translation': [0.0, -0.05999999865889549, 0.0], 'source_mask_iou': 0.7726255210357602}, {'scale': 1.6600000000000006, 'translation': [0.0, -0.05999999865889549, 0.0], 'source_mask_iou': 0.7755287699445775}, {'scale': 1.6000000000000005, 'translation': [0.0, -0.05999999865889549, 0.0], 'source_mask_iou': 0.7770666193158888}, {'scale': 1.5400000000000005, 'translation': [0.0, -0.05999999865889549, 0.0], 'source_mask_iou': 0.7776039604549879}, {'scale': 1.5400000000000005, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.8476483943275652}, {'scale': 1.4800000000000004, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.8659431995715847}, {'scale': 1.4200000000000004, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.8830557523233281}, {'scale': 1.3600000000000003, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.895367885749892}, {'scale': 1.3000000000000003, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.8957414881098115}, {'scale': 1.3300000000000003, 'translation': [-0.05999999865889549, -0.05999999865889549, 0.0], 'source_mask_iou': 0.8967786957242034}, {'scale': 1.3300000000000003, 'translation': [-0.05999999865889549, -0.08999999612569809, 0.0], 'source_mask_iou': 0.8994959549670715}, {'scale': 1.3600000000000003, 'translation': [-0.05999999865889549, -0.08999999612569809, 0.0], 'source_mask_iou': 0.9089120884665655}, {'scale': 1.3900000000000003, 'translation': [-0.05999999865889549, -0.08999999612569809, 0.0], 'source_mask_iou': 0.913615612938404}, {'scale': 1.3900000000000003, 'translation': [-0.08999999612569809, -0.08999999612569809, 0.0], 'source_mask_iou': 0.9201889654907534}, {'scale': 1.3900000000000003, 'translation': [-0.07499999552965164, -0.08999999612569809, 0.0], 'source_mask_iou': 0.9288919925887952}] |

Render summary:

| serial | role | projected points | coverage | output |
| --- | --- | ---: | ---: | --- |
| 222200042 | source_render | 244485 | 0.680134 | /data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 202129 | 0.497442 | /data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 189658 | 0.415471 | /data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 204107 | 0.427952 | /data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g63_lam_mesh_true_krt_source_aligned/g63_private_lam_mesh_source_aligned_sheet.png
```

Decision:

```text
Source-mask-only alignment produced nonempty true-KRT LAM mesh renders. Interpretation still depends on visual/evaluator gates.
```

Next gate:

```text
Run the held-out evaluator and visual gate. If appearance remains broken, switch to a method with native camera-aligned output or implement a better source-derived pose/scale solver.
```
