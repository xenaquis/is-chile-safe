#!/usr/bin/env bash
# check-secret-hygiene.sh
#
# SEC-05 (F-116/F-117/F-120, FM-01/FM-02/FM-04/FM-06/FM-09): fails the build
# on any of four named log-hygiene risk shapes across the workflow/script
# layer (and one narrow Python-layer check) that could leak a secret value
# into a public Actions log.
#
# FM-01, BLOCKER: this script must not flag itself. Every scanning grep
# below carries --exclude=check-secret-hygiene.sh, and every ::error::
# string is worded so it does NOT contain the literal patterns being
# hunted (e.g. "xtrace/command-echo enabled" instead of a string containing
# "set -x"; "verbose curl invocation" instead of a string containing
# "curl -v"/"--verbose"). Do not "clean up" these strings back to the
# literal hunted text -- that reintroduces the self-flag defect.
#
# FM-02/F-120, BLOCKER: a process substitution's exit status
# (`done < <(grep ...)`) is invisible to both `set -e` and `pipefail` --
# proven this session against check-sha-pins.sh's identical fix. Every
# evidence-gathering grep below therefore captures to an explicit mktemp
# file with `rc=$?` outside any pipeline, and hard-fails on rc >= 2. Never
# use `2>/dev/null || true` (that launders an unreadable-tree failure into
# a false "zero findings" pass).
#
# FM-06, HIGH: this gate has no positive control unless proven against a
# committed, deliberately-dirty canary fixture first. The canary is scanned
# BEFORE the real tree; if any of the four expected findings does not fire
# against it, the instrument is not armed and the script aborts loudly,
# mirroring lint-workflows.sh's own canary structure.
set -euo pipefail

SELF_NAME="check-secret-hygiene.sh"
FIXTURE_DIR=".github/scripts/fixtures/secret-hygiene-canary"

# F-111 + FM-04: 7 real repo secrets PLUS the CF_HOOK alias every consumer
# actually reads in a run: body (cead-scraper.yml, deploy-on-code.yml,
# news-pipeline.yml, require-env.sh). CF_HOOK is NOT a repo secret name --
# it is the job-level env alias for CF_DEPLOY_HOOK_URL.
SECRET_NAMES="CF_DEPLOY_HOOK_URL|CF_HOOK|DEEPSEEK_API_KEY|OPENROUTER_API_KEY|R2_ACCESS_KEY_ID|R2_SECRET_ACCESS_KEY|R2_ENDPOINT_URL|TOKEN_VALUE_R2"

ECHO_PATTERN="(echo|printf)[^|]*\\\$\\{?(${SECRET_NAMES})\\b"
XTRACE_PATTERN="set[[:space:]]+-x\\b|set[[:space:]]+-o[[:space:]]+xtrace"
CURL_PATTERN="curl[^|]*(-v\\b|--verbose)"
BOTOCORE_PATTERN="set_stream_logger|level[[:space:]]*=[[:space:]]*logging\\.DEBUG|level[[:space:]]*=[[:space:]]*10\\b"

# ---------------------------------------------------------------------------
# Scan helpers
# ---------------------------------------------------------------------------

# _scan_grep PATTERN FILE...   -- runs the shared mktemp+rc discipline once;
# result rows land in $SCAN_TMP, hard-fails (exit 1) on rc >= 2.
_scan_grep() {
  local pattern="$1"; shift
  SCAN_TMP="$(mktemp)"
  set +e
  grep -rHnE --exclude="$SELF_NAME" "$pattern" "$@" >"$SCAN_TMP"
  local rc=$?
  set -e
  if [ "$rc" -ge 2 ]; then
    echo "::error::check-secret-hygiene.sh: scan failed (grep rc=$rc) against pattern '$pattern' -- refusing to report a clean tree"
    rm -f "$SCAN_TMP"
    exit 1
  fi
  # rc 0 (matches) and rc 1 (no matches) are both legitimate data.
}

# _count_noncomment_matches FILE -- FM-09: for checks 2/3 only, a match on a
# line whose first non-whitespace character is '#' is a comment, not live
# shell/YAML, and must not count as a finding.
_count_noncomment_matches() {
  local file="$1"
  local n=0
  while IFS=: read -r f l content; do
    stripped="${content#"${content%%[![:space:]]*}"}"
    case "$stripped" in
      "#"*) continue ;;
    esac
    n=$((n + 1))
  done <"$file"
  echo "$n"
}

# _report FILE MESSAGE -- prints ::error:: for every row in FILE (checks 1/4,
# which are NOT comment-line-skipped per FM-09 -- an `echo "# $SECRET"`
# inside a run: body is still live shell, not a YAML/shell comment).
_report_all() {
  local file="$1" message="$2" fail_var="$3"
  while IFS=: read -r f l content; do
    echo "::error file=$f,line=$l::${message}: $content"
    eval "$fail_var=1"
  done <"$file"
}

