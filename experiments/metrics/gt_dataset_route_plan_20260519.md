# GT Dataset Route Plan

Date: 2026-05-19

## Decision

For reconstruction-quality validation, switch from web pseudo-view candidates
to a public dataset case with real multi-view images and 3D ground truth.

The web first10 set remains useful for:

```text
pseudo-view failure taxonomy
VLM/manual candidate filtering
diagnosing diffusion distortions
```

It is not suitable as the main reconstruction benchmark.

## Candidate Datasets

### 1. FaceScape

Sources:

```text
https://nju-3dv.github.io/projects/FaceScape/
https://github.com/zhuhao-nju/facescape
```

Official repository states that FaceScape includes:

```text
multi-view images
camera parameters
corresponding 3D face mesh
>400k images
359 identities x 20 expressions x about 60 views
non-commercial research license
```

Local sample/access status:

```text
external/facescape/samples/download_sample.sh works.
The downloaded sample has metadata for 58 views, 52 valid view flags, two
public sample images, camera parameters, distortion parameters, and a
corresponding 4_anger.ply mesh.
The sample readme says not to distribute it, so raw images/mesh/thumbnails stay
out of git.
Metadata audit:
experiments/metrics/facescape_sample_access_audit_20260519.md
```

Use plan:

```text
Apply/request access.
Download one identity, one neutral expression, about 6-12 calibrated views.
Export a compact repo-safe case manifest, thumbnails, and GT mesh metadata.
Do not commit restricted raw data unless license permits.
If using FaceScape, first choose a publishable-list identity or keep all visual
outputs local and commit only metadata-level results.
```

Why first choice:

```text
It directly matches single-view face reconstruction with known mesh/cameras.
It is small enough to create a compact case once access is approved.
```

### 2. Multiface

Source: https://github.com/facebookresearch/multiface

Official repository states that Multiface includes:

```text
13 identities
multi-view capture with facial expressions
roughly 40 to 160 camera views per frame
tracked meshes, head poses, textures, camera intrinsics/extrinsics
mini-dataset option around 16.2 GB
full dataset around 65 TB
```

Use plan:

```text
Try mini-dataset first.
Extract one identity, one neutral-ish frame, 6-12 cameras, tracked mesh, and calibration.
Use it as a positive-control sparse-view reconstruction case.
```

Why second choice:

```text
Very strong GT/camera package, but heavier than FaceScape and may be more
dynamic-expression oriented.
```

### 3. NeRSemble

Source: https://tobias-kirschstein.github.io/nersemble/

Official project page states that NeRSemble uses:

```text
16 calibrated machine-vision cameras
7.1 MP synchronized images
73 fps
over 4700 sequences
more than 220 human heads
dataset access and download links
```

Use plan:

```text
Use only if access and download size are manageable.
Extract one subject, one frame/timestep, sparse views, masks/cameras if available.
Use primarily for novel-view / radiance-field comparison, not mesh-accuracy.
```

Why third choice:

```text
Excellent full-head multi-view data, but may be heavier to ingest than FaceScape
for a small one-month sprint.
```

### 4. UEA 3D Face Database

Source: https://uea3dfaces.org/

Official page states that UEA includes:

```text
about 100 people
about 300 high-resolution 3D face models
about 1000 photos in five facing directions
OBJ scanning set treated as ground-truth 3D structure
free for non-commercial academic research after license agreement
```

Use plan:

```text
Use as a fallback if FaceScape/Multiface access is slow.
Extract one subject with five orientations plus OBJ scan.
Good for face-surface validation; weaker for full-head/hair.
```

## Next Milestone Gate

```text
G16a: GT dataset access gate
  choose primary dataset
  confirm license and redistribution constraints
  download sample or request access
  record exact case ID and assets
  current status: FaceScape sample metadata checked; reconstruction case blocked
  until licensed/publishable or redistributable data exists

G16b: compact GT case export
  one identity
  one expression/frame
  6-12 calibrated views
  GT mesh/point cloud
  camera metadata
  repo-safe thumbnails/figures only if license allows

G16c: reconstruction rerun
  only after GT case audit passes
```
