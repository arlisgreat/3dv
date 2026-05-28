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

After the G77-G80 renderer/evaluator validation, the central question is:

```text
Can pseudo multi-view generation provide trustworthy 3D Gaussian supervision,
or does it only create plausible 2D hallucinations that fail real held-out
camera evaluation?
```

G83-G108 run this question as a three-arm NeRSemble held-out experiment. The
current answer is negative for the tested route: identity/confidence-aware
pseudo-view supervision does not exceed either direct single-image Gaussian or
matched naive pseudo-view supervision.

G110-G119 find a narrower positive mechanism: do not let pseudo views define
geometry. Keep the direct Gaussian prior, select alpha only from source
render/source mask, and use strict identity/confidence pseudo views as a
conservative color prior. On the same single NeRSemble source/eval split this
beats direct and naive under the original G55 held-out evaluator, but it remains
single-case diagnostic evidence pending replication. G115 records the repo-safe
artifact sync set for the single-case pass. G116 then prevents overclaiming the
naive failure: the naive source render already under-covers the source mask, so
pose/crop/source/geometry risk remains. G117/G118 show the single-case ablation
pattern; G119 records that multi-case replication is not complete and no empty
GPU was available for the next source split.

The intended contribution is not a qualitative single-image demo. It is a
strict supervision-validity protocol: identity-anchored and confidence-aware
pseudo views, no real multi-view images as training supervision, full-head 3DGS
reconstruction, and rendering/evaluation in real held-out benchmark cameras.

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
results. G26-G33 also remain plumbing/numerical gates, not quality claims. G34
closes the current RI3D scaling route; G35 confirms no additional ready
public/local real-GT benchmark is available; G36 resets the method direction
toward learned-prior/full-head Gaussian approaches. G37-G38 add model/data
distribution and artifact-sync safeguards before any future method claim.
G39-G41 then open the learned-prior route under those gates, run a local LAM
smoke on the Multiface real-GT train view, and block quality interpretation
until camera-aligned held-out renders or GT geometry metrics exist. G42-G43
verify local LAM frame/geometry export and a weak normalized mesh sanity check,
while preserving the same block on quality interpretation because neither gate
uses held-out Multiface cameras or an aligned metric GT geometry frame. G44 then
adds a similarity/ICP-aligned mesh diagnostic in the Multiface GT frame, but
keeps the same no-quality-claim boundary because ICP alignment is not camera
recovery, verified surface correspondence, or held-out view reconstruction. G45
then renders the aligned LAM mesh into the three held-out Multiface cameras and
passes silhouette/depth diagnostics, while still blocking RGB/SOTA quality
claims because native LAM Gaussians and held-out appearance are not evaluated.
G47-G49 preconfigure stronger benchmark intake and scope forecasts. G50-G55
then update the benchmark route with actual NeRSemble data: the official v2 and
benchmark folders are present with 79 explicit HTTP-404 exclusions; official
NVS/Mono/SVFR protocol assets pass; v2 participant 017 EXP-1-head passes a
local all-camera visual audit; official NVS participant 388 GLASSES frame 0 has
RGB, alpha maps, cameras, and pointcloud wired into a local adapter; and a
copy-source baseline proves held-out RGB/mask metric IO. These gates authorize a
real method-output run, not a method-quality claim by themselves. G56 blocks the
first method-readiness check because LAM-on-NeRSemble is in-domain with possible
dataset overlap and no held-out NeRSemble camera renderer/prediction files exist.
G57 then produces finite LAM prediction files through a `source_to_lam_sample`
motion-camera path, but G58 downgrades the run to diagnostic-only because the
renderer contract is not verified NeRSemble K/R/T and the held-out predictions
are blank/cropped. G59/G60 validate the true NeRSemble K/R/T path with the
official pointcloud as an oracle positive control. G61/G62 route LAM textured
mesh output through that same camera path only after GT pointcloud bbox
alignment; this is nonempty but visually broken and remains diagnostic-only.

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
G20-G33: acquire one local real-GT compact case, repair adapter/numerical
         plumbing, and show no held-out quality gain.
