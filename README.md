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
downstream dataset build
RI3D first2 dataset conversion
RI3D first2 160px iter50 smoke render
RI3D first2 160px iter500 milestone
RI3D first2 role-aware iter500 milestone
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

已经构建好三套下游输入：

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
```

下一步：

1. 不急着扩 first30 / first50。
2. 实现 G10：explicit role-weighted RI3D loss。
3. 让 identity / geometry-only / reject / mask_reject 真正进入训练 loss。
4. 如果 G10/G11 证明 filtered pseudo views 稳定优于 raw，再扩 first10 / first30 / first50。
