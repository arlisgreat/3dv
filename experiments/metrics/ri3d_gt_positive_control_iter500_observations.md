# ri3d_gt_positive_control_iter500 downstream observations

Date: 2026-05-20

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Run the G17c longer positive-control RI3D check after the G17c preflight gate.
Test whether extending the CC0 mesh-derived head case from 10 to 500 iterations
turns the smoke pass into a usable reconstruction-quality pass.
```

Run:

```bash
GPU=0 USE_MASK=1 PCD_MASK_FILTER=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/gt_positive_control OUT_ROOT=experiments/downstream_3d/ri3d_gt_positive_control_iter500 VARIANTS_STR="mesh_rendered" SAMPLES_STR="wikimedia_blender_head_cc0" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/gt_positive_control RUN_ROOT=experiments/downstream_3d/ri3d_gt_positive_control_iter500 VARIANTS_STR="mesh_rendered" SAMPLES_STR="wikimedia_blender_head_cc0" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/gt_positive_control --run-root experiments/downstream_3d/ri3d_gt_positive_control_iter500 --export-root experiments/reconstructions/ri3d_gt_positive_control_iter500 --metrics-csv experiments/metrics/ri3d_gt_positive_control_iter500.csv --observations experiments/metrics/ri3d_gt_positive_control_iter500_observations.md --input-figure experiments/figures/ri3d_gt_positive_control_iter500_inputs.png --render-figure experiments/figures/ri3d_gt_positive_control_iter500_renders.png --iteration 500 --run-name ri3d_gt_positive_control_iter500 --variants mesh_rendered
```

Published artifacts:

```text
experiments/metrics/ri3d_gt_positive_control_iter500.csv
experiments/figures/ri3d_gt_positive_control_iter500_inputs.png
experiments/figures/ri3d_gt_positive_control_iter500_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| wikimedia_blender_head_cc0 | mesh_rendered | 8 | positive_control_gt:8 | 0.3598759 | 109888 | yes |

Observations:

```text
The CC0 mesh-derived positive-control case remains end-to-end executable through RI3D.
This longer run used the same gate-passed 8-view export, masks, and point-cloud mask filter.
wikimedia_blender_head_cc0: best training loss is mesh_rendered (0.3598759).
The render sheet still shows ghosted multi-fragment head structure after 500 iterations.
Compared with the G16b source contact sheet, the output is not a coherent single head orbit.
Therefore G17c is an execution/provenance pass but a reconstruction-quality fail.
Exported RGB/depth MP4s both validate as 120 frames at 256x256.
```

Next iteration:

```text
Do not spend more milestone time scaling this RI3D positive-control route without
a stronger initialization/geometry strategy. Use G17c as evidence that the
current RI3D plumbing runs but remains visually weak even on a clean mesh-derived
positive-control case. Proceed to G18 failure taxonomy and G19 paper packaging.
```
