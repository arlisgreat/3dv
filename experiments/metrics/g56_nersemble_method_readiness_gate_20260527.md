# G56 NeRSemble Method Readiness Gate

Date: 2026-05-27

Premise:

```text
Before running a learned-prior/feed-forward/head-anchored method on NeRSemble, the real-GT/data/VLM gates, model/test distribution statement, camera renderer, and held-out prediction files must all be explicit.
```

Verdict:

```text
BLOCKED_NERSEMBLE_METHOD_OUTPUT_CAMERA_RENDERER_MISSING
```

Distribution audit:

| field | value |
| --- | --- |
| candidate_method | LAM-20K baseline / learned-prior head-anchored Gaussian family |
| test_data | NeRSemble official NVS 388 GLASSES frame 0 local held-out split plus v2 017 compact visual gate |
| training_distribution_statement | LAM-20K is documented in prior project gates as trained on VFHQ + NeRSemble. |
| in_distribution_status | in-domain for NeRSemble; possible subject/dataset overlap cannot be ruled out from local metadata alone |
| allowed_interpretation | baseline sanity and in-distribution benchmark plumbing; not an unseen cross-dataset generalization claim |

Renderer/readiness checks:

| check | value |
| --- | --- |
| g52_g55_required_gates_pass | True |
| camera_renderer_script_present | True |
| camera_renderer_script | /data1/workspace/airulan/3dv/scripts/lam_render_nersemble_cameras.py |
| expected_eval_prediction_count | 3 |
| present_eval_prediction_count | 3 |
| prediction_root | /data1/workspace/airulan/3dv_work/runs/g56_nersemble_lam_eval/predictions |
| renderer_audit_json | /data1/workspace/airulan/3dv/experiments/metrics/g58_nersemble_lam_renderer_contract_audit_20260527.json |
| renderer_audit_verdict | PASS_DIAGNOSTIC_ONLY_RENDERER_CONTRACT_FAILED |
| renderer_contract_pass | False |
| raw_rgb_policy | private local only under 3dv_work; commit metrics/hashes/mask-only figures unless user explicitly reviews identifiable media |

Decision:

```text
Blocked for method-quality evaluation: data and metric gates pass, but the method prediction set lacks a passing true NeRSemble K/R/T renderer-contract audit. Do not substitute LAM motion-camera MP4s or source-to-sample frames for held-out NeRSemble camera renders.
```

Next gate:

```text
Implement or import a renderer that maps method output into the G54 NeRSemble camera intrinsics/extrinsics, then write predictions for each G55 eval serial and run the held-out evaluator.
```
