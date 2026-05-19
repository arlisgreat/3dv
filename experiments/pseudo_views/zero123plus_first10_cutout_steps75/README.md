# Zero123++ First10 Cutout Steps75

This directory contains the input-format ablation for the first10 pilot.

Run identity:

```text
model: sudo-ai/zero123plus-v1.2
inputs: experiments/inputs/first10/cutouts_manifest.csv
seed: 42
steps: 75
views: 6 per input
output: experiments/pseudo_views/zero123plus_first10_cutout_steps75/
log: /data1/workspace/airulan/3dv_work/logs/zero123plus_first10_cutout_steps75_20260519.log
```

Purpose:

```text
Test whether subject-only gray-background cutouts reduce Zero123++ photo-frame
rotation failures compared with the raw portrait crops.
```

Evaluation:

```text
experiments/metrics/pseudo_view_reliability_raw_vs_cutout_steps75.csv
experiments/metrics/raw_vs_cutout_comparison_steps75.csv
experiments/metrics/pseudo_view_clip_consistency_raw_vs_cutout_steps75.csv
experiments/metrics/clip_raw_vs_cutout_comparison_steps75.csv
experiments/figures/zero123plus_first10_raw_vs_cutout_steps75_grids.png
experiments/figures/trusted_region_masks_first10_cutout75_budget4.png
```
