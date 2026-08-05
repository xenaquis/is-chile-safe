---
phase: 32-cron-consistency
verified: 2026-08-04T22:40:00Z
status: human_needed
score: 5/5 success criteria verified (7/7 CRON requirements satisfied)
overrides_applied: 1
overrides:
  - must_have: "Every workflow explicitly asserts each secret it consumes is non-empty before doing real work, and fails loudly (not a silent green no-op) when a secret is unset — verified by a deliberately-blanked-secret dry run."
    reason: "Directive gate amendment 2 / F-75..F-82: the LIVE blanked-secret dry run is deferred; satisfaction is by LOCAL SIMULATION of require-env.sh plus actionlint. Verifier independently executed the local simulation in both directions."
    accepted_by: "user (task directive)"
    accepted_at: "2026-08-04"
human_verification:
  - test: "Observe one real scheduled run of heartbeat.yml in the Actions UI (do not workflow_dispatch it; wait for 12:00 UTC)."
    expected: "The 'Check R2 archive heartbeat' step's `gh run list` call succeeds under GITHUB_TOKEN with `actions: read` and returns a timestamp, rather than 403-ing."
    why_human: "Verifier executed `gh run list` with a maintainer PAT, not the workflow's GITHUB_TOKEN. The permissions-block comment in heartbeat.yml states that an insufficient scope would 403 on the FIRST scheduled run and alert about a healthy R2 archive. This is the single load-bearing assumption in the phase that no local execution can settle."
  - test: "Deliberately blank CF_DEPLOY_HOOK_URL and run news-pipeline.yml via workflow_dispatch (DEPLOYMENT.md §8a procedure)."
    expected: "Data commit lands and is pushed; the job then hard-fails at 'Guard deploy hook' and opens a `pipeline-failure-news` issue."
    why_human: "Deferred live dry run (gate amendment 2). Requires mutating a repo secret and creating an issue — both outside this verification's read-only scope."
  - test: "Confirm the first alert path end-to-end: force any one guarded workflow red once and confirm the label is created and the issue filed with the per-pipeline label."
    expected: "`pipeline-failure-<name>` + `pipeline-failure` labels created; one issue opened; a second failure comments rather than duplicating."
    why_human: "Creating/modifying GitHub issues and labels is explicitly forbidden in this run. No label currently exists in the repo for heartbeat; creation is only exercised on a real failure."
  - test: "Observe the ci.yml `lint-workflows` job on an actual PR."
    expected: "fetch-lint-tools.sh installs the Linux binaries, the canary fires (SC2034 + SC2086), and the lint passes."
    why_human: "Verifier confirmed the pinned Linux SHA-256 checksums by downloading both artifacts (exact match), but ci.yml is pull_request-triggered only and no PR was opened."
  - test: "Next quarterly CEAD run (2026-10-01): confirm the failure is still an HTTP 403 and not a different error."
    expected: "Red run, 403, issue body pointing to the local-run runbook."
    why_human: "Requires the cron to fire from an Actions runner IP; cannot be reproduced locally."
---

# Phase 32: Cron Consistency Verification Report

**Phase Goal:** The entire GitHub Actions schedule surface (news, R2 archive, CEAD quarterly reminder, freshness guard) behaves as ONE coherent, self-diagnosing system — a silent stall or an empty-secret no-op is caught automatically.
**Verified:** 2026-08-04 (independent, goal-backward, execution-first)
**Status:** human_needed (all five criteria PASSED by local evidence; five items are only settleable on live GitHub infrastructure)
**Re-verification:** No — initial verification.

## The question that matters: if a cron stopped firing tomorrow, what goes red, how, and when?

Answered by simulation against the SHIPPED `check-heartbeat.sh`, feeding each mode
tripping evidence and legitimate evidence.

