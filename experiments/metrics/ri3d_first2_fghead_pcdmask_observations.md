# ri3d_first2_fghead_pcdmask_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Test whether the remaining G12 card artifact is seeded by RI3D point-cloud initialization.
Keep the G12 fghead mask-aware RGB/mask inputs, but filter the initial point cloud to foreground mask pixels.
Preserve RI3D defaults unless PCD_MASK_FILTER=1 is set.
```

Run:

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_fghead_maskaware --run-root experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 --export-root experiments/reconstructions/ri3d_first2_fghead_pcdmask_iter500 --metrics-csv experiments/metrics/ri3d_first2_fghead_pcdmask_iter500.csv --observations experiments/metrics/ri3d_first2_fghead_pcdmask_observations.md --input-figure experiments/figures/ri3d_first2_fghead_pcdmask_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_fghead_pcdmask_iter500_renders.png --iteration 500 --run-name ri3d_first2_fghead_pcdmask_iter500 --variants roleaware_cutout75_budget4
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_fghead_pcdmask_iter500.csv
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_fghead_pcdmask_vs_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_fghead_pcdmask_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| web_clean_frontal_03 | roleaware_cutout75_budget4 | 4 | geometry_only:2, identity_supervision:2 | 0.1139016 | 27064 | yes |
| web_clean_frontal_01 | roleaware_cutout75_budget4 | 4 | identity_supervision:4 | 0.2007467 | 38064 | yes |

Observations:

```text
Initial naive mask filtering failed because RI3D assumes the number of points is divisible by the camera count.
The G13 patch therefore uses a dynamic equal-points-per-view target after foreground filtering.
web_clean_frontal_03 keeps 6766 foreground points/view, 27064 total splats, final train loss 0.1139016.
web_clean_frontal_01 keeps 9516 foreground points/view, 38064 total splats, final train loss 0.2007467.
Compared with G12 fghead mask-aware, the gray rectangular card backgrounds are visibly reduced or removed.
The outputs are still not stable 3D heads: foreground fragments remain detached and sparse, especially on orbit views.
Conclusion: point-cloud foreground filtering is a partial positive implementation signal, but not a sufficient geometry prior.
```

Next iteration:

```text
Do not expand first10 yet.
Use this result to justify a stronger LAM/FLAME mesh/depth/silhouette prior for first2.
If FLAME-derived depth/silhouette cannot repair detached fragments, pivot the paper framing toward diagnostic failure taxonomy and use LAM as the baseline positive control.
```
