# Server Guide

服务器负责跑模型；本地电脑只管理仓库、写论文、看结果。

## 1. 服务器要求

```text
Linux
NVIDIA GPU
CUDA 11.8 或 12.1
conda / miniconda
git
建议 100GB+ 可用磁盘
```

先检查：

```bash
nvidia-smi
conda --version
git --version
```

如果 `nvidia-smi` 不通，先修 GPU/CUDA，不要继续装环境。

## 2. 拉仓库

```bash
git clone https://github.com/arlisgreat/3dv.git
cd 3dv
bash scripts/clone_external.sh P0
bash scripts/external_status.sh
```

## 3. 设置缓存目录

如果服务器有 `/data`：

```bash
export CACHE_ROOT=/data/$USER/cache/3dv
```

否则：

```bash
export CACHE_ROOT=$PWD/.cache
```

## 4. 检查服务器

```bash
bash scripts/server/00_check_server.sh
```

## 5. 跑 LAM

CUDA 12.1：

```bash
bash scripts/server/01_setup_lam_env.sh cu121
bash scripts/server/02_download_lam_assets.sh hf
bash scripts/server/03_run_lam_sample.sh
```

CUDA 11.8：

```bash
bash scripts/server/01_setup_lam_env.sh cu118
bash scripts/server/02_download_lam_assets.sh hf
bash scripts/server/03_run_lam_sample.sh
```

如果 HuggingFace 下载慢，用 ModelScope：

```bash
bash scripts/server/02_download_lam_assets.sh modelscope
```

## 6. 跑 Zero123++

CUDA 12.1：

```bash
bash scripts/server/04_setup_zero123plus_env.sh cu121
bash scripts/server/05_run_zero123plus_sample.sh
```

CUDA 11.8：

```bash
bash scripts/server/04_setup_zero123plus_env.sh cu118
bash scripts/server/05_run_zero123plus_sample.sh
```

Zero123++ sample 输出：

```text
experiments/pseudo_views/zero123plus_sample/
```

## 7. 跑自己的单张图片

Zero123++：

```bash
conda activate zero123plus
python scripts/zero123plus_generate.py \
  --input experiments/inputs/first10/your_image.png \
  --outdir experiments/pseudo_views/zero123plus/your_image \
  --steps 75
```

LAM：

```bash
conda activate lam
bash scripts/server/03_run_lam_sample.sh experiments/inputs/first10/your_image.png
```

## 8. 常见问题

### LAM 编译失败

通常是 CUDA / torch / gcc 版本不匹配，或者 `pytorch3d`、`diff-gaussian-rasterization`、`nvdiffrast` 编译失败。保留完整日志再处理。

### Zero123++ 下载慢

检查 HuggingFace 网络；必要时配置镜像或代理。

### 显存不足

Zero123++ 基础推理约需 5GB VRAM。LAM 更重，先跑 sample，不要一开始批量跑。

