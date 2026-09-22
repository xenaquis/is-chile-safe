---
phase: 32-cron-consistency
reviewed: 2026-08-04T00:00:00Z
depth: deep
diff_base: cde5a96
files_reviewed: 13
files_reviewed_list:
  - .github/scripts/require-env.sh
  - .github/scripts/check-heartbeat.sh
  - .github/scripts/push-with-rebase.sh
  - .github/scripts/fetch-lint-tools.sh
  - .github/scripts/lint-workflows.sh
  - .github/scripts/fixtures/canary-bad-workflow.yml
  - .github/workflows/heartbeat.yml
  - .github/workflows/news-pipeline.yml
  - .github/workflows/cead-scraper.yml
  - .github/workflows/r2-archive.yml
  - .github/workflows/deploy-on-code.yml
  - pipeline/tests/test_workflow_guards.py
  - pipeline/tests/test_push_race.py
  - DEPLOYMENT.md
  - .gitignore
findings:
  critical: 5
  warning: 9
  info: 7
  total: 21
status: issues_found
---

# Phase 32 "Cron Consistency" — Adversarial Code Review

**Reviewed:** 2026-08-04 · **Depth:** deep (execution-based) · **Base:** `cde5a96..HEAD`
**Status:** issues_found — **5 HIGH**, 9 MEDIUM, 7 LOW

Everything below was reached by **running** the artifact, not by reading it. Repo left
clean: every mutation was reverted and `git status --porcelain` is empty at the end of
this review (verified).

---

## Summary

The instrument-quality work is real: `lint-workflows.sh`'s canary is genuinely
un-foolable, `shellcheck` is clean on all five shipped scripts, and **every** pytest
assertion I mutated went RED. But three of the phase's five touched workflows have
live-production defects that execution surfaces immediately, and the two headline
artifacts — the lint gate and the CEAD reminder — are respectively **never invoked**
and **structurally unable to produce the outcome its own alert text describes**.

The single most urgent item is HIGH-1: the R2 archive, which is LIVE today, will
hard-fail on its next scheduled run (05:30 UTC) because Phase 32 added a required-secret
guard for a variable that is not a secret and never was.

---

## HIGH

### H-01 · `r2-archive.yml` guards `R2_BUCKET`, which is not a secret — the daily archive stops tomorrow

**File:** `.github/workflows/r2-archive.yml:29-35`
**Class:** a gate that cannot pass on a correct tree.

`require-env.sh R2_ENDPOINT_URL R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET`.

Live repo configuration (`gh secret list`, `gh variable list`, environments — all read-only):

```
CF_DEPLOY_HOOK_URL, DEEPSEEK_API_KEY, OPENROUTER_API_KEY,
R2_ACCESS_KEY_ID, R2_ENDPOINT_URL, R2_SECRET_ACCESS_KEY, TOKEN_VALUE_R2
```

There is **no `R2_BUCKET` secret, no repo variable, and no environment**. And that is
deliberate — `pipeline/archive_r2.py:475` reads:

```python
# `or` fallback: GitHub Actions injects unset secrets as empty strings, so a
# plain .get() default never kicks in and boto3 gets Bucket="" (run 30208466155).
bucket = os.environ.get("R2_BUCKET", "").strip() or "ischilesafe"
```

`archive_r2.py:458` lists only **three** required vars; `R2_BUCKET` is optional with a
hard-coded default. Phase 32 promoted an optional var to a hard requirement.

**Executed proof** (the guard step verbatim, with the live env shape):

```
$ env -u R2_BUCKET R2_ENDPOINT_URL=https://x R2_ACCESS_KEY_ID=k R2_SECRET_ACCESS_KEY=s \
    bash .github/scripts/require-env.sh R2_ENDPOINT_URL R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET
::error::R2_BUCKET is not set (empty string) — refusing to proceed
GUARD_RC=1
```

