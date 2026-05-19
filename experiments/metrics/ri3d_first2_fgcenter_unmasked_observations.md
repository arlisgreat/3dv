# ri3d_first2_fgcenter_unmasked_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
G12 mask-loss ablation for largest-square foreground canonicalization.
Use the same first2_fgcenter_maskaware dataset, but train with USE_MASK=0 so
foreground canonical RGB is supervised as a full gray-background image.
```

Run:

```bash
GPU=0 USE_MASK=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_fgcenter_unmasked_iter500.csv
experiments/figures/ri3d_first2_fgcenter_unmasked_iter500_inputs.png
experiments/figures/ri3d_first2_fgcenter_unmasked_iter500_renders.png
experiments/reconstructions/ri3d_first2_fgcenter_unmasked_iter500/
```

Summary:

| sample | views | roles | final loss | rgb mp4 |
| --- | ---: | --- | ---: | --- |
| web_clean_frontal_03 | 4 | geometry_only:2, identity_supervision:2 | 0.0092889 | yes |
| web_clean_frontal_01 | 4 | identity_supervision:4 | 0.0157918 | yes |

Observations:

```text
All four MP4s validate as 120 frames at 160x160.
Removing USE_MASK does not remove the card/fragment render failure.
The output is visually almost identical to the USE_MASK=1 branch.
Conclusion: G12 failure is not caused only by masked RGB/SSIM or silhouette
loss. The RI3D setup still lacks a structural head/full-body geometry prior.
```

Next iteration:

```text
Test the more aggressive mask_width_anchor crop, then stop G12 if visual quality
still does not improve.
```
