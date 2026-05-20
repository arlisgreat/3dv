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
G22_BLOCKED_BEFORE_TRAINING_MODEL_DATA_ADAPTER
G23_REAL_CAMERA_ADAPTER_PREFLIGHT_PASS
G24_REAL_GT_ADAPTER_CONTRACT_PASS
G25_RI3D_INIT_ONLY_SMOKE_PASS
G26_HELDOUT_RENDER_EVAL_SMOKE_PASS
G27_TRAIN10_NUMERICAL_HEALTH_BLOCKED_NAN
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
| G22 | blocked before training | Old RI3D/evaluation adapter did not preserve Multiface per-view intrinsics, real-camera depth/conf priors, or held-out/mesh metrics; direct training was blocked. |
| G23 | complete, adapter pass | Local-only Multiface adapter, mesh z-buffer depth/conf, and mask/depth-only audit figure pass preflight. |
| G24 | complete, contract pass | CPU RI3D adapter contract, local-only policy, train/test split, and metrics skeleton pass. |
| G25 | complete, init-only pass | RI3D loads the G24 adapter and saves a 67,410-point iteration-1 point cloud; no full training or quality claim. |
| G26 | complete, eval smoke pass | Held-out render/eval metrics execute from the G25 point cloud without saving PNG/JPEG/MP4; metrics remain init-only smoke values. |
| G27 | blocked | Tiny train10 executes but training loss is NaN even under plain L1-only settings; longer training is blocked. |

Current stop condition:

```text
The local sprint has verified the old route enough for diagnostic value only:
failure-aware gating is necessary, candidate hygiene is not training validity,
and the current RI3D reconstruction path is not a solved quality route. Further
quality claims require first resolving the G27 NaN loss blocker, then passing
separate real-GT training and held-out evaluation gates.
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
1. Real GT branch: G28 loss-path numerical diagnosis for the NaN train loss.
2. Benchmark branch: once G28 is fixed, implement held-out silhouette/RGB/depth/
   mesh metrics without committing raw person-identifying data.
3. Writing branch: draft the diagnostic/gate paper, with G21 as the benchmark
   premise pass and G22-G27 as adapter/init/eval/numerical gate history.
```
