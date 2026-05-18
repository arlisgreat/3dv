# External

这里放第三方仓库。第三方源码不提交到主仓库。

## 已管理仓库

清单：

```text
external/repos.tsv
```

版本锁：

```text
external/repos.lock.tsv
```

## 命令

克隆 P0 仓库：

```bash
bash scripts/clone_external.sh P0
```

检查状态：

```bash
bash scripts/external_status.sh
```

添加自己的 fork：

```bash
bash scripts/add_fork_remote.sh LAM https://github.com/arlisgreat/LAM.git
```

## 规则

1. 原作者远程叫 `upstream`。
2. 你的 fork 远程叫 `origin`。
3. 论文改动分支叫 `paper/3dv-pseudo-view-study`。
4. 如果改第三方代码，最后导出 patch 到 `patches/<repo>/`。

