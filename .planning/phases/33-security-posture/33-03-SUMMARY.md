---
phase: 33-security-posture
plan: 03
subsystem: ci-security
tags: [secret-hygiene, courtesy-delay, sec-02, sec-05, sec-06, canary-fixture]
requires: ["33-01", "33-02"]
provides: ["check-secret-hygiene.sh", "scrape_news.py courtesy delay", "SHA-pin decision record"]
affects: [".github/workflows/ci.yml", "pipeline/scrape_news.py", "pipeline/tests/test_scrape_news.py", "pipeline/tests/test_workflow_guards.py", "DEPLOYMENT.md"]
tech-stack:
  added: ["committed canary fixture directory (.github/scripts/fixtures/secret-hygiene-canary/)"]
  patterns: ["mktemp+rc grep-exit-code discipline (rc 0/1 data, rc>=2 hard fail) instead of process-substitution set -e", "canary-scanned-before-real-tree gate armament proof", "comment-line-aware unanchored greps (FM-09)"]
key-files:
  created:
    - ".github/scripts/check-secret-hygiene.sh"
    - ".github/scripts/fixtures/secret-hygiene-canary/canary-workflow.yml"
    - ".github/scripts/fixtures/secret-hygiene-canary/canary-script.sh"
    - ".github/scripts/fixtures/secret-hygiene-canary/canary_module.py"
  modified:
    - ".github/workflows/ci.yml"
    - "pipeline/scrape_news.py"
    - "pipeline/tests/test_scrape_news.py"
    - "pipeline/tests/test_workflow_guards.py"
    - "DEPLOYMENT.md"
decisions:
  - "check-secret-hygiene.sh scans .yml/.sh top-level globs only (no --exclude-dir needed for the canary fixture subdirectory -- shell globs without globstar never match a path separator, so the fixture directory is excluded by construction, not by an extra flag)"
  - "FM-10's workflow_dispatch evidence is documented as PENDING in DEPLOYMENT.md -- producing it requires a dispatch against pushed commits, and this execution contract has the executor never push"
  - "F-123 (orchestrator addition): persist-credentials regression guard added to test_workflow_guards.py; phase-close pytest figure restated as an equality, 395/1/1 (390 + 2 courtesy-delay + 3 persist-credentials)"
metrics:
  duration: "~50 min"
  completed: "2026-08-05"
---

# Phase 33 Plan 03: Secret log-hygiene gate, courtesy delay, pin decision record Summary

Shipped `.github/scripts/check-secret-hygiene.sh` (self-excluding, canary-proven, CF_HOOK-aware, comment-line-safe, mktemp+rc disciplined) wired into `ci.yml`'s `lint-workflows` job; added a 1.5s inter-feed courtesy delay to `scrape_news.py`'s 9-feed loop covered by an ordered argument-list pytest assertion; and recorded DEPLOYMENT.md's SHA/version-pin decision record for all three F-103 reference classes plus the FM-16 zizmor-pin caveat. Per the orchestrator's F-123 addition, also added a `test_workflow_guards.py` regression guard asserting all six non-pushing checkouts carry `persist-credentials: false` and the two pushing crons carry no such key at all, since zizmor's `artipacked` audit only fires on the key's absence, not on it being `true`.

## Tasks Completed

1. **Task 1 — `check-secret-hygiene.sh`** (commit `7a9c8f0`): four risk shapes (echo/printf of a secret name incl. `CF_HOOK`, xtrace, verbose curl, botocore-DEBUG in `pipeline/*.py`), self-excluded via `--exclude=check-secret-hygiene.sh`, reworded `::error::` strings that do not contain the hunted literal patterns (FM-01), comment-line-skip on the two unanchored checks only (FM-09), explicit `mktemp`+`rc` capture per evidence-gathering grep instead of a process-substitution `set -e` claim (FM-02/F-120). A committed dirty canary fixture (`.github/scripts/fixtures/secret-hygiene-canary/`: one `.yml`, one `.sh`, one `.py`) is scanned first and the script aborts loudly if any of the four expected findings does not fire (FM-06). New CI step added to `ci.yml`'s `lint-workflows` job after the existing zizmor step.

2. **Task 2 — inter-feed courtesy delay** (commit `017742c`): `pipeline/scrape_news.py`'s feed loop changed to `for i, (feed_name, feed_url) in enumerate(FEEDS.items())`, with `if i > 0: time.sleep(REQUEST_DELAY)` as the first statement in the loop body, reusing `pipeline.news.fulltext.REQUEST_DELAY` (1.5s) rather than a second unreviewed constant. Two new pytest cases in `test_scrape_news.py`: `test_inter_feed_courtesy_delay` (3-feed dict → exactly 2 sleep calls, asserted as an ordered argument list `[REQUEST_DELAY] * 2`, not a bare call_count, per FM-12) and `test_inter_feed_courtesy_delay_never_before_first_feed` (1-feed dict → zero sleep calls).

