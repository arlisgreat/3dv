# G20 Real GT Benchmark Pivot

Date: 2026-05-20

## Verdict

```text
OLD_PSEUDOVIEW_RI3D_ROUTE_INVALID_FOR_QUALITY_CLAIMS
REAL_GT_BENCHMARK_REQUIRED_BEFORE_ANY_NEW_RECONSTRUCTION_CLAIM
NO_PSEUDOVIEW_OR_RI3D_SCALING_WITHOUT_PASS_REAL_GT_BENCHMARK
G20_BENCHMARK_SPEC_COMPLETE
G21_REAL_GT_COMPACT_CASE_PASS_LOCAL
RAW_IDENTIFIABLE_ASSETS_LOCAL_ONLY_PENDING_ARTIFACT_REVIEW
```

## Core Purpose After Pivot

The sprint can no longer be framed as proving that the current pseudo-view
frontend improves reconstruction. G2-G19 remain useful as stop-loss diagnostics:
they identify split-grid preprocessing risk, weak candidate selection, distorted
pseudo views, and RI3D failure modes.

The active experimental goal is now:

```text
Establish a licensed, auditable real-GT benchmark for single-image/few-view
head reconstruction before making any reconstruction-quality claim.
```

Without that benchmark, additional pseudo-view generation or RI3D iterations
only produce more diagnostic evidence, not credible method results.

## Minimum Benchmark Gate

A compact real-GT benchmark case must satisfy all of the following before any
training or reconstruction milestone starts:

```text
same identity and static expression/frame
6-12 real captured RGB views, not diffusion-generated pseudo views
camera intrinsics and extrinsics for every selected view
foreground masks or reliable segmentation route
GT full-head mesh or point cloud suitable for Chamfer/normal/silhouette checks
license/privacy status allowing at least compact derived audit artifacts in repo
visual/VLM audit sheet passes: no wrong subject, crop breakage, view mismatch,
  mesh-image mismatch, or unusable mask
model/data distribution audit is recorded before interpreting any result
```

Required verdict:

```text
PASS_REAL_GT_BENCHMARK
```

Any weaker verdict is not enough for reconstruction-quality claims.

## Route Matrix

| Route | Fit | Local status | Decision |
| --- | --- | --- | --- |
| H3DS v2 | Best technical fit for this sprint: full-head mesh, images, masks, cameras, default sparse-view configs, evaluation code | Python package/config audited locally; no `H3DS_ACCESS_TOKEN` available | Preferred next acquisition route, blocked by access token/license |
| FaceScape multi-view data | Strong face multi-view route with images, camera parameters, and corresponding 3D face mesh | Local sample metadata confirms the right structure, but sample redistribution is blocked and only two mview images are available locally | Viable after licensed full case access; not repo-safe today |
| Multiface | Strong real-capture route with high-resolution multi-view images, calibrations, tracked meshes, headpose, textures, audio | Debug compact case passes local G21: 9 same-frame RGB views, KRT cameras, projected mesh masks, and tracked OBJ; identity `6795937`, expression `E001_Neutral_Eyes_Open`, frame `000102` | Current executable local benchmark route; raw RGB/mesh stay in `3dv_work` pending artifact review |
| NeRSemble | Potentially useful dynamic head/face route | Not locally acquired in a compact, licensed, auditable form | Secondary route only |
| Wikimedia/Blender CC0 mesh positive control | Repo-safe synthetic camera/geometry plumbing check | G16b/G17 passed provenance/export; RI3D visual quality failed | Positive-control only; not a real-capture benchmark |

## Model/Data Distribution Audit

The previous web-first10 setting is not a valid benchmark for interpreting
method quality:

```text
Zero123++ on unconstrained web portraits is outside a controlled real-GT
evaluation distribution. Its failures are useful for taxonomy, but not for
quantitative reconstruction claims.

RI3D assumes coherent sparse views. The generated candidate pools violate that
premise when they contain split bodies, rotated photo cards, cropped fragments,
background-only regions, identity drift, and inconsistent geometry.

LAM is closer to the clean single-portrait domain, but LAM output alone does not
certify that pseudo-view supervision improves full-head reconstruction.

The CC0 mesh positive control is synthetic and useful for pipeline sanity only.
It cannot replace real captured multi-view data with GT geometry.
```

## Hard Stop

For old pseudo-view/RI3D assets, regardless of the G21 local pass:

```text
do not train from experiments/downstream_datasets
do not scale web first10/first30 pseudo-view reconstruction
do not use RI3D loss/render differences as reconstruction-quality evidence
do not report CC0 mesh positive-control quality as real-capture performance
do use old pseudo-view/RI3D outputs only for diagnostic figures and failure taxonomy
```

## Milestone State

| Gate | State | Meaning |
| --- | --- | --- |
| G20 | complete | Benchmark-first pivot, route audit, and distribution gate are recorded. |
| G21 | complete locally | Multiface debug compact case passes PASS_REAL_GT_BENCHMARK; repo records metrics/hashes/mask-only PNG, while raw RGB/mesh remain local. |

The benchmark premise is now locally satisfied for the next controlled
preflight, but this is not a method result. No GPU experiment should start from
the old web pseudo-view route. The next action is G22: rerun the G21 gate,
verify model/test-data distribution, then run a minimal real-GT reconstruction
or block before training if the audit regresses.