**Failure scenario:** at 05:30 UTC the guard exits 1 on step 2 of 5. `archive_r2.py`
never runs. The R2 research corpus stops accruing and a `pipeline-failure-r2` issue is
opened, then commented on **daily, forever**, with a cause that is not a real outage.
Five days later `heartbeat.yml`'s R2 check also starts firing (no successful run in
> 4 days), so the operator gets two daily alert streams for a non-problem — the classic
route to alert fatigue that then masks a real outage.

**Remedy:** drop `R2_BUCKET` from the guard list (`r2-archive.yml:35`), matching
`archive_r2.py`'s own `required_vars`. If a non-default bucket is genuinely wanted, set
it as a repo **variable** and pass `R2_BUCKET: ${{ vars.R2_BUCKET }}` — but the guard
must still not require it, because the code has a documented default.

**How the fix is proven:** re-run the exact command above with the corrected argument
list and assert RC=0; and add a pytest case that reads `required_vars` out of
`pipeline/archive_r2.py` and asserts the workflow's `require-env.sh` argument list is
**equal** to it (not a superset) — that ties the two together so the drift cannot recur.

---

### H-02 · `cead-scraper.yml` lost its Python setup in the rewrite — the "expected 403" reminder can no longer produce a 403

**File:** `.github/workflows/cead-scraper.yml:42-72` (removed at `git diff cde5a96..HEAD`)

The rewrite deleted two steps that were present at the base commit:

```diff
       - uses: actions/checkout@v7
-
-      - uses: actions/setup-python@v7
         with:
-          python-version: '3.12'
-
-      - name: Install pipeline deps
-        run: pip install -r pipeline/requirements.txt
+          fetch-depth: 0
```

The `with:` block was re-targeted onto `checkout` (to add `fetch-depth: 0`) and the
`setup-python` + `pip install` steps went with it. The shipped file now runs
`python pipeline/scrape_cead.py` (line 54) with no interpreter pin and **no
`requests`/`bs4`/`lxml` installed**, and the same for
`fetch_enusc_vhdv.py`, `build_enusc_enrichment.py`, `build_composite_index.py`,
`build_map_payload.py` (lines 56-72).

`news-pipeline.yml:47-52` and `r2-archive.yml:37-42` both still have their
`setup-python` + `pip install` pair — this is an isolated regression in one file.

**Failure scenario:** on 2026-10-01 the quarterly reminder fires and dies with
`ModuleNotFoundError`, not HTTP 403. The file header (lines 3-12) and the alert issue
body (line 121) both tell the maintainer:

> "This is the expected quarterly reminder **if the failure is an HTTP 403** … **If the
> failure is NOT a 403, this is a real regression**"

