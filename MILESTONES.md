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
Filtered pseudo views and role metadata look more reliable as 2D supervision,
but have not yet been proven to improve final downstream 3D reconstruction
quality without explicit role-weighted losses.
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
| G9 | done, ambiguous | Non-invasive role-aware RI3D first2 iter500 | `experiments/metrics/ri3d_first2_roleaware_iter500.csv` | Role metadata/desaturation runs, but explicit role-weighted loss is still needed. |
| G10 | done, ambiguous | Explicit role-weighted RI3D first2 iter500 | `experiments/metrics/ri3d_first2_roleweighted_iter500.csv` | Scalar per-view role weights run, but spatial artifacts remain dominant. |
| G11 | done, negative | Spatial mask-aware RI3D first2 iter500 | `experiments/metrics/ri3d_first2_maskaware_iter500.csv` | Mask-aware loss runs and exports valid videos, but visual artifacts remain and recentering/priors are needed. |
| G12 | done, negative | Foreground-canonical mask ablation on first2 | `experiments/metrics/ri3d_first2_fghead_unmasked_iter500.csv` | Foreground scale/crop and mask-loss ablations improve inputs but still render card-like fragments. |

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

## G9 Result

RI3D first2 role-aware iter500 completed for:

```text
roleaware_cutout75_budget4
```

Samples:

```text
web_clean_frontal_03: 2 identity_supervision + 2 geometry_only
web_clean_frontal_01: 4 identity_supervision
```

Published artifacts:

```text
scripts/build_roleaware_downstream_dataset.py
experiments/downstream_datasets/roleaware_cutout75_budget4/
experiments/ri3d_datasets/first2_roleaware/
experiments/metrics/ri3d_first2_roleaware_iter500.csv
experiments/metrics/ri3d_first2_roleaware_observations.md
experiments/figures/ri3d_first2_roleaware_iter500_inputs.png
experiments/figures/ri3d_first2_roleaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleaware_iter500/
```

Loss summary:

```text
web_clean_frontal_03:
  raw75_budget4: 0.0147302
  cutout75_budget4_masked: 0.0157672
  roleaware_cutout75_budget4: 0.0157378

web_clean_frontal_01:
  raw75_budget4: 0.0163405
  cutout75_budget4_masked: 0.0152439
  roleaware_cutout75_budget4: 0.0154150
```

Interpretation:

```text
The role-aware data path is now reproducible and exports all expected MP4/PNG/CSV/JSON artifacts.

web_clean_frontal_03 is slightly better than cutout75_budget4_masked by loss,
but still worse than raw75_budget4. web_clean_frontal_01 is better than
raw75_budget4 but slightly worse than cutout75_budget4_masked.

The first-frame render sheet still shows fragmented/rotated photo-card artifacts.
Therefore G9 is an infrastructure pass but not a final method win.

Next step: make RI3D training loss explicitly consume role weights. Metadata
and geometry-only desaturation alone are not enough.
```

## G10 Result

RI3D first2 role-weighted iter500 completed for:

```text
roleaware_cutout75_budget4
```

Patch:

```text
patches/ri3d/role_weighted_loss.patch
transforms.json -> CameraInfo -> Camera -> cal_loss
identity_supervision: role_rgb_weight=1.0, role_depth_weight=1.0
geometry_only: role_rgb_weight=0.25, role_depth_weight=1.0
reject roles: zero weights and excluded before current first2 training
```

Published artifacts:

```text
patches/ri3d/role_weighted_loss.patch
experiments/ri3d_datasets/first2_roleweighted/
experiments/metrics/ri3d_first2_roleweighted_iter500.csv
experiments/metrics/ri3d_first2_roleweighted_observations.md
experiments/figures/ri3d_first2_roleweighted_iter500_inputs.png
experiments/figures/ri3d_first2_roleweighted_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleweighted_iter500/
```

Loss summary:

