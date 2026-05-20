# G16 Positive-Control Route Update

Date: 2026-05-20

Premise:

```text
Web first10 pseudo views are diagnostic-only. Before any new reconstruction
claim, the repo needs an auditable case with known cameras and GT geometry.
```

Real-capture route:

```text
G16a remains open. FaceScape, H3DS, Multiface, NeRSemble, and UEA are still the
scientifically stronger routes, but they require license/access checks before
raw or rendered face data can be published.
```

Positive-control route:

```text
G16b uses a CC0 human head mesh from Wikimedia Commons / Blender human base
meshes. Raw STL stays outside git. Derived RGB/depth/mask/normal PNGs, camera
JSON, manifest CSV, contact sheet, and orbit MP4 are repo-safe result records.
```

Selected case:

```text
case_id: wikimedia_blender_head_cc0
source: https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
license: CC0 1.0 Universal Public Domain Dedication
raw_stl: /data1/workspace/airulan/3dv_work/datasets/wikimedia_blender_head_cc0/Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
```

Generated artifacts:

```text
scripts/data/render_mesh_positive_control_case.py
experiments/gt_cases/wikimedia_blender_head_cc0/manifest.csv
experiments/gt_cases/wikimedia_blender_head_cc0/cameras.json
experiments/gt_cases/wikimedia_blender_head_cc0/views/*.png
experiments/gt_cases/wikimedia_blender_head_cc0/orbit_rgb.mp4
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.json
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.json
```

Visual/VLM gate:

```text
PASS_POSITIVE_CONTROL_ONLY
The contact sheet shows coherent front, side, rear, and oblique head views with
no split body/card/cropped-fragment artifacts. This pass does not promote web
first10 pseudo views to training data and does not prove real-capture identity
preservation.
```

Rejected immediate alternatives:

```text
NIH 3D Visible Human Male Bust and Visible Male Head were downloaded to
3dv_work only and visually checked. They are useful anatomy meshes, but their
available orientation/content is anatomical/cross-section style rather than a
clean face-head positive control, so they are not the active G16b case.
```

Next gate:

```text
G17 has passed the no-training camera/provenance sanity check for
wikimedia_blender_head_cc0. The next task is conversion into a reconstruction
input format and a tiny positive-control smoke run, still scoped to
POSITIVE_CONTROL_ONLY.
```
