# Research Plan

## 1. 论文问题

原申请书的完整路线是：

```text
PanoHead + Gaussian Splatting + Diffusion + Transformer + FLAME / 3DMM
```

这个适合一年项目，不适合一个月论文。

当前压缩为一个可实验的问题：

> Diffusion 生成的伪多视角，在单图 Gaussian 人头重建中什么时候有帮助，什么时候会伤害身份一致性？

## 2. 论文贡献点

建议最终写成三点：

1. 系统分析 diffusion pseudo views 在单图 Gaussian head reconstruction 中的收益和风险。
2. 提出轻量级 active view selection / identity filtering 协议。
3. 构建一套 failure taxonomy，分析身份漂移、几何塌陷、纹理不一致、漂浮点和 diffusion 幻觉。

## 3. 实验设计

### Main Comparison

```text
single image only
fixed pseudo views
active selected pseudo views
active + identity filtering
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

目标：主实验。

1. 扩展到 30-50 张。
2. 比较 single / fixed / active / active+filtering。
3. 做第一张主表。
4. 做第一张主图。

### Week 3

目标：消融和诊断。

1. view budget 曲线。
2. failure taxonomy。
3. identity filtering。
4. 可选：depth / FLAME 小实验。

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

