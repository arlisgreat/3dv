# Milestones

This file is the follow-up ledger for the 3DV sprint. `EXPERIMENTS.md` remains
the detailed result index; this file records the final goal, completed gates,
active decision point, and planned milestones.

Full experiment narrative and gate decision tree:

```text
docs/experiment_narrative_and_gates.md
```

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
old compressed paper goal was:

```text
Diagnose when diffusion pseudo views help or hurt single-image Gaussian head
reconstruction, and define a failure-aware pseudo-view supervision protocol.
```

G2-G19 show that this old route is useful only as a diagnostic/stop-loss study.
The current active goal is benchmark-first:

```text
Establish a licensed, auditable real-GT benchmark before making any
single-image/few-view head reconstruction-quality claim.
```

## Working Thesis

Current hypothesis after the benchmark pivot:

```text
No pseudo-view or RI3D result is credible as a method-quality claim until it is
tested against a licensed real-GT benchmark with real captured views, cameras,
masks, and GT mesh/point-cloud geometry.
```

Historical diagnostic pseudo-view frontend:

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
-> diagnostic-only unless a later visual gate passes
```

Current unresolved claim:

```text
Filtered pseudo views and role metadata are only candidate pools. They look
more reliable as 2D candidates, but G8-G14 show they have not been proven to be
valid reconstruction training supervision. The route is now invalid for
quality claims even after G21; `PASS_REAL_GT_BENCHMARK` only authorizes
real-GT adapter and reconstruction preflights, not renewed web pseudo-view/RI3D
training. G23/G24 pass only the local adapter and CPU file-contract gates. G25-G33
prove init, eval, numerical diagnosis, guarded train10, and post-guard eval
plumbing. G34-G36 close the current RI3D scaling route, confirm no additional
ready public/local real-GT benchmark is available, and reset the method direction
toward learned-prior/full-head Gaussian approaches. G37-G38 add explicit
model/data distribution and artifact-sync gates so that old candidate pools and
raw/private assets cannot slip back into the main claim. None of these is a
reconstruction-quality result.
```

## Mandatory Data Audit Gate

Every new milestone must pass a data audit gate before training or reconstruction.

```text
1. State the premise.
2. Run structural audit with scripts/audit_data_gate.py.
3. Generate a visual audit sheet for candidate PNGs.
4. Inspect generated images with VLM/manual visual checking.
5. Record PASS_REAL_GT_BENCHMARK, PASS_RECONSTRUCTION_TRAINING,
   PASS_DIAGNOSTIC_ONLY, or BLOCKED.
