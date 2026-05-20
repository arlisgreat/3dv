# Experiments

这里放我们自己的输入、输出、指标和论文图表。

## 结构

```text
experiments/
  inputs/           # 输入头像
  pseudo_views/     # Zero123++ 等生成的伪多视角
  reconstructions/  # LAM / baseline 输出
  downstream_datasets/ # pseudo-view candidate pools, not validated training datasets
  downstream_3d/    # 下游 3D 工作目录，本地 ignored
  metrics/          # CSV / JSON 指标
  figures/          # 论文图
  ri3d_datasets/    # RI3D-compatible downstream inputs
  gt_cases/          # optional compact GT case metadata, only if license permits
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

实验结果需要回传到仓库：伪视角 PNG、重建 MP4、指标和索引文件都提交。
权重、cache、第三方源码产物仍然不要提交。

`experiments/downstream_datasets/` 是历史路径名，语义上只是伪视角候选池
导出，不是已经证明适合重建的训练集。
G20 之后，没有 `PASS_REAL_GT_BENCHMARK` 就不能从这些候选池继续训练或做
重建质量结论。

真实人脸/人头数据集同样必须先看许可证。FaceScape sample 已经做过本地
metadata access audit，但 sample readme 明确不允许分发，因此 raw images、
mesh、tarball、thumbnails 和渲染图都不提交；仓库只保存 CSV/JSON/MD 级别
的 access/gate 记录。

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
experiments/metrics/downstream_candidate_pool_semantics_20260519.md
experiments/metrics/milestone_data_audit_protocol_20260519.md
experiments/metrics/first10_candidate_pool_audit_gate_20260519.md
experiments/metrics/first10_candidate_pool_visual_audit_20260519.md
experiments/figures/first10_candidate_pool_audit_gate_20260519.png
experiments/figures/first10_candidate_pool_visual_audit_20260519.png
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
experiments/metrics/ri3d_first2_roleweighted_iter500.csv
experiments/metrics/ri3d_first2_roleweighted_observations.md
experiments/figures/ri3d_first2_roleweighted_iter500_inputs.png
experiments/figures/ri3d_first2_roleweighted_iter500_renders.png
experiments/reconstructions/ri3d_first2_roleweighted_iter500/
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
experiments/metrics/zero123plus_grid_split_bug_20260519.md
experiments/metrics/head_cutout_probe_resplit3x2_gate_20260519.md
experiments/metrics/gt_dataset_route_plan_20260519.md
experiments/metrics/gt_dataset_access_gate_20260519.md
experiments/metrics/facescape_sample_access_audit_20260519.md
```
