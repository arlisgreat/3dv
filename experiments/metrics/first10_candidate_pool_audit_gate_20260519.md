# G15 Data Audit Gate

Date: 2026-05-19

Premise under audit:

```text
first10 downstream_datasets are weakly screened pseudo-view candidate pools; before any reconstruction, audit whether they are even suitable for diagnostic use
```

Gate verdict:

```text
Candidate-pool diagnostic gate: BLOCKED
Reconstruction-training gate: BLOCKED_UNVALIDATED
Visual/VLM gate: BLOCKED
```

Interpretation:

```text
The audited directories are pseudo-view candidate pools and RI3D-readable candidate exports.
They are structurally usable for diagnostic and failure-taxonomy work only.
They are not validated reconstruction training datasets.
No milestone should start training/reconstruction from them unless the milestone premise explicitly states this risk.
```

Artifacts:

```text
experiments/metrics/first10_candidate_pool_audit_gate_20260519.csv
experiments/figures/first10_candidate_pool_audit_gate_20260519.png
```

Visual/VLM notes:

```text
VLM/manual inspection of experiments/figures/first10_candidate_pool_visual_audit_20260519.png shows many selected candidates are split bodies, rotated photo cards, cropped fragments, or background/body-only pieces. Current candidate pools are not valid reconstruction training data.
```

Variant summary:

| variant | samples | min views | mean views | missing refs | stale abs refs | roles | candidate gate | training gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| cutout75_budget4_masked | 10/10 | 3 | 3.70 | 0 | 74 | id:0, geom:0, uniform:37 | pass_with_warnings_for_diagnostics | blocked_unvalidated |
| raw75_all6 | 10/10 | 6 | 6.00 | 60 | 120 | id:0, geom:0, uniform:60 | blocked_until_data_fixed | blocked_unvalidated |
| raw75_budget4 | 10/10 | 4 | 4.00 | 0 | 80 | id:0, geom:0, uniform:40 | pass_with_warnings_for_diagnostics | blocked_unvalidated |
| roleaware_cutout75_budget4 | 2/10 | 4 | 4.00 | 8 | 0 | id:6, geom:2, uniform:0 | blocked_until_data_fixed | blocked_unvalidated |

Required before the next milestone:

```text
1. State the experimental premise in falsifiable terms.
2. Run this data audit gate and publish CSV/MD/PNG outputs.
3. If the gate only passes for diagnostics, do not describe candidates as training data.
4. If reconstruction training is attempted, add a separate positive-control or manual-quality gate.
5. Record any blocked or warning state in MILESTONES.md before running GPU jobs.
```
