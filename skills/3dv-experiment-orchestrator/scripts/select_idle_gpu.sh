#!/usr/bin/env bash
set -euo pipefail

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi not found" >&2
  exit 1
fi

nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits |
  awk -F',' '{
    gsub(/^[ \t]+|[ \t]+$/, "", $1)
    gsub(/^[ \t]+|[ \t]+$/, "", $2)
    gsub(/^[ \t]+|[ \t]+$/, "", $3)
    print $2, $3, $1
  }' |
  sort -n -k1,1 -k2,2 |
  awk 'NR == 1 {print $3}'
