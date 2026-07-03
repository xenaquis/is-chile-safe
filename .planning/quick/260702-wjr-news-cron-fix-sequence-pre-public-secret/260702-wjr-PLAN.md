---
phase: quick-260702-wjr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/news-pipeline.yml
  - .github/workflows/cead-scraper.yml
  - site/scripts/validate/freshness.mjs
  - site/scripts/validate/all.mjs
autonomous: true
requirements: [NEWS-CRON-FIX]
must_haves:
  truths:
    - "Fase 25 UI + fresh 07-xx news data is live on ischilesafe.com (deploy-on-code fired)"
    - "A future pipeline failure opens/updates a GitHub Issue instead of failing silently"
    - "The build fails loudly if data/incidents/current.json.generated is > 3 days old"
    - "A Cloudflare deploy hook that returns HTTP 4xx/5xx is retried (not silently dropped)"
    - "cead-scraper.yml runs green (no ModuleNotFoundError: No module named 'pipeline')"
    - "The DeepSeek classifier requests json_object output (already present) and pipeline tests pass"
  artifacts:
    - path: "site/scripts/validate/freshness.mjs"
      provides: "Validator #15 — freshness guard on data/incidents/current.json"
      contains: "current.json"
    - path: "site/scripts/validate/all.mjs"
      provides: "Registers freshness.mjs as validator #15"
      contains: "freshness.mjs"
    - path: ".github/workflows/news-pipeline.yml"
      provides: "if: failure() alerting step + --retry-all-errors deploy hook"
      contains: "retry-all-errors"
    - path: ".github/workflows/cead-scraper.yml"
      provides: "if: failure() alerting step + PYTHONPATH import fix"
      contains: "if: failure()"
  key_links:
    - from: "site/scripts/validate/all.mjs"
      to: "site/scripts/validate/freshness.mjs"
      via: "VALIDATORS array entry"
      pattern: "freshness\\.mjs"
    - from: ".github/workflows/cead-scraper.yml"
      to: "pipeline package import"
      via: "PYTHONPATH or python -m"
      pattern: "PYTHONPATH|python -m pipeline"
---

<objective>
Execute the 6-step news-cron fix sequence from the 07-03 diagnosis, in prescribed
order, one atomic commit per code step. Publishes Fase 25 + fresh data, then hardens
the pipeline against the silent 8-day outage (06-23→06-30) and the secondary failures
(unretried HTTP 400 deploy hook, CEAD import bug).

Purpose: Turn a silent, unrecoverable outage into a loud, self-alerting, self-guarding
pipeline — and get the already-built Fase 25 work into production.

Output: Fase 25 live on prod; alerting + freshness guard + resilient deploy hook +
CEAD import fix committed and verified.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/NEWS-CRON-DIAGNOSIS-260703.md

<key_facts>
Verified during planning (do not re-derive):
- Local repo divergence at planning time: 47 ahead / 17 behind origin/master. The 17
  remote commits are `data:` auto-updates (news/CEAD). Local 47 = all of Fase 25.
- Local data/incidents/current.json.generated = 2026-06-20 (STALE). After `git pull
  --rebase` it becomes the fresh remote version (~07-03) — this is WHY sync must run
  FIRST, before the freshness validator is exercised locally.
- `pipeline/` IS a proper Python package (pipeline/__init__.py and
  pipeline/news/__init__.py both exist) → both `python -m pipeline.scrape_cead` and
  a job-level `PYTHONPATH: .` are valid fixes for the CEAD ModuleNotFoundError.
- STEP 6 IS ALREADY DONE: pipeline/news/classifier.py lines 196-197 already add
  `kwargs["response_format"] = {"type": "json_object"}` for the deepseek provider
  (committed in f3f7e6a as part of Fase 25). Step 6 therefore reduces to VERIFY-ONLY
  + run pytest. Do NOT add a duplicate line and do NOT create an empty commit.
- Both workflow jobs already have a job-level `env:` block containing
  `CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}` — add PYTHONPATH alongside it.
- Existing validators are numbered #1–#14 (figure-registry=#13, avs-b-budget=#14).
  The new freshness validator is #15.
- OneDrive gotcha: dist/ vanishes between separate processes — build+validate MUST
  chain in ONE command: `cd site && npm run build && npm run validate`.
</key_facts>

<interfaces>
Existing validator pattern to mirror (from site/scripts/validate/figure-registry.mjs):
- ESM module, run standalone via `node scripts/validate/<name>.mjs`.
- Path resolution:
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const SITE_ROOT = path.resolve(__dirname, '../..');
    const REPO_ROOT = path.resolve(SITE_ROOT, '..');
