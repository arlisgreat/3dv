# 3DV Paper Sprint

这个仓库只做一件事：管理一个月内能完成的 3DV 方向论文实验。

当前论文题目暂定：

> **A Diagnostic Study of Diffusion-Guided Pseudo Views for Single-Image Gaussian Head Reconstruction**

中文：

> **扩散伪多视角引导的单图高斯人头重建诊断研究**

## 现在要做什么

先跑通两个最小闭环：

1. **LAM**：单张头像 -> Gaussian head baseline。
2. **Zero123++**：同一张头像 -> 6 个伪多视角。

跑通后做 first10 实验：

```text
3 张干净正脸
2 张轻微侧脸
2 张眼镜
2 张复杂头发
1 张遮挡或低质量
```

核心观察：

```text
伪多视角是否改善后脑/侧脸？
伪多视角是否改变身份、发型、眼镜、脸型？
视角选择和筛选是否比盲目增加视图更有效？
```

## 目录怎么用

```text
3dv/
  README.md              # 当前入口：先看这里
  PLAN.md                # 研究计划、论文结构、一个月安排
  EXPERIMENTS.md         # 实验阶段、结果、文件索引
  MILESTONES.md          # milestone ledger: 已完成 gate、当前 gate、下一步
  SERVER.md              # 服务器运行步骤
  data_manifest.csv      # 样本清单

  experiments/           # 我们自己的输入、输出、指标、图表
  scripts/               # 我们自己的脚本
  external/              # 第三方仓库，不提交到主仓库
  patches/               # 如果改了第三方代码，把 patch 放这里
```

## 外部仓库

第三方代码放在 `external/`，主仓库不提交这些大项目源码。

| 路径 | 用途 |
| --- | --- |
| `external/LAM` | 主 baseline：one-shot Gaussian head |
| `external/zero123plus` | 伪多视角 diffusion 生成器 |
| `external/PanoHead` | 申请书锚点和传统 baseline |
| `external/ri3d` | repair / inpainting 思路参考 |

检查外部仓库：

```bash
bash scripts/external_status.sh
```

克隆外部仓库：

```bash
bash scripts/clone_external.sh P0
```

## 服务器怎么跑

本地电脑不跑模型，服务器 GPU 跑模型。

服务器上看：

```text
SERVER.md
```

最小命令序列：

```bash
git clone https://github.com/arlisgreat/3dv.git
cd 3dv

bash scripts/clone_external.sh P0
bash scripts/server/00_check_server.sh

# CUDA 12.1
bash scripts/server/01_setup_lam_env.sh cu121
bash scripts/server/02_download_lam_assets.sh hf
bash scripts/server/03_run_lam_sample.sh

bash scripts/server/04_setup_zero123plus_env.sh cu121
bash scripts/server/05_run_zero123plus_sample.sh
```

如果服务器是 CUDA 11.8，把 `cu121` 换成 `cu118`。

## 技术路线是否合理

合理。当前路线跟 2025-2026 年单图 3D avatar / Gaussian head 的趋势一致：

1. NeRF full-head 正在转向 Gaussian head / Gaussian avatar。
2. LAM / PanoLAM 说明 one-shot Gaussian head/full-head 是近期主线。
3. FLAME / 3DMM 正在从初始化工具变成结构锚点。
4. Zero123++ 提供单图一致多视角先验。
5. RI3D 说明 sparse-view 3DGS 中 diffusion repair / inpainting 是有效方向。

我们不从零造大系统，而是基于现有开源项目做一个清晰、可复现、有诊断价值的问题：

> diffusion pseudo views 对单图 Gaussian head reconstruction 的收益、风险和筛选策略。

## 下一步

当前实验索引见：

```text
EXPERIMENTS.md
MILESTONES.md
```

已经完成：

