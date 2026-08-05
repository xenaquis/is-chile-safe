# Phase 32 — Fable plan review, cycle 1: AMENDMENTS (F-83..F-91)

**Verdict on the plans as drafted: REJECTED, revision required.** The Opus plan-checker returned
NEEDS REVISION (6 blockers) and the Opus premortem returned 5 phase-killing findings. They agree
on three items and each found things the other missed. I re-derived the load-bearing ones by
execution rather than accepting either report (Operating Lesson 5).

**Three of the defects below are in MY OWN binding decisions, not in the planner's work.** They are
recorded by name, in the F-70 tradition, because a decision doc that is wrong propagates further
than a plan that is wrong.

---

## F-83 — CORRECTION OF MY OWN F-79, in three separate places

### (a) The heartbeat must watch the NEWS cron, and my stated compensating control does not exist

F-79's own threshold table has a News row. The plans dropped it and justified the drop with a
sentence **I wrote**: that `freshness.mjs` "re-derives the news signal from `data/` on every local
`npm run validate` and in `ci.yml`". Verified: `ci.yml` triggers on `pull_request` +
`workflow_dispatch` **only**. In the exact scenario this phase exists to prevent — a quiet repo
with dead crons — no PR is opened, so `freshness.mjs` never runs, and the local path needs a human
already at the keyboard. **If the news cron stopped tomorrow, nothing in this repo would go red on
its own.** That is the phase's headline invariant failing on the phase's most important cron.

This is the same error shape as F-70: I asserted a compensating control without checking the
trigger conditions of the thing I was leaning on, and the plan inherited the false premise.

Required: a `news` mode in `check-heartbeat.sh` (threshold **3 days**, evidence =
`data/incidents/current.json`'s `generated` field, the same source and number `freshness.mjs` uses,
so the two instruments cannot disagree) and a third step in `heartbeat.yml`. Two-direction pytest
proof: `now-5d` → exit 1; `now-1d` → exit 0; exactly `now-3d` → exit 0 (boundary inclusive,
matching the `-gt` already proven). Plus `grep -c 'check-heartbeat.sh news' .github/workflows/heartbeat.yml`
≥ 1, so deleting the wiring reddens something — otherwise the tests pass while the workflow is mute.

### (b) `freshness.mjs` is validator **#15**, not #16 — my error, repeated into the plan

`site/scripts/validate/all.mjs:19` → `15. freshness.mjs`; line 20 → `16. facets.mjs`. F-79 said #16
and `32-03-PLAN.md`'s heartbeat header comment copied it. A documentation-correctness milestone
writing a wrong validator number into a new file is Operating Lesson 25 exactly. Fix both.

### (c) The CEAD threshold of 100 days is arithmetically guaranteed to cry wolf — raise it to **150**

Measured, not estimated: `git log -1 --format=%cI -- data/cead/` → `2026-06-19T17:24:23-04:00`.
The next quarterly scrape is due 2026-10-01, which is **103 days** later. With a 100-day threshold
the heartbeat opens a `pipeline-failure-cead` issue around **2026-09-27, four days before the scrape
is even due**, every day, for a perfectly healthy system. A monitor that cries wolf on a legitimate
cadence stops being read, and the next real alert dies with it (Operating Lesson 26: I widened
coverage on the stall axis and narrowed it into a false positive on the legitimate-cadence axis).

150 days is the number: it still fires when an entire quarter is genuinely skipped (two consecutive
misses ≈ 182+ days) while tolerating a maintainer who is weeks late — and this run exists precisely
because the maintainer is away. State both directions in the plan: **MUST fire** on a gap spanning
two quarterly boundaries; **MUST stay silent** on any gap ≤ 150 days, including the real 103-day one
measured above. Encode both as pytest cases with an injected "as-of" date, never a live `date`.

## F-84 — CORRECTION OF MY OWN F-76: the deploy-hook guard moves AFTER the commit step

F-76 put `CF_DEPLOY_HOOK_URL` into the first-step guard of `news-pipeline.yml` and
`cead-scraper.yml`. Both Opus passes independently flagged the consequence and they are right:
today a rotated hook loses only the *deploy*; under F-76 as written it kills the **scrape**, four
times a day, so RSS items age out of their feeds and become a permanent hole in the corpus. One
broken secret would redden two signals instead of one, and the second one is unrecoverable.

The loudness F-76 exists to buy costs nothing here: keep `CF_DEPLOY_HOOK_URL` **out** of the
first-step guard in those two workflows, and give it its own hard guard placed **after** the
"Commit data if changed" step and **before** the curl. An empty hook then still fails the job hard,
still reaches `if: failure()`, still alerts — and the news data for that run is collected, committed
and pushed first. Strictly better on every axis.

Unchanged: in `deploy-on-code.yml` the guard stays first-step, because there is genuinely nothing
else for that job to do. The rest of F-76 stands: no soft skip anywhere, the `env.CF_HOOK != ''`
clause is deleted, the "dry-run mode" prose goes.

