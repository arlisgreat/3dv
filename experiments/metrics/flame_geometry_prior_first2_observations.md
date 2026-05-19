# G14 FLAME Geometry Prior First2 Observations

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

## Result

G14 is a diagnostic negative result.

The generated FLAME proxy priors are usable as repository artifacts: they are
nonblank, cover the central head/neck region, and are stored under:

```text
experiments/geometry_priors/flame_first2_proxy/
experiments/figures/flame_geometry_prior_first2_proxy_sheet.png
```

The RI3D run using those priors also completed:

```text
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_flame_proxy_vs_pcdmask_iter500_renders.png
experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500/
```

## Comparison To G13

```text
web_clean_frontal_03:
  G13 final loss: 0.1139016
  G14 final loss: 0.1279854
  visual: less card support, but upper face/texture support is also lost

web_clean_frontal_01:
  G13 final loss: 0.2007467
  G14 final loss: 0.2391389
  visual: still disconnected body/head fragments
```

All four G14 MP4s validate as 120 frames at 160x160.

## Interpretation

The simple FLAME proxy does not provide enough aligned, identity-preserving
support for RI3D. It is too generic and mainly changes point support rather
than adding a strong head reconstruction backbone.

This strengthens the current paper framing:

```text
Failure-aware pseudo-view supervision is necessary, but pseudo-view RGB/mask
filtering plus generic sparse-view 3DGS repair is not sufficient for reliable
single-image Gaussian head reconstruction.
```

The next milestone should expand first10 only as a diagnostic/failure-taxonomy
study, or switch to a positive-control LAM/PanoLAM-style head backbone before
claiming reconstruction quality.
