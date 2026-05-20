# G21 Real GT Benchmark Gate

Date: 2026-05-20

Gate verdict:

```text
PASS_REAL_GT_BENCHMARK
NO_GPU_TRAINING_STARTED
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
experiments/metrics/g21_multiface_debug_gate_20260520.json
experiments/metrics/g21_multiface_debug_gate_20260520.md
/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/compact_case_000102_9view/audit/g21_multiface_gate_audit_sheet.png
experiments/figures/g21_multiface_debug_mask_gate_20260520.png
```

Visual/manual audit note:

```text
The full local RGB/mask/overlay sheet was inspected before setting
visual_verdict=PASS. The 9 views are same-subject, same-frame real captured
Multiface views; projected masks are broadly aligned with head/neck geometry.
Some close/top views are cropped, so G21 is a benchmark-premise pass, not a
method-quality result. Raw RGB/OBJ/contact-sheet artifacts remain in 3dv_work.
The committed PNG is mask-only to avoid publishing identifiable face imagery.
License/privacy boundary: CC-BY-NC 4.0, recognizable human-subject data, public
repo export limited to metrics, hashes, and mask-only PNG unless artifact review
explicitly approves derived imagery.
```

Case results:

| case | verdict | views | rgb | masks | cameras | geometry | failed checks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| gate_case | PASS_REAL_GT_BENCHMARK | 9 | 9 | 9 | 9 | 1 | none |

Current G21 closure:

```text
PASS_REAL_GT_BENCHMARK: at least one compact real-capture case passed the gate.
```
