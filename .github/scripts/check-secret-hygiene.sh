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

# HI-01/F-125: the bare $VAR/${VAR} shell form is only ONE of several
# real-world shapes that leak a secret into a log. `${{ secrets.NAME }}` is
# THE canonical GitHub Actions expression spelling and the most likely real
# leak; `printenv NAME` and a here-string `<<< "$NAME"` dump the value just
# as plainly. Each shape gets its own sub-pattern so the canary below can
# arm each one individually rather than one pattern papering over a gap.
ECHO_PATTERN="(echo|printf)[^|]*\\\$\\{?(${SECRET_NAMES})\\b"
SECRETS_EXPR_PATTERN="(echo|printf)[^|]*\\\$\\{\\{[[:space:]]*secrets\\.(${SECRET_NAMES})\\b"
PRINTENV_PATTERN="printenv[[:space:]]+(${SECRET_NAMES})\\b"
HERESTRING_PATTERN="<<<[[:space:]]*\"?\\\$\\{?(${SECRET_NAMES})\\b"
EXPOSURE_PATTERN="${ECHO_PATTERN}|${SECRETS_EXPR_PATTERN}|${PRINTENV_PATTERN}|${HERESTRING_PATTERN}"
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

# _report_noncomment FILE MESSAGE -- FM-09/F-126: skip lines whose FIRST
# non-whitespace character is '#'. Used by ALL FOUR checks.
#
# F-126 corrects an earlier rationale in this file which claimed checks 1
# and 4 must NOT skip comment lines because `echo "# $SECRET"` inside a
# run: body is live shell. That reasoning conflates two different things:
# `echo "# $SECRET"` does not START with '#' -- it starts with `echo` --
# so a first-character test never silences it. What the missing skip DID
# silence-fail on was ordinary explanatory prose: this repo's workflows
# are comment-heavy and this very phase writes comments telling readers
# not to echo secrets, each of which reddened the build. Measured: three
# such comments (`# never echo "$DEEPSEEK_API_KEY" ...`, `# do not
# printenv OPENROUTER_API_KEY`, `# never echo "${{ secrets.X }}"`) all
# exited 1 before this change. A guard that bans documenting the rule it
# enforces is the Phase 31 defect (a guard that fires on legitimate
# content), and widening check 1's pattern in fix cycle 1 is what
# enlarged its blast radius.
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
canary_echo_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

# HI-01/F-125: each sibling shape of check 1 gets its own must-fire
# assertion -- a single combined pattern printing "armed" while three
# sibling shapes pass silently is exactly the F-85 defect class relocated
# into this gate's own countermeasure.
_scan_grep "$SECRETS_EXPR_PATTERN" "$canary_yml" "$canary_sh"
canary_secrets_expr_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$PRINTENV_PATTERN" "$canary_yml" "$canary_sh"
canary_printenv_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$HERESTRING_PATTERN" "$canary_yml" "$canary_sh"
canary_herestring_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$XTRACE_PATTERN" "$canary_yml" "$canary_sh"
canary_xtrace_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$CURL_PATTERN" "$canary_yml" "$canary_sh"
canary_curl_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

_scan_grep "$BOTOCORE_PATTERN" "$canary_py"
canary_botocore_hits="$(_count_noncomment_matches "$SCAN_TMP")"
rm -f "$SCAN_TMP"

if [ "$canary_echo_hits" -lt 1 ] || [ "$canary_secrets_expr_hits" -lt 1 ] || \
   [ "$canary_printenv_hits" -lt 1 ] || [ "$canary_herestring_hits" -lt 1 ] || \
   [ "$canary_xtrace_hits" -lt 1 ] || [ "$canary_curl_hits" -lt 1 ] || \
   [ "$canary_botocore_hits" -lt 1 ]; then
  echo "::error::secret-hygiene canary did not produce its expected findings (echo=$canary_echo_hits secrets_expr=$canary_secrets_expr_hits printenv=$canary_printenv_hits herestring=$canary_herestring_hits xtrace=$canary_xtrace_hits curl=$canary_curl_hits botocore=$canary_botocore_hits) -- instrument is not armed"
  exit 1
fi
echo "check-secret-hygiene.sh: canary armed (echo=$canary_echo_hits secrets_expr=$canary_secrets_expr_hits printenv=$canary_printenv_hits herestring=$canary_herestring_hits xtrace=$canary_xtrace_hits curl=$canary_curl_hits botocore=$canary_botocore_hits)"

# ---------------------------------------------------------------------------
# Pass 2: real tree. Fixture directory is excluded by construction -- the
# top-level globs below (.github/workflows/*.yml, .github/scripts/*.sh,
# pipeline/*.py) do not descend into the fixtures/ subdirectory, so no
# separate --exclude-dir is needed; this is confirmed by design, not
# incidental (shell globs without `**`/`shopt -s globstar` never match a
# path separator).
# ---------------------------------------------------------------------------

fail=0

# HI-02/F-125: GitHub accepts both .yml and .yaml for workflow files; a
# *.yml-only glob would silently skip a .yaml workflow from this gate,
# reintroducing the exact L-01 defect lint-workflows.sh:42-48 already fixed.
# nullglob so a genuinely absent extension does not pass a literal
# unexpanded glob string to grep.
shopt -s nullglob
WORKFLOW_FILES=(.github/workflows/*.yml .github/workflows/*.yaml)
shopt -u nullglob
if [ "${#WORKFLOW_FILES[@]}" -eq 0 ]; then
  echo "::error::check-secret-hygiene.sh: no workflow files found -- refusing to report a clean tree"
  exit 1
fi

# Check 1: echo/printf/${{ secrets.X }}/printenv/here-string exposure of a
# secret name or alias -- comment-line-skipped (FM-09/F-126).
_scan_grep "$EXPOSURE_PATTERN" "${WORKFLOW_FILES[@]}" .github/scripts/*.sh
_report_noncomment "$SCAN_TMP" "possible secret exposure (echo/printf/secrets-expression/printenv/here-string of a secret name)" fail
rm -f "$SCAN_TMP"

# Check 2: set -x / set -o xtrace -- comment-line-skipped (FM-09).
_scan_grep "$XTRACE_PATTERN" "${WORKFLOW_FILES[@]}" .github/scripts/*.sh
_report_noncomment "$SCAN_TMP" "xtrace/command-echo enabled (can echo expanded secret args)" fail
rm -f "$SCAN_TMP"

# Check 3: curl -v/--verbose -- comment-line-skipped (FM-09).
_scan_grep "$CURL_PATTERN" "${WORKFLOW_FILES[@]}" .github/scripts/*.sh
_report_noncomment "$SCAN_TMP" "verbose curl invocation (can print a secret-bearing URL)" fail
rm -f "$SCAN_TMP"

# Check 4: botocore wire-level DEBUG logging -- F-116/A3, scoped ONLY to
# pipeline/*.py (top-level, not a defensive blanket .py scan).
# Comment-line-skipped (F-126) -- a Python comment naming set_stream_logger
# is documentation, not an enabled logger.
_scan_grep "$BOTOCORE_PATTERN" pipeline/*.py
_report_noncomment "$SCAN_TMP" "botocore-DEBUG log-hygiene risk (wire-level logging could expose R2 credentials in a traceback)" fail
rm -f "$SCAN_TMP"

if [ "$fail" -eq 0 ]; then
  echo "check-secret-hygiene.sh: clean -- no log-hygiene findings against the real tree"
fi

exit "$fail"