- Reads a repo data file with readFileSync/existsSync (offline, no dist/ needed).
- Exit 0 on PASS (console.log), exit 1 on FAIL (console.error).

all.mjs registration surface:
- VALIDATORS is a flat array of filename strings, executed in order via spawnSync.
- The header block comment enumerates validators 1..N — extend it to include #15.

Data file shape (data/incidents/current.json): top-level object with a
`generated` field = ISO-8601 UTC timestamp string (e.g. "2026-06-20T19:21:39.576863Z").
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: SYNC + DEPLOY Fase 25 (Step 1 — no new authored commit)</name>
  <files>(git sync only — publishes existing 47 local commits; touches no source file authored here)</files>
  <action>
    Run `git pull --rebase origin master`. The 17 remote commits are `data:`
    auto-updates; the only plausible conflict is data/incidents/current.json — if it
    conflicts, REMOTE version wins (`git checkout --theirs data/incidents/current.json`
    then `git add`), because remote holds the fresh ~07-03 data. Do NOT touch Fase 25
    source commits during the rebase.

    After a clean rebase, run `git push`. This publishes Fase 25 + fresh data and fires
    the Cloudflare deploy-on-code hook.

    Then poll prod POLITELY (Cloudflare build takes a few minutes — wait ~60s between
    polls, do not hammer):
      - `curl -I https://ischilesafe.com/404-test/` MUST return HTTP 404 (Fase 25
        pending-verification carry-over from MEMORY).
      - Fetch https://ischilesafe.com/news/ and confirm the NEW layout (an <h2> per
        month + chips/date-family markup) AND that July (07-xx) dates appear — proving
        fresh data shipped, not the local 06-20 snapshot.

    Do NOT create a new commit in this task — it only publishes existing commits.
  </action>
  <verify>
    <automated>curl -sI https://ischilesafe.com/404-test/ | findstr /C:"404"</automated>
    <human-check>https://ischilesafe.com/news/ shows month <h2> headings + chips with July (07-xx) dates</human-check>
  </verify>
  <done>origin/master and local master are in sync; prod serves Fase 25 UI with July news data; /404-test/ returns 404.</done>
</task>

<task type="auto">
  <name>Task 2: Workflow hardening — alerting, deploy-hook retry, CEAD import (Steps 2, 4, 5 — 3 commits)</name>
  <files>.github/workflows/news-pipeline.yml, .github/workflows/cead-scraper.yml</files>
  <action>
    Do these as THREE separate atomic commits, in this order.

    COMMIT A (Step 2 — alerting, both files): Append a final step to the `scrape` job
    in BOTH news-pipeline.yml and cead-scraper.yml with `if: failure()`. The step needs
    issue-write permission — add `issues: write` to each job's existing `permissions:`
    block (which currently has `contents: write`). The step runs a shell script with
    `env: GH_TOKEN: ${{ github.token }}` that: (1) searches for an OPEN issue with label
    `pipeline-failure` via `gh issue list --label pipeline-failure --state open`; (2) if
    one exists, `gh issue comment <n>` with the run URL; else `gh issue create --label
    pipeline-failure --title "[pipeline] <workflow-name> failed on $(date -u +%F)"
    --body` including `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}`.
    Use the real workflow name per file ("News Pipeline" / "CEAD Scraper"). Rationale:
    32 runs failed silently over 8 days. Commit: `ci: alert via GitHub Issue on pipeline failure`.

    COMMIT B (Step 4 — deploy hook, news file only): In news-pipeline.yml, change the
    "Trigger Cloudflare Pages deploy" step's curl from
    `--fail --silent --show-error --retry 3` to
    `--fail --silent --show-error --retry 5 --retry-all-errors`. The 07-02 HTTP 400 was
    not retried because `--retry` alone covers only network/transient errors, not HTTP
    4xx/5xx. Commit: `ci: retry cloudflare deploy hook on HTTP errors (--retry-all-errors)`.

    COMMIT C (Step 5 — CEAD import fix, cead file only): Fix
    `ModuleNotFoundError: No module named 'pipeline'`. Add `PYTHONPATH: .` to the
    `scrape` job's existing job-level `env:` block (next to CF_HOOK) — this fixes ALL
    python steps in the job (scrape_cead + the ENUSC/composite/map steps) at once.
    (Equivalent per locked decision: convert each `python pipeline/X.py` to
    `python -m pipeline.X`; prefer the single PYTHONPATH env for minimal diff.) Do NOT
    touch classification logic or the rolling window. Commit: `fix(ci): set PYTHONPATH so cead-scraper resolves the pipeline package`.

    After committing all three, `git push`, then VERIFY the CEAD fix against the updated
    workflow on master (see verify). Do not wait for cron.
  </action>
  <verify>
    <automated>gh workflow run cead-scraper.yml && gh run watch $(gh run list --workflow=cead-scraper.yml --limit 1 --json databaseId --jq ".[0].databaseId") --exit-status</automated>
    <human-check>Both workflow files contain an `if: failure()` step with `issues: write` permission; news-pipeline curl uses `--retry-all-errors`; the manual cead-scraper run completes green with no ModuleNotFoundError.</human-check>
  </verify>
  <done>Three commits pushed; `gh workflow run cead-scraper.yml` completes successfully (green); alerting steps present in both files; news deploy-hook uses --retry-all-errors.</done>