| Cron | What goes red | Mechanism (executed) | Detection latency |
|------|---------------|----------------------|-------------------|
| **News (every 6h)** | `heartbeat.yml` step "Check news pipeline heartbeat" fails → red run → `pipeline-failure-news`… no: `pipeline-failure-heartbeat` issue | `data/incidents/current.json`'s `generated` field vs 3-day threshold. Live evidence today = `2026-08-04T19:27:07Z` → **OK, 6h old**. Injected 4-day-old evidence → `::error::` exit 1. Injected exactly 3d → PASS; 3d+1s → FAIL. | **≤ 4 days** (3d threshold + ≤1d heartbeat cadence). Measured max historical gap between real `current.json` commits over the last 40 commits = **0.31 days**, so no false-positive headroom problem. |
| **R2 archive (daily 05:30 UTC)** | Same workflow, step "Check R2 archive heartbeat" | `gh run list --workflow=r2-archive.yml --status success` vs 4-day threshold. **Executed live against this repo**: returned `2026-08-04T07:58:30Z` → "r2 heartbeat OK: last evidence 18h old". Injected 5-day-old → exit 1. Empty result (workflow deleted/never ran) → exit 1. | **≤ 5 days.** |
| **CEAD (quarterly)** | Same workflow, step "Check CEAD reminder heartbeat" | Quarter-boundary counting on `git log -1 -- data/cead/`. Executed across a walk of as-of dates: ev=2026-05-15 → 0 boundaries (silent) at 06-30, **1** at 07-01/08-05/09-30 (silent, "maintainer running late"), **2 → red** at 10-01, 3 at 2027-01-01. Year-crossing case (ev 2025-11-01, as-of 2026-02-01) = 1, correct. Empty and >24h-future evidence both exit 1. | **~92 days — one full quarter.** This is the honest weak point (see F-98 below). |

Nothing here is "nothing goes red". All three trip, and all three stay silent on
legitimate evidence. The CEAD answer is materially slower than the other two and
is a design choice, not a defect — but it must be stated plainly rather than
folded into "all three covered".

## F-98 (BL-01 rejected) — re-derived independently

**I agree with the rejection, on the narrow point, and disagree with how reassuring it reads.**

The reviewer's premise — that a maintainer scraping *early* (2026-06-19) has their
one-boundary tolerance consumed by a due date their own scrape covered — is indeed
wrong: CEAD publishes ON the boundary, so a 06-19 scrape cannot contain 07-01 data.
Firing on 2026-10-01 is correct behaviour, and my own walk reproduces F-98's exact
three data points (`2026-08-04 → OK/1`, `2026-09-30 → OK/1`, `2026-10-01 → error/2`).

What F-98 records as "accepted as DESIGNED" deserves louder billing, because it is
the state the repo is in *right now*: the July 1 2026 CEAD release has already been
missed (last `data/cead/` evidence = `2026-06-19T17:24:23-04:00`), the guard is
**green today**, and it will stay green until **2026-10-01**. So the shipped system
detects the *second* consecutive missed quarter, not the first. Restated
generally: for any single missed CEAD release the alert arrives ~92 days late.
That is defensible for a manually-run quarterly scrape and is the price of never
crying wolf, but a reader of SC-2's phrase "a simulated stall on any one of them is
detected and surfaced" would not guess it. The DEPLOYMENT.md row does explain the
1-vs-2 boundary semantics; it does **not** state the resulting ~1-quarter latency
in days. That is the one place I'd ask for a sentence.

