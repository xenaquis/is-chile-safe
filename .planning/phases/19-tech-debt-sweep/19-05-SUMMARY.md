---
phase: 19-tech-debt-sweep
plan: "05"
subsystem: frontend + pipeline
status: complete
tags: [tech-debt, placeholder, i18n, schema, ci-assertion, testing]
dependency_graph:
  requires: ["19-04"]
  provides: [TD-02, TD-07]
  affects: [site/src/components/MapPlaceholderSlot.astro, site/src/config/i18n.ts, pipeline/shared/schema.py]
tech_stack:
  added: []
  patterns:
    - TypedDict for pipeline schema by_family (strict Pydantic v2 validation)
    - Dynamic year range derived from new Date().getFullYear()
key_files:
  created: []
  modified:
    - site/src/components/MapPlaceholderSlot.astro
    - site/src/config/i18n.ts
    - pipeline/shared/schema.py
    - pipeline/tests/test_schema.py
    - pipeline/tests/test_centroids.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_dedup.py
    - pipeline/tests/test_feeds.py
    - pipeline/tests/test_store.py
    - pipeline/tests/conftest.py
    - site/src/components/map/FiltersRow.tsx
    - .planning/milestones/v1.0-phases/04-editorial-pages-adsense/04-VALIDATION.md
    - .planning/milestones/v1.0-phases/05-rss-news-pipeline/05-VALIDATION.md
    - .planning/milestones/v1.0-phases/06-cicd-cloudflare-deployment/06-VALIDATION.md
decisions:
  - "Replace MapPlaceholderSlot with static live-map CTA (no Leaflet island on editorial pages)"
  - "ByFamily TypedDict strict keys cause Pydantic to require all 7 keys in conftest fixture — auto-fixed"
  - "AVAILABLE_YEARS upper bound derived from new Date().getFullYear() (not hardcoded 2025)"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_changed: 14
---

# Phase 19 Plan 05: Tech-Debt Sweep TD-02 + TD-07 Summary

**One-liner:** Retired stale map placeholder with neutral live-map CTA; added FAMILY_KEYS CI assertion + ByFamily TypedDict; cleaned Wave-1 skipif cruft; reconciled nyquist flags.

## Tasks Completed

| # | Name | Commit | Key files |
|---|------|--------|-----------|
| 1 | Remove stale map placeholder; link to live map (TD-02) | 7fe5aa5 | MapPlaceholderSlot.astro, i18n.ts |
| 2 (RED) | Failing tests for FAMILY_KEYS assertion + ByFamily | aa42cf7 | test_schema.py |
| 2 (GREEN) | FAMILY_KEYS CI assertion + typed by_family + skipif cleanup | c603129 | schema.py, 5 test files, conftest.py |
| 3 | Dynamic AVAILABLE_YEARS + reconcile nyquist flags | 4bde912 | FiltersRow.tsx, 3 VALIDATION.md |

## Verification

- Build: 791 pages built
- Validators: 12/12 passed (all validators green)
- pytest: 170/170 passed, 0 skipped, 0 unexpected skips
- Grep gates:
  - `map_placeholder_text` count in i18n.ts: 0
  - "coming soon" / "disponible proximamente" in dist: 0 hits
  - `/map/` refs in MapPlaceholderSlot.astro: 2
  - `2025-i` / `length: 21` in FiltersRow.tsx: 0
  - `nyquist_compliant: false` in phases 04-06: 0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated conftest fixture to satisfy strict ByFamily TypedDict**
- **Found during:** Task 2 GREEN phase
- **Issue:** `sample_commune_dict` fixture used `by_family: {}` — Pydantic v2 TypedDict validation requires all 7 keys to be present
- **Fix:** Updated conftest.py to provide all 7 family keys (all `None`) in the fixture's series entry
- **Files modified:** `pipeline/tests/conftest.py`
- **Commit:** c603129

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes at trust boundaries introduced.

## Self-Check: PASSED

- MapPlaceholderSlot.astro: found, contains `/map/` and `/es/mapa/`
- i18n.ts: `map_placeholder_text` removed, `map_cta_label` added
- schema.py: `FAMILY_KEYS_CANONICAL` and `ByFamily` present
- test_schema.py: 3 new CI-assertion tests confirmed passing
- FiltersRow.tsx: `CEAD_EARLIEST_YEAR` + dynamic `AVAILABLE_YEARS` present
- Commits 7fe5aa5, aa42cf7, c603129, 4bde912 all exist in git log
