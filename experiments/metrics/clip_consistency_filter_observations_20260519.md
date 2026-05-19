# CLIP Consistency Filter Notes

Date: 2026-05-19

## Scope

This is a lightweight learned-image consistency pass using the cached
Zero123++ `vision_encoder` (`CLIPVisionModelWithProjection`). It does not add a
new dependency or download a new identity model.

Generated files:

```text
scripts/evaluate_clip_consistency.py
experiments/metrics/pseudo_view_clip_consistency_first10_steps20_75.csv
experiments/metrics/clip_consistency_summary_first10_steps20_75.csv
experiments/metrics/view_budget_clip_selection_first10_steps20_75.csv
experiments/figures/view_budget_clip_selection_first10_steps75_budget4.png
```

This is not an ArcFace/InsightFace identity verifier. It is a stronger proxy
than HSV histogram similarity because it uses the same learned image encoder
family that conditions Zero123++.

## Aggregate Result

```text
steps20 mean CLIP cosine: 0.4533
steps75 mean CLIP cosine: 0.4893

steps20 mean trusted score: 66.36
steps75 mean trusted score: 69.59

steps20 good trusted views, score >= 60: 31
steps75 good trusted views, score >= 60: 38
```

The CLIP-weighted score agrees with the earlier reliability score: `steps75`
is generally better, but not sufficient to trust all generated views.

## View Budget

Average CLIP-weighted selected-view score:

```text
steps20 budget1: 88.38
steps20 budget2: 82.71
steps20 budget4: 72.78
steps20 budget6: 66.36

steps75 budget1: 85.47
steps75 budget2: 83.89
steps75 budget4: 76.37
steps75 budget6: 69.59
```

`steps75 + budget4` remains the best current compromise. It improves over
blind budget6 while retaining more coverage than budget1/2.

## Important Limitation

The learned-image proxy still selects some views where Zero123++ rotated the
whole source photograph, frame, or background object. These can be CLIP-similar
to the input while being bad 3D priors.

Therefore:

```text
CLIP consistency should re-rank candidate views.
Foreground/photo-frame failure labels should still reject unsafe views.
True identity filtering still needs a face-aware embedding model.
Trusted-region masks are still necessary before Gaussian/PanoHead fusion.
```

## Decision

For the next experiment:

```text
Use the intersection of reliability labels and CLIP-weighted ranking.
Keep budget4 as the default candidate count.
Escalate to ArcFace/InsightFace only if installation can be isolated cleanly.
Do not describe CLIP similarity as final identity preservation.
```
