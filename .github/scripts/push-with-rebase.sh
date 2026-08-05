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
  # L-04: rebase against FETCH_HEAD (this fetch's actual result), not
  # origin/<branch> (a locally cached ref that opportunistically updates on
  # `git fetch` but is not guaranteed to under every refspec configuration).
  git fetch origin "$branch"
  if ! git rebase FETCH_HEAD; then
    echo "::error::rebase conflict during data commit — aborting, a human must resolve"
    # L-03: `git rebase --abort` itself can fail (e.g. an already-clean tree)
    # and would exit non-zero under `set -e`, masking the intended exit 1
    # with an unrelated exit 128. The `::error::` line above already ran and
    # survives either way; the explicit `exit 1` below is what actually
    # determines this script's exit code, so `|| true` here is a controlled
    # allowance on a best-effort cleanup call, not exit-code laundering.
    git rebase --abort || true
    exit 1
  fi
  # L-02: sleep only between retries, not after the final rebase (which will
  # loop back to `git push` immediately) and not on the last attempt (which
  # would sleep for no subsequent retry).
  if [ "$i" -lt "$max_attempts" ]; then
    sleep $((i * 3))
  fi
  i=$((i + 1))
done

if [ "$pushed" -ne 1 ]; then
  echo "::error::push failed after $max_attempts attempts"
  exit 1
fi
echo "push succeeded"
