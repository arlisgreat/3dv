# Experiments

这里放我们自己的输入、输出、指标和论文图表。

## 结构

```text
experiments/
  inputs/           # 输入头像
  pseudo_views/     # Zero123++ 等生成的伪多视角
  reconstructions/  # LAM / baseline 输出
  downstream_3d/    # 下游 3D 工作目录，本地 ignored
  metrics/          # CSV / JSON 指标
  figures/          # 论文图
  ri3d_datasets/    # RI3D-compatible downstream inputs
```

## First10

第一批样本放这里：

```text
experiments/inputs/first10/
```

对应清单：

```text
data_manifest.csv
```

样本构成：

```text
3 clean frontal
2 mild side-view
2 glasses
2 complex hair
1 occlusion or low-quality
```

## 输出规则

不要把实验结果散落在 `external/` 里。第三方代码可以临时产出结果，但最终要复制或导出到 `experiments/`。

实验结果需要回传到仓库：伪视角 PNG、重建 MP4、指标和索引文件都提交。权重、cache、第三方源码产物仍然不要提交。

```text
experiments/pseudo_views/**/metadata.json
experiments/pseudo_views/**/*.png
experiments/reconstructions/**/metadata.json
experiments/reconstructions/**/*.mp4
experiments/metrics/*.csv
experiments/metrics/*.md
```

当前 smoke 结果：

```text
experiments/metrics/smoke_runs_20260518.csv
experiments/metrics/local_environment_20260518.md
experiments/pseudo_views/zero123plus_smoke/teaser_low_steps10/
experiments/reconstructions/lam_smoke/status_look_in_my_eyes/
```

当前 first10 pilot 结果：

```text
experiments/inputs/first10/manifest.csv
experiments/figures/first10_wikimedia_contact_sheet.png
experiments/pseudo_views/zero123plus_first10/
experiments/figures/zero123plus_first10_steps20_grids.png
experiments/metrics/zero123plus_first10_steps20.csv
experiments/reconstructions/lam_first10/
experiments/figures/lam_first10_look_in_my_eyes_frames.png
experiments/metrics/lam_first10_look_in_my_eyes.csv
experiments/metrics/first10_pilot_observations_20260518.md
```

当前 iteration 结果：

```text
experiments/pseudo_views/zero123plus_first10_steps75/
experiments/figures/zero123plus_first10_steps20_vs75_grids.png
experiments/figures/view_budget_selection_first10_steps75_budget4.png
experiments/metrics/pseudo_view_reliability_first10_steps20_75.csv
experiments/metrics/pseudo_view_summary_first10_steps20_75.csv
experiments/metrics/view_budget_selection_first10_steps20_75.csv
experiments/metrics/steps20_vs75_comparison_first10.csv
experiments/metrics/zero123plus_first10_steps75_view_budget_observations_20260519.md
experiments/metrics/application_alignment_and_iteration_ideas_20260519.md
experiments/metrics/pseudo_view_clip_consistency_first10_steps20_75.csv
experiments/metrics/view_budget_clip_selection_first10_steps20_75.csv
experiments/figures/view_budget_clip_selection_first10_steps75_budget4.png
experiments/metrics/clip_consistency_filter_observations_20260519.md
experiments/pseudo_views/trusted_region_masks_steps75_budget4/
experiments/metrics/trusted_region_mask_observations_20260519.md
experiments/inputs/first10/cutouts/
experiments/inputs/first10/cutouts_manifest.csv
experiments/figures/first10_cutout_inputs.png
experiments/pseudo_views/zero123plus_first10_cutout_steps75/
experiments/figures/zero123plus_first10_raw_vs_cutout_steps75_grids.png
experiments/pseudo_views/trusted_region_masks_cutout75_budget4/
experiments/metrics/cutout_input_ablation_observations_20260519.md
scripts/evaluate_face_identity_filter.py
experiments/metrics/face_identity_filter_first10_cutout75_budget4.csv
experiments/metrics/face_identity_filter_summary_first10_cutout75_budget4.csv
experiments/figures/face_identity_filter_first10_cutout75_budget4.png
experiments/metrics/face_identity_filter_observations_20260519.md
experiments/ri3d_datasets/first2_160/
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
experiments/metrics/ri3d_first2_roleaware_iter500.csv
experiments/metrics/ri3d_first2_roleaware_observations.md
experiments/figures/ri3d_first2_roleaware_iter500_inputs.png
experiments/figures/ri3d_first2_roleaware_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleaware_iter500/
```
