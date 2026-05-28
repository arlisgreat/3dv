# G116 Naive Pose/Crop/Source/Oracle Diagnostic

Date: 2026-05-28

Verdict:

```text
PASS_G116_NAIVE_POSE_CROP_SOURCE_ORACLE_DIAGNOSTIC
```

Premise:

```text
Check whether the G81 naive pseudo-view RI3D baseline failed because of camera pose/crop/source-render issues rather than only pseudo-view quality.
```

Summary:

| arm | source IoU | source cov ratio | eval IoU | eval cov ratio | eval bbox IoU | eval center err |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| direct_lam_g77 | 0.9152944137259885 | 1.058427787227802 | 0.8996994861687494 | 1.0772668701563113 | 0.9895981660566141 | 0.0046787273861509755 |
| naive_ri3d_g102 | 0.3428303711577204 | 0.5265596418494494 | 0.30971166292766217 | 0.5223985161181396 | 0.8141463531919966 | 0.05510774915262876 |
| strict_aware_ri3d_g102 | 0.28485062391838967 | 0.38742415953084947 | 0.30652221427156784 | 0.4045649432252394 | 0.758629417080504 | 0.05502779951559611 |
| g110_source_gated | 0.952514256536123 | 0.9979793438180303 | 0.9150921915885543 | 1.0069176384606113 | 0.9883583254507168 | 0.005302557704304434 |
| gt_pointcloud_oracle_g59 | 0.582903275432855 | 0.5902608060319354 | 0.5236046612111784 | 0.5291783448961352 | 0.885387319519758 | 0.04082701041244405 |

Pose/crop/source/oracle interpretation:

```text
Naive RI3D failure is not safe to attribute only to pseudo-view image quality. The render manifest shows the same NeRSemble K/R/T adapter and a sign-flip/source-mask plus eval-frustum guard were used, with valid-z/in-frame evidence rather than a catastrophic empty-pose failure (min eval in-frame 0.4821). However, the naive source render already under-covers the source mask (IoU 0.3428303711577204, coverage ratio 0.5265596418494494), so source-space crop/scale/geometry mismatch is present before held-out evaluation. Direct LAM/G110 have much stronger mask support (direct eval IoU 0.8996994861687494; G110 is recorded separately in G113), while the GT pointcloud oracle confirms KRT plumbing is usable but itself under-covers the full alpha mask (oracle eval IoU 0.5236046612111784; G60 mean mask IoU 0.5539237552340944). Conclusion: G110's current value is that it bypasses pseudo-view geometry/pose/crop risk by preserving direct geometry; the naive baseline remains a failed baseline that needs stronger pose/crop/oracle复核 before using it as evidence against pseudo-view supervision quality alone.
```

Repo-safe mask sheet:

```text
/data1/workspace/airulan/3dv/experiments/figures/g116_naive_pose_crop_source_oracle_mask_diagnostic_20260528.png
1c14a8592cd799cde64512318806059e5cb38094a47c756ce16e3d0c49944491
```

Decision:

```text
Naive failure remains real, but current evidence supports a mixed source/crop/geometry-risk diagnosis, not a pure pseudo-view-quality diagnosis.
```

Next gate:

```text
Run ablations with direct geometry preserved, then add multi-case replication; for naive RI3D, add a stronger source-render/oracle-aligned pose-crop repair before drawing final conclusions.
```
