# G44 Similarity-Aligned LAM Geometry Diagnostic

Date: 2026-05-20

Verdict:

```text
PASS_ALIGNED_GEOMETRY_DIAGNOSTIC_ONLY_NO_RECONSTRUCTION_QUALITY_CLAIM
```

Premise:

```text
Given the G42 local LAM export and G21 real-GT Multiface mesh, fit a similarity/ICP transform from the LAM shaped mesh to the Multiface GT mesh and record a weak aligned geometry diagnostic without publishing private mesh/media artifacts.
```

Data gate:

```text
PASS_REAL_GT_DIAGNOSTIC_ONLY. Inputs are the G42 private LAM shaped mesh and the G21 local Multiface GT mesh. No experiments/downstream_datasets candidate pool, generated pseudo-view training data, or held-out RGB media are consumed. G42 visual audit still applies.
```

Geometry inputs:

| input | vertices | bbox_diag | private_path_policy |
| --- | ---: | ---: | --- |
| LAM shaped mesh | 5023 | 0.451613 | metrics/hashes only; OBJ remains under 3dv_work |
| Multiface GT mesh | 7306 | 462.264619 | metrics only; OBJ remains under 3dv_work |

Similarity/ICP alignment:

| field | value |
| --- | ---: |
| sample_count | 3000 |
| icp_iterations | 20 |
| final_scale_lam_to_gt | 884.238336 |
| determinant_rotation | 1.000000 |

Final nearest-neighbor diagnostic distances:

| metric | raw GT units | normalized by GT bbox diag |
| --- | ---: | ---: |
| lam_to_gt_mean | 12.779202 | 0.027645 |
| lam_to_gt_median | 10.628933 | 0.022993 |
| lam_to_gt_p95 | 29.746796 | 0.064350 |
| gt_to_lam_mean | 21.550446 | 0.046619 |
| gt_to_lam_median | 21.450184 | 0.046402 |
| gt_to_lam_p95 | 42.063151 | 0.090994 |
| symmetric_mean | 17.164824 | 0.037132 |

Blocked interpretations:

```text
Do not report this as final reconstruction quality.
Do not compare this directly to held-out RGB PSNR/SSIM/LPIPS.
Do not treat ICP alignment as proof that LAM recovered the real camera or metric coordinate frame.
Do not ignore coverage/topology mismatch: LAM and Multiface meshes differ around hair, neck, shoulders, and boundary support.
Do not publish the private Multiface or LAM OBJ/PLY/PNG/MP4 artifacts without explicit review.
Do not use experiments/downstream_datasets as training or evaluation data.
```

Decision:

```text
G44 is an aligned geometry diagnostic only. It is stronger than G43's independent bbox-normalized sanity because one similarity/ICP transform is fit into the GT frame, but it still lacks held-out camera rendering, verified surface correspondence, coverage trimming, and a publishable benchmark artifact package.
```
