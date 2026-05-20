# Monitor Literature / VLM Gate

Date: 2026-05-20

Scope:

```text
milestone / literature / VLM-gate monitor only
read README.md, MILESTONES.md, experiments/metrics closure docs, experiment artifacts, and QY25181 PDF best-effort
write scope limited to this file
no MILESTONES.md edit
```

## Executive Verdict

```text
KEEP_G34_G36_CLOSURE
OLD_PSEUDO_VIEW_RI3D_ROUTE_DIAGNOSTIC_ONLY
REAL_GT_BENCHMARK_REQUIRED_BEFORE_ANY_QUALITY_CLAIM
NEXT_METHOD_MUST_BE_LEARNED_PRIOR_FEED_FORWARD_OR_HEAD_ANCHORED
VLM_MANUAL_GATE_REQUIRED_FOR_EVERY_GENERATED_VIEW_POOL
```

The current repository positioning should be conservative:

```text
This sprint is a diagnostic / gate paper about why diffusion pseudo views cannot
be treated as reconstruction supervision without a real-GT benchmark gate.
```

Do not position the current experiments as proving that filtered pseudo views
improve single-image Gaussian head reconstruction. G2-G19 are useful failure
taxonomy and stop-loss evidence. G20-G36 correctly pivot to benchmark-first
validation, pass only a local Multiface compact real-GT premise, and close the
current RI3D scaling route after finite but init-level held-out metrics.

## Application Alignment

`QY25181-申请书-6-13.pdf` could not be text-extracted in this environment:
`pdftotext`, `pypdf`, `PyPDF2`, `fitz`, and `pdfplumber` are unavailable, and
`strings` only exposed compressed/font metadata. The reliable application
summary therefore comes from the project ledger in `MILESTONES.md`:

```text
single portrait/head image
-> diffusion-generated multi-view priors for invisible regions
-> PanoHead-style 360 full-head modeling
-> replace NeRF rendering with 3D Gaussian representation
-> Transformer/style consistency across input and pseudo views
-> FLAME/FaceVerse/3DMM structural priors for stable geometry and animation
```

This target is directionally aligned with recent literature, but the full
system is larger than the current one-month sprint. The sprint should keep the
paper scope at the gate/diagnostic level unless a new method and benchmark pass
fresh gates.

## Recent Literature Signal

Primary / reliable sources checked:

| Work | Date | Link | Signal for this repo |
| --- | --- | --- | --- |
| GAGAvatar | 2024-10 | https://arxiv.org/abs/2410.07971 | One-shot Gaussian head avatars are already feed-forward and use 3DMM structure; novelty is not simply converting a portrait to Gaussians. |
| FaceLift | 2024-12 / 2025 revision | https://arxiv.org/abs/2412.17812 | Single-image 360 head reconstruction uses multi-view latent diffusion plus a transformer GS reconstructor, trained with consistent synthetic multi-view supervision. This supports pseudo views as priors, not unchecked GT. |
| LAM | 2025-02 | https://arxiv.org/abs/2502.17796 | Strong one-shot animatable Gaussian head baseline; uses FLAME canonical points and Transformer image features. Current repo must compare or reposition around gates/diagnosis. |
| Avat3r | 2025-02 | https://arxiv.org/abs/2502.20220 | Few-image head avatars learn strong priors from large multi-view video data; reinforces the need for learned priors and real captured benchmarks. |
| RI3D | 2025-03 / 2026 revision | https://arxiv.org/abs/2503.10860 | Diffusion repair/inpainting is designed for coherent sparse-view inputs. It does not license malformed pseudo-view candidate pools as training data. |
| PanoLAM | 2025-09 | https://arxiv.org/abs/2509.07552 | One-shot full-head Gaussian synthesis trend is full-head, learned-prior, and structure-aware. |
| OMEGA-Avatar | 2026-02 | https://arxiv.org/abs/2602.11693 | Latest framing explicitly demands feed-forward, 360 full-head, animation-ready Gaussian avatars. |
| OMG-Avatar | 2026-03 | https://arxiv.org/abs/2603.01506 | Single-image head reconstruction uses Transformer features, depth-buffer-guided local sampling, and multi-region decomposition. |
| FFAvatar | 2026-05 | https://arxiv.org/abs/2605.15320 | Few-shot feed-forward Gaussian head reconstruction uses multi-view fusion, FLAME prediction, 360 capture fine-tuning, and NeRSemble evaluation. This is the strongest evidence that the next repo method should not be longer RI3D training. |
| Zero123++ | 2023-10 | https://arxiv.org/abs/2310.15110 | Consistent multi-view diffusion is a useful prior generator, but generated views remain predictions and must be audited before any supervision claim. |

