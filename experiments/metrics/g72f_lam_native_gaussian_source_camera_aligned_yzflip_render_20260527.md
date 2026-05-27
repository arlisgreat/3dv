# G72F LAM Native Gaussian Source-Aligned True-KRT Render

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
| alignment_mode | source_camera_then_mask |
| prealign | {'prealign': 'source_camera_c2w_to_c2w', 'lam_transform_json': '/data1/workspace/airulan/3dv/external/LAM/tracking_output/export/cam_222200042_frame_00000/transforms.json', 'lam_yz_flip': True, 'lam_c2w': [[1.0, -0.0, -0.0, 0.02826753258705139], [0.0, -1.0, -0.0, 0.014753027819097042], [0.0, -0.0, -1.0, 0.8508920669555664], [0.0, 0.0, 0.0, 1.0]], 'nersemble_source_c2w': [[0.6907656788825989, 0.18140476942062378, -0.6999537348747253, 0.7809341549873352], [-0.024437515065073967, -0.9616088271141052, -0.2733337879180908, 0.30164316296577454], [-0.7226657271385193, 0.20591473579406738, -0.6598132252693176, 0.7618785500526428], [0.0, 0.0, 0.0, 1.0]], 'prealign_transform': [[0.6907656788825989, -0.18140476942062378, 0.6999537348747253, 0.16849911212921143], [-0.024437515065073967, 0.9616088271141052, 0.2733337879180908, 0.05556975305080414], [-0.7226657271385193, -0.20591473579406738, 0.6598132252693176, 0.22391456365585327], [0.0, 0.0, 0.0, 1.0]]} |
| uses_gt_geometry_for_alignment | False |
| uses_heldout_views_for_alignment | False |
| source_serial | 222200042 |
| source_mask_iou | 0.8545511203244825 |
| scale | 0.9249999999999999 |
| translation | [0.05249999836087227, 0.0, -0.022499999031424522] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.6042148254438646}, {'scale': 0.88, 'translation': [0.0, 0.0, 0.0], 'source_mask_iou': 0.619289748807992}, {'scale': 0.88, 'translation': [0.11999999731779099, 0.0, 0.0], 'source_mask_iou': 0.6712047813367314}, {'scale': 1.0, 'translation': [0.11999999731779099, 0.0, 0.0], 'source_mask_iou': 0.7023197302793671}, {'scale': 1.12, 'translation': [0.11999999731779099, 0.0, 0.0], 'source_mask_iou': 0.7111328847398956}, {'scale': 1.06, 'translation': [0.11999999731779099, 0.0, 0.0], 'source_mask_iou': 0.7133636366450303}, {'scale': 1.06, 'translation': [0.05999999865889549, 0.0, 0.0], 'source_mask_iou': 0.7941150253889996}, {'scale': 1.0, 'translation': [0.05999999865889549, 0.0, 0.0], 'source_mask_iou': 0.8333412952815902}, {'scale': 0.94, 'translation': [0.05999999865889549, 0.0, 0.0], 'source_mask_iou': 0.8393499985957168}, {'scale': 0.97, 'translation': [0.05999999865889549, 0.0, 0.0], 'source_mask_iou': 0.8411271261442362}, {'scale': 0.955, 'translation': [0.05999999865889549, 0.0, 0.0], 'source_mask_iou': 0.8424555138230404}, {'scale': 0.955, 'translation': [0.05999999865889549, 0.0, -0.014999999664723873], 'source_mask_iou': 0.845719406724433}, {'scale': 0.94, 'translation': [0.05999999865889549, 0.0, -0.014999999664723873], 'source_mask_iou': 0.8491290907469607}, {'scale': 0.9249999999999999, 'translation': [0.05999999865889549, 0.0, -0.014999999664723873], 'source_mask_iou': 0.8495199525944864}, {'scale': 0.9249999999999999, 'translation': [0.05249999836087227, 0.0, -0.014999999664723873], 'source_mask_iou': 0.8543899611289223}, {'scale': 0.9249999999999999, 'translation': [0.05249999836087227, 0.0, -0.022499999031424522], 'source_mask_iou': 0.8545511203244825}] |
| render_max_size | 768 |
| native_rasterizer | diff_gaussian_rasterization |

Render summary:

| serial | role | coverage | output |
| --- | --- | ---: | --- |
| 222200042 | source_render | 0.674173 | /data1/workspace/airulan/3dv_work/runs/g72f_lam_native_gaussian_true_krt_source_camera_aligned_yzflip/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 0.308006 | /data1/workspace/airulan/3dv_work/runs/g72f_lam_native_gaussian_true_krt_source_camera_aligned_yzflip/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 0.263555 | /data1/workspace/airulan/3dv_work/runs/g72f_lam_native_gaussian_true_krt_source_camera_aligned_yzflip/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 0.072924 | /data1/workspace/airulan/3dv_work/runs/g72f_lam_native_gaussian_true_krt_source_camera_aligned_yzflip/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g72f_lam_native_gaussian_true_krt_source_camera_aligned_yzflip/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Decision:

```text
Native Gaussian rasterization produced nonempty source-only aligned true-KRT renders. It still needs held-out evaluator and visual gates before a method claim.
```

Next gate:

```text
Run G55 held-out evaluator and visual/mask/appearance gate on the native Gaussian predictions.
```