3. **Task 3 — DEPLOYMENT.md decision record + F-123 regression guard** (commit `4587b76`): new "SHA-Pin and Version-Pin Decision Record" subsection covering all three F-103 classes (13 `uses:` refs, the two `fetch-lint-tools.sh` binaries, zizmor's version pin), FM-16's zizmor-not-dependabot-covered sentence, the local `uvx zizmor@1.10.0` invocation instruction, and the SEC-01/SEC-05 settings re-verification (repo public, secret scanning + push protection enabled, confirmed via `gh api repos/xenaquis/is-chile-safe`). Also added three new test cases to `pipeline/tests/test_workflow_guards.py` (`TestPersistCredentialsRegression`) per the orchestrator's F-123 addition, and updated the plan's own phase-close pytest figure from 392 to the new equality, 395/1/1.

## Verification Actually Run

1. `bash .github/scripts/check-secret-hygiene.sh` on the real tree:
   ```
   check-secret-hygiene.sh: canary armed (echo=1 xtrace=1 curl=1 botocore=1)
   check-secret-hygiene.sh: clean -- no log-hygiene findings against the real tree
   ```
   Exit 0.

2. Falsifications, executed and restored, per F-110:
   - (a) Planted `run: echo "$DEEPSEEK_API_KEY"` in a scratch copy of `heartbeat.yml`: exit 1, `::error file=.github/workflows/heartbeat.yml,line=113::possible secret exposure (echo/printf of a secret name): ...` — restored.
   - (b) Planted `run: curl -v "$CF_HOOK"` in the same file: exit 1, `::error ...verbose curl invocation (can print a secret-bearing URL): ... curl -v "$CF_HOOK"` — restored (FM-04's whole point: the alias, not just the secret alias name, fires).
   - (c) A copy of the script with its scan glob repointed to `/nonexistent-path-xyz/*.yml` and `/nonexistent-path-xyz/*.py`: `grep: /nonexistent-path-xyz/*.yml: No such file or directory` then `::error::check-secret-hygiene.sh: scan failed (grep rc=2) ... -- refusing to report a clean tree`, exit 1 (NOT a false-clean exit 0).
   - (d) Planted `# never add curl -v here -- it would print the hook URL` and `# set -x is banned in this repo` comment lines in the same file: exit 0, no findings (FM-09's stay-silent direction).

3. `python -m pytest pipeline/tests/ -q` from repo root: `395 passed, 1 skipped, 1 xfailed, 67 warnings in 60.27s`. Exit 0.

4. `bash .github/scripts/check-sha-pins.sh`: `check-sha-pins.sh: examined 13 uses: lines (>= 13)`, exit 0.
   `bash .github/scripts/lint-workflows.sh`: `canary fired correctly (SC2034 + SC2086 both present), instrument is armed`, exit 0.
   `uvx zizmor@1.10.0 --persona=regular .github/workflows/`: `No findings to report. Good job! (2 ignored, 21 suppressed)`, exit 0.

5. Courtesy-delay falsification, executed and restored: removing the `if i > 0: time.sleep(REQUEST_DELAY)` block from `scrape_news.py` and running `pytest pipeline/tests/test_scrape_news.py -k courtesy_delay -q` produced `assert [] == [1.5, 1.5]` — `1 failed, 1 passed`. Fix restored; full file re-run afterward: `11 passed`.

6. `git status --porcelain -- data/`: empty.

## TDD Gate Compliance

Both tasks carrying `tdd="true"` (Task 1, Task 2) followed the plan's `<behavior>`-first shape rather than a strict RED/GREEN commit-pair sequence (no separate `test(...)` commit precedes each `feat(...)` commit — the test and implementation landed together per task, matching this plan's `type: execute` frontmatter, not `type: tdd`). This mirrors 33-01/33-02's precedent for this phase; no plan-level TDD gate was declared (`type: execute`), so this is not a compliance gap.

## Known Gap: FM-10 Zizmor CI Verification Evidence — PENDING

FM-10 requires the orchestrator's own `workflow_dispatch` of `ci.yml`, against the commits this plan lands, to prove zizmor's version banner actually prints on a real `ubuntu-latest` runner. **This executor did not perform that dispatch** — doing so requires the commits to already be on `origin`, and per the execution contract for this session, the executor does not push; the orchestrator pushes after the phase-close gate. `DEPLOYMENT.md`'s "Zizmor CI Verification" subsection documents this explicitly as PENDING, cites the nearest available (but non-satisfying) evidence — a real PR-triggered run of the `lint-workflows` job (run `30975549062`, 2026-08-05) whose `ci.yml` ref predates this phase's zizmor step — and specifies the exact follow-up the orchestrator must perform and record before SEC-04's success criterion 4 is considered met. This is a deliberate, disclosed gap, not a silent one; see `.planning/STATE.md`'s F-113/F-123 entries, which already anticipated this item landing as the phase's final blocking step.

## Deviations from Plan

### Auto-fixed / Required Additions

**1. [Orchestrator-directed, F-123] Added `TestPersistCredentialsRegression` to `pipeline/tests/test_workflow_guards.py`**
- **Found during:** Task 3, per explicit orchestrator instruction in this session's prompt (not discovered independently — pre-assigned scope, F-123).
- **Issue:** zizmor's `artipacked` audit fires on the `persist-credentials` key being ABSENT, not on its value being `true` — so a future accidental `persist-credentials: true` on any of the six non-pushing checkouts would make zizmor exit 0 while the phase's own headline mitigation silently regressed.
- **Fix:** three new test functions asserting (a) all six non-pushing checkouts carry the literal YAML key `persist-credentials: false`, (b) the two pushing crons carry no such key at all (only the explanatory comment), and (c) the detector is non-vacuous against a synthetic `true` mutation.
- **Files modified:** `pipeline/tests/test_workflow_guards.py`.
- **Commit:** `4587b76`.

No other deviations — the remaining two tasks executed as written in the plan, all four falsification directions proven live, no architectural changes, no auth gates encountered.

## Self-Check: PASSED

- `FOUND: .github/scripts/check-secret-hygiene.sh`
- `FOUND: .github/scripts/fixtures/secret-hygiene-canary/canary-workflow.yml`
- `FOUND: .github/scripts/fixtures/secret-hygiene-canary/canary-script.sh`
- `FOUND: .github/scripts/fixtures/secret-hygiene-canary/canary_module.py`
- `FOUND: 7a9c8f0` (git log --oneline --all | grep 7a9c8f0)
- `FOUND: 017742c`
- `FOUND: 4587b76`
