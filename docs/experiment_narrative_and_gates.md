# Experiment Narrative And Gates

Date: 2026-05-20

## Core Purpose

The full application in `QY25181-申请书-6-13.pdf` asks for single-image full-head
modeling: a portrait/head image is expanded with diffusion pseudo views, fused
with PanoHead-style 360-degree priors, represented by 3D Gaussians, and stabilized
with Transformer/style consistency plus FLAME/FaceVerse/3DMM structure.

The current paper sprint must stay narrower. The old diagnostic purpose was:

```text
Diagnose when diffusion pseudo views help or hurt single-image Gaussian head
reconstruction, and define a failure-aware pseudo-view supervision protocol.
```

G2-G19 show that this old route cannot support a positive reconstruction claim.
The active experimental purpose is now:

```text
Establish a licensed real-GT benchmark before making any
single-image/few-view head reconstruction-quality claim.
```

Expected claim boundary:

```text
Pseudo-view and RI3D experiments are diagnostic-only until a real-GT benchmark
with captured views, cameras, masks, and GT mesh/point cloud passes its gate.
```

## Current Corrections

These corrections are now part of the experimental premise:

```text
experiments/downstream_datasets/ contains pseudo-view candidate pools. It is not
a validated training dataset.

G2-G14 reconstruction-quality conclusions are downgraded to diagnostic evidence
because historical Zero123++ per-view PNGs were split as 2x3 while the saved
grids are 3x2.

Correct 3x2 resplitting removes one preprocessing bug, but web first10
head-cutout pseudo views still show visible identity and geometry distortions.
They remain diagnostic-only.
```

No milestone may restart reconstruction training from a generated candidate pool
or RI3D export. `PASS_REAL_GT_BENCHMARK` only authorizes real-GT adapter,
initialization, render/eval, or training gates on the passing captured benchmark
case or an equivalent licensed case. G23/G24/G25 are not reconstruction-quality
results. G26-G33 also remain plumbing/numerical gates, not quality claims.

## Real GT Benchmark Pivot

The current correction is stronger than "be careful with pseudo views":

```text
Without a real-GT benchmark, running more pseudo-view generation or RI3D
iterations cannot produce a trustworthy reconstruction-quality conclusion.
```

The minimum benchmark gate is:

```text
same identity and static expression/frame
6-12 real captured views
camera intrinsics and extrinsics
foreground masks or reliable segmentation route
GT full-head mesh or point cloud
license/privacy approval for compact derived repo artifacts
visual/VLM audit sheet passing before training
model/data distribution audit before interpreting results
```

Required verdict:

```text
PASS_REAL_GT_BENCHMARK
```

Current pivot artifact:

```text
experiments/metrics/real_gt_benchmark_pivot_20260520.md
experiments/metrics/real_gt_benchmark_pivot_20260520.json
experiments/metrics/g21_multiface_debug_gate_20260520.md
experiments/metrics/g21_multiface_debug_gate_20260520.json
experiments/figures/g21_multiface_debug_mask_gate_20260520.png
```

## Experiment Thread

The experimental path so far is:

```text
G0-G1: bring up LAM / Zero123++ and build first10 portrait inputs.
G2-G6: generate, rank, mask, cut out, and role-label pseudo-view candidates.
G7-G14: test RI3D reconstruction plumbing and several repair priors.
G15: audit data assumptions and discover that candidate-pool quality is too weak.
G16: replace distorted pseudo-view training premises with a GT-data gate.
```

The stable scientific signal is not "RI3D is solved." It is:

```text
1. Blindly adding all pseudo views is risky.
2. 2D candidate selection improves hygiene but does not prove 3D usefulness.
3. Reconstruction claims need a ground-truth positive control with cameras and
   mesh/point-cloud evidence.
```

## Gate Semantics

Every milestone begins with a data audit gate:

