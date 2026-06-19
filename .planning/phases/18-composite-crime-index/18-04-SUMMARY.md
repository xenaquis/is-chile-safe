---
phase: 18-composite-crime-index
plan: "04"
subsystem: frontend
tags: [composite-index, ResultPanel, commune-pages, i18n, caveat, CI-05, CI-06]
dependency_graph:
  requires: [18-02, 18-03]
  provides: [composite-score-display, bilingual-caveat, commune-page-ci-section]
  affects: [ResultPanel.tsx, commune/[slug].astro, es/comuna/[slug].astro, data.ts, i18n.ts, map.css]
tech_stack:
  added: []
  patterns:
    - mode-gated JSX block (D-06) — composite block rendered only when mode === 'composite'
    - always-visible caveat (D-07) — never inside details, unconditional within composite block
    - String(year) key for composite_index access (Pitfall 3)
    - Math.round(score) integer-only render — no toFixed, no /100 suffix (T-18-11)
    - BAND_EN/BAND_ES[level-1] for 5-label band rendering (D-08)
key_files:
  created: []
  modified:
    - site/src/components/map/ResultPanel.tsx
    - site/src/components/map/map.css
    - site/src/config/i18n.ts
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/lib/data.ts
decisions:
  - Composite block in ResultPanel gated strictly on mode === 'composite'; default prop value is 'family' (safe fallback)
  - Commune Astro pages render composite section unconditionally (when data present) — they are static index-mode surfaces with no toggle (D-06 note)
  - CompositeIndexEntry interface added to data.ts (shared source of truth) and duplicated locally in ResultPanel.tsx (component isolation)
  - Reference year hardcoded as 2024 in Astro pages per UI-SPEC (caveat text says "Reference year: 2024")
  - All user-facing strings (bands, rank formats, caveat, heading) routed through i18n.ts EN_STRINGS/ES_STRINGS
metrics:
  duration: "~25 minutes"
  completed: "2026-06-19"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 18 Plan 04: Composite Index Display Surfaces Summary

One-liner: Integer 0-100 composite score + 5-band label + national/regional rank + always-visible bilingual caveat surfaced in ResultPanel (index-mode gated) and both EN/ES commune Astro pages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ResultPanel mode prop + composite block + caveat + i18n | 87f0a32 | ResultPanel.tsx, map.css, i18n.ts |
| 2 | Commune pages (EN + ES) composite section + caveat | cbee6fc | commune/[slug].astro, es/comuna/[slug].astro, data.ts |

## What Was Built

### Task 1 — ResultPanel

- Extended `CommuneData` interface (ResultPanel.tsx) with `composite_index?`, `spd_homicide_rate?`, `sii_exposure_index?` (D-12 additive).
- Added `mode` to `ResultPanel` function signature with default `'family'`.
- Added `BAND_EN` / `BAND_ES` const arrays for 5-level labels (D-08).
- New composite JSX block between badge row and stat-card — gated `mode === 'composite'` (D-06). Reads `data.composite_index?.[String(year)]`; omits section entirely if absent. Renders `Math.round(ci.score)` in `.stat-big`, band in `.stat-unit`, national+regional rank in `.ci-rank`, always-visible caveat in `.ci-caveat` (D-07).
- All strings (band labels, rank format, caveat text, section heading) routed through `EN_STRINGS`/`ES_STRINGS` in `i18n.ts`.
- New CSS in `map.css`: `.composite-index-section`, `.ci-rank`, `.ci-caveat` per UI-SPEC.

### Task 2 — Commune Pages

- Added `CompositeIndexEntry` interface and `composite_index?` field to `CommuneData` in `data.ts` (D-12).
- EN `commune/[slug].astro`: composite section between family breakdown and ComparableCommune. Renders integer score, `BAND_EN_PAGE[level-1]` label, national + regional rank strings from `EN_STRINGS`, and `.ci-caveat` with EN caveat text. Section omitted when `composite_index` absent.
- ES `es/comuna/[slug].astro`: mirror with `BAND_ES_PAGE` and `ES_STRINGS` strings including ES caveat text.
- Both pages: static index-mode surfaces, no map mode state imported (D-06 note).
- Build: 791 pages, sampled HTML (`/commune/algarrobo/`) confirmed score=33, band="Very High", rank=#43 of 346 nationally · #6 in Valparaíso, caveat text rendered.

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| threat_flag: editorial (mitigated) | commune/[slug].astro, es/comuna/[slug].astro | Composite score+rank now visible in static HTML — mitigated by always-visible `.ci-caveat` block (D-07, T-18-10) |

No new unmitigated trust boundaries introduced. The caveat block (D-07) is the T-18-10 mitigation — it is unconditional within the composite block on every surface.

## Known Stubs

None. The composite section is only rendered when `composite_index` data is present in the commune JSON (produced by Plan 18-01). Communes without composite data simply omit the section — no stubs, no N/A placeholders.

## Self-Check

- [x] site/src/components/map/ResultPanel.tsx — modified (composite block, mode prop, CommuneData extension)
- [x] site/src/components/map/map.css — modified (.composite-index-section, .ci-rank, .ci-caveat)
- [x] site/src/config/i18n.ts — modified (ci_band_1..5, ci_rank_national/regional, ci_caveat_text, ci_section_heading EN+ES)
- [x] site/src/pages/commune/[slug].astro — modified (composite section)
- [x] site/src/pages/es/comuna/[slug].astro — modified (composite section)
- [x] site/src/lib/data.ts — modified (CompositeIndexEntry, composite_index? on CommuneData)
- [x] Commit 87f0a32 exists
- [x] Commit cbee6fc exists
- [x] Build: 791 pages, no new errors
- [x] `mode === 'composite'` present in ResultPanel.tsx — D-06 gate confirmed
- [x] `.ci-caveat` and `.composite-index-section` present in map.css
- [x] Caveat strings in i18n.ts (not inline)
- [x] No toFixed in composite block; integer-only via Math.round

## Self-Check: PASSED