## Goal Achievement — Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Secret guards, fail loudly, no silent green no-op | ✓ PASSED (override on the *live* dry run) | `require-env.sh` executed: `CF_HOOK=""` → `::error::CF_HOOK is not set (empty string)`, exit 1; unset var → exit 1; present → exit 0; 3-var call with one blank names only the blank one; **secret value never printed** (grep for the value in the failure path = 0 hits). Guards present in `news-pipeline.yml` (OPENROUTER pre-scrape; CF_HOOK post-commit), `cead-scraper.yml` (CF_HOOK post-commit), `r2-archive.yml` (3 R2 vars), `deploy-on-code.yml` (CF_HOOK first-step). No `if: … && env.CF_HOOK != ''` silent-skip clause survives anywhere (grepped). |
| 2 | Heartbeat covers all three data crons, drift-tolerant, simulated stall surfaces | ✓ PASSED | See the table above — six tripping simulations and five silent-on-healthy simulations, plus **two live evidence collections** (`gh run list` for R2, `python3` read of `current.json` for news, `git log -- data/cead/` for CEAD) all executed end-to-end. `heartbeat.yml` runs on its own `0 12 * * *` schedule, outside the workflows it watches. Steps 2 and 3 carry `if: '!cancelled()'` so one failing check does not hide the others (F-88 — verified in the file). |
| 3 | Deploy-hook behaviour identical everywhere; per-pipeline labels | ✓ PASSED | `grep -o` across all workflows yields exactly **one** unique curl line (`cat -A`-confirmed byte-identical): `curl -X POST --fail --silent --show-error --retry 3 --retry-all-errors --max-time 60 "$CF_HOOK"` in `news-pipeline.yml:96`, `cead-scraper.yml:111`, `deploy-on-code.yml:62`. Labels: `pipeline-failure-news`, `-cead`, `-r2`, `-heartbeat`, each 3× (create + 2 issue refs), plus the shared `pipeline-failure` created in every alerting workflow (M-02). |
| 4 | CEAD expected-403 documented in the workflow file | ✓ PASSED | `cead-scraper.yml` lines 1–12 are a dedicated header comment naming the 403, the local-run runbook, and "NOT a regression". The failure-alert issue **body itself** repeats it, so a maintainer who only sees the issue (not the file) still gets the history. |
| 5 | Fetch+rebase before push, no lost update; one documented table | ✓ PASSED (as narrowed by F-90) | **Independently simulated with real bare git repos, not the project's tests.** Disjoint paths: A's push rejected → fetch → `git rebase FETCH_HEAD` → push succeeds; `origin` ends with **both** commits and all three files. Same file: rebase conflict → `::error::rebase conflict during data commit — aborting, a human must resolve` → exit 1, `origin` left exactly as the first writer left it (`B-version`), A's data discarded loudly. DEPLOYMENT.md's CRON-06 paragraph claims **precisely this and no more** ("no SILENT lost update… NOT a claim that no data is ever lost under any race") — checked word by word; no overclaim. CRON-07 table verified row by row (below). |

## Close Gate — independently re-measured

| Gate | Command | Result |
|------|---------|--------|
| Workflow lint | `bash .github/scripts/lint-workflows.sh` | ✓ exit 0, `canary fired correctly (SC2034 + SC2086 both present), instrument is armed` |
| Pipeline tests | `cd pipeline && python -m pytest tests/ -q` | ✓ **388 passed, 1 skipped, 1 xfailed** — exactly 1 and 1, as specified |
| Site build+validate (chained, OneDrive rule) | `npm run build && npm run validate` in one command | ✓ **16/16 validators passed** |
| Frontend unit | `cd site && npx vitest run` | ✓ **59 passed** (6 files) |
| Cron-specific tests | `pytest test_push_race.py test_workflow_guards.py test_workflow_order.py` | ✓ 50 passed |
| Pinned tool integrity (extra) | Downloaded both **Linux** artifacts and hashed them | ✓ actionlint `023070a2…0757` and shellcheck `8c3be12b…7198` match `fetch-lint-tools.sh` byte for byte — the CI job will install a genuine linter |

## DEPLOYMENT.md cadence table — fact-checked against the workflow files

| Claim | Verdict |
|-------|---------|
| News: `0 */6 * * *`, schedule+dispatch, OPENROUTER guarded / DEEPSEEK not guarded / CF_HOOK guarded post-commit, `contents: write` + `issues: write`, writes `data/` + push + hook | ✓ all correct |
| R2: `30 5 * * *`, 3 R2 secrets guarded, **not** R2_BUCKET, `contents: read` + `issues: write`, "R2 bucket only — no `data/` write, no push" | ✓ correct. `archive_r2.py` `required_vars` = exactly those 3; `bucket = os.environ.get("R2_BUCKET","").strip() or "ischilesafe"` confirmed; no `data/` write in the workflow |
| CEAD: `0 3 1 1,4,7,10 *`, CF_HOOK guarded post-commit, `contents: write` + `issues: write`, 403-expected, setup-python + pip restored (H-02) | ✓ correct — `actions/setup-python@v7` and `pip install -r pipeline/requirements.txt` are both present |
| Heartbeat: `0 12 * * *`, no secrets, `actions: read` + `contents: read` + `issues: write`, writes nothing | ✓ correct |
| Deploy on code push: `push` on `site/**` + own workflow file, CF_HOOK first-step, `contents: read`, no failure alert | ✓ correct |
| CI: `pull_request` + `workflow_dispatch`, explicit `permissions: contents: read` at **`ci.yml:8-9`** | ✓ correct — lines 8 and 9 exactly |
| `freshness.mjs` is validator **#15** | ✓ correct — validate output order confirms position 15 of 16 |
| `fetch-lint-tools.sh:42` is the idempotency short-circuit | ✓ correct — line 42 is `if [ -x "$ACTIONLINT_BIN" ] && [ -x "$SHELLCHECK_BIN" ]` |
| §6 "no `R2_BUCKET` secret needed", §8a "no silent-skip dry-run mode" | ✓ both consistent with shipped code |
| CRON-07 clustering note ("Phase 26 NO-GO, no clustering wired into news-pipeline") | ✓ `news-pipeline.yml` runs one `python pipeline/scrape_news.py`, `timeout-minutes: 30` — matches |

