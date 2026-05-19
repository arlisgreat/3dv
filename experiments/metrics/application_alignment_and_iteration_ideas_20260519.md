# Application Alignment And Iteration Ideas

Date: 2026-05-19

Source application: `QY25181-申请书-6-13.pdf`

Coordination note: a research subagent later completed a read-only PDF and
literature pass. The repo updates below fold that result into the current
experiment path.

## Application Target

The final application is not just a LAM baseline. The target system is:

```text
single 2D portrait/head image
-> diffusion-generated multi-view priors for invisible regions
-> PanoHead-style 360 full-head modeling
-> replace NeRF rendering with 3D Gaussian representation
-> Transformer/style consistency constraints across input and pseudo views
-> FLAME/FaceVerse/3DMM structural prior for stable geometry and animation
```

The proposed key problems are:

```text
NeRF efficiency bottleneck in PanoHead-style full-head modeling
incomplete back-head/ear/invisible-region reconstruction from one image
style drift and identity loss in diffusion pseudo views
optimization instability and geometry distortion without explicit priors
```

Therefore, the current repository experiments should be interpreted as a
front-end diagnostic stage:

```text
LAM validates the one-shot Gaussian-head baseline and local environment.
Zero123++ validates whether diffusion pseudo views are useful enough to trust.
View-budget and failure-taxonomy experiments decide which pseudo views should
be passed to the later PanoHead/Gaussian/FLAME reconstruction route.
```

## Recent Work Checked

Primary sources checked on 2026-05-19:

```text
PanoHead, 2023-03-23
https://arxiv.org/abs/2303.13071

3D Gaussian Splatting, 2023-08-08
https://arxiv.org/abs/2308.04079

Zero123++, 2023-10-23
https://arxiv.org/abs/2310.15110

FaceLift, 2024-12-23
https://arxiv.org/abs/2412.17812

GAF: Gaussian Avatar Reconstruction from Monocular Videos via Multi-view Diffusion, 2024-12-13
https://arxiv.org/abs/2412.10209

Consistency Diffusion Models for Single-Image 3D Reconstruction with Priors, 2025-01-28
https://arxiv.org/abs/2501.16737

LAM: Large Avatar Model for One-shot Animatable Gaussian Head, 2025-02-25
https://arxiv.org/abs/2502.17796
https://aigc3d.github.io/projects/LAM/

Avat3r, 2025-02-27
https://arxiv.org/abs/2502.20220

RI3D, 2025-03-13
https://arxiv.org/abs/2503.10860

GS-Diff: Diffusion-Guided Gaussian Splatting, 2025-04-02
https://arxiv.org/abs/2504.01960

SEGA, 2025-04-19
https://arxiv.org/abs/2504.14373

Dream, Lift, Animate, 2025-07-21
https://arxiv.org/abs/2507.15979

MoGA, 2025-07-31
https://arxiv.org/abs/2507.23597

PanoLAM, 2025-09-09
https://arxiv.org/abs/2509.07552

Generalizable and Animatable 3D Full-Head Gaussian Avatar from a Single Image, 2026-01-19
https://arxiv.org/abs/2601.12770

VASA-3D, 2025-12-16
https://arxiv.org/abs/2512.14677

Splatent, 2025-12-10 / revised 2026-04-28
https://arxiv.org/abs/2512.09923

OMEGA-Avatar, 2026-02-12
https://arxiv.org/abs/2602.11693

OMG-Avatar, 2026-03-02
https://arxiv.org/abs/2603.01506
```

## Literature Implications

Recent work has moved strongly toward feed-forward Gaussian full-head avatars:

```text
LAM uses FLAME canonical points as Transformer queries to predict canonical
Gaussian attributes from one image.

FaceLift uses a multi-view latent diffusion model followed by a transformer
reconstructor to produce 360-degree 3D Gaussian head splats.

PanoLAM, OMEGA-Avatar, OMG-Avatar, and the 2026 full-head Gaussian avatar work
all point to the same target: one-shot, 360-complete, animation-ready Gaussian
avatars without heavy test-time optimization.

RI3D and Consistency Diffusion both support separating visible-region fidelity
from missing-region hallucination/repair instead of trusting every generated
view equally.

GS-Diff supports using diffusion pseudo-observations for sparse 3DGS, but also
adds appearance/depth/regularization components; this reinforces that pseudo
RGB alone is not a complete supervision protocol.

VASA-3D and Splatent both point at robust losses and multi-view consistency as
current bottlenecks. This matches the G9 finding that metadata-only roles and
desaturated geometry-only views do not fully remove 3D artifacts.

MoGA explicitly argues that sparse 2D diffusion views can be inconsistent and
can create 3D artifacts, which matches the first10 observations here.
```

