# G17c RI3D Positive-Control Iter500 Visual Gate

Date: 2026-05-20

Gate verdict:

```text
PASS_EXECUTION_AND_EXPORT
FAIL_RECONSTRUCTION_QUALITY
POSITIVE_CONTROL_ONLY
```

Premise:

```text
The G16b/G17a CC0 mesh-derived positive-control case has known cameras, masks,
depth proxies, and 8 coherent rendered views. A longer RI3D run should preserve
a single coherent head orbit if the current reconstruction path is strong enough
for this sprint.
```

Inputs:

```text
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/figures/ri3d_gt_positive_control_iter500_inputs.png
experiments/figures/ri3d_gt_positive_control_iter500_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter500/
```

Visual audit:

```text
The input sheet is coherent: front, side, rear, and oblique head views form a
plausible orbit. The iter500 render sheet still shows ghosted side heads and a
multi-fragment central support rather than one stable head. The output therefore
does not pass reconstruction-quality criteria, even though the run executed and
exported valid MP4 files.
```

MP4 validation:

```text
rgb: 120 frames, 256x256
depth: 120 frames, 256x256
```

Decision:

```text
Stop scaling this RI3D positive-control route in the current sprint unless a
new geometry/initialization strategy is added. Use this as evidence that the
data/provenance/export pipeline works, but the current RI3D reconstruction path
is not a quality solution.
```
