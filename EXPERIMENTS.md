# Experiment Index

这个文件是实验索引。它不存放结果，只解释：

```text
做了什么
结果在哪里
当前结论是什么
下一步是什么
```

## 1. 当前总进展

已经完成：

```text
LAM smoke test
Zero123++ smoke test
first10 输入集
Zero123++ raw steps20
Zero123++ raw steps75
steps20 vs steps75 对比
CLIP/reliability ranking
view budget 实验
subject cutout 输入消融
trusted-region mask
face identity filter
downstream candidate-pool export
RI3D first2 160px downstream smoke
RI3D first2 160px iter500 gate
RI3D first2 role-aware iter500 gate
RI3D first2 role-weighted iter500 gate
RI3D first2 mask-aware iter500 gate
RI3D first2 foreground-canonical mask ablations
RI3D first2 foreground point-cloud initialization filter
RI3D first2 FLAME proxy geometry-prior diagnostic
Zero123++ 3x2 split correction and head-cutout diagnostic probe
FaceScape sample metadata access gate
Multiface real-GT intake readiness gate
CC0 mesh positive-control gate and RI3D visual fail
real-GT benchmark-first pivot
G21 local Multiface debug real-GT benchmark gate
G22 real-GT reconstruction/evaluation preflight gate
G23 Multiface local-only real-camera adapter preflight
G24 CPU real-GT adapter contract gate
G25 RI3D Multiface init-only smoke
G26 held-out render/evaluation smoke
G27 RI3D train10 numerical gate
G28 RI3D loss-path numerical diagnostic
G29 zero-weight loss guard L1-only train10
G30 post-guard held-out eval smoke
G31 guarded loss-component audit
G32 monodisp scale guard train10
G33 combined guarded train10 held-out eval
G34 post-G33 route reset
G35 public/stronger benchmark availability audit
G36 method redesign direction and 2026 literature update
G37 model/data distribution audit
G38 artifact sync gate
G39 learned-prior/feed-forward/head-anchored Gaussian method gate
G40 LAM-20K local Multiface learned-prior smoke
G41 learned-prior held-out evaluation contract
```

还没有完成：

```text
redesigned method implementation on a passing real-GT benchmark
camera-aligned learned-prior held-out rendering or geometry export
quantitative real-GT reconstruction evaluation beyond init/smoke metrics
publishable artifact review for any identifiable Multiface RGB/mesh result
public/stronger real-GT benchmark access
```

历史 diagnostic pseudo-view 前端：

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability reranking
-> budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
```

Current gate status:

```text
Web first10 pseudo views are diagnostic-only.
Correcting Zero123++ grid splitting from 2x3 to 3x2 fixes an artificial crop
bug, but visual inspection still shows multi-view distortions. No more
reconstruction training should consume web pseudo-view candidates or RI3D
exports; G21's PASS_REAL_GT_BENCHMARK applies to the real captured Multiface
case only.