Also fix, per the premortem: guard the variable the `run:` actually consumes. The steps export
`CF_HOOK` at job level and pass the name `CF_DEPLOY_HOOK_URL` to the guard — assert `CF_HOOK`, or a
rename of the job-level alias would leave the curl unguarded while the guard still passes.

## F-85 — The lint instrument must prove it is armed. As drafted it CANNOT FAIL.

The single worst finding of this review, and it lands on the instrument **I** established in F-82.
Proven by execution:

```
actionlint.exe -shellcheck ./shellcheck.exe broken.yml   → 2 findings, exit 1
actionlint.exe -shellcheck "" broken.yml                 → 0 findings, exit 0
actionlint.exe -shellcheck "/nope/shellcheck.exe" broken.yml → 0 findings, exit 0
```

A missing or empty shellcheck path **silently disables shell linting and reports green**. The plans
resolve both binaries from a glob over a *session-scoped* temp directory
(`/c/Users/*/AppData/Local/Temp/claude/*/*/scratchpad/…`); the executor runs in a different session,
where that glob yields empty. The phase's only instrument for its own payload — which is entirely
bash — would then pass every gate with every line unlinted. That is the "gate that cannot fail"
class this run has found in every phase since 27, and this time it was hiding inside the
countermeasure.

Required, all three:
1. **Deterministic location, not the session scratchpad.** A `.github/scripts/fetch-lint-tools.sh`
   downloads `actionlint` v1.7.12 and `shellcheck` v0.11.0 into a gitignored `.tools/` at the repo
   root, **verifying the SHA-256 against the release checksums** and failing loudly otherwise. Add
   `.tools/` to `.gitignore`. Idempotent: skips the download when the binaries are already present
   and executable.
2. **Armed-check before every use:** `[ -x "$ACTIONLINT" ] && [ -x "$SHELLCHECK" ]`, else
   `::error::lint tooling not found` and exit 1 — an exit code and a message distinguishable from
   a lint finding. "Instrument absent" and "code bad" must never be the same signal.
3. **A canary that must fire.** Before linting the real workflows, run the lint command against a
   committed known-bad fixture (`.github/scripts/fixtures/canary-bad-workflow.yml`, containing an
   unquoted expansion) and assert it exits **non-zero**. If the canary passes, shellcheck is
   disabled and the gate aborts. Without this the whole apparatus is unproven.

## F-86 — The new pytest tests do not execute bash on this machine; 8 of them pass for the wrong reason

Proven by execution: `subprocess.run(["bash", ...])` from Python resolves to the WSL stub and
returns `rc=1` with **empty stdout** and a WSL relay error on stderr. Every "must exit 1" assertion
is therefore satisfied by a failure that never ran the script, and `test_never_prints_secret_value`
is vacuous against empty output — it would pass if the script printed the secret in full.

Required:
1. Resolve bash explicitly (`C:/Program Files/Git/bin/bash.exe` when present, else `/usr/bin/bash`,
   else `shutil.which`), never the bare name.
2. A **canary test** asserting the resolved bash actually works: `bash -c 'echo hello; exit 3'`
   must give `rc == 3` and `stdout.strip() == "hello"`. If that fails, every other test in the file
   is meaningless, and it should fail first and say so.
3. Every must-fail assertion asserts the expected **stdout/stderr substring** in addition to the
   exit code, so an empty-output failure cannot satisfy it.
4. `test_never_prints_secret_value` must be proven non-vacuous: assert the guard's success line IS
   present *and* the secret value is not — otherwise "output contains no secret" is satisfied by no
   output at all.

## F-87 — Do not let the alert step be the thing that fails, and create the labels BEFORE the workflows reference them

Two ordering/robustness defects:
- The plans create the labels in **Wave 3**, while **Wave 2** already commits workflows that
  reference them. Between those commits, a real failure produces `gh issue create --label <missing>`
  → the alert about the failure fails. Move label creation into **Wave 2**, before or with the
  workflow edits.
