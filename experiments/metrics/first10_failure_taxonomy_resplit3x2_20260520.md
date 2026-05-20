# G18 Corrected First10 Failure Taxonomy

Date: 2026-05-20

Gate verdict:

```text
PASS_DIAGNOSTIC_ONLY
BLOCKED_RECONSTRUCTION_TRAINING
```

Premise:

```text
Only corrected Zero123++ 3x2 head-cutout pseudo views are audited here.
The taxonomy explains pseudo-view failures; it does not validate web
first10 as reconstruction-training data.
```

Artifacts:

```text
experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.csv
experiments/figures/first10_failure_taxonomy_resplit3x2_20260520.png
experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png
experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png
```

Role counts:

| role | count |
| --- | ---: |
| geometry_only | 37 |
| identity_supervision | 10 |
| reject | 13 |

Failure label counts:

| label | count |
| --- | ---: |
| geometry_drift | 24 |
| accessory_or_occlusion_instability | 19 |
| face_detector_miss_nonfrontal | 18 |
| hair_or_head_boundary_instability | 18 |
| texture_style_drift | 15 |
| source_frame_or_background_leakage | 14 |
| card_or_billboard_artifact | 10 |
| identity_drift | 9 |
| low_information_or_ambiguous | 9 |
| viewpoint_pose_error | 2 |

Sample primary families:

| family | samples |
| --- | ---: |
| accessory_occlusion_dominant | 3 |
| geometry_or_card_artifact_dominant | 2 |
| identity_drift_dominant | 1 |
| mostly_coherent_head_orbit | 1 |
| style_or_source_artifact_dominant | 3 |

Budget4 audit:

```text
selected_views: 40
selected_reject_views: 8
selected_severity3_views: 8
Reliability-selected budget4 still contains manual reject/severe views,
so automatic ranking cannot certify reconstruction supervision.
```

Group-level dominant labels:

| group | dominant labels |
| --- | --- |
| clean_frontal | geometry_drift:14, face_detector_miss_nonfrontal:12, hair_or_head_boundary_instability:8, identity_drift:4 |
| complex_hair | accessory_or_occlusion_instability:6, hair_or_head_boundary_instability:5, geometry_drift:5, texture_style_drift:4 |
| glasses | accessory_or_occlusion_instability:7, source_frame_or_background_leakage:5, card_or_billboard_artifact:4, texture_style_drift:4 |
| mild_side | texture_style_drift:7, card_or_billboard_artifact:6, source_frame_or_background_leakage:6, identity_drift:3 |
| occlusion_lowq | accessory_or_occlusion_instability:6, low_information_or_ambiguous:3, source_frame_or_background_leakage:2, face_detector_miss_nonfrontal:1 |

Allowed claim:

```text
The corrected first10 pseudo views reveal recurring identity, geometry,
accessory, style, and card/source-frame failures. Budgeted candidate
selection improves 2D hygiene in some cases but does not make the
candidate pool valid reconstruction supervision.
```

Disallowed claim:

```text
Do not claim that corrected first10 pseudo views are a valid RI3D training
dataset or that CLIP/reliability/budget4 proves 3D reconstruction quality.
```
