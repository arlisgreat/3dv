# Zero123++ First10 Steps75 And View-Budget Notes

Date: 2026-05-19

## Experiment

The first10 set was regenerated with Zero123++ at `steps=75` and compared
against the existing `steps=20` pass. The diagnostic script evaluates every
generated view with cheap, reproducible proxies:

```text
nonblank check
foreground area and bounding box relative to the gray background
foreground center offset
OpenCV frontal-face detection
HSV histogram correlation to the input square crop
failure labels for photo/background rotation, weak style match, glasses,
hair, occlusion, and overfull/empty outputs
```

Generated files:

```text
experiments/pseudo_views/zero123plus_first10_steps75/
experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv
experiments/metrics/pseudo_view_summary_first10_steps20_75.csv
experiments/metrics/view_budget_selection_first10_steps20_75.csv
experiments/metrics/steps20_vs75_comparison_first10.csv
experiments/figures/zero123plus_first10_steps20_vs75_grids.png
experiments/figures/view_budget_selection_first10_steps75_budget4.png
```

## Result

Across the 10 samples, `steps=75` is useful but not universally safer:

```text
verdicts: 5 helped, 3 neutral, 2 hurt
mean reliability: 62.97 at steps20 -> 66.97 at steps75
good views, score >= 60: 25 at steps20 -> 32 at steps75
face-detected views: 12 at steps20 -> 17 at steps75
```

The two hurt cases are important:

```text
web_clean_frontal_03: 33.33 -> 27.33, no good views in either pass
web_complex_hair_02: 58.33 -> 47.33, good views 1 -> 0
```

This supports the current hypothesis: increasing diffusion steps alone is not
a reliable fix. View selection and failure filtering are necessary.

## View Budget

Average selected-view reliability:

```text
steps20 budget 1: 92.20
steps20 budget 2: 84.00
steps20 budget 4: 71.30
steps20 budget 6: 62.97

steps75 budget 1: 85.20
steps75 budget 2: 83.80
steps75 budget 4: 76.25
steps75 budget 6: 66.97
```

Interpretation:

```text
budget=1 often cherry-picks a high-score front-ish view but gives poor coverage.
budget=6 includes all bad views and reproduces the full-run failure modes.
budget=4 is the current best compromise for steps75: it improves coverage while
keeping the average selected reliability above the all-view setting.
```

## Failure Signals

Dominant failure modes are consistent with the paper problem:

```text
full_photo_or_background_rotation
no_frontal_face_detected
weak or low input style similarity
glasses_identity_risk
hair_hallucination_risk
occlusion_identity_risk
```

Several generated views rotate the entire source photograph or frame rather
than reconstructing a free-standing head. These views should be treated as
unsafe pseudo priors for the application route, because they will likely inject
background geometry into Gaussian reconstruction.

## Decision

For the next iteration:

```text
Use steps75 + budget4 as the default pseudo-view candidate set.
Reject samples or views with full_photo_or_background_rotation when possible.
Keep steps20 outputs as a diagnostic baseline rather than deleting or replacing them.
Do not feed all six pseudo views blindly into downstream reconstruction.
```

The current proxy metrics are intentionally cheap. A later identity filter
should replace or augment the histogram/Haar checks with face embedding or
ArcFace-style identity similarity where the view contains a usable face.
