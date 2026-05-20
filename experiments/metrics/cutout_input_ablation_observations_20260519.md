# Cutout Input Ablation Observations

Date: 2026-05-19

## Scope

This iteration tests whether Zero123++ should receive the original portrait
crop or a subject-only gray-background cutout.

Generated files:

```text
scripts/data/make_first10_cutouts.py
scripts/evaluate_cutout_ablation.py
scripts/evaluate_cutout_clip_consistency.py
experiments/inputs/first10/cutouts/
experiments/inputs/first10/cutouts_manifest.csv
experiments/figures/first10_cutout_inputs.png
experiments/pseudo_views/zero123plus_first10_cutout_steps75/
experiments/metrics/pseudo_view_reliability_raw_vs_cutout_steps75.csv
experiments/metrics/raw_vs_cutout_comparison_steps75.csv
experiments/metrics/pseudo_view_clip_consistency_raw_vs_cutout_steps75.csv
experiments/metrics/clip_raw_vs_cutout_comparison_steps75.csv
experiments/pseudo_views/trusted_region_masks_cutout75_budget4/
experiments/figures/trusted_region_masks_first10_cutout75_budget4.png
```

`rembg` downloaded `u2net.onnx` into the local cache under `.cache/rembg`.
That model file is not part of the committed experiment record.

## Reliability Result

Raw `steps75` versus cutout `steps75`:

```text
raw75 mean reliability: 66.97
cutout75 mean reliability: 70.58
delta: +3.62

raw75 good views, score >= 60: 32
cutout75 good views, score >= 60: 42

raw75 face-detected views: 17
cutout75 face-detected views: 13
```

Per-sample verdict:

```text
cutout_helped: 5
cutout_neutral: 2
cutout_hurt: 3
```

The face-detection count goes down because the cutout views more often include
profiles and back-head views. This is not necessarily bad for reconstruction,
but it means Haar face count should not be used as the primary success metric.

## CLIP Consistency Result

```text
raw75 mean CLIP cosine: 0.4893
cutout75 mean CLIP cosine: 0.5401

raw75 mean trusted score: 69.59
cutout75 mean trusted score: 72.83

raw75 good trusted views, score >= 60: 38
cutout75 good trusted views, score >= 60: 43
```

Average CLIP-weighted selected-view score:

```text
raw75 budget1: 85.47
raw75 budget2: 83.89
raw75 budget4: 76.37
raw75 budget6: 69.59

cutout75 budget1: 91.86
cutout75 budget2: 88.60
cutout75 budget4: 80.79
cutout75 budget6: 72.83
```

## Trusted-Region Mask Result

The mask pass is the clearest signal:

```text
raw75 CLIP-budget4 accepted masks: 25 / 40
cutout75 CLIP-budget4 accepted masks: 37 / 40
```

The raw run had many `photo_frame_geometry_risk` and
`full_photo_or_background_rotation` failures. The cutout run reduces those
failures because Zero123++ is conditioned on the subject instead of the whole
photograph frame.

## Decision

The input-format ablation validates the current iteration idea:

```text
Use subject cutouts before Zero123++ pseudo-view generation.
Keep steps75 and budget4 as the default pseudo-view setting.
Keep trusted-region masks before any diagnostic downstream export.
Do not rely on cutouts alone; identity/filter checks are still required.
```

Post-G20 note: this remains a historical diagnostic frontend only. Corrected
3x2 audits later found visible pseudo-view distortions, so it is not an approved
training route without `PASS_REAL_GT_BENCHMARK`.
