# G14 FLAME Geometry Prior First2 Plan

Date: 2026-05-19

## Context

G13 confirmed that RI3D point-cloud initialization is part of the repeated card artifact: removing background points from the initial point cloud reduced the gray rectangular cards. The remaining failure is detached foreground fragments, which suggests the initialization still lacks coherent head geometry.

Existing LAM tracking exports provide FLAME assets for the same first2 samples:

```text
external/LAM/tracking_output/export/web_clean_frontal_01/
external/LAM/tracking_output/export/web_clean_frontal_03/
external/LAM/tracking_output/tracking/*/train/mesh/frame_00000_499_lmk_init_all.obj
```

## Hypothesis

A FLAME-derived depth/confidence proxy, rendered into the same RI3D view slots and used for point-cloud initialization, should produce a more coherent foreground support than the smooth analytic depth used through G13.

## Experiment

Generate a new data-only RI3D root:

```text
experiments/ri3d_datasets/first2_flame_proxy_pcdmask/
```

from the G12 fghead data:

```text
experiments/ri3d_datasets/first2_fghead_maskaware/
```

For each frame:

1. Copy the G12 RGB/mask/transforms unchanged.
2. Render a normalized FLAME OBJ proxy into the RI3D frame azimuth/elevation.
3. Replace `depths4.npy` and `images/depth_rel/*.npy` with the FLAME proxy depth.
4. Replace `confs4.npy` with FLAME proxy confidence so `PCD_CONF_THRESHOLD` can keep the FLAME-supported region.
5. Preserve source metadata and write prior metadata under `source_metadata.json`.

Planned training command:

```bash
GPU=<idle_gpu> USE_MASK=1 PCD_MASK_FILTER=1 PCD_CONF_THRESHOLD=0.5 \
PCD_MIN_POINTS=256 PCD_POINTS_PER_VIEW=0 ITERATIONS=500 \
DATA_ROOT=experiments/ri3d_datasets/first2_flame_proxy_pcdmask \
OUT_ROOT=experiments/downstream_3d/ri3d_first2_flame_proxy_pcdmask_iter500 \
VARIANTS_STR="roleaware_cutout75_budget4" \
SAMPLES_STR="web_clean_frontal_03 web_clean_frontal_01" \
bash scripts/run_ri3d_first2.sh
```

## Success Criteria

- The FLAME proxy sheet is nonblank and aligned enough to cover the central head/upper-body region.
- Both first2 RI3D init/train runs complete.
- Render sheets reduce detached fragments beyond G13.
- CSV/PNG/MP4/MD artifacts are synced to GitHub.

## Failure Criteria

- FLAME proxy projection is visibly misaligned or too generic to use.
- RI3D still renders detached fragments after the FLAME proxy.
- The best paper framing becomes a diagnostic result: pseudo-view RGB/mask filtering helps data hygiene, but this RI3D path needs stronger full-head priors or a different backbone.
