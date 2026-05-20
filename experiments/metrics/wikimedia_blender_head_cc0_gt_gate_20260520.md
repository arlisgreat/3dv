# G16b Wikimedia Blender CC0 realistic human head Positive-Control Gate

Date: 2026-05-20

Gate verdict:

```text
PASS_POSITIVE_CONTROL_ONLY
PASS_RECONSTRUCTION_TRAINING_FOR_SYNTHETIC_RENDERED_GT_ONLY
BLOCKED_FOR_REAL_CAPTURE_RECONSTRUCTION_CLAIMS
```

Premise:

```text
Use a public GT mesh to render deterministic multi-view RGB/depth/mask/normal
views with known cameras. This validates data-gate and reconstruction plumbing
without claiming that web pseudo views or synthetic renders are real captured
multi-view training data.
```

Source:

```text
case_id: wikimedia_blender_head_cc0
title: Wikimedia Blender CC0 realistic human head
entry: https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
download_endpoint: https://upload.wikimedia.org/wikipedia/commons/8/84/Head_%28Sculpting%29_-_Realistic_by_Dan_Ulrich_%28CC0%29.stl
license: CC0 1.0 Universal Public Domain Dedication
local_raw_mesh: /data1/workspace/airulan/3dv_work/datasets/wikimedia_blender_head_cc0/Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
raw_mesh_sha256: 63cdcac1722ea6bf5d8f6758aafc7c8adee962d7b2e505c79f39eb4ea7e6c86b
repo_policy: raw mesh is not committed; only derived audit outputs are committed
```

Mesh audit:

```text
vertices: 845442
faces: 1690880
sampled_surface_points_for_render: 180000
rendering: deterministic orthographic sampled-surface z-buffer
```

Artifacts:

```text
experiments/gt_cases/wikimedia_blender_head_cc0/cameras.json
experiments/gt_cases/wikimedia_blender_head_cc0/manifest.csv
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/gt_cases/wikimedia_blender_head_cc0/orbit_rgb.mp4
experiments/gt_cases/wikimedia_blender_head_cc0/views/*.png
```

Manual/VLM visual audit:

```text
PASS_POSITIVE_CONTROL_ONLY after visual inspection of
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png.
The sheet shows coherent front, side, rear, and oblique head views with no split
body/card/cropped-fragment artifacts. Scope remains synthetic mesh-derived GT;
it does not validate real-capture identity preservation.
```

Limitations:

```text
This is a mesh-derived positive control, not a real multi-camera capture.
It cannot validate identity preservation on real portraits.
It can validate camera/provenance handling, derived GT views, masks, depth,
and whether downstream reconstruction code can consume auditable inputs.
```
