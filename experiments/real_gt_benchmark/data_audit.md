# Real-GT Benchmark Manifest Audit

Date: 2026-05-20

Verdict:

```text
PASS_CURRENT_LOCAL_MANIFEST_BLOCKED_FOR_ADDITIONAL_BENCHMARKS
```

Scope:

```text
Repo-safe data audit plus benchmark manifest for the current local Multiface real-GT route. This confirms a current local benchmark exists, while additional public/licensed benchmarks remain blocked. experiments/downstream_datasets is not read and is not a verified training set.
```

Current usable case:

| field | value |
| --- | --- |
| dataset | Multiface |
| case_id | multiface_debug_6795937_e001_000102_9view |
| status | PASS_REAL_GT_BENCHMARK |
| views | 9 |
| cameras | 9 |
| license | Creative Commons Attribution-NonCommercial 4.0 International |
| raw artifact policy | metadata and hash summaries may be committed; raw RGB, masks, mesh, and identifiable contact sheets remain in 3dv_work pending artifact review |

Gate checks:

| check | status |
| --- | --- |
| g21_gate_passed | PASS |
| manifest_exists | PASS |
| view_count_6_to_12 | PASS |
| rgb_files_exist_local | PASS |
| mask_files_exist_local | PASS |
| cameras_json_exists | PASS |
| camera_count_matches_views | PASS |
| camera_intrinsics_present | PASS |
| camera_extrinsics_present | PASS |
| mesh_exists_local | PASS |
| real_capture | PASS |
| not_generated_candidate | PASS |
| same_identity_static | PASS |
| license_recorded | PASS |
| privacy_policy_recorded | PASS |
| repo_policy_keeps_raw_assets_out | PASS |
| downstream_datasets_not_used | PASS |

Other routes:

| route | status | ready | reason |
| --- | --- | --- | --- |
| H3DS v2 | blocked | False | Local wheel/config only; no H3DS_ACCESS_TOKEN or dataset files available. |
| FaceScape | blocked | False | Toolkit/sample metadata exists locally, but sample has only limited images and redistribution is blocked; full licensed case is required. |
| Multiface | current_route_only | True | Local debug compact case is already the current G21-G33 route; it is not a new benchmark and G33 shows no quality gain. |
| NeRSemble | blocked | False | No compact local dataset found; access/download is required before a gate. |
| Wikimedia/Blender CC0 head | positive_control_only | False | Repo-safe synthetic plumbing control, not a real-capture benchmark. |
| FaceScape sample local metadata | metadata_access_only | False | Sample confirms FaceScape has calibrated multi-view params and a corresponding mesh, but the public sample exposes only two images and must not be committed or redistributed. |

Decision:

```text
Use the local Multiface compact case only for auditable real-GT benchmark plumbing and held-out evaluation gates. Do not claim method quality from this manifest alone, do not train from experiments/downstream_datasets, and do not treat FaceScape sample metadata or the synthetic CC0 positive control as a ready real-capture benchmark.
```

Artifacts:

```text
experiments/real_gt_benchmark/benchmark_manifest.json
experiments/real_gt_benchmark/benchmark_manifest.csv
experiments/real_gt_benchmark/data_audit.json
experiments/real_gt_benchmark/data_audit.md
experiments/real_gt_benchmark/data_audit_summary.png
```
