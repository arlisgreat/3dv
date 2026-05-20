# G36 Method Redesign Direction

Date: 2026-05-20

Verdict:

```text
PASS_METHOD_REDESIGN_DIRECTION_NO_LONGER_RI3D_SCALING
```

Scope:

```text
Update the method direction after G33 and the latest 2026 head-avatar literature
scan.
```

Monitor report:

```text
/data1/workspace/airulan/3dv_work/agent_reports/monitor_g34_20260520.md
```

Latest literature signal:

| Work | Date | Source | Implication |
| --- | --- | --- | --- |
| FFAvatar | 2026-05-14 | https://arxiv.org/abs/2605.15320 | Few-shot feed-forward Gaussian head reconstruction now uses multi-view fusion, FLAME prediction, and high-quality 360 capture fine-tuning. |
| OMEGA-Avatar | 2026-02-12 | https://arxiv.org/abs/2602.11693 | One-shot 360 full-head Gaussian avatars are framed as feed-forward, full-head, animation-ready systems. |
| OMG-Avatar | 2026-03-02 | https://arxiv.org/abs/2603.01506 | Recent work emphasizes transformer features, depth-buffer-guided local sampling, and multi-region decomposition. |
| PanoLAM | 2025-09-09 | https://arxiv.org/abs/2509.07552 | Full-head Gaussian synthesis from one unposed image uses synthetic-data-trained feed-forward priors and FLAME/triplane-style structure. |
| LAM | 2025-02-25 | https://arxiv.org/abs/2502.17796 | A strong single-image Gaussian-head baseline already exists; novelty is not simply one-shot Gaussian head output. |
| RI3D | 2025-03-13 | https://arxiv.org/abs/2503.10860 | RI3D is appropriate for coherent sparse inputs with repair/inpainting priors, not malformed pseudo-view candidate pools or quality claims after init-level metrics. |

Method decision:

```text
Do not scale current RI3D iterations as the next method.
Use current RI3D results as numerical/diagnostic evidence.
If implementation continues, the next minimal method should be feed-forward or
learned-prior anchored: LAM/PanoLAM/OMEGA/FFAvatar style, with real-GT held-out
metrics and VLM/manual gates.
Pseudo views can only re-enter as audited conditional priors, never as
ground-truth training views.
```

Next allowed milestone:

```text
Acquire or construct a benchmark/method premise that can pass
PASS_REAL_GT_BENCHMARK plus method-specific preflight; otherwise stop at paper
packaging.
```

Artifact policy:

```text
No new media was generated for this method direction gate.
```