</task>

<task type="auto">
  <name>Task 3: Freshness validator #15 + DeepSeek json verify (Steps 3, 6 — 1 commit + verify)</name>
  <files>site/scripts/validate/freshness.mjs, site/scripts/validate/all.mjs, pipeline/news/classifier.py</files>
  <action>
    STEP 3 (freshness guard — 1 commit): Create site/scripts/validate/freshness.mjs
    following the figure-registry.mjs pattern EXACTLY (ESM, __dirname → SITE_ROOT →
    REPO_ROOT resolution, readFileSync/existsSync, exit 0 PASS / exit 1 FAIL). It reads
    `<REPO_ROOT>/data/incidents/current.json`, parses the `generated` ISO timestamp, and
    computes age in days vs Date.now(). If the file is missing, or `generated` is absent/
    unparseable, or age > 3 days → console.error a FAIL message that explicitly says the
    news cron is probably down and links `.planning/NEWS-CRON-DIAGNOSIS-260703.md`, then
    `process.exit(1)`. Otherwise console.log PASS with the age in days and exit 0.

    Register it as validator #15 in site/scripts/validate/all.mjs: append `'freshness.mjs'`
    to the VALIDATORS array AND add a `15. freshness.mjs — data/incidents/current.json <= 3 days old`
    line to the header comment block (currently enumerates 1..14). Keep it LAST in the array.

    Validate the whole thing in ONE chained command (OneDrive dist/ gotcha):
    `cd site && npm run build && npm run validate`. Because Task 1 already rebased the
    fresh ~07-03 current.json into local, validator #15 must PASS. Commit:
    `feat(validate): add freshness guard (#15) failing build if news data > 3 days stale`.

    STEP 6 (DeepSeek json — VERIFY ONLY, no commit): Confirm pipeline/news/classifier.py
    already sets `response_format={"type": "json_object"}` for the deepseek provider
    (it does — lines ~196-197). Do NOT add a duplicate and do NOT create an empty commit.
    Run the pipeline test suite to confirm nothing regressed:
    `python -m pytest pipeline/tests/ -q` (targets include test_classifier.py,
    test_scrape_cead.py, test_workflow_order.py).

    Push after the freshness commit.
  </action>
  <verify>
    <automated>cd site && npm run build && npm run validate</automated>
    <automated>python -m pytest pipeline/tests/ -q</automated>
  </verify>
  <done>freshness.mjs created and registered as #15; `npm run build && npm run validate` passes with freshness PASS; pipeline pytest suite green; classifier json_object confirmed present (no new commit for step 6).</done>
</task>

</tasks>

<verification>
- Prod live: /404-test/ → 404; /news/ shows July dates in the new month/chips layout.
- `git status` clean; local and origin/master in sync after final push.
- `gh workflow run cead-scraper.yml` completes green (import fix proven).
- Both workflows contain an `if: failure()` alerting step with `issues: write`.
- news-pipeline deploy hook uses `--retry-all-errors`.
- Validator suite (15 validators) passes via the single chained build+validate command.
- `python -m pytest pipeline/tests/` passes.
</verification>

<success_criteria>
All 6 diagnosis steps executed in order with one atomic commit per code step (Step 1 =
sync/publish, Steps 2/4/5 = 3 workflow commits, Step 3 = 1 validator commit, Step 6 =
verify-only). Fase 25 is live; the pipeline now alerts on failure, guards data freshness
at build time, retries the deploy hook on HTTP errors, and the CEAD scraper runs green.
No classification logic or rolling-window changes; no attempt to recover the lost
06-23..06-28 window.
</success_criteria>

<output>
Create `.planning/quick/260702-wjr-news-cron-fix-sequence-pre-public-secret/260702-wjr-SUMMARY.md` when done.
</output>