The old pseudo-view/RI3D route is invalid for reconstruction-quality claims.
Its value is diagnostic: failure taxonomy, gate design, and stop-loss evidence.
G21 now provides a local Multiface debug real-GT case with
PASS_REAL_GT_BENCHMARK; new method claims still require a separate G22
reconstruction/evaluation preflight on that real captured case. G22 is currently
blocked before training because the existing RI3D/evaluation adapter assumes a
global synthetic-style camera model and lacks real-camera depth/metric plumbing.
G23/G24 resolve this only to the level of local adapter and CPU contract gates:
they authorize a smallest init-only smoke, not a reconstruction-quality claim.
G25 passes that init-only smoke and saves a point cloud locally; the active next
gate then became G26 held-out render/eval smoke. G26 passes eval plumbing, but
G27 blocks training because RI3D reports NaN loss even under plain L1-only
settings. G28 identifies train-loop zero-weight loss contamination after
optimizer steps. G29 clears only the L1-only train10 blocker by guarding
zero-weight branches. G30 shows post-guard held-out eval still runs but remains
at G26 init-level metrics. G31-G33 close the component and combined guarded
train10 smoke loop, but held-out metrics still match init-level values, so the
route remains non-quality. G34 explicitly closes longer-training scaling on the
current RI3D setup. G35 finds no additional ready public/local real-GT benchmark
beyond the current local Multiface debug case and the CC0 positive control.
G36 resets the method direction toward learned/feed-forward head-specific priors
with real-GT held-out metrics; pseudo views may only re-enter as audited
conditional priors, never as ground-truth training views. G37-G38 add the
distribution and artifact-sync safeguards. G39-G41 complete the first
learned-prior smoke loop: LAM-20K can run locally on a real Multiface train
view after a PyTorch 2.6+ TorchScript loading patch, but private MP4s stay out
of GitHub and visual audit is only PASS_LOCAL_SMOKE_ONLY. The repo-safe CC0
point-splat positive-control image is outside LAM's natural portrait input
distribution and fails face tracking. The next credible method milestone must
add camera-aligned held-out rendering or geometry export before any quality
claim.
```

## 2. Stage 00: Inputs

目的：

```text
准备 first10 测试输入
```

位置：

```text
experiments/inputs/first10/
```

关键文件：

```text
experiments/inputs/first10/manifest.csv
experiments/inputs/first10/cutouts_manifest.csv
experiments/figures/first10_wikimedia_contact_sheet.png
experiments/figures/first10_cutout_inputs.png
```

样本构成：

```text
3 clean frontal
2 mild side-view
2 glasses
2 complex hair
1 occlusion / low-quality
```

相关脚本：

```text
scripts/data/collect_wikimedia_headshots.py
scripts/data/make_first10_cutouts.py
```

## 3. Stage 01: Smoke Tests

目的：

```text
确认服务器环境、模型权重、CUDA、脚本路径能跑通
```

注意：smoke test 只证明“能跑”，不证明“方法有效”。

位置：

```text
experiments/pseudo_views/zero123plus_smoke/
experiments/reconstructions/lam_smoke/
```

指标：

```text
experiments/metrics/smoke_runs_20260518.csv
```

结论：

```text
Zero123++ smoke 成功
LAM smoke 成功
```

## 4. Stage 02: Raw Pseudo Views

目的：

```text
测试原始输入图直接送入 Zero123++ 的效果
比较 steps20 和 steps75
```

输出：

```text
experiments/pseudo_views/zero123plus_first10/
experiments/pseudo_views/zero123plus_first10_steps75/
```

关键指标：

```text
experiments/metrics/zero123plus_first10_steps20.csv
experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv
experiments/metrics/pseudo_view_summary_first10_steps20_75.csv
experiments/metrics/steps20_vs75_comparison_first10.csv
```

关键图：

```text
experiments/figures/zero123plus_first10_steps20_grids.png
experiments/figures/zero123plus_first10_steps20_vs75_grids.png
```

结论：

```text
steps75 通常比 steps20 好，但不是所有样本都更好
5/10 helped
3/10 neutral
2/10 hurt
```

这说明：

```text
增加 diffusion steps 有帮助，但不能解决伪视角不可信的问题
```

## 5. Stage 03: View Ranking And Budget

目的：

```text
不要盲目使用 Zero123++ 的 6 个视角
用 reliability 和 CLIP consistency 做重排
比较 budget1 / budget2 / budget4 / budget6
```

关键文件：

```text
experiments/metrics/view_budget_selection_first10_steps20_75.csv
experiments/metrics/view_budget_clip_selection_first10_steps20_75.csv
experiments/metrics/clip_consistency_summary_first10_steps20_75.csv
experiments/metrics/pseudo_view_clip_consistency_first10_steps20_75.csv
```

关键图：

```text
experiments/figures/view_budget_selection_first10_steps75_budget4.png
experiments/figures/view_budget_clip_selection_first10_steps75_budget4.png
```

结论：

```text
budget1/2 质量高但覆盖不足
budget6 覆盖多但坏视图也进来
budget4 是当前较合理折中
```

## 6. Stage 04: Trusted-Region Masks For Raw Views

目的：

```text
对 raw steps75 budget4 视图生成可信区域 mask
检查哪些视角不应该送入下游 3D 监督
```

输出：

```text
experiments/pseudo_views/trusted_region_masks_steps75_budget4/
```

关键文件：

```text
experiments/metrics/trusted_region_masks_first10_steps75_budget4.csv
experiments/metrics/trusted_region_mask_summary_first10_steps75_budget4.csv
experiments/metrics/trusted_region_mask_observations_20260519.md
```

关键图：

```text
experiments/figures/trusted_region_masks_first10_steps75_budget4.png
```

结论：

```text
raw75 CLIP-budget4 accepted masks: 25 / 40
```

主要问题：

```text
photo_frame_geometry_risk
full_photo_or_background_rotation
overwide_mask_without_face
```

这说明：

```text
原始输入经常让 Zero123++ 旋转整张照片/背景/相框，而不是旋转人头主体
```

## 7. Stage 05: Cutout Ablation

目的：

```text
测试 subject cutout 是否能改善 Zero123++ 伪视角质量
```

输出：

```text
experiments/inputs/first10/cutouts/
experiments/pseudo_views/zero123plus_first10_cutout_steps75/
```

关键文件：

```text
experiments/metrics/raw_vs_cutout_comparison_steps75.csv
experiments/metrics/clip_raw_vs_cutout_comparison_steps75.csv
experiments/metrics/pseudo_view_reliability_raw_vs_cutout_steps75.csv
experiments/metrics/pseudo_view_clip_consistency_raw_vs_cutout_steps75.csv
experiments/metrics/cutout_input_ablation_observations_20260519.md
```

关键图：

```text
experiments/figures/zero123plus_first10_raw_vs_cutout_steps75_grids.png
experiments/figures/first10_cutout_inputs.png
```

结论：

```text
raw75 mean reliability: 66.97
cutout75 mean reliability: 70.58

