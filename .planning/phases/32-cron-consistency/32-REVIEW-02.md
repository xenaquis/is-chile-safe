---
phase: 32-cron-consistency
reviewed: 2026-08-04T22:00:00Z
depth: deep
diff_base: cde5a96
cycle: re-review after fix-cycle 1
files_reviewed: 14
files_reviewed_list:
  - .github/scripts/require-env.sh
  - .github/scripts/check-heartbeat.sh
  - .github/scripts/push-with-rebase.sh
  - .github/scripts/fetch-lint-tools.sh
  - .github/scripts/lint-workflows.sh
  - .github/workflows/heartbeat.yml
  - .github/workflows/news-pipeline.yml
  - .github/workflows/cead-scraper.yml
  - .github/workflows/r2-archive.yml
  - .github/workflows/deploy-on-code.yml
  - .github/workflows/ci.yml
  - pipeline/tests/test_workflow_guards.py
  - pipeline/tests/test_push_race.py
  - DEPLOYMENT.md
findings:
  critical: 2
  warning: 9
  info: 0
  total: 11
status: issues_found
---

# Phase 32 "Cron Consistency" — Independent Re-Review (fix-cycle 1)

**Reviewed:** 2026-08-04 · **Depth:** deep (execution + mutation) · **Base:** `cde5a96..HEAD`
**Status:** issues_found — **2 BLOCKER**, 9 WARNING

I did not take the fixer's summary as evidence. Every claim below was reached by running the
artifact or by mutating it and watching the suite. `git status --porcelain` is empty at the end
of this review (verified); every mutation was reverted with `git checkout --`. No push, no
`workflow_dispatch`, no issue/label mutation, no `data/` write.

**Headline:** the fix cycle is unusually disciplined on scope — I looked hard for collateral and
found almost none (no `permissions:` edits, no trigger widening, no `data/` writes). But **both
structural redesigns are defective**: F-93's quarter-boundary rule fires a false alarm on the
repo's real current evidence 58 days from now, and F-96's seconds-precision change turned two
boundary tests into a measured **25% CI flake**.

---

## Measured gate results (run by me, this session)

| Gate | Command | Measured |
|---|---|---|
| Workflow lint | `bash .github/scripts/lint-workflows.sh` | **exit 0**, canary fired (SC2034+SC2086) |
| Pipeline tests | `cd pipeline && python -m pytest tests/ -q` | **375 passed, 1 skipped, 1 xfailed** (skipped=1, xfailed=1 ✓) |
| Site | `cd site && npm run build && npm run validate` (one command) | build 834 pages, **16/16 validators passed** |
| Site unit | `cd site && npx vitest run` | **59 passed** (6 files) |
| Shellcheck (by hand — nothing in CI does this) | `.tools/shellcheck.exe -s bash .github/scripts/*.sh` | **exit 0**, zero findings |

The fixer's reported numbers reproduce exactly. That is the *only* thing about the fix summary I
was able to confirm without qualification.

---

## BLOCKER

### BL-01 · F-93's quarter-boundary rule will fire a false "a whole quarter was skipped" alert on 2026-10-01, on the repo's real evidence — the "running late" tolerance is consumed by scraping EARLY

**File:** `.github/scripts/check-heartbeat.sh:112-128` (the boundary counter), wired at
`.github/workflows/heartbeat.yml:59-63`
**Class:** a monitor that cries wolf on a legitimate cadence — the exact failure F-83c and F-93
were both written to eliminate, reintroduced in a new shape.

The rule counts quarterly due dates strictly after the evidence timestamp. It therefore assumes
evidence always lands **on or after** the due date it satisfies. A maintainer who scrapes a few
days **before** the due date has their one-boundary tolerance consumed immediately by the
boundary their own fresh scrape already covered.

The repo is in exactly that state today. `git log -1 --format=%cI -- data/cead/` →
`2026-06-19T17:24:23-04:00` — twelve days *ahead* of the 2026-07-01 due date.

**Executed proof** (real evidence, as-of the first heartbeat run of Q4):

