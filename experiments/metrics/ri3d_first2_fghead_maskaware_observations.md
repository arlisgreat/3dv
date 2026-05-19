# ri3d_first2_fghead_maskaware_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
G12 head/upper-body foreground canonicalization branch.
Use foreground_crop_mode=mask_width_anchor with width_scale=1.8,
height_fraction=0.55, y_anchor=0.45, then train with USE_MASK=1.
```

Run:

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_fghead_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --foreground-crop --foreground-crop-mode mask_width_anchor --foreground-width-scale 1.8 --foreground-height-fraction 0.55 --foreground-y-anchor 0.45 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fghead_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

Published artifacts:

```text
experiments/ri3d_datasets/first2_fghead_maskaware/
experiments/metrics/ri3d_first2_fghead_maskaware_iter500.csv
experiments/figures/ri3d_first2_fghead_maskaware_iter500_inputs.png
experiments/figures/ri3d_first2_fghead_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_fghead_maskaware_iter500/
```

Summary:

| sample | views | roles | final loss | rgb mp4 |
| --- | ---: | --- | ---: | --- |
| web_clean_frontal_03 | 4 | geometry_only:2, identity_supervision:2 | 0.0091152 | yes |
| web_clean_frontal_01 | 4 | identity_supervision:4 | 0.0165959 | yes |

Observations:

```text
All four MP4s validate as 120 frames at 160x160.
The input sheet is visibly better scaled than G11/G12 largest_square: foreground
subjects occupy more of the RI3D frame and small disconnected fragments are removed.
The render sheet still shows rotated photo-card-like planes and detached chunks.
web_clean_frontal_01 regresses by loss relative to G8 cutout75_budget4_masked
and G10 roleweighted, though the objective is changed and not directly comparable.
Conclusion: head/upper-body canonicalization plus mask-aware loss still does not
solve the downstream geometry failure.
```

Next iteration:

```text
Run the same fghead data with USE_MASK=0. If that also fails, end G12 and move
to LAM/FLAME/full-head geometry priors.
```