# _report_noncomment FILE MESSAGE -- FM-09: for checks 2/3, skip comment lines.
_report_noncomment() {
  local file="$1" message="$2" fail_var="$3"
  while IFS=: read -r f l content; do
    stripped="${content#"${content%%[![:space:]]*}"}"
    case "$stripped" in
      "#"*) continue ;;
    esac
    echo "::error file=$f,line=$l::${message}: $content"
    eval "$fail_var=1"
  done <"$file"
}

# ---------------------------------------------------------------------------
# Pass 1: canary fixture (FM-06) -- must fire on ALL FOUR shapes or the
# instrument is not armed and we abort loudly, before trusting anything the
# real-tree pass reports.
# ---------------------------------------------------------------------------

canary_yml="$FIXTURE_DIR/canary-workflow.yml"
canary_sh="$FIXTURE_DIR/canary-script.sh"
canary_py="$FIXTURE_DIR/canary_module.py"

_scan_grep "$ECHO_PATTERN" "$canary_yml" "$canary_sh"
canary_echo_hits=$(wc -l <"$SCAN_TMP" | tr -d ' ')
rm -f "$SCAN_TMP"

_scan_grep "$XTRACE_PATTERN" "$canary_yml" "$canary_sh"
canary_xtrace_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$CURL_PATTERN" "$canary_yml" "$canary_sh"
canary_curl_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$BOTOCORE_PATTERN" "$canary_py"
canary_botocore_hits="$(wc -l <"$SCAN_TMP" | tr -d ' ')"
rm -f "$SCAN_TMP"

if [ "$canary_echo_hits" -lt 1 ] || [ "$canary_xtrace_hits" -lt 1 ] || \
   [ "$canary_curl_hits" -lt 1 ] || [ "$canary_botocore_hits" -lt 1 ]; then
  echo "::error::secret-hygiene canary did not produce its expected findings (echo=$canary_echo_hits xtrace=$canary_xtrace_hits curl=$canary_curl_hits botocore=$canary_botocore_hits) -- instrument is not armed"
  exit 1
fi
echo "check-secret-hygiene.sh: canary armed (echo=$canary_echo_hits xtrace=$canary_xtrace_hits curl=$canary_curl_hits botocore=$canary_botocore_hits)"

# ---------------------------------------------------------------------------
# Pass 2: real tree. Fixture directory is excluded by construction -- the
# top-level globs below (.github/workflows/*.yml, .github/scripts/*.sh,
# pipeline/*.py) do not descend into the fixtures/ subdirectory, so no
# separate --exclude-dir is needed; this is confirmed by design, not
# incidental (shell globs without `**`/`shopt -s globstar` never match a
# path separator).
# ---------------------------------------------------------------------------

fail=0

# Check 1: echo/printf of a secret name or alias -- NOT comment-skipped
# (FM-09: an echo of "# $SECRET" inside a run: body is still live shell).
_scan_grep "$ECHO_PATTERN" .github/workflows/*.yml .github/scripts/*.sh
_report_all "$SCAN_TMP" "possible secret exposure (echo/printf of a secret name)" fail
rm -f "$SCAN_TMP"

# Check 2: set -x / set -o xtrace -- comment-line-skipped (FM-09).
_scan_grep "$XTRACE_PATTERN" .github/workflows/*.yml .github/scripts/*.sh
_report_noncomment "$SCAN_TMP" "xtrace/command-echo enabled (can echo expanded secret args)" fail
rm -f "$SCAN_TMP"

# Check 3: curl -v/--verbose -- comment-line-skipped (FM-09).
_scan_grep "$CURL_PATTERN" .github/workflows/*.yml .github/scripts/*.sh
_report_noncomment "$SCAN_TMP" "verbose curl invocation (can print a secret-bearing URL)" fail
rm -f "$SCAN_TMP"

# Check 4: botocore wire-level DEBUG logging -- F-116/A3, scoped ONLY to
# pipeline/*.py (top-level, not a defensive blanket .py scan). NOT
# comment-skipped -- a live logging.basicConfig call is never a comment.
_scan_grep "$BOTOCORE_PATTERN" pipeline/*.py
_report_all "$SCAN_TMP" "botocore-DEBUG log-hygiene risk (wire-level logging could expose R2 credentials in a traceback)" fail
rm -f "$SCAN_TMP"

if [ "$fail" -eq 0 ]; then
  echo "check-secret-hygiene.sh: clean -- no log-hygiene findings against the real tree"
fi

exit "$fail"