```
$ bash .github/scripts/check-heartbeat.sh cead "2026-06-19T17:24:23-04:00" "2026-10-01T12:00:00Z"
::error::cead heartbeat: 2 quarterly due dates have elapsed since last evidence
        (2026-06-19T17:24:23-04:00) — a whole quarter was skipped
rc=1
```

And the general shape, proven independently of today's data — a maintainer scraping 3 days early,
every quarter, forever:

```
$ bash ... cead 2026-09-28T00:00:00Z 2026-12-31T00:00:00Z   → rc=0  (1 boundary)
$ bash ... cead 2026-09-28T00:00:00Z 2027-01-01T12:00:00Z   → rc=1  (2 boundaries)   <-- day zero of the quarter
$ bash ... cead 2026-10-01T03:00:00Z 2027-01-02T12:00:00Z   → rc=0  (on-time scrape is fine)
```

**Failure scenario:** on **2026-10-01 at 12:00 UTC** — nine hours after `cead-scraper.yml`'s own
quarterly reminder fires at 03:00 UTC, and before any human could plausibly have run the local
scrape — `heartbeat.yml` goes red and opens `[pipeline] Heartbeat detected a stalled cron`. It
then re-fires **daily**, and because heartbeat dedup is `--state open` (F-89's named residual),
closing it produces a new one the next day. The operator gets two independent daily alert streams
(cead-scraper's and heartbeat's) on the first day of the quarter, for a system that is behaving
correctly. That is alert fatigue manufactured on a schedule, and it masks the next real outage.

Note the second-order consequence: **M-03's original complaint is not actually closed.** M-03
said the check was green on an allegedly-already-missed 2026-07-01 quarter. The new rule is *also*
green on that same quarter today (1 boundary). What changed is only *when* it goes red — and it
goes red at the worst possible moment.

**Remedy:** count boundaries against the *quarter the evidence belongs to*, not against the
evidence instant. Concretely: map the evidence timestamp to its containing quarter's due date
`Q(ts)` (the most recent Jan 1 / Apr 1 / Jul 1 / Oct 1 **at or before** `ts + grace`, where a
14-day forward grace credits an early scrape to the upcoming due date), then count due dates
strictly after `Q(ts)` and `<= as_of`; fail on `>= 2`. Equivalent minimal shape: before counting,
advance `ts_epoch` to the next boundary if one falls within 14 days after it.

**How the remedy is proven:** add these four pytest cases alongside the existing six, with
injected as-of dates, and confirm the current code fails them before the change:
- evidence `2026-06-19`, as-of `2026-10-01T12:00Z` → **exit 0** (early Q3 scrape, Q4 just opened)
- evidence `2026-06-19`, as-of `2027-01-02T12:00Z` → **exit 1** (Q4 genuinely skipped)
- evidence `2026-09-28`, as-of `2027-01-01T12:00Z` → **exit 0**
- evidence `2026-10-01T03:00Z`, as-of `2027-01-02T12:00Z` → **exit 0** (unchanged, on-time path)
Then mutate the grace window to 0 days and confirm the first and third go RED — otherwise the
grace is decorative.

---

### BL-02 · F-96's seconds-precision change made two boundary tests flaky — measured 3 failures in 12 runs (25%)

**Files:** `pipeline/tests/test_workflow_guards.py:206-210` (`TestCheckHeartbeatR2::test_boundary_exactly_at_threshold_passes`),
`:307-311` (`TestCheckHeartbeatNews::test_boundary_exactly_at_threshold_passes`),
helper `:186-190` (`_iso_days_ago`)
**Class:** a gate that fails on a correct tree, nondeterministically.

`_iso_days_ago(N)` builds the timestamp in Python with `strftime("%Y-%m-%dT%H:%M:%SZ")`, which
**truncates sub-second precision**, making the evidence up to 0.999 s older than "exactly N days
ago". The script then reads its own clock in a *later* subprocess. With the arithmetic:

```
ts_epoch  = floor(T) - N*86400          (Python truncation)
now_epoch = floor(T + spawn_delay)      (bash `date -u +%s`)
age_s     = N*86400 + floor(frac(T) + spawn_delay)
```

`age_s > max_age_s` — and the test fails — whenever `frac(T) + spawn_delay >= 1`. Under the old
integer-day comparison this was impossible (`(N*86400 + ε)/86400` truncated back to `N`); F-96
removed exactly that safety margin.

**Executed proof** — 12 consecutive isolated runs of just these two tests:

```
$ for i in $(seq 1 12); do python -m pytest tests/test_workflow_guards.py -q \
    -k "boundary_exactly_at_threshold"; done
run1: 1 failed, 1 passed     run10: 1 failed, 1 passed     run11: 1 failed, 1 passed
(the other nine runs: 2 passed)
TOTAL_RUNS_WITH_FAILURE = 3/12
```

It also fired spontaneously during an unrelated mutation run in this session, which is how I found
it — not by reading.

**Failure scenario:** `ci.yml`'s `pipeline` job runs `pytest pipeline/tests/ -q` on every pull
request. Roughly one PR in four gets a red CI for a reason that has nothing to do with the change
under review. This repo has spent four phases teaching people that a red gate means something;
F-95 rejected a `push:` trigger specifically to avoid manufacturing a recurring red signal, and
the fix cycle then manufactured one anyway, inside the test suite.

**Remedy:** stop round-tripping through a truncated string for the boundary cases. Either
(a) have `_iso_days_ago` floor the *base* clock first — `datetime.now(timezone.utc).replace(microsecond=0)` — and subtract a small deliberate margin for the boundary tests
(`_iso_days_ago(N) - 2s` is still "at or inside the threshold" and is the semantics the test
means), or (b) give `check-heartbeat.sh` an injectable `HEARTBEAT_NOW_EPOCH` override and pin both
sides of the comparison, matching what F-93 already requires for the cead mode ("the test path
must NEVER depend on a live `date` call") — the news/r2 modes were left on the live clock.

**How the remedy is proven:** run the two boundary tests 100 times in a loop and require 100
passes; then mutate `check-heartbeat.sh`'s `-gt` to `-ge` and require both to go RED on the first
run — proving the fix removed the flake without removing the assertion's teeth.

---

## WARNING

### WR-01 · The L-06 "fix" does not kill the mutation it claims to kill

**File:** `pipeline/tests/test_workflow_guards.py:155-175`; docstring at `:156-162`; also asserted
in `32-FIX-01-SUMMARY.md:121-127`

The test's own docstring says it covers "the exact branch the review's mutation
(`echo "${!v}"` in the error loop) would have hit and previously survived undetected." I applied
that literal mutation:

```
$ sed -i 's|    missing=1|    echo "${!v}"\n    missing=1|' .github/scripts/require-env.sh
$ cd pipeline && python -m pytest tests/test_workflow_guards.py -q -k RequireEnv
8 passed, 21 deselected     <-- MUTATION SURVIVED
```

It survives because that branch only executes for vars that are **empty** — `echo "${!v}"` prints
a blank line, never a secret. The review's original M5 was itself a false alarm.

Credit where due: the test is *not* worthless. I built two further mutations and both went RED —
`echo "checking $v=${!v:-}"` at the top of the loop (2 failed) and a failure-path loop echoing all
values (1 failed, caught only by the new test). So L-06 added genuine coverage; only the stated
proof is false.

**Remedy:** correct the docstring and the summary to describe what the test actually kills (a
failure-path leak of a *present* var's value), and add the harmless-mutation note so nobody
re-opens it. **Proof:** the two mutations above, recorded with their RED output.

### WR-02 · H-03's fix has no regression guard, and the second half of the remedy was dropped — the phase's own five bash scripts are linted by nothing in CI

**Files:** `.github/workflows/ci.yml:68-69`, `.github/scripts/lint-workflows.sh:43`

Two gaps:

1. **No test asserts `ci.yml` invokes `lint-workflows.sh`.** `grep -rn "lint-workflows" pipeline/tests/ site/` returns nothing. The exact defect H-03 found — the instrument having zero callers — can silently recur on the next edit to `ci.yml`, and nothing reddens. The review's stated proof (push a defective branch, confirm CI red, then confirm green) was replaced by a manual local injection, which is a claim, not a gate.
2. **`.github/scripts/*.sh` are still unlinted by any automation.** `actionlint -shellcheck` lints only inline `run:` bodies; the workflows call the scripts as `run: bash .github/scripts/…`, so actionlint never sees them. This cycle edited three of the five (`check-heartbeat.sh` +140 lines, `push-with-rebase.sh`, `lint-workflows.sh`) with no shell linting anywhere in the loop. I ran it by hand — `shellcheck -s bash .github/scripts/*.sh` → **exit 0, zero findings**, so there is no live defect today; the *gate* is missing, not the quality.

**Remedy:** append to `lint-workflows.sh` (so both callers get it):
`"$SH" -s bash "$ROOT"/.github/scripts/*.sh`; and add a pytest asserting
`'bash .github/scripts/lint-workflows.sh' in ci.yml` **and** that `rhysd/actionlint` does not
appear in it.
**Proof:** delete the `run:` line from `ci.yml` → the new pytest goes RED; introduce `SC2086`
(an unquoted `$branch`) into `push-with-rebase.sh` → `lint-workflows.sh` exits 1. Both halves,
red first.

### WR-03 · L-04's `FETCH_HEAD` change is an unproven edit to the live push path

**File:** `.github/scripts/push-with-rebase.sh:22`

I mutated it straight back to the pre-fix form and the suite did not notice:

```
$ sed -i 's/git rebase FETCH_HEAD/git rebase origin\/"$branch"/' .github/scripts/push-with-rebase.sh
$ cd pipeline && python -m pytest tests/test_push_race.py -q
2 passed
```

Both forms pass, so `test_push_race.py` cannot distinguish them. The change is plausible and I
found no way to break it, but it modifies the script that pushes production data four times a
day, and it ships with zero discriminating evidence. F-91 requires proofs be *encoded*.

**Remedy:** add a third race test whose bare-clone is configured with a non-covering refspec
(`git config remote.origin.fetch '+refs/heads/nothing:refs/remotes/origin/nothing'`) — under that
topology `origin/<branch>` goes stale and `FETCH_HEAD` does not.
**Proof:** the new test must PASS on `FETCH_HEAD` and FAIL when mutated back to `origin/"$branch"`.

### WR-04 · `cead` mode silently passes on a future-dated evidence timestamp

**File:** `.github/scripts/check-heartbeat.sh:114-123`

`end_year=$(( asof_year + 1 ))` and the loop starts at `ev_year`; when the evidence is in the
future the window is empty and `boundaries=0`:

```
$ bash ... cead 2027-06-01T00:00:00Z 2026-08-04T00:00:00Z
cead heartbeat OK: 0 quarterly due date(s) elapsed ...   rc=0
$ bash ... cead 2030-01-01T00:00:00Z 2026-08-04T00:00:00Z   → rc=0
```

A committer date in the future is not exotic — a skewed local clock on the maintainer's quarterly
push, or a rewritten/cherry-picked commit, produces it, and `git log --format=%cI` reports it
verbatim. The monitor then reports green forever. The other three input-garbage cases are handled
correctly (unparseable evidence, unparseable as-of, empty as-of, empty evidence all exit 1 with a
named message — verified), which makes this the one hole.

**Remedy:** after parsing, `[ "$ts_epoch" -le "$as_of_epoch" ] || { echo "::error::cead heartbeat: evidence timestamp '$ts' is in the future relative to '$as_of' — refusing to treat as healthy"; exit 1; }`.
**Proof:** the two commands above must exit 1; the six existing cead cases must stay green.

### WR-05 · The seconds fix left the human-readable message self-contradictory

**File:** `.github/scripts/check-heartbeat.sh:69,72`

`age_days_display` is still integer-truncated while the comparison is in seconds, so the failure
line reads:

```
::error::news heartbeat: last evidence is 3d old, exceeds 3d threshold
```

Measured directly on a 3-day-and-1-second-old timestamp. A maintainer reading "3d old exceeds 3d
threshold" in an alert issue will reasonably conclude the guard is broken and start debugging the
monitor instead of the cron — which is how a correct alert gets dismissed.

**Remedy:** report hours or one decimal place: `age_h=$(( age_s / 3600 ))` →
`"last evidence is ${age_h}h old, exceeds ${max_age_days}d (${max_age_s}s) threshold"`.
**Proof:** assert the failure-path stdout of `news 3 <3d+1s>` contains `73h` and does not contain
`3d old, exceeds 3d`.

### WR-06 · `DEPLOYMENT.md` §6 still says "Add both of the following" above a six-row table

**File:** `DEPLOYMENT.md:117`

H-04's remedy extended the table from two rows to six and left the sentence introducing it
untouched. A maintainer following §6 literally adds two secrets and stops — which is the same
class of onboarding failure H-04 was raised to fix, one line above the table that fixes it.
Two adjacent stale items in the same document:

- `DEPLOYMENT.md:3` — "Last updated: 2026-06-19", after a 2026-08-04 rewrite of §1, §6, §8a and §10.
- `DEPLOYMENT.md:288` — the M-07 Known Gap says the defect is "masked today by CRON-05/**H-02**
  (the scraper never gets past step 1 on Actions)". H-02 was fixed in this very cycle; only
  CRON-05 (the 403) still masks it. Citing a closed finding as a live mitigation is exactly the
  drift H-04 exists to prevent.

**Remedy:** "Add all of the following:"; bump the date; drop the `/H-02` citation.
**Proof:** a doc test asserting the §6 row count equals the number of distinct `secrets.X`
references across `.github/workflows/*.yml` (currently 5 consumed + the table's 6th optional row)
— which is the check H-04's own remedy proposed and the fix cycle did not build.

### WR-07 · `news-pipeline.yml`'s `fetch-depth: 0` rationale now describes code that no longer exists

**File:** `.github/workflows/news-pipeline.yml:29`

> `# fetch-depth: 0 (CRON-06) -- push-with-rebase.sh's ` **`git rebase origin/master`**

L-04 changed that line to `git rebase FETCH_HEAD`. The rationale for `fetch-depth: 0` still holds,
but the comment now cites a command string that appears nowhere in the repo — the next reader
greps for it, finds nothing, and cannot tell whether the comment or the script is wrong.
`cead-scraper.yml:43` dodges this by pointing at news-pipeline.yml instead, so the drift is
single-sourced and one edit fixes both.
**Remedy:** `git rebase FETCH_HEAD`. **Proof:**
`grep -c 'origin/master' .github/workflows/*.yml` → 0.

### WR-08 · The retry loop still burns its final attempt on a rebase it will never push

**File:** `.github/scripts/push-with-rebase.sh:12-45`

L-02 removed the *sleep* after the final rebase but not the rebase itself. With
`max_attempts=5`, attempt 5 pushes, fails, fetches, rebases — and then the loop condition ends the
loop, so `pushed=0` and the script exits 1 with the local branch freshly rebased onto origin and
never pushed. The data commit exists locally on a runner that is about to be destroyed; the job
goes red and alerts (correct), but one of the five "attempts" is structurally incapable of
succeeding, so the real retry budget is 4 pushes, not 5. The review's L-02 remedy — move the sleep
to the *top* of the loop body — would have fixed both at once.

**Remedy:** restructure as `for i in $(seq 1 max); do [ "$i" -gt 1 ] && sleep $(((i-1)*3)); git push && exit 0; fetch; rebase; done`.
**Proof:** a test with `max_attempts=2` against a bare clone that moves once — assert exactly two
`git push` invocations occur (instrument via `GIT_TRACE` or a wrapper on PATH) and the second
succeeds; today the second push happens but a third rebase is executed on failure paths.

### WR-09 · M-02's shared-label fix has no test, and neither does the guard-argument/`required_vars` coupling H-01 asked for

**Files:** `.github/workflows/{news-pipeline,r2-archive,cead-scraper,heartbeat}.yml` (the four
`Ensure alert label exists` steps); `.github/workflows/r2-archive.yml:41`

`grep -rn "pipeline-failure" pipeline/tests/` returns nothing. The `gh label create pipeline-failure`
line is present in all four workflows (I verified each by reading), but nothing reddens if a future
edit drops it from one of them — and the failure mode it prevents is the unrecoverable one F-87
names (the alert about the failure fails).

Likewise, H-01's stated remedy included *"add a pytest case that reads `required_vars` out of
`pipeline/archive_r2.py` and asserts the workflow's `require-env.sh` argument list is **equal** to
it"* — the coupling that makes the drift non-recurrable. Only the one-off edit was applied. The
suite already parses workflow text for the H-02 guard, so the machinery exists.

**Remedy:** two pytest cases — (a) every `Ensure alert label exists` step's body contains both the
per-pipeline and the shared label; (b) `r2-archive.yml`'s `require-env.sh` argument list equals
`archive_r2.py`'s `required_vars` set.
**Proof:** delete `gh label create pipeline-failure` from `heartbeat.yml` → (a) RED; re-add
`R2_BUCKET` to the guard → (b) RED. Restore both.

---

## Previous review's findings: independently CONFIRMED closed vs merely CLAIMED

**Confirmed closed by execution (naming what I ran):**

| ID | How I confirmed |
|---|---|
| **H-01** | Read `r2-archive.yml:36-41` — guard list is exactly the three credentials. Ran `env -u R2_BUCKET R2_ENDPOINT_URL=x R2_ACCESS_KEY_ID=k R2_SECRET_ACCESS_KEY=s bash require-env.sh R2_ENDPOINT_URL R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY` → rc 0. `R2_BUCKET` no longer appears anywhere in the file (`git diff` confirms both the guard arg and the `env:` entry were removed). |
| **H-02** | Read `cead-scraper.yml:42-67` — order is checkout(`fetch-depth: 0`) → `setup-python@v7` (3.12) → `pip install -r pipeline/requirements.txt` → `python pipeline/scrape_cead.py`. Nothing was displaced: job-level `PYTHONPATH: .` (`:40`) and `env: CF_HOOK` are intact, the `fetch-depth: 0` that caused the original loss is still on checkout. The class-level guard is load-bearing: I deleted the `setup-python`+`pip install` pair from **news-pipeline.yml** and `test_every_workflow_python_step_has_setup_python_and_pip_install` went RED (1 failed, 28 passed); restored. |
| **H-03 (install path only)** | The runner-side question the fixer could not answer locally, answered: I downloaded both **Linux** artifacts and hashed them. `actionlint_1.7.7_linux_amd64.tar.gz` → `023070a287cd8ccc…` and `shellcheck-v0.11.0.linux.x86_64.tar.xz` → `8c3be12b05d5c177…` — **both match the pins in `fetch-lint-tools.sh:22,24` exactly**. Archive members verified: actionlint's tarball contains a flat `actionlint` (so `tar -xzf … actionlint` is right) and shellcheck's contains `shellcheck-v0.11.0/shellcheck` (so the `mv "$tmpdir/shellcheck-v${SHELLCHECK_VERSION}/shellcheck"` path is right). I extracted both to confirm. The lint job will install its linter on the CI runner. |
| **M-01** | `news-pipeline.yml:50-53` guards `OPENROUTER_API_KEY` only; `DEEPSEEK_API_KEY` survives at `:65` in the scrape step's `env:`, so the alternative provider still works. |
| **M-04 / F-96 (the behaviour, not the tests)** | Executed both directions on both modes at second granularity. Exactly N days → rc 0; N days **+1 second** → rc 1; N days −1 second → rc 0. Verified for `news 3` *and* `r2 4`. Mutated the comparison back to `age_days_display -gt max_age_days` → both `test_seconds_precision_fails_just_past_threshold` cases went RED (2 failed, 27 passed); restored. The precision claim is true. (The tests it broke are BL-02.) |
| **M-05** | `r2-archive.yml:31-35` now states the corrected baseline (silent `return 0`, not an exception). Matches `archive_r2.py:458-467`. |
| **M-09** | `DEPLOYMENT.md:248` states "explicit workflow-level `permissions: contents: read`" and lists all three `ci.yml` jobs — matches `ci.yml:8-9` and `ci.yml:12,33,50`. |
| **L-01** | `lint-workflows.sh:39-41` globs `*.yml` **and** `*.yaml` under `nullglob`. |
| **L-03** | `push-with-rebase.sh:30` — `git rebase --abort \|\| true` followed by an explicit `exit 1`. Not laundering: the `exit 1` is what sets the status. |
| **L-07** | `DEPLOYMENT.md:247` lists both trigger paths, matching `deploy-on-code.yml:30-32`. |
| **L-08** | `import pytest` absent from both test files (read directly). |
| **F-93 mechanics** | All four F-93 cases reproduce exactly (1→pass, 2→fail, 1→pass, 4→fail). Boundary exclusivity holds (evidence exactly on a due date does not count it — mutating `-gt` to `-ge` at `:118` turns `test_evidence_exactly_at_boundary_counts_as_elapsed` RED; restored). Year-boundary case `2025-12-31 → 2026-01-01` counts 1, `→ 2026-04-01` counts 2. Timezone-offset evidence (`-04:00`) parses. No division by zero, no infinite loop; the pathological `1999-01-01` input terminates in 2.6 s with 110 boundaries. The *mechanics* are sound — the *semantics* are BL-01. |
| **Scope discipline** | `git diff 9555df8..HEAD` reviewed line by line. **Zero** `permissions:` edits, **zero** trigger changes, **zero** `data/` writes, no changes to `require-env.sh` or `fetch-lint-tools.sh`, no dropped comments. Phase 33's ownership of `permissions:` was respected. `push-with-rebase.sh` was touched only for L-02/L-03/L-04, all of which the review requested. |

**Merely claimed — I could not confirm, and one is provably overstated:**

| ID | Status |
|---|---|
| **H-03 (runtime behaviour on Linux)** | I proved the tools *install*; I could not execute `actionlint` v1.7.7 + `shellcheck` v0.11.0 on Linux to confirm the canary still emits both SC2034 and SC2086 there. Same versions as local, so it very likely holds, but if it does not the CI job fails with `lint canary did not produce its expected findings` — loudly, not silently, so the F-85 defect is *not* re-created. Recorded as a residual, plus the missing regression guard (WR-02). |
| **H-04** | Substantially closed — `CF_HOOK != ''` and "skipped silently" are gone (grep: 0 hits), §8a describes hard failure, the §1 diagram is correct, §6 was extended. But it is **not** internally consistent: see WR-06 (three residual false or stale statements, one of them the sentence directly above the table H-04 fixed). |
| **L-06** | Claimed to kill the review's surviving mutation. **It does not** — proven by re-running that exact mutation, which survived (WR-01). The test does add real coverage of a different, more realistic leak shape. |
| **L-02 / L-04** | Applied, but neither is discriminated by any test (WR-03, WR-08). |
| **M-02** | The code is present in all four workflows (verified by reading each). No test guards it (WR-09). |
| **M-03** | The *interface* changed as designed; the underlying complaint (green on an allegedly-missed quarter) is still green today, and the new rule mis-fires later (BL-01). |
| **H-05, M-06, M-07, M-08** | Documented, not fixed — per F-97, correctly. I re-verified each is genuinely described in `DEPLOYMENT.md` § Known Gaps / the CRON-07 table, and H-05/M-07 in `.planning/STATE.md`. No objection. |

---

## Where I looked hard and found nothing (verified negatives)

These cost more time than the findings and are worth as much.

1. **Exit-code laundering, swept from scratch on the current tree.** Grepped every shipped script and workflow for `node -e`, `|| true`, `|| echo`, `; echo ok`, trailing `| tail` / `| head`, and `;` breaking an `&&` chain. Three hits, all benign: the compensated canary (`lint-workflows.sh:24`, fully offset by the `grep -q SC2034` + `grep -q SC2086` pair on the next line), `push-with-rebase.sh:30`'s cleanup `|| true` followed by an explicit `exit 1`, and two occurrences inside comments. **No hidden exit codes.**
2. **The canary still cannot be fooled after this cycle's edits.** `bash .github/scripts/lint-workflows.sh` → exit 0 with `canary fired correctly (SC2034 + SC2086 both present)`. The `nullglob` L-01 edit did not weaken the armed-check: the canary runs before target selection and uses an explicit fixture path, so an empty glob cannot skip it.
3. **`shellcheck -s bash .github/scripts/*.sh` → exit 0, zero findings** across all five scripts, including the three edited this cycle. All use `set -euo pipefail`. No live shell defect — only the missing gate (WR-02).
4. **Guard-input garbage handling in `check-heartbeat.sh` is complete except for the future-date hole.** Executed: empty evidence → rc 1 "no timestamp evidence found"; unparseable evidence → rc 1 "could not be parsed"; unparseable as-of → rc 1; empty-but-provided as-of → rc 1 "as-of timestamp was provided but empty"; unknown mode → rc 2 with `Usage:` on **stderr**; missing args → rc 2. Every one names its cause. Only WR-04 escapes.
5. **F-78 byte identity survived the fix cycle.** `grep -h 'curl -X POST' <the three workflows> | sed 's/^ *//' | sort -u | wc -l` → **1**. All three deploy-hook invocations are still identical.
6. **All five live-production paths re-traced on the current files.** News cron: data changed → commit → push-with-rebase → `Guard deploy hook` (no `if:`, runs always) → `Trigger deploy` gated on `steps.commit.outputs.changed == 'true'` → hook fires exactly once. Data unchanged → `changed=false`, guard still runs, deploy step skipped, **no hook** (correct). Scrape failed → job red at the scrape step, no commit, no hook, label+issue path reached. Guard failed (blank `CF_HOOK`) → job red **after** the data is committed and pushed, F-84 satisfied. Push rejected then rebase-conflicted → `push-with-rebase.sh` exits 1 inside the commit step, so `changed=true` is never written to `$GITHUB_OUTPUT` and the deploy correctly does not fire. CEAD cron: unchanged behaviour, now reaching the scraper with a real interpreter. **The deploy hook still fires exactly when it should; I found no path that fires it spuriously and none that drops a deploy that was owed.** (H-05 — the maintainer's local `data/` push — remains unfired, correctly documented as an accepted gap.)
7. **The H-02 class-level guard's parser is crude but not vacuous.** `_python_run_steps_missing_setup` uses indentation heuristics rather than YAML, and its job-reset test also matches 2-space keys under `on:` (e.g. `  schedule:`) — harmless, since those always precede any steps. I confirmed it is load-bearing by the news-pipeline deletion mutation above, and confirmed its own vacuity check (`test_guard_is_non_vacuous_against_a_synthetic_regression`) really does strip both steps from its in-memory copy.
8. **No collateral in the fix diff.** Enumerated in the table above — the fix cycle changed only what it was asked to change. Given this run's history (Phase 30's three regressions, Phase 31's two landmines), I expected to find scope creep and did not.
9. **Repo left clean.** Seven mutations applied and reverted (`check-heartbeat.sh` ×3, `require-env.sh` ×3, `news-pipeline.yml` ×1, `push-with-rebase.sh` ×1). `git status --porcelain` → empty. No push, no `workflow_dispatch`, no issue/label writes, no `data/` writes; the only network calls were two read-only GitHub release downloads into the scratchpad.

---

_Reviewed: 2026-08-04 · Reviewer: gsd-code-reviewer (independent second pass, adversarial, execution + mutation) · Depth: deep_