```text
LAM first10 baseline
Zero123++ raw steps20 / steps75
CLIP + reliability view ranking
trusted-region masks
subject cutout ablation
face identity filter
downstream candidate-pool export
RI3D first2 dataset conversion
RI3D first2 160px iter50 smoke render
RI3D first2 160px iter500 milestone
RI3D first2 role-aware iter500 milestone
RI3D first2 role-weighted iter500 milestone
RI3D first2 mask-aware / foreground-canonical / point-cloud-filter milestones
RI3D first2 FLAME proxy geometry-prior diagnostic
Zero123++ 3x2 grid split correction and head-cutout diagnostic probe
FaceScape sample metadata access gate
```

当前默认 pseudo-view 前端：

```text
subject cutout
-> Zero123++ steps75
-> CLIP + reliability budget4
-> trusted-region mask
-> face identity filter
-> identity / geometry-only / reject split
```

已经构建好三套下游候选池。注意：这里的历史目录名是
`downstream_datasets`，但语义不是“已证明适合重建的训练集”，而是筛出来的
伪视图候选池：

```text
experiments/downstream_datasets/raw75_all6/
experiments/downstream_datasets/raw75_budget4/
experiments/downstream_datasets/cutout75_budget4_masked/
```

identity filter 结果和仓库内 skill：

```text
experiments/metrics/face_identity_filter_observations_20260519.md
experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv
experiments/figures/face_identity_filter_first10_cutout75_budget4.png
skills/3dv-experiment-orchestrator/
```

并且已经转换出 RI3D 可直接读取的 first2 pilot 数据：

```text
experiments/ri3d_datasets/first2/
experiments/ri3d_datasets/first2_roleaware/
experiments/ri3d_datasets/first2_fghead_maskaware/
experiments/ri3d_datasets/first2_flame_proxy_pcdmask/
```

这些 RI3D 目录同样只是“下游可读候选导出”，不是 validated training set。
G8-G14 的结果已经证明：候选筛选指标仍弱，候选视图即使更干净，也可能在
RI3D 中产生卡片、碎片和身份/几何失败。

当前最新结论：

```text
G13 foreground point-cloud filtering reduces the rectangular card background
seeded by RI3D initialization, but still leaves detached foreground chunks.
G14 FLAME proxy depth/conf priors run end-to-end and export valid MP4s, but do
not repair the fragments and can remove subject support. The next stage should
stabilize the paper as a failure-aware pseudo-view diagnostic study on first10,
not claim that this RI3D repair path is a solved reconstruction method.

Critical correction: the current experiments/downstream_datasets candidate pools
are visually poor. Many selected views are split bodies, rotated photo cards,
cropped fragments, or background/body-only pieces. Future milestones must pass
a structural data audit and a VLM/manual visual audit before any reconstruction
training.

Second correction: historical Zero123++ per-view PNGs were split as 2x3, while
the saved grids are 3x2. Correct 3x2 resplitting removes the artificial tall
split-view tiles, but the generated head-cutout pseudo views still have visible
identity and geometry distortions. Web first10 is therefore diagnostic-only.

Current reconstruction-quality route: use a real GT multi-view dataset case
with cameras and mesh/point-cloud ground truth. FaceScape is the primary route:
its sample was inspected locally for metadata only, but its readme says not to
distribute the sample, so raw images/meshes stay out of git.
```

G16 access/audit records:

```text
experiments/metrics/zero123plus_grid_split_bug_20260519.md
experiments/metrics/head_cutout_probe_resplit3x2_gate_20260519.md
experiments/metrics/gt_dataset_route_plan_20260519.md
experiments/metrics/gt_dataset_access_gate_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.md
```

RI3D first2 smoke 复现命令：

```bash
GPU=0 ITERATIONS=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 OUT_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=50 DATA_ROOT=experiments/ri3d_datasets/first2_160 RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter50 bash scripts/render_ri3d_first2.sh
```

RI3D first2 500-iteration gate 复现命令：

```bash
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_160 OUT_ROOT=experiments/downstream_3d/ri3d_first2_160_iter500 bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_160 RUN_ROOT=experiments/downstream_3d/ri3d_first2_160_iter500 bash scripts/render_ri3d_first2.sh
```

