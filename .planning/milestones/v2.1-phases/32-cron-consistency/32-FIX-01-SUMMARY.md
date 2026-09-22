# Phase 32 "Cron Consistency" — Fix-cycle 1 Summary

Applied per `32-REVIEW.md` (5 HIGH / 9 MEDIUM / 8 LOW) and `32-FABLE-AMENDMENTS.md`'s
"Fix-cycle 1 decisions (F-93..F-97)". Two live-breaking findings (no `R2_BUCKET` secret; no
`setup-python`/`pip install` in `cead-scraper.yml`) were confirmed by the user before dispatch
and treated as established fact, not re-litigated.

## Commits (chronological)

1. `4db3f07` — over-broad secret guards removed (H-01/M-01), CEAD python setup restored
   (H-02), shared `pipeline-failure` label added everywhere (M-02), R2 comment corrected (M-05)
2. `bc785e0` — CEAD heartbeat quarter-boundary rule (F-93), news/r2 seconds precision (F-96)
3. `6c14289` — `lint-workflows.sh` wired into `ci.yml` (H-03), no `push:` trigger added (F-95)
4. `360f979` — `DEPLOYMENT.md` corrected (H-04, M-09), H-05/M-06/M-07/M-08 documented as
   backlog, `.planning/STATE.md` backlog entries added for H-05/M-07
5. `be19db1` — LOW findings triaged: L-01 (`.yaml` glob), L-02 (retry sleep placement), L-03
   (`rebase --abort` exit-code masking), L-04 (`FETCH_HEAD` instead of `origin/<branch>`)
6. `4f2276f` — tests updated for the new interfaces, L-06 (secret-leak failure-path test)
   fixed, L-08 (unused imports) fixed, H-02 class-level pytest guard added

## Fixed (per F-97's list plus L-06)

### H-01 — `r2-archive.yml` guarded `R2_BUCKET`, which is not a secret
**What must fire:** the guard now lists only `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY` — exactly `archive_r2.py:458`'s `required_vars`. Any of those three
being blank still fails the job (verified: `require-env.sh` unit tests
`test_fails_on_blank_secret` / `test_fails_on_all_blank` still pass unmodified).
**What must stay silent:** the real, correctly-configured repo (all three R2 credentials set,
no `R2_BUCKET` secret at all) — confirmed by re-running `bash .github/scripts/lint-workflows.sh`
(unaffected) and by the existing `require-env.sh` "all present" test passing with only three
args. The daily archive will no longer hard-fail on its next 05:30 UTC run.

### H-02 — `cead-scraper.yml` lost `setup-python`/`pip install`
**What must fire:** `TestWorkflowPythonStepsHaveSetup::test_guard_is_non_vacuous_against_a_synthetic_regression`
proves the new class-level pytest guard detects a synthetic H-02-shaped mutation (setup-python
+ pip install removed, `run: python ...` step kept) — RED before restoring.
**What must stay silent:** every other workflow with a `python` step
(`news-pipeline.yml`, `r2-archive.yml`) already had both steps and the guard passes clean
against the real tree (`test_every_workflow_python_step_has_setup_python_and_pip_install`
PASSED). Restored the exact two steps in their original position/form
(`actions/setup-python@v7`, `python-version: '3.12'`, `pip install -r pipeline/requirements.txt`),
between checkout (`fetch-depth: 0` preserved) and "Run CEAD scraper".

### H-03 — `lint-workflows.sh` had zero callers
**What must fire:** `ci.yml`'s `lint-workflows` job now runs
`bash .github/scripts/lint-workflows.sh` instead of `rhysd/actionlint@v1`. Proven by execution:
injected an SC2086-shaped unquoted-expansion defect into a copy of `heartbeat.yml`'s `run:`
block, re-ran the script directly — exit 1, `SC2086` reported — then restored the file
(`git diff --stat` confirmed only the intended edit remained).
**What must stay silent:** the real, clean tree — `bash .github/scripts/lint-workflows.sh`
against all six workflow files → exit 0, canary fired correctly, before AND after every other
fix in this cycle (re-run four separate times across the session). F-95's rejection of a
`push:` trigger was honored — no trigger changes to `ci.yml`, only the step body.

