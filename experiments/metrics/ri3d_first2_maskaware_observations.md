# ri3d_first2_maskaware_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Test whether spatial mask-aware RI3D supervision reduces pseudo-view
background/photo-frame artifacts after G10 per-view role weights remained
visually ambiguous.
```

Run:

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_maskaware --run-root experiments/downstream_3d/ri3d_first2_maskaware_iter500 --export-root experiments/reconstructions/ri3d_first2_maskaware_iter500 --metrics-csv experiments/metrics/ri3d_first2_maskaware_iter500.csv --observations experiments/metrics/ri3d_first2_maskaware_observations.md --input-figure experiments/figures/ri3d_first2_maskaware_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_maskaware_iter500_renders.png --iteration 500 --run-name ri3d_first2_maskaware_iter500 --variants roleaware_cutout75_budget4
```

Published artifacts:

```text
patches/ri3d/mask_aware_loss.patch
experiments/ri3d_datasets/first2_maskaware/
experiments/metrics/ri3d_first2_maskaware_iter500.csv
experiments/figures/ri3d_first2_maskaware_iter500_inputs.png
experiments/figures/ri3d_first2_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_maskaware_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| web_clean_frontal_03 | roleaware_cutout75_budget4 | 4 | geometry_only:2, identity_supervision:2 | 0.0084686 | 102400 | yes |
| web_clean_frontal_01 | roleaware_cutout75_budget4 | 4 | identity_supervision:4 | 0.0155180 | 102400 | yes |

Observations:

```text
The pipeline is now end-to-end executable with mask_path metadata and explicit
USE_MASK=1 RI3D training.
The patch gates mask loading behind --use_mask so older first2/G9/G10 baselines
do not silently change when mask_path exists.
All four exported MP4s validate as 120 frames at 160x160.
web_clean_frontal_03 final loss is 0.0084686, close to G10 0.0085665, but not
directly comparable to unmasked full-image losses because foreground masking
changes the optimized objective.
web_clean_frontal_01 final loss is 0.0155180, worse than G10 0.0152099 and
worse than the G8 cutout75_budget4_masked 0.0152439.
The render sheet still shows fragmented/rotated photo-card artifacts and
largely empty views. Masked RGB/SSIM plus silhouette is therefore an
implementation pass but not a visual method win.
Likely cause: foreground masking removes background loss pressure but does not
canonicalize the subject scale/position or add a true head/full-body structural
prior. The optimizer can satisfy the foreground objective with small floating
fragments.
```

Next iteration:

```text
Do not expand to first10 yet.
Run a first2 foreground-canonical ablation: crop/recenter each pseudo-view by
its trusted mask before RI3D conversion, preserve role weights, and compare
mask RGB only vs mask RGB + silhouette vs geometry-only depth/silhouette only.
If recentering still fails, move to a stronger LAM/FLAME/full-head geometry
prior before spending compute on first10/first30.
```
