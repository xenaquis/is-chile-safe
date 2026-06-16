---
phase: quick-260616-huj
plan: 01
subsystem: crime-ranking-pages
tags: [presentational, i18n, copy, formatting]
dependency_graph:
  requires: []
  provides: [clarified-rate-labels-EN, clarified-rate-labels-ES]
  affects: [crime-ranking pages EN, ranking-delito pages ES]
tech_stack:
  added: []
  patterns: [shared-constants-in-familyDefs, locale-aware-toLocaleString]
key_files:
  created: []
  modified:
    - site/src/lib/familyDefs.ts
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
decisions:
  - Explainer placed after h2 section-heading, before .table-wrapper — maximises proximity to table
  - Column header uses concise form with latestYear interpolated; explainer sentence carries full denuncia detail
  - Style .rate-explainer mirrors .low-pop-footnote treatment (0.85em, var(--muted))
  - Region-breakdown bar values left as Math.round (out-of-scope per plan guardrail)
metrics:
  duration: 12m
  completed: "2026-06-16"
  tasks: 3
  files: 3
---

# Quick Task 260616-huj: Clarify Rate Labels on Crime-Ranking Pages Summary

**One-liner:** Clarified EN/ES crime-ranking rate labels — denuncia-framed column headers, 1-decimal locale-aware formatting, and inline CEAD-attributed explainer paragraph on both ranking page variants.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add shared bilingual rate-explainer strings to familyDefs.ts | 22f3bc8 | site/src/lib/familyDefs.ts |
| 2 | Wire clarified labels, 1-decimal formatting, and inline explainer into both ranking pages | 4be9045 | site/src/pages/crime-ranking/[crime].astro, site/src/pages/es/ranking-delito/[crime].astro |
| 3 | Chained build + validate (OneDrive desync guard) | (no commit — verification only) | — |

## Changes Made

### familyDefs.ts
Appended two new exported constants after `RANKING_METHODOLOGY_ES`:
- `RANKING_RATE_EXPLAINER_EN` — sober English sentence attributing CEAD, noting small/touristic communes can show high rates
- `RANKING_RATE_EXPLAINER_ES` — Spanish mirror in es-CL phrasing

No existing strings were mutated.

### crime-ranking/[crime].astro (EN)
- Import: added `RANKING_RATE_EXPLAINER_EN`
- Column header: `Rate per 100k` → `Reported complaints per 100k residents ({latestYear})`
- Rate cells: `Math.round(row.rate).toLocaleString('en-US')` → `row.rate.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })`
- National mean: same 1-decimal treatment, `per 100k ({latestYear})` suffix kept
- Added `<p class="rate-explainer">{RANKING_RATE_EXPLAINER_EN}</p>` immediately after `<h2>`, before `.table-wrapper`
- Added `.rate-explainer` CSS style (0.85em, var(--muted), margin-bottom, max-width 72ch)
- Region-breakdown bars: unchanged

### es/ranking-delito/[crime].astro (ES)
- Import: added `RANKING_RATE_EXPLAINER_ES`
- Column header: `Tasa por 100k` → `Denuncias por 100.000 hab. ({latestYear})`
- Rate cells: `Math.round(row.rate).toLocaleString('es-CL')` → `row.rate.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 })`
- National mean: same 1-decimal treatment, `por 100k ({latestYear})` suffix kept
- Added `<p class="rate-explainer">{RANKING_RATE_EXPLAINER_ES}</p>` immediately after `<h2>`, before `.table-wrapper`
- Added `.rate-explainer` CSS style (identical to EN)
- Region-breakdown bars: unchanged

## Build + Validate Result

Single chained command from `site/`: `npm run build && npm run validate`

**12/12 validators passed** — structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths, or schema changes introduced. All edits are static copy/formatting.

## Self-Check: PASSED

- site/src/lib/familyDefs.ts: modified, contains RANKING_RATE_EXPLAINER_EN and RANKING_RATE_EXPLAINER_ES
- site/src/pages/crime-ranking/[crime].astro: modified, contains rate-explainer and minimumFractionDigits: 1
- site/src/pages/es/ranking-delito/[crime].astro: modified, contains rate-explainer and minimumFractionDigits: 1
- Commits 22f3bc8 and 4be9045 exist in git log
- 12/12 validators passed including forbidden-language