**No false statement found in the new DEPLOYMENT.md prose.** Given that wrong new
prose was this run's most-repeated defect, this was checked line by line rather than sampled.

## Scope fence

| Fence | Result |
|-------|--------|
| `permissions:` edits beyond heartbeat.yml's own new block | ✓ CLEAN — `git diff cde5a96..HEAD -- .github/workflows` shows exactly one added `permissions:` block, heartbeat.yml's (`actions/contents/issues`). No other permissions lines added or removed. |
| SHA-pinning (Phase 33) | ✓ none — zero `uses: …@<40-hex>` in any workflow |
| dependabot / zizmor (Phase 33) | ✓ neither file nor reference introduced |
| `data/` generated-artifact writes | ✓ none — `git diff --name-only cde5a96..HEAD -- data/` is empty |
| `workflow_dispatch` triggered during verification | ✓ none triggered; no issues/labels created; no push |
| Working tree after verification | ✓ `git status --short` empty. Race simulation ran entirely in the scratchpad against throwaway bare repos; no repo file was mutated. |

Phase footprint (excluding `.planning`): 6 scripts + 1 fixture, 6 workflows, `.gitignore` (+`.tools/`), `DEPLOYMENT.md`, 2 new test files. 1657 insertions / 66 deletions. Nothing outside the fence.

## Requirements Coverage

