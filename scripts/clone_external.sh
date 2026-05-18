#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/external/repos.tsv"

mkdir -p "$ROOT/external"

priority="${1:-P0}"

tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r name url branch role repo_priority; do
  if [[ -z "${name:-}" ]]; then
    continue
  fi

  if [[ "$repo_priority" != "$priority" ]]; then
    continue
  fi

  target="$ROOT/external/$name"
  if [[ -d "$target/.git" ]]; then
    echo "[skip] $name already cloned at $target"
    git -C "$target" remote -v
    continue
  fi

  echo "[clone] $name -> $target"
  git clone "$url" "$target"
  git -C "$target" remote rename origin upstream
  git -C "$target" checkout -B "paper/3dv-pseudo-view-study"
  echo "[done] $name: $role"
done
