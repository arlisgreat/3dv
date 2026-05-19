# Head-Cutout Probe Resplit3x2 Gate

Date: 2026-05-19

Gate verdict:

```text
PASS_DIAGNOSTIC_ONLY
BLOCKED_RECONSTRUCTION_TRAINING
```

Artifacts:

```text
experiments/inputs/first10/head_cutouts/
experiments/pseudo_views/zero123plus_first10_head_cutout_steps75_resplit3x2/
experiments/metrics/head_cutout_probe_observations_20260519_resplit3x2.md
experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png
experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png
```

Interpretation:

```text
Correcting the grid split from 2x3 to 3x2 removes the artificial tall split-view
tiles. The head-cutout probe now produces more coherent 3x2 grids for several
samples.

However, the generated pseudo views still contain identity drift, view-dependent
geometry distortion, missing/changed accessories, stylized backs of head, and
problematic cases for glasses/occlusion. They are not reliable enough as
reconstruction training supervision.
```

Next action:

```text
Use web first10 only for pseudo-view failure taxonomy.
Use a true multi-view / mesh / point-cloud dataset case for reconstruction
validation.
```
