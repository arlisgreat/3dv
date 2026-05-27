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

The sharpened paper question after G77-G80 is:

```text
Can 2D hallucinations from pseudo multi-view generation become trustworthy
3D Gaussian reconstruction supervision if they are identity-anchored,
confidence-aware, and evaluated by rendering into real held-out cameras?
```

The project must not be positioned as:

```text
single image -> diffusion side/back views -> 3DGS -> qualitative render
```

That route is too weak against FaceLift / HQ Head / CAP4D / GAF-style baselines.
The valuable route is a supervision-validity study: single-image input, no real
multi-view images as supervision, identity/confidence-gated pseudo views, full-head
3DGS reconstruction, and strict real-camera evaluation on NeRSemble / RenderMe-360 /
Ava-256 / FaceScape-style held-out protocols.

## Working Thesis

Current hypothesis after the benchmark pivot:

```text
No pseudo-view or RI3D result is credible as a method-quality claim until it is
tested against a licensed real-GT benchmark with real captured views, cameras,
masks, and GT mesh/point-cloud geometry.
```

Current scientific hypothesis:

```text
Naive pseudo-view supervision is unreliable; identity-anchored and
confidence-aware pseudo-view supervision may become useful only if it improves
real held-out camera reconstruction over both direct single-image Gaussian and
naive pseudo-view pipelines.
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
raw/private assets cannot slip back into the main claim. G39-G45 open the first
learned-prior/feed-forward/head-anchored Gaussian smoke and geometry-diagnostic
loop on Multiface: LAM can run and export local geometry, but the results remain
diagnostic because native held-out RGB rendering is not evaluated. G50-G62 move
the benchmark route from credential-waiting to NeRSemble-backed data and metric
plumbing: official data is present with 79 explicit HTTP-404 exclusions, a
v2 compact case passes local visual audit, and an official NVS frame-0 adapter
plus copy-source held-out metric smoke passes. G57 produces finite LAM files
but G58 downgrades them because the `source_to_lam_sample` camera path is not a
verified NeRSemble held-out renderer and the visual sheet is mostly blank/crop
fragments. G59/G60 prove the real K/R/T renderer and evaluator using the
NeRSemble GT pointcloud as an oracle positive control. G61/G62 route the LAM
textured mesh through the same K/R/T path only after GT pointcloud bbox
alignment; this is diagnostic-only and visually broken, not method quality.
G63-G66 remove GT pointcloud alignment for LAM textured mesh via source-mask
alignment and true K/R/T rendering, but point/triangle mesh rendering remains
visually broken. G67/G69 expose a critical LAM export contract issue: the
`*_gs_offset.ply` x/y/z fields are offsets, not final Gaussian positions. G70
fixes that by combining `framework_img.obj` xyz with PLY opacity/scale/rotation
and LAM's native diff-gaussian rasterizer, producing the first plausible
source-only aligned native Gaussian true-K/R/T renders. G71/G73 show finite
held-out metrics and a repo-safe visual gate, but crop/alignment errors still
block a reconstruction-quality claim. G74-G76 rerun the same path from a
frontal NeRSemble source and confirm that simply changing the source camera is
not enough: one held-out view remains cropped and metrics are worse than G70.
G77 adds a source-mask plus eval-camera-frustum crop guard that uses no
held-out RGB/mask and no GT pointcloud, then renders the same LAM native
Gaussian into the G54 held-out cameras. G78/G79 are the first strong
method-direction positive under the real-GT gate: mean held-out mask IoU rises
to 0.900017 and private visual review no longer shows the severe side-view
crop. This validates the overall learned-prior/head-anchored Gaussian ->
true-K/R/T renderer -> held-out evaluator direction, but it remains
diagnostic-only pending multi-case validation and model/data-overlap review.
G81 must not merely scale that LAM diagnostic. It must test the actual paper
claim: whether identity-anchored, confidence-aware pseudo multi-view supervision
can produce more stable full-head 3DGS than direct single-image Gaussian and
naive pseudo-view supervision under the same real held-out camera evaluator.
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
6. For learned-prior/feed-forward methods, declare the model training/test
   distribution and held-out/geometry evaluation contract before interpreting
   outputs.
7. Update this file before any GPU experiment starts.
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
paths. G39 passes the learned-prior method premise under real-GT/data/VLM gates.
G40 runs LAM-20K on one local Multiface train view and records only hashes and
manual audit because the derived media are identifiable/private. G40 also blocks
the repo-safe CC0 positive control as a LAM input-distribution smoke because the
point-splat render fails face tracking. G41 records the evaluation contract:
no learned-prior quality claim is allowed until the method can render held-out
Multiface cameras or export geometry for GT metrics. G42 verifies that LAM can
export local PNG/MP4/PLY/OBJ artifacts, but keeps private identifiable media
under `3dv_work` and records repo-safe hashes only. G43 adds a weak
bbox-normalized LAM-mesh-vs-Multiface-mesh sanity check; it can catch a
catastrophic geometry/export failure, but it is not a camera-aligned or metric
GT reconstruction result. G44 fits one similarity/ICP transform from the LAM
shaped mesh into the Multiface GT mesh frame and records a stronger aligned
geometry diagnostic; it still lacks held-out camera rendering, verified surface
correspondence, and a publishable benchmark artifact package. G45 renders the
G44-aligned LAM mesh into the three held-out Multiface cameras and compares
silhouette/depth against GT-derived masks/z-buffers. This is the first
held-out-camera learned-prior geometry diagnostic, but still not RGB
reconstruction quality because it depends on similarity/ICP alignment and does
not render native LAM Gaussians or held-out RGB appearance. G47 clones official
benchmark tool repos and prepares local ignored dataset roots for FaceScape,
NeRSemble, and H3DS, while recording that NeRSemble/H3DS remain
credential-gated. G48 checks the future benchmark intake contract: official
tools and raw-data policy are ready, but method-quality work stays blocked
until user-provided NeRSemble/H3DS credentials pass data/VLM/distribution gates.
G49 records project completion probability by scope, separating the repo-safe
diagnostic package from the larger RGB method-quality and proposal-level system.
G50/G51 record official NeRSemble partial intake and full download launch. G52
closes the download with 156260 ok manifest paths and 79 final HTTP-404
exclusions, mainly participant 545/546/548 cam_222200041. G53 passes official
benchmark protocol preflight and selects v2 participant 017 EXP-1-head as a
full 16-camera compact case after a local visual/VLM audit sheet. G54 prepares
an official NVS participant 388 GLASSES frame-0 local adapter with 13 visible
views, alpha maps, cameras, and a 673854-point pointcloud. G55 proves the
held-out RGB/mask metric harness with a deliberately weak copy-source baseline;
that is plumbing only, not a reconstruction method. G56 correctly blocks
method-quality evaluation until a real method output can be rendered into the
exact NeRSemble held-out cameras; LAM motion-camera MP4s are not acceptable
substitutes. G57 then confirms the risk: a LAM `source_to_lam_sample` render can
produce finite files, but G58 marks it diagnostic-only because the camera
contract fails and the held-out predictions are mostly blank/cropped. G59/G60
establish a true-KRT pointcloud oracle positive control, proving that the G54
camera/evaluator path itself works. G61/G62 render a LAM textured mesh through
the same path only with GT pointcloud bbox alignment; the result is nonempty but
texture-broken and remains diagnostic-only. G63/G64 try source-mask-only LAM
mesh true-KRT renders and evaluator; G65/G66 replace point splats with triangle
rasterization. Both are diagnostic because texture/appearance remains broken.
G67/G69 test Gaussian PLY point/native rendering but reveal that
`gs_offset.ply` stores offsets rather than final xyz. G70 fixes the coordinate
contract by using `framework_img.obj` xyz plus PLY opacity/scale/rotation and
the LAM native rasterizer. G71/G73 are the current best method-direction
evidence: the renderer/evaluator path works and produces recognizable heads,
but mask IoU is only 0.498004 mean and the private sheet shows crop/alignment
risk. G74-G76 show that a frontal source alone still fails the crop gate. G77
adds an eval-camera-frustum guard that is allowed to use K/R/T metadata but not
held-out RGB/mask or GT pointcloud; G78/G79 improve mean mask IoU to 0.900017
and pass the stricter post-hoc mask/visual gate. Method-quality claims are now
blocked by scale and distribution limits rather than by the renderer/evaluator
plumbing itself.
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
| G39 | done, method gate pass local-only | Learned-prior/feed-forward/head-anchored Gaussian method gate | `experiments/metrics/g39_learned_prior_method_gate_20260520.md` | Real-GT/data/VLM/distribution gates authorize only local LAM smoke and repo-safe positive controls; no quality claim. |
| G40 | done, local smoke pass no quality claim | LAM-20K learned-prior smoke after G39 | `experiments/metrics/g40_learned_prior_lam_smoke_20260520.md`, `patches/lam/torch26_vgghead_torchscript_load.patch` | Multiface train-view LAM smoke succeeds locally with private media hashes only; CC0 point-splat positive-control input is blocked by LAM face tracking. |
| G41 | done, eval contract pass/block | Learned-prior held-out evaluation contract | `experiments/metrics/g41_learned_prior_eval_contract_20260520.md` | Current LAM wrapper cannot support held-out camera-aligned or geometry metrics; next work must implement/export those before a quality claim. |
| G42 | done, export pass no quality claim | LAM local frame/geometry export gate | `experiments/metrics/g42_lam_export_gate_20260520.md` | LAM exports 50 PNG frames, 50 per-frame PLYs, canonical Gaussian PLY, MP4, and mesh OBJs locally; private media remain under `3dv_work`, and the run is still not held-out camera aligned. |
| G43 | done, geometry sanity pass no quality claim | Weak normalized LAM mesh vs Multiface GT mesh sanity | `experiments/metrics/g43_lam_geometry_sanity_gate_20260520.md` | Bbox-normalized nearest-neighbor sanity is non-catastrophic, but independent normalization and missing camera/scale alignment block any reconstruction-quality claim. |
| G44 | done, aligned geometry diagnostic pass no quality claim | Similarity/ICP-aligned LAM mesh vs Multiface GT mesh diagnostic | `experiments/metrics/g44_lam_similarity_geometry_gate_20260520.md` | Symmetric mean nearest-neighbor distance after similarity/ICP alignment is 17.164824 GT units, normalized 0.037132 by GT bbox diagonal; this is diagnostic only, not final reconstruction quality. |
| G45 | done, held-out geometry diagnostic pass no RGB quality claim | Render G44-aligned LAM mesh into Multiface held-out cameras | `experiments/metrics/g45_lam_heldout_camera_geometry_gate_20260520.md` | Held-out mask IoU mean 0.708083 and depth mean error 0.029646 of GT median pass geometry diagnostics; no held-out RGB/SOTA claim. |
| G46 | done, forecast pass | Project completion forecast and risk register | `experiments/metrics/g46_project_completion_forecast_20260520.md` | Repo-safe diagnostic package can close in roughly 2-4 focused work days; RGB method-quality or full proposal scope needs more work and user decisions. |
| G47 | done, access/tooling partial pass | Benchmark dataset access/download preparation | `experiments/metrics/g47_benchmark_dataset_access_download_20260520.md`, `datasets/access_manifest.tsv` | FaceScape SVFR/sample and official NeRSemble/H3DS tool repos are local; NeRSemble/H3DS data remain blocked until official credentials arrive. |
| G48 | done, intake preflight pass data blocked | Future NeRSemble/H3DS benchmark intake contract | `experiments/metrics/g48_benchmark_intake_preflight_20260520.md`, `scripts/benchmark_intake_preflight.py` | Official tool repos, ignored raw-data roots, required credentials, and benchmark contracts are preconfigured; no fake benchmark result is created. |
| G49 | done, probability pass | Project completion probability by scope | `experiments/metrics/g49_project_completion_probability_20260520.md` | Diagnostic package probability is high; method-quality result depends on native held-out rendering and official NeRSemble/H3DS data access. |
| G50 | done, partial intake pass | Official NeRSemble SVFR and v2 metadata/calibration intake | `experiments/metrics/g50_nersemble_official_intake_20260524.md`, `scripts/download_nersemble_official.py` | SVFR RGB inputs and v2 metadata/calibrations were ready; NVS/mono/full v2 remained resumable. |
| G51 | done, transfer launch | Official NeRSemble full download launch | `experiments/metrics/g51_nersemble_full_download_launch_20260524.md`, `datasets/nersemble_full_manifest.tsv` | Full v2/benchmark download was launched with 128 workers; manifest stays local/ignored. |
| G52 | done, intake pass with exclusions | NeRSemble full download integrity gate | `experiments/metrics/g52_nersemble_download_integrity_gate_20260527.md`, `scripts/nersemble_download_integrity_gate.py` | 1.4TB v2 and 3.2GB benchmark data are present; 156260 manifest paths are ok and 79 final HTTP-404 paths must be excluded. |
| G53 | done, visual/data gate pass local-only | NeRSemble benchmark protocol and compact v2 case gate | `experiments/metrics/g53_nersemble_compact_case_gate_20260527.md`, `scripts/nersemble_compact_case_gate.py` | Official NVS/Mono/SVFR protocol assets pass; v2 participant 017 EXP-1-head all-16-camera sheet passes local visual audit but identifiable sheet remains under `3dv_work`. |
| G54 | done, adapter preflight pass local-only | Official NeRSemble NVS frame-0 local adapter | `experiments/metrics/g54_nersemble_nvs_frame0_adapter_preflight_20260527.md`, `experiments/figures/g54_nersemble_nvs_frame0_mask_audit_20260527.png` | Participant 388 GLASSES frame 0 yields 13 visible RGB/alpha views, cameras, and a 673854-point pointcloud; raw RGB stays local. |
| G55 | done, metric harness smoke pass | NeRSemble held-out RGB/mask eval harness smoke | `experiments/metrics/g55_nersemble_heldout_eval_harness_smoke_20260527.md`, `scripts/nersemble_heldout_copy_eval_smoke.py` | A copy-source baseline gives finite held-out metrics (mean PSNR 11.730165, SSIM 0.364646); this is metric plumbing only. |
| G56 | done, blocked correctly | NeRSemble method readiness and distribution gate | `experiments/metrics/g56_nersemble_method_readiness_gate_20260527.md`, `scripts/nersemble_method_readiness_gate.py` | LAM-on-NeRSemble is in-domain with possible dataset overlap; prediction files now exist, but G58 renderer-contract audit fails, so method-quality evaluation remains blocked. |
| G57 | done, finite but not quality | LAM source-to-sample camera render into G55 evaluator | `experiments/metrics/g57_lam_nersemble_heldout_eval_20260527.md`, `scripts/lam_render_nersemble_cameras.py` | Finite metrics are produced, but mean PSNR is 3.683666 and mean prediction-mask IoU is 0.035656 after the stricter mask fix; G58 controls interpretation. |
| G58 | done, diagnostic downgrade | LAM renderer contract and visual gate audit | `experiments/metrics/g58_nersemble_lam_renderer_contract_audit_20260527.md`, `experiments/figures/g57_g61_nersemble_render_mask_audit_20260527.png`, `scripts/audit_nersemble_lam_renderer_contract.py` | `source_to_lam_sample` is not a verified NeRSemble K/R/T renderer; held-out predictions are blank/cropped. G57 is diagnostic-only. |
| G59 | done, oracle renderer pass | True NeRSemble K/R/T pointcloud renderer positive control | `experiments/metrics/g59_nersemble_pointcloud_true_krt_renderer_20260527.md`, `scripts/render_nersemble_pointcloud_heldout.py` | The official frame-0 pointcloud projects into source/eval cameras with plausible view direction and nonempty coverage; this validates camera plumbing, not a method. |
| G60 | done, oracle eval pass | Held-out evaluator on G59 pointcloud oracle renders | `experiments/metrics/g60_nersemble_pointcloud_oracle_eval_20260527.md` | Oracle pointcloud visible-heldout metrics are finite (mean PSNR 5.343938, mask IoU 0.553924); sparse pointcloud RGB remains an evaluator/camera sanity check. |
| G61 | done, diagnostic render pass | LAM textured mesh through true K/R/T after GT bbox alignment | `experiments/metrics/g61_lam_mesh_true_krt_bbox_aligned_20260527.md`, `scripts/render_lam_mesh_nersemble_true_krt.py` | LAM mesh renders are nonempty but use GT pointcloud bbox alignment and show broken texture/appearance; diagnostic-only. |
| G62 | done, diagnostic eval pass | Held-out evaluator on G61 LAM mesh true-KRT diagnostic renders | `experiments/metrics/g62_lam_mesh_true_krt_eval_20260527.md` | Finite metrics (mean PSNR 6.894329, mask IoU 0.708950) do not validate the method because the visual result is broken and GT-aligned. |
| G63 | done, diagnostic render pass | LAM textured mesh true-KRT source-mask alignment | `experiments/metrics/g63_lam_mesh_true_krt_source_aligned_20260527.md`, `scripts/render_lam_mesh_nersemble_source_aligned.py` | Removes GT pointcloud alignment and produces nonempty renders, but point-splat texture is visibly broken. |
| G64 | done, diagnostic eval pass | Held-out evaluator on G63 source-mask mesh renders | `experiments/metrics/g64_lam_mesh_source_aligned_eval_20260527.md` | Finite metrics (mean PSNR 5.806210, mask IoU 0.422768) remain diagnostic because visual quality fails. |
| G65 | done, diagnostic render pass | Triangle-rasterized source-mask LAM mesh true-KRT renders | `experiments/metrics/g65_lam_mesh_source_aligned_triangle_render_20260527.md` | Triangle rasterization removes point-splat noise but still shows swirled/broken texture. |
| G66 | done, diagnostic eval pass | Held-out evaluator on G65 triangle mesh renders | `experiments/metrics/g66_lam_mesh_source_aligned_triangle_eval_20260527.md` | Finite metrics (mean PSNR 5.860206, mask IoU 0.417768) do not validate the mesh route. |
| G67 | done, diagnostic render pass | LAM Gaussian PLY point approximation through true K/R/T | `experiments/metrics/g67_lam_gaussian_source_aligned_render_20260527.md`, `scripts/render_lam_gaussian_nersemble_source_aligned.py` | Simple point rendering is sparse; it also helped expose that PLY x/y/z are offsets. |
| G69 | done, invalidated diagnostic | Native Gaussian renderer before xyz contract fix | `experiments/metrics/g69_lam_native_gaussian_source_aligned_render_20260527.md`, `scripts/render_lam_native_gaussian_nersemble_source_aligned.py` | Native rasterizer can run, but this run used offset coordinates and is superseded by G70. |
| G70 | done, best diagnostic positive | Native LAM Gaussian true-KRT render with corrected xyz source | `experiments/metrics/g70_lam_native_gaussian_source_aligned_xyz_render_20260527.md` | Uses `framework_img.obj` xyz plus PLY opacity/scale/rotation and source-mask alignment; renders recognizable heads without GT/held-out alignment. |
| G71 | done, diagnostic eval pass | Held-out evaluator on G70 corrected native Gaussian renders | `experiments/metrics/g71_lam_native_gaussian_source_aligned_xyz_eval_20260527.md` | Mean PSNR 6.318184 and mask IoU 0.498004; evaluator works but crop/alignment risk remains. |
| G72 | done, blocked | Source-camera prealignment without LAM y/z convention fix | `experiments/metrics/g72_lam_native_gaussian_source_camera_aligned_render_20260527.md` | Source mask IoU is 0, so this camera-frame mapping is invalid. |
| G72F | done, diagnostic negative | Source-camera prealignment with LAM y/z flip | `experiments/metrics/g72f_lam_native_gaussian_source_camera_aligned_yzflip_render_20260527.md` | Source gate passes numerically, but private visual audit shows source/held-out cameras are semantically wrong or off-frame. |
| G73 | done, visual gate partial pass | Visual/mask gate for G70/G71 native Gaussian renders | `experiments/metrics/g73_lam_native_gaussian_visual_gate_20260527.md`, `experiments/figures/g73_lam_native_gaussian_source_aligned_mask_audit_20260527.png`, `scripts/audit_nersemble_method_visual_gate.py` | Renderer path is technically working and partially validates the direction, but method-quality claim is blocked by crop/alignment. |
| G74 | done, diagnostic render pass | LAM native Gaussian true-KRT render from frontal source 220700191 | `experiments/metrics/g74_lam_source220700191_inference_20260527.md`, `experiments/metrics/g74_lam_native_gaussian_source220700191_render_20260527.md` | LAM export and native rendering work from a second real source, but source-mask-only alignment still leaves crop risk. |
| G75 | done, diagnostic eval pass | Held-out evaluator on G74 frontal-source renders | `experiments/metrics/g75_lam_native_gaussian_source220700191_eval_20260527.md` | Finite metrics, but mean PSNR 5.885673 and mask IoU 0.458910 are worse than G70/G71. |
| G76 | done, visual gate partial pass | Visual/mask gate for G74/G75 | `experiments/metrics/g76_lam_native_gaussian_source220700191_visual_gate_20260527.md`, `experiments/figures/g76_lam_native_gaussian_source220700191_mask_audit_20260527.png` | Severe side-view crop improves only partially; method-quality claim remains blocked. |
| G77 | done, render pass current best | Source-mask plus eval-camera-frustum crop guard render | `experiments/metrics/g77_lam_native_gaussian_source220700191_frustum_guard_render_20260527.md`, `scripts/render_lam_native_gaussian_nersemble_source_aligned.py` | Uses held-out camera K/R/T metadata only as a frustum guard, not held-out RGB/mask or GT geometry; renders noncropped held-out predictions. |
| G78 | done, eval pass current best | Held-out evaluator on G77 frustum-guard renders | `experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.md` | Mean PSNR 12.690455 and mask IoU 0.900017, a large improvement over G75 and G71. |
| G79 | done, visual gate pass diagnostic | Visual/mask gate for G77/G78 | `experiments/metrics/g79_lam_native_gaussian_source220700191_frustum_guard_visual_gate_20260527.md`, `experiments/figures/g79_lam_native_gaussian_source220700191_frustum_guard_mask_audit_20260527.png`, `scripts/audit_nersemble_method_visual_gate.py` | Current best method-direction positive: no gross crop in private review and high mask overlap, but still diagnostic pending multi-case validation and distribution review. |
| G80 | done, sync pass | Artifact sync gate for G74-G79 repo-safe outputs | `experiments/metrics/g80_artifact_sync_gate_20260527.md`, `scripts/artifact_sync_gate.py` | 18 new repo-safe sync candidates and 0 blocked private/raw paths; checkpoint committed and pushed. |

## Active Next Milestone

| Gate | Status | Purpose | Entry gate | Stop condition |
| --- | --- | --- | --- | --- |
| G81 | active next | Reposition and test pseudo-view supervision validity: identity-anchored, confidence-aware pseudo multi-view supervision -> full-head 3DGS -> real held-out camera evaluation | `experiments/metrics/g81_pseudo_supervision_repositioning_20260527.md`; G77-G80 validate the real-GT renderer/evaluator/sync harness; G15-G20 prove naive pseudo-view candidate pools are unsafe | Compare direct single-image Gaussian, naive pseudo-view supervision, and identity/confidence-aware pseudo supervision on the same real-GT held-out cameras. Pass only if the gated pseudo-supervision variant improves stability/metrics/visual gate without using real multi-view images as supervision; otherwise record a negative result. |

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
