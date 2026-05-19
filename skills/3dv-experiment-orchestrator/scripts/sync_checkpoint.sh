#!/usr/bin/env bash
set -euo pipefail

REPO="/data1/workspace/airulan/3dv"
MESSAGE="sync 3dv experiment checkpoint"
APPLY=0
PUSH=0
FORCE_RESULTS=0
BRANCH=""

usage() {
  cat <<'USAGE'
Usage: sync_checkpoint.sh [--repo PATH] [--message MSG] [--branch NAME] [--force-add-results] [--apply] [--push]

Dry-run by default. With --apply, stages and commits safe project files.
With --push, pushes the current branch after committing.
--force-add-results adds selected experiment PNG/MP4/CSV/MD result artifacts.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --force-add-results) FORCE_RESULTS=1; shift ;;
    --apply) APPLY=1; shift ;;
    --push) PUSH=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

cd "$REPO"

echo "== repo =="
pwd
git status --short --branch
echo

echo "== compact result candidates =="
{
  find experiments/inputs -type f \( -name 'manifest.csv' -o -name 'README.md' -o -name '*.json' \) -size -50M -print 2>/dev/null || true
  find experiments/metrics experiments/figures -type f -size -50M -print 2>/dev/null || true
  find experiments/pseudo_views -type f \( -name '*.png' -o -name 'metadata.json' -o -name 'manifest.json' -o -name 'README.md' \) -size -100M -print 2>/dev/null || true
  find experiments/reconstructions -type f \( -name '*.mp4' -o -name 'metadata.json' -o -name 'summary.json' -o -name 'README.md' \) -size -100M -print 2>/dev/null || true
} | sort
echo

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry run only; add --apply to commit, --push to push"
  exit 0
fi

if [[ -n "$BRANCH" ]]; then
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git switch "$BRANCH"
  else
    git switch -c "$BRANCH"
  fi
fi

git add -u
git add README.md PLAN.md SERVER.md data_manifest.csv scripts skills external/repos.tsv external/repos.lock.tsv patches 2>/dev/null || true

if [[ "$FORCE_RESULTS" -eq 1 ]]; then
  while IFS= read -r file; do
    git add -f "$file"
  done < <({
    find experiments/inputs -type f \( -name 'manifest.csv' -o -name 'README.md' -o -name '*.json' \) -size -50M -print 2>/dev/null || true
    find experiments/metrics experiments/figures -type f -size -50M -print 2>/dev/null || true
    find experiments/pseudo_views -type f \( -name '*.png' -o -name 'metadata.json' -o -name 'manifest.json' -o -name 'README.md' \) -size -100M -print 2>/dev/null || true
    find experiments/reconstructions -type f \( -name '*.mp4' -o -name 'metadata.json' -o -name 'summary.json' -o -name 'README.md' \) -size -100M -print 2>/dev/null || true
  } | sort)
fi

if git diff --cached --quiet; then
  echo "nothing staged; no commit created"
  exit 0
fi

git diff --cached --stat
git commit -m "$MESSAGE"

if [[ "$PUSH" -eq 1 ]]; then
  git push -u origin "$(git branch --show-current)"
fi
