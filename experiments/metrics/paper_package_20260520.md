# G19 Paper Package

Date: 2026-05-20

## Final Scope

```text
Failure-aware pseudo-view supervision as diagnostic evidence only, followed by
a mandatory real-GT benchmark gate for any reconstruction-quality claim.
```

This paper sprint does not claim solved single-image full-head reconstruction.
It packages a diagnostic protocol and the evidence that generic diffusion
pseudo views must be gated before they can supervise 3D reconstruction.
After G20/G21, the old pseudo-view/RI3D route remains invalid for positive
quality claims. G21 supplies the benchmark premise locally; quality claims still
need method redesign or a stronger public real-GT benchmark plus real-GT
training and held-out evaluation beyond the G23-G33 adapter/init/eval/numerical
gates. G34-G36 now close current RI3D scaling, confirm no additional ready
public/local benchmark is available, and reset the method direction toward
learned-prior/full-head Gaussian reconstruction under real-GT gates.

## Main Claim

```text
Blindly adding diffusion pseudo views is unreliable. Corrected first10 audits
show persistent identity drift, geometry drift, card/source-frame artifacts,
accessory and hair instability, and style drift. CLIP/reliability ranking and
budgeted view selection improve 2D candidate hygiene, but do not certify valid
3D reconstruction supervision. A repo-safe mesh-derived positive-control case
validates provenance, conversion, training, rendering, and result export
plumbing, but the current RI3D path still fails visual reconstruction quality.
```

## Evidence Map

| Evidence | Artifact | Claim supported |
| --- | --- | --- |
| Zero123++ 3x2 split correction | `experiments/metrics/zero123plus_grid_split_bug_20260519.md` | Historical 2x3 per-view conclusions are contaminated and downgraded. |
| Candidate-pool audit | `experiments/metrics/first10_candidate_pool_audit_gate_20260519.md` | `experiments/downstream_datasets` is not a validated training set. |
| Head-cutout corrected probe | `experiments/metrics/head_cutout_probe_resplit3x2_gate_20260519.md` | Corrected pseudo views remain diagnostic-only. |
| GT route gate | `experiments/metrics/gt_dataset_access_gate_20260519.md` | Real-capture quality claims need licensed cameras and GT geometry. |
| GT intake readiness | `experiments/metrics/g16a_real_gt_intake_readiness_20260520.md` | Multiface is ready as a local intake route; G21 later closes the compact-case gate locally. |
| Real-GT benchmark pivot | `experiments/metrics/real_gt_benchmark_pivot_20260520.md` | Old pseudo-view/RI3D results are diagnostic-only; H3DS/FaceScape/Multiface compact real-GT benchmark is the mandatory next gate. |
| G21 local real-GT gate | `experiments/metrics/g21_multiface_debug_gate_20260520.md` | A Multiface debug compact case satisfies the real-GT benchmark premise locally; raw RGB/mesh artifacts remain outside git. |
| G22 preflight | `experiments/metrics/g22_real_gt_reconstruction_preflight_20260520.md` | Current RI3D/evaluation plumbing is blocked before training on real Multiface cameras. |
| G23 adapter | `experiments/metrics/g23_multiface_real_camera_adapter_20260520.md` | A local-only RI3D-readable Multiface adapter passes camera/depth/conf preflight; not a quality result. |
| G24 contract | `experiments/metrics/g24_real_gt_adapter_contract_gate_20260520.md` | CPU file contracts, local-only policy, split, and metrics skeleton pass. |
| G25 init smoke | `experiments/metrics/g25_ri3d_multiface_init_smoke_20260520.md` | RI3D loads the adapter and saves an initialization point cloud; no full training or quality claim. |
| G26 eval smoke | `experiments/metrics/g26_heldout_eval_smoke_20260520.md` | Held-out render/eval executes without saving identifiable media; metrics are init-only smoke values. |
| G27 numerical gate | `experiments/metrics/g27_ri3d_train10_numerical_gate_20260520.md` | Tiny training is blocked by NaN loss even under plain L1-only settings. |
| G28 loss-path diagnosis | `experiments/metrics/g28_ri3d_loss_path_diagnosis_20260520.md` | The NaN path is localized to train-loop zero-weight branch contamination after optimizer steps. |
| G29 zero-weight guard | `experiments/metrics/g29_zero_weight_loss_guard_train10_20260520.md` | L1-only train10 finishes with finite loss after skipping zero-weight SSIM/silhouette/depth branches. |
| G30 post-guard eval | `experiments/metrics/g30_post_guard_heldout_eval_smoke_20260520.md` | Held-out eval runs from the G29 checkpoint, but metrics match init-only G26 and remain non-quality. |
| G31 component audit | `experiments/metrics/g31_guarded_loss_component_audit_20260520.md` | SSIM/silhouette components are finite; mono-depth-only is NaN before the scale guard. |
| G32 monodisp guard | `experiments/metrics/g32_monodisp_scale_guard_train10_20260520.md` | Clamping monodisp scales fixes depth-only train10 NaNs. |
| G33 combined guarded eval | `experiments/metrics/g33_combined_guarded_train10_eval_20260520.md` | Combined guarded train10 is finite, but held-out metrics still match init-only values. |
| G34 route reset | `experiments/metrics/g34_post_g33_route_reset_20260520.md` | Current RI3D setup is closed for longer-training method scaling after no held-out quality gain. |
| G35 benchmark availability | `experiments/metrics/g35_public_benchmark_availability_20260520.md` | No additional ready public/local real-GT benchmark exists locally; access/license is still required. |
| G36 method direction | `experiments/metrics/g36_method_redesign_direction_20260520.md` | Latest literature supports learned-prior/feed-forward/head-anchored redesign, not ad hoc RI3D scaling. |
| CC0 positive control | `experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md` | Repo-safe GT-derived case passes positive-control-only gate. |
| G17 iter500 visual gate | `experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.md` | Current RI3D path executes but fails reconstruction quality even on positive control. |
| G18 taxonomy | `experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.md` | Corrected first10 pseudo views support failure taxonomy, not training. |