G34-G36: stop current RI3D scaling, audit benchmark availability, and reset the
         method direction with current literature.
G37-G38: audit model/data distribution interpretability and repo artifact sync.
G39-G41: gate learned-prior/head-anchored Gaussian work, run LAM local smoke,
         and require held-out camera/geometry export before any quality claim.
G42-G43: verify LAM local PNG/MP4/PLY/OBJ export and weak normalized mesh sanity,
         but keep all identifiable media private and block quality claims.
G44: add similarity/ICP-aligned LAM-vs-Multiface mesh diagnostic, still
     diagnostic-only and private-artifact-safe.
G45: project the aligned LAM mesh into held-out Multiface cameras and record
     silhouette/depth diagnostics, still no RGB reconstruction claim.
G46: record project completion forecast and user-check risks.
G47-G48: preconfigure official benchmark tooling and intake contracts for
         NeRSemble/H3DS while data access is still credential-gated.
G49: record completion probability by project scope.
G50-G52: ingest NeRSemble official data and close the download integrity gate
         with 156260 ok manifest paths and 79 explicit HTTP-404 exclusions.
G53: pass NeRSemble official benchmark protocol checks and a local visual/VLM
     gate for a v2 all-16-camera compact case.
G54-G55: prepare an official NVS frame-0 local adapter and smoke-test held-out
         RGB/mask metrics with a trivial copy-source baseline.
G56: block method-quality evaluation until a real method output can be rendered
     into the G54 NeRSemble held-out cameras.
G57-G58: show that LAM source-to-sample camera files are finite but invalid for
         method claims after renderer-contract and visual audit.
G59-G60: validate true NeRSemble K/R/T camera/evaluator plumbing with the GT
         pointcloud oracle positive control.
G61-G62: render/evaluate LAM textured mesh through true K/R/T only with GT bbox
         alignment; keep it diagnostic-only because texture/appearance are broken.
G63-G73: remove GT pointcloud alignment and identify the usable native Gaussian
         contract: `framework_img.obj` xyz plus LAM PLY opacity/scale/rotation
         rendered through the native diff-gaussian rasterizer into true K/R/T.
         The first pass is recognizable but crop-limited.
G74-G76: rerun from a frontal source view; LAM export/render/eval work, but a
         source change alone does not solve crop/off-center failure.
G77-G79: add source-mask plus eval-camera-frustum crop guard with no held-out
         RGB/mask or GT pointcloud alignment; held-out mask IoU reaches 0.900017
         and visual review passes as the current single-case method-direction
         positive.
G81-G108: run the actual pseudo-view supervision validity test on the same
          NeRSemble source/eval split: source-only pseudo generation input,
          naive and identity/confidence-aware manifests, private RI3D arms,
          held-out rendering/evaluation, strict three-arm contract rerun, and
          mask-only visual audit. The identity/confidence-aware arm does not
          beat direct or naive.
G110-G119: replace the failed pseudo-geometry arm with a source-gated
           direct-prior refinement. The strict identity/confidence pseudo views
           only provide a color prior; source render/source mask select alpha.
           This passes the original G55 evaluator and three-arm contract on the
           current held-out cameras, then passes artifact sync. The later gates
           add a naive pose/crop caveat, run requested ablations, and preflight
           multi-case replication.
```

The stable scientific signal is not "RI3D is solved." It is:

```text
1. Blindly adding all pseudo views is risky.
2. 2D candidate selection improves hygiene but does not prove 3D usefulness.
3. Reconstruction claims need a ground-truth positive control with cameras and
   mesh/point-cloud evidence.
4. A learned-prior/head-anchored Gaussian method can be made evaluable only
   after its output is rendered into real held-out cameras under an explicit
   no-leakage gate.
5. Identity/confidence-gated pseudo views do not rescue the RI3D-style
   pseudo-geometry route, but they can help as a conservative source-gated color
   prior on top of a strong direct Gaussian prior in the current single case.
6. G110/G112 answer the active single-case objective positively.
7. G116 says naive failure is real but not cleanly attributable to pseudo-view
   quality alone; source-render crop/geometry risk must stay in the story.