```text
web_clean_frontal_03:
  roleweighted_cutout75_budget4: 0.0085665
  roleaware_cutout75_budget4: 0.0157378
  raw75_budget4: 0.0147302

web_clean_frontal_01:
  roleweighted_cutout75_budget4: 0.0152099
  roleaware_cutout75_budget4: 0.0154150
  cutout75_budget4_masked: 0.0152439
```

Interpretation:

```text
The web_clean_frontal_03 weighted loss drop is not directly comparable because
2/4 views have only 0.25 RGB weight. web_clean_frontal_01 is more comparable
because all four views are identity_supervision and slightly improves over G9.

All MP4s render and validate as 120 frames at 160x160. However, the first-frame
render sheet still shows fragmented/rotated photo-card artifacts similar to G9.

Conclusion: scalar per-view role weighting is not enough. The next milestone
must use spatial foreground/mask-aware loss or a stronger geometry prior before
expanding beyond first2.
```

## G11 Result

RI3D first2 mask-aware iter500 completed for:

```text
roleaware_cutout75_budget4
```

Patch:

```text
patches/ri3d/mask_aware_loss.patch
transforms.json mask_path -> CameraInfo.mask -> Camera.mask -> masked cal_loss
--use_mask explicitly gates mask loading so older baselines do not change silently
masked RGB/SSIM foreground loss + silhouette BCE + masked monodepth indexing
```

Published artifacts:

```text
experiments/ri3d_datasets/first2_maskaware/
experiments/metrics/ri3d_first2_maskaware_iter500.csv
experiments/metrics/ri3d_first2_maskaware_observations.md
experiments/figures/ri3d_first2_maskaware_iter500_inputs.png
experiments/figures/ri3d_first2_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_maskaware_iter500/
```

Loss summary:

```text
web_clean_frontal_03:
  maskaware_cutout75_budget4: 0.0084686
  roleweighted_cutout75_budget4: 0.0085665
  raw75_budget4: 0.0147302

web_clean_frontal_01:
  maskaware_cutout75_budget4: 0.0155180
  roleweighted_cutout75_budget4: 0.0152099
  cutout75_budget4_masked: 0.0152439
```

Interpretation:

```text
The loss values are not directly comparable to unmasked full-image losses
because G11 changes the objective to foreground-masked RGB/SSIM plus silhouette.

All four MP4s validate as 120 frames at 160x160. However, the render sheet still
shows small fragmented/rotated photo-card foregrounds and large blank regions.
Spatial masking prevents background pixels from supervising RGB, but it does
not canonicalize subject scale/position and does not add a structural full-head
prior.

Conclusion: G11 is an implementation pass and a visual-method failure. The next
milestone should not be first10 expansion or iter1500 confirmation. It should
first test foreground recentering/mask ablations or a stronger geometry prior.
```

## G12 Result

RI3D first2 foreground-canonical ablations completed for:

```text
roleaware_cutout75_budget4
```

Branches:

```text
first2_fgcenter_maskaware: largest connected mask component, square crop, USE_MASK=1
first2_fgcenter_unmasked: same largest-square data, USE_MASK=0
first2_fghead_maskaware: mask_width_anchor head/upper-body crop, USE_MASK=1
first2_fghead_unmasked: same head/upper-body data, USE_MASK=0
```

Published artifacts:

```text
experiments/ri3d_datasets/first2_fgcenter_maskaware/
experiments/ri3d_datasets/first2_fghead_maskaware/
experiments/metrics/ri3d_first2_fgcenter_maskaware_iter500.csv
experiments/metrics/ri3d_first2_fgcenter_maskaware_observations.md
experiments/metrics/ri3d_first2_fgcenter_unmasked_iter500.csv
experiments/metrics/ri3d_first2_fgcenter_unmasked_observations.md
experiments/metrics/ri3d_first2_fghead_maskaware_iter500.csv
experiments/metrics/ri3d_first2_fghead_maskaware_observations.md
experiments/metrics/ri3d_first2_fghead_unmasked_iter500.csv
experiments/metrics/ri3d_first2_fghead_unmasked_observations.md
experiments/figures/ri3d_first2_fgcenter_maskaware_iter500_renders.png
experiments/figures/ri3d_first2_fgcenter_unmasked_iter500_renders.png
experiments/figures/ri3d_first2_fghead_maskaware_iter500_renders.png
experiments/figures/ri3d_first2_fghead_unmasked_iter500_renders.png
experiments/reconstructions/ri3d_first2_fgcenter_maskaware_iter500/
experiments/reconstructions/ri3d_first2_fgcenter_unmasked_iter500/
experiments/reconstructions/ri3d_first2_fghead_maskaware_iter500/
experiments/reconstructions/ri3d_first2_fghead_unmasked_iter500/
```

