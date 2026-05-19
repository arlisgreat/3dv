# ri3d_first2_roleweighted_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Test explicit role-weighted RI3D loss on first2 after G9 showed metadata-only role awareness was insufficient.
Use identity_supervision RGB frames at full RGB/depth weight and geometry_only frames at 0.25 RGB / 1.0 depth weight.
```

Run:

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_roleweighted --run-root experiments/downstream_3d/ri3d_first2_roleweighted_iter500 --export-root experiments/reconstructions/ri3d_first2_roleweighted_iter500 --metrics-csv experiments/metrics/ri3d_first2_roleweighted_iter500.csv --observations experiments/metrics/ri3d_first2_roleweighted_observations.md --input-figure experiments/figures/ri3d_first2_roleweighted_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_roleweighted_iter500_renders.png --iteration 500 --run-name ri3d_first2_roleweighted_iter500 --variants roleaware_cutout75_budget4
```

Published artifacts:

```text
patches/ri3d/role_weighted_loss.patch
experiments/ri3d_datasets/first2_roleweighted/
experiments/metrics/ri3d_first2_roleweighted_iter500.csv
experiments/figures/ri3d_first2_roleweighted_iter500_inputs.png
experiments/figures/ri3d_first2_roleweighted_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleweighted_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| web_clean_frontal_03 | roleaware_cutout75_budget4 | 4 | geometry_only:2, identity_supervision:2 | 0.0085665 | 102400 | yes |
| web_clean_frontal_01 | roleaware_cutout75_budget4 | 4 | identity_supervision:4 | 0.0152099 | 102400 | yes |

Baseline comparison:

| sample | role-weighted loss | G9 role-aware loss | raw75_budget4 loss | cutout75_budget4_masked loss | read |
| --- | ---: | ---: | ---: | ---: | --- |
| web_clean_frontal_03 | 0.0085665 | 0.0157378 | 0.0147302 | 0.0157672 | lower weighted loss is expected because 2/4 views have 0.25 RGB weight; not directly comparable |
| web_clean_frontal_01 | 0.0152099 | 0.0154150 | 0.0163405 | 0.0152439 | all views are identity_supervision, so this is roughly comparable and slightly beats cutout by loss |

Observations:

```text
The RI3D patch propagates supervision_role through transforms.json -> CameraInfo -> Camera -> cal_loss.
geometry_only frames use role_rgb_weight=0.25 and role_depth_weight=1.0.
web_clean_frontal_01: best training loss is roleaware_cutout75_budget4 (0.0152099).
web_clean_frontal_03: best training loss is roleaware_cutout75_budget4 (0.0085665).
All four exported MP4s were readable with 120 frames at 160x160.
The first-frame render sheet is still visually dominated by fragmented/rotated photo-card artifacts.
Conclusion: scalar per-view role weighting alone is still not enough; the next method step needs spatial foreground masks or stronger geometry priors.
```

Next iteration:

```text
Add spatial foreground/mask-aware loss before scaling beyond first2.
Keep first2 as the gate until render sheets improve, not just weighted training loss.
Do not treat the web_clean_frontal_03 weighted loss drop as a final quality win.
```
