# G16a-Local Real GT Intake Readiness Gate

Date: 2026-05-20

Gate verdict:

```text
PASS_INTAKE_READY
BLOCKED_REAL_CAPTURE_RECONSTRUCTION
NO_TRAINING_STARTED
```

Post-G21 update:

```text
This file remains the historical intake/readiness gate. G21 later acquired and
audited a local Multiface debug compact case with 9 same-frame real views,
KRT cameras, projected masks, and tracked mesh, recording
PASS_REAL_GT_BENCHMARK in experiments/metrics/g21_multiface_debug_gate_20260520.md.
Raw RGB/mesh assets remain under 3dv_work pending artifact review.
```

Purpose:

```text
Close the remaining local G16a planning gap without pretending that a licensed
real-capture reconstruction case has already passed. This gate prepares the
repo to ingest a real multi-view head case, records the most viable route, and
keeps reconstruction blocked until raw images, cameras, mesh/point cloud, and
visual audit all pass.
```

Primary executable route:

```text
Multiface mini / partial identity 6795937
source_repo: external/multiface
source_commit: db70c1a
license: CC-BY-NC 4.0
case target: one static E001_Neutral_Eyes_Open frame with 6-12 calibrated views
```

Why Multiface is the current best real-capture route:

```text
The official dataset provides raw multi-view images, tracked meshes/headposes,
camera calibration metadata, and per-frame assets for human faces. The license
allows non-commercial sharing/adaptation with attribution, but raw assets and
person-identifying imagery should still be staged under 3dv_work until a compact
case has an explicit repo-safe artifact review.
```

Local checks completed:

| Check | Result |
| --- | --- |
| Official repo cloned | `external/multiface`, commit `db70c1a` |
| Metadata tar downloaded | `/data1/workspace/airulan/3dv_work/datasets/multiface_6795937_e001/metadata.tar` |
| Metadata sha256 | `995deae0aa2058c5df5848b1088f0862984a096fb24383217f8168fe585f58da` |
| KRT cameras parsed | 38 cameras |
| Frame list parsed | 13,478 rows |
| E001 static-expression frames | 26 frames, `000102` to `000177` |
| Camera split config for identity 6795937 | 38 train/test cameras, 2 visual cameras |
| E001 image tar remote size | 2,964.31 MiB |
| E001 tracked-mesh tar remote size | 34.00 MiB |
| Mini config image tar sizes checked | E057 5,784.39 MiB, E061 7,309.18 MiB |
| Slow download handling | Partial E001 mesh download stopped and moved to `3dv_work/quarantine/20260520_multiface_partial/` |

Required case schema before any real-GT reconstruction:

```text
experiments/gt_cases/<case_id>/README.md
experiments/gt_cases/<case_id>/manifest.csv
experiments/gt_cases/<case_id>/cameras.json
experiments/gt_cases/<case_id>/views/*.png
experiments/gt_cases/<case_id>/masks/*.png
experiments/figures/<case_id>_contact_sheet.png
experiments/metrics/<case_id>_real_gt_gate_YYYYMMDD.{md,json}
```

Minimum raw local inputs for that future gate:

```text
1. One expression/frame with a stable face pose.
2. 6-12 raw camera images from the same frame.
3. KRT intrinsics/extrinsics for exactly those cameras.
4. The corresponding tracked mesh or point cloud.
5. A derived mask or projected mesh silhouette for visual auditing.
6. Attribution and license note for any derived PNG/MP4 committed to the repo.
```

Stop conditions:

```text
Do not start RI3D or other reconstruction training from Multiface until the
actual compact case exists and a visual/manual gate records
PASS_REAL_GT_BENCHMARK.

Do not treat this intake gate as a quality result. It is a readiness result.

Do not commit raw Multiface full-resolution images, meshes, tarballs, or partial
downloads without an explicit repo-safe artifact review.
```

Current closure:

```text
The local G16a milestone is complete as an intake/readiness gate. The original
scientific G16a goal, a licensed real-capture reconstruction-quality validation
case, remains blocked by data acquisition speed and artifact review, not by repo
planning.
```
