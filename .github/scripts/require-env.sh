#!/usr/bin/env bash
# .github/scripts/require-env.sh — fail loudly if any named env var is empty.
# Usage: require-env.sh VAR1 VAR2 ...
#
# CRON-01 (F-76, amended F-84): the deploy-hook skip path used to be a silent
# no-op (a step reported "skipped", never failing the job). This script makes
# every REQUIRED secret a hard, first-step-or-later failure instead. Guard
# the variable a run: step actually CONSUMES (e.g. CF_HOOK, not the secret's
# alias name CF_DEPLOY_HOOK_URL) — F-84 found a rename of the job-level alias
# would otherwise leave the curl unguarded while the guard still passed.
# Never prints a secret's VALUE, only its NAME.
set -euo pipefail
missing=0
for v in "$@"; do
  # F-102: strip whitespace before the emptiness test. A bare `[ -z ]` accepted a
  # whitespace-only value, and `pipeline/archive_r2.py` then `.strip()`s it, treats it
  # as absent and returns 0 — a green job that archived nothing, which is the exact
  # silent no-op this guard exists to abolish, surviving INSIDE the guard. The value is
  # only ever consumed by the test below; it is never echoed.
  if [ -z "$(printf '%s' "${!v:-}" | tr -d '[:space:]')" ]; then
    echo "::error::$v is not set (empty or whitespace-only) — refusing to proceed"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "All required secrets present: $*"