### H-04 / M-09 — `DEPLOYMENT.md` documented deleted/wrong behaviour
Rewrote §6 (secrets table extended to all six consumed secrets + "Consumed by" column), §8a
(the "dry-run mode" framing removed; a missing `CF_DEPLOY_HOOK_URL` is now documented as a hard
post-commit failure), the §1 architecture diagram, the CI permissions row (explicit
workflow-level block, not repo default), and the CRON-07 cadence table for every workflow this
cycle touched. Grepped after edits: `CF_HOOK != ''` and `skipped silently` — zero matches
remaining; `dry-run` — two remaining occurrences both correctly state there is NO silent
skip.

### M-01 — `news-pipeline.yml` hard-guarded `DEEPSEEK_API_KEY`
**What must fire:** the "Guard required secrets" step still hard-fails on a missing/blank
`OPENROUTER_API_KEY` (unchanged, still guarded).
**What must stay silent:** running the job with `DEEPSEEK_API_KEY` unset — `DEEPSEEK_API_KEY`
is no longer in the `require-env.sh` argument list; it remains in the "Run news scraper" step's
`env:` so the alternative provider still works if ever selected.

### M-02 — shared `pipeline-failure` label never created
All four "Ensure alert label exists" steps (news, r2, cead, heartbeat) now also run
`gh label create pipeline-failure --force` alongside the per-pipeline label, both inside the
same `continue-on-error: true` prep step (not the alert step itself, preserving F-87's
ordering guarantee).

### M-03 / F-93 — CEAD heartbeat quarter-boundary rule
Replaced the flat day threshold with: count quarterly due dates (Jan 1 / Apr 1 / Jul 1 / Oct 1
UTC) strictly after the evidence timestamp and up to (inclusive) the as-of timestamp; `>=2` →
fail, `<=1` → pass. New interface: `check-heartbeat.sh cead <evidence_ts> [as_of_ts]` — no
`max_age_days` argument for this mode; `as_of_ts` is optional and defaults to the live clock
only in the (non-test) workflow path.

All four F-93 proof cases verified by direct execution AND encoded as pytest cases:
| evidence | as-of | boundaries | expected | measured |
|---|---|---|---|---|
| 2026-06-19 | 2026-09-30 | 1 (Jul 1) | pass | pass |
| 2026-06-19 | 2026-10-02 | 2 (Jul 1, Oct 1) | fail | fail |
| 2026-09-15 | 2026-10-02 | 1 (Oct 1) | pass | pass |
| 2025-12-31 | 2026-10-02 | 4 (Jan/Apr/Jul/Oct 2026) | fail | fail |

**What must fire:** `TestCheckHeartbeatCead::test_two_boundaries_elapsed_fails` and
`test_old_evidence_four_boundaries_fails` — both exit 1 on the real tree.
**What must stay silent:** `test_one_boundary_elapsed_passes`,
`test_recent_evidence_one_boundary_passes`, plus a boundary-exclusivity case (evidence exactly
ON a due date does not count that same date) and a zero-boundaries case — all exit 0.
**Mutation-proved:** changed `-ge 2` to `-ge 3` in `check-heartbeat.sh`, re-ran
`pytest -k Cead` → `test_two_boundaries_elapsed_fails` went RED (`assert 0 == 1`); other 5
cead tests stayed green (the mutation only affects the 2-boundary case, correctly). Restored,
re-ran → 6/6 green again.

