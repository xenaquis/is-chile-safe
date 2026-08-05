#!/usr/bin/env bash
# .github/scripts/push-with-rebase.sh — push HEAD to origin/<branch>, retrying with a
# fetch+rebase on a non-fast-forward rejection (CRON-06). Assumes the caller already
# committed locally; this script does not stage or commit.
# Usage: push-with-rebase.sh <branch> [max_attempts]
set -euo pipefail
branch="${1:?branch required}"
max_attempts="${2:-5}"

pushed=0
i=1
while [ "$i" -le "$max_attempts" ]; do
  if git push origin "$branch"; then
    pushed=1
    break
  fi
  echo "push rejected, attempt $i of $max_attempts — fetching and rebasing (CRON-06)"
  git fetch origin "$branch"
  if ! git rebase "origin/$branch"; then
    echo "::error::rebase conflict during data commit — aborting, a human must resolve"
    git rebase --abort
    exit 1
  fi
  sleep $((i * 3))
  i=$((i + 1))
done

if [ "$pushed" -ne 1 ]; then
  echo "::error::push failed after $max_attempts attempts"
  exit 1
fi
echo "push succeeded"
