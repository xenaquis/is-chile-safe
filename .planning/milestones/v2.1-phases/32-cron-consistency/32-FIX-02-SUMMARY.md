# Phase 32 "Cron Consistency" — Fix-cycle 2 Summary (FINAL cycle)

Applied per `32-REVIEW-02.md` (independent Opus re-review: 2 BLOCKER, 9 WARNING) and
`32-FABLE-AMENDMENTS.md`'s "Fix-cycle 2 decisions (F-98..F-101)", which is binding and
overrides the re-review wherever they differ. Per the run's directive, this is the last fix
cycle the plan permits; everything still open after it is carried debt, not a defect.

## Commits (chronological)

1. `e55b1c2` — heartbeat thresholds made clock-injectable for `news`/`r2` (F-99/BL-02),
   future-dated evidence rejected in all three modes (F-100/WR-04), failure message reports
   hours not truncated days (WR-05)
2. `33258ba` — retry loop stops burning an unusable final rebase (WR-08), `FETCH_HEAD` gets a
   discriminating test (WR-03), stale `origin/master` comment corrected (WR-07)
3. `2be880a` — `lint-workflows.sh` shellchecks the phase's own `.github/scripts/*.sh` files
   directly, plus a regression guard on `ci.yml`'s wiring (WR-02)
4. `d71bd18` — `DEPLOYMENT.md` stale prose fixed (WR-06), `32-FIX-01-SUMMARY.md`'s L-06 proof
   claim corrected in place (WR-01)

## BL-01 — REJECTED, per F-98 (binding), no code change

The re-review's premise ("an early scrape's tolerance is consumed by a boundary it already
covers") is wrong: a scrape on 2026-06-19 cannot contain data CEAD publishes on 2026-07-01, so
by 2026-10-01 there are genuinely two unincorporated releases (Jul 1, Oct 1) and firing is the
intended quarter-skip alert, not a false alarm. I did not touch `check-heartbeat.sh`'s
quarter-boundary counting logic. Re-verified by direct execution before starting any other
work:

```
$ bash .github/scripts/check-heartbeat.sh cead "2026-06-19T17:24:23-04:00" "2026-08-04T00:00:00Z"
cead heartbeat OK: 1 quarterly due date(s) elapsed since last evidence (...)
$ bash .github/scripts/check-heartbeat.sh cead "2026-06-19T17:24:23-04:00" "2026-10-01T00:00:00Z"
::error::cead heartbeat: 2 quarterly due dates have elapsed since last evidence (...) — a whole quarter was skipped
```
Both match F-98's designed behaviour exactly.

## Fixed

### BL-02 / F-99 — the CI flakiness, fixed by construction

Confirmed by my own execution first: `pytest tests/test_workflow_guards.py -k
"boundary_exactly_at_threshold"` run 12 times isolated — before this cycle's fix, this class of
test raced a Python-truncated "exactly N days ago" evidence string against a marginally later
live `date -u +%s` read inside the bash subprocess.

**Fix:** `news` and `r2` modes in `check-heartbeat.sh` gained the same optional trailing
`as-of` argument the `cead` mode already had (interface: `check-heartbeat.sh {news|r2}
<max_age_days> <ts> [as_of]`). Every threshold/boundary/precision test in
`TestCheckHeartbeatR2`/`TestCheckHeartbeatNews` now passes fixed, injected evidence AND as-of
timestamps — the wall clock is out of the test path entirely, not narrowed by a margin.
Production callers are unchanged: the workflow invocations in `heartbeat.yml` pass exactly 3
args (unchanged), so they fall through to the same live-clock default branch as before.

**The default (production) path is not left untested** — `test_default_as_of_uses_live_clock`
exists in both `TestCheckHeartbeatR2` and `TestCheckHeartbeatNews`, using a wide 1-day margin
against a 3-4 day threshold (far from any boundary, so it cannot flake, while still proving the
default branch executes and passes).

**Two-direction proof, both directions executed:**
- Measured: `python -m pytest tests/ -q` run **12 times** after the fix — **0/12 red**, every
  run **388 passed, 1 skipped, 1 xfailed** (see "Measured results" below for the full log).