### M-04 / F-96 — integer-day truncation loosened every threshold
`news`/`r2` modes now compare `age_s = now_epoch - ts_epoch` against `max_age_s = max_age_days
* 86400` directly, instead of `age_days = (now-ts)/86400` then comparing days. The boundary
stays pass-inclusive (exactly N days old → exit 0, unchanged and re-verified).
**What must fire:** N days + 1 hour past the threshold. Directly executed:
`news 3 <3d1h-ago>` → exit 1 (previously exit 0 under truncation, since `(3d1h)/86400 = 3` an
integer). `r2 4 <4d1h-ago>` behaves identically.
**What must stay silent:** exactly N days old still exits 0 — directly executed and unchanged.
**Mutation-proved:** reverted the seconds-comparison code to the old
`age_days=$(( (now-ts)/86400 ))` form, re-ran `pytest -k seconds_precision` →
`test_seconds_precision_fails_just_past_threshold` went RED for both `TestCheckHeartbeatR2`
and `TestCheckHeartbeatNews` (`assert 0 == 1`). Restored, re-ran → both green.

### M-05 — R2 guard comment stated a falsehood
Corrected: `archive_r2.py:458-467` returns 0 on missing/blank required vars (a silent no-op),
it does not raise. The comment now states this correctly and frames the guard's value as
"converts a silent no-op into a loud, named failure," not "adds a name to something that
already alerted."

### L-06 — secret-leak test covered only the success path
Split into `test_never_prints_secret_value_on_success` (unchanged) and a new
`test_never_prints_secret_value_on_failure_path`: two named vars, one blank (triggers the
error branch) and one present with a distinctive secret value — asserts the error branch's
output contains the missing-var error line and does NOT contain the present secret's value.

**Correction (32-FIX-02, WR-01):** the sentence originally here claimed this test proves the
review's own mutation (`echo "${!v}"` added to require-env.sh's error loop) "previously
survived undetected." That claim is FALSE — the 32-REVIEW-02.md re-review re-ran that exact
mutation and it SURVIVED against this test too (`echo "${!v}"` on a var that is *blank* prints
an empty line, never a secret value, so no assertion here or in the success-path test catches
it; the review's own original finding was itself a false alarm). What this test actually
proves, confirmed by the re-review's own further mutation testing: a *different*, more
realistic leak shape — a failure-path loop that echoes ALL named vars' values (including a
*present* one) while reporting the missing one — does get caught RED by this test. The test
stays because that coverage is real; the claim above is corrected, not deleted, per WR-01's
requirement not to quietly erase what was actually (and not actually) proven.

## Triaged LOW findings

**Fixed (cheap, safe):**
- **L-01** — `lint-workflows.sh`'s default glob now covers `.github/workflows/*.yml` AND
  `*.yaml` with `nullglob`.
- **L-02** — `push-with-rebase.sh`'s retry `sleep` moved to only run between retries (not
  after the final rebase attempt, not on the last iteration).
- **L-03** — `git rebase --abort` guarded with `|| true`; the explicit `exit 1` immediately
  after is what actually determines the script's exit code, so this does not launder any
  status — it prevents an unrelated `git rebase --abort` failure (exit 128 under `set -e`) from
  masking the intended `exit 1`.
- **L-04** — `push-with-rebase.sh` now rebases against `FETCH_HEAD` (this fetch's actual
  result) instead of `origin/<branch>` (a locally cached ref not guaranteed to update under
  every refspec configuration). Re-ran `pipeline/tests/test_push_race.py` after the change —
  both race-direction tests (disjoint-path survives, same-file aborts loudly) still pass.
- **L-07** — `DEPLOYMENT.md`'s Deploy on Code Push row now also lists the workflow-file-itself
  trigger path, matching `deploy-on-code.yml:30-32`.
- **L-08** — removed unused `import pytest` from both `test_workflow_guards.py` and
  `test_push_race.py` (confirmed unused via `grep -n "pytest\."` returning nothing).

**Deliberately left (with reason):**
- **L-05** — `test_push_race.py` duplicates `_find_bash()` from `test_workflow_guards.py` and
  ships no independent F-86 bash-resolution canary. Left as-is: extracting a shared
  `conftest.py` is a real improvement but touches test infrastructure shared by every future
  test file in this directory, which is a broader change than a fix-cycle triage pass should
  make without dedicated review. The current duplication is safe (both files independently
  resolve a real bash correctly on this machine, verified by both files' own canary/assertions
  passing) — it is a maintainability nit, not a correctness gap.