Dataset / benchmark sources:

| Dataset | Link | Gate implication |
| --- | --- | --- |
| Multiface | https://github.com/facebookresearch/multiface | Real multi-view capture, cameras, meshes/textures, and expressions make it a credible local compact benchmark route; raw identifiable assets must remain local unless reviewed. |
| H3DS package | https://pypi.org/project/h3ds/ | Strong full-head benchmark route because it exposes mesh, images, masks, cameras, default sparse-view configs, and evaluation, but access token/license are required. |
| FaceScape benchmark | https://arxiv.org/abs/2111.01082 | Strong 3D face benchmark route; local sample metadata confirms structure but sample redistribution and limited images block immediate repo-safe validation. |
| NeRSemble benchmark/toolkit | https://pypi.org/project/nersemble-benchmark/ | Relevant public benchmark direction for head avatars, but still requires dataset access and a compact auditable local case. |

## Why Real GT Is Mandatory

The core scientific risk is label substitution:

```text
diffusion pseudo view != captured view
candidate pool != training set
RI3D-readable export != validated reconstruction benchmark
synthetic positive control != real-capture performance
```

Recent methods use diffusion views as priors or generated intermediate signals,
but their quality claims rely on controlled supervision, learned priors, held-out
views, real or high-fidelity synthetic benchmarks, and explicit metrics. This
repo's web first10 pseudo views are unconstrained portraits. Their generated
side/back views can drift in identity, geometry, accessories, hair, body crop,
and background. A training loss over those images would measure agreement with
hallucinations, not reconstruction accuracy.

Minimum real-GT gate before any quality claim:

```text
same identity and static frame/expression
real captured multi-view RGB, not diffusion-generated views
per-view intrinsics and extrinsics
foreground masks or validated segmentation
GT mesh / point cloud / depth suitable for geometry checks
held-out views never used as training supervision
license/privacy policy recorded
VLM/manual contact sheet pass before GPU work
compact metrics recorded without committing raw identifiable assets
```

## Experiment Artifact Risk Checklist

Observed from existing README / metrics / experiment directories:

