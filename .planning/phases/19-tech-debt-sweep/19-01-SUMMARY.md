---
phase: 19-tech-debt-sweep
plan: "01"
subsystem: methodology-prose, pipeline-payload
status: complete
tags: [tech-debt, methodology, pipeline, partial-year]
dependency_graph:
  requires: []
  provides: [TD-01-methodology-unweighted, TD-06-partial-year-flag]
  affects: [site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro, pipeline/scrape_cead.py]
tech_stack:
  added: []
  patterns: [tdd-red-green, conventional-commits]
key_files:
  created: []
  modified:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - pipeline/scrape_cead.py
    - pipeline/tests/test_scrape_cead.py
decisions:
  - "Fixed methodology prose to match data.ts unweighted-mean semantics (two locations each in EN+ES)"
  - "partial_year derived from series[year].partial flag; a year is partial if ANY commune record for that year has partial=True"
metrics:
  duration: ~20min
  completed: 2026-06-19
  tasks_completed: 2
  files_changed: 4
---

# Phase 19 Plan 01: Methodology Wording + Map-Payload partial_year Summary

**One-liner:** Fixed unweighted/weighted contradiction in EN+ES methodology prose (two locations each) and added partial_year boolean to build_map_payload output.

## Tasks Completed

| # | Name | Commit | Status |
|---|------|--------|--------|
| 1 | Correct methodology national-mean wording EN+ES (TD-01) | 7aadbd4 | done |
| 2 | Emit partial_year flag in map-payload generator (TD-06) | 65018ae + 5a97832 (RED test) | done |

## Verification Output

### Build + Validators (Task 1)
- Build: green (static generation complete)
- Validators: 12/12 passed (structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo)

### Pipeline pytest (Task 2)
- test_scrape_cead.py: 6 passed (including 2 new partial_year tests)
- Full pipeline suite: 160 passed, 12 warnings (feedparser deprecation, pre-existing)

### Grep verification
- `grep -ci "unweighted" site/src/pages/methodology.astro` → 2 (main paragraph + glossary)
- `grep -in "ponderada por poblaci" site/src/pages/es/metodologia.astro` → 0

## Changes Made

### TD-01: Methodology prose (EN)
- `methodology.astro:192` — "population-weighted mean" → "unweighted mean ... a typical-commune figure"
- `methodology.astro:302` — glossary "National average definition" also fixed from "population-weighted" → "unweighted"

### TD-01: Methodology prose (ES)
- `metodologia.astro:193` — "media ponderada por población" → "media simple (no ponderada) ... no es un promedio per cápita ponderado por población"
- `metodologia.astro:312` — glossary "Definición de promedio nacional" also fixed

### TD-06: partial_year flag
- `scrape_cead.py` build_map_payload: computes `partial_year = any(yr_rec.get("partial", False) for r in records for yr_rec in r["series"] if yr_rec["year"] == year)`
- Returns `partial_year` boolean alongside `generated`, `year`, `comunas`
- TDD: RED commit 5a97832, GREEN commit 65018ae

## Deviations from Plan

**1. [Rule 2 - Missing coverage] Fixed second "ponderada por población" in glossary sections**
- **Found during:** Task 1 grep verification
- **Issue:** The grep `returns 0` condition revealed a second occurrence in the glossary definition list (EN line ~302, ES line ~312) — both also claimed "population-weighted" / "media ponderada por población"
- **Fix:** Updated both glossary definitions to match the corrected main paragraph wording
- **Files modified:** methodology.astro, es/metodologia.astro
- **Included in:** commit 7aadbd4

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes at trust boundaries.

## Self-Check: PASSED

- `site/src/pages/methodology.astro` — exists, contains "unweighted"
- `site/src/pages/es/metodologia.astro` — exists, "ponderada por poblaci" count = 0
- `pipeline/scrape_cead.py` — exists, contains "partial_year"
- Commits 5a97832, 7aadbd4, 65018ae — verified in git log
