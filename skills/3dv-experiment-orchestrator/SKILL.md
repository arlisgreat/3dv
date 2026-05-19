---
name: 3dv-experiment-orchestrator
description: Orchestrate the local /data1/workspace/airulan/3dv paper-sprint repository for diffusion pseudo-view single-image Gaussian head reconstruction. Use when planning, running, monitoring, rolling back, branching, or syncing arlisgreat/3dv experiments; coordinate LAM, Zero123++, first10/first30 data, GitHub checkpoints, hf-mirror downloads, GitHub mirrors, or agent work for this project.
---

# 3DV Experiment Orchestrator

Use `/data1/workspace/airulan/3dv` as the canonical repository. Keep the current
layout stable:

```text
experiments/inputs/          input manifests and approved cutouts
experiments/pseudo_views/    Zero123++ and mask outputs
experiments/reconstructions/ LAM or downstream reconstruction outputs
experiments/metrics/         CSV/JSON/Markdown metrics and observations
experiments/figures/         publishable PNG figures
external/                    third-party repos, not committed as source
patches/                     third-party patches when needed
skills/                      project-specific Codex skill copy
```

Scratch logs and large handoff notes go under `/data1/workspace/airulan/3dv_work`.
Only publish compact run notes and selected PNG/MP4/CSV/MD artifacts inside the
repo.

## Environment

Use the working conda install:

```bash
export PATH=/data1/workspace/airulan/conda/miniconda3/bin:$PATH
source /data1/workspace/airulan/conda/miniconda3/etc/profile.d/conda.sh
```

For CUDA 12.x work on this host:

```bash
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
source /data1/workspace/airulan/env124.sh
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH#"$CUDA_HOME/lib64"}"
```

Pick an idle GPU before every GPU run:

```bash
export CUDA_VISIBLE_DEVICES="$(skills/3dv-experiment-orchestrator/scripts/select_idle_gpu.sh)"
```

Use local caches:

```bash
export CACHE_ROOT=/data1/workspace/airulan/3dv/.cache
export HF_HOME="$CACHE_ROOT/huggingface"
export TORCH_HOME="$CACHE_ROOT/torch"
export PIP_CACHE_DIR="$CACHE_ROOT/pip"
```

Use `HF_ENDPOINT=https://hf-mirror.com` for HuggingFace downloads when it works.
If a GitHub release is slow, benchmark mirrors such as `ghfast.top` and
`gh-proxy.com`, then record the chosen mirror in the experiment observation.

## Experiment Policy

Current validated pseudo-view frontend:

```text
subject cutout
-> Zero123++ steps75
-> CLIP/reliability budget4
-> trusted-region mask
-> face identity filter
-> identity / geometry-only / reject split
```

Do not feed all pseudo views blindly into downstream Gaussian/PanoHead/FLAME
experiments. Identity-accepted views may supervise face identity. Geometry-only
views may supervise coarse side/back coverage. Mask-rejected and identity-reject
views are excluded unless explicitly used in a failure ablation.

## Sync Policy

Use the helper in dry-run mode first:

```bash
skills/3dv-experiment-orchestrator/scripts/sync_checkpoint.sh \
  --repo /data1/workspace/airulan/3dv \
  --message "sync 3dv experiment checkpoint"
```

Add `--apply` to commit and `--push` to push. Use `--force-add-results` when
the checkpoint should include experiment PNG/MP4/CSV/MD artifacts.

Create a new branch for large or risky changes:

```text
new baseline/method implementation
changed third-party patch behavior
many new experiment outputs
large binary result upload
changes that need a clean rollback point
```

Prefer branch names like `exp/<topic>-YYYYMMDD` or `sync/<topic>-YYYYMMDD`.

## Rollback

Before long experiments:

```bash
skills/3dv-experiment-orchestrator/scripts/status_snapshot.sh \
  /data1/workspace/airulan/3dv \
  > /data1/workspace/airulan/3dv_work/status/before_<task>.md
```

Never reset or delete user changes without explicit instruction. Move unrelated
large untracked experiment outputs to `/data1/workspace/airulan/3dv_work/quarantine`
instead of deleting them.
