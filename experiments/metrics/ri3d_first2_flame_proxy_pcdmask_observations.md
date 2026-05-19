# ri3d_first2_flame_proxy_pcdmask_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Test whether a LAM/FLAME-derived structural proxy can improve the G13 foreground
point-cloud filter. G13 removed much of the rectangular card background, but
still left detached foreground chunks.

This G14 pass copies the G12 fghead RGB/mask scenes, replaces RI3D depth/conf
with rendered FLAME proxy depth/conf, and then keeps only foreground/confident
points through the G13 `PCD_MASK_FILTER=1` path.
```

Run:

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_flame_proxy_pcdmask OUT_ROOT=experiments/downstream_3d/ri3d_first2_flame_proxy_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_flame_proxy_pcdmask RUN_ROOT=experiments/downstream_3d/ri3d_first2_flame_proxy_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_flame_proxy_pcdmask --run-root experiments/downstream_3d/ri3d_first2_flame_proxy_pcdmask_iter500 --export-root experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500 --metrics-csv experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv --observations experiments/metrics/ri3d_first2_flame_proxy_pcdmask_observations.md --input-figure experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_renders.png --iteration 500 --run-name ri3d_first2_flame_proxy_pcdmask_iter500 --variants roleaware_cutout75_budget4
```

Published artifacts:

```text
scripts/render_flame_proxy_priors.py
experiments/metrics/flame_geometry_prior_first2_plan.md
experiments/metrics/flame_geometry_prior_first2_observations.md
experiments/geometry_priors/flame_first2_proxy/
experiments/figures/flame_geometry_prior_first2_proxy_sheet.png
experiments/figures/ri3d_first2_flame_proxy_vs_pcdmask_iter500_renders.png
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_renders.png
experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500/
```

Summary:

| sample | variant | views | roles | final loss | splats | rgb mp4 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| web_clean_frontal_03 | roleaware_cutout75_budget4 | 4 | geometry_only:2, identity_supervision:2 | 0.1279854 | 21364 | yes |
| web_clean_frontal_01 | roleaware_cutout75_budget4 | 4 | identity_supervision:4 | 0.2391389 | 25432 | yes |

Observations:

```text
The FLAME proxy sheet is nonblank for both first2 samples and gives a coherent
head/neck silhouette for all four RI3D view slots.

Both first2 init/train/render runs complete at 500 iterations. The exported
RGB/depth MP4s validate as 120 frames at 160x160.

G14 reduces some background/card support relative to G13, but it also removes
too much subject support. web_clean_frontal_03 loses the upper face in several
frames, and web_clean_frontal_01 remains split into disconnected body/head
fragments.

Training loss is higher than G13:
  web_clean_frontal_03: G13 0.1139016 -> G14 0.1279854
  web_clean_frontal_01: G13 0.2007467 -> G14 0.2391389

The render command emitted one zero-range depth normalization warning for
web_clean_frontal_01 depth video generation. The RGB MP4 still exported and
validated, so this is a visualization warning rather than a failed run.

Conclusion: the simple rendered FLAME depth/conf proxy is a useful diagnostic
artifact, but it does not repair RI3D into a stable 3D head. It confirms that
the paper claim should not be "we solved reconstruction with pseudo views";
the defensible claim is a failure-aware diagnostic protocol showing where
pseudo-view filtering helps and where sparse-view RI3D still needs stronger
head-specific structure.
```

Next iteration:

```text
Do not scale G14 as a reconstruction method win.

Use first10 expansion as a diagnostic study only: keep G13/G14 first2 evidence
as the reason to report pseudo-view failure taxonomy, not as a solved method.

If another reconstruction repair is attempted, it should be a positive-control
LAM mesh/Gaussian baseline or a direct head-template initialization, not another
generic RI3D depth/conf replacement.
```