```text
1. State the premise in falsifiable terms.
2. Check structural provenance: files, metadata, camera layout, grid layout,
   role labels, masks, and source license.
3. Generate a visual contact sheet or audit PNG.
4. Inspect the sheet with VLM/manual review.
5. Record one of:
   PASS_REAL_GT_BENCHMARK
   PASS_RECONSTRUCTION_TRAINING
   PASS_POSITIVE_CONTROL_ONLY
   PASS_DIAGNOSTIC_ONLY
   BLOCKED
6. Update MILESTONES.md before GPU training or reconstruction starts.
```

Decision tree:

```text
If source files are missing, mislabeled, license-blocked, or visually malformed:
  BLOCKED

If files are structurally present but generated views are distorted:
  PASS_DIAGNOSTIC_ONLY

If the case is synthetic/rendered from a known mesh with cameras:
  PASS_POSITIVE_CONTROL_ONLY

If the case has licensed real multi-view images, cameras, GT geometry, and
passes visual/VLM + distribution audit:
  PASS_REAL_GT_BENCHMARK

Only after PASS_REAL_GT_BENCHMARK may a method milestone record:
  PASS_RECONSTRUCTION_TRAINING
```

## Active Data Routes

`G16a` is the real-capture route. H3DS, FaceScape, Multiface, NeRSemble, and UEA
remain useful, but each route has access, license, size, or redistribution
constraints. Until one compact case is licensed and auditable, it cannot support
public reconstruction-quality claims.

`G20` ranks the current routes:

```text
H3DS v2: best technical fit, but blocked by H3DS_ACCESS_TOKEN/license.
FaceScape: strong multi-view face route, but local sample is not repo-safe and
  full case requires licensed access.
Multiface: local G21 pass route; debug compact case has 9 same-frame real
  captured views, KRT cameras, projected mesh masks, and tracked OBJ. Raw
  RGB/mesh assets remain under 3dv_work pending artifact review.
NeRSemble/UEA: secondary until compact licensed access exists.
CC0 mesh positive control: pipeline sanity only, not real capture.
```

`G16a-local` remains the intake/readiness closure for that route. Multiface is
the current best real-capture candidate because its official assets include
multi-view raw images, camera calibration metadata, tracked meshes, and headpose.
`G21` upgrades that route from intake-ready to a local real-GT benchmark pass
using the Multiface debug dataset: 9 same-frame real captured views, KRT cameras,
projected mesh masks, and a tracked OBJ all pass structural plus VLM/manual
audit. Raw RGB/mesh assets remain under `3dv_work`; the repo only publishes
metrics, hashes, and a mask-only PNG summary.

`G16b` is the repo-safe positive-control route. A public mesh case can be rendered
into deterministic multi-view RGB/depth/mask/camera artifacts. This validates the
pipeline and gate mechanics without pretending to be real captured multi-view
data.

Current positive control:

```text
Wikimedia Commons / Blender human base mesh realistic head
source: https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
license: CC0 1.0 Universal Public Domain Dedication
raw mesh location: /data1/workspace/airulan/3dv_work/datasets/wikimedia_blender_head_cc0/
repo policy: commit only derived PNG/MP4/CSV/JSON/MD audit outputs, not raw mesh.
```

NIH 3D Visible Human head/bust meshes were also checked, but their available
views are anatomical/cross-section oriented rather than a clean face-head
positive control, so they are not the active G16b case.

## Next Milestones