Loss summary:

```text
web_clean_frontal_03:
  fgcenter_maskaware: 0.0093817
  fgcenter_unmasked: 0.0092889
  fghead_maskaware: 0.0091152
  fghead_unmasked: 0.0092128

web_clean_frontal_01:
  fgcenter_maskaware: 0.0159728
  fgcenter_unmasked: 0.0157918
  fghead_maskaware: 0.0165959
  fghead_unmasked: 0.0163692
```

Interpretation:

```text
G12 improves the input sheets. The mask_width_anchor branch produces a much
more stable head/upper-body scale than G11 and removes disconnected foreground
fragments from the training RGB images.

However, every G12 render sheet still shows rotated card-like planes and
detached chunks. The USE_MASK=0 branches are visually similar to USE_MASK=1,
so the failure is not only caused by masked RGB/SSIM or silhouette loss.

Conclusion: foreground canonicalization is useful data hygiene but not enough
to make RI3D pseudo-view supervision produce a stable 3D head. The next step
must add a structural geometry prior, not more first2 crop/mask variants.
```

## Active Milestone: G13

Name:

```text
Geometry-prior first2 repair
```

Purpose:

```text
Inject a stronger structure signal after G8-G12 all show that filtered
pseudo-view RGB/mask supervision alone collapses into card-like geometry.
Start with the lowest-risk local prior: LAM/FLAME/full-head silhouette, depth,
normal, or initialization evidence that can be generated from existing first2
inputs without retraining a new model.
```

Planned outputs:

```text
experiments/metrics/geometry_prior_first2_plan.md
experiments/metrics/geometry_prior_first2_observations.md
experiments/figures/geometry_prior_first2_*.png
experiments/reconstructions/geometry_prior_first2_*/
patches/ri3d/geometry_prior_*.patch if RI3D loss/init is changed
```

Pass criteria:

```text
1. A LAM/FLAME/full-head structural proxy is generated for the same first2 samples.
2. The proxy can be consumed without overwriting G8-G12 artifacts.
3. Render sheets reduce card-like planes or clearly explain why the RI3D path is
   the wrong downstream baseline for this paper sprint.
```

Failure criteria:

```text
1. Available LAM/FLAME outputs cannot provide a usable first2 structural proxy.
2. Geometry-prior integration requires a large risky rewrite.
3. Outputs still collapse to cards/fragments, pushing the paper framing toward a
   diagnostic negative result rather than a reconstruction method win.
```

## Planned Milestones

| Gate | Planned milestone | Start condition | Stop condition |
| --- | --- | --- | --- |
| G13 | Geometry-prior first2 repair | G12 fails or remains ambiguous | LAM/FLAME/normal/depth prior either helps or is rejected |
| G14 | Expand to first10 downstream | G12/G13 positive | Per-group result table across clean/side/glasses/hair/occlusion |
| G15 | Expand to first30/first50 | first10 trend stable | Main paper table and failure taxonomy stable |
| G16 | Paper packaging | Main result stable | Figures, tables, limitations, supplementary ready |

## Rollback And Sync Policy

```text
Keep raw RI3D PLYs and downstream working directories ignored.
Commit CSV/JSON/MD/PNG/MP4 result records.
Export any external/ri3d changes as patches under patches/ri3d/.
Create an exp/<topic>-YYYYMMDD branch if adding >100 MB publishable artifacts,
changing third-party behavior substantially, or replacing many result files.
```