RI3D first2 role-aware 500-iteration gate 复现命令：

```bash
python scripts/build_roleaware_downstream_dataset.py --overwrite
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_roleaware --variants roleaware_cutout75_budget4 --image-size 160 --overwrite
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

RI3D first2 role-weighted 500-iteration gate 复现命令：

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_roleweighted --variants roleaware_cutout75_budget4 --image-size 160 --overwrite
GPU=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted OUT_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_roleweighted RUN_ROOT=experiments/downstream_3d/ri3d_first2_roleweighted_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

RI3D first2 mask-aware 500-iteration gate 复现命令：

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

RI3D first2 foreground-canonical ablation 复现命令：

```bash
python scripts/prepare_ri3d_dataset.py --downstream-root experiments/downstream_datasets --output-root experiments/ri3d_datasets/first2_fghead_maskaware --variants roleaware_cutout75_budget4 --image-size 160 --foreground-crop --foreground-crop-mode mask_width_anchor --foreground-width-scale 1.8 --foreground-height-fraction 0.55 --foreground-y-anchor 0.45 --overwrite
GPU=0 USE_MASK=1 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_maskaware_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 USE_MASK=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_unmasked_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
```

RI3D first2 foreground point-cloud filter 复现命令：

```bash
GPU=0 USE_MASK=1 PCD_MASK_FILTER=1 PCD_CONF_THRESHOLD=0.0 PCD_MIN_POINTS=256 PCD_POINTS_PER_VIEW=0 ITERATIONS=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware OUT_ROOT=experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/run_ri3d_first2.sh
GPU=0 ITERATION=500 DATA_ROOT=experiments/ri3d_datasets/first2_fghead_maskaware RUN_ROOT=experiments/downstream_3d/ri3d_first2_fghead_pcdmask_iter500 VARIANTS_STR="roleaware_cutout75_budget4" bash scripts/render_ri3d_first2.sh
```

当前结论：

```text
filtered pseudo-view frontend 已经比 raw pseudo views 更可靠。
face-embedding filter 在 cutout75+budget4 上得到 20/40 identity candidates、
14/40 geometry-only candidates、1/40 identity reject。
RI3D first2 160px iter50 已跑通下游闭环，但还只是 smoke 级验证。
raw75_all6 在两个样本上训练 loss 都更高，说明盲目增加视角不可靠。
RI3D first2 160px iter500 已完成；raw75_all6 仍然更差。
cutout75_budget4_masked 只在其中一个 first2 样本上略优于 raw75_budget4，
因此 G8 是执行通过但科学结论仍然 ambiguous。
RI3D first2 role-aware iter500 已完成；角色 metadata/desaturation 路径跑通，
但 loss 和 render sheet 仍不构成稳定 method win。
RI3D first2 role-weighted iter500 已完成；per-view scalar role weights 路径跑通，
但 render sheet 仍有 fragmented/photo-card artifacts，仍不是最终 method win。
RI3D first2 mask-aware iter500 已完成；mask_path/USE_MASK 训练路径跑通，
但 foreground-only loss 仍学出小碎片/相框 artifact，不是最终 method win。
RI3D first2 foreground-canonical ablations 已完成；输入尺度和主体对齐改善，
但 USE_MASK=1/0 都仍输出卡片/碎片，不是最终 method win。
RI3D first2 foreground point-cloud filter 已完成；G12 的矩形卡片背景明显减少，
但仍有 detached foreground fragments，不是最终 method win。
```

下一步：

1. 不急着扩 first30 / first50。
2. 实现 G14：LAM/FLAME mesh/depth/silhouette structural prior first2 repair。
3. 如果 G14 仍失败，把论文定位收紧为诊断负结果和 failure-aware protocol。
4. 只有当结构先验证明 filtered pseudo views 稳定优于 raw，再扩 first10 / first30 / first50。
