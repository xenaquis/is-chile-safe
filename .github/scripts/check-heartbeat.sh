#!/usr/bin/env bash
# .github/scripts/check-heartbeat.sh — cadence-appropriate staleness checks.
# Each mode is independently testable with a synthetic timestamp; no regex,
# plain numeric epoch-seconds comparison only (F-36 — git-bash corrupts \b in
# node -e regex, so this phase's logic stays in bash with no pattern matching).
#
# Usage:
#   check-heartbeat.sh news <max_age_days> <iso8601_last_generated_timestamp> [iso8601_as_of_timestamp]
#   check-heartbeat.sh r2   <max_age_days> <iso8601_last_run_timestamp> [iso8601_as_of_timestamp]
#   check-heartbeat.sh cead <iso8601_last_commit_timestamp> [iso8601_as_of_timestamp]
#
# F-83(a): "news" mode watches the 6-hourly news cron; freshness.mjs (validator
# #15, not #16 — F-83b corrects the earlier miscount) only runs via `npm run
# validate` or in ci.yml, and ci.yml is pull_request-triggered only, so it
# never runs on the quiet repo an outage produces. This mode reads the same
# field freshness.mjs uses (data/incidents/current.json's `generated` field)
# so the two instruments cannot disagree.
#
# F-96: news/r2 thresholds compare epoch SECONDS against max_age_days*86400,
# not truncated integer days — integer-day division previously made every
# stated threshold up to one day looser than advertised (a "3-day" threshold
# would only fire after 3 days 23h59m). The boundary stays PASS-inclusive:
# exactly N days old still exits 0.
#
# F-93: "cead" mode is QUARTER-BOUNDARY based, not a flat day threshold. A flat
# age threshold cannot distinguish "the maintainer is running late" from "a
# whole quarter was skipped" — tuning the number only slides the false-positive/
# false-negative tradeoff, it cannot remove it (Operating Lesson 26, hit twice
# on this exact check: 100 days cried wolf on a healthy 103-day gap, 150 days
# stayed green through an already-missed quarter). Instead this mode counts how
# many quarterly due dates (Jan 1, Apr 1, Jul 1, Oct 1 UTC) have elapsed in the
# window strictly after the evidence timestamp and up to (inclusive of) the
# as-of timestamp. One elapsed boundary is a maintainer running late (normal,
# stays silent); two or more means a whole quarter was genuinely skipped
# (alert). The as-of date defaults to the live clock (`date -u`) so the
# workflow needs no extra argument, but is always overridable for tests — the
# test path must NEVER depend on a live `date` call, per F-93.
#
# F-99: "news" and "r2" now take the SAME injectable trailing as-of argument
# "cead" already had. F-96's move to second-precision removed the slack that
# integer-day truncation used to absorb, which made the old wall-clock-based
# boundary tests race a truncated evidence string against a marginally later
# live `date` read in the subprocess (measured 3/12 runs red). Giving every
# mode an explicit as-of takes the wall clock out of the test path entirely,
# rather than papering over the race with an epsilon margin. Production
# callers are unaffected: the as-of argument stays optional and defaults to
# the real clock when omitted (see the "no as-of supplied" branches below).
#
# F-100: evidence timestamped more than 24h in the future (relative to as-of)
# is refused in all three modes. A future timestamp yields a negative-or-tiny
# age that trivially passes every threshold check forever — the exact
# silent-green-no-op class this phase exists to abolish, previously hiding
# inside the instrument built to abolish it.
set -euo pipefail

FUTURE_ALLOWANCE_S=86400

usage() {
  echo "Usage: $0 news <max_age_days> <iso8601_timestamp> [iso8601_as_of_timestamp]" >&2
  echo "       $0 r2   <max_age_days> <iso8601_timestamp> [iso8601_as_of_timestamp]" >&2
  echo "       $0 cead <iso8601_timestamp> [iso8601_as_of_timestamp]" >&2
  exit 2
}

[ "$#" -ge 1 ] || usage
mode="$1"

