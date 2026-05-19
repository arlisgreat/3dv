# Zero123++ First10 Steps75

This directory contains the second Zero123++ first10 pass.

Run identity:

```text
model: sudo-ai/zero123plus-v1.2
inputs: experiments/inputs/first10/processed/
seed: 42
steps: 75
views: 6 per input
output: experiments/pseudo_views/zero123plus_first10_steps75/
log: /data1/workspace/airulan/3dv_work/logs/zero123plus_first10_steps75_20260519_092137.log
```

Purpose:

```text
Test whether a higher diffusion step count improves pseudo-view reliability
for the first10 head-image set, and provide candidates for view-budget and
trusted-view selection.
```

Summary:

```text
10 / 10 samples completed.
Each sample has input_square.png, grid.png, six view_*.png files, and metadata.json.
```

Evaluation:

```text
experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv
experiments/metrics/pseudo_view_summary_first10_steps20_75.csv
experiments/metrics/view_budget_selection_first10_steps20_75.csv
experiments/metrics/steps20_vs75_comparison_first10.csv
experiments/figures/zero123plus_first10_steps20_vs75_grids.png
experiments/figures/view_budget_selection_first10_steps75_budget4.png
```

The result is not a final face-quality benchmark. It is a diagnostic pass for
deciding which generated views are safe enough to feed into later
PanoHead/Gaussian reconstruction experiments.
