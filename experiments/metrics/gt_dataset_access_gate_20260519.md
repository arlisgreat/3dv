# G16 GT Dataset Access Gate

Date: 2026-05-19

Gate verdict:

```text
PASS_ROUTE_IDENTIFIED
PASS_FACESCAPE_SAMPLE_METADATA_CHECK
BLOCKED_RECONSTRUCTION_RERUN_UNTIL_LICENSED_OR_REDISTRIBUTABLE_CASE_EXISTS
```

Premise:

```text
Web first10 Zero123++ pseudo views remain visibly distorted after correct 3x2
grid splitting. They are useful for failure taxonomy, but they are not valid
reconstruction-training supervision. Reconstruction-quality claims now require
a real multi-view / camera / mesh-or-point-cloud dataset case.
```

Primary route:

```text
FaceScape is the first-choice GT route because its official docs provide
multi-view images, camera parameters, validity flags, distortion parameters,
and corresponding reconstructed 3D face meshes.
```

Secondary routes checked:

```text
Multiface mini: technically strong and public under CC-BY-NC 4.0, but official
mini size is 16.2 GB and local source download was slow/unreliable in this
session. Good fallback after setting up a stable mirror/cache.

NeRSemble: excellent full-head multi-view data, but v2 access requires approval
and a private dataset URL; full dataset is too large for immediate blind download.

UEA 3D Face: useful OBJ GT fallback after license agreement, but only five
photo directions and weaker calibrated multi-view coverage.
```

Local access check:

```text
external/facescape/samples/download_sample.sh downloaded samples.tar.gz
content_length: 37,597,885 bytes
sample_mview_data/4_anger/params.json contains 58 camera entries
52 entries are marked valid
the public sample exposes only 2 high-resolution images
the sample includes a corresponding 4_anger.ply mesh
```

Repo-safe artifact:

```text
experiments/metrics/facescape_sample_access_audit_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.json
```

Policy:

```text
The FaceScape sample readme says not to distribute it. Raw images, mesh files,
thumbnails, rendered face figures, and sample tarballs stay local under ignored
external/ or 3dv_work. Only metadata-level access audits are committed.
```

Next pass condition:

```text
1. Obtain licensed FaceScape access and use a publishable-list subject, or pick
   another dataset with redistributable demo assets.
2. If using Multiface mini, first download only one identity/expression subset
   and confirm license-compatible repo outputs.
3. Export only a compact case manifest and allowed thumbnails/figures.
4. Confirm 6-12 valid calibrated views and GT mesh/point cloud.
5. Run visual/VLM data audit on the actual case before any reconstruction.
```

## 2026-05-20 Addendum

The real-capture access route remains open, but a repo-safe positive-control
route has now passed:

```text
case_id: wikimedia_blender_head_cc0
source: https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl
license: CC0 1.0 Universal Public Domain Dedication
verdict: PASS_POSITIVE_CONTROL_ONLY
```

Artifacts:

```text
experiments/metrics/gt_positive_control_route_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.json
experiments/gt_cases/wikimedia_blender_head_cc0/
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
```

Scope:

```text
This positive-control case can start G17 conversion/reconstruction plumbing.
It does not replace the need for a licensed real multi-view GT case for
real-capture reconstruction-quality claims.
```
