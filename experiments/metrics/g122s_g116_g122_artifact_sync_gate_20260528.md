# G122S Artifact Sync Gate

Date: 2026-05-28

Verdict:

```text
PASS_ARTIFACT_SYNC_GATE_READY
```

Counts:

| field | value |
| --- | ---: |
| tracked_result_artifacts | 1683 |
| untracked_allowed_sync_candidates | 23 |
| blocked_untracked_paths | 0 |
| oversized_sync_candidates | 0 |

Untracked allowed sync candidates:

```text
experiments/figures/g116_naive_camera_crop_audit_20260528.png
experiments/metrics/g116_naive_camera_crop_audit_20260528.json
experiments/metrics/g116_naive_camera_crop_audit_20260528.md
experiments/metrics/g116_source_gated_pseudo_prior_ablation_20260528.json
experiments/metrics/g116_source_gated_pseudo_prior_ablation_20260528.md
experiments/metrics/g117_g116_full_aware_ablation_eval_20260528.json
experiments/metrics/g117_g116_full_aware_ablation_eval_20260528.md
experiments/metrics/g118_g116_without_identity_gate_eval_20260528.json
experiments/metrics/g118_g116_without_identity_gate_eval_20260528.md
experiments/metrics/g119_g116_without_confidence_gate_eval_20260528.json
experiments/metrics/g119_g116_without_confidence_gate_eval_20260528.md
experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.json
experiments/metrics/g120_g116_six_arm_ablation_summary_20260528.md
experiments/metrics/g121_nersemble_source222200042_pseudo_input_prep_20260528.json
experiments/metrics/g121_nersemble_source222200042_pseudo_input_prep_20260528.md
experiments/metrics/g122_multicase_replication_preflight_20260528.json
experiments/metrics/g122_multicase_replication_preflight_20260528.md
experiments/metrics/g122s_g116_g122_artifact_sync_gate_20260528.json
experiments/metrics/g122s_g116_g122_artifact_sync_gate_20260528.md
scripts/g116_naive_camera_crop_audit.py
scripts/g116_source_gated_pseudo_prior_ablation.py
scripts/g120_g116_six_arm_summary.py
scripts/g122_multicase_replication_preflight.py
```

Blocked paths:

```text
none
```

Decision:

```text
All current untracked result artifacts are repo-safe sync candidates. Stage them with the milestone docs, commit, and push.
```
