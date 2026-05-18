# Patches

如果我们修改了 `external/` 里的第三方项目，把补丁导出到这里。

推荐格式：

```
patches/
  LAM/
    0001-add-batch-inference-for-3dv-study.patch
  zero123plus/
    0001-save-view-metadata.patch
```

导出命令示例：

```bash
cd external/LAM
git format-patch upstream/main..HEAD -o ../../patches/LAM
```

这样可以在论文主仓库中保留自己的改动证据，同时不污染第三方代码归属。

