#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/external/repos.tsv"

tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r name url branch role priority; do
  if [[ -z "${name:-}" ]]; then
    continue
  fi

  target="$ROOT/external/$name"
  echo "== $name ($priority) =="
  if [[ ! -d "$target/.git" ]]; then
    echo "missing: $target"
    continue
  fi
  git -C "$target" status --short
  git -C "$target" branch --show-current
  git -C "$target" log -1 --oneline
done
