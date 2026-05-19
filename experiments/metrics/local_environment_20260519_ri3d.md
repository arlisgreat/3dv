# Local RI3D environment notes

Date: 2026-05-19

GitHub issue: https://github.com/arlisgreat/3dv/issues/10

Purpose:

```text
Record local deviations needed to run the RI3D first2 downstream smoke under
the available CUDA 12.4 / env124 setup.
```

Runtime:

```text
GPU: 0, NVIDIA A800-SXM4-80GB, idle before launch
CUDA env: /data1/workspace/airulan/env124.sh
Conda: /data1/workspace/airulan/conda/miniconda3
Env: lam
Torch: 2.6.0+cu124
```

Local fixes:

```text
env124.sh leaves LD_LIBRARY_PATH without a separator; the active shell repaired
it with CUDA_HOME/lib64 plus ':' before running.

The lam env needed torchmetrics, gsplat, kornia, scikit-learn, and lpips for
RI3D scripts. These were installed locally in the lam conda environment.

scripts/run_ri3d_first2.sh now exports PYTHONPATH=$RI3D_ROOT so RI3D local
imports resolve from the external checkout.

scripts/run_ri3d_first2.sh and scripts/render_ri3d_first2.sh now normalize
relative DATA_ROOT/OUT_ROOT/RUN_ROOT paths before cd'ing into external/ri3d.

scripts/prepare_ri3d_dataset.py now resolves missing absolute source image
paths by falling back to src_scene/images/<basename>. This handles metadata
generated on another machine.

external/ri3d/scripts/render.py was patched locally so --render_path does not
instantiate LPIPS and download a 528MB VGG16 checkpoint. The exported patch is:
patches/ri3d/render_path_lazy_lpips.patch
```

Experiment artifacts:

```text
320px RI3D smoke was too slow for iteration work and was stopped after the
first completed scene. Its local partial output remains ignored under:
experiments/downstream_3d/ri3d_first2_smoke5/

The published smoke uses 160px inputs and 50 iterations:
experiments/ri3d_datasets/first2_160/
experiments/downstream_3d/ri3d_first2_160_iter50/

Raw PLYs and RI3D working directories are intentionally ignored because they
are large intermediate outputs. The GitHub checkpoint publishes compact CSV,
PNG, JSON, and MP4 artifacts instead.
```
