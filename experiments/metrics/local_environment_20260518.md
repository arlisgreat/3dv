# Local Environment Notes: 2026-05-18

This file records repository-relevant deviations discovered while running the
smoke tests on `/data1/workspace/airulan`. It is intentionally compact; full
logs stay in `/data1/workspace/airulan/3dv_work/logs`.

## Machine

```text
GPU: 8 x NVIDIA A800-SXM4-80GB
working conda: /data1/workspace/airulan/conda/miniconda3
preferred CUDA env: /data1/workspace/airulan/env124.sh
```

Before GPU runs, choose an idle card:

```bash
export CUDA_VISIBLE_DEVICES="$(/home/airulan/.codex/skills/3dv-experiment-orchestrator/scripts/select_idle_gpu.sh)"
```

## env124

`/data1/workspace/airulan/env124.sh` is usable, but it lacks a separator in
`LD_LIBRARY_PATH`. Repair the current shell after sourcing it:

```bash
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
source /data1/workspace/airulan/env124.sh
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH#"$CUDA_HOME/lib64"}"
```

## Network

`hf-mirror` failed metadata checks for both Zero123++ and LAM assets. Direct
HuggingFace worked for Zero123++ and LAM assets, but large LAM-20K downloads
were more reliable via ModelScope.

The shell also had a dead local proxy:

```text
HTTP_PROXY=http://127.0.0.1:6790
HTTPS_PROXY=http://127.0.0.1:6790
ALL_PROXY=socks5://127.0.0.1:6790
```

Unset proxy variables before large downloads unless that proxy is confirmed
alive:

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY="*"
```

## Validated Environments

### Zero123++

```text
conda env: zero123plus
torch: 2.6.0+cu124
torch CUDA: 12.4
diffusers: 0.20.2
transformers: 4.29.2
huggingface_hub: 0.25.2
onnxruntime: 1.23.2
```

### LAM

```text
conda env: lam
torch: 2.6.0+cu124
torch CUDA: 12.4
xformers: 0.0.29.post3
pytorch3d: 0.7.9
diff_gaussian_rasterization: 0.0.0
nvdiffrast: 0.3.3
simple_knn: 1.0.0
scipy: 1.10.1
```

Under PyTorch 2.6, LAM sample inference needs:

```bash
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
```

The DINOv2 encoder checkpoint was cached manually because Torch Hub was very
slow:

```text
.cache/torch/hub/checkpoints/dinov2_vitl14_reg4_pretrain.pth
sha256: 36e4deffbaef061a2576705b0c36f93621e2ae20bf6274694821b0b492551b51
```

## GitHub Tracking

- #1 local CUDA/conda divergence
- #2 hf-mirror failure for Zero123++
- #3 missing onnxruntime for Zero123++ rembg
- #4 LAM env124/cu124 and missing assets
- #5 hf-mirror failure for LAM assets
- #6 dead local proxy for LAM-20K download
- #7 PyTorch 2.6 `weights_only` default for LAM VGGHead
- #8 slow Torch Hub DINOv2 download
