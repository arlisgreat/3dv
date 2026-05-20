# Research Plan

## 1. 论文问题

原申请书的完整路线是：

```text
PanoHead + Gaussian Splatting + Diffusion + Transformer + FLAME / 3DMM
```

这个适合一年项目，不适合一个月论文。

旧压缩问题是：

> Diffusion 生成的伪多视角，在单图 Gaussian 人头重建中什么时候有帮助，什么时候会伤害身份一致性？

G2-G19 已经证明这条旧路线只能提供诊断和止损价值。当前问题改为：

> 在没有真实 GT benchmark 的情况下，pseudo-view/RI3D 不能产生可信重建结论；
> 下一步必须先建立 licensed real-GT benchmark gate。

## 2. 论文贡献点

当前建议最终写成三点：

1. 系统分析 diffusion pseudo views 的失败模式和数据前提错误。
2. 提出 gate-first 的 benchmark/data audit protocol。
3. 明确真实 GT benchmark 是任何重建质量结论的前置条件。

## 3. 实验设计

### Main Comparison

历史 pseudo-view comparison 已关闭为 diagnostic-only：

```text
single image only
fixed pseudo views
active selected pseudo views
active + identity filtering
```

当前可信 comparison 必须走 G21->G22：

```text
G21 local licensed real-GT compact case
single-image baseline on the same case
method variants only inside G22 after repeated data/VLM/distribution gate
```

### View Budget

```text
1 view
2 views
4 views
6 views
8 views
```

核心假设：

> 选对视角和筛掉坏视图，比盲目增加伪视图更重要。

### Failure Types

```text
identity drift
geometry collapse
texture inconsistency
floaters
diffusion hallucination
```

## 4. 数据

第一批 sanity check：

```text
3 clean frontal
2 mild side-view
2 glasses
2 complex hair
1 occlusion or low-quality
```

放在：

```text
experiments/inputs/first10/
```

记录在：

```text
data_manifest.csv
```

## 5. 一个月计划

### Week 1

目标：跑通最小闭环。

1. LAM sample。
2. Zero123++ sample。
3. first10 输入图。
4. 第一批定性图。
5. 开始记录 identity drift / hallucination。

### Week 2

原目标：主实验。该目标已经取消为质量主实验，只保留诊断价值。

1. 不扩展到 30-50 张。
2. 不从 `experiments/downstream_datasets` 训练。
3. 保留 first10 pseudo-view 作为 failure taxonomy。
4. 主实验必须等待 real-GT benchmark。

当前 first10 进展：

```text
steps20 和 steps75 Zero123++ 伪视角已完成。
steps75 对 5/10 个样本提升、3/10 持平、2/10 变差。
budget4 的 selected-view 平均可靠性高于盲目使用全部 6 视角。
CLIP consistency proxy 确认 steps75 的 learned-image consistency 也更高，
但仍会保留部分整图/背景旋转视图，后续必须叠加 mask 或 face-aware identity filter。
trusted-region mask 将 raw75 CLIP-budget4 的 40 个候选筛到 25 个可用。
subject cutout 输入把 cutout75 CLIP-budget4 可用 mask 提升到 37/40，
因此当时的 diagnostic frontend 改成 cutout -> steps75 -> budget4 -> mask。
face-embedding identity filter 进一步把 cutout75+budget4 的 40 个视角分成
20 个 identity-supervision candidates、14 个 geometry-only candidates、
1 个 identity reject 和 mask-rejected views。
```

这一轮只支持诊断假设：视角选择和过滤比单纯增加 diffusion steps 或视角数更关键。
也进一步支持输入格式假设：先把人物从照片/相框背景中分离，会明显减少
Zero123++ 旋转整张照片而不是旋转头部的失败。
它不证明这些伪视角可以作为重建训练集。

### Week 3

目标：消融和诊断。

1. view budget 曲线。
2. failure taxonomy。
3. identity filtering。
4. 可选：depth / FLAME 小实验。