6. Update this file before any GPU experiment starts.
```

The current candidate-pool gate is:

```text
experiments/metrics/first10_candidate_pool_audit_gate_20260519.md
experiments/metrics/first10_candidate_pool_visual_audit_20260519.md
experiments/figures/first10_candidate_pool_audit_gate_20260519.png
experiments/figures/first10_candidate_pool_visual_audit_20260519.png
```

Current verdict:

```text
BLOCKED for reconstruction training.
The existing experiments/downstream_datasets candidate pools are invalid for
training. A later audit also found a severe Zero123++ 2x3/3x2 grid split bug
that contaminates historical per-view PNGs.
After correct 3x2 resplitting, the head-cutout pseudo views are still visibly
distorted, so web first10 remains diagnostic-only.
G21 now records PASS_REAL_GT_BENCHMARK on a local Multiface debug compact case.
This unlocks only the next real-GT preflight. It does not make any historical
web pseudo-view candidate pool valid for reconstruction training.
G22 correctly blocked direct GPU reconstruction because the old adapter did not
preserve real-camera assumptions. G23/G24 now repair the local adapter contract
enough to allow only the smallest RI3D init smoke on an explicitly selected
idle GPU. G28-G33 then clear two numerical NaN classes and confirm combined
guarded train10/eval still runs; they do not produce held-out quality gain or
authorize longer/default-loss training. G34-G36 turn that into the current
closure: no scaling from this RI3D route, no additional ready benchmark
locally, and no new method-quality milestone without a redesigned method plus
fresh data/VLM gate. G37 confirms that existing model/test pairs are
interpretable only as qualitative, diagnostic, or plumbing/numerical evidence.
G38 confirms the current repo-safe artifact sync set has no blocked raw/private
paths.
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
| G6 | done | Add face identity filtering | `experiments/metrics/face_identity_filter_observations_20260519.md` | Cutout75 budget4 splits pseudo-view candidates into identity, geometry-only, and reject roles. |
| G7 | done | Close RI3D first2 iter50 smoke | `experiments/metrics/ri3d_first2_160_iter50.csv` | Downstream loop runs, but render quality is smoke-level. |
| G8 | done, ambiguous | Run RI3D first2 iter500 gate | `experiments/metrics/ri3d_first2_160_iter500.csv` | Execution passed; method conclusion is not strong enough to scale data. |
| G9 | done, ambiguous | Non-invasive role-aware RI3D first2 iter500 | `experiments/metrics/ri3d_first2_roleaware_iter500.csv` | Role metadata/desaturation runs, but explicit role-weighted loss is still needed. |
| G10 | done, ambiguous | Explicit role-weighted RI3D first2 iter500 | `experiments/metrics/ri3d_first2_roleweighted_iter500.csv` | Scalar per-view role weights run, but spatial artifacts remain dominant. |
| G11 | done, negative | Spatial mask-aware RI3D first2 iter500 | `experiments/metrics/ri3d_first2_maskaware_iter500.csv` | Mask-aware loss runs and exports valid videos, but visual artifacts remain and recentering/priors are needed. |
| G12 | done, negative | Foreground-canonical mask ablation on first2 | `experiments/metrics/ri3d_first2_fghead_unmasked_iter500.csv` | Foreground scale/crop and mask-loss ablations improve inputs but still render card-like fragments. |
| G13 | done, partial positive | RI3D foreground point-cloud initialization filter | `experiments/metrics/ri3d_first2_fghead_pcdmask_iter500.csv` | Card backgrounds are reduced, but detached foreground fragments remain; a stronger FLAME/LAM structural prior is still needed. |
| G14 | done, diagnostic negative | FLAME proxy depth/conf prior on G13 | `experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv` | FLAME proxy priors run and export valid videos, but lose subject support and do not repair detached fragments. |
| G15a | done, blocked | Candidate-pool structural and visual audit | `experiments/metrics/first10_candidate_pool_audit_gate_20260519.md` | Existing downstream candidate pools fail the reconstruction-training premise. |
| G15b | done, probe input pass | Head-cutout input recovery gate | `experiments/metrics/first10_head_cutout_input_gate_20260519.md` | Tighter gray-background head crops pass only for a small generation probe, not reconstruction training. |
| G15c | done, blocked for training | Zero123++ 3x2 split correction and head-cutout probe | `experiments/metrics/zero123plus_grid_split_bug_20260519.md` | Correct 3x2 splitting fixes a major preprocessing bug, but pseudo views still show visible distortions and remain diagnostic-only. |
| G16a | superseded locally by G21 | GT dataset access gate | `experiments/metrics/gt_dataset_access_gate_20260519.md` | FaceScape remains sample/metadata-only; H3DS/full access is still external, but the immediate compact-case premise is now handled by G21. |
| G16a-local | done, intake-only | Real GT intake readiness gate | `experiments/metrics/g16a_real_gt_intake_readiness_20260520.md` | Historical intake gate; G21 later acquired and audited the Multiface debug compact case. Full/publishable artifact review remains pending. |
| G16b | done, positive-control pass | Mesh-derived repo-safe GT case | `experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md` | A CC0 realistic human head mesh was rendered into 8 deterministic RGB/depth/mask/normal views with camera metadata; visual gate passes only for synthetic positive-control work. |
| G17a | done, provenance pass | Positive-control case structural sanity | `experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.md` | Manifest, cameras, PNG dimensions, masks, MP4, and raw-mesh exclusion all pass; scope remains positive-control only. |
| G17b | done, smoke pass | RI3D positive-control iter10 smoke | `experiments/metrics/ri3d_gt_positive_control_iter10_observations.md` | Conversion, init, 10-iteration train, render, and MP4 export all pass; visual quality is smoke-only with ghosted fragments, so not a quality win. |
| G17c | done, quality fail | RI3D positive-control iter500 visual gate | `experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.md` | 500 iterations execute and export valid MP4s, but visual audit still shows ghosted fragments; current RI3D route is not a quality solution. |
| G18 | done, diagnostic-only | Corrected first10 failure taxonomy | `experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.md` | 60 corrected views audited; 10 identity, 37 geometry-only, 13 reject; budget4 still includes 8 severe/reject views. |
| G19 | done | Paper package and milestone closure | `experiments/metrics/paper_package_20260520.md` | Conservative claim, figure set, limitations, and closure state recorded. |
| G20 | done | Real-GT benchmark pivot and distribution audit | `experiments/metrics/real_gt_benchmark_pivot_20260520.md` | Old pseudo-view/RI3D route is invalid for quality claims; real-GT benchmark is the mandatory next gate. |
| G21 | done, local pass | Compact real-GT benchmark acquisition and VLM/manual gate | `experiments/metrics/g21_multiface_debug_gate_20260520.md`, `experiments/metrics/g21_real_gt_benchmark_gate_20260520.md`, `experiments/figures/g21_multiface_debug_mask_gate_20260520.png` | Multiface debug case passes local real-GT gate with 9 real views, cameras, masks, and mesh; raw RGB/mesh remain in `3dv_work` pending artifact review. |
| G22 | done, blocked before training | Real-GT reconstruction/evaluation preflight on G21 | `experiments/metrics/g22_real_gt_reconstruction_preflight_20260520.md` | Direct GPU training is blocked because the old RI3D/evaluation path did not preserve Multiface real-camera intrinsics, depth/confidence priors, or held-out/mesh metrics. |
| G23 | done, adapter pass | Local-only Multiface real-camera adapter | `experiments/metrics/g23_multiface_real_camera_adapter_20260520.md`, `experiments/figures/g23_multiface_adapter_depth_mask_summary_20260520.png` | Affine-normalized RI3D-readable adapter, masks, depth/conf arrays, and train/heldout split pass preflight; raw RGB/mesh remain local. |
| G24 | done, contract pass | CPU-only RI3D adapter file-contract gate | `experiments/metrics/g24_real_gt_adapter_contract_gate_20260520.md` | File contracts, centered intrinsics, local-only policy, train/test split, and metrics skeleton pass; no GPU training has started. |
| G25 | done, init-only pass | Minimal RI3D init-only smoke on the G24 adapter | `experiments/metrics/g25_ri3d_multiface_init_smoke_20260520.md` | RI3D loads the adapter and saves an iteration-1 point cloud with 67,410 points; no full training or quality claim. |
| G26 | done, eval smoke pass | Held-out render/evaluation smoke from the G25 point cloud | `experiments/metrics/g26_heldout_eval_smoke_20260520.md` | Held-out metrics execute without saving PNG/JPEG/MP4; PSNR 4.2685, LPIPS 0.5011 are init-only smoke numbers, not quality. |
| G27 | done, blocked | Tiny RI3D train10 numerical gate | `experiments/metrics/g27_ri3d_train10_numerical_gate_20260520.md` | Training executes but reports NaN loss even for plain L1-only; longer training and quality claims are blocked. |
| G28 | done, diagnostic blocked | RI3D loss-path numerical diagnostic | `experiments/metrics/g28_ri3d_loss_path_diagnosis_20260520.md` | Static losses are finite, but train-loop depth loss becomes NaN after optimizer steps; zero-weight loss branches can still poison total loss. |
| G29 | done, narrow numerical pass | Zero-weight loss guard and L1-only train10 rerun | `experiments/metrics/g29_zero_weight_loss_guard_train10_20260520.md`, `patches/ri3d/g29_zero_weight_loss_guard.patch` | L1-only train10 completes with finite loss after skipping zero-weight SSIM/silhouette/depth branches; no default-loss or quality claim. |
| G30 | done, eval smoke pass | Held-out eval from the G29 iteration-10 checkpoint | `experiments/metrics/g30_post_guard_heldout_eval_smoke_20260520.md` | Eval runs without saving identifiable media; metrics match G26 init-level smoke, so numerical execution is fixed but quality remains unproven. |
| G31 | done, component blocked | Guarded loss-component audit | `experiments/metrics/g31_guarded_loss_component_audit_20260520.md` | SSIM-only and silhouette-only train10 are finite; mono-depth-only is NaN with and without mask, blocking combined/default depth training. |
| G32 | done, numerical pass | Monodisp scale guard and depth-only rerun | `experiments/metrics/g32_monodisp_scale_guard_train10_20260520.md`, `patches/ri3d/g32_monodisp_scale_guard.patch` | Clamping monodisp scale denominators clears depth-only train10 NaNs; metrics remain init-level. |
| G33 | done, numerical/eval pass no quality gain | Combined guarded train10 and held-out eval | `experiments/metrics/g33_combined_guarded_train10_eval_20260520.md` | Combined guarded losses are finite, but held-out SSIM/PSNR/LPIPS match G26/G30 init-level values; quality remains unproven. |
| G34 | done, route-stop pass | Post-G33 route reset | `experiments/metrics/g34_post_g33_route_reset_20260520.md` | Longer RI3D training on the current adapter is closed as a method-quality milestone; no web pseudo-view candidate pool may become training data. |
| G35 | done, benchmark blocked | Public/stronger benchmark availability audit | `experiments/metrics/g35_public_benchmark_availability_20260520.md` | No additional ready local/public real-GT benchmark exists; H3DS/FaceScape/NeRSemble require access/license, and Multiface is the current local route only. |
| G36 | done, method direction pass | Method redesign and latest literature update | `experiments/metrics/g36_method_redesign_direction_20260520.md` | Next method work must be learned-prior/feed-forward/head-anchored with real-GT gates; pseudo views can only be audited conditional priors. |
| G37 | done, distribution pass no quality claim | Model/data distribution audit | `experiments/metrics/g37_model_data_distribution_audit_20260520.md` | LAM first10 is qualitative-only; pseudo-view/RI3D exports are diagnostic-only; Multiface G21-G33 is real-GT plumbing/numerical evidence without quality gain. |
| G38 | done, sync pass | Artifact sync gate | `experiments/metrics/g38_artifact_sync_gate_20260520.md`, `experiments/real_gt_benchmark/` | Current untracked repo-safe PNG/MP4/CSV/JSON/MD artifacts are sync candidates; blocked raw/private paths are zero. |