So the phase's own alert text will now instruct the maintainer that a defect Phase 32
introduced is a real regression — while the actual signal (does CEAD still 403 Actions
IPs? has the endpoint's schema changed?) is destroyed, because the scraper never gets far
enough to make a request. `workflow_dispatch` on this workflow is equally broken.

**Remedy:** restore, between the checkout and `Run CEAD scraper`:

```yaml
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'

      - name: Install pipeline deps
        run: pip install -r pipeline/requirements.txt
```

**How the fix is proven:** not by reading the YAML back. Add a pytest that parses every
workflow under `.github/workflows/` and asserts: *any job containing a `run:` step whose
command starts with `python ` must also contain an `actions/setup-python` step and a
`pip install -r` step earlier in its step list.* Mutate by deleting `setup-python` from
`news-pipeline.yml` and confirm RED. That converts a one-off restore into a class-level
guard, which is what this phase is nominally about.

---

### H-03 · `lint-workflows.sh` — the phase's flagship instrument — has zero callers

**Files:** `.github/scripts/lint-workflows.sh`, `.github/scripts/fetch-lint-tools.sh`,
`.github/workflows/ci.yml:50-57`

Repo-wide search for invocations (excluding `.planning/`):

```
./.github/scripts/lint-workflows.sh:6:  bash "$ROOT/.github/scripts/fetch-lint-tools.sh"   <- self
(nothing else)
```

`ci.yml` has a job *named* `lint-workflows`, but it is a name collision — it runs
`uses: rhysd/actionlint@v1`, not the shipped script. So:

1. The hardened, canary-armed, SHA-pinned, shellcheck-verified instrument that F-85
   exists to build is **dead code**, runnable only by a human who knows to type it.
2. The gate that *does* run is `rhysd/actionlint@v1` — the exact wrapper whose
   shellcheck-wiring the phase's own decision record says silently disables shell
   linting when misconfigured. The phase built the fix and left the defect wired in.
3. `ci.yml` triggers on `pull_request` + `workflow_dispatch` only. This repo's own
   history (`git log`) is direct commits to `master`. **No workflow YAML change in this
   phase's diff was linted by CI at all**, because none of it went through a PR.

Also: `.github/scripts/*.sh` are invoked as `run: bash .github/scripts/…`, so actionlint
never sees them either — actionlint only lints inline `run:` bodies. I ran shellcheck on
them by hand (see "Verified clean") because nothing in CI does.

**Remedy:** replace `ci.yml:57` with `run: bash .github/scripts/lint-workflows.sh` plus a
second line `run: .tools/shellcheck -s bash .github/scripts/*.sh`, and add a `push:`
trigger for `branches: [master]` restricted to `paths: ['.github/**']` so master-direct
workflow edits are linted.

**How the fix is proven:** push a branch containing the H-02 defect shape (a workflow
with an unquoted `$VAR` in `run:`) and confirm the CI job goes red; then confirm the same
branch with the defect removed goes green. A green run on a tree that was never linted is
the failure mode being closed, so the *red* half is the load-bearing half of that proof.

---

### H-04 · `DEPLOYMENT.md` now documents the deleted behaviour as current, in three places

**File:** `DEPLOYMENT.md:23-24`, `DEPLOYMENT.md:122-124`, `DEPLOYMENT.md:153-163`

Phase 32 deleted `if: … && env.CF_HOOK != ''` from all three deploy-hook workflows and
replaced it with a hard `require-env.sh CF_HOOK` failure. It updated §10 and left the
rest of the document asserting the opposite:

- `:23-24` (architecture diagram): `|-- if changed == true AND CF_DEPLOY_HOOK_URL is set`
- `:122-124`: *"**Without `CF_DEPLOY_HOOK_URL`:** The `curl` step in both cron workflows
  is **skipped silently** (guarded by `env.CF_HOOK != ''`). … This is the dry-run mode —
  safe to use before the CF project exists."*
- `:161`: *"Skip the `curl` step because `env.CF_HOOK` is empty."* under the heading
  **"8a. Dry-run (before setting CF_DEPLOY_HOOK_URL)"*, presented as the documented
  first-run onboarding procedure.

A new maintainer following §8a today gets a **red job and a GitHub issue**, having been
told by the same document that this is the safe, expected path. `DEPLOYMENT.md:227`
simultaneously states the new behaviour. The document contradicts itself.

Compounding it, **§6's secrets table (`:117-120`) lists only two secrets** —
`CF_DEPLOY_HOOK_URL` and `DEEPSEEK_API_KEY`. Phase 32 made `OPENROUTER_API_KEY`
(news-pipeline.yml:45) and four `R2_*` vars (r2-archive.yml:35) **hard** requirements.
A setup done from §6 alone now fails the news cron on step 2 of 7. §10's own new table
claims all of these are "hard-guarded, CRON-01" — so §6 and §10 disagree about which
secrets exist.

**Remedy:** rewrite `:122-124` and §8a to describe hard failure; delete the "dry-run
mode" framing entirely (it no longer exists — the replacement dry-run is
`workflow_dispatch` with all secrets set); fix the `:23` diagram to
`if changed == true` and add a separate `Guard deploy hook (always)` node; extend §6's
table to all seven consumed secrets.

