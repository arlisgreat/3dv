# Experiment Narrative And Gates

Date: 2026-05-20

## Core Purpose

The full application in `QY25181-申请书-6-13.pdf` asks for single-image full-head
modeling: a portrait/head image is expanded with diffusion pseudo views, fused
with PanoHead-style 360-degree priors, represented by 3D Gaussians, and stabilized
with Transformer/style consistency plus FLAME/FaceVerse/3DMM structure.

The current paper sprint must stay narrower. The final experimental purpose is:

```text
Diagnose when diffusion pseudo views help or hurt single-image Gaussian head
reconstruction, and define a failure-aware pseudo-view supervision protocol.
```

Expected paper claim:

```text
Pseudo views are useful only after explicit failure-aware gating. More views are
not automatically better, and candidate-pool hygiene is not the same as valid
3D reconstruction supervision.
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
unless a fresh gate records `PASS_RECONSTRUCTION_TRAINING`.

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

If the case has licensed real multi-view images, cameras, and GT geometry:
  PASS_RECONSTRUCTION_TRAINING
```

## Active Data Routes

`G16a` is the real-capture route. FaceScape, H3DS, Multiface, NeRSemble, and UEA
remain useful, but each route has access, license, size, or redistribution
constraints. Until one compact case is licensed and auditable, it cannot support
public reconstruction-quality claims.

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
| G16b | Mesh-derived positive-control gate | Public mesh with redistributable derived outputs | 6-12 rendered views, cameras, depth/mask, contact sheet, and visual audit |
| G17 | Reconstruction positive-control rerun | G16b passes | Iter10/iter500 execute and export; visual quality fails, so current RI3D route is diagnostic only |
| G18 | Corrected first10 failure taxonomy | G15c/G16 gates block web training | 60 corrected views labeled; web first10 remains diagnostic-only |
| G19 | Paper packaging | G17 and G18 are stable | Claims, figures, limitations, and milestone closure are recorded |

## Expected Final Outputs

The expected final package is:

```text
1. A gate-first protocol for pseudo-view supervision.
2. A corrected first10 failure taxonomy for diffusion pseudo views.
3. A positive-control reconstruction case with known cameras and GT geometry.
4. A paper claim that is conservative: pseudo views can guide reconstruction only
   after reliability, visual, and geometry gates pass.
```

## Current Closure

As of 2026-05-20:

```text
G16a real-capture GT remains externally blocked by access/license constraints.
G16b positive-control data gate passes.
G17 iter10 and iter500 both execute and export valid MP4s, but iter500 still
fails visual reconstruction quality with ghosted multi-fragment heads.
G18 corrected first10 taxonomy is complete and diagnostic-only.
G19 paper package and milestone closure are complete.
```
