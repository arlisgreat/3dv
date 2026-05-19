# G15 Head-Cutout Zero123++ Probe

Date: 2026-05-19

Purpose:

```text
Test whether tighter gray-background head cutouts recover the pseudo-view candidate premise.
This is a generation/candidate audit only; it does not approve reconstruction training.
```

Artifacts:

```text
experiments/pseudo_views/zero123plus_first10_head_cutout_steps75_resplit3x2
experiments/metrics/pseudo_view_reliability_first10_head_cutout_steps75_resplit3x2.csv
experiments/metrics/view_budget_selection_first10_head_cutout_steps75_resplit3x2.csv
experiments/metrics/pseudo_view_summary_first10_head_cutout_steps75_resplit3x2.csv
experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png
experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png
```

Metric summary:

```text
mean reliability over samples: 79.467
mean views/sample with score >= 60: 6.00
```

Gate note:

```text
Use the PNG grid and budget figures for VLM/manual inspection. The old metric
is known to be weak, so a high score alone is not a pass.
```

| sample | group | mean score | good views >=60 | face views | dominant failures |
| --- | --- | ---: | ---: | ---: | --- |
| web_clean_frontal_01 | clean_frontal | 86.000 | 6 | 3 | no_frontal_face_detected:3 |
| web_clean_frontal_02 | clean_frontal | 76.667 | 6 | 1 | no_frontal_face_detected:5 |
| web_clean_frontal_03 | clean_frontal | 76.667 | 6 | 1 | no_frontal_face_detected:5 |
| web_complex_hair_01 | complex_hair | 86.000 | 6 | 3 | no_frontal_face_detected:3 |
| web_complex_hair_02 | complex_hair | 76.667 | 6 | 1 | no_frontal_face_detected:5 |
| web_glasses_01 | glasses | 76.667 | 6 | 1 | no_frontal_face_detected:5;glasses_identity_risk:5 |
| web_glasses_02 | glasses | 76.667 | 6 | 1 | no_frontal_face_detected:5;glasses_identity_risk:5 |
| web_mild_side_01 | mild_side | 76.667 | 6 | 1 | no_frontal_face_detected:5 |
| web_mild_side_02 | mild_side | 86.000 | 6 | 3 | no_frontal_face_detected:3 |
| web_occlusion_lowq_01 | occlusion_lowq | 76.667 | 6 | 1 | no_frontal_face_detected:5;occlusion_identity_risk:5 |
