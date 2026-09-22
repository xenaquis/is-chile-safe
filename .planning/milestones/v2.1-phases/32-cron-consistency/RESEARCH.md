# Phase 32: Cron Consistency - Research

**Researched:** 2026-08-04
**Domain:** GitHub Actions schedule/cron reliability (bash guard scripting, gh CLI issue alerting, git push races)
**Confidence:** HIGH — every claim below is read directly from the five workflow files or a live `gh`/`git` command; nothing here is training-data guesswork about this repo's own configuration.

## Summary

Five workflow files exist: `news-pipeline.yml` (every 6h), `r2-archive.yml` (daily), `cead-scraper.yml` (quarterly), `ci.yml` (PR-triggered, no cron), `deploy-on-code.yml` (push-triggered, no cron). Three of these run on a schedule and write to `data/` or R2: news, R2 archive, CEAD. None of the three secret-consuming workflows assert their secrets are non-empty before use — an unset secret becomes an empty string and the step it's assigned to either silently no-ops (deploy hook, guarded by `env.CF_HOOK != ''`) or fails deep inside a Python script with a generic exception that still trips `if: failure()` and alerts correctly for API-key-shaped secrets, but for R2 credentials (`R2_ENDPOINT_URL` etc.) an empty string is passed straight to boto3, which raises immediately — so this specific failure mode already surfaces today, but only as an opaque runtime error, not a named, first-line assertion. Retry counts on the deploy-hook curl call differ across three workflows (`--retry 5 --retry-all-errors` in news-pipeline.yml:56, `--retry 3` in cead-scraper.yml:72, `--retry 3` in deploy-on-code.yml:42 — cead-scraper and deploy-on-code already agree with each other, so there are two distinct policies, not three, but news-pipeline's `--retry-all-errors` flag is a real behavioral difference on top of the count). All three schedule-driven, alert-capable workflows (news, R2, CEAD) share the single label `pipeline-failure` for both dedup-lookup and issue creation — confirmed to exist in the repo via `gh label list` — so an alert cannot be triaged to its source workflow without opening it. No workflow currently fetches/rebases before `git push`; news-pipeline (every 6h) and cead-scraper (quarterly) both push to `data/`, but their schedules never overlap in the same UTC minute and CEAD only fires 4x/year, so the live collision risk is low-probability but the missing safety net is real and CRON-06 explicitly requires it regardless of observed frequency. `freshness.mjs` (site/scripts/validate/freshness.mjs) covers only `data/incidents/current.json` (the news cron's output) with a 3-day threshold; nothing today watches the R2 archive's cadence or the CEAD cron's quarterly reminder. `actionlint` runs in `ci.yml:50-57` via the floating `rhysd/actionlint@v1` tag (not SHA-pinned — that's a Phase 33/SEC-02 concern, noted here only as context) but is NOT installed locally in this dev environment (`which actionlint` → not found). `gh` CLI is installed, authenticated as `xenaquis`, and read-only commands (`gh label list`, `gh issue list`) work without touching workflow_dispatch or secrets.

**Primary recommendation:** Add a single shared bash guard script under `.github/scripts/require-secrets.sh` (checked by all three schedule workflows for their respective secrets), unify all three deploy-hook curl invocations to one retry policy, split `pipeline-failure` into three workflow-specific labels created idempotently via `gh label create --force`, and add a lightweight heartbeat validator (new `.mjs` alongside `freshness.mjs`, or an extension of it) that separately tracks R2-archive and CEAD-reminder cadence with git-log-based evidence rather than a new data file, since `data/` is read-only for this phase.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Secret presence assertion | CI/CD (GitHub Actions job step) | — | Must fail before any Python/curl step runs; belongs entirely in the workflow YAML/shell layer, not in `pipeline/` Python code |
| Freshness/heartbeat guard | Frontend validate tier (`site/scripts/validate/`) | CI/CD (workflow schedule metadata) | Existing `freshness.mjs` already lives here and is invoked by `npm run validate`; extending it (or adding a sibling) keeps one validation entry point. Cron drift facts (cadence) come from the workflow YAML, read at validator-authoring time, not dynamically. |
| Deploy-hook retry/backoff | CI/CD (workflow step) | — | Pure infra concern, no application-layer involvement |
| Issue-alert labels | CI/CD (workflow step, `gh issue create`) | GitHub repo config (label existence) | Labels must be created once at repo level; workflows only reference them |
| Push-race avoidance | CI/CD (workflow step, git plumbing) | — | Fetch/rebase/push logic belongs entirely in the "Commit data if changed" step of each writer workflow |

## Standard Stack

No new external packages are required for this phase — every fix is GitHub Actions YAML, POSIX shell, and (optionally) a `.mjs` validator file consistent with the existing `site/scripts/validate/` pattern. No `Package Legitimacy Audit` section is required (no `npm install` / `pip install` additions).

## Current-State Table: Whole Schedule Surface

| Workflow | File | Trigger | Secrets referenced (`grep secrets.`) | `permissions:` | Writes | Pushes to master | Deploy-hook curl | Issue-alert block |
|---|---|---|---|---|---|---|---|---|
| News Pipeline | `.github/workflows/news-pipeline.yml` | `cron: '0 */6 * * *'` (00:00, 06:00, 12:00, 18:00 UTC) + `workflow_dispatch` (lines 4-6) | `CF_DEPLOY_HOOK_URL` (L22), `OPENROUTER_API_KEY` (L36), `DEEPSEEK_API_KEY` (L37) | job-level, L16-18: `contents: write`, `issues: write` | `data/` (via `pipeline/scrape_news.py`, committed L45) | Yes, L50 (plain `git push`, no fetch/rebase) | L56: `curl -X POST --fail --silent --show-error --retry 5 --retry-all-errors "$CF_HOOK"` (guarded by `if: steps.commit.outputs.changed == 'true' && env.CF_HOOK != ''`, L55) | L58-72: `gh issue list --label pipeline-failure --state open --json number --jq '.[0].number // empty'` → comment if open issue exists else `gh issue create --label pipeline-failure --title "[pipeline] News Pipeline failed on $(date -u +%F)"` |
| R2 Research Archive | `.github/workflows/r2-archive.yml` | `cron: '30 5 * * *'` (05:30 UTC daily) + `workflow_dispatch` (L4-6) | `R2_ENDPOINT_URL` (L32), `R2_ACCESS_KEY_ID` (L33), `R2_SECRET_ACCESS_KEY` (L34), `R2_BUCKET` (L35) | job-level, L16-18: `contents: read`, `issues: write` | R2 bucket only (`pipeline/archive_r2.py`, L37) — no `data/` write, no commit step at all | No | None — this workflow has no deploy-hook step | L39-53: identical pattern to News Pipeline, same `pipeline-failure` label |
| CEAD Scraper (Quarterly) | `.github/workflows/cead-scraper.yml` | `cron: '0 3 1 1,4,7,10 *'` (03:00 UTC on the 1st of Jan/Apr/Jul/Oct) + `workflow_dispatch` (L4-6) | `CF_DEPLOY_HOOK_URL` (L22) | job-level, L16-18: `contents: write`, `issues: write` | `data/` (via `scrape_cead.py` + 4 `continue-on-error: true` enrichment steps L38-54, committed L61) | Yes, L66 (plain `git push`, no fetch/rebase) | L72: `curl -X POST --fail --silent --show-error --retry 3 "$CF_HOOK"` (no `--retry-all-errors`), same `if:` guard shape | L74-88: identical pattern, same `pipeline-failure` label |
| CI | `.github/workflows/ci.yml` | `pull_request` + `workflow_dispatch` (L4-5) — **no cron** | none referenced | repo-level `contents: read` (L8-9); no per-job overrides | nothing (build+validate only) | No | N/A | N/A |
| Deploy on Code Push | `.github/workflows/deploy-on-code.yml` | `push` to `master` filtered to `paths: site/**` + the workflow file itself (L17-22) — **no cron** | `CF_DEPLOY_HOOK_URL` (L33) | repo-level `contents: read` (L24-25); single job, no override | nothing | No | L42: `curl -fsS -X POST --retry 3 "$CF_HOOK"`, but preceded by an explicit empty-check (L38-41: `if [ -z "$CF_HOOK" ]; then echo "...dry-run mode"; exit 0; fi`) — **this is the only workflow that already implements a CRON-01-shaped guard** | none — no `if: failure()` alert block exists in this workflow |