8. G117/G118: identity helps RGB modestly; confidence weighting is not proven
   useful on the single case; source alpha helps mask; direct geometry is the
   dominant contributor.
9. G119: multi-case replication remains open; G120 must run only when an empty
   GPU is available and must preserve the source-only/pseudo-only gate.
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

Before interpreting any method metric, also require:
  explicit model training/evaluation distribution statement
  in-distribution or out-of-distribution status for the test benchmark
  held-out split that is not used as supervision
  artifact sync gate for PNG/MP4/CSV/JSON/MD outputs
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
| G34 | Post-G33 route reset | G33 no-quality-gain result | Done: no longer RI3D scaling milestone is authorized from the current adapter/objective |
| G35 | Public/stronger benchmark availability audit | G34 route stop | Done, blocked: no additional ready local/public real-GT benchmark beyond current Multiface debug route and synthetic positive control |
| G36 | Method redesign direction | G34/G35 | Done: next method must be learned-prior/feed-forward/head-anchored with real-GT gates; pseudo views are conditional priors only |
| G37 | Model/data distribution audit | G36 method reset | Done: current results are qualitative, diagnostic, or plumbing/numerical evidence only; next method must declare in/out distribution before GPU work |
| G38 | Artifact sync gate | G37 distribution audit and repo-safe manifests | Done: current repo-safe PNG/MP4/CSV/JSON/MD artifacts are sync candidates; blocked raw/private paths are zero |
| G39 | Learned-prior method gate | G36-G38 pass | Done: real-GT/data/VLM/distribution gates authorize only local LAM smoke or repo-safe positive controls |
| G40 | LAM learned-prior smoke | G39 pass | Done: Multiface train-view smoke succeeds locally with private hashes only; CC0 point-splat input is blocked by LAM face tracking |
| G41 | Learned-prior evaluation contract | G40 smoke | Done: current LAM wrapper cannot provide held-out camera-aligned or geometry metrics, so quality claims remain blocked |
| G42 | LAM local export gate | G41 contract and private artifact policy | Done: local LAM exports 50 PNGs, 50 PLYs, canonical Gaussian PLY, MP4, and mesh OBJs; repo records hashes/metrics only |
| G43 | LAM-vs-Multiface geometry sanity | G42 export gate | Done: bbox-normalized mesh sanity is non-catastrophic but not scale/camera aligned, so no quality claim |
| G44 | Similarity/ICP geometry diagnostic | G43 weak geometry sanity | Done: similarity-aligned symmetric mean nearest-neighbor is 17.164824 GT units / 0.037132 normalized, but this remains diagnostic-only |
| G45 | Held-out camera geometry diagnostic | G44 aligned geometry diagnostic | Done: held-out mask IoU mean 0.708083 and depth mean error 0.029646 of GT median pass diagnostic thresholds; still no RGB/SOTA claim |
| G46 | Project completion forecast | G45 diagnostic closure and literature monitor | Done: fastest repo-safe diagnostic package is estimated at 2-4 focused work days; stronger RGB method-quality/full-proposal scope needs more time and user decisions |
| G47 | Benchmark access/tooling setup | User-side NeRSemble/H3DS applications are pending | Done: FaceScape support and official NeRSemble/H3DS tool repos are local; credential-gated data remains blocked |
| G48 | Benchmark intake preflight | G47 tooling setup | Done: raw-data roots, credentials, contracts, and git policy are checked without creating fake benchmark results |
| G49 | Completion probability | G48 preaccess closure | Done: diagnostic package probability is high; method-quality probability depends on native held-out rendering and official benchmark data |
| G50 | NeRSemble official intake | Official access URL available | Done: SVFR inputs and v2 metadata/calibration downloaded; full videos still resumable |
| G51 | NeRSemble full download launch | G50 partial intake | Done: full v2/benchmark transfer launched with ignored manifest under `datasets/` |
| G52 | NeRSemble download integrity gate | Download completed locally | Done: v2 and benchmark roots present; 79 final HTTP-404 paths are explicitly excluded |
| G53 | NeRSemble compact case data/VLM gate | G52 pass with exclusions | Done: official NVS/Mono/SVFR protocols pass and v2 017 EXP-1-head passes local visual audit |
| G54 | NeRSemble NVS frame-0 adapter | G53 pass | Done: official NVS 388 GLASSES frame 0 adapter has RGB/alpha/cameras/pointcloud local-only |
| G55 | NeRSemble held-out metric smoke | G54 pass | Done: copy-source baseline produces finite held-out RGB/mask metrics; this is metric plumbing only |
| G56 | NeRSemble method readiness gate | G55 pass | Blocked correctly: prediction files exist, but no passing true NeRSemble K/R/T renderer-contract audit; LAM-on-NeRSemble also has in-domain/possible-overlap risk |
| G57 | LAM source-to-sample evaluator diagnostic | G56 blocked on renderer | Done: finite files/metrics, but not a true NeRSemble camera renderer |
| G58 | LAM renderer contract audit | G57 files present | Done: G57 downgraded to diagnostic-only due failed camera contract and blank/cropped predictions |
| G59 | True-KRT pointcloud renderer positive control | G58 downgrade requires camera isolation | Done: official GT pointcloud renders into source/eval cameras with plausible view direction |
| G60 | Pointcloud oracle held-out eval | G59 pass | Done: finite oracle visible-heldout metrics; validates evaluator/camera path only |
| G61 | LAM mesh true-KRT diagnostic render | G59/G60 pass | Done: nonempty renders after GT pointcloud bbox alignment; diagnostic-only and visually broken |
| G62 | LAM mesh true-KRT diagnostic eval | G61 pass | Done: finite metrics but no method-quality claim due GT alignment and broken appearance |
| G63 | Source/model-derived true-KRT method render | G61/G62 diagnostic closure | Active next: remove GT geometry alignment or use a method with native NeRSemble camera output |

