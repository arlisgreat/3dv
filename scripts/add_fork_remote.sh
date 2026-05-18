#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <repo-name> <your-fork-url>"
  echo "Example: $0 LAM https://github.com/arlisgreat/LAM.git"
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="$1"
fork_url="$2"
target="$ROOT/external/$name"

if [[ ! -d "$target/.git" ]]; then
  echo "Missing repository: $target"
  exit 1
fi

if git -C "$target" remote get-url origin >/dev/null 2>&1; then
  git -C "$target" remote set-url origin "$fork_url"
else
  git -C "$target" remote add origin "$fork_url"
fi

git -C "$target" remote -v

