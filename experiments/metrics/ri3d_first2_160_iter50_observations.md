# RI3D first2 160px iter50 downstream observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Close the first downstream 3D loop before expanding first10 to first30/first50.
Compare raw all-6 pseudo views, raw CLIP/reliability budget4, and cutout+mask budget4.
```

Run:

```bash
GPU=0 ITERATIONS=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 OUT_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/render_ri3d_first2.sh
python scripts/summarize_ri3d_first2.py --data-root experiments/ri3d_datasets/first2_160 --run-root experiments/downstream_3d/ri3d_first2_160_iter50 --iteration 50
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_160_iter50.csv
experiments/figures/ri3d_first2_160_iter50_inputs.png
experiments/figures/ri3d_first2_160_iter50_renders.png
experiments/reconstructions/ri3d_first2_160_iter50/
```

Summary:

| sample | variant | views | final loss | splats | rgb mp4 |
| --- | --- | ---: | ---: | ---: | --- |
| web_clean_frontal_03 | raw75_all6 | 6 | 0.1471757 | 153600 | yes |
| web_clean_frontal_01 | raw75_all6 | 6 | 0.1407922 | 153600 | yes |
| web_clean_frontal_03 | raw75_budget4 | 4 | 0.1258080 | 102400 | yes |
| web_clean_frontal_01 | raw75_budget4 | 4 | 0.1285311 | 102400 | yes |
| web_clean_frontal_03 | cutout75_budget4_masked | 4 | 0.1272559 | 102400 | yes |
| web_clean_frontal_01 | cutout75_budget4_masked | 4 | 0.1273211 | 102400 | yes |

Observations:

```text
The pipeline is now end-to-end executable through RI3D on two first10 samples.
At this very short 50-iteration smoke budget, raw75_budget4 is best on web_clean_frontal_03.
cutout75_budget4_masked is best by a small margin on web_clean_frontal_01.
raw75_all6 has more splats and higher training loss in both samples, so more views are not automatically better.
The rendered videos are smoke-quality only: several views still show rotated full-photo/background artifacts.
Some 4-view depth videos emitted zero-range depth normalization warnings; use RGB renders and longer runs for judgment.
This is not yet a final quality claim; it is a gate that justifies longer iter runs and visual inspection.
```

Next iteration:

```text
Run the same 160px protocol at 500-1500 iterations for first2.
Use rendered video inspection plus identity-filter tags before expanding beyond first2.
Keep RI3D PLYs in the ignored downstream output area unless a size-reviewed branch is created.
```
