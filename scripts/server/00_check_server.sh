#!/usr/bin/env bash
set -euo pipefail

echo "== System =="
uname -a

echo
echo "== GPU =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi not found"
fi

echo
echo "== Conda =="
if command -v conda >/dev/null 2>&1; then
  conda --version
  conda info --envs
else
  echo "conda not found"
fi

echo
echo "== Python =="
if command -v python >/dev/null 2>&1; then
  which python
  python --version
else
  echo "python not found"
fi

echo
echo "== Disk =="
df -h .

echo
echo "== External repos =="
bash scripts/external_status.sh || true

