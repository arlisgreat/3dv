#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/data1/workspace/airulan/3dv}"
WORK="${THREEDV_WORK_ROOT:-/data1/workspace/airulan/3dv_work}"

cd "$REPO"
mkdir -p "$WORK/status" "$WORK/logs" "$WORK/quarantine"

echo "# 3DV Status Snapshot"
echo
echo "- time: $(date -Is)"
echo "- repo: $REPO"
echo "- work: $WORK"
echo "- user: $(whoami)"
echo "- host: $(hostname)"
echo

echo "## Git"
echo '```text'
git status --short --branch || true
git log --oneline --decorate -5 || true
git remote -v || true
echo '```'
echo

echo "## GPU"
echo '```text'
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits || true
echo '```'
echo

echo "## Recent Experiment Files"
echo '```text'
find experiments patches skills -type f -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort | tail -60 || true
echo '```'