| Gate | Purpose | Start condition | Stop condition |
| --- | --- | --- | --- |
| G16a | Real GT access gate | Web first10 remains diagnostic-only | Licensed compact real case with images, cameras, and GT mesh/point cloud |
| G16a-local | Real GT intake readiness | Real GT was externally blocked at full-benchmark level | Multiface route/schema recorded; no training until G21 or equivalent real-GT gate passes |
| G16b | Mesh-derived positive-control gate | Public mesh with redistributable derived outputs | 6-12 rendered views, cameras, depth/mask, contact sheet, and visual audit |
| G17 | Reconstruction positive-control rerun | G16b passes | Iter10/iter500 execute and export; visual quality fails, so current RI3D route is diagnostic only |
| G18 | Corrected first10 failure taxonomy | G15c/G16 gates block web training | 60 corrected views labeled; web first10 remains diagnostic-only |
| G19 | Paper packaging | G17 and G18 are stable | Claims, figures, limitations, and milestone closure are recorded |
| G20 | Real-GT benchmark pivot | Old route cannot support quality claims | Benchmark spec, route audit, and distribution gate recorded |
| G21 | Compact real-GT benchmark acquisition | H3DS token or FaceScape/Multiface raw access | Done locally on Multiface debug case with PASS_REAL_GT_BENCHMARK; raw assets remain local |
| G22 | Real-GT reconstruction/evaluation preflight | G21 local pass, repeated data/VLM/distribution audit | Blocked before training: current RI3D/evaluation adapter does not preserve Multiface per-view intrinsics/depth/metrics |
| G23 | Local-only Multiface real-camera adapter | G22 blocker recorded | Adapter, depth/conf arrays, and mask/depth-only audit figure pass preflight |
| G24 | CPU adapter contract gate | G23 pass | RI3D file contracts, local-only policy, split, and metrics skeleton pass |
| G25 | RI3D init-only smoke | G24 pass and idle GPU selected | RI3D loads adapter and saves iteration-1 point cloud; no quality claim |
| G26 | Held-out render/eval smoke | G25 pass | Done: numeric held-out metrics recorded; no identifiable PNG/JPEG/MP4 committed |
| G27 | Tiny train10 numerical gate | G26 pass | Blocked: RI3D training loss is NaN even for plain L1-only |
| G28 | Loss-path numerical diagnostic | G27 blocked | Done: train-loop zero-weight depth branch contamination identified |
| G29 | Zero-weight loss guard train10 | G28 diagnosis | Done: L1-only train10 finite after skipping zero-weight branches; no default-loss or quality claim |
| G30 | Post-guard held-out eval smoke | G29 pass | Done: eval runs without media export, but metrics match init-only G26 |
| G31 | Guarded loss-component audit | G29/G30 pass | Done: SSIM/silhouette finite, mono-depth NaN blocks default depth training |
| G32 | Monodisp scale guard | G31 mono-depth blocked | Done: depth-only train10 becomes finite after clamping monodisp normalization scales |
| G33 | Combined guarded train10/eval | G32 pass | Done: combined guarded train10 finite, but held-out metrics match init-only values |

## Expected Final Outputs

The expected final package is:

```text
1. A gate-first protocol showing why pseudo-view supervision cannot be trusted
   without data/visual/geometry gates.
2. A corrected first10 failure taxonomy for diffusion pseudo views.
3. A positive-control reconstruction case with known cameras and GT geometry.
4. A real-GT benchmark requirement and route audit for the next credible claim.
```

## Current Closure

As of 2026-05-20:

```text
G16a real-capture GT is no longer blocked at the local compact-case level:
G21 passes on Multiface debug data. H3DS remains preferred for a stronger
full-head benchmark, and any identifiable Multiface artifact publication still
requires review.
G16a-local real-GT intake readiness is complete; Multiface metadata/KRT/frame
structure is verified.
G16b positive-control data gate passes.
G17 iter10 and iter500 both execute and export valid MP4s, but iter500 still
fails visual reconstruction quality with ghosted multi-fragment heads.
G18 corrected first10 taxonomy is complete and diagnostic-only.
G19 paper package and milestone closure are complete.
G20 real-GT benchmark pivot is complete.
G21 compact real-GT acquisition is complete locally with
PASS_REAL_GT_BENCHMARK. G22 blocks direct training on the old adapter mismatch.
G23/G24 pass the local-only Multiface adapter and CPU contract gates. G25 passes
RI3D init-only loading and saves a local point cloud. G26 passes held-out
render/eval plumbing without saving identifiable media. G27 blocks training
because the RI3D train loop reports NaN loss even in plain L1-only settings.
G28 localizes the failure to zero-weight branch contamination after optimizer
steps. G29 clears only the L1-only train10 path by guarding zero-weight losses.
G30 verifies post-guard held-out eval still runs, but metrics match the init-only
smoke. G31-G33 close the component/combined numerical-smoke loop, but still show
no held-out quality gain. The next action is method redesign or stronger public
real-GT benchmark access, not renewed web pseudo-view training or longer RI3D
training.
```
