# Trusted Region Mask Observations

Date: 2026-05-19

## Scope

This pass turns the CLIP-ranked `steps75 + budget4` Zero123++ pseudo views into
foreground mask atlases and overlay atlases.

Generated files:

```text
scripts/build_trusted_region_masks.py
experiments/pseudo_views/trusted_region_masks_steps75_budget4/
experiments/metrics/trusted_region_masks_first10_steps75_budget4.csv
experiments/metrics/trusted_region_mask_summary_first10_steps75_budget4.csv
experiments/figures/trusted_region_masks_first10_steps75_budget4.png
```

The goal is not to produce final segmentation. The goal is to test whether the
currently selected pseudo views can be made safe enough for later
Gaussian/PanoHead supervision by masking unreliable regions.

## Result

```text
selected views: 40
accepted masks: 25
rejected masks: 15
```

Accepted selected views by sample:

```text
web_clean_frontal_01: 4 / 4
web_clean_frontal_02: 4 / 4
web_clean_frontal_03: 0 / 4
web_complex_hair_01: 3 / 4
web_complex_hair_02: 0 / 4
web_glasses_01: 3 / 4
web_glasses_02: 3 / 4
web_mild_side_01: 2 / 4
web_mild_side_02: 2 / 4
web_occlusion_lowq_01: 4 / 4
```

Dominant reject reasons:

```text
photo_frame_geometry_risk: 14
low_reliability: 9
full_photo_or_background_rotation: 9
overwide_mask_without_face: 6
low_trusted_score: 5
overfull_mask: 4
hair_hallucination_risk: 4
glasses_identity_risk: 1
```

## Interpretation

The mask pass confirms that a pure pseudo-view ranking is still too optimistic.
Several generated images are rotations of the source photograph or photo frame,
not rotations of the head itself. CLIP similarity and foreground masking can
reduce this damage, but they cannot fully fix the input-format problem.

This changes the next iteration priority:

```text
Do not feed all selected pseudo views into 3D supervision.
Use the mask pass to reject obvious unsafe views first.
Run an input-format ablation with subject-only gray-background cutouts.
Only compare reconstruction quality after the pseudo-view input format is sane.
```

## Decision

The current best validated route is:

```text
Zero123++ steps75
-> CLIP/reliability budget4 ranking
-> trusted-region mask rejection
-> reject samples with fewer than 2 accepted views
-> rerun/repair with subject cutouts before Gaussian or PanoHead fusion
```

This partially validates the application hypothesis: pseudo views can add useful
coverage, but only after failure-aware selection and masking. It also falsifies
the weaker idea that more diffusion steps alone make pseudo views safe.
