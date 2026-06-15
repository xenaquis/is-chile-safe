---
phase: 09-ux-readability-accessibility-polish
plan: "02"
subsystem: map-island
tags: [ux, legend, tooltip, accessibility, comparison-bar, nationalAvg]
dependency_graph:
  requires: ["09-01"]
  provides: ["numeric-legend-bands", "rate-tooltip-panel", "comparison-bar", "family-glossary-tooltips"]
  affects: ["site/src/components/map/Legend.tsx", "site/src/components/map/MapIsland.tsx", "site/src/components/map/ResultPanel.tsx", "site/src/components/map/PanelFamilyBars.tsx", "site/src/pages/map.astro", "site/src/pages/es/mapa.astro", "site/src/components/map/map.css"]
tech_stack:
  added: []
  patterns: ["build-time prop threading (loadNationalAverage → Astro frontmatter → island prop)", "quantile-break legend bands", "CSS-only comparison bar", "RateTooltip <details>/<summary> pattern"]
key_files:
  created: []
  modified:
    - site/src/components/map/Legend.tsx
    - site/src/components/map/MapIsland.tsx
    - site/src/components/map/ResultPanel.tsx
    - site/src/components/map/PanelFamilyBars.tsx
    - site/src/pages/map.astro
    - site/src/pages/es/mapa.astro
    - site/src/components/map/map.css
decisions:
  - "breaks computed in MapIsland from rate array (not pulled from ChoroplethLayer) per PATTERNS.md threading correction"
  - "nationalAvg prop made optional (default 0) in MapIsland so page can be mounted without the prop during testing"
  - "Comparison bar uses Math.min(rate/(nationalAvg*3),1) width so communes at 3× average fill 100% of track"
  - "PanelFamilyBars sources labels from familyDefs.ts — removes local FAMILY_LABELS duplicate"
metrics:
  duration: "18m"
  completed: "2026-06-15"
  tasks: 3
  files: 7
---

# Phase 09 Plan 02: Map Readability — Legend Bands, Rate Tooltip, Comparison Bar Summary

**One-liner:** Numeric+qualitative legend bands fed by quantile breaks, an accessible rate-per-100k tooltip in the commune panel, a neutral multiplier/comparison-bar vs. build-time national average, and per-family definition tooltips — all on the existing React island.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Legend numeric bands + qualitative labels (D-03), thread breaks from MapIsland, aria | b744b16 | Legend.tsx, MapIsland.tsx |
| 2 | ResultPanel rate tooltip (D-01) + multiplier/comparison bar (D-04); thread nationalAvg | f12ab7b | ResultPanel.tsx, MapIsland.tsx, map.astro, es/mapa.astro, map.css |
| 3 | Per-family glossary affordance in PanelFamilyBars (D-02) | d11445b | PanelFamilyBars.tsx |

## What Was Built

### Task 1 — Legend bands (D-03)
- `Legend.tsx` Props extended to `{ lang, breaks?: number[] }`.
- 5 bands rendered as `legend-band-row`: swatch (aria-hidden) + `legend-qual-label` (from `legend_qual_1..5` i18n keys) + `legend-range` (numeric e.g. "0 – 1 500" / "1 501 – 3 200") when `breaks` is provided.
- Per-100k unit note from `legend_per_100k_note` i18n.
- `MapIsland.tsx`: added `breaks` state; `computeQuantileBreaks` called after initial load and after each year-filter load; `<Legend breaks={breaks} />` threaded.
- A11Y-01 year select: `aria-label` already present in `FiltersRow.tsx`; chip buttons render full text labels. No duplication needed.

### Task 2 — Rate tooltip + comparison bar (D-01, D-04)
- `map.astro` + `es/mapa.astro`: `loadNationalAverage()` called in Astro frontmatter; result passed as `nationalAvg` prop to `<MapIsland>`. No fs call in any React component (Pitfall 1 clean).
- `MapIsland.tsx`: `nationalAvg?: number` prop added (default 0); forwarded to `<ResultPanel>`.
- `ResultPanel.tsx`: imports `RateTooltip` and `EN_STRINGS`/`ES_STRINGS`; renders `<RateTooltip>` inline next to stat-unit.
- Multiplier computed as `rate / nationalAvg`, formatted via `toLocaleString` with 1 decimal; `comparison_national` i18n template substituted.
- CSS-only comparison bar: `.comparison-bar-track` (relative), `.comparison-bar-fill` (width = `min(rate/avg*3,1)*100%`, colored `var(--s{level})`), `.comparison-bar-avg-marker` at `left:33.3%` (= 1× average). Entire bar wrapper is `aria-hidden`; text label is the accessible signal.
- `overflow: visible` added to `.stat-card` (Pitfall 2 — tooltip body clip prevention).
- No absolute safety language (no "peligroso/dangerous/safe/seguro" introduced).

### Task 3 — Family glossary tooltips (D-02)
- `PanelFamilyBars.tsx` refactored: local `FAMILY_LABELS` removed; now imports `FAMILY_ORDER`, `FAMILY_LABELS_EN`, `FAMILY_LABELS_ES`, `FAMILY_DEFS_EN`, `FAMILY_DEFS_ES` from `familyDefs.ts`.
- `<RateTooltip lang tip={FAMILY_DEFS_*[key]} />` rendered next to each family label.
- No cross-plan glossary `#anchor` link — fully self-contained from Plan 01 contracts.
- `aria-hidden` accent-dot on featured families preserved.

## Deviations from Plan

None — plan executed exactly as written.

## A11Y-01 Map Controls Audit

The year `<select>` in `FiltersRow.tsx` already carried `aria-label` (Phase 8 / prior work). Each crime-type chip `<button>` renders the full localized label as its text content (e.g. "Life crimes" / "Vida y convivencia") — no icon-only chips. No additions were needed; this task confirmed the accessible names are present.

## Known Stubs

None. All data is wired: breaks come from the runtime payload; nationalAvg is loaded at build time from CEAD data.

## Threat Flags

None. No new network endpoints, auth paths, or file access patterns introduced. `loadNationalAverage` is confirmed build-time only (T-09-03, T-09-04, T-09-SC dispositions: accepted/mitigated as per threat register).

## Self-Check: PASSED

- b744b16: `git log --oneline` — present
- f12ab7b: `git log --oneline` — present
- d11445b: `git log --oneline` — present
- `site/src/components/map/Legend.tsx` — modified (breaks prop, 5 bands)
- `site/src/components/map/MapIsland.tsx` — modified (computeQuantileBreaks, nationalAvg)
- `site/src/components/map/ResultPanel.tsx` — modified (RateTooltip, comparison bar)
- `site/src/components/map/PanelFamilyBars.tsx` — modified (RateTooltip per family)
- `site/src/pages/map.astro` — modified (loadNationalAverage, nationalAvg prop)
- `site/src/pages/es/mapa.astro` — modified (loadNationalAverage, nationalAvg prop)
- `site/src/components/map/map.css` — modified (comparison-bar + legend-band CSS)
- Build: `npm run build` exited 0 on all three tasks.
