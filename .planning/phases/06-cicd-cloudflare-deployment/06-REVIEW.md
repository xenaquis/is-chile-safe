---
phase: 06-cicd-cloudflare-deployment
reviewed: 2026-06-13T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - .github/workflows/news-pipeline.yml
  - .github/workflows/cead-scraper.yml
  - .github/workflows/ci.yml
  - DEPLOYMENT.md
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-06-13
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed three GitHub Actions workflow files and the deployment runbook for Phase 6 (CI/CD +
Cloudflare Pages). The overall architecture is sound: data-change gate logic, concurrency
groups, git identity configuration, and `[skip ci]` belt-and-suspenders are all correctly
implemented. One critical defect exists: the Deploy Hook `if:` guard references `env.CF_HOOK`
before the variable enters scope, which causes the Cloudflare Pages trigger to silently never
fire in either cron workflow. This breaks the primary delivery path for scraped data reaching
production. Three warnings cover missing curl failure detection, a floating action version, and
missing explicit permissions on CI. Two info items cover a misleading dry-run note and minor
curl robustness.

---

## Critical Issues

### CR-01: `env.CF_HOOK` is out of scope in the step `if:` — Deploy Hook never fires

**Files:**
- `.github/workflows/news-pipeline.yml:49`
- `.github/workflows/cead-scraper.yml:47`

**Issue:** In GitHub Actions, the `env` context in a step-level `if:` expression only includes
variables defined at **workflow level** or **job level**. Variables defined inside a step's own
`env:` block are NOT visible to that step's `if:` condition — the `if:` is evaluated before
the step's environment is applied.

Both workflows define `CF_HOOK` exclusively inside the step's `env:` block:

```yaml
# news-pipeline.yml lines 48-52
- name: Trigger Cloudflare Pages deploy
  if: steps.commit.outputs.changed == 'true' && env.CF_HOOK != ''
  env:
    CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}
  run: curl -X POST "$CF_HOOK"
```

At evaluation time, `env.CF_HOOK` resolves to `''` because the step-level env hasn't been
applied yet. The second half of the condition (`env.CF_HOOK != ''`) is always `false`.
Therefore the `curl` step is **permanently skipped**, even when `CF_DEPLOY_HOOK_URL` is set
as a repo secret and data has actually changed. The deploy hook will never be called by
either cron workflow.

**Fix:** Hoist `CF_HOOK` to the job-level `env:` block so it is visible in the `if:`
expression. Apply the same fix to both workflow files.

```yaml
# news-pipeline.yml — add job-level env (after timeout-minutes, before steps)
jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: write
    env:
      CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}   # ← add this

    steps:
      # ... existing steps unchanged ...

      - name: Trigger Cloudflare Pages deploy
        if: steps.commit.outputs.changed == 'true' && env.CF_HOOK != ''
        run: curl -X POST "$CF_HOOK"
        # ↑ Remove the step-level env: block; job-level env is inherited automatically
```

Apply the identical change to `cead-scraper.yml`.

---

## Warnings

### WR-01: `curl` does not fail the job on HTTP error response from Cloudflare

**Files:**
- `.github/workflows/news-pipeline.yml:52`
- `.github/workflows/cead-scraper.yml:50`

**Issue:** `curl -X POST "$CF_HOOK"` exits 0 even when Cloudflare returns a 4xx or 5xx HTTP
status (e.g., invalid/expired hook URL, rate limit, CF outage). The step shows green in GitHub
Actions while the deploy hook silently failed. Operators would not notice the site is out of
date until checking CF Pages manually.

**Fix:** Add `--fail` (exit non-zero on HTTP error) and `--silent --show-error` for clean
output. Consider `--retry 3` for transient CF outages.

```yaml
run: curl --fail --silent --show-error --retry 3 -X POST "$CF_HOOK"
```

---

### WR-02: `rhysd/actionlint` pinned to floating major version `@v1`

**File:** `.github/workflows/ci.yml:53`

**Issue:** `uses: rhysd/actionlint@v1` resolves to whatever the latest `v1.x.y` tag points
to at run time. If a future `v1` minor release introduces a new lint rule or breaking flag
change, CI can start failing (or worse, passing with different semantics) without any change
to this repo. The GitHub Actions security hardening guide recommends pinning third-party
actions to a commit SHA for supply-chain integrity.

**Fix:** Pin to the current release SHA. At time of writing `v1.7.7` is current — verify and
use the corresponding commit SHA:

```yaml
- uses: rhysd/actionlint@v1.7.7   # or @<commit-sha> for full pin
```

---

### WR-03: `ci.yml` has no explicit `permissions:` block — inherits repo default

**File:** `.github/workflows/ci.yml` (job level, all three jobs)

**Issue:** `ci.yml` omits a top-level or per-job `permissions:` declaration. It inherits the
repository's default token permissions. If the repo default is `contents: write` (the GitHub
default for classic repos), the three CI jobs — which only need read access — receive write
permission. A compromised or buggy step in CI could push to the repo. This is the
least-privilege violation most commonly exploited in supply-chain attacks.

The cron workflows correctly declare `permissions: contents: write` only where needed. CI
should explicitly declare read-only permissions.

**Fix:** Add a top-level permissions block to `ci.yml`:

```yaml
# ci.yml — add after the `on:` block
permissions:
  contents: read
```

This scopes all three jobs to read-only without changing their functional behavior.

---

## Info

### IN-01: Dry-run documentation implies a failing scrape is an acceptable dry-run

**File:** `DEPLOYMENT.md:148-149`

**Issue:** Section 8a states: "Attempt to scrape news (exits 1 if `DEEPSEEK_API_KEY` is also
missing — that is fine for a structural dry-run)." If `scrape_news.py` exits 1, GitHub Actions
marks the job as failed and skips all subsequent steps, including the commit step. The
git-commit and push logic is therefore never exercised in this scenario. An operator following
this runbook who has not set `DEEPSEEK_API_KEY` will see a red workflow run and may assume the
commit path was tested — it was not.

**Fix:** Clarify the note to set accurate expectations:

> "If `DEEPSEEK_API_KEY` is missing, the scrape step exits 1 and the job fails — no commit
> or push occurs. To dry-run the git commit/push path, `DEEPSEEK_API_KEY` must be set. You
> can trigger a no-op commit dry-run by ensuring the scraper exits 0 but writes no new data."

---

### IN-02: Deploy Hook branch is `master`; runbook should note branch-mismatch risk

**File:** `DEPLOYMENT.md:95`

**Issue:** Step 5 instructs creating the Deploy Hook with Branch: `master`. This is correct
for the current repo (main branch is `master` per git status). However, the Quick Reference
Checklist (line 244) and DEPLOYMENT.md do not note that if the default branch is ever renamed
to `main` (GitHub's current default for new repos), the Deploy Hook would build from the
wrong branch — silently serving stale content. The CF Pages project connection also defaults
to the production branch, which may differ.

**Fix:** Add a one-line note to the Deploy Hook creation step and the checklist:

> "The branch value (`master`) must match the repo's actual default branch. Verify with
> `git remote show origin | grep 'HEAD branch'` before generating the hook."

---

_Reviewed: 2026-06-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
