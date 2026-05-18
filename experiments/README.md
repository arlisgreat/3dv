# Experiments

这里放我们自己的输入、输出、指标和论文图表。

## 结构

```text
experiments/
  inputs/           # 输入头像
  pseudo_views/     # Zero123++ 等生成的伪多视角
  reconstructions/  # LAM / baseline 输出
  metrics/          # CSV / JSON 指标
  figures/          # 论文图
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

