# 下一阶段实验计划：flame 决定性实验 × 后脑勺方向（2026-10-11）

承接：`00_synthesis.md` 的定位、flame/docs/07_current_findings.md 的
"下一组决定性实验"、主线 G133 的两案例聚合结论。

## A. 立刻可做（本地资产 + 免审批数据）

### A1. G134：Ava-256 后脑勺评测协议（优先）

- 依据：Ava-256（CC BY-NC 4.0，AWS 脚本直接下载，无审批），80 相机 dome
  360° 全覆盖含后脑勺，带 tracked mesh（`docs/04`）。
- 步骤：下载 → 结构/VLM 审计 gate → 选 2-3 个 compact case（正脸 source +
  后脑/侧后 holdout 相机）→ 移植 G54/G55 式 K/R/T 评估器 → 建立
  前/侧/后分组指标（PSNR/SSIM/LPIPS/DreamSim/ArcFace-CSIM + mask IoU）。
- 产出：`experiments/metrics/g134_*` gate 文档 + 可复用评估脚本。
- 注意：NeRSemble 物理上无法评后脑勺（±50° 前半球），Ava-256 是唯一
  免审批的真 360° 真人多相机数据。

### A2. 开源方法的后脑勺体检（G135）

- 在 A1 协议上跑：LAM（已有管线）、FlexAvatar（CVPR'26，开源权重，
  [github.com/tobias-kirschstein/flexavatar](https://github.com/tobias-kirschstein/flexavatar)）、
  FaceLift（Apache-2.0，若权重可用）。
- 价值：首个公开的后脑勺专项对比；预期 LAM 背面显著弱（PanoLAM 已侧面
  证实），FlexAvatar 最强——用我们自己的协议独立验证。
- 这同时给出我们方法的 baseline 差距表。

### A3. Cafca 合成数据接入（备选）

- FaceLift 的评测协议（Cafca 40 人 × 7-19 测试视角，含背面 GT）可直接
  复现，作为 A1 的补充（合成域但相机覆盖全）。

## B. flame 决定性实验（按与后脑勺的耦合度排序）

### B1. 动态 A crossover 的多视图复现（flame 遗留 #1）

- 原限制：公开动态 benchmark 只有单训练相机（temporal held-out）。
- 解锁点：我们已下载 **NeRSemble v2 全量 1.4TB**，每个序列 16 相机。
  可以在动态序列上同时做 temporal held-out + novel-view held-out，
  验证 A 角色的 crossover（8 帧 −4.31 dB → 全量 +3.69 dB）在新视角度量下
  是否保留。
- 与后脑勺的耦合：novel-view held-out 是背面泛化的最近似代理。

### B2. head-unsupported 区域细化：头发/颅顶 ROI

- 现状：head-unsupported 的 released 优势（N_id=384 +5.12 dB）是混合区域
  （头发+轮廓+饰品）。
- 扩展：用 BiSeNet face parsing + scalp/头发 标注把 unsupported ROI 拆成
  hair/scalp/outline 子区域，重评 N_id scaling 曲线——把"后脑勺盲区"
  从聚合指标变成分区证据。直接用 flame/ 的 frozen checkpoints 重评即可，
  不需要重新训练（147 个 checkpoint 已 SHA 冻结）。

### B3. C-local soft transport 可学习分支（flame 遗留 #3）

- 依据 F10：10mm 邻域 local correspondence 显著优于 global，但仍有损失。
  把受控打乱换成可学习 soft transport，测是否回收 C 损失。
- 与后脑勺的耦合：后脑对应关系本就弱，soft transport 是后脑监督的正确
  归纳偏置候选。

### B4. 联合 evidence-conditioned APR（flame 遗留 #4，最重）

- 把已验证的 A gate / G_mu r=30 gate 扩展为 ρ_G/ρ_C/ρ_A/ρ_P 联合释放，
  与 fixed residual / scheduled release / parameter-matched free 对比。
- 排期：在 A1 协议落地后做，这样 APR 可以直接以后脑勺指标为终点。

### B5. mouth localization 反例分析（flame 遗留 #5）

- 独立标注/光流分析 mouth 序列的联动；优先级最低，属于论文健壮性补全。

## C. 方法方向（在 A/B 证据就位后启动）

工作假设：**区域自适应先验释放的全头 3DGS**——

```text
单图 → FLAME/FaceVerse 全头锚定（支撑面内强先验）
     → 支撑面外（后脑/头发）按 flame 证据做 region-conditioned release
     → 头发用 strand 先验（DiffLocks 40K / Im2Haircut PERM）约束
     → 伪视角仅以 identity/confidence gate 过滤后作颜色先验（G110 机制，
       且 G133 提醒：该增益 case-sensitive，不作主卖点）
     → 评测走 A1 后脑勺协议
```

## D. 需要用户/外部的事项

1. RenderMe-360 license 申请（邮件签协议）——背面真机评测的最佳数据。
2. H3DS v2 申请（学术邮箱填表）——全头几何 Chamfer 评测。
3. 确认论文定位（`00_synthesis.md` 第 5 节的三个贡献候选的取舍）。

## E. 风险与止损

- FlexAvatar 若在 A1 协议上全面碾压且开源完善 → 方法贡献退为
  评测协议 + 机制分析（仍有发表价值，参考 flame 的 negative/诊断定位经验）。
- Ava-256 与 NeRSemble 域差大 → 保留 Cafca 合成域协议作对照。
- 头发 strand 先验与 3DGS 桥接若工程代价过高 → 退而用 GaussianHaircut
  双表示或 hair card（CGHair 思路）。
