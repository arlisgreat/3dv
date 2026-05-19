# ri3d_first2_fghead_unmasked_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
G12 mask-loss ablation for the head/upper-body mask_width_anchor crop.
Use the same first2_fghead_maskaware dataset but train with USE_MASK=0.
```

Run:

```bash
GPU=0 USE_MASK=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fghead_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_fghead_unmasked_iter500.csv
experiments/figures/ri3d_first2_fghead_unmasked_iter500_inputs.png
experiments/figures/ri3d_first2_fghead_unmasked_iter500_renders.png
experiments/reconstructions/ri3d_first2_fghead_unmasked_iter500/
```

Summary:

| sample | views | roles | final loss | rgb mp4 |
| --- | ---: | --- | ---: | --- |
| web_clean_frontal_03 | 4 | geometry_only:2, identity_supervision:2 | 0.0092128 | yes |
| web_clean_frontal_01 | 4 | identity_supervision:4 | 0.0163692 | yes |

Observations:

```text
All four MP4s validate as 120 frames at 160x160.
Removing USE_MASK does not materially improve the render sheet.
The result remains a rotated-card / fragmented foreground reconstruction.
This closes G12 as a negative result: foreground canonicalization and mask-loss
ablation improve the input presentation but do not solve the 3D failure mode.
```

Next iteration:

```text
Stop expanding RI3D pseudo-view variants at first2. Move to G13: inject a
structural geometry prior, starting with LAM/FLAME/full-head depth or silhouette
anchors, before any first10/first30 scale-up.
```
