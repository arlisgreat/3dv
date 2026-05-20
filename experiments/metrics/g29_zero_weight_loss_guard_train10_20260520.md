# G29 Zero-Weight Loss Guard Train10

Date: 2026-05-20

Verdict:

```text
PASS_ZERO_WEIGHT_LOSS_GUARD_L1_TRAIN10
```

Scope:

```text
Resolve the specific G27 L1-only train10 NaN blocker on the local Multiface
real-GT adapter. This is a numerical-health smoke, not a reconstruction-quality
result.
```

Input gates:

```text
G21 PASS_REAL_GT_BENCHMARK on the local Multiface compact case.
G23/G24 pass local-only adapter and CPU file-contract gates.
G25 provides the init-only point cloud.
G28 identifies a train-loop zero-weight loss contamination path.
```

G28 diagnosis:

```text
Static train-view losses are finite, but the train-loop probe becomes non-finite
after optimizer steps. Render and L1 remain finite while mono-depth loss becomes
NaN; the unguarded formula can still propagate 0*NaN into the total loss when
mono_depth_weight=0.
```

Patch:

```text
patches/ri3d/g29_zero_weight_loss_guard.patch
```

Patch summary:

```text
Skip SSIM, silhouette, and mono-depth branches in external/ri3d/scripts/train_gs.py
when their effective weights are zero. This prevents zero-weight non-finite terms
from contaminating the total loss.
```

Run:

```text
run_root=/data1/workspace/airulan/3dv_work/runs/g29_ri3d_multiface_train10_l1_guard_20260520
log=/data1/workspace/airulan/3dv_work/runs/g29_ri3d_multiface_train10_l1_guard_20260520/train10_l1_guard.log
selected_gpu=0
iterations=10
lambda_dssim=0
lambda_silhouette=0
mono_depth_weight=0
exit_code=0
final_progress_loss=0.6124692
saved_iteration=10
saved_point_count=67410
```

Train-log metrics:

| Split | L1 | PSNR |
| --- | ---: | ---: |
| test | 0.5926034251848856 | 4.268513361612955 |
| train | 0.6414766907691956 | 3.526849460601807 |

Boundary:

```text
G29 only clears the L1-only train10 NaN blocker. It does not validate default
RI3D loss settings, depth/silhouette supervision, longer training, densification,
or reconstruction quality.
```

Artifact policy:

```text
The iteration-10 PLY, cameras.json, cfg_args, and logs remain local under
3dv_work. No RGB renders, PNG/JPEG/MP4, mesh, raw person-identifying media, or
full logs are committed.
```

Next gate:

```text
G30 held-out eval smoke from the G29 iteration-10 checkpoint, with no identifiable
image/video export. If metrics remain init-level, keep the claim as plumbing only.
```