**How the fix is proven:** grep the whole of `DEPLOYMENT.md` for `CF_HOOK != ''`,
`skipped silently`, and `dry-run` and assert zero matches; then add a doc test that
extracts every `secrets.X` reference from `.github/workflows/*.yml` and asserts each
appears in §6's table. Prose defects recur precisely because they are checked by reading.

---

### H-05 · New CEAD data pushed by a maintainer never reaches production

**Files:** `.github/workflows/deploy-on-code.yml:27-32`, `.github/workflows/cead-scraper.yml:93-98`

Cloudflare auto-build is disabled, so the deploy hook is the sole production trigger.
Trace every path by which new CEAD data can land on `master`:

| Path | Deploy fires? |
|---|---|
| news cron, data changed | yes — `news-pipeline.yml:86-88` |
| news cron, data unchanged | no (correct) |
| news cron, hook empty | job red + issue, data preserved — **F-84 satisfied, verified** |
| news cron, push rebase-conflicts | no (correct: commit never reached origin) |
| `cead-scraper.yml` on Actions | **never** — the scrape 403s (and now, per H-02, ImportErrors) at step 2, so `Guard deploy hook` and `Trigger deploy` at lines 93-98 are unreachable in production |
| **maintainer's local quarterly scrape → `git push` of `data/cead/`** | **no** |

That last row is *the documented real CEAD process* (`cead-scraper-quarterly-local`
memory; `cead-scraper.yml:6-8`). `deploy-on-code.yml:30-32` filters on
`site/**` and `.github/workflows/deploy-on-code.yml` — `data/**` matches neither. So the
quarterly CEAD refresh sits on `master` and production keeps serving the previous
quarter's numbers until the next unrelated `site/**` push happens to rebuild.
`DEPLOYMENT.md:220` nonetheless lists "triggers CF deploy hook" as a thing the CEAD
Scraper does.

Note the boundary carefully: `data/**` cannot simply be added to `deploy-on-code.yml`'s
paths — that would reintroduce the rebuild loop the file's header (lines 5-7) exists to
prevent, since the news cron writes `data/` every 6h. (`[skip ci]` is a commit-message
convention GitHub honours for `push` triggers, but relying on it here would make the
loop-prevention depend on a commit message, which is worse.)

**Remedy (two viable shapes, pick one and state it in `DEPLOYMENT.md`):**
(a) add a `Trigger production deploy` step to the *documented local runbook* — an
explicit `curl -X POST "$CF_DEPLOY_HOOK_URL"` the maintainer runs after pushing; or
(b) add a `workflow_dispatch`-only `deploy.yml` whose single job is the canonical curl,
and document "run this after a manual data push".
(b) is preferable — it keeps the hook URL out of a human's shell history.

**How the fix is proven:** simulate the maintainer path end to end on a scratch branch —
commit a `data/cead/` change, push, and assert (via `gh run list`) that a deploy-firing
run exists. Under (a), assert the runbook step is present and that `DEPLOYMENT.md`'s
CEAD row no longer claims the workflow triggers the hook.

---

## MEDIUM

### M-01 · `news-pipeline.yml` hard-guards `DEEPSEEK_API_KEY`, which the default provider does not consume
**File:** `.github/workflows/news-pipeline.yml:41-45`
`scrape_news.py:177-182` selects the key by provider, defaulting to `openrouter` →
`OPENROUTER_API_KEY`. `DEEPSEEK_API_KEY` is consumed only when `NEWS_PROVIDER=deepseek`,
which nothing sets. The guard makes a dead secret load-bearing: the day someone tidies up
the unused DeepSeek secret, the 6-hourly news cron hard-fails four times a day for a key
no code path reads. **Remedy:** guard `OPENROUTER_API_KEY` only, or make the guard
provider-aware by reusing the same mapping. **Proof:** run the job with
`DEEPSEEK_API_KEY` unset and assert green + a normal news commit.