case "$mode" in
  news|r2)
    [ "$#" -ge 3 ] && [ "$#" -le 4 ] || usage
    max_age_days="$2"
    ts="$3"

    if [ -z "$ts" ]; then
      echo "::error::$mode heartbeat: no timestamp evidence found (empty input) — treating as stalled"
      exit 1
    fi

    if [ "$#" -eq 4 ]; then
      as_of="$4"
      if [ -z "$as_of" ]; then
        echo "::error::$mode heartbeat: as-of timestamp was provided but empty"
        exit 1
      fi
      now_epoch=$(date -u -d "$as_of" +%s 2>/dev/null) || {
        echo "::error::$mode heartbeat: as-of timestamp '$as_of' could not be parsed"
        exit 1
      }
    else
      # No as-of supplied (the live workflow path): use the real clock. Tests
      # MUST always pass an explicit as-of and never rely on this branch
      # (F-93/F-99).
      now_epoch=$(date -u +%s)
    fi

    ts_epoch=$(date -u -d "$ts" +%s 2>/dev/null) || {
      echo "::error::$mode heartbeat: timestamp '$ts' could not be parsed"
      exit 1
    }

    # F-100: refuse evidence timestamped more than 24h into the future.
    if [ "$ts_epoch" -gt "$(( now_epoch + FUTURE_ALLOWANCE_S ))" ]; then
      echo "::error::$mode heartbeat: evidence timestamp '$ts' is more than 24h in the future relative to the as-of clock — refusing to treat as healthy"
      exit 1
    fi

    age_s=$(( now_epoch - ts_epoch ))
    max_age_s=$(( max_age_days * 86400 ))
    age_h=$(( age_s / 3600 ))

    if [ "$age_s" -gt "$max_age_s" ]; then
      echo "::error::$mode heartbeat: last evidence is ${age_h}h old, exceeds ${max_age_days}d (${max_age_s}s) threshold"
      exit 1
    fi

    echo "$mode heartbeat OK: last evidence ${age_h}h old (threshold ${max_age_days}d)"
    ;;

  cead)
    [ "$#" -ge 2 ] && [ "$#" -le 3 ] || usage
    ts="$2"

    if [ -z "$ts" ]; then
      echo "::error::cead heartbeat: no timestamp evidence found (empty input) — treating as stalled"
      exit 1
    fi

    ts_epoch=$(date -u -d "$ts" +%s 2>/dev/null) || {
      echo "::error::cead heartbeat: timestamp '$ts' could not be parsed"
      exit 1
    }

    if [ "$#" -eq 3 ]; then
      as_of="$3"
      if [ -z "$as_of" ]; then
        echo "::error::cead heartbeat: as-of timestamp was provided but empty"
        exit 1
      fi
      as_of_epoch=$(date -u -d "$as_of" +%s 2>/dev/null) || {
        echo "::error::cead heartbeat: as-of timestamp '$as_of' could not be parsed"
        exit 1
      }
    else
      # No as-of supplied (the live workflow path): use the real clock. Tests
      # MUST always pass an explicit as-of and never rely on this branch (F-93).
      as_of_epoch=$(date -u +%s)
    fi

    # F-100: refuse evidence timestamped more than 24h into the future.
    if [ "$ts_epoch" -gt "$(( as_of_epoch + FUTURE_ALLOWANCE_S ))" ]; then
      echo "::error::cead heartbeat: evidence timestamp '$ts' is more than 24h in the future relative to '${as_of:-the current clock}' — refusing to treat as healthy"
      exit 1
    fi

    ev_year=$(date -u -d "@$ts_epoch" +%Y)
    asof_year=$(date -u -d "@$as_of_epoch" +%Y)

    boundaries=0
    y="$ev_year"
    end_year=$(( asof_year + 1 ))
    while [ "$y" -le "$end_year" ]; do
      for m in 01 04 07 10; do
        b_epoch=$(date -u -d "${y}-${m}-01T00:00:00Z" +%s)
        if [ "$b_epoch" -gt "$ts_epoch" ] && [ "$b_epoch" -le "$as_of_epoch" ]; then
          boundaries=$(( boundaries + 1 ))
        fi
      done
      y=$(( y + 1 ))
    done

    if [ "$boundaries" -ge 2 ]; then
      echo "::error::cead heartbeat: $boundaries quarterly due dates have elapsed since last evidence ($ts) — a whole quarter was skipped"
      exit 1
    fi

    echo "cead heartbeat OK: $boundaries quarterly due date(s) elapsed since last evidence ($ts)"
    ;;

  *) usage ;;
esac
