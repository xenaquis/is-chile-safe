---
phase: 06-cicd-cloudflare-deployment
plan: "01"
subsystem: github-actions
tags: [ci-cd, cron, github-actions, cloudflare-pages, data-pipeline]
dependency_graph:
  requires: []
  provides: [news-pipeline-cron, cead-scraper-cron, data-change-gated-deploy]
  affects: [pipeline/scrape_news.py, pipeline/scrape_cead.py, cloudflare-pages-deploys]
tech_stack:
  added: []
  patterns: [data-change-gated-commit, env-var-if-gate, concurrency-guard, dry-run-safe-hook]
key_files:
  created:
    - .github/workflows/news-pipeline.yml
    - .github/workflows/cead-scraper.yml
  modified: []
decisions:
  - "Use env: CF_HOOK mapping + env.CF_HOOK != '' in if: (not secrets.* directly) — safer GH Actions pattern per RESEARCH Open Question 1"
  - "timeout-minutes: 60 for CEAD (346 communes x 7 families x ~20 years + inter-batch sleeps exceeds 30min)"
  - "cancel-in-progress: false on both concurrency groups — never cancel a half-finished scrape leaving partial data"
  - "git add data/ (not git add .) — prevents .planning/, docs, and other non-data changes from triggering spurious deploys"
metrics:
  duration: "12m"
  completed: "2026-06-13"
  tasks: 2
  files: 2
requirements: [INFRA-01, INFRA-02]
---

# Phase 06 Plan 01: Cron Workflows (news-pipeline + cead-scraper) Summary

**One-liner:** Two GitHub Actions cron workflows with data-change-gated commits and dry-run-safe Cloudflare Pages Deploy Hook curl via `env.CF_HOOK` pattern.

## What Was Built

### Task 1 — news-pipeline.yml (commit 534b0ed)

6-hourly cron (`0 */6 * * *`) + `workflow_dispatch`. Single `scrape` job on ubuntu-latest: `timeout-minutes: 30`, `permissions: contents: write`, `concurrency: group: news-pipeline, cancel-in-progress: false`. Steps: checkout@v4, setup-python@v5 (3.12), pip install, run `scrape_news.py` with `DEEPSEEK_API_KEY` in step `env:`, commit-if-changed step (`id: commit`) writing `changed=true/false` to `$GITHUB_OUTPUT`, deploy hook curl gated on `steps.commit.outputs.changed == 'true' && env.CF_HOOK != ''` with `CF_HOOK` mapped from `secrets.CF_DEPLOY_HOOK_URL` in a step-level `env:` block.

### Task 2 — cead-scraper.yml (commit 2b3bda3)

Quarterly cron (`0 3 1 1,4,7,10 *`) + `workflow_dispatch`. Mirrors news-pipeline structure exactly except: `timeout-minutes: 60` (CEAD runtime), `concurrency: group: cead-scraper`, runs `scrape_cead.py` (no `DEEPSEEK_API_KEY` — CEAD does not use it), commit message `"data: auto-update CEAD [skip ci]"`. Deploy hook gate identical to news-pipeline.

## Deviations from Plan

None — plan executed exactly as written. The env-var `if:` gate pattern (`env.CF_HOOK != ''`) was already specified in the plan per RESEARCH Open Question 1 resolution.

## Verification Results

- **YAML parse:** Both files pass `python -c "yaml.safe_load(open(p))"` — no syntax errors.
- **actionlint:** Docker not available locally. Deferred to `ci.yml` `lint-workflows` job (plan 06-02) which runs `rhysd/actionlint@v1` — this is the equivalent gate per acceptance criteria.
- **26 grep assertions:** All passed — cron expressions, `workflow_dispatch`, `contents: write`, `timeout-minutes`, scraper entry points, `git add data/`, `git diff --staged --quiet`, `$GITHUB_OUTPUT`, `steps.commit.outputs.changed == 'true'`, `env.CF_HOOK != ''`, secret mappings, concurrency groups.

## Security Audit (STRIDE Compliance)

| Threat ID | Status |
|-----------|--------|
| T-06-01 DEEPSEEK_API_KEY info disclosure | Mitigated: only in step `env:` block, never echoed |
| T-06-02 CF_DEPLOY_HOOK_URL info disclosure | Mitigated: mapped to `CF_HOOK` env var, used only in `curl -X POST "$CF_HOOK"`, never printed |
| T-06-03 GITHUB_TOKEN elevation | Mitigated: `permissions: contents: write` only — no other scopes |
| T-06-04 Pinned action supply chain | Mitigated: `actions/checkout@v4`, `actions/setup-python@v5` — no `@main` or unpinned refs |
| T-06-05 Rebuild loop / build quota | Mitigated: Deploy Hook curl gated on `changed==true`; `git add data/` excludes docs; `[skip ci]` in commit messages |

## Known Stubs

None. Both workflows are complete automation paths; no placeholder or hardcoded values.

## Threat Flags

None. No new network endpoints, auth paths, or schema changes introduced beyond what the plan's threat model already covers.

## Self-Check: PASSED

- `.github/workflows/news-pipeline.yml` — FOUND (commit 534b0ed)
- `.github/workflows/cead-scraper.yml` — FOUND (commit 2b3bda3)
- Both commits verified in `git log --oneline -3`