The application remains technically valid, but the pitch should be tightened:

```text
Do not claim novelty just for "single image -> Gaussian head"; that area is
moving fast.

Focus the repo contribution on pseudo-view reliability, style/identity filtering,
and failure-aware integration into a PanoHead/Gaussian/3DMM pipeline.

Treat LAM/PanoLAM/OMEGA/OMG as strong baselines or design references rather than
as work to duplicate blindly.
```

## Iteration Ideas

Short-term, already supported by the current repo:

```text
1. steps20 vs steps75 pseudo-view reliability.
2. budget=1/2/4/6 view selection.
3. failure taxonomy and unsafe-view rejection.
4. curated first10 -> first30/first50 expansion with the same manifest groups.
5. replacement of cheap histogram/Haar scoring with a face-embedding identity filter.
6. RI3D first2 raw75_all6/raw75_budget4/cutout75_budget4_masked downstream smoke.
```

Medium-term architecture:

```text
1. Use selected pseudo views as conditional supervision for a Gaussian head
   reconstruction baseline.
2. Add FLAME/FaceVerse fitting to each input and record whether geometry priors
   predict failure cases earlier than image heuristics.
3. Build trusted-region masks: visible input face and high-confidence generated
   regions supervise texture; background/photo-frame regions are ignored.
4. Compare LAM, PanoLAM/OMEGA-style feed-forward references, and a lightweight
   PanoHead-to-Gaussian adaptation if implementation time allows.
5. Add a RI3D-inspired two-stage protocol: identity/visible regions first,
   missing side/back regions second with lower identity weight.
6. Add FLAME normal/depth compatibility scoring before reconstruction, borrowing
   the GAF direction without training a new diffusion model.
7. Patch RI3D locally so identity_supervision and geometry_only affect RGB/depth
   losses differently, with reject roles excluded before optimization.
8. Add spatial mask-aware supervision after G10: scalar per-view role weights
   reduce the numeric loss but do not remove background/photo-card artifacts.
9. After G11, add foreground-canonical crop/recenter before RI3D conversion:
   masking alone removes background loss pressure but still lets Gaussians fit
   small off-center fragments.
10. Add mask-loss ablations: mask RGB only, mask RGB plus silhouette, and
    geometry_only depth/silhouette only. Record foreground loss, background
    leakage, silhouette BCE, and mask coverage instead of final training loss
    alone.
11. After G12, stop adding RI3D crop/mask variants until a structural prior is
    present. LAM/FLAME/full-head depth, normal, silhouette, or initialization
    should be tested before any first10 expansion.
```

High-risk / rollback-monitored work:

```text
1. Modifying PanoHead internals to replace NeRF with Gaussian rendering.
2. Training any Transformer consistency model from scratch.
3. Adding large datasets or generated MP4/mesh/PLY dumps to the repository.
4. Changing third-party repos under external/ without exporting patches.
```

## Current Experimental Conclusion

The first10 steps75 run and RI3D first2 smoke partially verify the iteration
hypothesis:

```text
higher diffusion steps improve many samples but hurt some hard identity/hair cases.
all six views are not safe as priors.
budget4 selected views currently look more defensible than blind budget6.
diffusion pseudo-view quality must be filtered before any Gaussian/PanoHead fusion.
RI3D first2 160px iter50 closes the downstream loop, but the MP4 renders still
show smoke-level artifacts and cannot yet prove final reconstruction quality.
RI3D first2 160px iter500 confirms raw75_all6 is risky, but filtered variants
remain ambiguous.
RI3D first2 role-aware iter500 confirms the role-aware data path works, but
metadata/desaturation alone is not enough to make a stable final 3D win.
RI3D first2 role-weighted iter500 confirms explicit per-view role weights work,
but scalar weights alone are still insufficient for visual quality.
RI3D first2 mask-aware iter500 confirms spatial masks can be passed through
the RI3D data loader and training loss, but foreground-only loss still produces
fragmented/card-like renders without subject recentering or structural priors.
RI3D first2 foreground-canonical ablations improve input scale and remove
disconnected components, but both USE_MASK=1 and USE_MASK=0 still render
card-like fragments. The repeated failure now points to missing structural
geometry rather than only pseudo-view selection, masks, or crop scale.
```

The next concrete experiment should keep the same first2 samples and introduce
a LAM/FLAME/full-head geometry proxy before further RI3D pseudo-view variants.
Expand to first10 or first30/first50 only after the geometry-prior path changes
the render sheets, not merely the training loss.
