# ri3d_first2_fgcenter_maskaware_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
G12 largest-square foreground canonicalization branch.
Use the largest trusted-mask connected component, crop/recenter it with
foreground_crop_mode=largest_square and margin=0.35, then train with USE_MASK=1.
```

Run:

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_fgcenter_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --foreground-crop --foreground-crop-margin 0.35 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

Published artifacts:

```text
experiments/ri3d_datasets/first2_fgcenter_maskaware/
experiments/metrics/ri3d_first2_fgcenter_maskaware_iter500.csv
experiments/figures/ri3d_first2_fgcenter_maskaware_iter500_inputs.png
experiments/figures/ri3d_first2_fgcenter_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_fgcenter_maskaware_iter500/
```

Summary:

| sample | views | roles | final loss | rgb mp4 |
| --- | ---: | --- | ---: | --- |
| web_clean_frontal_03 | 4 | geometry_only:2, identity_supervision:2 | 0.0093817 | yes |
| web_clean_frontal_01 | 4 | identity_supervision:4 | 0.0159728 | yes |

Observations:

```text
All four MP4s validate as 120 frames at 160x160.
The input sheet is cleaner than G11 because non-main mask components are removed
from RGB and the main foreground is recentered.
The render sheet still shows the same fragmented/rotated photo-card pattern.
The loss is not comparable to full-image baselines because G12 changes both
input scale and mask objective.
Conclusion: largest-square foreground canonicalization with mask-aware loss is
an implementation pass but not a visual method win.
```

Next iteration:

```text
Compare against the same data without USE_MASK and against a more aggressive
mask_width_anchor head/upper-body crop. If those also fail, move to a structural
geometry prior instead of expanding to first10.
```