## Active Next Milestone

| Gate | Status | Purpose | Entry gate | Stop condition |
| --- | --- | --- | --- | --- |
| none | closed for current RI3D route | Stop scaling this RI3D setup as a method result | G34 route reset + G35 benchmark audit + G36 method redesign direction + G37 distribution audit + G38 sync gate | Open a new milestone only after a passing method premise, explicit model/data distribution statement, and real-GT/data/VLM gate; no longer-training milestone is authorized from current RI3D evidence. |

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

Semantic note:

```text
experiments/downstream_datasets/roleaware_cutout75_budget4/ is a candidate pool,
not validated training data.
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

## G13 Result

Name:

```text
Foreground point-cloud geometry-prior first2 repair
```

Purpose:

```text
Test whether G12's card artifact is seeded by RI3D initialization. G11/G12 only
used masks in supervision loss; RI3D still back-projected every image pixel into
the initial point cloud. G13 adds a gated point-cloud filter that keeps only
trusted foreground mask pixels and equalizes point count per view to preserve
RI3D's internal camera grouping assumption.
```

Patch:

```text
patches/ri3d/geometry_prior_pointcloud_filter.patch
scripts/run_ri3d_first2.sh adds PCD_MASK_FILTER=1 plumbing
external/ri3d dataset reader filters initial point cloud by frame mask/confidence
dynamic equal-points-per-view target avoids GaussianModel grouping failure
```

Published artifacts:

```text
experiments/metrics/geometry_prior_first2_plan.md
patches/ri3d/geometry_prior_pointcloud_filter.patch
experiments/metrics/ri3d_first2_fghead_pcdmask_iter500.csv
experiments/metrics/ri3d_first2_fghead_pcdmask_observations.md
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_fghead_pcdmask_vs_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_fghead_pcdmask_iter500/
```

Point-count and loss summary:

```text
web_clean_frontal_03:
  foreground points/view: 6766
  total splats: 27064
  final loss: 0.1139016