- Mutation: `-gt` → `-ge` in the threshold comparison → both `test_boundary_exactly_at_threshold_passes`
  cases (R2 and News) went RED (`assert 1 == 0`, `::error::... exceeds ... threshold` on what
  should be the pass-inclusive boundary). Restored, re-ran → both green, and `git diff --stat`
  confirmed no drift.

### F-100 / WR-04 — future-dated evidence, fixed in all three modes

A timestamp in the future previously yielded a negative/near-zero age (news/r2) or zero
elapsed boundaries (cead) and passed every check forever — a silent-green-no-op inside the
instrument built to abolish silent-green-no-ops.

**Fix:** all three modes now reject evidence timestamped more than 24h (a deliberate clock-skew
allowance) in the future relative to the as-of clock, with its own distinct
`::error::... is more than 24h in the future ... refusing to treat as healthy` message —
distinguishable in the output from an ordinary staleness failure.

**Two-direction proof, both directions executed:**
- `now+48h` → exit 1, message contains `future` — verified for `news`, `r2`, and `cead`
  (`test_future_evidence_beyond_allowance_fails` × 3).
- `now+1h` → passes normally, unaffected by the allowance — verified for all three
  (`test_future_evidence_within_allowance_passes` × 3).
- Mutation: deleted the future-date guard block from all three branches → all three
  `..._beyond_allowance_fails` tests went RED (`assert 0 == 1`, evidence at `now+48h` returned
  `returncode=0`, e.g. `news heartbeat OK: last evidence -48h old (threshold 3d)`). Restored,
  re-ran the full `test_workflow_guards.py` suite → 40/40 green, `git diff --stat` confirmed
  only the intended 55-insertion/9-deletion change to `check-heartbeat.sh` remained.

### WR-05 (cheap, triaged in) — self-contradictory failure message

`age_days_display` stayed integer-truncated after F-96 moved the comparison to seconds,
producing lines like `"3d old, exceeds 3d threshold"` for evidence only fractionally past the
boundary. The failure line now reports hours (`age_h = age_s / 3600`):
`"73h old, exceeds 3d (259200s) threshold"`. Proven by
`test_failure_message_reports_hours_not_self_contradictory_days` (asserts `"73h"` present,
`"3d old, exceeds 3d"` absent).

### WR-02 — lint instrument regression guard + self-coverage, both gaps closed

1. **`ci.yml` wiring guard:** `test_ci_yml_calls_lint_workflows_script` asserts `ci.yml`
   contains `bash .github/scripts/lint-workflows.sh` and no `uses: rhysd/actionlint` step.
   Mutation: replaced the `run:` line with `run: echo skipped` → test went RED. Restored →
   green, `git diff --stat` clean.
2. **Scripts linted directly:** `lint-workflows.sh` now runs `"$SH" -s bash
   .github/scripts/*.sh` (shellcheck directly on the phase's own scripts), in addition to
   actionlint's inline-`run:`-body coverage of the workflow YAML. Proven both ways:
   - `bash .github/scripts/lint-workflows.sh` on the clean tree → exit 0 (measured, see below).
   - Mutation A: injected an unquoted `$branch` (SC2086) into `push-with-rebase.sh` → exit 1,
     `SC2086` reported. Restored → exit 0.
   - Mutation B: same SC2086 shape injected into `heartbeat.yml`'s `run:` block (proves the
     pre-existing YAML coverage still fires too) → exit 1, `SC2086` reported. Restored → exit 0.
   - `test_lint_workflows_shellchecks_its_own_scripts_directly` (text assertion the invocation
     line exists) — mutation: removed the line → RED. Restored → green.

### WR-08 — retry loop no longer burns an unusable final rebase

With `max_attempts=N`, the old loop fetched+rebased even after the **last** push attempt
failed, even though there is no subsequent attempt that could use it — wasting runner time and
delaying the exhausted-retries report. The loop now `break`s immediately when the failing
attempt is the last one; the real retry budget is exactly `max_attempts` pushes (previously
`max_attempts - 1` effectively did the pushing, with attempt `max_attempts` only ever
fetch+rebasing for nothing).

