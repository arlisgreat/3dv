# G21 Real GT Benchmark Gate

Date: 2026-05-20

Gate verdict:

```text
BLOCKED_EXTERNAL_ACCESS
NO_GPU_TRAINING_STARTED
```

Scope note:

```text
This is the repo-only dry run over experiments/gt_cases, where only synthetic
positive-control data is present. The local Multiface debug real-capture case
under 3dv_work is recorded separately in
experiments/metrics/g21_multiface_debug_gate_20260520.md and passes
PASS_REAL_GT_BENCHMARK. Raw Multiface RGB/mesh assets are intentionally not
copied into experiments/gt_cases.
```

Minimum executable checks:

| Check | Requirement |
| --- | --- |
| Images | 6-12 same-identity, same static expression/frame real captured RGB views. |
| Cameras | `cameras.json` covers every view and records intrinsics plus extrinsics. |
| Masks | One foreground mask per selected view. |
| GT geometry | Mesh or point cloud exists for the same frame/identity. |
| License/privacy | License, redistribution policy, and subject/privacy policy are recorded. |
| Distribution | Model/data distribution audit is recorded before interpreting results. |
| VLM/manual audit sheet | Contact sheet exists and reviewer records `PASS` only if subject/view/crop/mask/geometry are coherent. |

Artifacts:

```text
experiments/metrics/g21_real_gt_benchmark_gate_20260520.json
experiments/metrics/g21_real_gt_benchmark_gate_20260520.md
experiments/figures/g21_real_gt_benchmark_audit_sheet_20260520.svg
```

Case results:

| case | verdict | views | rgb | masks | cameras | geometry | failed checks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| wikimedia_blender_head_cc0 | BLOCKED_EXTERNAL_ACCESS | 8 | 8 | 8 | 8 | 0 | camera_intrinsics_present, camera_extrinsics_present, mesh_or_point_cloud_exists, compact_artifact_policy_recorded, distribution_audit_recorded, privacy_or_subject_policy_recorded, same_identity_static_frame_recorded, real_capture_not_synthetic, visual_audit_sheet_passed |

Current G21 closure:

```text
REPO_ONLY_DRY_RUN_BLOCKED_EXTERNAL_ACCESS: experiments/gt_cases contains only synthetic positive-control data. The local Multiface debug real-capture case is recorded separately in experiments/metrics/g21_multiface_debug_gate_20260520.md and passes PASS_REAL_GT_BENCHMARK; raw RGB/mesh assets stay outside the repo.
```
