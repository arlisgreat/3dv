# Face Identity Filter Observations

Date: 2026-05-19

## Scope

This pass upgrades the previous cheap CLIP/Haar proxy into an explicit
face-embedding identity filter for the current best pseudo-view frontend:

```text
subject cutout input
-> Zero123++ steps75
-> CLIP/reliability budget4 selection
-> trusted-region mask rejection
-> Facenet/MTCNN identity verification
```

Generated files:

```text
scripts/evaluate_face_identity_filter.py
experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv
experiments/metrics/face_identity_filter_summary_first10_cutout75_budget4.csv
experiments/figures/face_identity_filter_first10_cutout75_budget4.png
```

Local environment note:

```text
conda env: zero123plus
CUDA env: /data1/workspace/airulan/env124.sh
torch: 2.6.0+cu124
facenet_pytorch: installed in zero123plus env
Facenet checkpoint: .cache/torch/checkpoints/20180402-114759-vggface2.pt
download fallback: gh-proxy.com mirror for GitHub release
GPU: CUDA_VISIBLE_DEVICES=0
```

The Facenet VGGFace2 checkpoint cache initially contained a truncated file.
The corrupted local cache was moved aside and the checkpoint was re-downloaded
through a GitHub release mirror, then verified with `torch.load`.

## Result

For the 10 first10 samples and 4 selected pseudo views per sample:

```text
selected views: 40
mask accepted: 37
view face detected by MTCNN: 21
identity-supervision candidates: 20
geometry-only candidates: 14
identity rejects: 1
```

Per-sample identity-supervision counts:

```text
web_clean_frontal_01: 4 / 4
web_clean_frontal_02: 2 / 4
web_clean_frontal_03: 2 / 4
web_complex_hair_01: 2 / 4
web_complex_hair_02: 2 / 4
web_glasses_01: 3 / 4
web_glasses_02: 0 / 4
web_mild_side_01: 2 / 4
web_mild_side_02: 2 / 4
web_occlusion_lowq_01: 1 / 4, plus 1 identity reject
```

The strongest positive result is that the cutout frontend now produces at least
some identity-usable pseudo views for 8 of 10 samples. The two remaining hard
cases are informative rather than accidental:

```text
web_glasses_02: input face was not detected, so identity cannot be verified.
web_occlusion_lowq_01: one selected frontal-ish view has low identity cosine
and should be rejected despite high reliability/trusted scores.
```

## Interpretation

This verifies the current iteration hypothesis more strongly than the earlier
CLIP proxy:

```text
blind budget6 is unsafe.
steps75 alone is not sufficient.
subject cutout helps avoid photo-frame/background rotation.
masking catches geometry-risk views before identity scoring.
face embedding catches at least one identity drift that CLIP/reliability missed.
```

The new policy should distinguish supervision roles instead of treating every
accepted pseudo view as the same kind of evidence:

```text
identity_accept / identity_accept_weak:
  usable for identity-sensitive texture/face supervision.

identity_unverified + geometry_only_candidate:
  usable only for coarse geometry or non-face missing regions.

identity_reject:
  exclude from downstream reconstruction supervision.

mask_rejected:
  exclude unless manually reviewed for a targeted ablation.
```

## Decision

The current best validated pseudo-view policy is:

```text
cutout -> Zero123++ steps75 -> CLIP/reliability budget4
-> trusted-region mask
-> face identity filter
-> split selected views into identity, geometry-only, and reject sets
```

For downstream Gaussian/PanoHead/FLAME experiments, only the
identity-supervision candidates should supervise visible face identity. The
geometry-only candidates can be useful for coarse side/back coverage but should
not be used as direct identity or expression constraints.

## Next Experiment

The next useful iteration is to expand the same protocol to `first30` or
`first50`, then report:

```text
accepted mask rate
identity-supervision candidate rate
identity reject rate
per-group failure counts
whether cutout + identity filtering stays stable outside first10
```

If time permits, feed only the identity-accepted and geometry-only split into a
lightweight downstream reconstruction ablation. Do not feed all selected views
blindly into a Gaussian reconstruction baseline.