## Figure Set

Primary figures:

```text
experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png
experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png
experiments/figures/first10_failure_taxonomy_resplit3x2_20260520.png
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/figures/ri3d_gt_positive_control_iter500_inputs.png
experiments/figures/ri3d_gt_positive_control_iter500_renders.png
```

Supplementary result records:

```text
experiments/reconstructions/ri3d_gt_positive_control_iter10/
experiments/reconstructions/ri3d_gt_positive_control_iter500/
experiments/reconstructions/ri3d_first2_160_iter500/
experiments/reconstructions/ri3d_first2_roleaware_iter500/
experiments/reconstructions/ri3d_first2_roleweighted_iter500/
experiments/reconstructions/ri3d_first2_maskaware_iter500/
experiments/reconstructions/ri3d_first2_fghead_pcdmask_iter500/
experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500/
```

## Key Numbers

G18 corrected first10 taxonomy:

```text
views audited: 60
identity_supervision: 10
geometry_only: 37
reject: 13
budget4 selected views: 40
budget4 selected reject/severity3 views: 8
```

G17 positive control:

```text
case: wikimedia_blender_head_cc0
views: 8
iter10 MP4s: 120 frames at 256x256
iter500 MP4s: 120 frames at 256x256
iter500 verdict: execution/export pass, reconstruction-quality fail
```

G20/G21 benchmark pivot:

