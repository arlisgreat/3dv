# ri3d_first2_roleaware_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Test whether identity-filter roles can improve the first2 RI3D gate without invasive third-party loss changes.
Use identity_supervision RGB frames and geometry_only desaturated frames from cutout75 budget4.
```

Run:

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_roleaware --run-root experiments/downstream_3d/ri3d_first2_roleaware_iter500 --export-root experiments/reconstructions/ri3d_first2_roleaware_iter500 --metrics-csv experiments/metrics/ri3d_first2_roleaware_iter500.csv --observations experiments/metrics/ri3d_first2_roleaware_observations.md --input-figure experiments/figures/ri3d_first2_roleaware_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_roleaware_iter500_renders.png --iteration 500 --run-name ri3d_first2_roleaware_iter500 --variants roleaware_cutout75_budget4
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_roleaware_iter500.csv
experiments/figures/ri3d_first2_roleaware_iter500_inputs.png
experiments/figures/ri3d_first2_roleaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleaware_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| web_clean_frontal_03 | roleaware_cutout75_budget4 | 4 | geometry_only:2, identity_supervision:2 | 0.0157378 | 102400 | yes |
| web_clean_frontal_01 | roleaware_cutout75_budget4 | 4 | identity_supervision:4 | 0.0154150 | 102400 | yes |

Baseline comparison:

| sample | role-aware loss | raw75_budget4 loss | cutout75_budget4_masked loss | read |
| --- | ---: | ---: | ---: | --- |
| web_clean_frontal_03 | 0.0157378 | 0.0147302 | 0.0157672 | slightly better than cutout, worse than raw budget4 |
| web_clean_frontal_01 | 0.0154150 | 0.0163405 | 0.0152439 | better than raw budget4, worse than cutout |

Observations:

```text
The pipeline is now end-to-end executable with role-aware first2 RI3D inputs.
This run deliberately keeps RI3D loss code unchanged; role effects enter through prepared images and metadata.
web_clean_frontal_01: best training loss is roleaware_cutout75_budget4 (0.0154150).
web_clean_frontal_03: best training loss is roleaware_cutout75_budget4 (0.0157378).
This run tests role-aware RI3D inputs rather than another uniform filtered-view baseline.
identity_supervision frames keep RGB texture; geometry_only frames are desaturated and have lower depth-confidence metadata.
RI3D still applies a uniform RGB reconstruction loss, so this is a conservative non-invasive G9 pass.
All four exported MP4s were readable with 120 frames at 160x160.
The first-frame render sheet still shows fragmented/rotated photo-card artifacts, so this is not a visual win.
Conclusion: role metadata plus geometry-only desaturation is useful infrastructure, but explicit RI3D loss weighting is still required.
```

Next iteration:

```text
Compare role-aware videos against raw75_budget4 and cutout75_budget4_masked iter500.
If geometry-only desaturation is insufficient, patch RI3D loss to consume per-frame role weights explicitly.
Expand beyond first2 only after role-aware visual quality is no worse than raw75_budget4.
```