raw75 mean CLIP cosine: 0.4893
cutout75 mean CLIP cosine: 0.5401

raw75 good trusted views: 38
cutout75 good trusted views: 43
```

样本级结果：

```text
cutout_helped: 5
cutout_neutral: 2
cutout_hurt: 3
```

解释：

```text
cutout 是更好的默认输入格式，但仍不能单独解决身份漂移和错误几何问题
```

## 8. Stage 06: Trusted Masks For Cutout Views

目的：

```text
对 cutout75 budget4 视图生成 trusted-region masks
```

输出：

```text
experiments/pseudo_views/trusted_region_masks_cutout75_budget4/
```

关键文件：

```text
experiments/metrics/trusted_region_masks_first10_cutout75_budget4.csv
experiments/metrics/trusted_region_mask_summary_first10_cutout75_budget4.csv
```

关键图：

```text
experiments/figures/trusted_region_masks_first10_cutout75_budget4.png
```

结论：

```text
raw75 CLIP-budget4 accepted masks: 25 / 40
cutout75 CLIP-budget4 accepted masks: 37 / 40
```

这曾经是最强的 2D candidate-hygiene 证据：

```text
cutout + budget4 + trusted mask 比 raw pseudo views 更干净，但它没有证明
这些伪视角适合下游 3D reconstruction 训练监督。
```

## 9. Stage 07: Face Identity Filter

目的：

```text
在 trusted cutout views 上显式区分身份监督、几何补全和身份拒绝
```

关键文件：

```text
experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv
experiments/metrics/face_identity_filter_summary_first10_cutout75_budget4.csv
experiments/metrics/face_identity_filter_observations_20260519.md
```

关键图：

```text
experiments/figures/face_identity_filter_first10_cutout75_budget4.png
```

结论：

```text
40 个 cutout75 budget4 视图里：
20 identity_supervision
14 geometry_only
1 identity_reject
37 mask_accepted
```

这一步把“筛选”推进为下游监督协议：

```text
identity_supervision 用于可见身份/纹理
geometry_only 只给侧后脑等几何补全信号
identity_reject 不进入下游监督
```

## 10. Stage 08: Downstream Candidate Pool Export

目的：

```text
把伪视角候选整理成下游 3D reconstruction 可以读取的格式。
这不是 validated training dataset；只是 candidate pool / candidate export。
```

输出：

```text
experiments/downstream_datasets/
```

三套候选池：

```text
raw75_all6/
raw75_budget4/
cutout75_budget4_masked/
```

每个 sample 内部：

```text
images/
masks/
metadata.json
```

脚本：

```text
scripts/build_downstream_dataset.py
```

运行方式：

```bash
python3 scripts/build_downstream_dataset.py --overwrite
```

这一步已经完成。

注意：

```text
这一步只是准备下游可读候选池，不等于已经证明这些候选适合做训练监督，
也不等于已经证明 3D reconstruction 被提升。
```

## 11. Stage 09: Downstream 3D Reconstruction

状态：

```text
RI3D first2 160px iter50 smoke 已完成
RI3D first2 160px iter500 gate 已完成，但结论 ambiguous
RI3D first2 role-aware iter500 gate 已完成，但非侵入版本仍 ambiguous
RI3D first2 role-weighted iter500 gate 已完成，但 scalar weights 仍 ambiguous
RI3D first2 mask-aware iter500 gate 已完成，但 foreground-only loss 仍没有修复视觉 artifact
RI3D first2 foreground-canonical ablations 已完成，但尺度对齐和 mask-loss ablation 仍没有修复视觉 artifact
RI3D first2 foreground point-cloud / FLAME proxy diagnostics 已完成，但当前解释必须受 candidate-pool 质量限制
```

重要更新：

```text
Stage 09 暂停作为重建方法实验继续推进。
原因不是 RI3D/Gaussian 一定失败，而是上游 candidate pool 没有过前提 gate。
experiments/downstream_datasets 中大量候选图本身是 split body、rotated
photo card、cropped fragment 或背景/身体片段。
```

已用于验证的候选池/导出：

```text
raw75_all6 candidate pool -> RI3D diagnostic
raw75_budget4 candidate pool -> RI3D diagnostic
cutout75_budget4_masked candidate pool -> RI3D diagnostic
roleaware_cutout75_budget4 candidate pool -> RI3D diagnostic
roleweighted_cutout75_budget4 candidate export -> RI3D diagnostic
maskaware_cutout75_budget4 candidate export -> RI3D diagnostic
```

目标问题：

```text
这些弱指标筛出来的伪视角候选为什么不能作为可靠 3D reconstruction 监督？
下一轮如何通过 VLM/manual visual gate 重建候选池？
```

最新 gate artifacts：

```text
experiments/metrics/milestone_data_audit_protocol_20260519.md
experiments/metrics/downstream_candidate_pool_semantics_20260519.md
experiments/metrics/first10_candidate_pool_audit_gate_20260519.csv
experiments/metrics/first10_candidate_pool_audit_gate_20260519.md
experiments/metrics/first10_candidate_pool_visual_audit_20260519.md
experiments/figures/first10_candidate_pool_audit_gate_20260519.png
experiments/figures/first10_candidate_pool_visual_audit_20260519.png
```

建议先只选 2 个样本：

```text
web_clean_frontal_03      # cutout 明显帮助
web_clean_frontal_01      # cutout 可能伤害
```

本地已生成 RI3D-readable candidate exports：

```text
experiments/ri3d_datasets/first2/
experiments/ri3d_datasets/first2_160/
experiments/ri3d_datasets/first2_roleaware/
experiments/ri3d_datasets/first2_roleweighted/
experiments/ri3d_datasets/first2_maskaware/
experiments/ri3d_datasets/first2_fgcenter_maskaware/
experiments/ri3d_datasets/first2_fghead_maskaware/
```

包含：

```text
2 samples x 3 variants = 6 scenes
raw75_all6: 6 views/sample
raw75_budget4: 4 views/sample
cutout75_budget4_masked: 4 views/sample
roleaware_cutout75_budget4: 4 views/sample, with supervision_role metadata
roleweighted_cutout75_budget4: same views plus role_rgb_weight / role_depth_weight
maskaware_cutout75_budget4: same views plus mask_path / source_mask / mask_coverage
fgcenter/fghead: foreground connected-component crop metadata and resized masks
```

CPU 端准备脚本：

```text
Historical diagnostic reproduction only. Do not run these as a new quality
experiment; G21 permits only real-GT adapter/preflight work, and G23/G24 pass
only the local adapter contract for the Multiface case.
```

```bash
python3 scripts/prepare_ri3d_dataset.py --overwrite
python3 scripts/prepare_ri3d_dataset.py --output-root experiments/ri3d_datasets/first2_160 --image-size 160 --overwrite
```

GPU 端运行脚本：

```bash
bash scripts/run_ri3d_first2.sh
GPU=0 ITERATIONS=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 OUT_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/render_ri3d_first2.sh
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_fgcenter_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --foreground-crop --foreground-crop-margin 0.35 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 USE_MASK=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fgcenter_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fgcenter_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_fghead_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --foreground-crop --foreground-crop-mode mask_width_anchor --foreground-width-scale 1.8 --foreground-height-fraction 0.55 --foreground-y-anchor 0.45 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 USE_MASK=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
```

默认输出：

```text
experiments/downstream_3d/ri3d_first2/
experiments/downstream_3d/ri3d_first2_160_iter50/
experiments/downstream_3d/ri3d_first2_160_iter500/
experiments/downstream_3d/ri3d_first2_roleaware_iter500/
experiments/downstream_3d/ri3d_first2_roleweighted_iter500/
experiments/downstream_3d/ri3d_first2_maskaware_iter500/
experiments/downstream_3d/ri3d_first2_fgcenter_maskaware_iter500/
experiments/downstream_3d/ri3d_first2_fgcenter_unmasked_iter500/
experiments/downstream_3d/ri3d_first2_fghead_maskaware_iter500/
experiments/downstream_3d/ri3d_first2_fghead_unmasked_iter500/
```

已发布结果：

```text
experiments/metrics/ri3d_first2_160_iter50.csv
experiments/metrics/ri3d_first2_160_iter50_observations.md
experiments/figures/ri3d_first2_160_iter50_inputs.png
experiments/figures/ri3d_first2_160_iter50_renders.png
experiments/reconstructions/ri3d_first2_160_iter50/
experiments/metrics/ri3d_first2_160_iter500.csv
experiments/metrics/ri3d_first2_160_iter500_observations.md
experiments/figures/ri3d_first2_160_iter500_inputs.png
experiments/figures/ri3d_first2_160_iter500_renders.png
experiments/reconstructions/ri3d_first2_160_iter500/
scripts/build_roleaware_downstream_dataset.py
experiments/downstream_datasets/roleaware_cutout75_budget4/
experiments/ri3d_datasets/first2_roleaware/
experiments/metrics/ri3d_first2_roleaware_iter500.csv
experiments/metrics/ri3d_first2_roleaware_observations.md
experiments/figures/ri3d_first2_roleaware_iter500_inputs.png
experiments/figures/ri3d_first2_roleaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleaware_iter500/
patches/ri3d/role_weighted_loss.patch
experiments/ri3d_datasets/first2_roleweighted/
experiments/metrics/ri3d_first2_roleweighted_iter500.csv
experiments/metrics/ri3d_first2_roleweighted_observations.md
experiments/figures/ri3d_first2_roleweighted_iter500_inputs.png
experiments/figures/ri3d_first2_roleweighted_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleweighted_iter500/
patches/ri3d/mask_aware_loss.patch
experiments/ri3d_datasets/first2_maskaware/
experiments/metrics/ri3d_first2_maskaware_iter500.csv
experiments/metrics/ri3d_first2_maskaware_observations.md
experiments/figures/ri3d_first2_maskaware_iter500_inputs.png
experiments/figures/ri3d_first2_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_maskaware_iter500/
experiments/ri3d_datasets/first2_fgcenter_maskaware/
experiments/ri3d_datasets/first2_fghead_maskaware/
experiments/metrics/ri3d_first2_fgcenter_maskaware_iter500.csv
experiments/metrics/ri3d_first2_fgcenter_unmasked_iter500.csv
experiments/metrics/ri3d_first2_fghead_maskaware_iter500.csv
experiments/metrics/ri3d_first2_fghead_unmasked_iter500.csv
experiments/figures/ri3d_first2_fgcenter_maskaware_iter500_renders.png
experiments/figures/ri3d_first2_fgcenter_unmasked_iter500_renders.png
experiments/figures/ri3d_first2_fghead_maskaware_iter500_renders.png
experiments/figures/ri3d_first2_fghead_unmasked_iter500_renders.png
experiments/reconstructions/ri3d_first2_fgcenter_maskaware_iter500/
experiments/reconstructions/ri3d_first2_fgcenter_unmasked_iter500/
experiments/reconstructions/ri3d_first2_fghead_maskaware_iter500/
experiments/reconstructions/ri3d_first2_fghead_unmasked_iter500/
patches/ri3d/geometry_prior_pointcloud_filter.patch
experiments/metrics/geometry_prior_first2_plan.md
experiments/metrics/ri3d_first2_fghead_pcdmask_iter500.csv
experiments/metrics/ri3d_first2_fghead_pcdmask_observations.md
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_fghead_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_fghead_pcdmask_vs_maskaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_fghead_pcdmask_iter500/
experiments/metrics/flame_geometry_prior_first2_plan.md
experiments/metrics/flame_geometry_prior_first2_observations.md
experiments/geometry_priors/flame_first2_proxy/
experiments/ri3d_datasets/first2_flame_proxy_pcdmask/
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_iter500.csv
experiments/metrics/ri3d_first2_flame_proxy_pcdmask_observations.md
experiments/figures/flame_geometry_prior_first2_proxy_sheet.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_inputs.png
experiments/figures/ri3d_first2_flame_proxy_pcdmask_iter500_renders.png
experiments/figures/ri3d_first2_flame_proxy_vs_pcdmask_iter500_renders.png
experiments/reconstructions/ri3d_first2_flame_proxy_pcdmask_iter500/
experiments/inputs/first10/head_cutouts/
experiments/inputs/first10/head_cutouts_manifest.csv
experiments/figures/first10_head_cutout_inputs.png
experiments/pseudo_views/zero123plus_first10_cutout_steps75_resplit3x2/
experiments/pseudo_views/zero123plus_first10_head_cutout_steps75_resplit3x2/
experiments/figures/zero123plus_first10_head_cutout_steps75_resplit3x2_grids.png
experiments/figures/view_budget_selection_head_cutout75_resplit3x2_budget4.png
experiments/metrics/zero123plus_grid_split_bug_20260519.md
experiments/metrics/head_cutout_probe_resplit3x2_gate_20260519.md
experiments/metrics/head_cutout_probe_observations_20260519_resplit3x2.md
experiments/metrics/pseudo_view_reliability_first10_head_cutout_steps75_resplit3x2.csv
experiments/metrics/view_budget_selection_first10_head_cutout_steps75_resplit3x2.csv
experiments/metrics/pseudo_view_summary_first10_head_cutout_steps75_resplit3x2.csv
experiments/metrics/gt_dataset_route_plan_20260519.md
experiments/metrics/gt_dataset_access_gate_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.json
experiments/metrics/g16a_real_gt_intake_readiness_20260520.md
experiments/metrics/g16a_real_gt_intake_readiness_20260520.json
experiments/metrics/gt_positive_control_route_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_gt_gate_20260520.json
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_g17_provenance_sanity_20260520.json
experiments/gt_cases/wikimedia_blender_head_cc0/
experiments/figures/g16b_wikimedia_blender_head_cc0_contact_sheet.png
experiments/ri3d_datasets/gt_positive_control/
experiments/metrics/ri3d_gt_positive_control_iter10.csv
experiments/metrics/ri3d_gt_positive_control_iter10_observations.md
experiments/figures/ri3d_gt_positive_control_iter10_inputs.png
experiments/figures/ri3d_gt_positive_control_iter10_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter10/
experiments/metrics/wikimedia_blender_head_cc0_g17c_iter500_preflight_20260520.md
experiments/metrics/wikimedia_blender_head_cc0_g17c_iter500_preflight_20260520.json
experiments/metrics/ri3d_gt_positive_control_iter500.csv
experiments/metrics/ri3d_gt_positive_control_iter500_observations.md
experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.md
experiments/metrics/ri3d_gt_positive_control_iter500_visual_gate_20260520.json
experiments/figures/ri3d_gt_positive_control_iter500_inputs.png
experiments/figures/ri3d_gt_positive_control_iter500_renders.png
experiments/reconstructions/ri3d_gt_positive_control_iter500/
experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.csv
experiments/metrics/first10_failure_taxonomy_resplit3x2_20260520.md
experiments/figures/first10_failure_taxonomy_resplit3x2_20260520.png
experiments/metrics/paper_package_20260520.md
experiments/metrics/milestone_closure_20260520.md
```

G14 结论：

```text
FLAME proxy depth/conf prior 能生成并接入 RI3D，所有 MP4 可读。
但它没有修复 G13 仍有的 detached foreground fragments，并且会削弱部分主体支持。
因此它是 diagnostic negative：后续 first10 应作为 failure taxonomy 和 protocol
验证，而不是宣称该 RI3D+FLAME proxy 路线已经解决重建质量。
之后的 G15 审计发现历史 Zero123++ per-view PNG 存在 2x3/3x2 切分错误；
修正后伪多视图仍然有畸变，所以 web first10 不再作为重建训练输入。
```

阶段结论：

```text
first2 下游闭环已经能跑通，但 iter50 仍然只是 smoke 级结果。
raw75_all6 在两个样本上 loss 都更高，说明盲目增加视角不可靠。
raw75_budget4 在 web_clean_frontal_03 上最低 loss。
cutout75_budget4_masked 在 web_clean_frontal_01 上略低于 raw75_budget4。
渲染视频仍可见 full-photo/background rotation，不能作为最终质量证明。
iter500 复现了同样趋势：raw75_all6 仍然更差；cutout75_budget4_masked
只在 web_clean_frontal_01 上优于 raw75_budget4。
因此下一步不是扩 first30/first50，而是让下游显式消费
identity_supervision / geometry_only / identity_reject / mask_reject。
G9 已完成非侵入 role-aware 数据和 iter500 渲染：web_clean_frontal_03
略优于 cutout75_budget4_masked 但仍差于 raw75_budget4；web_clean_frontal_01
优于 raw75_budget4 但略差于 cutout75_budget4_masked。
render sheet 仍有 fragmented/rotated photo-card artifacts，所以 G9 是
infrastructure pass，不是最终 method win。
G10 已完成 explicit role-weighted RI3D loss：web_clean_frontal_03 的 weighted
loss 降低但不能直接和未加权 loss 比较；web_clean_frontal_01 略优于 G9。
render sheet 仍有同类 artifacts。
G11 已完成 spatial mask-aware RI3D loss：MP4/PNG/CSV 全部导出且训练可复现，
但 render sheet 仍显示小碎片/相框 artifact。foreground-only loss 不能解决
尺度/位置 canonicalization 和结构先验缺失问题。
G12 已完成 foreground canonicalization 和 mask-loss ablation。largest_square
和 mask_width_anchor 都让输入 sheet 更干净，但 USE_MASK=1/0 的 render sheet
仍然是同类卡片/碎片失败。
之后 G13/G14 接入 foreground point-cloud filter 和 LAM/FLAME proxy prior，
但仍未修复 detached foreground fragments。
G15 之后的实际路线已经改为 G16/G17：真实 GT 多视角数据集 case 继续走
license/access gate；在真实采集数据通过前，先用 Wikimedia/Blender CC0
realistic human head mesh 做 G16b 正控，验证 camera、mask/depth、manifest、
PNG/MP4 同步和下游重建 plumbing。G17a provenance sanity 已确认 8 个视图、
8 条 camera 记录、PNG 尺寸、mask coverage、MP4 可读性和 raw mesh exclusion
全部通过。G17b RI3D iter10 smoke 已完成 conversion/init/train/render/export，
但 render sheet 仍是 smoke 质量且有 ghosted fragments，因此只是 execution pass，
不是重建质量结论。G17c iter500 继续通过执行和 MP4 导出 gate，但视觉上仍是
ghosted multi-fragment head，不是重建质量通过。G18 已完成 corrected 3x2
first10 taxonomy：60 个 view 中 10 个 identity_supervision、37 个
geometry_only、13 个 reject；budget4 选中的 40 个 view 仍有 8 个 severe/reject。
G19 已收口为 paper package：failure-aware gating 是主结论，web first10
仍 blocked for reconstruction training。G16a-local 完成了真实 GT intake
readiness：Multiface route 的 metadata/KRT/frame schema 已经站住。G21 进一步
完成了本地 Multiface debug compact case 的 structural + VLM/manual gate：
9 个同帧真实 captured views、KRT cameras、projected masks 和 tracked OBJ 均
满足 benchmark premise；原始 RGB/mesh 仍留在 3dv_work 等待 artifact review。
G20 进一步把路线正式切换为 benchmark-first：旧 pseudo-view/RI3D 路线只保留
诊断价值，不再作为质量主实验。G22 已阻塞直接训练；G23/G24 已完成 local-only
Multiface adapter 和 CPU contract gate；G25 已完成最小 init-only smoke；G26
已完成 held-out render/eval smoke。G27 十步训练被 NaN loss 阻塞，G28 定位
到 zero-weight branch contamination，G29 只清除了 L1-only train10 blocker，
G30 证明 post-guard eval 能跑但指标仍是 init-level；G31-G33 完成 component
audit、monodisp guard 和 combined guarded train10/eval，但质量仍未提升。下一步
不是更长训练，而是方法重设或更强 public real-GT benchmark。
```

对比指标：

```text
identity consistency
background/frame artifact rate
novel-view render quality
multi-view consistency
qualitative contact sheet
rendered output integrity
```

## 12. 当前默认路线

历史 diagnostic pseudo-view 前端：

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability reranking
-> budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
```