```text
G21 verdict: PASS_REAL_GT_BENCHMARK on local Multiface debug compact case
required next verdict: G28 loss-path numerical diagnosis before any longer
  training/evaluation run
preferred route: H3DS v2, blocked by access token/license
local benchmark route: Multiface debug 6795937 / E001_Neutral_Eyes_Open /
  frame 000102 passes G21 with 9 real views, cameras, masks, and tracked mesh
hard stop: no new web pseudo-view/RI3D scaling; next method work must stay on
  a real-GT adapter/eval gate
repo-safe result: experiments/figures/g21_multiface_debug_mask_gate_20260520.png
G22 result: BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER
G23 result: PASS_REAL_CAMERA_ADAPTER_PREFLIGHT
G24 result: PASS_REAL_GT_ADAPTER_CONTRACT
G25 result: PASS_RI3D_INIT_ONLY_SMOKE, point_count=67410
G26 result: PASS_HELDOUT_RENDER_EVAL_SMOKE, PSNR=4.2685, LPIPS=0.5011
G27 result: BLOCKED_RI3D_TRAINING_NUMERICAL_HEALTH_NAN
G28 result: BLOCKED_RI3D_LOSS_PATH_NUMERICAL_HEALTH, zero-weight depth branch
  can become NaN after optimizer steps
G29 result: PASS_ZERO_WEIGHT_LOSS_GUARD_L1_TRAIN10, final_loss=0.6124692
G30 result: PASS_POST_GUARD_HELDOUT_EVAL_SMOKE_NO_QUALITY_CLAIM,
  PSNR=4.2685, LPIPS=0.5011
G31 result: BLOCKED_MONODEPTH_COMPONENT_NUMERICAL_HEALTH
G32 result: PASS_MONODISP_SCALE_GUARD_DEPTH_TRAIN10, final_loss=0.6245082
G33 result: PASS_COMBINED_GUARDED_TRAIN10_EVAL_NO_QUALITY_GAIN,
  final_loss=0.5910920, PSNR=4.2685, LPIPS=0.5011
G34 result: PASS_ROUTE_RESET_CLOSE_CURRENT_RI3D_SCALING
G35 result: BLOCKED_NO_ADDITIONAL_READY_REAL_GT_BENCHMARK
G36 result: PASS_METHOD_REDESIGN_DIRECTION_NO_LONGER_RI3D_SCALING
```

## Limitations

```text
1. This sprint does not solve single-image full-head reconstruction.
2. Historical G2-G14 reconstruction conclusions are retained only as diagnostic
   engineering evidence because of the Zero123++ split bug and weak candidate
   pool quality.
3. Corrected web first10 pseudo views remain blocked for reconstruction training.
4. The CC0 mesh-derived positive-control case validates pipeline mechanics, not
   real-capture identity preservation or real multi-camera performance.
5. Real reconstruction-quality claims require a licensed or redistributable
   real GT case with calibrated views and mesh/point-cloud geometry.
6. G23-G33 are adapter/init/eval/numerical gates, not positive reconstruction method results.
   G29 and G32 fix numerical NaN classes, and G33 shows combined train10 can be
   finite, but held-out metrics remain init-level. The paper still cannot be
   framed as a positive reconstruction method result until a redesigned method
   or stronger benchmark produces held-out/geometry improvement on real GT.
7. G34-G36 close the current RI3D scaling route; they are planning/positioning
   gates, not new reconstruction evidence.
```

## Final Milestone Status

```text
G0-G15: complete, with G8-G14 downgraded to diagnostic evidence.
G16a: H3DS/full benchmark access still externally constrained; G21 provides a
      local Multiface debug compact-case pass.
G16a-local: complete as real-GT intake/readiness, not reconstruction.
G16b: complete for positive-control scope.
G17: complete for current sprint; RI3D positive-control execution passes but
     visual reconstruction quality fails.
G18: complete as corrected first10 diagnostic failure taxonomy.
G19: complete as conservative paper package and claim boundary.
G20: complete as benchmark-first pivot and route/distribution audit.
G21: complete locally on Multiface debug compact real-GT case; raw RGB/mesh stay
     local pending artifact review.
G22: blocked before training by real-camera adapter and metric mismatch.
G23: complete as local-only Multiface adapter preflight.
G24: complete as CPU RI3D adapter contract gate.
G25: complete as RI3D init-only smoke; no full training or quality claim.
G26: complete as held-out eval smoke; metrics are not quality.
G27: blocked by NaN training loss even under plain L1-only settings.
G28: complete as loss-path diagnosis; zero-weight depth branch contamination
     explains the train-loop NaN class.
G29: complete as narrow L1-only train10 numerical pass after zero-weight guards.
G30: complete as post-guard held-out eval smoke; no quality improvement.
G31: complete as guarded component audit; mono-depth blocks before scale guard.
G32: complete as monodisp scale guard; depth-only train10 finite.
G33: complete as combined guarded train10/eval; finite but no quality gain.
G34: complete as route reset; current RI3D scaling is closed.
G35: complete as benchmark availability audit; no additional ready public/local
     real-GT benchmark exists locally.
G36: complete as method redesign direction; next method must be learned-prior /
     feed-forward / head-anchored and real-GT gated.
```
