# G19 Paper Package

Date: 2026-05-20

## Final Scope

```text
Failure-aware pseudo-view supervision for single-image Gaussian head reconstruction.
```

This paper sprint does not claim solved single-image full-head reconstruction.
It packages a diagnostic protocol and the evidence that generic diffusion
pseudo views must be gated before they can supervise 3D reconstruction.

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
| GT intake readiness | `experiments/metrics/g16a_real_gt_intake_readiness_20260520.md` | Multiface is ready as a local intake route, but real reconstruction remains blocked until raw image/mesh case and visual audit pass. |
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
```

## Final Milestone Status

```text
G0-G15: complete, with G8-G14 downgraded to diagnostic evidence.
G16a: externally blocked by real dataset access/license constraints.
G16a-local: complete as real-GT intake/readiness, not reconstruction.
G16b: complete for positive-control scope.
G17: complete for current sprint; RI3D positive-control execution passes but
     visual reconstruction quality fails.
G18: complete as corrected first10 diagnostic failure taxonomy.
G19: complete as conservative paper package and claim boundary.
```
