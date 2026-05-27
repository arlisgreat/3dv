# G59 NeRSemble True-KRT Pointcloud Renderer Positive Control

Date: 2026-05-27

Premise:

```text
Render the official NeRSemble frame-0 GT pointcloud through the exact G54 visible-camera K/R/T. This is an oracle renderer positive control for camera/evaluator plumbing, not a learned-prior method result.
```

Verdict:

```text
PASS_NERSEMBLE_TRUE_KRT_POINTCLOUD_RENDERER_POSITIVE_CONTROL
```

Render summary:

| serial | role | projected points | coverage | output |
| --- | --- | ---: | ---: | --- |
| 222200042 | source_render | 663330 | 0.330359 | /data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/all_rendered_frames/cam_222200042_frame_00000.png |
| 220700191 | heldout_prediction | 673703 | 0.380953 | /data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/all_rendered_frames/cam_220700191_frame_00000.png |
| 222200041 | heldout_prediction | 673854 | 0.326258 | /data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/all_rendered_frames/cam_222200041_frame_00000.png |
| 222200047 | heldout_prediction | 673598 | 0.327921 | /data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/all_rendered_frames/cam_222200047_frame_00000.png |

Private contact sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g59_nersemble_pointcloud_true_krt_renderer/g59_private_pointcloud_true_krt_sheet.png
```

Decision:

```text
The true K/R/T pointcloud renderer produced nonempty source/eval renders and can be used as the camera-contract positive control.
```

Next gate:

```text
Run the G55 evaluator on these pointcloud renders as an oracle local-visible held-out baseline, then connect method mesh/Gaussian output to this same camera contract without using GT geometry for method alignment unless explicitly labeled diagnostic.
```
