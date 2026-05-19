# ri3d_first2_160_iter500 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Close the first downstream 3D loop before expanding first10 to first30/first50.
Compare raw all-6 pseudo views, raw CLIP/reliability budget4, and cutout+mask budget4.
```

Run:

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_160 OUT_ROOT=experiments/downstream_3d/ri3d_first2_160_iter500 bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_160 RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter500 bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_160 --run-root experiments/downstream_3d/ri3d_first2_160_iter500 --export-root experiments/reconstructions/ri3d_first2_160_iter500 --metrics-csv experiments/metrics/ri3d_first2_160_iter500.csv --observations experiments/metrics/ri3d_first2_160_iter500_observations.md --input-figure experiments/figures/ri3d_first2_160_iter500_inputs.png --render-figure experiments/figures/ri3d_first2_160_iter500_renders.png --iteration 500 --run-name ri3d_first2_160_iter500
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_160_iter500.csv
experiments/figures/ri3d_first2_160_iter500_inputs.png
experiments/figures/ri3d_first2_160_iter500_renders.png
experiments/reconstructions/ri3d_first2_160_iter500/
```

Summary:

| sample | variant | views | final loss | splats | rgb mp4 |
| --- | --- | ---: | ---: | ---: | --- |
| web_clean_frontal_03 | raw75_all6 | 6 | 0.0195983 | 153600 | yes |
| web_clean_frontal_01 | raw75_all6 | 6 | 0.0211399 | 153600 | yes |
| web_clean_frontal_03 | raw75_budget4 | 4 | 0.0147302 | 102400 | yes |
| web_clean_frontal_01 | raw75_budget4 | 4 | 0.0163405 | 102400 | yes |
| web_clean_frontal_03 | cutout75_budget4_masked | 4 | 0.0157672 | 102400 | yes |
| web_clean_frontal_01 | cutout75_budget4_masked | 4 | 0.0152439 | 102400 | yes |

Observations:

```text
The pipeline is now end-to-end executable through RI3D on two first10 samples.
raw75_all6 has more splats and higher training loss in both samples, so more views are not automatically better.
web_clean_frontal_01: best training loss is cutout75_budget4_masked (0.0152439).
web_clean_frontal_03: best training loss is raw75_budget4 (0.0147302).
This is a longer first2 milestone, but still a two-sample gate rather than a final first10/first50 claim.
Use the RGB/depth videos together with loss; low training loss alone does not prove better identity or geometry.
If filtered variants do not visibly improve over raw75_budget4, the next method step must change supervision roles before scaling data.
```

Next iteration:

```text
Compare RGB/depth videos frame-by-frame against the iter50 smoke and the input contact sheet.
Make the RI3D downstream loader consume identity_supervision, geometry_only, identity_reject, and mask_reject roles.
Expand beyond first2 only after the filtered path wins on rendered quality, not just on training loss.
```
