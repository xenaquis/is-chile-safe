---
phase: 32-cron-consistency
plan: 02
subsystem: ci-cd
tags: [github-actions, workflows, deploy-hook, labels, cron]
dependency-graph:
  requires: ["32-01"]
  provides: ["per-pipeline-alert-labels", "post-commit-deploy-hook-guard", "byte-identical-deploy-curl"]
  affects: [".github/workflows/news-pipeline.yml", ".github/workflows/cead-scraper.yml", ".github/workflows/r2-archive.yml", ".github/workflows/deploy-on-code.yml"]
tech-stack:
  added: []
  patterns: ["post-commit secret guard for publish-only failure modes (F-84)", "hoisted continue-on-error label-creation step separate from alert step (F-87)"]
key-files:
  created: []
  modified:
    - .github/workflows/news-pipeline.yml
    - .github/workflows/cead-scraper.yml
    - .github/workflows/r2-archive.yml
    - .github/workflows/deploy-on-code.yml
decisions:
  - "CF_DEPLOY_HOOK_URL guard placed AFTER 'Commit data if changed' in news-pipeline.yml and cead-scraper.yml (F-84), never first-step, so a rotated deploy hook cannot also halt scraping/committing"
  - "gh label create isolated into its own if: failure() + continue-on-error: true step, never the first line of the alert step (F-87)"
  - "All four per-pipeline labels for this wave (pipeline-failure-news, pipeline-failure-cead, pipeline-failure-r2) created via gh label create --force BEFORE the workflow files referencing them were committed"
metrics:
  duration: "~25 minutes"
  completed: "2026-08-04"
---

# Phase 32 Plan 02: Cron secret-guard split + per-pipeline alert labels Summary

Rewrote the four secret-consuming GitHub Actions workflows so a rotated `CF_DEPLOY_HOOK_URL`
can no longer also stop news/CEAD data collection, and split failure-alert label creation
into its own non-fatal step so a transient `gh` error can't swallow the original alert.

## What Was Built

**Task 1** — Created `pipeline-failure-news` and `pipeline-failure-cead` labels, then
replaced `news-pipeline.yml` and `cead-scraper.yml` in full with the plan's exact YAML:
- `fetch-depth: 0` added to checkout (needed by `push-with-rebase.sh`'s rebase, CRON-06)
- Scrape-only secrets (`OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`) guarded first-step via
  `require-env.sh`; `CF_DEPLOY_HOOK_URL` (aliased `CF_HOOK`) guarded in a new, separate
  "Guard deploy hook" step placed AFTER "Commit data if changed" (F-84)
- `git push` replaced with `bash .github/scripts/push-with-rebase.sh master`
- Curl call unified: `--retry 3 --retry-all-errors --max-time 60` (was `--retry 5` in
  news-pipeline, `--retry 3` with no `--max-time` in cead-scraper)
- `env.CF_HOOK != ''` conditional removed from the deploy step's `if:` — an empty hook is
  now a hard failure at its own guard step, not a silent skip
- `gh label create pipeline-failure-{news,cead}` hoisted into its own
  `if: failure()` + `continue-on-error: true` step, ahead of the alert-issue step
- cead-scraper.yml gained a header comment documenting the expected HTTP 403 on Actions
  runner IPs (CRON-05) and an alert body disambiguating expected-403 vs. real regression
- Relabeled the pre-existing orphaned issue #2 with `pipeline-failure-cead` so the new
  per-pipeline dedup query finds it

**Task 2** — Created `pipeline-failure-r2` label, then replaced `r2-archive.yml` and
`deploy-on-code.yml`:
- r2-archive.yml: all four R2 credentials guarded first-step (no collect/publish split to
  protect, so F-84 does not apply); label-creation hoisted the same way
- deploy-on-code.yml: removed the old silent "dry-run mode" skip on an empty hook — now a
  hard failure via `require-env.sh CF_HOOK`; added the `checkout` step needed to reach the
  shared guard script; curl unified to the canonical byte-identical form; guard stays
  first-step (F-84 explicitly does not apply — the entire job IS the deploy)

## Verification (measured)

1. `bash .github/scripts/lint-workflows.sh .github/workflows/*.yml` → canary fired
   correctly (SC2034 + SC2086 both present, instrument armed), **exit 0**, zero real
   findings across all five real workflow files.
2. CRON-03 byte-identity gate:
   `grep -h "curl -X POST" news-pipeline.yml cead-scraper.yml deploy-on-code.yml | sort -u | wc -l`
   → **1**. Mutation proof executed live this session: flipped cead-scraper.yml's
   `--retry 3` to `--retry 5` → count became **2** (gate went red); restored via
   `git checkout -- .github/workflows/cead-scraper.yml` → count returned to **1** (gate
   green again). Gate observed both red and green, not merely asserted.
3. `cd pipeline && python -m pytest tests/ -q` → **366 passed, 1 skipped, 1 xfailed**
   (exact match to the required baseline; this wave adds no tests).
4. `gh label list --json name --jq '.[].name'` → `pipeline-failure`,
   `pipeline-failure-cead`, `pipeline-failure-news`, `pipeline-failure-r2` all present
   (plus repo defaults). `gh issue list --label pipeline-failure-cead --state open --json
   number --jq '.[0].number'` → `2` (pre-existing orphan, now correctly relabeled).
5. Guard-order gate (Task 1's automated verify): in both news-pipeline.yml and
   cead-scraper.yml, the line number of "Commit data if changed" (60, 74 respectively) is
   lower than "Guard deploy hook" (80, 93 respectively) — guard runs strictly after commit.

## Diff review (manual, per instructions)

Diffed all four new files against `git show HEAD:<path>` (pre-Task-1 content) line by
line. Confirmed the ONLY removals across all four files were the intended ones: the old
`env.CF_HOOK != ''` `if:` clauses, the old inline dry-run skip block in
deploy-on-code.yml, and the old single generic `pipeline-failure` label references
(replaced by dual `--label pipeline-failure-X --label pipeline-failure`). No
`concurrency` group, `permissions` block, `timeout-minutes`, `continue-on-error` on the
four CEAD enrichment steps, `PYTHONPATH: .`, `ARCHIVE_MAX_FETCH`, or `@v7` action version
was lost.

## Deviations from Plan

None — plan executed exactly as written. All four workflow files match the plan's
`<interfaces>` YAML block byte-for-byte (verified by diff during execution).

## Self-Check

- `.github/workflows/news-pipeline.yml` — FOUND
- `.github/workflows/cead-scraper.yml` — FOUND
- `.github/workflows/r2-archive.yml` — FOUND
- `.github/workflows/deploy-on-code.yml` — FOUND
- Commit `ecbe24c` (Task 1) — FOUND in `git log --oneline`
- Commit `2f5c15c` (Task 2) — FOUND in `git log --oneline`

## Self-Check: PASSED
