# First10 Pilot Observations, 2026-05-18

## Scope

Inputs:

- `experiments/inputs/first10/manifest.csv`
- `experiments/figures/first10_wikimedia_contact_sheet.png`

Runs:

- Zero123++ first10 pilot: `experiments/pseudo_views/zero123plus_first10/`
- LAM first10 baseline: `experiments/reconstructions/lam_first10/`

Metrics and figures:

- `experiments/metrics/zero123plus_first10_steps20.csv`
- `experiments/metrics/lam_first10_look_in_my_eyes.csv`
- `experiments/figures/zero123plus_first10_steps20_grids.png`
- `experiments/figures/lam_first10_look_in_my_eyes_frames.png`

## Result Summary

- Wikimedia Commons crawl produced 10 licensed pilot inputs: 3 clean frontal, 2 mild side, 2 glasses, 2 complex hair, and 1 occlusion/low-quality.
- Zero123++ `steps=20`, `seed=42` completed for all 10 samples. Each sample has `input_square.png`, `grid.png`, 6 view PNGs, and `metadata.json`.
- LAM `Look_In_My_Eyes` completed for all 10 samples. Each sample has one render MP4, one audio-attached MP4, and `metadata.json`.
- Integrity checks found 10/10 nonblank Zero123++ grids and 20/20 nonblank LAM MP4 first frames.

## Early Failure Signals

- Zero123++ often rotates the full photo/object instead of producing a face/head-specific novel view. This is most visible for old framed photographs, half-body portraits, and images with strong backgrounds.
- Identity drift is already visible at `steps=20`, especially around eyes, facial hair, glasses, and stylized black-and-white photos.
- Glasses and occlusion are useful stress cases: Zero123++ can preserve broad accessory shape in some views but frequently changes lens geometry and face structure.
- LAM gives a stronger single-image face/head baseline on this pilot set, but it still smooths texture and can hallucinate or simplify hair, hats, masks, and old-photo details.
- The pilot supports the paper framing: pseudo views should be filtered or region-weighted instead of treated as equally reliable ground-truth views.

## Iteration Ideas

- Add Zero123++ `steps=75` for a face-quality pass and compare against the current `steps=20` diagnostic pass.
- Add view budgets `1/2/4/6`, recording exact azimuth/elevation selections instead of only view counts.
- Add identity filtering before pseudo-view use: ArcFace/InsightFace similarity, face landmark consistency, or a manual 1-5 identity score.
- Add a trusted-region protocol: use input-visible facial regions strongly, and use side/back pseudo-view regions as weak or qualitative guidance.
- Split first10 into two tracks: raw in-the-wild web portraits and curated/cropped head-only portraits. The current set is useful for failure discovery but mixes full-object/background effects with head reconstruction.

## Research Context

Recent related work supports this direction:

- LAM, SIGGRAPH 2025: https://arxiv.org/abs/2502.17796
- GAGAvatar, NeurIPS 2024: https://arxiv.org/abs/2410.07971
- FaceLift, ICCV 2025: https://arxiv.org/abs/2412.17812
- RI3D, ICCV 2025: https://arxiv.org/abs/2503.10860
- Avat3r, ICCV 2025: https://arxiv.org/abs/2502.20220
- Zero123++ official code: https://github.com/SUDO-AI-3D/zero123plus
