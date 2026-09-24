#!/usr/bin/env bash
# .github/scripts/news-deploy-needed.sh — FRESH-04 / V-12 deploy decision (35-02).
#
# Usage: news-deploy-needed.sh <from-ref> <to-ref>
# Prints exactly one line to stdout: `deploy=true` or `deploy=false`, suitable for
# appending to "$GITHUB_OUTPUT".
#
# deploy=true iff `git diff <from> <to>` touches the PUBLIC incident set:
#   data/incidents/current.json, data/incidents/archive/   (G-20(6) allowlist)
# seen.json, rejected/, pending.json still get committed by news-pipeline.yml but do
# not change what the site serves as incidents, so they do not deploy.
#
# R-09: news-pipeline.yml calls this AFTER `git commit` + push-with-rebase.sh as
# `news-deploy-needed.sh HEAD~1 HEAD` (never --cached), with a fail-open fallback
# (deploy=true + ::warning::) so a failure here can never block data collection (F-84).
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "::error::news-deploy-needed: usage: news-deploy-needed.sh <from-ref> <to-ref>" >&2
  exit 1
fi

from_ref="$1"
to_ref="$2"

set +e
git diff --quiet "$from_ref" "$to_ref" -- data/incidents/current.json data/incidents/archive/
rc=$?
set -e

case "$rc" in
  0) echo "deploy=false" ;;
  1) echo "deploy=true" ;;
  *)
    echo "::error::news-deploy-needed: git diff failed (rc=$rc)" >&2
    exit 1
    ;;
esac