### M-02 · The alert path can still lose the first alert — `pipeline-failure` is never created
**Files:** all four `Ensure alert label exists` steps (e.g. `news-pipeline.yml:97-102`,
`heartbeat.yml:73-78`)
The `continue-on-error` prep step creates only the **per-pipeline** label
(`pipeline-failure-news`, …). The alert step then passes **two** labels to
`gh issue create` (`news-pipeline.yml:115-116`): the per-pipeline one *and* the shared
`pipeline-failure`. `gh issue create` fails outright if any `--label` does not exist. So
F-87's hole is only half closed: if `pipeline-failure` is ever deleted or renamed, every
pipeline's *first* alert issue creation fails and the alert about the original failure is
lost — the exact unrecoverable mode F-87 names. (All five labels exist today —
verified via `gh label list` — so this is latent, not live.) **Remedy:** add
`gh label create pipeline-failure … --force` to the same prep step.
**Proof:** delete the label on a scratch repo, trip a failure, assert an issue appears.

### M-03 · The CEAD heartbeat is currently green on a quarter that has already been missed
**File:** `.github/workflows/heartbeat.yml:59-63`
Threshold is 150 days against a 91-day cadence. Measured today:
`git log -1 --format=%cI -- data/cead/` → `2026-06-19`, **46 days ago**. The 2026-07-01
quarterly reminder fired 34 days ago and no `data/cead/` commit followed — i.e. a
quarter has already been skipped — and the check reports
`cead heartbeat OK: last evidence 46d old`. It will not fire until **2026-11-16**, six
weeks into the *following* quarter. A guard whose threshold exceeds 1.5× the cadence it
watches cannot detect a single missed cycle; it only detects two.
**Remedy:** threshold 100 days. **Proof:** `check-heartbeat.sh cead 100 <101d-ago>` → 1
and `<99d-ago>` → 0, plus a pytest boundary pair (the existing 150/151 pair, retargeted).

### M-04 · Integer-day truncation makes every stated threshold one day looser than advertised
**File:** `.github/scripts/check-heartbeat.sh:47-49`
`age_days=$(( (now - ts) / 86400 ))` then `-gt "$max_age_days"`. With `max=3`, an
entry 3 days 23 h 59 m old yields `age_days=3` and passes. Combined with the daily
12:00 UTC schedule, a dead 6-hourly news cron is detected **4 to 5 days** later — 16 to
20 missed runs. Step names (`heartbeat.yml:65` "3-day threshold"), the script header, and
`DEPLOYMENT.md:221` all say "3 days". `freshness.mjs:78` by contrast uses float days, so
the two instruments the header claims "cannot disagree" **do** disagree by up to 24 h.
**Remedy:** compare seconds — `max_age_s=$(( max_age_days * 86400 ))`, `[ $((now-ts)) -gt
$max_age_s ]`; keep reporting whole days for humans. **Proof:** a pytest asserting
`check-heartbeat.sh news 3 <3d-and-1h-ago>` exits 1 — mutate to the current integer form
and confirm RED (today it exits 0).

### M-05 · `r2-archive.yml`'s justification comment states a falsehood about the code it guards
**File:** `.github/workflows/r2-archive.yml:26-28`
> "Today an empty credential reaches boto3 and raises a generic exception deep inside
> `pipeline/archive_r2.py` (RESEARCH.md) — **that already alerts**, but with no named cause."

`archive_r2.py:458-467` does the opposite: missing/blank required vars are logged as a
warning and the function `return 0`s — a clean exit, no exception, **no alert**. The
guard's real value is larger than the comment claims (it converts a silent no-op into a
failure), and the stated baseline is wrong. **Remedy:** correct the comment to
"…returns 0 and the run reports green — a silent no-op". **Proof:** run
`R2_ENDPOINT_URL= python pipeline/archive_r2.py; echo $?` → 0.

