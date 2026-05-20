# ri3d_gt_positive_control_iter10 downstream observations

Date: 2026-05-20

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Run the first G17 positive-control RI3D smoke after G16b/G17a gates.
Validate that the CC0 mesh-derived head case can be converted, initialized,
trained for 10 iterations, rendered, and exported as compact MP4/PNG/CSV records.
```

Run:

```bash
GPU=0 USE_MASK=1 PCD_MASK_FILTER=1 ITERATIONS=10 DATA_ROOT=experiments/ri3d_datasets/gt_positive_control OUT_ROOT=experiments/downstream_3d/ri3d_gt_positive_control_iter10 VARIANTS_STR="mesh_rendered" SAMPLES_STR="wikimedia_blender_head_cc0" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=10 DATA_ROOT=experiments/ri3d_datasets/gt_positive_control RUN_ROOT=experiments/downstream_3d/ri3d_gt_positive_control_iter10 VARIANTS_STR="mesh_rendered" SAMPLES_STR="wikimedia_blender_head_cc0" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/gt_positive_control --run-root experiments/downstream_3d/ri3d_gt_positive_control_iter10 --export-root experiments/reconstructions/ri3d_gt_positive_control_iter10 --metrics-csv experiments/metrics/ri3d_gt_positive_control_iter10.csv --observations experiments/metrics/ri3d_gt_positive_control_iter10_observations.md --input-figure experiments/figures/ri3d_gt_positive_control_iter10_inputs.png --render-figure experiments/figures/ri3d_gt_positive_control_iter10_renders.png --iteration 10 --run-name ri3d_gt_positive_control_iter10 --variants mesh_rendered
```

Published artifacts:

```text
experiments/metrics/ri3d_gt_positive_control_iter10.csv
experiments/figures/ri3d_gt_positive_control_iter10_inputs.png
experiments/figures/ri3d_gt_positive_control_iter10_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter10/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| wikimedia_blender_head_cc0 | mesh_rendered | 8 | positive_control_gt:8 | 0.3389232 | 109888 | yes |

Observations:

```text
The CC0 mesh-derived positive-control case is end-to-end executable through RI3D.
This smoke used the gate-passed 8-view export, masks, and point-cloud mask filter.
wikimedia_blender_head_cc0: best training loss is mesh_rendered (0.3389232).
The render sheet is smoke-quality only and still shows multiple ghosted head
fragments after 10 iterations, so this is an execution/provenance pass, not a
reconstruction-quality pass.
Exported RGB/depth MP4s both validate as 120 frames at 256x256.
```

Next iteration:

```text
Run a longer positive-control reconstruction only after recording a new gate.
Compare against the source contact sheet and keep raw PLY/downstream working
directories ignored; publish only compact PNG/MP4/CSV/JSON/MD records.
Continue G16a real-capture access in parallel before making real-data claims.
```
