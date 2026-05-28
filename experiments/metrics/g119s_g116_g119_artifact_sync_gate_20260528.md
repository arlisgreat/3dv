# G119S Artifact Sync Gate

Date: 2026-05-28

Verdict:

```text
PASS_ARTIFACT_SYNC_GATE_READY
```

Counts:

| field | value |
| --- | ---: |
| tracked_result_artifacts | 1664 |
| untracked_allowed_sync_candidates | 23 |
| blocked_untracked_paths | 0 |
| oversized_sync_candidates | 0 |

Untracked allowed sync candidates:

```text
experiments/figures/g116_naive_pose_crop_source_oracle_mask_diagnostic_20260528.png
experiments/metrics/g116_naive_pose_crop_source_oracle_diagnostic_20260528.json
experiments/metrics/g116_naive_pose_crop_source_oracle_diagnostic_20260528.md
experiments/metrics/g117_full_identity_confidence_eval_20260528.json
experiments/metrics/g117_full_identity_confidence_eval_20260528.md
experiments/metrics/g117_source_gated_pseudo_prior_ablation_20260528.json
experiments/metrics/g117_source_gated_pseudo_prior_ablation_20260528.md
experiments/metrics/g117_without_confidence_gate_eval_20260528.json
experiments/metrics/g117_without_confidence_gate_eval_20260528.md
experiments/metrics/g117_without_identity_gate_eval_20260528.json
experiments/metrics/g117_without_identity_gate_eval_20260528.md
experiments/metrics/g117_without_source_alpha_gate_eval_20260528.json
experiments/metrics/g117_without_source_alpha_gate_eval_20260528.md
experiments/metrics/g118_source_gated_ablation_contract_20260528.json
experiments/metrics/g118_source_gated_ablation_contract_20260528.md
experiments/metrics/g119_multicase_replication_preflight_20260528.json
experiments/metrics/g119_multicase_replication_preflight_20260528.md
experiments/metrics/g119s_g116_g119_artifact_sync_gate_20260528.json
experiments/metrics/g119s_g116_g119_artifact_sync_gate_20260528.md
scripts/g116_naive_pose_crop_diagnostic.py
scripts/g117_source_gated_pseudo_prior_ablation.py
scripts/g118_source_gated_ablation_contract.py
scripts/g119_multicase_replication_preflight.py
```

Blocked paths:

```text
none
```

Decision:

```text
All current untracked result artifacts are repo-safe sync candidates. Stage them with the milestone docs, commit, and push.
```