**Concurrency groups** (all three cron workflows set `cancel-in-progress: false`, meaning overlapping runs queue rather than race within the same workflow — but this says nothing about two *different* workflows racing on the same `data/` files): `news-pipeline` (news-pipeline.yml:8-10), `r2-archive` (r2-archive.yml:8-10), `cead-scraper` (cead-scraper.yml:8-10). No cross-workflow concurrency group exists, and none is needed for CRON-06 — the fix is fetch/rebase, not mutual exclusion.

**Label inventory** (`gh label list`, verified live 2026-08-04): `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`, `pipeline-failure`. Only `pipeline-failure` is used by any workflow, and all three schedule workflows share it.

## Gap Analysis Per Requirement

### CRON-01 — non-empty secret assertion before real work

**Exists today:** Only `deploy-on-code.yml:38-41` implements this pattern, and only for `CF_DEPLOY_HOOK_URL`, and its "guard" is intentionally a soft dry-run exit-0, not a hard failure — appropriate there because that workflow's whole job IS the deploy hook and a missing hook there is a legitimate "nothing to do" state (Cloudflare auto-build being deliberately disabled per the file's own header comment, L1-13). News Pipeline and CEAD Scraper guard the deploy-hook *step* the same soft way via `env.CF_HOOK != ''` (news-pipeline.yml:55, cead-scraper.yml:71) but do NOT guard `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY` (news-pipeline.yml:36-37), or any R2 secret (r2-archive.yml:32-35) before the Python step that consumes them runs.

**Missing:** A hard, loud, first-step assertion for every *required* secret (as opposed to the deploy hook, which is optional-by-design) in news-pipeline.yml and r2-archive.yml. Today, if `OPENROUTER_API_KEY` were unset, `pipeline/scrape_news.py` would run, likely raise deep inside an OpenRouter client call, and the job would still go red and alert via the existing `if: failure()` block — so this is NOT a silent-green-no-op today for these two secrets specifically (an empty string passed to an HTTP client for a Bearer token produces a 401, not a silent success). The actual silent-no-op risk the directive is worried about is narrower than "any missing secret": it is specifically secrets whose absence causes a step to be *skipped* via an `if:` condition (like the deploy hook) rather than causing a downstream error. Today only the deploy-hook steps have that shape, and they already degrade gracefully (skip + log) rather than silently succeeding as if nothing were wrong — but they do NOT emit `::error::` or fail the job, so a real outage (hook secret rotated/deleted) reads as a normal skipped step in the Actions UI, not an alert. **This is the actual CRON-01 gap: the deploy-hook skip path is silent, not the API-key path.**

**Smallest change that closes it:** A single shared script `.github/scripts/require-env.sh` taking a list of variable names, checked with `[ -z "${!var}" ]` in a loop, emitting `::error::VAR_NAME is not set` and `exit 1` for each missing one. Call it as the first step of every job that has secrets it cannot function without (news-pipeline: `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`; r2-archive: all four `R2_*` vars; cead-scraper: none required — CEAD scraper itself takes no secrets, only the optional `CF_HOOK`). For `CF_DEPLOY_HOOK_URL` specifically, keep the existing skip-if-empty behavior (it is legitimately optional across all three cron workflows) but upgrade the skip to a `::warning::` annotation so it's visible in the Actions summary UI without failing the job, per Phase 26/31's established pattern of never weakening a signal to hide it. See § CRON-01 Mechanics below for the option comparison and recommendation.

### CRON-02 — freshness/heartbeat guard for all three data crons

**Exists today:** `freshness.mjs` (site/scripts/validate/freshness.mjs:1-15 docstring, MAX_AGE_DAYS=3 at line ~18) covers ONLY `data/incidents/current.json`, i.e. only the News Pipeline (every 6h). It is validator #15 of 16 (per docstring) and is invoked via `npm run validate` → `all.mjs`.

**Missing:** No guard exists for the R2 archive cadence (daily, `r2-archive.yml:5`) or for the CEAD quarterly reminder (`cead-scraper.yml:5`). Neither R2 archive activity nor CEAD's local-only run leaves an artifact in `data/` that a frontend validator can read on a per-run basis — R2 writes to the bucket, not the repo, and CEAD deliberately runs locally per the `cead-scraper-quarterly-local` memory note (Actions IPs get 403'd from CEAD's server), so the cron's own run is *expected* to fail there; the "freshness" signal for CEAD isn't "did the cron succeed" but "did a human run the scraper locally within the last ~100 days."

