#!/usr/bin/env bash
# .github/scripts/lint-workflows.sh — armed-check + canary-proof + real lint (F-85).
# Usage: lint-workflows.sh [workflow-glob...]  (defaults to .github/workflows/*.yml)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
bash "$ROOT/.github/scripts/fetch-lint-tools.sh" >/dev/null

os="$(uname -s)"
case "$os" in
  Linux) AL="$ROOT/.tools/actionlint"; SH="$ROOT/.tools/shellcheck" ;;
  MINGW*|MSYS*|CYGWIN*) AL="$ROOT/.tools/actionlint.exe"; SH="$ROOT/.tools/shellcheck.exe" ;;
  *) echo "::error::unsupported OS $os"; exit 1 ;;
esac

[ -x "$AL" ] || { echo "::error::actionlint not found/executable at $AL"; exit 1; }
[ -x "$SH" ] || { echo "::error::shellcheck not found/executable at $SH — actionlint would silently skip all run: bash without it"; exit 1; }

# Instrument self-test: the canary fixture MUST produce the two SPECIFIC findings it is
# known to contain (SC2034, SC2086) — not merely "some nonzero exit". A corrupted or
# wrong-architecture shellcheck binary ALSO makes actionlint exit nonzero (a fork/exec
# error), which a bare exit-code check would misread as "the canary fired". Requiring
# the specific finding codes closes that gap (found and fixed by mutation-testing this
# exact script this session — see the plan's verified mutation log below).
canary_output="$(cd "$ROOT" && "$AL" -no-color -oneline -shellcheck "$SH" .github/scripts/fixtures/canary-bad-workflow.yml || true)"
if ! grep -q "SC2034" <<<"$canary_output" || ! grep -q "SC2086" <<<"$canary_output"; then
  echo "::error::lint canary did not produce its expected findings (SC2034, SC2086) — shellcheck is either disabled or broken, aborting before trusting the real lint"
  echo "$canary_output"
  exit 1
fi
echo "canary fired correctly (SC2034 + SC2086 both present), instrument is armed"

cd "$ROOT"
targets=("$@")
if [ "${#targets[@]}" -eq 0 ]; then
  # L-01: GitHub accepts both .yml and .yaml for workflow files; a *.yml-only
  # glob would silently skip a .yaml workflow from the very gate meant to be
  # un-skippable. nullglob so a genuinely absent extension does not pass a
  # literal unexpanded glob string to actionlint.
  shopt -s nullglob
  targets=(.github/workflows/*.yml .github/workflows/*.yaml)
  shopt -u nullglob
fi
"$AL" -no-color -oneline -shellcheck "$SH" "${targets[@]}"
