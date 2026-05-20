# Final Experiment Synthesis And Gate Review

Date: 2026-05-20

Final purpose:

```text
Diagnose when diffusion pseudo views help or hurt single-image Gaussian head
reconstruction, and define a failure-aware pseudo-view supervision protocol.
```

Expected paper stance:

```text
This sprint does not claim solved single-image full-head reconstruction.
It claims that pseudo-view supervision must be gated by provenance, visual
validity, identity consistency, geometry plausibility, and reconstruction
positive controls before it can be used as 3D training evidence.
```

## Experiment Thread

The experimental path is now:

```text
QY25181 target:
  single image -> diffusion multi-view priors -> 360 head model ->
  3D Gaussian representation -> identity/style/structure consistency.

Sprint compression:
  test whether generic diffusion pseudo views are useful or dangerous for
  single-image Gaussian head reconstruction.

G0-G1:
  bring up LAM / Zero123++ and build balanced first10 portrait inputs.

G2-G6:
  generate pseudo views, compare steps20/steps75, rank view budgets, add
  subject cutouts, trusted masks, and identity/geometry/reject roles.

G7-G14:
  run RI3D plumbing and repair attempts: baseline, role-aware data, role-weighted
  loss, mask-aware loss, foreground canonicalization, point-cloud foreground
  filtering, and FLAME proxy prior.

G15:
  audit the data premise. The old downstream candidate pools are not training
  datasets, and historical per-view Zero123++ outputs were contaminated by a
  2x3/3x2 grid split bug.

G16:
  split the GT route into two gates: externally blocked real-capture data access
  and repo-safe synthetic positive control.

G17:
  run RI3D on the CC0 positive-control case. Execution and export pass, but
  visual reconstruction quality fails.

G18:
  label corrected first10 pseudo views as a failure taxonomy, not training data.

G19:
  package claims, figures, limitations, and closure state.

G16a-local:
  prepare real-GT intake with Multiface metadata/KRT/frame schema, while keeping
  real-capture reconstruction blocked until raw compact data and visual audit pass.
```

## Core Evidence

| Evidence | Result | Interpretation |
| --- | --- | --- |
| Steps20 vs steps75 | steps75 often improves candidate quality | More sampling helps some views but does not solve identity/geometry failures. |
| View budget selection | budget4 is safer than all6 | Blindly adding views can add worse supervision. |
| Subject cutout and masks | improves 2D hygiene | Better 2D candidates are still not valid 3D supervision. |
| Identity/geometry/reject roles | candidates can be stratified | Role labels are diagnostics unless downstream quality passes. |
| RI3D G8-G14 | all major variants execute | Current pseudo-view route still produces photo-card/fragments. |
| G15 audit | candidate pools fail training premise | `experiments/downstream_datasets` is candidate-pool output only. |
| G16b positive control | provenance and rendered GT gate pass | Synthetic control validates plumbing, not real-capture quality. |
| G17c iter500 | MP4 export passes, visual quality fails | Current RI3D route is not a quality solution even on positive control. |
| G18 taxonomy | 60 corrected views audited | web first10 supports failure taxonomy only. |
| G16a-local | Multiface intake schema passes | Real GT route is ready to ingest data, but reconstruction remains blocked. |

## Gate Review

Current gate ledger:

| Gate | Current verdict | Training allowed? |
| --- | --- | --- |
| web first10 corrected 3x2 | `PASS_DIAGNOSTIC_ONLY` | no |
| `experiments/downstream_datasets` candidate pools | `BLOCKED_RECONSTRUCTION_TRAINING` | no |
| CC0 mesh-derived positive control | `PASS_POSITIVE_CONTROL_ONLY` | only for plumbing / positive-control checks |
| RI3D positive-control iter500 | `PASS_EXECUTION_AND_EXPORT`, `FAIL_RECONSTRUCTION_QUALITY` | no quality claim |
| Multiface G16a-local intake | `PASS_INTAKE_READY`, `BLOCKED_REAL_CAPTURE_RECONSTRUCTION` | no |
| Future licensed real compact case | not available yet | only after fresh `PASS_RECONSTRUCTION_TRAINING` |

Hard stop rules:

```text
Do not train from experiments/downstream_datasets.
Do not claim web first10 as a reconstruction dataset.
Do not claim RI3D positive-control quality as a pass.
Do not use G16a-local as a real-capture reconstruction result.
Do not commit raw meshes, full-resolution restricted images, tarballs, PLYs,
or downstream working directories without explicit artifact review.
```

