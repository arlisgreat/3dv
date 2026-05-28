# G118 Source-Gated Pseudo Prior Ablation Contract

Date: 2026-05-28

Verdict:

```text
PASS_G118_SOURCE_GATED_ABLATION_CONTRACT_SINGLE_CASE
```

Arms:

| arm | role | PSNR | mask IoU | coverage | note |
| --- | --- | ---: | ---: | ---: | --- |
| direct_lam_g77 | direct single-image Gaussian / LAM direct | 12.690455 | 0.900017 | 0.669642 | No pseudo views; tests direct prior strength. |
| naive_ri3d_g102 | naive pseudo-view pipeline | 4.904916 | 0.309712 | 0.324068 | Failed baseline; G116 says failure has pose/crop/source/geometry caveats. |
| full_identity_confidence_g117 | identity/confidence-aware pseudo prior | 13.068552 | 0.915092 | 0.626027 | Direct geometry plus strict identity/confidence pseudo color prior. |
| without_identity_gate_g117 | w/o identity gate | 12.923015 | 0.915092 | 0.626027 | Uses all aware train candidates without identity weighting. |
| without_confidence_gate_g117 | w/o confidence gate | 13.068995 | 0.915092 | 0.626027 | Uses strict identity views without confidence weighting. |
| without_source_alpha_gate_g117 | w/o source-gated alpha | 13.068552 | 0.899658 | 0.670091 | Fixed alpha threshold u8=8 instead of source-mask-selected threshold. |
| without_direct_geometry_g104 | w/o source-gated/direct geometry prior | 4.778723 | 0.306522 | 0.252817 | Old strict-aware RI3D pseudo geometry arm; removes G110 direct geometry preservation. |

Findings:

```text
Direct LAM prior is strong on this source split. Full G117/G110 beats direct and naive. Identity gate is a small positive RGB contributor because removing it lowers PSNR. Confidence weighting is not supported as a positive contributor in this single case because w/o confidence is numerically tied/slightly higher. Source-selected alpha mainly helps mask IoU: fixed alpha keeps PSNR but drops mask IoU below the full variant. The direct/source-gated geometry prior is the dominant factor: replacing it with strict-aware RI3D pseudo geometry collapses back to the old low-IoU result.
```

Naive baseline caveat:

```text
Naive RI3D failure is not safe to attribute only to pseudo-view image quality. The render manifest shows the same NeRSemble K/R/T adapter and a sign-flip/source-mask plus eval-frustum guard were used, with valid-z/in-frame evidence rather than a catastrophic empty-pose failure (min eval in-frame 0.4821). However, the naive source render already under-covers the source mask (IoU 0.3428303711577204, coverage ratio 0.5265596418494494), so source-space crop/scale/geometry mismatch is present before held-out evaluation. Direct LAM/G110 have much stronger mask support (direct eval IoU 0.8996994861687494; G110 is recorded separately in G113), while the GT pointcloud oracle confirms KRT plumbing is usable but itself under-covers the full alpha mask (oracle eval IoU 0.5236046612111784; G60 mean mask IoU 0.5539237552340944). Conclusion: G110's current value is that it bypasses pseudo-view geometry/pose/crop risk by preserving direct geometry; the naive baseline remains a failed baseline that needs stronger pose/crop/oracle复核 before using it as evidence against pseudo-view supervision quality alone.
```

Missing requirements:

```text
none
```

Decision:

```text
Single-case ablation contract is complete, with explicit caveats for naive pose/crop/source-render uncertainty and confidence-gate non-support.
```

Next gate:

```text
Replicate the same contract on additional NeRSemble source splits/cases before making a broad method claim.
```
