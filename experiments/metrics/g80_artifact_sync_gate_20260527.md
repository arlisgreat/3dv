# G80 Artifact Sync Gate

Date: 2026-05-27

Verdict:

```text
PASS_ARTIFACT_SYNC_GATE_READY
```

Counts:

| field | value |
| --- | ---: |
| tracked_result_artifacts | 1578 |
| untracked_allowed_sync_candidates | 18 |
| blocked_untracked_paths | 0 |
| oversized_sync_candidates | 0 |

Untracked allowed sync candidates:

```text
experiments/figures/g76_lam_native_gaussian_source220700191_mask_audit_20260527.png
experiments/figures/g79_lam_native_gaussian_source220700191_frustum_guard_mask_audit_20260527.png
experiments/metrics/g74_lam_native_gaussian_source220700191_render_20260527.json
experiments/metrics/g74_lam_native_gaussian_source220700191_render_20260527.md
experiments/metrics/g74_lam_source220700191_inference_20260527.json
experiments/metrics/g74_lam_source220700191_inference_20260527.md
experiments/metrics/g75_lam_native_gaussian_source220700191_eval_20260527.json
experiments/metrics/g75_lam_native_gaussian_source220700191_eval_20260527.md
experiments/metrics/g76_lam_native_gaussian_source220700191_visual_gate_20260527.json
experiments/metrics/g76_lam_native_gaussian_source220700191_visual_gate_20260527.md
experiments/metrics/g77_lam_native_gaussian_source220700191_frustum_guard_render_20260527.json
experiments/metrics/g77_lam_native_gaussian_source220700191_frustum_guard_render_20260527.md
experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.json
experiments/metrics/g78_lam_native_gaussian_source220700191_frustum_guard_eval_20260527.md
experiments/metrics/g79_lam_native_gaussian_source220700191_frustum_guard_visual_gate_20260527.json
experiments/metrics/g79_lam_native_gaussian_source220700191_frustum_guard_visual_gate_20260527.md
experiments/metrics/g80_artifact_sync_gate_20260527.json
experiments/metrics/g80_artifact_sync_gate_20260527.md
```

Blocked paths:

```text
none
```

Decision:

```text
All current untracked result artifacts are repo-safe sync candidates. Stage them with the milestone docs, commit, and push.
```