**Proof:** `test_final_attempt_does_not_burn_an_unusable_rebase` (max_attempts=1, a guaranteed
first-push rejection) asserts the "fetching and rebasing" line never appears and the script
fails fast with `push failed after 1 attempts`. Mutation: removed the last-attempt `break` guard
→ test went RED (`"fetching and rebasing"` appeared in stdout, confirming the old code always
burned the rebase). Restored → green; `pipeline/tests/test_push_race.py` full suite (4 tests)
stayed green, confirming the disjoint-path and same-file-conflict races are unaffected.

### WR-03 — `FETCH_HEAD` change now has discriminating coverage

The existing two race tests could not tell `git rebase FETCH_HEAD` apart from the pre-fix `git
rebase origin/"$branch"` — mutating it back left both green (re-confirmed this cycle before
changing anything). Added `test_fetch_head_used_not_stale_cached_origin_ref`: configures
clone-b's `remote.origin.fetch` refspec to NOT cover `master`, so the cached
`refs/remotes/origin/master` ref never updates on fetch while `FETCH_HEAD` (this fetch's actual,
explicit result) does.

**Proof:** on `FETCH_HEAD` → exit 0, both writers' commits land on origin (measured). Mutation:
reverted to `git rebase origin/"$branch"` → the new test went RED (non-fast-forward push
rejected repeatedly until attempts exhausted — `git push --help` hint in stderr); the two
**pre-existing** race tests stayed green under the same mutation, exactly reproducing the
re-review's original "cannot distinguish the two forms" finding and confirming the new test is
the one that closes it. Restored → all 4 tests green.

### WR-07 (cheap, triaged in) — stale rebase-command citation