### M-06 · `deploy-on-code.yml` is the only touched workflow with no failure alert
**File:** `.github/workflows/deploy-on-code.yml:34-62`
Its own header (lines 12-20) calls it "the SOLE production build trigger for code pushes"
and "the highest-severity instance" of the silent-no-op class. The other four workflows
all got a two-step label+issue alert path in this phase; this one got none. A red X on a
push run is visible only to whoever happens to look, and email notification depends on
per-user settings. **Remedy:** add the same
`Ensure alert label exists` + `Alert via GitHub Issue on failure` pair with
`pipeline-failure-deploy`, and add `issues: write` to `permissions` (currently
`contents: read` only, so the alert would 403 if added without it — check that too).
**Proof:** dispatch with a deliberately blank hook on a scratch branch and assert an
issue is created.

### M-07 · Four `continue-on-error: true` build steps can commit, push and deploy partial data with a green job
**File:** `.github/workflows/cead-scraper.yml:56-72`
`fetch_enusc_vhdv.py`, `build_enusc_enrichment.py`, `build_composite_index.py`,
`build_map_payload.py` all swallow their exit codes. If `build_map_payload.py` crashes
halfway, the `Commit data if changed` step (line 74) still stages whatever `data/`
contains, pushes it to `master`, and the deploy hook fires — shipping a truncated map
payload to production with a green checkmark. This is the CRON-01 silent-no-op class,
inside a file this phase rewrote, untouched. (Masked in practice today by H-02/CRON-05,
which is not a defence.) **Remedy:** drop `continue-on-error` from
`build_composite_index.py` and `build_map_payload.py` (both feed the production map); if
the ENUSC steps must stay best-effort, have them write a sentinel the commit step checks.
**Proof:** run the workflow with `build_map_payload.py` stubbed to `sys.exit(1)` and
assert the job goes red and no commit is pushed.

### M-08 · `fetch-lint-tools.sh` never re-verifies an already-present binary against its pinned SHA
**File:** `.github/scripts/fetch-lint-tools.sh:42-47`
The idempotency short-circuit is `[ -x "$ACTIONLINT_BIN" ] && [ -x "$SHELLCHECK_BIN" ]` —
executability only. Once `.tools/` exists (it is gitignored and persists across sessions
on a dev machine), the pinned SHA-256 is never checked again. The local `.tools/` I found
dates to Jan 2025 / Aug 2025, i.e. it predates this phase and was never verified by this
script. A stale, wrong-version, or tampered binary is trusted indefinitely, and
`lint-workflows.sh`'s canary would only catch it if the tampering also broke SC2034/SC2086
reporting. **Remedy:** move the `verify_sha256` calls above the short-circuit and run them
on the installed binaries, not only on the freshly downloaded archives.
**Proof:** `printf x >> .tools/shellcheck` and assert `fetch-lint-tools.sh` exits 1;
restore.

### M-09 · `DEPLOYMENT.md` CI row is factually wrong and incomplete
**File:** `DEPLOYMENT.md:223`
States `contents: read` **"(repo default; no per-job override)"**. `ci.yml:8-9` has an
explicit *workflow-level* `permissions: contents: read` block — not the repo default. The
row also omits `ci.yml`'s third job, `lint-workflows` (`ci.yml:50-57`), in a table whose
heading claims to be a six-workflow **audit**. **Remedy:** "explicit workflow-level
`permissions: contents: read`"; list all three jobs. **Proof:** the doc-test proposed in
H-04 should also assert every `jobs:` key in every workflow is named in the table.

---

## LOW

- **L-01** `lint-workflows.sh:35` — default glob is `.github/workflows/*.yml`; a workflow
  named `.yaml` (GitHub accepts both) is silently skipped by the very gate meant to be
  un-skippable. Use `.github/workflows/*.yml .github/workflows/*.yaml` with `nullglob`,
  or hand actionlint the directory. Proof: add a `.yaml` fixture with a known finding and
  assert the default-glob invocation exits 1.
