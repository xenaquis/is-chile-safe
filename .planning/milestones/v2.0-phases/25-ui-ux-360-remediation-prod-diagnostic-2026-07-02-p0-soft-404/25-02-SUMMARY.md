---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
plan: "02"
subsystem: map-panel / number-formatting
tags: [formatting, i18n, locale, map-panel, year-badge, tooltip, tdd]
dependency_graph:
  requires: [25-01]
  provides: [formatNumber-helper, year-badges, map-panel-locale-numbers]
  affects: [ResultPanel, Legend, CommuneRankingTable, ComparableCommune]
tech_stack:
  added: [vitest@4.1.9]
  patterns: [single-locale-formatter, inline-year-badge, reuse-RateTooltipReact]
key_files:
  created:
    - site/src/lib/formatNumber.ts
    - site/src/lib/formatNumber.test.ts
  modified:
    - site/src/components/map/ResultPanel.tsx
    - site/src/components/map/Legend.tsx
    - site/src/components/CommuneRankingTable.astro
    - site/src/components/ComparableCommune.astro
    - site/src/components/map/map.css
decisions:
  - formatRate wraps toLocaleString with locale map; formatDecimal adds fraction digits
  - Legend.tsx local fmt() redirects to formatRate (keeps local function signature, avoids ripple)
  - Year-mismatch tooltip reuses RateTooltipReact details/summary pattern; copy inline (no i18n.ts edit)
  - Plural fix was already correct in original code; noted as confirmed-not-changed
metrics:
  duration: "~20 minutes"
  completed: "2026-07-02"
  tasks_completed: 2
  files_changed: 7
---

# Phase 25 Plan 02: locale formatNumber helper + map panel year badges Summary

**One-liner:** Single `formatRate`/`formatDecimal` helper eliminates all hardcoded `es-CL` from ResultPanel and Astro components; map panel gains year badges (2024/2025) and a year-mismatch "?" tooltip via the existing RateTooltipReact pattern.

## Tasks Completed

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Create formatNumber helper + wire all call sites (P1-1) | 5112820 | Done |
| 2 | Year badges + year-mismatch tooltip + plural fix (P1-4, P2-3) | dc36cb2 | Done |

Note: TDD RED commit for Task 1: 28e4580 (test file added before implementation).

## What Was Built

**`site/src/lib/formatNumber.ts`** — pure Intl helper:
- `formatRate(value, locale)` → rounded integer with locale-correct thousands separator (EN: `4,984`, ES: `4.984`)
- `formatDecimal(value, locale, decimals=1)` → fixed-decimal with locale separators

**Call-site wiring:**
- `ResultPanel.tsx`: removed all 3 `es-CL` hardcodes; dropped `~` tilde from rate display; wired `formatRate` for rate + homicide, `formatDecimal` for multiplier
- `Legend.tsx`: local `fmt()` now delegates to `formatRate`
- `CommuneRankingTable.astro`: rate column calls `formatRate(row.rate, locale)`
- `ComparableCommune.astro`: rate display calls `formatRate(comparable.rate, locale)`

**Year badges:**
- Composite index heading: `<span class="year-badge">2024</span>` (COMPOSITE_YEAR const)
- Rate stat-card: `<span class="year-badge">{year}</span>` (year prop)
- `.year-badge` CSS rule added to `map.css` using tokens only (var(--line), var(--muted), var(--text-label), var(--weight-strong), var(--sm), var(--xs))

**Year-mismatch tooltip:**
- Reused `RateTooltipReact` `<details>`/`<summary>` "?" pattern
- EN copy: "Why do years differ? The Composite Index uses 2024 as the latest complete CEAD year..."
- ES copy: "¿Por qué difieren los años? El Índice Compuesto usa 2024..."

**Plural fix:** Already correct in original codebase (`count === 1 ? 'case' : 'cases'`, `count === 1 ? 'caso' : 'casos'`). Confirmed and left unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missed multiplier es-CL on line 320**
- **Found during:** Task 1 acceptance-criteria grep (grep -c "es-CL" returned 1, not 0)
- **Issue:** Multiplier decimal formatter `multiplierNum.toLocaleString(lang === 'es' ? 'es-CL' : 'en-US', ...)` was not in the plan's explicit list but is a `toLocaleString` call in ResultPanel
- **Fix:** Replaced with `formatDecimal(multiplierNum, lang, 1)` — needed to also import `formatDecimal` in ResultPanel
- **Files modified:** `site/src/components/map/ResultPanel.tsx`
- **Commit:** 5112820

### TDD Infrastructure

Installed `vitest@4.1.9` as devDependency (no test runner existed). 7/7 unit tests for `formatNumber.ts` pass.

## Known Stubs

None — all number formatting is live data; year badges use real COMPOSITE_YEAR const and `year` prop.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced.

## Self-Check: PASSED

- `site/src/lib/formatNumber.ts` exists: YES
- `site/src/lib/formatNumber.test.ts` exists: YES (7/7 tests pass)
- `grep -c "es-CL" ResultPanel.tsx` = 0: YES
- No `~{displayRate}` in ResultPanel: YES
- `formatRate` in CommuneRankingTable.astro: YES
- `formatRate` in ComparableCommune.astro: YES
- `.year-badge` in map.css: YES
- `year-badge` in ResultPanel.tsx: YES
- Plural `'case'`/`'cases'` in ResultPanel: YES
- 14/14 validators: PASS
- 834 pages built: YES
- Commits: 28e4580, 5112820, dc36cb2
