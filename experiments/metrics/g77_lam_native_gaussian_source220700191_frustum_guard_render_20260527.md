# G77 LAM Native Gaussian Source-Aligned True-KRT Render

Date: 2026-05-27

Premise:

```text
Use LAM's native diff-gaussian rasterizer to render the LAM head-anchored Gaussian PLY into the G54 NeRSemble source and held-out K/R/T cameras after source-mask alignment plus an eval-camera-frustum crop guard. The crop guard uses held-out K/R/T metadata only, not held-out RGB/mask or GT pointcloud.
```

Verdict:

```text
PASS_LAM_NATIVE_GAUSSIAN_TRUE_KRT_SOURCE_MASK_ALIGNED_DIAGNOSTIC
```

Alignment:

| field | value |
| --- | --- |
| alignment | source_mask_coordinate_descent_similarity_no_rotation_with_eval_camera_frustum_guard |
| alignment_mode | source_mask_eval_frustum_guard |
| prealign | {'prealign': 'none'} |
| uses_gt_geometry_for_alignment | False |
| uses_heldout_views_for_alignment | False |
| uses_heldout_rgb_or_mask_for_alignment | False |
| uses_heldout_camera_geometry_for_frustum_guard | True |
| frustum_guard | {'guard': 'eval_camera_frustum_only_no_eval_rgb_or_mask', 'seed': 60527, 'subsample': 20018, 'margin_fraction': 0.03, 'final_score': 1.5071755841038559, 'final_source_mask_iou': 0.8894323270504504, 'mean_eval_inframe_fraction': 0.9925733506510808, 'min_eval_inframe_fraction': 0.9884603856529124, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.17737885246775562, 'per_eval_camera': [{'serial': '222200042', 'valid_z_fraction': 1.0, 'inframe_fraction': 0.9884603856529124, 'overflow_penalty': 0.0, 'center_penalty': 0.1902708160047546, 'u_quantiles': [169.52908630371093, 352.7256774902344, 852.0312408447262], 'v_quantiles': [569.2224395751953, 895.2548828125, 1363.492883300781]}, {'serial': '222200041', 'valid_z_fraction': 1.0, 'inframe_fraction': 0.9935058447397342, 'overflow_penalty': 0.0, 'center_penalty': 0.10509660041513313, 'u_quantiles': [263.5289367675781, 535.9902648925781, 880.9330810546874], 'v_quantiles': [428.3539810180664, 634.027587890625, 1171.3620788574194]}, {'serial': '222200047', 'valid_z_fraction': 1.0, 'inframe_fraction': 0.9957538215605954, 'overflow_penalty': 0.0, 'center_penalty': 0.2367691409833791, 'u_quantiles': [345.7308151245117, 777.6443481445312, 979.803042602539], 'v_quantiles': [529.5723876953125, 834.6582946777344, 1284.5393737792965]}]} |
| source_serial | 220700191 |
| source_mask_iou | 0.8894323270504504 |
| scale | 1.1649999999999994 |
| translation | [0.029999999329447746, -0.014999999664723873, 0.10499998927116394] |
| trace | [{'scale': 1.0, 'translation': [0.0, 0.0, 0.0], 'score': 1.1867642560544225, 'source_mask_iou': 0.5529599774777573, 'mean_eval_inframe_fraction': 0.9987011689479468, 'min_eval_inframe_fraction': 0.9982515735837746, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.10174374777777236}, {'scale': 1.24, 'translation': [0.0, 0.0, 0.0], 'score': 1.2641298760664383, 'source_mask_iou': 0.6433956547984657, 'mean_eval_inframe_fraction': 0.985229959702934, 'min_eval_inframe_fraction': 0.9663303027275452, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.10590214095904445}, {'scale': 1.48, 'translation': [0.0, 0.0, 0.0], 'score': 1.268082029585517, 'source_mask_iou': 0.6871766891731304, 'mean_eval_inframe_fraction': 0.9631498318180305, 'min_eval_inframe_fraction': 0.915825756818863, 'mean_eval_overflow_penalty': 0.023737606164180844, 'mean_eval_center_penalty': 0.1112476689210331}, {'scale': 1.3599999999999999, 'translation': [0.0, 0.0, 0.11999999731779099], 'score': 1.302703733396225, 'source_mask_iou': 0.7198733033692828, 'mean_eval_inframe_fraction': 0.9730076264695108, 'min_eval_inframe_fraction': 0.9450994105305225, 'mean_eval_overflow_penalty': 0.008305898030598958, 'mean_eval_center_penalty': 0.24932110377308603}, {'scale': 1.2399999999999998, 'translation': [0.0, 0.0, 0.11999999731779099], 'score': 1.3169538817360291, 'source_mask_iou': 0.7154409161540136, 'mean_eval_inframe_fraction': 0.9863123189129782, 'min_eval_inframe_fraction': 0.9737236487161555, 'mean_eval_overflow_penalty': 0.000697334058357007, 'mean_eval_center_penalty': 0.24342960283580226}, {'scale': 1.2399999999999998, 'translation': [0.05999999865889549, 0.0, 0.11999999731779099], 'score': 1.325546842558464, 'source_mask_iou': 0.7538572789878825, 'mean_eval_inframe_fraction': 0.9669963699337263, 'min_eval_inframe_fraction': 0.9279648316515137, 'mean_eval_overflow_penalty': 0.01488746966737691, 'mean_eval_center_penalty': 0.2476119566399756}, {'scale': 1.1799999999999997, 'translation': [0.05999999865889549, 0.0, 0.11999999731779099], 'score': 1.3351531586339815, 'source_mask_iou': 0.7528565046061185, 'mean_eval_inframe_fraction': 0.9746394911246545, 'min_eval_inframe_fraction': 0.945648915975622, 'mean_eval_overflow_penalty': 0.010820778586647713, 'mean_eval_center_penalty': 0.24509518202691805}, {'scale': 1.1199999999999997, 'translation': [0.05999999865889549, 0.0, 0.11999999731779099], 'score': 1.3353124607816969, 'source_mask_iou': 0.7419519234209344, 'mean_eval_inframe_fraction': 0.9825656908782096, 'min_eval_inframe_fraction': 0.9650314716754921, 'mean_eval_overflow_penalty': 0.006769514604048212, 'mean_eval_center_penalty': 0.24256470790861015}, {'scale': 1.1199999999999997, 'translation': [0.029999999329447746, 0.0, 0.11999999731779099], 'score': 1.4636873838651367, 'source_mask_iou': 0.8495494743093641, 'mean_eval_inframe_fraction': 0.9945549005894695, 'min_eval_inframe_fraction': 0.9922569687281446, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.21242126303411688}, {'scale': 1.1199999999999997, 'translation': [0.029999999329447746, 0.0, 0.14999999105930328], 'score': 1.4738645708778972, 'source_mask_iou': 0.8727520131006168, 'mean_eval_inframe_fraction': 0.987378026442868, 'min_eval_inframe_fraction': 0.9746228394444999, 'mean_eval_overflow_penalty': 0.00047544722123579503, 'mean_eval_center_penalty': 0.2516784282261432}, {'scale': 1.1199999999999997, 'translation': [0.029999999329447746, -0.014999999664723873, 0.14999999105930328], 'score': 1.477238206831364, 'source_mask_iou': 0.8743237644424519, 'mean_eval_inframe_fraction': 0.9858960269091152, 'min_eval_inframe_fraction': 0.97197522229993, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.23422542786783782}, {'scale': 1.1349999999999996, 'translation': [0.029999999329447746, -0.014999999664723873, 0.13499999046325684], 'score': 1.494665347420611, 'source_mask_iou': 0.8844592591077801, 'mean_eval_inframe_fraction': 0.9902254637492923, 'min_eval_inframe_fraction': 0.9834149265660905, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.21385570458379233}, {'scale': 1.1499999999999995, 'translation': [0.029999999329447746, -0.014999999664723873, 0.11999998986721039], 'score': 1.5023404400181486, 'source_mask_iou': 0.8880435505574287, 'mean_eval_inframe_fraction': 0.9916908116028907, 'min_eval_inframe_fraction': 0.9867619142771505, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.19544239077340678}, {'scale': 1.1649999999999994, 'translation': [0.029999999329447746, -0.014999999664723873, 0.10499998927116394], 'score': 1.5071755841038559, 'source_mask_iou': 0.8894323270504504, 'mean_eval_inframe_fraction': 0.9925733506510808, 'min_eval_inframe_fraction': 0.9884603856529124, 'mean_eval_overflow_penalty': 0.0, 'mean_eval_center_penalty': 0.17737885246775562}] |
| render_max_size | 768 |
| native_rasterizer | diff_gaussian_rasterization |

Render summary:

| serial | role | coverage | output |
| --- | --- | ---: | --- |
| 220700191 | source_render | 0.683063 | /data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200042 | heldout_prediction | 0.722370 | /data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/all_rendered_frames/cam_222200042_frame_00000.png |
| 222200041 | heldout_prediction | 0.652030 | /data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 0.635360 | /data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g77_lam_native_gaussian_source220700191_frustum_guard/g69_private_lam_native_gaussian_source_aligned_sheet.png
```

Decision:

```text
Native Gaussian rasterization produced nonempty true-KRT renders after the source-mask plus camera-frustum guard. It still needs held-out evaluator and visual gates before a method claim.
```

Next gate:

```text
Run the G55 held-out evaluator and a strict visual/mask gate on the frustum-guard predictions.
```