- **L-02** `push-with-rebase.sh:24` — `sleep $((i*3))` sits *between* the rebase and the
  retry push, widening the window for origin to move again, and on the final iteration it
  sleeps 15 s after a rebase that will never be pushed. Move the sleep to the top of the
  loop body and skip it on the last attempt.
- **L-03** `push-with-rebase.sh:20-22` — if `git rebase` fails *without starting* (dirty
  tree, unborn upstream), `git rebase --abort` errors and `set -e` exits 128, not the
  intended 1. The `::error::` line is emitted first so the alert survives, but
  `test_push_race.py:138` asserts `returncode == 1` and would not cover this path. Guard
  with `git rebase --abort || true` *after* the echo, then `exit 1`.
- **L-04** `push-with-rebase.sh:18-19` — relies on `git fetch origin <branch>`
  opportunistically updating `refs/remotes/origin/<branch>` before `git rebase
  origin/<branch>`. I verified this works in the test topology (mutation M8: removing the
  fetch turns both `test_push_race.py` tests RED), and `actions/checkout` configures a
  covering refspec, so this is **not** currently broken. It is still a load-bearing
  implicit behaviour; `git fetch origin "$branch" && git rebase FETCH_HEAD` is
  unambiguous under any refspec configuration.
- **L-05** `pipeline/tests/test_push_race.py:28-43` — duplicates `_find_bash()` from
  `test_workflow_guards.py:29-49` but ships **no F-86 canary test**. Its assertions
  happen to be non-vacuous (they require substrings in stdout, which the WSL stub cannot
  produce), so this is currently safe — but the safety is accidental. Extract
  `_find_bash` + the canary into a shared `conftest.py`.
- **L-06** `test_workflow_guards.py:144-154` (`test_never_prints_secret_value`) only
  covers the **success** path. Mutation M5 — adding `echo "${!v}"` to `require-env.sh`'s
  *error* branch — **survived the suite**. `require-env.sh:16` is correct today, but the
  test named "never prints secret value" does not cover the branch where a leak is most
  likely. Add the mirror case with a blank-adjacent secret.
- **L-07** `DEPLOYMENT.md:222` — the Deploy on Code Push row says "touching `site/**`";
  `deploy-on-code.yml:30-32` also triggers on `.github/workflows/deploy-on-code.yml`.
  Minor, but the row sits in a table whose stated purpose is an exact audit.
- **L-08** `import pytest` is unused in both `test_workflow_guards.py:21` and
  `test_push_race.py:22`.

---

## Where I looked and found nothing (negative results, verified by execution)

These are as much a part of the review as the findings above.

1. **`lint-workflows.sh` cannot be made green while linting nothing.** I attacked it four
   ways: (a) explicit target = the canary fixture → RC 1 with both findings printed;
   (b) non-matching glob → RC 3, `could not read`, no false green; (c) an injected real
   defect (unquoted `$CF_HOOK` in a copy of `news-pipeline.yml`) → RC 1 with SC2086;
   (d) reasoning about a stubbed shellcheck — blocked, because the canary demands the two
   *specific* codes, not merely a nonzero exit. The `|| true` on line 24 is the only
   exit-code suppression in the phase and it is fully compensated by the grep on
   `SC2034`+`SC2086`. **The armed-check design is sound.**
2. **Every gate passes on a correct tree except H-01.** `bash .github/scripts/lint-workflows.sh`
   → RC 0 in 0.6 s. `pytest pipeline/tests/test_workflow_guards.py pipeline/tests/test_push_race.py -q`
   → **22 passed**.
3. **Mutation testing: 8 of 9 mutations RED.** Killed:
   `-gt`→never-fires (3 tests), empty-timestamp accepted (1), boundary `-gt`→`-ge` (2),
   `require-env` accepts blank (4), success line leaks values (1), `git push`→`git push
   --force` (2), rebase `--strategy-option=theirs` conflict-swallow (1), `git fetch`
   removed (2). Survivor: M5 (error-branch value leak) → recorded as L-06. **The
   assertions are genuinely load-bearing, not decorative.**
