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

### 本机 env124 已验证路径

在 `/data1/workspace/airulan` 这台机器上，实际可用的是 CUDA 12.4
环境，而不是脚本默认假设的 cu121/cu118。2026-05-18 已验证：

```text
conda env: lam
CUDA env: /data1/workspace/airulan/env124.sh
torch: 2.6.0+cu124
xformers: 0.0.29.post3
pytorch3d: 0.7.9
scipy: 1.10.1
```

运行前使用空闲 GPU，并修复 `env124.sh` 的 `LD_LIBRARY_PATH` 分隔符：

```bash
export PATH=/data1/workspace/airulan/conda/miniconda3/bin:$PATH
source /data1/workspace/airulan/conda/miniconda3/etc/profile.d/conda.sh
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
source /data1/workspace/airulan/env124.sh
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH#"$CUDA_HOME/lib64"}"
export CUDA_VISIBLE_DEVICES="$(/home/airulan/.codex/skills/3dv-experiment-orchestrator/scripts/select_idle_gpu.sh)"
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy HF_ENDPOINT
export NO_PROXY="*"
export CACHE_ROOT=$PWD/.cache
export HF_HOME="$CACHE_ROOT/huggingface"
export TORCH_HOME="$CACHE_ROOT/torch"
```

LAM-20K 权重在本机通过 ModelScope 下载更稳定：

```bash
conda activate lam
modelscope download "Damo_XR_Lab/LAM-20K" \
  --local_dir "./external/LAM/model_zoo/lam_models/releases/lam/lam-20k/step_045500/"
```

如果 Torch Hub 下载 DINOv2 很慢，先手动缓存：

```bash
curl -L -C - --retry 20 --retry-delay 5 --speed-limit 102400 --speed-time 120 \
  -o .cache/torch/hub/checkpoints/dinov2_vitl14_reg4_pretrain.pth \
  https://dl.fbaipublicfiles.com/dinov2/dinov2_vitl14/dinov2_vitl14_reg4_pretrain.pth
```

已验证 smoke 输出索引在：

```text
experiments/metrics/smoke_runs_20260518.csv
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
