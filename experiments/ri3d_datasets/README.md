# RI3D Datasets

This directory stores RI3D-compatible downstream inputs generated from:

```bash
python3 scripts/prepare_ri3d_dataset.py --overwrite
```

Current pilot:

```text
experiments/ri3d_datasets/first2/
experiments/ri3d_datasets/first2_160/
```

It contains 2 samples x 3 variants:

```text
raw75_all6
raw75_budget4
cutout75_budget4_masked
```

Each scene is ready for `external/ri3d` and includes:

```text
images/
images/depth_rel/
transforms.json
train_test_split_<N>.json
depths<N>.npy
confs<N>.npy
source_metadata.json
```

The depth files are simple CPU-generated bootstrap priors. They are not ground
truth and should be treated as a controlled pilot scaffold for comparing raw vs
filtered pseudo-view inputs.

`first2` is the 320px conversion. `first2_160` is a smaller reproducibility
copy used for the first RI3D downstream smoke:

```bash
python3 scripts/prepare_ri3d_dataset.py --output-root experiments/ri3d_datasets/first2_160 --image-size 160 --overwrite
```

Generated `point_cloud.ply` files are local RI3D bootstrap artifacts and are
ignored to keep GitHub checkpoints compact.
