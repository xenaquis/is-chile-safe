#!/usr/bin/env bash
# .github/scripts/check-heartbeat.sh — cadence-appropriate staleness checks.
# Each mode is independently testable with a synthetic timestamp; no regex,
# plain numeric epoch-seconds comparison only (F-36 — git-bash corrupts \b in
# node -e regex, so this phase's logic stays in bash with no pattern matching).
#
# Usage:
#   check-heartbeat.sh news <max_age_days> <iso8601_last_generated_timestamp>
#   check-heartbeat.sh r2   <max_age_days> <iso8601_last_run_timestamp>
#   check-heartbeat.sh cead <max_age_days> <iso8601_last_commit_timestamp>
#
# F-83(a): "news" mode is added in this revision. The heartbeat MUST watch the
# 6-hourly news cron; freshness.mjs (validator #15, not #16 — F-83b corrects
# the earlier miscount) only runs via `npm run validate` or in ci.yml, and
# ci.yml is pull_request-triggered only, so it never runs on the quiet repo
# an outage produces. This mode reads the same field freshness.mjs uses
# (data/incidents/current.json's `generated` field) so the two instruments cannot
# disagree.
set -euo pipefail

usage() {
  echo "Usage: $0 {news|r2|cead} <max_age_days> <iso8601_timestamp>" >&2
  exit 2
}

[ "$#" -eq 3 ] || usage
mode="$1"
max_age_days="$2"
ts="$3"

case "$mode" in
  news|r2|cead) ;;
  *) usage ;;
esac

if [ -z "$ts" ]; then
  echo "::error::$mode heartbeat: no timestamp evidence found (empty input) — treating as stalled"
  exit 1
fi

now_epoch=$(date -u +%s)
ts_epoch=$(date -u -d "$ts" +%s 2>/dev/null) || {
  echo "::error::$mode heartbeat: timestamp '$ts' could not be parsed"
  exit 1
}

age_days=$(( (now_epoch - ts_epoch) / 86400 ))

if [ "$age_days" -gt "$max_age_days" ]; then
  echo "::error::$mode heartbeat: last evidence is ${age_days}d old, exceeds ${max_age_days}d threshold"
  exit 1
fi

echo "$mode heartbeat OK: last evidence ${age_days}d old (threshold ${max_age_days}d)"