当前允许继续推进的下游对比：

```text
A: licensed real GT sparse multi-view case with 6-12 calibrated views, masks,
   and GT mesh/point cloud, after PASS_REAL_GT_BENCHMARK
B: single-image baseline on the same real-GT case
C: method variants only after the benchmark gate passes
D: pseudo-view diagnostic/failure taxonomy on corrected 3x2 first10 grids
```

当前最重要的未闭环问题：

```text
Full H3DS/publishable benchmark access and artifact publication review remain
open, but G21 has completed the local Multiface debug compact case gate:
PASS_REAL_GT_BENCHMARK with real captured cameras, masks, and tracked mesh.
G22 已阻塞直接训练，因为旧 adapter 的 per-view intrinsics、real-camera
depth/conf maps、held-out view / mesh metrics 没站住。G23/G24 现在只把
Multiface local-only adapter 和 RI3D file contract 补到可 smoke 的状态，G25
已证明 RI3D 能加载 adapter 并保存初始化点云。G26 已证明 held-out render/eval
指标链路能跑且不保存可识别媒体。G27 证明当前 RI3D train loop 数值不健康；
G28/G29 证明其中 L1-only NaN 类问题来自 zero-weight branch contamination
并可用 guard 清除；G30-G33 证明 guarded small-step train/eval 仍没有带来
held-out 质量提升。G34-G36 已把当前 RI3D scaling 关闭为方法路线，并把下一步
限定为更强 benchmark 或 learned-prior/head-anchored 方法重设。G37 进一步检查
模型/测试数据分布：LAM first10 只能做定性，pseudo-view/旧 RI3D 只能诊断，
Multiface G21-G33 只能说明 real-GT plumbing/numerical gate。G38 记录 artifact
sync gate，保证 repo-safe PNG/MP4/CSV/JSON/MD 结果进入 GitHub，同步时不混入
raw/private assets。不要从现有 web first10 candidate pool 继续训练，也不要把
G23-G38 或旧 RI3D 结果解释成质量结论。
```
