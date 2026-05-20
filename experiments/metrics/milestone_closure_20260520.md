# Milestone Closure

Date: 2026-05-20

Closure verdict:

```text
NO_FEASIBLE_LOCAL_MILESTONE_LEFT_UNRECORDED
OLD_PSEUDOVIEW_RI3D_ROUTE_INVALID_FOR_QUALITY_CLAIMS
REAL_GT_BENCHMARK_REQUIRED_BEFORE_NEW_RECONSTRUCTION_CLAIMS
H3DS_FULL_BENCHMARK_ACCESS_STILL_EXTERNAL
REAL_GT_INTAKE_READY_LOCALLY
G20_BENCHMARK_PIVOT_COMPLETE
G21_REAL_GT_COMPACT_CASE_PASS_LOCAL
G22_REAL_GT_RECONSTRUCTION_PREFLIGHT_REQUIRED
G22_BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER
```

Completed or closed milestones:

| Gate | Closure | Evidence |
| --- | --- | --- |
| G0-G7 | complete | Smoke, first10, pseudo-view ranking, masks, filters, and RI3D loop run. |
| G8-G14 | diagnostic complete | RI3D repair attempts run, but quality claims are downgraded. |
| G15 | complete, training blocked | Candidate-pool and corrected 3x2 audits block web first10 training. |
| G16a | superseded by G21 local pass | H3DS/full benchmark access still external; local Multiface debug compact case now handles the immediate benchmark premise. |
| G16a-local | complete, intake-only | Multiface route/schema recorded; metadata/KRT/frame-list checks pass. |
| G16b | complete | CC0 head positive-control gate passes. |
| G17 | complete for sprint | Positive-control RI3D iter10/iter500 execute and export, but visual quality fails. |
| G18 | complete | Corrected first10 failure taxonomy records diagnostic-only conclusion. |
| G19 | complete | Conservative paper package, figure list, claims, and limitations recorded. |
| G20 | complete | Real-GT benchmark pivot, route audit, and model/data distribution gate recorded in `experiments/metrics/real_gt_benchmark_pivot_20260520.md`. |
| G21 | complete locally | Multiface debug compact case passes structural and VLM/manual real-GT gate; raw person-identifying assets stay under `3dv_work`, and repo records only metrics/hashes/mask-only summary. |
| G22 | blocked before training | Current RI3D/evaluation adapter does not preserve Multiface per-view intrinsics, real-camera depth/conf priors, or held-out/mesh metrics; no GPU training started. |

Current stop condition:

```text
The local sprint has verified the old route enough for diagnostic value only:
failure-aware gating is necessary, candidate hygiene is not training validity,
and the current RI3D reconstruction path is not a solved quality route. Further
quality claims require fixing the G22 real-camera adapter blockers first.
```

Do not do next:

```text
Do not train from experiments/downstream_datasets.
Do not scale web first10/first30 reconstruction even though G21 passes locally;
that pass applies to a real captured Multiface case, not web pseudo views.
Do not claim G17 positive-control visual quality as a pass.
Do not treat synthetic positive control as a real-capture benchmark.
```

Next legitimate branches:

```text
1. Real GT branch: implement a local-only Multiface real-camera adapter, then
   rerun G21/G22 before selecting an idle GPU.
2. Benchmark branch: add mesh z-buffer depth/conf and held-out/mesh metrics
   without committing raw person-identifying data.
3. Writing branch: draft the diagnostic/gate paper, with G21 as the benchmark
   premise pass and G22 as a model/data mismatch stop condition.
```