web_clean_frontal_01:
  foreground points/view: 9516
  total splats: 38064
  final loss: 0.2007467
```

Interpretation:

```text
G13 removes or reduces the gray rectangular card backgrounds visible in G12,
so the initialization hypothesis is partially supported.

However, render sheets still show detached foreground chunks rather than a
stable 3D head. Training loss is much larger because the objective and point
support changed, so G13 should be judged visually and structurally, not by loss
against G12.

Conclusion: foreground point-cloud filtering is a useful RI3D repair and should
remain available behind `PCD_MASK_FILTER=1`, but it is not a complete geometry
prior. The next milestone should use actual LAM/FLAME mesh/depth/silhouette
structure or pivot the paper toward a diagnostic negative result.
```

## G14 Result

Name:

```text
LAM/FLAME structural prior first2 repair
```

Purpose:

```text
Use the existing LAM tracking exports for the same first2 samples to generate a
stronger full-head structural proxy: FLAME mesh/depth/silhouette/normal or a
LAM-rendered positive-control baseline. Compare against G13 to decide whether
RI3D can be repaired enough for this paper sprint.
```

Implemented outputs:

```text
experiments/metrics/flame_geometry_prior_first2_plan.md
experiments/metrics/flame_geometry_prior_first2_observations.md
scripts/render_flame_proxy_priors.py
experiments/geometry_priors/flame_first2_proxy/
experiments/ri3d_datasets/first2_flame_proxy_pcdmask/
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_observations.md
experiments/figures/flame_geometry_prior_first2_proxy_sheet.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_flame_proxy_vs_pcdmask_iter500_renders.png
experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500/
```

Point-count and loss summary:

```text
web_clean_frontal_03:
  G13 foreground points/view: 6766
  G14 FLAME/conf points/view: 5341
  G13 final loss: 0.1139016
  G14 final loss: 0.1279854