- `gh label create … --force` is the first command inside the `if: failure()` block, under
  `set -e` semantics: if it errors (rate limit, transient 5xx, permissions), the alert is lost
  silently — the one code path whose silent breakage is unrecoverable. Move it into its own
  preceding step with `if: failure()` **and** `continue-on-error: true`. That is a declarative,
  UI-visible allowance on a non-critical prep step, and it is explicitly NOT the banned `|| true`
  (which hides the status inside the same step's exit code).

## F-88 — A monitor must report every signal, not stop at the first

In the drafted `heartbeat.yml` the CEAD step never runs when the R2 step fails, so a maintainer
fixing R2 discovers CEAD only on the next day's run. Every check step gets `if: '!cancelled()'`
so all three always execute and the run log shows the complete picture; the alert step keeps
`if: failure()` and aggregates. Prove it: make two checks fail simultaneously in a scratch copy and
confirm both `::error::` lines appear in the same run.

## F-89 — `--status success` for the R2 evidence, and the remaining gap is named

`gh run list --workflow=r2-archive.yml` counts runs regardless of conclusion, so an archive that
fires daily and fails daily satisfies the heartbeat. Add `--status success`, then re-measure against
the live repo and confirm a timestamp still lands inside the 4-day window before relying on it.

**Named residual, not hidden:** a run that succeeds while archiving *zero* items still passes. F-79
chose this evidence source precisely to avoid a `data/` write, and that tradeoff is kept — but it
is stated, not implied away.

Second named residual: the heartbeat's dedup is `--state open`, so a maintainer who closes the issue
without fixing the cron gets a new issue the next day. That is intended (the system IS still
broken), and it must be written down, because on a DAILY cron it will look like spam to someone who
does not know it is by design.

## F-90 — CRON-06's success criterion is narrowed to what was actually proven

The premortem reproduced the race: the retry loop preserves both updates when the two writers touch
**disjoint paths**, which is the real news-vs-CEAD case. On a genuine **same-file** concurrent write
the rebase conflicts, and the loop aborts with `::error::` + exit 1 → the run's data is discarded and
an alert fires. That is correct behaviour and vastly better than today's unretried failure, but it
is not "no lost update" without qualification. The plan and DEPLOYMENT.md must claim exactly this
and no more: **no SILENT lost update; a same-file conflict fails loudly and is never resolved by
guessing.** ROADMAP SC-5's wording is read this way and the reading is recorded here.

## F-91 — Prose is not a gate. Move every close-bar claim into `<automated>`, and de-tautologize.

- The F-78 byte-identity check and the CRON-06 race proof live only in `<verification>` prose. F-78
  says in its own text that the identity must be asserted mechanically. Encode:
  `test "$(grep -h 'curl -X POST' <the three files> | sort -u | wc -l)" -eq 1`, and **prove it can
  fail** by flipping one file's `--retry 3` to `--retry 5`, observing exit 1, then restoring.
- Extract the push-retry loop into `.github/scripts/push-with-rebase.sh` so it is callable from
  pytest against two bare clones (F-81 requires the proof be encoded, not remembered). The workflows
  then call the script, which also removes the copy-paste duplication between news and cead.
- `32-03` Task 2's gate (`grep -c "Pipeline Heartbeat" DEPLOYMENT.md`) is tautological: the same task
  pastes that string. Replace it with an assertion the action did not literally write — iterate the
  real `.github/workflows/*.yml` directory and require every filename to appear in the table. Prove
  it fails by deleting a row.
- The phase-close bar (build+validate, vitest, pytest, actionlint, astro check) must be an
  `&&`-chained `<automated>` command, never `;`, never piped.

## Counting rule (applies to the pytest total)

The plan asserted "15 tests / 359 passed" while its own behaviour block named **17**, one of them a
duplicate (`test_require_env_all_blank` restates `test_fails_on_all_blank` — delete it). With F-83's
news cases and F-86's canary the count changes again. **Do not write a number before measuring it.**
Delete the duplicate, implement everything above, then run
`python -m pytest tests/test_workflow_guards.py -q`, and derive the suite total as
`344 + observed`. Baseline confirmed by execution today: `344 passed, 1 skipped, 1 xfailed`. The
skipped/xfailed counts stay exactly 1 and 1.

---

## F-92 — CORRECTION OF MY OWN F-82 record: the pinned actionlint is **v1.7.7**, and the "unverified assumption" framing is wrong in both directions

The revised plan pins actionlint **v1.7.7** and states that my cycle-0 figure of v1.7.12 was
"copied from an unverified assumption." Both halves of that need correcting, and I checked rather
than picked a side:

- My cycle-0 download WAS verified: the zip `actionlint_1.7.12_windows_amd64.zip` hashed to
  `6e7241b5…`, matching upstream `actionlint_1.7.12_checksums.txt` exactly. It was not an assumption.
- But the binary sitting at that path NOW self-reports `1.7.7 … built with go1.23.4`, not
  `1.7.12 … go1.26.1` as it did when I first ran it. The explanation is mundane and worth recording
  so nobody re-opens it as a supply-chain scare: the planner downloaded v1.7.7 into the **same
  shared scratchpad filename** while testing `fetch-lint-tools.sh`, overwriting my copy. Two agents,
  one scratchpad, same basename.
- What actually matters is the only thing that ships: the pins in `fetch-lint-tools.sh` match
  upstream **v1.7.7** byte for byte (`023070a2…` linux, `7f12f180…` windows, checked against
  `actionlint_1.7.7_checksums.txt` this session), and shellcheck's `8a4e35ab…` matches an artifact
  downloaded independently in an earlier session.

**Decision: keep v1.7.7.** It is the version the revision actually tested end to end, including the
tamper mutation, and "pin the version you tested" beats "pin the newest" — bumping to v1.7.12 would
re-open every proof for a version-currency gain that belongs to Phase 33's SHA-pinning scope, not
here. The plan's prose calling my figure unverified should be softened to the real story above;
leaving an inaccurate account of a checksum in a phase about self-diagnosing infrastructure is the
Operating-Lesson-25 trap (a correctness phase authoring its own drift).

**Operational note for any future phase:** two agents sharing one scratchpad with identical
basenames silently clobbered a verified binary. When a tool identity matters, verify it at the
point of use, not once at download — which is exactly what F-85's armed-check and canary now do.