## Expected Final Outputs

The expected final package is:

```text
1. A gate-first protocol showing why pseudo-view supervision cannot be trusted
   without data/visual/geometry gates.
2. A corrected first10 failure taxonomy for diffusion pseudo views.
3. A positive-control reconstruction case with known cameras and GT geometry.
4. A real-GT benchmark requirement and route audit for the next credible claim.
5. A learned-prior/head-anchored Gaussian method gate showing that LAM can run
   locally on real-GT input, but MP4 smoke is not a reconstruction metric.
6. A NeRSemble-backed benchmark route with explicit download exclusions,
   visual/data gates, local-only raw RGB policy, and a held-out metric harness.
```

## Current Closure

As of 2026-05-27:

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
training. G34-G36 record that stop condition explicitly: the current RI3D path
is closed for method scaling, no additional ready benchmark exists locally, and
the method story should pivot to learned-prior/full-head Gaussian reconstruction
under real-GT gates. G37-G38 add the two safeguards requested after the
candidate-pool mistake: model/data distribution must be declared before any
interpretation, and repo-safe artifacts are explicitly checked for GitHub sync
without admitting raw/private assets. G39-G41 complete the first learned-prior
iteration: the method family is fixed to feed-forward/head-anchored Gaussian;
LAM-20K runs on a local Multiface train view after a PyTorch 2.6+ TorchScript
load compatibility patch, but derived media stay private and visual audit shows
only local execution quality, not a metric-backed reconstruction result. The
repo-safe CC0 point-splat positive control is blocked for LAM input use because
face tracking fails. The next action must be a camera-aligned render/geometry
export adapter, stronger licensed benchmark access, or explicit artifact review,
not more ungated MP4 generation. After G50-G62, NeRSemble is now the main
real-GT route: official data is local but not perfectly complete, with 79
server-side 404 paths excluded. The true-KRT camera/evaluator path now passes
with a GT pointcloud oracle, while the current LAM routes remain diagnostic:
source-to-sample camera frames fail the renderer contract, and GT-bbox-aligned
LAM mesh renders are visually broken. The immediate next method milestone is a
source/model-derived true-KRT learned-prior/feed-forward/head-anchored output,
or a switch to a method with native NeRSemble camera output. Metrics are not
main-result evidence until model-distribution, visual, renderer-contract, and
artifact/privacy gates all pass.
```