| Risk | Evidence | Gate verdict |
| --- | --- | --- |
| Pseudo-view candidates treated as datasets | `experiments/downstream_datasets/` contains `raw75_all6`, `raw75_budget4`, `cutout75_budget4_masked`, and role-aware exports with historical dataset naming. README now clarifies they are candidate pools only. | `BLOCKED_RECONSTRUCTION_TRAINING` |
| Stale absolute paths in metadata | G15 audit records stale absolute refs in candidate metadata; sampled metadata still contains `/home/susie_lynn/3dv/...` paths. | `PASS_DIAGNOSTIC_ONLY_WITH_WARNINGS` |
| Data distribution mismatch | Web portraits plus Zero123++ pseudo views do not match RI3D's coherent sparse-view premise or real multi-camera head benchmarks. | `BLOCKED_QUALITY_CLAIM` |
| Visual gate weakness | G15 visual audit found split bodies, rotated photo cards, cropped fragments, background/body-only pieces. | `BLOCKED` |
| Grid split contamination | G15c/G18 record historical 2x3/3x2 split bug; corrected views still have visible distortions. | `DIAGNOSTIC_ONLY` |
| Identity / geometry drift | Face identity filter and corrected taxonomy split views into identity, geometry-only, and reject; budget4 can still include severe/reject views. | `DIAGNOSTIC_ONLY` |
| RI3D result over-interpretation | G8-G14 export valid MP4/figures but show card, fragments, ghosting, and failed visual quality. | `DOWNGRADE_TO_DIAGNOSTIC` |
| Synthetic positive-control overclaim | CC0 rendered head passes plumbing but G17c visual quality fails; it is not a real-capture benchmark. | `POSITIVE_CONTROL_ONLY` |
| Numerical health gap | G27-G33 clear specific NaN classes and combined train10 is finite, but held-out metrics remain init-level. | `NO_QUALITY_GAIN` |
| VLM/manual gate missing for future pools | Current docs require VLM/manual inspection before consuming generated PNGs. Any new generated view pool without a contact sheet and recorded verdict is blocked. | `BLOCKED_UNTIL_AUDITED` |

## Milestone Monitor State

Completed / accepted:

```text
G0-G7: environment, first10, pseudo-view generation/ranking/masks/filtering, RI3D loop smoke.
G8-G14: RI3D repair/role/mask/foreground/FLAME diagnostics, downgraded to failure evidence.
G15-G19: candidate-pool audit, split correction, real-GT route audit, positive-control, paper package.
G20: real-GT benchmark pivot.
G21: local Multiface compact real-GT premise pass.
G22-G24: old adapter blocked, real-camera adapter and CPU contract repaired.
G25-G33: init/eval/numerical gates completed; finite train10 but no held-out quality gain.
G34-G36: current RI3D scaling route closed, no additional ready benchmark, method direction reset.
```

Blocked:

```text
No training from experiments/downstream_datasets.
No renewed web first10/first30 pseudo-view scaling.
No default/larger RI3D quality milestone from the current adapter/loss setup.
No public-quality claim from local Multiface raw assets until artifact/privacy review.
No stronger benchmark until H3DS / FaceScape / NeRSemble / equivalent access is resolved.
```

Next round entry gate:

```text
1. State a new method premise: learned-prior / feed-forward / head-anchored Gaussian reconstruction.
2. Choose a real-GT benchmark case with cameras, masks, held-out views, and GT geometry.
3. Run structural audit plus VLM/manual contact sheet before any GPU training.
4. Record PASS_REAL_GT_BENCHMARK and method-specific PASS_RECONSTRUCTION_TRAINING.
5. Keep held-out RGB/silhouette/depth/mesh metrics separate from training views.
6. Treat pseudo views only as conditional priors or ablations, never as GT.
```

Downgrade / rollback to diagnostic material:

```text
experiments/downstream_datasets/*
experiments/ri3d_datasets/first2*
experiments/downstream_3d/ri3d_first2*
experiments/reconstructions/ri3d_first2*
old Zero123++ first10 pseudo-view PNGs before and after resplit
CC0 positive-control RI3D iter10/iter500 quality interpretations
G25-G33 RI3D Multiface outputs beyond adapter/init/eval/numerical-smoke claims
```

## Concrete Recommendation

The most defensible next paper angle is:

```text
Diffusion pseudo views are useful as auditable priors and failure probes, but
single-image Gaussian head reconstruction claims require real-GT benchmark
gates. Candidate hygiene metrics and RI3D-readable exports are insufficient
without visual/VLM validation and held-out real captured views.
```

Implementation recommendation:

```text
Stop current RI3D scaling.
Use existing artifacts for taxonomy, gate diagrams, and negative evidence.
If coding resumes, prototype a LAM/PanoLAM/OMEGA/FFAvatar-style head-anchored
learned-prior path only after a benchmark gate passes.
Prioritize H3DS access or a license-reviewed Multiface compact protocol.
```
