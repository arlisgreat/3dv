# G13 Geometry-Prior First2 Repair Plan

Date: 2026-05-19

## Context

G10-G12 established that role-aware view selection, mask-aware losses, and foreground-canonical crops are implementation-positive but method-negative. The RI3D render sheets still collapse into card-like or fragmented structures even when the input sheets are visually better.

The next test targets the initialization failure mode: RI3D currently back-projects every image pixel into the initial point cloud from `depths<N>.npy` and `images/depth_rel/*.npy`. G11/G12 masks affect supervision losses, but they do not remove background or low-trust pixels from point-cloud initialization. This can seed a large photo-card surface before optimization starts.

## Hypothesis

Filtering RI3D initial point clouds by the trusted foreground mask, and optionally by confidence, should reduce the background card prior. If the failure is mainly initialization-driven, the G13 render sheet should show less rectangular/card geometry than G12 while preserving the same RGB/mask supervision.

## Experiment

Use the best G12 canonical input scale:

- Dataset: `experiments/ri3d_datasets/first2_fghead_maskaware`
- Variant: `roleaware_cutout75_budget4`
- Samples: `web_clean_frontal_03`, `web_clean_frontal_01`
- RI3D iterations: 500
- Mask-aware loss: enabled
- New switch: point-cloud foreground filtering enabled
- Implementation note: RI3D's GaussianModel assumes the same point count per view when `mono_d_so_enable=True`, so the filter must use a dynamic equal-points-per-view target rather than independently keeping every foreground pixel.

Planned command:

```bash
ITERATIONS=500 GPU=<idle_gpu> USE_MASK=1 PCD_MASK_FILTER=1 \
PCD_CONF_THRESHOLD=0.0 PCD_MIN_POINTS=256 PCD_POINTS_PER_VIEW=0 \
DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware \
OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 \
VARIANTS_STR="roleaware_cutout75_budget4" \
SAMPLES_STR="web_clean_frontal_03 web_clean_frontal_01" \
bash scripts/run_ri3d_first2.sh
```

## Success Criteria

Implementation pass:

- RI3D init and train complete for both first2 samples.
- MP4 render outputs are valid and committed under `experiments/reconstructions/`.
- CSV/PNG/MD summaries are committed under `experiments/metrics/` and `experiments/figures/`.
- The RI3D behavior change is exported as a patch under `patches/ri3d/`.

Method signal:

- Positive if render sheets show visibly reduced rectangular background/card structures compared with G12 fghead mask-aware.
- Negative if point-cloud filtering reduces point count but leaves the same card/fragments, indicating that geometry must come from a stronger LAM/FLAME mesh prior or a different 3D backbone rather than RI3D depth initialization alone.

## Rollback

The change is controlled by `PCD_MASK_FILTER=1` in `scripts/run_ri3d_first2.sh` and new RI3D CLI flags. Default behavior remains unchanged.
