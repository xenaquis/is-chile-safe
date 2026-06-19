---
phase: 19-tech-debt-sweep
plan: "06"
subsystem: i18n
tags: [BIL-04, i18n, tech-debt, bilingual]
dependency_graph:
  requires: ["19-03"]
  provides: ["BIL-04"]
  affects: ["commune pages", "crime pages", "crime-ranking pages", "CookieConsent"]
tech_stack:
  added: []
  patterns: ["i18n key extraction", "EN_STRINGS/ES_STRINGS single source of truth"]
key_files:
  created: []
  modified:
    - site/src/config/i18n.ts
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
    - site/src/components/CookieConsent.astro
decisions:
  - "cookie_banner_text trimmed to prefix-only so the privacy link renders inline without duplication"
  - "EN-only pages (crime, crime-ranking) use EN_STRINGS directly; ES-only pages use ES_STRINGS directly"
  - "crime-ranking th_rate_per_100k keeps ({latestYear}) interpolation inline since the key is a label not a sentence"
metrics:
  duration: "~15 min"
  completed: "2026-06-19"
  tasks_completed: 2
  files_modified: 8
---

# Phase 19 Plan 06: BIL-04 — i18n String Extraction Summary

**One-liner:** Extracted commune section headings, crime/ranking table headers, footnotes, and cookie-consent strings from per-locale inline literals to i18n.ts as single source of truth.

## Status: COMPLETE

## Tasks

### Task 1: Add i18n keys + wire commune/crime/crime-ranking headings + table headers
**Commit:** 011cff6

Added 11 new keys to `I18nStrings` interface and both `EN_STRINGS`/`ES_STRINGS`:
- `map_spoke_heading`, `map_spoke_cta` ({name} placeholder)
- `similar_communes_heading`, `similar_communes_intro` ({region} placeholder)
- `crime_type_heading`
- `th_rank`, `th_commune`, `th_region`, `th_rate_per_100k`, `th_trend`
- `low_pop_footnote`

Pages updated to use `t.*`:
- `commune/[slug].astro` and `es/comuna/[slug].astro`: section headings, CTA, intro paragraph
- `crime/[family].astro` and `es/delito/[family].astro`: table headers + low-pop footnote
- `crime-ranking/[crime].astro` and `es/ranking-delito/[crime].astro`: table headers + low-pop footnote

### Task 2: Source CookieConsent strings from i18n.ts
**Commit:** 20d0dc3

Replaced 4 inline locale ternaries in `CookieConsent.astro` with `EN_STRINGS`/`ES_STRINGS` import and `t.*` references. `privacyHref` per-locale URL ternary retained. `is:inline` localStorage script untouched.

## Verification

- `grep -c "map_spoke_heading\|similar_communes_heading\|crime_type_heading" site/src/config/i18n.ts` → 9 (interface + EN + ES)
- `grep -c "View on Map" "site/src/pages/commune/[slug].astro"` → 0
- `grep -c "cookie_banner_text\|cookie_banner_accept\|cookie_banner_reject" site/src/components/CookieConsent.astro` → 3
- `grep -c "We use cookies to serve ads" site/src/components/CookieConsent.astro` → 0
- Build: green
- Validators: 12/12 PASSED

## Deviations from Plan

### Auto-adjustments (not bugs)

**1. cookie_banner_text value trimmed**
- Found during Task 2
- Issue: Existing `cookie_banner_text` in i18n.ts ended with "See our Privacy Policy." — rendering it alongside a separate `{t.footer_privacy}` link would duplicate "Privacy Policy" in output.
- Fix: Trimmed both EN and ES values to the prefix "See our" / "Ver nuestra" so the inline link renders the label cleanly.
- Files modified: `site/src/config/i18n.ts`

**2. th_rate_per_100k keeps ({latestYear}) inline in crime-ranking**
- The crime-ranking page has a more specific column header "Reported complaints per 100k residents ({latestYear})". Rather than create a second key for this variant, the key stores the generic label "Rate per 100k" / "Tasa por 100k" and `({latestYear})` is appended inline, consistent with how other year-bearing headings work.

## Known Stubs

None.

## Threat Flags

None — all changes are static string substitutions at build time; no new trust boundaries.

## Self-Check: PASSED

- Commits exist: 011cff6, 20d0dc3 ✓
- All 8 modified files staged and committed ✓
- 12/12 validators passed ✓
- Hardcoded EN literals removed from ES page sources ✓
