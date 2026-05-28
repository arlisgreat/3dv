# G122 Multi-Case Replication Preflight

Date: 2026-05-28

Verdict:

```text
PASS_G122_MULTICASE_REPLICATION_PREFLIGHT_RECORDED
```

Candidate source splits:

| source serial | status | direct eval | source input | pseudo views | full six-arm | next action |
| --- | --- | --- | --- | --- | --- | --- |
| 220700191 | complete_single_case_only | yes | yes | yes | yes | Use as reference; do not claim multi-case from this alone. |
| 222200042 | ready_for_pseudo_generation | yes | yes | no | no | Run source-only pseudo generation, manifest gate, source-gated ablations, and G55 eval. |

Decision:

```text
Multi-case replication is not complete. The second split has source-only input prepared and a direct eval baseline, but still lacks pseudo views, identity/confidence manifests, ablation predictions, and six-arm summary.
```
