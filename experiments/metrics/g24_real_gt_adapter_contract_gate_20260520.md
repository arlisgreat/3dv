# G24 Real-GT Adapter Contract Gate

Date: 2026-05-20

Verdict:

```text
PASS_REAL_GT_ADAPTER_CONTRACT
NO_GPU_TRAINING_STARTED
```

Checks:

| Check | Result |
| --- | --- |
| g23_adapter_passed | PASS |
| adapter_root_local_only | PASS |
| transforms_global_centered_intrinsics | PASS |
| train_test_split_valid | PASS |
| all_files_exist_and_shapes_ok | PASS |
| train_masks_not_extreme | PASS |
| heldout_metrics_defined | PASS |
| raw_asset_policy_recorded | PASS |

Train/heldout split:

```text
train_ids: [0, 1, 2, 3, 4, 5]
test_ids: [6, 7, 8]
```

Train mask coverage:

```text
min=0.1714 max=0.2721 mean=0.2106
```

Metrics contract:

```text
train: 6 normalized real-camera views with RGB/mask/depth/conf arrays
heldout: 3 held-out views for silhouette IoU and later RGB/LPIPS after rendering
mesh: tracked OBJ remains local; z-buffer depth arrays are available for geometry sanity
```

Closure:

```text
PASS_REAL_GT_ADAPTER_CONTRACT: file contracts, local-only policy, train/heldout split, and depth/conf arrays pass CPU gate. GPU is still not started; next step must select an idle GPU and run the smallest smoke only.
```
