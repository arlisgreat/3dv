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
```

还没有完成：

```text
candidate-pool recovery and VLM-gated regeneration before any more reconstruction
```

当前默认 pseudo-view 前端：

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability reranking
-> budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
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

这是当前最强的阶段性证据：

```text
cutout + budget4 + trusted mask 明显比 raw pseudo views 更适合下游 3D 监督
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
```

G14 结论：

```text
FLAME proxy depth/conf prior 能生成并接入 RI3D，所有 MP4 可读。
但它没有修复 G13 仍有的 detached foreground fragments，并且会削弱部分主体支持。
因此它是 diagnostic negative：后续 first10 应作为 failure taxonomy 和 protocol
验证，而不是宣称该 RI3D+FLAME proxy 路线已经解决重建质量。
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
因此下一步不是 first10 扩展，而是 G13：接入 LAM/FLAME/full-head geometry prior。
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

当前推荐 pseudo-view 前端：

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability reranking
-> budget4
-> trusted-region mask
-> face identity / geometry-only / reject split
```

当前推荐下游对比：

```text
A: LAM single-image baseline
B: raw75_all6 or raw75_budget4
C: cutout75_budget4_masked
```

当前最重要的未闭环问题：

```text
结构几何先验是否能修复 G8-G12 中 RI3D 反复出现的卡片/碎片几何失败？
```
