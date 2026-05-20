# Milestone Closure

Date: 2026-05-20

Closure verdict:

```text
NO_FEASIBLE_LOCAL_MILESTONE_LEFT_UNRECORDED
OLD_PSEUDOVIEW_RI3D_ROUTE_INVALID_FOR_QUALITY_CLAIMS
REAL_GT_BENCHMARK_REQUIRED_BEFORE_NEW_RECONSTRUCTION_CLAIMS
REAL_CAPTURE_GT_ACCESS_BLOCKED_EXTERNALLY
REAL_GT_INTAKE_READY_LOCALLY
G20_BENCHMARK_PIVOT_COMPLETE
G21_REAL_GT_COMPACT_CASE_BLOCKED_EXTERNALLY
```

Completed or closed milestones:

| Gate | Closure | Evidence |
| --- | --- | --- |
| G0-G7 | complete | Smoke, first10, pseudo-view ranking, masks, filters, and RI3D loop run. |
| G8-G14 | diagnostic complete | RI3D repair attempts run, but quality claims are downgraded. |
| G15 | complete, training blocked | Candidate-pool and corrected 3x2 audits block web first10 training. |
| G16a | externally blocked | Real GT dataset access/license not available for publishable compact case. |
| G16a-local | complete, intake-only | Multiface route/schema recorded; metadata/KRT/frame-list checks pass, but raw compact case is not fully acquired or visually audited. |
| G16b | complete | CC0 head positive-control gate passes. |
| G17 | complete for sprint | Positive-control RI3D iter10/iter500 execute and export, but visual quality fails. |
| G18 | complete | Corrected first10 failure taxonomy records diagnostic-only conclusion. |
| G19 | complete | Conservative paper package, figure list, claims, and limitations recorded. |
| G20 | complete | Real-GT benchmark pivot, route audit, and model/data distribution gate recorded in `experiments/metrics/real_gt_benchmark_pivot_20260520.md`. |
| G21 | externally blocked | Compact licensed real-GT case still needs H3DS token or FaceScape/Multiface raw access plus visual/VLM audit. |

Current stop condition:

```text
The local sprint has verified the old route enough for diagnostic value only:
failure-aware gating is necessary, candidate hygiene is not training validity,
and the current RI3D reconstruction path is not a solved quality route. Further
quality claims require a passing licensed real-GT benchmark first.
```

Do not do next:

```text
Do not train from experiments/downstream_datasets.
Do not scale web first10/first30 reconstruction without PASS_REAL_GT_BENCHMARK.
Do not claim G17 positive-control visual quality as a pass.
Do not treat synthetic positive control as a real-capture benchmark.
```

Next legitimate branches:

```text
1. Real GT branch: obtain H3DS/FaceScape/Multiface/etc. access and rerun gates.
2. Benchmark branch: create one compact case with images, cameras, masks, and GT
   mesh/point cloud, then record PASS_REAL_GT_BENCHMARK or BLOCKED.
3. Writing branch: draft only the diagnostic/gate paper until G21 passes.
```
