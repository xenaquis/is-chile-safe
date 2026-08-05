---
phase: 32-cron-consistency
plan: 03
subsystem: ci-cd / monitoring
tags: [github-actions, cron, heartbeat, monitoring, deployment-docs]
dependency-graph:
  requires: [32-01, 32-02]
  provides: [heartbeat.yml, pipeline-failure-heartbeat-label, deployment-cadence-table]
  affects: [.github/workflows/heartbeat.yml, DEPLOYMENT.md]
tech-stack:
  added: []
  patterns: ["independent daily heartbeat workflow watching sibling cron cadences via gh run list / git log / current.json evidence"]
key-files:
  created:
    - .github/workflows/heartbeat.yml
  modified:
    - DEPLOYMENT.md
decisions:
  - "actions: read added to heartbeat.yml permissions (closes premortem finding 1, CRITICAL) -- without it gh run list 403s on first scheduled run"
  - "all three cadences (news/r2/cead) checked independently via if: '!cancelled()' (F-88)"
  - "R2 evidence query filtered to --status success, conclusion field included (F-89)"
  - "news check python3 -c uses encoding='utf-8' explicitly -- real Windows cp1252 bug found and fixed by execution this session"
  - "DEPLOYMENT.md cadence table replaced with six-row audit, CRON-06 claim narrowed to 'no SILENT lost update' (F-90), clustering-audit note documents Phase 26 NO-GO / Phase 28 faceting-only (no cron shape change)"
metrics:
  duration: "~35 minutes"
  completed: "2026-08-04"
---

# Phase 32 Plan 03: Pipeline Heartbeat Workflow + DEPLOYMENT.md Cadence Audit Summary

Final wave of Phase 32: created `.github/workflows/heartbeat.yml`, an independently
scheduled daily workflow that watches all three data-cron cadences (news, R2, CEAD) and
alerts via a dedicated GitHub Issue label when any goes stale; replaced
DEPLOYMENT.md's four-row "Workflow Cadences" table with a six-row audited table covering
every workflow file in the repo, plus narrowed CRON-06/CRON-07 claims per the Fable
review's binding decisions (F-83a/F-83c/F-84/F-87/F-88/F-89/F-90/F-91).

## Tasks Completed

### Task 1: Create heartbeat.yml and the fourth per-pipeline label
Created `.github/workflows/heartbeat.yml` verbatim per the plan's interfaces block:
`permissions: actions: read` (alongside `contents: read`, `issues: write`), three
independent check steps (`if: '!cancelled()'` on the CEAD and news steps), R2 evidence
query filtered to `--status success` with `conclusion` in the JSON fields, and the
`encoding='utf-8'` fix in the news check's `python3 -c` one-liner. Created the fourth
per-pipeline label `pipeline-failure-heartbeat` via `gh label create`.

Commit: `bef88b1`

### Task 2: DEPLOYMENT.md cadence table replacement + full phase-close gate
Replaced DEPLOYMENT.md's "### Workflow Cadences" section with the six-row table
(News Pipeline, R2 Research Archive, CEAD Scraper, Pipeline Heartbeat, Deploy on Code
Push, CI), the narrowed CRON-06 claim, and the clustering-audit note. Ran the full
phase-close verification (measured results below).

Commit: `a68483b`

## Measured Verification Results

1. **`bash .github/scripts/lint-workflows.sh .github/workflows/heartbeat.yml`** (Task 1)
   and **`bash .github/scripts/lint-workflows.sh .github/workflows/*.yml`** (all six
   files, Task 2 gate) — canary fired correctly (SC2034 + SC2086 both present,
   instrument armed), exit 0, zero findings against real content both times.

2. **`grep -c` checks on heartbeat.yml:** `actions: read` = 2, `if: '!cancelled()'` = 3,
   `check-heartbeat.sh news` = 1, `check-heartbeat.sh r2` = 1, `check-heartbeat.sh cead`
   = 1, `encoding='utf-8'` = 1. All three cadences wired.

3. **`gh label list`** — five `pipeline-failure*` labels present:
   `pipeline-failure`, `pipeline-failure-cead`, `pipeline-failure-news`,
   `pipeline-failure-r2`, `pipeline-failure-heartbeat`.

4. **Directory-iteration gate** (`.github/workflows/` vs `DEPLOYMENT.md` table) —
   `PASS: all 6 workflow files present in DEPLOYMENT.md table`.

5. **`cd site && npm run build && npm run validate`** (chained per OneDrive rule) —
   `16/16 validators passed`, including `freshness: data/incidents/current.json is 0.2
   days old` (no F-19 exclusion needed; data was fresh at execution time).

6. **`cd site && npx vitest run`** — `Test Files 6 passed (6)`, `Tests 59 passed (59)`.
   Matches expected 59.

7. **`cd pipeline && python -m pytest tests/ -q`** — `366 passed, 1 skipped, 1 xfailed`.
   Exact match to the plan's expected baseline (344 pre-existing + 20 in
   `test_workflow_guards.py` + 2 in `test_push_race.py`).

8. **`npx astro check`** (site) — `4 errors, 0 warnings, 43 hints`. All 4 errors
   confirmed at `ComparatorPairsLinks.astro:28` (`ts(7031)` implicit-any on
   `nameB`/`nameA`/`cutB`/`cutA` binding elements) — the documented pre-existing
   baseline, unchanged by this phase (no `.astro` file touched).

All six phase-close gates are green at their documented baselines exactly as specified
in the plan. No number was adjusted to match an observed result.

## Deviations from Plan

None — plan executed exactly as written. The one deviation flagged in the plan text
itself (the `encoding='utf-8'` fix for the Windows cp1252 bug) was already applied in
the plan's own interfaces block content, not something this execution needed to
additionally correct.

## Self-Check: PASSED

- FOUND: `.github/workflows/heartbeat.yml`
- FOUND: commit `bef88b1` in `git log --oneline --all`
- FOUND: commit `a68483b` in `git log --oneline --all`
- FOUND: `pipeline-failure-heartbeat` label in `gh label list`
- FOUND: "### Workflow Cadences (CRON-07, audited 2026-08-04, Phase 32)" heading in `DEPLOYMENT.md`