## Full-suite measured results (after ALL fixes, chained where specified)

1. `bash .github/scripts/lint-workflows.sh` — **exit 0**, zero findings across all six
   workflow files, canary armed. Re-verified arming: injected an SC2086-shaped defect into a
   copy of `heartbeat.yml`, re-ran → exit 1 with `SC2086` reported; restored, re-ran → exit 0.
2. `cd pipeline && python -m pytest tests/ -q` — **375 passed, 1 skipped, 1 xfailed** (was 366
   passed / 1 skipped / 1 xfailed before this cycle; net +9 tests: +2 L-06 split, +1 R2
   boundary, +1 R2 seconds-precision, +3 net CEAD interface rewrite (3 old removed, 6 new
   added), +1 news seconds-precision, +2 H-02 class-level guard). Skipped and xfailed stayed
   exactly 1 and 1, as required.
3. `cd site && npm run build && npm run validate` (single chained command) —
   **16/16 validators passed**, including `freshness` (0.2 days old against the 3-day
   threshold — green, F-19's exclusion was not needed this run).
4. `cd site && npx vitest run` — **59 passed** (6 test files), matching the required count.
5. Mutation-proved both structural changes (see M-03/F-93 and M-04/F-96 sections above for the
   exact break/RED/restore/GREEN sequence on each).

`git status --short` after all commits and the final verification pass shows a clean working
tree with only the intended six commits — no stray temp-file modifications, no accidental
`data/` writes, no push performed.

## Documented, not remediated (F-97's explicit list, reasons per F-97)

- **H-05** — new CEAD data pushed by a maintainer never triggers a production build
  (`deploy-on-code.yml` filters `site/**` only, CF auto-build off). Real, pre-existing gap;
  changing production deploy triggers is outside cron-consistency's scope. Documented in
  `DEPLOYMENT.md` § Known Gaps and `.planning/STATE.md` § Blockers.
- **M-06** — `deploy-on-code.yml` has no failure alert. Accepted: push-triggered, a human is
  already present; widening the deploy job's token for a marginal gain was judged not worth it.
  Documented in the CRON-07 table.
- **M-07** — four `continue-on-error: true` CEAD enrichment steps can commit/deploy partial
  data with a green job. Real, pre-existing; a data-quality defect in the CEAD path, not
  cron-consistency. Documented in `DEPLOYMENT.md` § Known Gaps and `.planning/STATE.md` §
  Blockers.
- **M-08** — `fetch-lint-tools.sh` does not re-verify an already-present binary's SHA-256 on
  every invocation. Accepted: `.tools/` is gitignored/local, and the F-85 canary proves at
  every run that whatever binary is present still produces the correct findings. Documented in
  `DEPLOYMENT.md` § Known Gaps.

## Self-Check

- `.github/scripts/check-heartbeat.sh` — FOUND, modified, executed directly (all 4 F-93 cases
  + seconds-precision cases verified by hand before trusting pytest).
- `.github/scripts/push-with-rebase.sh` — FOUND, modified; `test_push_race.py`'s two race
  tests re-ran green after the `FETCH_HEAD` change.
- `.github/scripts/lint-workflows.sh` — FOUND, modified; executed directly multiple times.
- `.github/workflows/{r2-archive,news-pipeline,cead-scraper,heartbeat,ci}.yml` — FOUND,
  modified; `lint-workflows.sh` shellcheck+actionlint clean against all of them.
- `pipeline/tests/test_workflow_guards.py`, `test_push_race.py` — FOUND, modified; full pytest
  suite run and measured (375/1/1).
- `DEPLOYMENT.md`, `.planning/STATE.md` — FOUND, modified.
- Commits `4db3f07`, `bc785e0`, `6c14289`, `360f979`, `be19db1`, `4f2276f` — all present in
  `git log --oneline -6` on `master`. Not pushed, per instructions.

## Self-Check: PASSED