4. **`shellcheck -s bash .github/scripts/*.sh` → RC 0, zero findings.** All five scripts
   use `set -euo pipefail`.
5. **Exit-code laundering sweep.** Grepped all shipped scripts and workflows for
   `|| true`, `|| echo`, `; echo ok`, trailing `| tail`/`| head`, and `;`-broken `&&`
   chains. Only hit is the compensated canary (item 1). Every `continue-on-error` is on a
   step where it is intentional and UI-visible; the four in `cead-scraper.yml` are
   over-broad (M-07) but not laundering. **No hidden exit codes.**
6. **Timestamp parsing across all three real evidence formats.** Executed
   `check-heartbeat.sh` against the actual values, not synthetic ones:
   `2026-08-04T19:27:07.995153Z` (Python microseconds, from the live
   `data/incidents/current.json`) → OK; `2026-06-19T17:24:23-04:00` (git `%cI`, negative
   offset) → OK; `2026-08-03T05:30:12Z` (gh API) → OK. **Fractional seconds and non-UTC
   offsets both parse.**
7. **`heartbeat.yml`'s news check reads the right field and degrades correctly.**
   `current.json`'s key set is `['generated', 'window_days', 'incidents']`;
   `freshness.mjs:56` reads `data.generated` and the heartbeat's `python3 -c` reads
   `['generated']` — they agree. Simulated three degradations, all exit 1 under the
   default `bash -e` used by `run:` blocks: file missing (`FileNotFoundError` → step RC 1),
   `generated` key absent (`KeyError` → RC 1), evidence path empty
   (`no timestamp evidence found … treating as stalled` → RC 1). **A malformed or missing
   `current.json` is treated as a stall, not a pass.**
8. **F-83b's validator numbering is correct.** `site/scripts/validate/all.mjs` lists 16
   validators and `freshness.mjs` is #15. The header comment's correction is accurate.
9. **F-84's shape holds where it is claimed.** In both `news-pipeline.yml` and
   `cead-scraper.yml` the `Guard deploy hook` step is positioned strictly after
   `Commit data if changed` and carries no `if:`, so a blank hook fails the job loudly
   *after* the corpus is safely committed and pushed. Traced all four news-cron paths
   (changed / unchanged / scrape-failed / push-rejected) — the deploy fires exactly when
   `steps.commit.outputs.changed == 'true'`, and a rebase conflict correctly prevents both
   the `changed=true` output and the deploy.
10. **`heartbeat.yml` permissions are correct and complete.** `actions: read` is required
    and present for `gh run list`; `issues: write` for `gh label create` / `gh issue
    create`; `contents: read` + `fetch-depth: 0` for the CEAD `git log`. Steps 2 and 3
    carry `if: '!cancelled()'` so all three checks run independently — F-88 as described.
11. **`actions/checkout@v7` / `setup-python@v7` are the repo-wide pre-existing pin**
    (present in `ci.yml` and at the base commit), not something this phase invented.
12. **R2 env var names match the code.** `archive_r2.py:470-475` reads exactly
    `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` — the guard
    names are right, only the *required-ness* of `R2_BUCKET` is wrong (H-01).
13. **`DEPLOYMENT.md`'s "R2 … no `data/` write, no push" claim is true** — no `data/`
    write path exists in `archive_r2.py`.
14. **Repo left clean.** `git status --porcelain` empty after all nine mutations were
    reverted with `git checkout --`. No writes to `data/`, no push, no
    `workflow_dispatch`, no issue or label mutation (only `gh label list`,
    `gh secret list`, `gh variable list`, `gh api …/environments` — all read-only).

---

_Reviewed: 2026-08-04 · Reviewer: gsd-code-reviewer (adversarial, execution-based) · Depth: deep_
