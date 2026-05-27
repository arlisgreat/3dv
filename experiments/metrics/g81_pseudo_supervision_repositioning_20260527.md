# G81 Pseudo-Supervision Repositioning

Date: 2026-05-27

Premise:

```text
The valuable research question is not whether a single portrait can produce a
qualitative 3D head render. The question is whether pseudo multi-view generation
can become credible 3D Gaussian reconstruction supervision after identity
anchoring, confidence weighting, and strict real held-out camera evaluation.
```

Rejected positioning:

```text
single image -> diffusion side/back views -> 3DGS -> qualitative render
```

Reason:

```text
That story is too weak against FaceLift / HQ Head / CAP4D / GAF-style work and
does not answer whether 2D hallucinations are valid 3D supervision.
```

Accepted positioning:

```text
single-image input
-> pseudo views generated without using real multi-view supervision
-> identity-anchored and confidence-aware pseudo-view supervision
-> full-head 3DGS reconstruction
-> render into real held-out NeRSemble / RenderMe-360 / Ava-256 / FaceScape cameras
-> compare against direct single-image Gaussian and naive pseudo-view supervision
```

Required experiment arms:

| arm | supervision | expected role |
| --- | --- | --- |
| direct_single_image | source image only, no pseudo-view supervision | direct baseline |
| naive_pseudo_view | generated pseudo views without identity/confidence gating | failure-prone baseline |
| identity_confidence_pseudo_view | pseudo views with identity anchor, reliability score, trusted-region mask, role-aware losses | proposed supervision protocol |

Pass condition:

```text
The identity/confidence-aware arm must improve held-out camera metrics and
visual/VLM gates over both direct_single_image and naive_pseudo_view without
using real multi-view images as training supervision.
```

Failure condition:

```text
If the gated pseudo-supervision arm cannot improve real held-out camera
reconstruction, the correct conclusion is negative: current 2D hallucinated
pseudo views are not trustworthy 3DGS supervision.
```

Status:

```text
G77-G80 validate the real-GT renderer/evaluator/sync harness. They do not
complete the pseudo-supervision claim. G81 opens that claim with explicit
baselines, no-leakage rules, and real held-out camera evaluation.
```