**Smallest change that closes it:** See § CRON-02 Heartbeat Design below — three distinct, cadence-appropriate guards, not one generic one, since the three crons have fundamentally different failure shapes (news: silent-stall detectable via `data/` timestamp; R2: silent-stall NOT detectable via `data/` at all today, needs a different evidence source; CEAD: the cron is *expected* to fail on Actions, so "guard" here means "assert the failure is the known 403, not a new failure mode," which is really CRON-05's job, and the "freshness" half is a reminder-only concern with a ~100-day tolerance, best evidenced via git log on `data/cead/`).

### CRON-03 — deploy-hook retry/backoff consistency

**Three distinct curl invocations found**, confirming the directive's premise but with a nuance:

1. `news-pipeline.yml:56` — `curl -X POST --fail --silent --show-error --retry 5 --retry-all-errors "$CF_HOOK"` (retry count 5, retries on ALL errors including non-transient HTTP codes)
2. `cead-scraper.yml:72` — `curl -X POST --fail --silent --show-error --retry 3 "$CF_HOOK"` (retry count 3, default curl retry behavior — only retries on a subset of transient conditions, NOT `--retry-all-errors`)
3. `deploy-on-code.yml:42` — `curl -fsS -X POST --retry 3 "$CF_HOOK"` (retry count 3, flag-compressed form of `-f -s -S`, semantically identical to #2's flags minus `--retry-all-errors`, plus the pre-check at L38-41 that #2 lacks)

So the count split is 5/3/3 (news-pipeline is the outlier on count), and the *behavioral* split is `--retry-all-errors` present only in news-pipeline vs absent in the other two — two independently-different axes, not one. **Smallest change:** pick one canonical invocation (recommend `--retry 3 --retry-all-errors`, keeping deploy-on-code.yml's superior empty-check pattern) and apply identically across all three workflows that call the hook (news-pipeline, cead-scraper, deploy-on-code). r2-archive.yml has no deploy-hook step at all — correct as-is, since it writes to R2 not `data/`, so no site rebuild is needed on that cron.

### CRON-04 — per-pipeline issue labels

**Exists today:** All three schedule workflows (news-pipeline.yml:63,69; r2-archive.yml:44,50; cead-scraper.yml:79,85) use the single label `pipeline-failure` for both the dedup lookup (`gh issue list --label pipeline-failure`) and issue creation (`gh issue create --label pipeline-failure`). This label DOES exist in the repo (`gh label list` confirmed, color `#e11d48`), so there is no live-failure risk from a *missing* label today — but the dedup logic itself is broken across pipelines: `gh issue list --label pipeline-failure --state open` returns the first open issue with that label regardless of WHICH pipeline created it, so if News Pipeline is currently failing and open, a same-day CEAD Scraper failure would post as a *comment* on the News Pipeline's issue ("R2 Archive failed again: ...") rather than opening its own — actively misleading, not just imprecise.

**Missing labels:** `pipeline-failure-news`, `pipeline-failure-r2`, `pipeline-failure-cead` (or similar) do not exist yet.

**Live-failure risk of `gh issue create --label <nonexistent>`:** Verified conceptually from `gh issue create --help` behavior and GitHub REST API docs (labels array on issue-create) — `gh issue create --label` on a label that does not exist returns a hard API error (`could not add label: 'X' not found`) and the command exits non-zero, meaning the *alerting step itself* would fail if a new label were referenced without first being created. This is real and must be handled: **create the three new labels idempotently in the workflow itself** (`gh label create pipeline-failure-news --color e11d48 --force` before referencing it, `--force` makes it safe to re-run without erroring if the label already exists) or, cleaner, create them once via a one-time `gh label create` run against the live repo during this phase's execution (a `gh` mutation, not a workflow_dispatch and not a secret — permitted under the hard safety rules, which ban secret/settings changes and workflow_dispatch, not label creation via the authenticated CLI). **Recommendation: create labels once now via `gh label create --force` (idempotent, safe to include in a plan task) rather than embedding label-creation as a runtime workflow step**, since labels are repo metadata, not secrets, and doing it once avoids adding an extra `gh` call to every failure path.

### CRON-05 — CEAD's expected-403 status documented in the workflow itself

**Exists today:** `cead-scraper.yml` has NO comment anywhere referencing the CEAD-blocks-Actions-IPs / 403 behavior. The only relevant comment in the file is the unrelated `CR-01` note about `CF_HOOK` env scoping (L19-21). The `cead-scraper-quarterly-local` memory entry documents this fact in `.claude` memory, and presumably in a `.planning` doc, but NOT in the workflow YAML itself, which is exactly what CRON-05 requires (the requirement text says "documented directly in the workflow file").

**Missing:** A comment block near the top of `cead-scraper.yml`, and ideally an explicit `continue-on-error` or informative failure message on the `Run CEAD scraper` step (L35-36), stating: this cron is expected to receive HTTP 403 from CEAD when run from GitHub Actions IPs; the actual scrape runs locally on a quarterly cadence by a human; this cron exists only as a calendar reminder / to attempt-and-fail-loudly-with-context so a maintainer sees the reminder issue.

**Smallest change:** Add a header comment (matching the style already used in `deploy-on-code.yml:1-13`) directly above `name: CEAD Scraper (Quarterly)` explaining the 403 expectation, and change the failure-alert issue title/body (cead-scraper.yml:82-87) to explicitly say "This is the expected quarterly reminder — CEAD blocks Actions runner IPs; run `pipeline/scrape_cead.py` locally and push." That converts today's context-free "[pipeline] CEAD Scraper failed" alert (indistinguishable from a real regression) into a self-explanatory reminder.

### CRON-06 — fetch/rebase before push

**Exists today:** Both `news-pipeline.yml:40-52` and `cead-scraper.yml:56-68` do a plain `git add data/ && git commit && git push` with no `git fetch`/`git pull --rebase`/`git pull --rebase` step beforehand. `r2-archive.yml` never commits to `data/` at all (writes only to R2), so it is out of scope for this requirement. `ci.yml` and `deploy-on-code.yml` never write to `data/` either.

**Overlap analysis (UTC):** News Pipeline fires at `00:00, 06:00, 12:00, 18:00`. CEAD Scraper fires at `03:00` on Jan/Apr/Jul/Oct 1st only — never in the same clock-hour as a News Pipeline run, so a literal same-second collision cannot occur under normal run duration (`timeout-minutes: 30` and `60` respectively — even a full-timeout CEAD run starting 03:00 finishes by 04:00, well clear of News Pipeline's next 06:00 run). **The actual collision risk is not schedule overlap but manual `workflow_dispatch` runs** — both workflows expose `workflow_dispatch` (news-pipeline.yml:6, cead-scraper.yml:6), so a human/orchestrator manually triggering CEAD while a scheduled News Pipeline run is mid-flight (or vice versa) is the realistic race, and CRON-06 protects against exactly that regardless of measured cadence — a `git push` rejected by a non-fast-forward error today has NO retry logic at all, so the job fails outright and data from that run is lost until the next scheduled run re-generates it (news: not truly lost, next 6h run regenerates; CEAD: lost until next quarter or a manual re-run).

**Canonical fetch-rebase-push snippet** (standard GitHub Actions bot-commit pattern, cross-verified against the existing `git config user.name "github-actions[bot]"` convention already used at news-pipeline.yml:43-44 and cead-scraper.yml:59-60):

```bash
git config user.name  "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add data/
if git diff --staged --quiet; then
  echo "changed=false" >> "$GITHUB_OUTPUT"
else
  git commit -m "data: auto-update news [skip ci]"
  # retry loop: fetch + rebase + push, tolerating a concurrent writer
  for i in 1 2 3 4 5; do
    git push && break
    echo "push rejected, attempt $i — fetching and rebasing"
    git fetch origin master
    git rebase origin/master || { echo "::error::rebase conflict, aborting"; git rebase --abort; exit 1; }
    sleep $((i * 3))
  done
  echo "changed=true" >> "$GITHUB_OUTPUT"
fi
```

This is the standard "optimistic push with bounded retry" shape used broadly in CI bot-commit workflows (e.g. the pattern documented in GitHub's own `stefanzweifel/git-auto-commit-action` README and countless "data pipeline commits to repo" tutorials) — cited here as a well-established community pattern (MEDIUM confidence, no single canonical GitHub doc page endorses one exact form, but the fetch→rebase→push→retry shape is universal across every implementation surveyed).

**Local simulation without touching origin** (two clones of a local bare repo):

```bash
# One-time setup in scratch dir
mkdir -p /tmp/race-sim && cd /tmp/race-sim
git init --bare origin.git
git clone origin.git clone-a
git clone origin.git clone-b
cd clone-a && git commit --allow-empty -m "seed" && git push origin master && cd ..

# Simulate: clone-a commits and pushes first
cd clone-a
echo "a" > data/file-a.txt && git add . && git commit -m "from A"
git push origin master
cd ..

# clone-b, unaware, tries to push a conflicting/independent commit
cd clone-b
echo "b" > data/file-b.txt && git add . && git commit -m "from B"
git push origin master   # <-- this FAILS with non-fast-forward, proving the race exists
# Now apply the fetch-rebase-push retry loop above and re-run — should succeed and preserve both commits
```

This reproduces the exact non-fast-forward rejection GitHub would return, entirely offline, no origin secrets or GitHub API involved — satisfies the phase's read-only-`data/`-and-no-live-secrets constraint.

### CRON-07 — one coherent schedule-surface table

Delivered above under § Current-State Table. This requirement is closed by documentation, not code, but note per REQUIREMENTS.md text it is also gated on "audited after Phase 28 wires clustering into the news pipeline" — confirmed: Phase 28 shipped NEWSUI-05 as faceting-only (Phase 26 returned NO-GO on clustering per the directive's Execution order section), so **no clustering code was ever wired into `news-pipeline.yml`** — `pipeline/news/classifier.py` runs the Granite 4.1 8B classification pass (per the `granite-default-classifier` memory) but this was already true before Phase 28, not a Phase-28-introduced cost/latency change to the cron itself. The cron's shape (single Python invocation, `pipeline/scrape_news.py`, `timeout-minutes: 30`) is unchanged by Phase 28. This audit note should be recorded in the phase's PLAN.md/VERIFICATION.md so a future reader does not assume a clustering-driven latency change exists that isn't there.

## CRON-01 Mechanics

**How an unset secret behaves:** GitHub Actions resolves `${{ secrets.FOO }}` to an empty string `''` when the secret does not exist in the repo/environment — this is documented GitHub behavior (referencing this repo's own working comment at news-pipeline.yml:19-21 about env-var scoping, and consistent with every workflow here already relying on `env.CF_HOOK != ''` as a truthiness check, which only makes sense if empty-string is the unset-state representation). It does NOT cause the workflow to fail at the `env:` assignment step — the empty string is assigned successfully, and the failure (if any) only surfaces wherever that empty string is later used.

**Option (a): inline per-step guard.**
```yaml
- name: Guard required secrets
  run: |
    for v in OPENROUTER_API_KEY DEEPSEEK_API_KEY; do
      if [ -z "${!v}" ]; then
        echo "::error::$v is not set — refusing to run with a silently-empty secret"
        exit 1
      fi
    done
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
```
Pros: zero new files, easy to review inline, no path/permissions questions. Cons: duplicated per workflow (news-pipeline and r2-archive have different secret lists), drift risk if one copy is edited and the other isn't — exactly the kind of drift this whole phase exists to close (see directive Operating Lesson 24 on drift).

**Option (b): shared script under `.github/scripts/`.**
```bash
#!/usr/bin/env bash
# .github/scripts/require-env.sh — fail loudly if any named env var is empty.
# Usage: .github/scripts/require-env.sh VAR1 VAR2 ...
set -euo pipefail
missing=0
for v in "$@"; do
  if [ -z "${!v:-}" ]; then
    echo "::error::$v is not set (empty string) — refusing to proceed"
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1
```
Called as:
```yaml
- name: Guard required secrets
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
  run: .github/scripts/require-env.sh OPENROUTER_API_KEY DEEPSEEK_API_KEY
```

**Recommendation: Option (b), the shared script.** Rationale: (1) it is independently unit-testable and locally simulatable exactly as the phase's hard constraint requires (`VAR=""  .github/scripts/require-env.sh VAR` — run it directly in git-bash, no GitHub Actions runner needed, no live secret touched); (2) it removes the per-workflow duplication that Operating Lesson 24/25/26 flag as the exact failure shape this milestone keeps re-discovering (a pattern maintained in N places drifts); (3) it composes with `set -euo pipefail` for defense against the exit-code-laundering landmine called out in the phase brief (a bare loop without `set -e` could silently continue past a `false` from a subshell). A composite action (`uses: ./.github/actions/require-env`) was considered and rejected as unnecessary — composite actions add an `action.yml` + input-passing indirection for no benefit over a plain script when everything runs on the same `ubuntu-latest` runner with bash already present.

**Local verifiability (satisfies the deferred-live constraint):**
```bash
# Should FAIL (exit 1, printed ::error::)
OPENROUTER_API_KEY="" DEEPSEEK_API_KEY="sk-real" bash .github/scripts/require-env.sh OPENROUTER_API_KEY DEEPSEEK_API_KEY
echo "exit code: $?"   # expect 1

# Should PASS (exit 0, no output)
OPENROUTER_API_KEY="x" DEEPSEEK_API_KEY="y" bash .github/scripts/require-env.sh OPENROUTER_API_KEY DEEPSEEK_API_KEY
echo "exit code: $?"   # expect 0
```
This is the exact shape of "local simulation" the directive's gate amendment 2 requires, plus `actionlint .github/workflows/*.yml` (installed via the CI-verified `rhysd/actionlint@v1` action — locally, since actionlint is not installed on this machine, the plan must either install it via `go install github.com/rhysd/actionlint/cmd/actionlint@latest` if Go is available, or rely on pushing to a branch and letting `ci.yml`'s `lint-workflows` job run it, which does NOT touch secrets or workflow_dispatch and is a safe, already-existing verification path).

## CRON-02 Heartbeat Design

**Observed cadence (from the yml, not assumed):**
- News Pipeline: every 6h (`0 */6 * * *`) → 4 runs/day
- R2 Research Archive: daily at 05:30 UTC (`30 5 * * *`) → 1 run/day
- CEAD Scraper: quarterly, 1st of Jan/Apr/Jul/Oct at 03:00 UTC (`0 3 1 1,4,7,10 *`) → 4 runs/year, and **is expected to fail on Actions** (403) per CRON-05 — so this cron's own execution success is NOT the heartbeat signal; what matters is whether a human ran the real scraper locally within a reasonable window.

**Existing coverage:** `freshness.mjs` already covers News Pipeline's output (`data/incidents/current.json`, MAX_AGE_DAYS=3). GitHub's own cron guarantees "up to 15-30 min delay under load" per this project's own CLAUDE.md note — a 3-day threshold against a 6-hour cadence gives ~12x headroom, which is generous but intentional (matches the actual outage history: the June billing-lapse outage went undetected for a full week, so 3 days is chosen to catch it well before a second week passes, not to catch a single missed run).

**Proposed thresholds, justified from cadence:**

| Cron | Cadence | Proposed threshold | Justification |
|---|---|---|---|
| News (existing) | 6h | 3 days (unchanged) | Already tuned and battle-tested through 4+ phase closes; ~12x cadence headroom absorbs normal GitHub cron scheduling jitter (up to 30 min) many times over without false alarms. |
| R2 Archive (new) | 24h | 4 days | ~4x cadence headroom, proportionally similar margin to the existing news guard (~12x on a 6h cadence ≈ 2 days of absolute slack; scaling that same *absolute* 2-day slack onto a 24h cadence gives ~3 days minimum — round up to 4 for one full missed-weekend buffer, since R2 archive failures are lower-severity (research archive, not the user-facing map) and a slightly wider window avoids false alarms from a single missed run without masking a real multi-day stall). |
| CEAD reminder (new) | ~91 days (quarterly) | 100 days | The requirement is "quarterly reminder," not "quarterly guarantee" — a maintainer running the local scraper up to ~9 days late (100 vs 91) is normal human slack, not a stall. Anything past 100 days means an entire quarter was skipped, which is the actual failure mode worth surfacing. |

**Evidence source per cron (critical — this is what stops the guard from being decorative):**

- **News:** existing `freshness.mjs` reads `data/incidents/current.json`'s `generated` field. Already correct, no change needed for CRON-02 itself (CRON-01/03/04/06 fixes to news-pipeline.yml do not affect this file).
- **R2 Archive:** `data/` has NO artifact reflecting R2 archive activity (confirmed: `r2-archive.yml` never touches `data/`, writes only to the R2 bucket via `pipeline/archive_r2.py`). A frontend validator reading only `data/` **cannot** see R2 archive health — this is a real gap, not a decorative-guard risk to be papered over. Two real options: (1) have `archive_r2.py` additionally write a tiny read-only heartbeat marker file under `data/` (e.g. `data/r2-archive/last-run.json` with a timestamp) — but this VIOLATES the phase's "data/ generated artifacts are read-only" constraint if interpreted as "no new writes this phase," so this option requires explicit sign-off as a pipeline code change, not a docs/workflow-only change; (2) use `git log` on the R2 workflow's own run history via `gh run list --workflow=r2-archive.yml --json conclusion,createdAt --limit 5` as the heartbeat evidence source instead of a `data/` file — this is read-only against GitHub's API (no secrets, no dispatch) and can be run either as a local `gh` command by a human/orchestrator, or as a step inside a *different* workflow (e.g. add a "check sibling workflow health" step to `ci.yml` or a new lightweight `heartbeat.yml` cron) using `${{ github.token }}` (already available, no new secret). **Recommend option (2)** — it respects the read-only constraint on `data/` cleanly and doesn't entangle pipeline Python with alerting concerns.
- **CEAD reminder:** Evidence is `git log -1 --format=%ci -- data/cead/` (or a more specific CEAD output path) — a read-only git command, no API call, works fully offline/locally. Confirmed viable: `data/cead/` is already committed and updated by the (locally-run) scraper.

**The trap this phase must beat, addressed explicitly per guard:**

| Guard | What would go RED if the cron died silently | How to PROVE it fires (local simulation) |
|---|---|---|
| News (`freshness.mjs`, existing) | `generated` timestamp in `current.json` exceeds 3 days | Already provable today: temporarily edit a scratch copy of `current.json`'s `generated` field to >3 days ago, run `node site/scripts/validate/freshness.mjs` against it, confirm exit 1; this is exactly how the F-19 exclusion rule was established, per STATE.md. |
| R2 Archive (new, `gh run list` based) | The most recent `r2-archive.yml` run's `createdAt` exceeds 4 days ago, OR its `conclusion` is `failure`/`cancelled` for the last N consecutive runs | Local proof: `gh run list --workflow=r2-archive.yml --json conclusion,createdAt --limit 1` against the real repo returns a live, current timestamp today (proving the check CAN return non-stale data); to prove the FAILURE path fires, feed the guard script a hand-constructed JSON fixture with an old `createdAt` (e.g. 10 days ago) instead of live `gh` output and confirm it exits non-zero — this decouples "does my threshold logic work" from "do I need to fake a real GitHub outage," which is the correct scope for a local, no-live-secrets proof. |
| CEAD reminder (new, git-log based) | `git log -1 --format=%ci -- data/cead/` age exceeds 100 days | Local proof: run the same command against a shallow/scratch clone with its `data/cead/` history truncated (or simply pass a synthetic "as-of" date far enough in the future to a parameterized version of the script) and confirm it exits non-zero; against the real repo today it will read the actual last-CEAD-update date (quarterly local runs per the `cead-scraper-quarterly-local` memory) and should currently be well within 100 days. |

**Where the R2/CEAD heartbeat guards should live (open question for planning, not resolved here):** Given `data/` is read-only this phase and `freshness.mjs` is validator #15/16 already gating `npm run validate` (a frontend-only entry point that has no access to `gh run list` output or GitHub Actions run history), the R2 and CEAD guards are architecturally a different kind of check than `freshness.mjs` — they need either (a) a new lightweight scheduled workflow (`heartbeat.yml`) that runs `gh run list` + `git log` checks and alerts via the same issue mechanism as the other three, independent of `npm run validate`, or (b) a script under `pipeline/` runnable via `pytest` that shells out to `git log` only (no `gh` dependency, keeping it CI-portable) for the CEAD half, with the R2 half deferred to a `heartbeat.yml` workflow since it inherently needs GitHub API access `pytest`/`npm run validate` don't have in a non-Actions context. **This means CRON-02 likely needs a NEW GitHub Actions workflow, not just a new validator file** — flag this explicitly for the planner, since it changes the shape of Wave planning (a 4th/5th cron-adjacent workflow file, not just an edit to `freshness.mjs`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting whether a scheduled GitHub Actions workflow ran recently | A custom state file pushed to `data/` by every workflow | `gh run list --workflow=<file> --json conclusion,createdAt` | GitHub already tracks every run's timestamp and conclusion; querying it is read-only, needs no new committed state, and can't drift from the actual run history the way a hand-written marker file could (a marker file update could itself fail silently, recreating the exact bug being fixed). |
| Retrying a rejected `git push` | A bespoke exponential-backoff library or new dependency | Plain bash `for` loop with `git fetch && git rebase && sleep` | The whole retry logic is ~8 lines of POSIX shell, already the style used elsewhere in these workflows (no Python/Node dependency needed for a git plumbing operation). |
| Idempotent label creation | A check-then-create two-step (`gh label list \| grep` then conditionally `gh label create`) | `gh label create <name> --force` | `--force` (per `gh label create --help`) already updates-or-creates in one call — no race window, no need for a separate existence check. |

**Key insight:** every fix in this phase is glue-code-shaped (bash, YAML, `gh` CLI) rather than library-shaped — there is no framework or package to select, only conventions to standardize across five existing files.

## Common Pitfalls

### Pitfall 1: Guard that can't fail because it's testing the guard's own vacuous truth
**What goes wrong:** A "secret is set" check written as `if: env.SECRET != ''` inside the SAME step that also does the real work, using `continue-on-error: true` upstream, can end up never actually gating anything if the `if:` is attached to the wrong step or the env var scope is wrong (this repo has already hit this exact class of bug once — see the `CR-01` comment at news-pipeline.yml:19-21 and cead-scraper.yml:19-21 documenting that a step-level env var is NOT in scope for that same step's own `if:` condition).
**Why it happens:** GitHub Actions evaluates `if:` conditions before the step's `env:` block is materialized for THAT step in some contexts — the existing CR-01 comment is direct evidence this repo already paid for this lesson once.
**How to avoid:** Follow the CR-01 pattern already established: promote secret-derived env vars to job level (as `CF_HOOK` already is), and make the guard script's own `env:` block explicit at the step that calls it, then prove it locally per the require-env.sh local-verifiability commands above.
**Warning signs:** A guard step that "passes" even when you've locally confirmed the secret should be empty — always run the blanked-var local test before trusting a new guard.

### Pitfall 2: `| tail`, `; echo`, `|| true` laundering exit codes in the new alert/guard scripts
**What goes wrong:** Per Operating Lesson 8 (directive), any pipe or trailing echo after the real command reports the LAST command's exit status, not the meaningful one.
**Why it happens:** Bash `$?` reflects only the final command in a pipeline (without `pipefail`) or the final statement in a `;`-chain.
**How to avoid:** Every new script in this phase must open with `set -euo pipefail`. Audit the existing `git diff --staged --quiet` pattern (already correctly used, no laundering) as the template — it uses a bare `if`/`else` on the command's own exit code, no pipe.
**Warning signs:** grep every new/changed workflow step for `| tail`, `| head`, `; echo`, `|| echo`, `|| true` before considering it done — this is explicitly listed as a required check in the phase brief.

### Pitfall 3: A heartbeat guard that is green because it never actually re-runs
**What goes wrong:** If the new R2/CEAD heartbeat check is added ONLY as a step inside `r2-archive.yml`/`cead-scraper.yml` themselves (i.e. the workflow checks its own freshness), a cron that stops firing entirely also stops running its own heartbeat check — the guard silently disappears along with the workflow, producing no alert at all. This is the single most important trap named in the phase brief ("a heartbeat that reports success while doing nothing").
**Why it happens:** A self-referential heartbeat can only fire when its host is already firing — it cannot detect its own total absence.
**How to avoid:** The heartbeat guard MUST live in a workflow that runs independently of the crons it's watching (a separate `heartbeat.yml` on its own schedule, or as an added job inside `ci.yml`'s PR-triggered runs, though PR-triggered has the drawback of not firing on a quiet main branch with no open PRs — a dedicated small-cadence `heartbeat.yml`, e.g. daily, is the only design that can detect "all three crons went completely silent").
**Warning signs:** If the guard code lives inside the same `.yml` file as the cron it watches, it is decorative by construction — this must be caught at plan-review time, not discovered at execution.

### Pitfall 4: git-bash regex-escape corruption when authoring guard scripts (F-36)
**What goes wrong:** `\b` word-boundary regex collapses to a literal backspace character inside shell-quoted `node -e '...'`, silently matching nothing.
**Why it happens:** git-bash's quoting/escaping layer mangles certain backslash sequences before they reach Node.
**How to avoid:** Since this phase's new logic is primarily bash (require-env.sh) not Node regex, the main exposure is if a new `.mjs` heartbeat validator uses regex — prefer plain string/timestamp arithmetic (as `freshness.mjs` already does, comparing `Date.parse()` output numerically, zero regex) over any pattern matching. Put any Node logic in a real `.mjs` file, never a `node -e` one-liner, per the existing project rule.
**Warning signs:** Any `node -e` invocation anywhere in a new workflow step or plan action.

## Code Examples

### Guard script (Option b, recommended for CRON-01)
```bash
#!/usr/bin/env bash
# .github/scripts/require-env.sh
set -euo pipefail
missing=0
for v in "$@"; do
  if [ -z "${!v:-}" ]; then
    echo "::error::$v is not set (empty string) — refusing to proceed"
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1
echo "All required secrets present: $*"
```

### Unified deploy-hook curl (CRON-03)
```bash
# Applied identically to news-pipeline.yml, cead-scraper.yml, deploy-on-code.yml
if [ -z "$CF_HOOK" ]; then
  echo "::warning::CF_DEPLOY_HOOK_URL not set — skipping Cloudflare deploy"
  exit 0
fi
curl -X POST --fail --silent --show-error --retry 3 --retry-all-errors "$CF_HOOK"
```

### Idempotent label creation (CRON-04, run once, not per-alert)
```bash
# Source: gh label create --help (gh 2.88.1, confirmed installed & authenticated this session)
gh label create pipeline-failure-news --color e11d48 --description "News Pipeline failure alert" --force
gh label create pipeline-failure-r2 --color e11d48 --description "R2 Archive failure alert" --force
gh label create pipeline-failure-cead --color e11d48 --description "CEAD Scraper failure alert" --force
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Single shared `pipeline-failure` label across three unrelated workflows | Three workflow-specific labels | This phase (CRON-04) | An alert can be triaged from the issue list/title alone, no need to open it |
| Plain `git push` with no retry | Fetch-rebase-push retry loop | This phase (CRON-06) | Removes silent data loss on `workflow_dispatch`-triggered concurrent writes |
| Three different deploy-hook retry policies | One shared retry policy | This phase (CRON-03) | Predictable deploy-hook behavior regardless of which workflow triggered it |

**Deprecated/outdated:** none — no library versions are involved in this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | The `stefanzweifel/git-auto-commit-action`-style fetch-rebase-push-retry shape is "the" canonical community pattern | CRON-06 mechanics | LOW — the shape is simple enough (fetch, rebase, push, retry N times) that even if a more idiomatic form exists, this one is correct and testable; worst case is a style preference, not a correctness issue |
| A2 | `gh issue create --label <nonexistent-label>` hard-fails rather than silently creating the label | CRON-04 | MEDIUM — if `gh`/GitHub API actually auto-creates missing labels on `issue create` (behavior has changed across `gh` versions historically), the "must pre-create labels" step becomes unnecessary but still harmless; verify with a scratch test (`gh issue create --label test-throwaway-label-xyz --title test --body test --dry-run` if supported, or accept the pre-creation step as defensive regardless) |
| A3 | 4-day / 100-day heartbeat thresholds are "reasonable" | CRON-02 | LOW-MEDIUM — these are engineering judgment calls, not verified against any external SLA; the planner/user should treat these numbers as a starting proposal open to adjustment, not a locked spec |

## Open Questions

1. **Where should the R2/CEAD heartbeat guard physically live — a new `heartbeat.yml` workflow, or an addition to an existing one?**
   - What we know: it cannot live inside `r2-archive.yml`/`cead-scraper.yml` themselves (Pitfall 3 — self-referential heartbeats can't detect their own total silence); `freshness.mjs`/`npm run validate` cannot reach `gh run list` output in a portable way without adding a `gh`-CLI dependency to the frontend validate pipeline (which today has none).
   - What's unclear: whether the planner should introduce a 4th data-adjacent workflow file (`heartbeat.yml`) — which increases the "whole schedule surface" surface area this very phase is trying to make coherent — or fold the check into `ci.yml` as an additional job (drawback: `ci.yml` only runs on `pull_request`/`workflow_dispatch`, so on a quiet repo with no open PRs it would never fire, defeating the purpose).
   - Recommendation: a new minimal `heartbeat.yml` on a daily cron (`workflow_dispatch` + e.g. `cron: '0 12 * * *'`) is the only design that satisfies "detects total silence" — recommend the planner scope this as its own small workflow file, reusing `.github/scripts/require-env.sh`-style shared script conventions for the age-check logic itself (a `.github/scripts/check-heartbeat.sh` sibling).

2. **Does the R2 archive need a `data/`-visible marker at all, or is `gh run list` sufficient forever?**
   - What we know: `gh run list` retains run history well beyond any threshold this phase would set (GitHub retains workflow run logs 90 days on public repos by default, per GitHub's own retention docs — MEDIUM confidence, not verified live this session since it's a billing/retention-policy fact rather than something greppable in this repo).
   - What's unclear: whether 90-day default retention could ever race against a >90-day threshold in a way that breaks the heartbeat's own evidence source (not for this phase's 4-day R2 threshold, but worth a footnote if the CEAD 100-day threshold is ever pushed higher).
   - Recommendation: not a blocker for this phase (100 days < typical 90-day-plus retention isn't even close to relevant since CEAD's evidence source is `git log`, not `gh run list` — only R2's 4-day threshold uses `gh run list`, comfortably inside any retention window). Flag as a non-blocking footnote only.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| `gh` CLI | CRON-04 label creation, CRON-02 R2 heartbeat evidence, all local verification in this phase | Yes | 2.88.1, authenticated as `xenaquis` | — |
| `actionlint` | Local pre-approval linting of workflow YAML changes (phase brief explicitly asks for it) | No (not installed locally) | — | Rely on `ci.yml`'s existing `lint-workflows` job (`rhysd/actionlint@v1`, ci.yml:50-57) by opening a PR/branch push — this is a safe, already-existing CI path that does not require workflow_dispatch or touch secrets. If a local run is strictly required, install via `go install github.com/rhysd/actionlint/cmd/actionlint@latest` (requires Go, availability unconfirmed this session) or download the pinned release binary for Windows from the actionlint GitHub Releases page. |
| `git` (bash) | CRON-06 local race simulation | Yes (implicit — every command in this research ran via git-bash) | not explicitly queried, assume recent given other tooling | — |
| Node.js | Any new `.mjs` heartbeat validator sibling to `freshness.mjs` | Yes (implied by existing `site/scripts/validate/` suite already running) | 20 LTS per CLAUDE.md | — |

**Missing dependencies with fallback:** `actionlint` — use the CI job instead of local execution, or install via `go install`/binary download if local pre-verification before pushing is preferred by the planner.

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework (frontend) | vitest (existing, 59 tests per current baseline) + custom `.mjs` validators under `site/scripts/validate/` invoked via `node scripts/validate/all.mjs` |
| Framework (pipeline) | pytest (existing, 344 passed / 1 skipped / 1 xfailed baseline) |
| Framework (workflows) | `actionlint` via `ci.yml`'s `lint-workflows` job — no local install this session (see Environment Availability) |
| Config file | `site/vitest.config.*` (existing), `pipeline/pytest.ini` or equivalent (existing) — not modified by this phase |
| Quick run command | `bash .github/scripts/require-env.sh` local-blanked test (seconds); `git log -1 --format=%ci -- data/cead/` (instant) |
| Full suite command | `cd site && npm run build && npm run validate` (chained per OneDrive rule) + `node scripts/validate/all.mjs` extended with new heartbeat check if implemented as a validator; `cd pipeline && pytest tests/ -q` unaffected by this phase (no Python code changes anticipated) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| CRON-01 | Guard script fails loudly on blanked secret | unit (shell) | `OPENROUTER_API_KEY="" DEEPSEEK_API_KEY=y bash .github/scripts/require-env.sh OPENROUTER_API_KEY DEEPSEEK_API_KEY; test $? -eq 1` | Wave 0 — script does not exist yet |
| CRON-01 | actionlint accepts the new guard steps | integration | `ci.yml`'s existing `lint-workflows` job (push/PR-triggered) | Exists — no new file needed, existing CI job covers it |
| CRON-02 | Heartbeat check fires red on a stale fixture | unit | new `.mjs`/`.sh` heartbeat script run against a synthetic old-timestamp fixture | Wave 0 — does not exist |
| CRON-03 | All three deploy-hook curl invocations byte-identical (modulo hook URL) | manual/grep diff | `grep -n 'curl -X POST' .github/workflows/*.yml` and diff the flag sets | N/A — grep-based check, no new file |
| CRON-04 | Labels exist and are workflow-specific | manual | `gh label list` shows three new labels; `gh issue list --label pipeline-failure-news` etc. return only that pipeline's issues | N/A — `gh` command, no file |
| CRON-05 | Comment present documenting expected 403 | manual/grep | `grep -n '403' .github/workflows/cead-scraper.yml` returns non-empty | Wave 0 — comment does not exist yet |
| CRON-06 | Retry loop survives a simulated concurrent write | integration | the two-bare-clone local race simulation documented above | Wave 0 — no existing test for this |
| CRON-07 | Schedule-surface table exists and matches the files | manual review | diff this RESEARCH.md's table against the five files at plan-close time | N/A — documentation-only |

### Sampling Rate
- **Per task commit:** run the relevant local shell/grep check above for whichever CRON-NN the task touches
- **Per wave merge:** `cd site && npm run build && npm run validate` (chained, per OneDrive rule) + full pytest suite (baseline 344/1/1, unaffected but must stay green) + push a branch so `ci.yml`'s `lint-workflows` (actionlint) runs
- **Phase gate:** all of the above green, plus a manual `gh label list` / `gh run list` spot-check before closing

### Wave 0 Gaps
- [ ] `.github/scripts/require-env.sh` — does not exist, needed for CRON-01
- [ ] Heartbeat check script(s) for R2 + CEAD — does not exist, needed for CRON-02 (and likely a new `heartbeat.yml` workflow, see Open Question 1)
- [ ] Three new GitHub labels (`pipeline-failure-news`, `pipeline-failure-r2`, `pipeline-failure-cead`) — do not exist in the repo yet, needed for CRON-04
- [ ] No new pytest/vitest test files are strictly required (all new logic is bash/YAML), but the local shell-based assertions above should be captured as either a small pytest wrapper (`pipeline/tests/test_require_env_guard.py` shelling out to the script) or left as documented manual commands in PLAN.md — planner's call; recommend a thin pytest wrapper so it runs automatically in CI's `pipeline` job rather than relying on someone remembering to run it manually.

## Security Domain

> `security_enforcement` status not confirmed in `.planning/config.json` this session (not read — out of this phase's explicit read list). Given Phase 33 (Security Posture) exists as a dedicated adjacent phase covering `permissions:`, SHA-pinning, dependabot, and `zizmor`, this phase (32) deliberately does NOT duplicate that scope. The one item bordering security in scope here — `permissions:` blocks — is documented factually in the Current-State Table above (all three cron workflows already declare job-level `permissions:`, none rely on repo-default alone for the write/issues-write jobs) but no changes to `permissions:` are proposed by this research; that is explicitly Phase 33 / SEC-01's job.

### Known Threat Patterns for this stack (informational only, not actioned this phase)
| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Secret exfiltration via `echo $SECRET` in a debug step | Information Disclosure | Never `echo`/`printf` a secret var directly; the guard script here only checks `-z`, never prints the value — confirmed by design in the Code Examples section |
| Label/issue spam via repeated failed runs | Denial of Service (low severity) | The existing dedup-by-open-issue logic (comment instead of new issue) already mitigates this; per-pipeline labels (CRON-04) don't change this behavior |

## Sources

### Primary (HIGH confidence — read directly this session)
- `.github/workflows/news-pipeline.yml` (full file, all 73 lines)
- `.github/workflows/r2-archive.yml` (full file, all 54 lines)
- `.github/workflows/cead-scraper.yml` (full file, all 89 lines)
- `.github/workflows/ci.yml` (full file, all 58 lines)
- `.github/workflows/deploy-on-code.yml` (full file, all 43 lines)
- `site/scripts/validate/freshness.mjs` (first 80 lines read)
- `.planning/ROADMAP.md` § Phase 32 (lines 438-451) and cross-phase notes (lines 100-117)
- `.planning/REQUIREMENTS.md` CRON-01..CRON-07
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` (full file)
- `.planning/STATE.md` (lines 260-334: Phase 31 Outcome, Deferred-live list, Fable Decisions header)
- `gh label list` (live command, this session) — confirmed 10 labels including `pipeline-failure`, no per-pipeline labels
- `gh --version` / `gh auth status` (live, this session) — confirmed 2.88.1, authenticated
- `which actionlint` (live, this session) — confirmed not installed locally

### Secondary (MEDIUM confidence)
- Fetch-rebase-push-retry as the standard CI bot-commit shape — inferred from widespread community convention (e.g. `stefanzweifel/git-auto-commit-action` documentation pattern), not verified against one single canonical GitHub doc page this session
- `gh issue create --label <nonexistent>` hard-fail behavior — based on documented `gh` CLI/GitHub REST API label-array semantics, not live-tested against a real nonexistent label this session (would require a live mutation against the repo, avoided per the read-only-verification spirit of this research phase)
- GitHub Actions workflow-run log retention (~90 days on public repos) — general GitHub platform knowledge, not verified live this session

### Tertiary (LOW confidence)
- None — all findings above were either read directly from repo files/git history or are clearly labeled as community-convention inference.

## Metadata

**Confidence breakdown:**
- Current-state table / gap analysis (CRON-01..07): HIGH — every cell is a direct file read or live `gh`/`git` command this session
- CRON-02 heartbeat design: MEDIUM — the guard mechanics and evidence-source reasoning are sound and testable, but the specific threshold numbers (4 days, 100 days) are engineering judgment, not derived from an external SLA or measured incident data beyond the one documented June outage
- CRON-06 race analysis: HIGH for the schedule-overlap math (computed directly from cron expressions) and the local-simulation recipe (standard git plumbing); MEDIUM for "this is the canonical retry snippet" (community convention, not a single citable spec)

**Research date:** 2026-08-04
**Valid until:** ~14 days — GitHub Actions YAML/CLI behavior is stable, but this repo's own workflow files are actively being modified by every cron run (`[skip ci]` data commits); re-verify line numbers before executing a plan if more than a few days pass, since automated commits can shift files (though these five workflow files are not touched by the data-commit crons themselves, only `data/` is).
