#!/usr/bin/env bash
# check-sha-pins.sh
#
# SEC-02 (F-114/F-117/F-118/F-120): fails the build on any `uses:` ref in
# .github/workflows/*.yml that is not pinned to a full 40-hex commit SHA with
# a trailing `# vN.N.N` version comment. This is the ONLY gate in this repo
# that covers SHA-pin regression (F-119: zizmor does not flag first-party tag
# refs as unpinned-uses at either persona).
#
# FM-02/F-120, BLOCKER: a process substitution's exit status
# (`done < <(grep ...)`) is invisible to both `set -e` and `pipefail` -- proven
# this session: a grep against a nonexistent path prints its own stderr error
# line but the enclosing script still reaches `exit 0`. This script therefore
# captures the grep's output to a temp file with an EXPLICIT `rc=$?`, outside
# any process substitution or pipeline, and hard-fails on rc >= 2 itself. Do
# not "simplify" this back to a process substitution.
set -euo pipefail

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

# HI-02/F-125: GitHub accepts both .yml and .yaml for workflow files; a
# *.yml-only glob would silently skip a .yaml workflow from this gate,
# reintroducing the exact L-01 defect lint-workflows.sh:42-48 already fixed.
# nullglob so a genuinely absent extension does not pass a literal
# unexpanded glob string to grep.
shopt -s nullglob
workflow_files=(.github/workflows/*.yml .github/workflows/*.yaml)
shopt -u nullglob
if [ "${#workflow_files[@]}" -eq 0 ]; then
  echo "::error::check-sha-pins.sh: no workflow files found -- refusing to report a clean tree"
  exit 1
fi

# F-117: never launder a scan failure with `2>/dev/null || true` -- that turns
# an unreadable-tree failure into a false "zero findings" pass.
set +e
grep -rHn "uses:" "${workflow_files[@]}" >"$tmp"
rc=$?
set -e

if [ "$rc" -ge 2 ]; then
  echo "::error::check-sha-pins.sh: scan failed (grep rc=$rc) -- refusing to report a clean tree"
  exit 1
fi
# rc 0 (matches found) and rc 1 (no matches) are both legitimate data here --
# rc 1 would itself be caught below by the coverage floor, since uses: lines
# are expected to exist in this repo.

fail=0
count=0

while IFS=: read -r file line content; do
  # RR-M1/F-127: a line whose FIRST non-whitespace character is '#' is a
  # comment, not a step. Commenting a step out (`# - uses: actions/x@v4`) is
  # the ordinary way to disable it, and without this skip it produced an
  # unsatisfiable ::error:: demanding a SHA pin for a ref that does not run.
  # It also left this script inconsistent with check-secret-hygiene.sh, which
  # skips comments in all four of its checks from the SAME CI job (F-126).
  # Note this does NOT weaken detection: a live `- uses:` line starts with
  # '-', never '#'. Comment lines are excluded from `count` as well, so the
  # coverage floor measures real refs (still exactly 13) rather than prose.
  stripped="${content#"${content%%[![:space:]]*}"}"
  case "$stripped" in
    "#"*) continue ;;
  esac
  count=$((count + 1))
  ref="$(printf '%s' "$content" | sed -n 's/.*uses:[[:space:]]*\([^[:space:]#]*\).*/\1/p')"
  if [[ "$ref" != *@* ]]; then
    echo "::error file=$file,line=$line::malformed uses: line, no @ref: $content"
    fail=1
    continue
  fi
  sha="${ref##*@}"
  if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "::error file=$file,line=$line::uses: ref is not pinned to a 40-hex commit SHA: $ref"
    fail=1
  elif ! printf '%s' "$content" | grep -qE '#[[:space:]]*v[0-9]+(\.[0-9]+){0,2}'; then
    echo "::error file=$file,line=$line::SHA-pinned ref missing a '# vN.N.N' version comment: $content"
    fail=1
  fi
done <"$tmp"

# F-117/FM-08: coverage floor. An undercounted or empty scan (e.g. a future
# glob typo that silently narrows .github/workflows/*.yml) must never exit 0.
EXPECTED_MIN_COUNT=13

if [ "$count" -lt "$EXPECTED_MIN_COUNT" ]; then
  echo "::error::check-sha-pins.sh: examined only $count uses: lines, expected at least $EXPECTED_MIN_COUNT -- scan may have been silently narrowed"
  fail=1
elif [ "$count" -gt "$EXPECTED_MIN_COUNT" ]; then
  echo "::notice::check-sha-pins.sh: examined $count uses: lines; EXPECTED_MIN_COUNT is $EXPECTED_MIN_COUNT -- this is a coverage floor, not a pin failure; bump it in check-sha-pins.sh if a step was legitimately added"
else
  echo "check-sha-pins.sh: examined $count uses: lines (>= $EXPECTED_MIN_COUNT)"
fi

exit "$fail"
