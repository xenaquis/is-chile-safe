---
phase: quick-260702-wjr
plan: 01
subsystem: ci-pipeline
tags: [news-cron, cead-scraper, alerting, freshness-validator, deploy-hook]
key-files:
  created:
    - site/scripts/validate/freshness.mjs
  modified:
    - .github/workflows/news-pipeline.yml
    - .github/workflows/cead-scraper.yml
    - site/scripts/validate/all.mjs
decisions:
  - PYTHONPATH=. at job-level env fixes ModuleNotFoundError for all pipeline steps in cead-scraper
  - pipeline-failure GitHub label created manually (not in workflow — label must exist before first alert fires)
  - CEAD 403 from GitHub Actions runner is external/known; PYTHONPATH fix is verified (scraper starts, contacts CEAD, no import error)
  - test_build_enusc_enrichment.py 5 failures are pre-existing (import path issue unrelated to this task)
metrics:
  duration: ~25min
  completed: "2026-07-02"
  tasks: 3
  commits: 4
---

# Quick Task 260702-wjr: News Cron Fix Sequence + Pre-Public Secret Audit

**One-liner:** Fase 25 deployed to prod; news pipeline hardened with GitHub Issue alerting, --retry-all-errors deploy hook, CEAD PYTHONPATH fix, and build-time freshness guard (validator #15).

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | git pull --rebase + push → Cloudflare deploy fired; prod live with Fase 25 + July news | (sync, no new commit) |
| 2A | Alerting: if:failure() step + issues:write permission in both workflow files | 7e7728a |
| 2B | Deploy hook: --retry-all-errors added to news-pipeline.yml curl | c5b0662 |
| 2C | CEAD import fix: PYTHONPATH: . added to cead-scraper.yml job env | 8ca46d7 |
| 3 | Freshness validator #15 created + registered in all.mjs; 15/15 validators pass | b12067b |

## Verification Results

- **Prod /404-test/** → HTTP 404 (Fase 25 404.html deployed, confirmed at 23:36 HSP)
- **/news/ on prod** → h2 "July 2026" heading + 07-xx dated news items visible
- **Validator suite** → 15/15 PASS (freshness: 0.0 days old, generated: 2026-07-03T02:37:35.792618Z)
- **Targeted pytest** → test_classifier.py + test_scrape_cead.py + test_workflow_order.py: 16/16 PASS
- **PYTHONPATH fix** → CEAD scraper imports resolved (no ModuleNotFoundError); run hit CEAD server (403 = external block)
- **DeepSeek json_object** → confirmed at classifier.py lines 195-197 (no duplicate added)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Created pipeline-failure GitHub label**
- **Found during:** Task 2 — CEAD workflow run verification
- **Issue:** Alert step `gh issue create --label pipeline-failure` failed with "label not found"; the label must be created in the repo before the alerting step can use it.
- **Fix:** `gh label create pipeline-failure --color "e11d48"` run manually (not a code commit — label lives in GitHub, not the repo).
- **Files modified:** None (GitHub repo label)

### Known Pre-existing Issues (out of scope)

- `test_build_enusc_enrichment.py` — 5 tests fail with `ModuleNotFoundError: No module named 'build_enusc_enrichment'`. Pre-existing issue (module not on sys.path for this test file). Not related to this task. Added to deferred-items.

### CEAD 403 Note

The CEAD scraper workflow still exits non-zero due to HTTP 403 from `cead.minsegpublica.gob.cl` — the CEAD server blocks GitHub Actions runner IPs. This is an external/known issue, not a regression from our changes. The PYTHONPATH fix is verified: the scraper now starts, imports cleanly, and reaches the CEAD endpoint before failing.

## Self-Check

- [x] freshness.mjs exists at site/scripts/validate/freshness.mjs
- [x] all.mjs contains 'freshness.mjs' in VALIDATORS array
- [x] 4 code commits exist: 7e7728a, c5b0662, 8ca46d7, b12067b
- [x] All commits pushed to origin/master
- [x] 15/15 validators pass

## Self-Check: PASSED