| Req | Status | Evidence |
|-----|--------|----------|
| CRON-01 | ✓ SATISFIED (live dry run deferred by amendment) | require-env.sh executed both directions; wired into all four secret-consuming workflows; no secret value leaked |
| CRON-02 | ✓ SATISFIED | three modes, six trip simulations + live evidence collection for all three; residual (heartbeat's own silence) documented in both `heartbeat.yml` and DEPLOYMENT.md — the docs do **not** imply full coverage |
| CRON-03 | ✓ SATISFIED | one byte-identical curl line, three call sites |
| CRON-04 | ✓ SATISFIED | four per-pipeline labels + shared label created in every alerting workflow |
| CRON-05 | ✓ SATISFIED | file header + issue body |
| CRON-06 | ✓ SATISFIED as narrowed (F-90) | independent two-direction bare-repo simulation |
| CRON-07 | ✓ SATISFIED | table fact-checked row by row against the files |

## Anti-patterns / carried debt

| Item | Severity | Note |
|------|----------|------|
| **Whitespace-only secret defeats the guard.** `require-env.sh` tests `[ -z "$v" ]`, so `R2_ACCESS_KEY_ID="   "` **passes** the guard (verified: exit 0). `archive_r2.py` then `.strip()`s it, treats it as missing, logs a warning and `return 0` → **green job, nothing archived**. The heartbeat's R2 check uses `--status success`, so it stays green too. This is a surviving end-to-end instance of the exact silent-green-no-op class CRON-01 exists to abolish, inside the instrument built to abolish it. | ⚠️ WARNING (new, undocumented) | Low likelihood (requires a whitespace-padded secret) but a one-word fix (`${!v// /}` or a `.strip()`-equivalent test). Not documented in F-89's residual list, which only covers "succeeds while archiving zero items". |
| CEAD single-missed-quarter latency ≈ 92 days; the guard detects only the second consecutive miss, and is green today over an already-missed 2026-07-01 release | ⚠️ WARNING (documented in mechanism, not in days) | Design per F-93/F-98; recommend one sentence in the DEPLOYMENT.md heartbeat row stating the latency in days |
| `heartbeat.yml`'s own silence unmonitored | ℹ️ documented residual (F-79) | Stated in the file and in DEPLOYMENT.md; closing it needs an external monitor (~$0 constraint) |
| R2 run that succeeds archiving zero items still passes | ℹ️ documented residual (F-89) | Stated |
| Daily re-issue after closing an alert without fixing | ℹ️ documented residual (F-89) | Stated, intended |
| H-05: maintainer-pushed CEAD data never triggers a production build | ℹ️ documented backlog | Real pre-existing gap, out of scope, in STATE.md |
| M-07: four `continue-on-error` steps in cead-scraper can commit partial data green | ℹ️ documented backlog | Masked today by the 403 |
| M-08: `fetch-lint-tools.sh` doesn't re-hash an already-present binary | ℹ️ documented, accepted | Canary mitigates |
| Master pushes are not linted by CI (F-95 rejected a `push:` trigger) | ℹ️ documented | Mitigation is "run the gate locally" — an unenforceable, human-memory control. Real but consciously chosen. |

No `TBD`/`FIXME`/`XXX` markers in any file this phase touched.

## What this phase claims that I could NOT verify, and why

1. **That `heartbeat.yml` works at all when GitHub actually runs it.** Every check
   was executed with my shell and, for R2, a maintainer-authenticated `gh`. I never
   ran it under `GITHUB_TOKEN` with `permissions: actions: read`. The workflow's own
   comment says an insufficient scope 403s on the first scheduled run and alerts about
   a healthy archive. **This is the highest-value unverified item in the phase** — the
   entire CRON-02 claim rests on a permissions scope that has never executed.
2. **The alert path has never fired.** No `pipeline-failure-*` issue or label has been
   created by this system. `gh issue create` fails outright if a label is missing; the
   label-creation step is `continue-on-error: true` and precedes it, which is the right
   shape, but the shape is untested against the live API. Forbidden to test here.
3. **The blanked-secret LIVE dry run** (SC-1's literal wording) — deferred by gate
   amendment 2, correctly on the deferred-live list rather than counted as a failure.
4. **That CI's `lint-workflows` job passes on ubuntu-latest.** I proved the pinned
   Linux binaries are authentic (exact SHA-256 match on both) — a stronger check than
   most — but `ci.yml` is PR-triggered and no PR exists, so the job has never run.
5. **That the CEAD cron still 403s.** Unexecutable locally. If CEAD ever unblocks
   Actions IPs, the M-07 `continue-on-error` chain becomes live and can push partial
   data with a green job — a documented, currently-masked defect that would silently unmask.
6. **`push-with-rebase.sh` under real GitHub concurrency.** My simulation used local
   bare repos with deterministic ordering. Real contention (two runners, remote
   ref-update races, GitHub's own push rejections) was not reproduced. The disjoint-path
   case is the realistic one and it works; the same-file case is the documented loud abort.
7. **The 5-attempt retry budget in anger.** I verified the loop's shape and the L-02/WR-08
   fixes by reading and by one rejection cycle; I did not force 5 consecutive rejections.

## Gaps Summary

No blocker. All five ROADMAP success criteria and all seven CRON requirements are
satisfied in the shipped code, verified by execution rather than by reading the
SUMMARYs. The phase goal — a self-diagnosing schedule surface — is achieved for
news (≤4 days to red) and R2 (≤5 days), and achieved at quarter granularity
(~92 days, second-miss detection) for CEAD.

Two things keep this from a clean `passed`: a set of claims that only live
GitHub infrastructure can settle (chiefly whether the heartbeat's `actions: read`
scope actually permits its own `gh run list`), and one new, undocumented
residual — a whitespace-only secret slips through `require-env.sh` and lands in
`archive_r2.py`'s silent `return 0`, reproducing the phase's own target defect
inside the phase's own guard.

---

_Verified: 2026-08-04_
_Verifier: Claude (gsd-verifier), goal-backward, execution-first_
