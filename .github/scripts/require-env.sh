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
  if [ -z "${!v:-}" ]; then
    echo "::error::$v is not set (empty string) — refusing to proceed"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  exit 1
fi
echo "All required secrets present: $*"
