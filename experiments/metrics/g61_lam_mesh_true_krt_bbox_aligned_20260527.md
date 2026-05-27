# G61 LAM Mesh True-KRT Diagnostic Render

Date: 2026-05-27

Premise:

```text
Render the LAM-20K textured mesh output into the G54 NeRSemble cameras after an explicit GT pointcloud bbox similarity alignment. This tests the renderer path for method-shaped geometry but is diagnostic-only because GT geometry is used for alignment.
```

Verdict:

```text
PASS_DIAGNOSTIC_ONLY_LAM_MESH_TRUE_KRT_GT_BBOX_ALIGNED
```

Alignment:

| field | value |
| --- | --- |
| alignment | gt_pointcloud_bbox_similarity_no_rotation |
| uses_gt_geometry_for_alignment | True |
| source_bbox_min | [-0.19374975562095642, -0.26007580757141113, -0.1568860113620758] |
| source_bbox_max | [0.13082073628902435, 0.15755565464496613, 0.07697687298059464] |
| target_bbox_min | [-0.13689957559108734, -0.23069514334201813, -0.049469463527202606] |
| target_bbox_max | [0.16206927597522736, 0.1687164604663849, 0.17027217149734497] |
| scale | 0.9396174550056458 |
| translation_after_scale | [0.04214945435523987, 0.017175521701574326, 0.09794336557388306] |

Render summary:

| serial | role | projected points | coverage | output |
| --- | --- | ---: | ---: | --- |
| 222200042 | source_render | 268403 | 0.578959 | /data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 268730 | 0.521005 | /data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 269218 | 0.506629 | /data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 270018 | 0.464947 | /data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g61_lam_mesh_true_krt_bbox_aligned/g61_private_lam_mesh_true_krt_sheet.png
```

Decision:

```text
LAM mesh renders are nonempty under the true NeRSemble K/R/T path, but this remains diagnostic-only because GT pointcloud bbox alignment was used.
```

Next gate:

```text
Run the held-out evaluator on these diagnostic renders. A method-quality gate still requires a renderer alignment derived from the source image/camera or model output alone, not from GT pointcloud geometry.
```