`news-pipeline.yml`'s `fetch-depth: 0` comment still read `git rebase origin/master`, a string
L-04 (fix-cycle 1) removed from the repo entirely. Now reads `git rebase FETCH_HEAD`, matching
what the script actually does. `cead-scraper.yml`'s comment points at `news-pipeline.yml`
instead of duplicating the rationale, so this one edit fixes both (unchanged from the
re-review's observation).

### WR-06 (cheap, triaged in) — stale DEPLOYMENT.md prose

- `DEPLOYMENT.md:117` — "Add both of the following" (written when the table had two rows,
  never updated after H-04 extended it to six) → "Add all of the following:".
- `DEPLOYMENT.md:3` — "Last updated: 2026-06-19" → 2026-08-04 (the actual date of this and the
  prior cycle's §1/§6/§8a/§10 rewrites).
- `DEPLOYMENT.md`'s M-07 Known Gap — corrected "masked today by CRON-05/H-02" (H-02 was fixed
  in fix-cycle 1 and no longer contributes to the masking) to name only CRON-05, the still-live
  cause.

### WR-01 — false proof claim in `32-FIX-01-SUMMARY.md`, corrected

The summary claimed the L-06 test was proven by re-running the review's own mutation
(`echo "${!v}"` in `require-env.sh`'s error loop), which "previously survived undetected." The
re-review re-ran that exact mutation literally and it **survived against this test too** — it
prints an empty line for a blank var, never a secret value, so the review's own original finding
was itself a false alarm. The test is **not** worthless: two other mutations (a
loop that unconditionally echoes `$v=${!v:-}`, and a failure-path loop echoing all named vars'
values) both went RED, so it does add real coverage of a different, more realistic leak shape.
The summary's L-06 section was rewritten to state exactly this — what was proven, and what was
not — rather than silently deleting the incorrect sentence.

## Triaged WARNINGs — left as backlog

- **WR-09** (M-02's shared-label fix has no test; `required_vars`/guard-argument coupling H-01
  asked for was never encoded) — not addressed this cycle. Both are real but neither is a
  currently-live defect (verified by reading all four `Ensure alert label exists` steps and
  `r2-archive.yml`'s guard list this session — all correct today), and this is explicitly the
  final permitted fix cycle; adding two more pytest cases plus reasoning through the
  `archive_r2.py:required_vars` parsing correctly under time pressure risked exactly the kind
  of rushed, undertested addition every prior fix cycle in this run introduced a regression
  with. Left as carried debt for a future phase, named here rather than silently dropped.

## Measured results (all gates, chained/looped as specified)

1. **Pipeline pytest, 12 consecutive runs** (the flakiness fix is this cycle's headline —
   1 green run does not demonstrate it):

   | Run | Result |
   |---|---|
   | 1 | 388 passed, 1 skipped, 1 xfailed |
   | 2 | 388 passed, 1 skipped, 1 xfailed |
   | 3 | 388 passed, 1 skipped, 1 xfailed |
   | 4 | 388 passed, 1 skipped, 1 xfailed |
   | 5 | 388 passed, 1 skipped, 1 xfailed |
   | 6 | 388 passed, 1 skipped, 1 xfailed |
   | 7 | 388 passed, 1 skipped, 1 xfailed |
   | 8 | 388 passed, 1 skipped, 1 xfailed |
   | 9 | 388 passed, 1 skipped, 1 xfailed |
   | 10 | 388 passed, 1 skipped, 1 xfailed |
   | 11 | 388 passed, 1 skipped, 1 xfailed |
   | 12 | 388 passed, 1 skipped, 1 xfailed |

   **0/12 runs red.** Total moved from the re-review's measured baseline (375 passed / 1
   skipped / 1 xfailed) to **388 passed** — net +13 tests: +6 F-99 fixed-timestamp/default-path
   coverage (R2 ×1 default-path, News ×1 default-path — the existing boundary/precision tests
   were converted in place, not added), +6 F-100 future-date tests (news/r2/cead × 2
   directions), +1 WR-05 message-format test, +2 WR-02 lint-instrument tests, +1 WR-08 push-race
   test, +1 WR-03 push-race test. Skipped and xfailed stayed exactly 1 and 1, as required.

2. `bash .github/scripts/lint-workflows.sh` → **exit 0**. Re-armed by injecting an SC2086-shaped
   unquoted-expansion defect into a copy of `heartbeat.yml`'s `run:` block → exit 1, `SC2086`
   reported; restored → exit 0. Separately injected the same defect shape into
   `push-with-rebase.sh` (a `.sh` file, not YAML) → exit 1, `SC2086` reported; restored → exit
   0. Both halves proven, both restored, `git status --short` clean after each.

3. `cd site && npm run build && npm run validate` (single chained command) —
   **16/16 validators passed**, including `freshness` (0.3 days old against the 3-day
   threshold — green; F-19's exclusion was not needed this run).

4. `cd site && npx vitest run` → **59 passed** (6 test files), matching the required count.

5. Every new assertion added this cycle was mutation-proved (break → RED → restore → GREEN),
   documented inline above per finding; `git status --short` is clean after all commits.

## Self-Check

- `.github/scripts/check-heartbeat.sh` — FOUND, modified; F-99/F-100/WR-05 changes executed
  directly and via pytest, all mutation-proved.
- `.github/scripts/push-with-rebase.sh` — FOUND, modified; WR-08/WR-03 changes executed via
  `test_push_race.py`, mutation-proved.
- `.github/scripts/lint-workflows.sh` — FOUND, modified; executed directly multiple times,
  WR-02 mutation-proved on both a workflow and a script.
- `.github/workflows/news-pipeline.yml` — FOUND, modified (WR-07 comment only).
- `pipeline/tests/test_workflow_guards.py`, `test_push_race.py` — FOUND, modified; full pytest
  suite run 12 times and measured (388/1/1 every run).
- `DEPLOYMENT.md`, `.planning/phases/32-cron-consistency/32-FIX-01-SUMMARY.md` — FOUND,
  modified (WR-06, WR-01).
- Commits `e55b1c2`, `33258ba`, `2be880a`, `d71bd18` — all present in `git log --oneline -6` on
  `master`. Not pushed, per instructions. `git status --short` clean.

## Self-Check: PASSED