Repository hygiene note:

```text
The final audit found historical committed point_cloud.ply intermediates under
some experiments/ri3d_datasets paths. They were not introduced by the final
closure commits and are not used to upgrade any claim. Treat removal or
replacement with compact records as a separate repository-hygiene decision;
do not silently rewrite history or delete them during milestone closure.
```

## Final Milestone State

```text
G0-G7: complete.
G8-G14: execution complete, downgraded to diagnostic evidence.
G15: complete; candidate-pool training blocked.
G16a: externally blocked for real-capture reconstruction-quality validation.
G16a-local: complete as intake/readiness only.
G16b: complete as synthetic positive-control gate.
G17: complete for sprint; execution/export pass, visual quality fail.
G18: complete as corrected first10 failure taxonomy.
G19: complete as conservative paper package.
```

Closure verdict:

```text
ALL_FEASIBLE_LOCAL_MILESTONES_CLOSED
REAL_CAPTURE_RECONSTRUCTION_REMAINS_DATA_BLOCKED
PAPER_PACKAGE_READY_WITH_CONSERVATIVE_CLAIMS
```

## Literature Update

Recent work reinforces this sprint's pivot:

| Work | Direction relevant to this sprint |
| --- | --- |
| Any3DAvatar, arXiv:2604.13856 | Uses a unified dense multi-view head data suite and a structured Gaussian scaffold rather than trusting unstructured pseudo-view noise. |
| Generalizable and Animatable 3D Full-Head Gaussian Avatar from a Single Image, arXiv:2601.12770 | Uses pretrained 3D full-head priors, UV-space Gaussian primitives, and parametric-face structure. |
| High-Quality 3D Head Reconstruction from Any Single Portrait Image, arXiv:2503.08516 | Builds a high-quality 96-view portrait dataset and adds identity/expression-aware multi-view diffusion guidance. |
| SEGA, arXiv:2504.14373 | Combines generalized prior models, 3D priors from multi-view/multi-expression/multi-ID data, and FLAME-based UV Gaussian structure. |
| Avat3r, arXiv:2502.20220 | Learns a powerful head prior from large multi-view video data and uses dense geometric/feature cues. |
| GAF, arXiv:2412.10209 | Uses FLAME-normal-conditioned multi-view head diffusion and evaluates on NeRSemble, showing the importance of view/structure control. |
| FaceLift, arXiv:2412.17812 | Uses head-specific multi-view latent diffusion and a Gaussian-splat reconstructor trained with synthetic head supervision. |
| MoGA, arXiv:2507.23597 | Uses a generative 3D avatar prior to regularize sparse/inconsistent 2D diffusion views. |
| HuGDiffusion, arXiv:2501.15008 | Directly generates 3DGS attributes using human priors and proxy 3D Gaussian supervision. |
| AdaHuman, arXiv:2505.24877 | Couples multi-view diffusion with 3DGS reconstruction in the diffusion process to preserve consistency. |

Literature implication:

```text
The field is moving toward structured 3D priors, dense or curated multi-view
supervision, identity/expression guidance, and joint diffusion-3D consistency.
The repo's negative/diagnostic results are therefore useful: they show why a
generic Zero123++ candidate pool and weak 2D selection metrics should not be
treated as valid 3D supervision.
```

## Next Legitimate Branches

```text
1. Real-GT branch:
   finish Multiface/H3DS/FaceScape compact raw image + mesh acquisition, create
   a repo-safe contact sheet, and run a fresh visual gate.

2. Method branch:
   add a stronger structured prior before another reconstruction attempt:
   FLAME/UV Gaussian scaffold, Plucker-aware scaffold, head-specific diffusion,
   DUSt3R-style geometry, or a learned full-head 3D prior.

3. Writing branch:
   draft the paper around failure-aware pseudo-view supervision, candidate-pool
   invalidity, corrected failure taxonomy, and positive-control failure analysis.
```

Sources checked:

```text
https://arxiv.org/abs/2604.13856
https://arxiv.org/abs/2601.12770
https://arxiv.org/abs/2503.08516
https://arxiv.org/abs/2504.14373
https://arxiv.org/abs/2502.20220
https://arxiv.org/abs/2412.10209
https://arxiv.org/abs/2412.17812
https://arxiv.org/abs/2507.23597
https://arxiv.org/abs/2501.15008
https://arxiv.org/abs/2505.24877
https://github.com/facebookresearch/multiface
```