当前 identity filtering 已在 first10 上跑通，RI3D first2 iter50 和 iter500
也已经闭合下游重建循环。iter500 的结论是：raw75_all6 仍然更差，但
cutout75_budget4_masked 只在一个 first2 样本上优于 raw75_budget4。
G9 已把 downstream reconstruction ablation 的输入从“selected views”
改成显式的 `identity / geometry-only / reject / mask_reject` 四路候选协议，
并完成 first2 role-aware iter500 训练/渲染。结果仍然 ambiguous：角色
metadata 和 geometry-only desaturation 不足以稳定改善 RI3D 输出。
G10 已让 RI3D loss 显式消费 per-view/per-role 权重，但 render sheet
仍然有 fragmented/photo-card artifacts。因此下一步不应先扩 first30/first50，
而应先把 trusted foreground / mask-aware spatial supervision 接入 RI3D loss。
G11 已把 trusted mask 接入 RI3D 的 masked RGB/SSIM、silhouette 和 depth loss，
并完成 first2 iter500。结果显示 loss 不能直接比较，且 render sheet 仍有
小碎片/相框 artifact。下一步应先做 foreground canonical crop/recenter 和
mask-loss ablation；若仍失败，再接 LAM/FLAME/full-head geometry prior，而不是扩 first10。
G12 已完成 foreground canonical crop/recenter 和 mask-loss ablation：输入 sheet
明显更干净，但 USE_MASK=1/0 都仍输出卡片/碎片。当前应转 G13，先验证
LAM/FLAME/full-head geometry prior 能否作为结构锚点；在此之前不扩 first10。
G13 已完成 RI3D foreground point-cloud initialization filter：它去掉了 G12 中
明显的灰色矩形卡片背景，说明初始化确实是一个关键失效源；但输出仍是
前景碎片，不是稳定 3D head。因此下一步 G14 应使用现有 LAM tracking export
里的 FLAME mesh/depth/silhouette 做更强结构先验，或把论文主张转向诊断负结果。
G14 已完成 FLAME proxy depth/conf prior：代理先验可生成、可接入 RI3D，并且
所有 MP4 可读；但它没有修复 G13 的 detached fragments，反而会削弱部分主体
支持。因此当前不应继续堆 RI3D 修补变量，应转向 first10 diagnostic expansion：
把 paper claim 固定为 failure-aware pseudo-view supervision / failure taxonomy，
而不是宣称 RI3D+generic FLAME proxy 已经解决单图 head reconstruction。
重要语义修正：`experiments/downstream_datasets/` 只是伪视图 candidate pool
的历史目录名，不是“已证明可用于重建训练的数据集”。当前筛选指标仍弱，
G8-G14 已经显示候选池即使更干净也会产生碎片/卡片 artifact。后续 first10
应先做 candidate quality audit 和 failure taxonomy，而不是把候选池直接当
validated training set 扩展。
进一步审计后，当前 candidate pool 质量本身极差：大量 selected views 是
split body、rotated photo card、cropped fragment 或背景/身体片段。这个前提
没有站住，所以 G8-G14 的科学解释必须降级为“弱候选池 + RI3D 的失败证据”，
不能说成“可靠伪视角监督协议失败”。之后每个 milestone 必须先过 data audit
gate：结构审计 + PNG 可视/VLM 审计 + 明确 gate verdict，然后才能启动训练。
G15 进一步发现一个严重工程错误：历史 Zero123++ grids 实际是 3x2，但脚本
按 2x3 切 per-view PNG。这个错误污染了 G2-G14 的 per-view PNG 和下游 RI3D
候选。修正 3x2 切分后，head-cutout 伪多视图仍有身份漂移、几何畸变和配件/
发型不一致，因此 web first10 只能保留为 failure taxonomy，不能作为重建训练集。

### Replanned Gate After G15a

```text
G15: candidate-pool recovery and VLM-gated regeneration. Done, blocked for training.
G16: GT multi-view dataset access gate. Use FaceScape/Multiface/NeRSemble/UEA,
     not web pseudo views, for reconstruction-quality validation.
G17: compact GT case export and reconstruction rerun only after G16 passes.
G18: first10 pseudo-view failure taxonomy using corrected 3x2 grids.
G19: conservative paper package and closure.
G20: benchmark-first pivot and route/distribution audit. Done.
G21: compact real-GT benchmark acquisition. Done locally on Multiface debug data;
     raw person-identifying RGB/mesh assets remain under 3dv_work.
G22: real-GT reconstruction/evaluation preflight. Planned; must re-run data/VLM/
     distribution gate before any GPU training.
```

Current G16 access result:

```text
FaceScape sample metadata confirms 58 camera entries, 52 valid views, 2 public
sample images, and a corresponding mesh. The sample readme says not to distribute
it, so only metadata audits are committed. A reconstruction rerun remains blocked
until licensed/publishable or otherwise redistributable GT assets are available.
```

Current G20/G21 result:

```text
H3DS v2 is the preferred technical route but needs access token/license.
Multiface now has a local debug compact case with 9 same-frame real captured
views, KRT cameras, projected mesh masks, and tracked OBJ; it passes G21 as a
local real-GT benchmark premise.
FaceScape remains viable only after licensed full-case access.
No pseudo-view/RI3D scaling is allowed from web candidate pools. The only valid
next method experiment is a real-GT G22 preflight on the G21 case or an
equivalent licensed benchmark.
```

### Week 4

目标：论文成稿。

1. 固定结果。
2. 写完正文。
3. 整理图表和 supplementary。

## 6. 论文骨架

```text
Abstract
1. Introduction
2. Related Work
3. Method
   3.1 Problem formulation
   3.2 Pseudo-view generation
   3.3 View selection and filtering
   3.4 Gaussian head reconstruction baseline
   3.5 Evaluation protocol
4. Experiments
   4.1 Dataset
   4.2 Baselines
   4.3 Metrics
   4.4 Main results
   4.5 View budget study
   4.6 Failure analysis
5. Limitations
6. Conclusion
```

## 7. 参考方向

1. LAM: Large Avatar Model for One-shot Animatable Gaussian Head.
2. PanoLAM: Gaussian Full-Head Synthesis from One-shot Unposed Image.
3. Zero123++: Single Image to Consistent Multi-view Diffusion.
4. RI3D: Few-Shot Gaussian Splatting with Repair and Inpainting Diffusion Priors.
5. PanoHead: Geometry-Aware 3D Full-Head Synthesis in 360°.
6. FaceLift: single-image 360-degree 3D Gaussian head reconstruction with multi-view diffusion.
7. OMEGA-Avatar / OMG-Avatar: 2026 one-shot 360 Gaussian avatar references.
8. Splatent / GS-Diff / VASA-3D: 2025-2026 diffusion+3DGS references that
   reinforce robust losses, multi-view consistency, and sparse-view artifact control.
