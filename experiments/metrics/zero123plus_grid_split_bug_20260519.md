# Zero123++ Grid Split Bug

Date: 2026-05-19

## Finding

The historical Zero123++ splitting code used:

```text
rows=2
cols=3
```

But the saved `sudo-ai/zero123plus-v1.2` grids in this repo are:

```text
640 x 960 pixels
3 rows x 2 columns
```

This means the historical per-view PNG files were incorrectly sliced into tall
tiles that combined parts of two different generated views. The obvious
split-body and photo-card artifacts in `experiments/downstream_datasets/` were
therefore caused by both:

```text
1. real Zero123++ generation distortions
2. a severe 2x3 versus 3x2 grid-splitting bug
```

## Fix

The default split was corrected in:

```text
scripts/zero123plus_batch.py
scripts/zero123plus_generate.py
```

and existing grids can be repaired with:

```text
scripts/resplit_zero123plus_grids.py
```

## Corrected Artifacts

```text
experiments/pseudo_views/zero123plus_first10_cutout_steps75_resplit3x2/
experiments/pseudo_views/zero123plus_first10_head_cutout_steps75_resplit3x2/
```

The wrong 2x3 head-cutout probe was moved out of the repo to:

```text
/data1/workspace/airulan/3dv_work/quarantine/wrong_2x3_head_cutout_probe_20260519/
```

## Impact

All milestones that consumed historical per-view Zero123++ PNGs must be
interpreted under this bug:

```text
G2-G6 pseudo-view scoring/selection metrics are contaminated by wrong per-view crops.
G8-G14 RI3D/Gaussian experiments consumed invalid candidate views and cannot
support reconstruction-quality conclusions.
```

The useful retained lessons are engineering lessons:

```text
every generated image artifact needs VLM/manual visual audit before a milestone
every grid/tile parser needs a visual and dimension sanity check
candidate pools are not training datasets
```

## Current Status

Correct 3x2 resplitting improves the artifact situation substantially, but
visual inspection still shows identity and geometry distortions in the generated
pseudo views. Therefore the corrected web first10 pseudo views remain
diagnostic-only and are still blocked for reconstruction training.