web_clean_frontal_01:
  G13 foreground points/view: 9516
  G14 FLAME/conf points/view: 6358
  G13 final loss: 0.2007467
  G14 final loss: 0.2391389
```

Interpretation:

```text
The FLAME proxy prior is generated successfully and all four G14 RGB/depth MP4s
validate as 120 frames at 160x160.

However, simple FLAME proxy depth/conf does not improve final visual quality
beyond G13. It reduces some remaining card/background support but also removes
too much subject support: web_clean_frontal_03 loses upper-face texture in
several frames, and web_clean_frontal_01 remains split into detached fragments.

Conclusion: G14 is a diagnostic negative result. It supports the paper pivot
toward failure-aware pseudo-view supervision and failure taxonomy, not a claim
that RI3D plus generic FLAME proxy is already a strong reconstruction method.
```

## Final Closure State

Closure:

```text
No feasible local milestone remains unrecorded on the old route.
The old pseudo-view/RI3D route is closed as diagnostic-only and invalid for
quality claims.
G20 benchmark-first pivot is complete.
G21 compact real-GT benchmark acquisition is complete locally on a Multiface
debug case. Raw RGB/mesh assets remain local pending artifact review.
G22 real-GT reconstruction/evaluation preflight is blocked before training by
model/data adapter mismatch. G23/G24 repair the local-only adapter and file
contract enough for smoke testing. G25 passes RI3D init-only loading and point
cloud save, and G26 passes held-out eval plumbing without saving media. G27
blocks training because the RI3D train loop reports NaN loss even under plain
L1-only settings.
```

Final purpose:

```text
Do not claim solved single-image full-head reconstruction.
Use G2-G19 as failure taxonomy and stop-loss diagnostics.
Resume quality experiments only after each real-GT data, visual/VLM, adapter,
render/eval, and model/data distribution gate passes on the Multiface adapter
or an equivalent licensed benchmark. The active next gate is G28 loss-path
numerical diagnosis; no longer-run training should run before it.
```

Closure artifacts:

```text
docs/experiment_narrative_and_gates.md
experiments/metrics/milestone_data_audit_protocol_20260519.md
experiments/metrics/zero123plus_grid_split_bug_20260519.md
experiments/metrics/head_cutout_probe_resplit3x2_gate_20260519.md
experiments/metrics/gt_dataset_route_plan_20260519.md
experiments/metrics/gt_dataset_access_gate_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.json
experiments/metrics/g16a_real_gt_intake_readiness_20260520.md
experiments/metrics/g16a_real_gt_intake_readiness_20260520.json
experiments/metrics/real_gt_benchmark_pivot_20260520.md
experiments/metrics/real_gt_benchmark_pivot_20260520.json
experiments/metrics/gt_positive_control_route_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.json
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.json
experiments/gt_cases/wikimedia_blender_head_cc0/manifest.csv
experiments/gt_cases/wikimedia_blender_head_cc0/cameras.json
experiments/gt_cases/wikimedia_blender_head_cc0/views/*.png
experiments/gt_cases/wikimedia_blender_head_cc0/orbit_rgb.mp4
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/ri3d_datasets/gt_positive_control/
experiments/metrics/ri3d_gt_positive_control_iter10.csv
experiments/metrics/ri3d_gt_positive_control_iter10_observations.md
experiments/figures/ri3d_gt_positive_control_iter10_inputs.png
experiments/figures/ri3d_gt_positive_control_iter10_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter10/
experiments/metrics/wikimedia_blender_head_cc0_g17c_iter500_preflight_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_g17c_iter500_preflight_20260520.json
experiments/metrics/ri3d_gt_positive_control_iter500.csv
experiments/metrics/ri3d_gt_positive_control_iter500_observations.md
experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.md
experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.json
experiments/figures/ri3d_gt_positive_control_iter500_inputs.png
experiments/figures/ri3d_gt_positive_control_iter500_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter500/
experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.csv
experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.md
experiments/figures/first10_failure_taxonomy_resplit3x2_20260520.png
experiments/metrics/paper_package_20260520.md
experiments/metrics/milestone_closure_20260520.md
experiments/metrics/first10_head_cutout_input_gate_20260519.md
experiments/inputs/first10/head_cutouts/
experiments/figures/first10_head_cutout_inputs.png
experiments/metrics/downstream_candidate_pool_semantics_20260519.md
```

Stop criteria met:

```text
1. All feasible local gates have explicit artifacts.
2. PNG/MP4/CSV/JSON/MD result records are published in repo paths.
3. G16a is not silently treated as solved; G21 records only a local compact-case pass and raw identifiable assets remain outside git.
4. G17 records both execution success and visual quality failure.
5. G18 records corrected first10 taxonomy as diagnostic-only.
6. G19 records claims, figures, limitations, and next legitimate branches.
```

## Planned Milestones Closure

| Gate | Planned milestone | Closure |
| --- | --- | --- |
| G16a | Real GT dataset access gate | Blocked externally by license/access; next branch requires approved data. |
| G16a-local | Real GT intake/readiness gate | Complete as planning/schema gate; not a reconstruction pass. |
| G16b | Mesh-derived positive-control gate | Complete. |
| G17 | Compact positive-control reconstruction rerun | Complete for sprint: execution/export pass, visual quality fail. |
| G18 | first10 pseudo-view failure taxonomy | Complete, diagnostic-only. |
| G19 | Paper packaging | Complete. |

## Rollback And Sync Policy

```text
Keep raw RI3D PLYs and downstream working directories ignored.
Commit CSV/JSON/MD/PNG/MP4 result records.
Export any external/ri3d changes as patches under patches/ri3d/.
Create an exp/<topic>-YYYYMMDD branch if adding >100 MB publishable artifacts,
changing third-party behavior substantially, or replacing many result files.
```
