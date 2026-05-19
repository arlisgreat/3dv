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
2. Export only a compact case manifest and allowed thumbnails/figures.
3. Confirm 6-12 valid calibrated views and GT mesh/point cloud.
4. Run visual/VLM data audit on the actual case before any reconstruction.
```
