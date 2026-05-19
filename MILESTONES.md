# Milestones

This file is the follow-up ledger for the 3DV sprint. `EXPERIMENTS.md` remains
the detailed result index; this file records the final goal, completed gates,
active decision point, and planned milestones.

## Final Goal

The full application in `QY25181-申请书-6-13.pdf` targets:

```text
single portrait/head image
-> diffusion-generated multi-view priors for invisible regions
-> PanoHead-style 360 full-head modeling
-> replace NeRF rendering with 3D Gaussian representation
-> Transformer/style consistency across input and pseudo views
-> FLAME/FaceVerse/3DMM structural priors for stable geometry and animation
```

That full system is too large for the current one-month paper sprint. The
compressed paper goal is:

```text
Diagnose when diffusion pseudo views help or hurt single-image Gaussian head
reconstruction, and define a failure-aware pseudo-view supervision protocol.
```

The strongest current framing is:

```text
Failure-aware pseudo-view supervision for single-image Gaussian head reconstruction.
```

## Working Thesis

Current hypothesis:

```text
View selection and failure-aware filtering matter more than blindly adding more
diffusion pseudo views.
```

Current pseudo-view frontend:

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
```

Current unresolved claim:

```text
Filtered pseudo views look more reliable as 2D supervision, but have not yet
been proven to improve final downstream 3D reconstruction quality.
```

## Completed Milestones

| Gate | Status | Purpose | Main artifacts | Decision |
| --- | --- | --- | --- | --- |
| G0 | done | Bring up LAM and Zero123++ smoke runs | `experiments/metrics/smoke_runs_20260518.csv` | Environment can run both core baselines. |
| G1 | done | Build balanced first10 input set | `data_manifest.csv`, `experiments/inputs/first10/` | Dataset covers clean, side, glasses, hair, occlusion/low-quality cases. |
| G2 | done | Compare Zero123++ steps20 vs steps75 | `experiments/metrics/steps20_vs75_comparison_first10.csv` | More diffusion steps help some samples but do not solve failure modes. |
| G3 | done | Rank and budget pseudo views | `experiments/metrics/view_budget_selection_first10_steps20_75.csv` | Budget4 is a better compromise than blind budget6. |
| G4 | done | Test subject cutout input ablation | `experiments/metrics/cutout_input_ablation_observations_20260519.md` | Cutout improves average reliability and CLIP consistency. |
| G5 | done | Add trusted-region masks | `experiments/metrics/trusted_region_mask_observations_20260519.md` | Masking rejects full-photo/background rotation regions. |
| G6 | done | Add face identity filtering | `experiments/metrics/face_identity_filter_observations_20260519.md` | Cutout75 budget4 splits into identity, geometry-only, and reject roles. |
| G7 | done | Close RI3D first2 iter50 smoke | `experiments/metrics/ri3d_first2_160_iter50.csv` | Downstream loop runs, but render quality is smoke-level. |
| G8 | done, ambiguous | Run RI3D first2 iter500 gate | `experiments/metrics/ri3d_first2_160_iter500.csv` | Execution passed; method conclusion is not strong enough to scale data. |

## G8 Result

RI3D first2 160px iter500 completed for:

```text
raw75_all6
raw75_budget4
cutout75_budget4_masked
```

Samples:

```text
web_clean_frontal_03
web_clean_frontal_01
```

Published artifacts:

```text
experiments/metrics/ri3d_first2_160_iter500.csv
experiments/metrics/ri3d_first2_160_iter500_observations.md
experiments/figures/ri3d_first2_160_iter500_inputs.png
experiments/figures/ri3d_first2_160_iter500_renders.png
experiments/reconstructions/ri3d_first2_160_iter500/
```

Loss summary:

```text
web_clean_frontal_03:
  raw75_all6: 0.0195983
  raw75_budget4: 0.0147302
  cutout75_budget4_masked: 0.0157672

web_clean_frontal_01:
  raw75_all6: 0.0211399
  raw75_budget4: 0.0163405
  cutout75_budget4_masked: 0.0152439
```

Interpretation:

```text
raw75_all6 remains worse by training loss on both samples, supporting the
"do not blindly add all views" hypothesis.

cutout75_budget4_masked does not clearly dominate raw75_budget4: it wins
web_clean_frontal_01 by loss but loses web_clean_frontal_03 by loss.

Render sheets still show full-photo/background rotation artifacts. Therefore
G8 is an execution pass but a scientific ambiguity, not a proof that filtered
pseudo views already improve final 3D reconstruction.
```

## Active Milestone: G9

Name:

```text
Role-aware downstream supervision on first2
```

Purpose:

```text
Stop treating all selected pseudo views uniformly. Make downstream supervision
consume the roles discovered by masks and identity filtering:

identity_supervision -> visible face/identity/texture supervision
geometry_only        -> side/back/head-shape completion with low identity weight
identity_reject      -> excluded from identity supervision
mask_reject          -> excluded from geometry/texture supervision
```

Why G9 comes before first30/first50:

```text
G8 shows that simple cutout+mask filtering is not enough to produce a stable
downstream win. Scaling data before role-aware supervision would mostly scale
the same ambiguity.
```

Planned outputs:

```text
scripts/build_downstream_dataset.py role fields or a new role-aware RI3D prep script
experiments/ri3d_datasets/first2_roleaware/
experiments/metrics/ri3d_first2_roleaware_iter500.csv
experiments/metrics/ri3d_first2_roleaware_observations.md
experiments/figures/ri3d_first2_roleaware_renders.png
experiments/reconstructions/ri3d_first2_roleaware_iter500/
```

Pass criteria:

```text
1. Role-aware first2 jobs finish and export RGB/depth MP4s.
2. raw75_all6 remains a riskier baseline than selected-view variants.
3. role-aware cutout supervision visibly reduces background/full-photo rotation.
4. identity regions remain closer to the source face than geometry-only regions.
5. The next decision is clear: either run first2 at 1500 or expand to first10.
```

Failure criteria:

```text
1. Role-aware logic cannot be expressed with the current RI3D loader without
   invasive third-party changes.
2. Render quality remains dominated by bad pseudo-view geometry.
3. The method still cannot beat raw75_budget4 on first2 visual quality.
```

## Planned Milestones

| Gate | Planned milestone | Start condition | Stop condition |
| --- | --- | --- | --- |
| G9 | Role-aware downstream supervision on first2 | G8 exported and reviewed | Clear first2 visual/loss decision |
| G10 | first2 iter1500 confirmation | G9 positive or narrowly ambiguous | Same conclusion holds at longer optimization |
| G11 | Expand to first10 downstream | G9/G10 positive | Per-group result table across clean/side/glasses/hair/occlusion |
| G12 | Expand to first30/first50 | first10 trend stable | Main paper table and failure taxonomy stable |
| G13 | Paper packaging | Main result stable | Figures, tables, limitations, supplementary ready |

## Rollback And Sync Policy

```text
Keep raw RI3D PLYs and downstream working directories ignored.
Commit CSV/JSON/MD/PNG/MP4 result records.
Export any external/ri3d changes as patches under patches/ri3d/.
Create an exp/<topic>-YYYYMMDD branch if adding >100 MB publishable artifacts,
changing third-party behavior substantially, or replacing many result files.
```
