---
phase: 10-high-resolution-commune-geometry
plan: "03"
subsystem: editorial-attribution
tags: [attribution, gpl3, chilemapas, methodology, human-uat, i18n]
dependency_graph:
  requires: [10-02]
  provides: [GEO-01-attribution, GEO-02-uat-gate]
  affects:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - .planning/phases/10-high-resolution-commune-geometry/10-HUMAN-UAT.md
tech_stack:
  added: []
  patterns: [bilingual-section-parity, editorial-attribution]
key_files:
  created:
    - .planning/phases/10-high-resolution-commune-geometry/10-HUMAN-UAT.md
  modified:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - Attribution section added directly after CEAD section in both locales — new dedicated H2, not a footnote
  - EN heading "Map boundaries: chilemapas" / ES heading "Geometría del mapa: chilemapas" chosen for clarity and parity
  - GPL-3, INE/SUBDERE/BCN, and chilemapas GitHub/pacha.dev URLs included in both pages
  - Geometry-vs-statistics separation explicitly stated to avoid reader confusion
  - HUMAN-UAT device class reuses Phase-3 gate (Moto G4 + Fast 3G) for continuity
metrics:
  duration: 10m
  completed: "2026-06-15"
  tasks: 2
  files: 3
---

# Phase 10 Plan 03: Attribution + HUMAN-UAT Gate Summary

Chilemapas GPL-3 boundary-source credit added to EN and ES methodology pages in matching dedicated sections, and a HUMAN-UAT gate document created with concrete step-by-step instructions for the two intrinsic manual checks — visual polygon recognizability and throttled-mobile pan/zoom/hover performance. Manual gate is **pending human sign-off**.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add chilemapas attribution to methodology pages (EN + ES) | 08f67e3 | site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro |
| 2 | Author HUMAN-UAT gate document | 1704cef | .planning/phases/10-high-resolution-commune-geometry/10-HUMAN-UAT.md |

## What Was Built

**Task 1 — Attribution (both locales):**

- `site/src/pages/methodology.astro`: New `<section>` with `<h2>Map boundaries: chilemapas</h2>` inserted after the CEAD section. Credits chilemapas (github.com/pachadotdev/chilemapas / pacha.dev/chilemapas), GPL-3 license, and INE/SUBDERE/BCN government sources. Paragraph explicitly distinguishes geometry source (chilemapas) from crime-statistics source (CEAD).
- `site/src/pages/es/metodologia.astro`: Matching `<section>` with `<h2>Geometría del mapa: chilemapas</h2>` — same content in Spanish, same links, same GPL-3 and INE/SUBDERE/BCN attribution. Full content and structure parity with EN (Phase-9 parity rule).
- Astro build exits 0; `dist/methodology/index.html` and `dist/es/metodologia/index.html` both contain "chilemapas" and "GPL-3".

**Task 2 — HUMAN-UAT gate document:**

`.planning/phases/10-high-resolution-commune-geometry/10-HUMAN-UAT.md` created with:
- Shipped asset baseline table (345.4 KB raw / 85.6 KB gzip).
- Gate 1 (visual recognizability): step-by-step instructions to open `/map/` and `/es/mapa/`, spot-check 6 specific comunas (Isla de Pascua 5601, Juan Fernández 5602, Antártica 12202, Valparaíso 5101, Santiago 13101, Temuco 9101), and confirm coastline fidelity vs prior blocky render. Explicit pass/fail boxes.
- Gate 2 (throttled-mobile perf): Chrome DevTools emulation instructions — Moto G4 + Fast 3G (reusing Phase-3 gate device), pan/zoom/hover/click sequence, console clean check. Explicit pass/fail boxes.
- Additional regression checks: choropleth all-346 colour check, methodology attribution pages, nav links.
- Per-gate sign-off table with tester/date/notes fields and resume-signal instruction.

## Verification Results

```
npm run build → exit 0, 102 pages built in 34s
dist/methodology/index.html — contains "chilemapas": true | contains "GPL-3": true
dist/es/metodologia/index.html — contains "chilemapas": true | contains "GPL-3": true
```

## Deviations from Plan

None — plan executed exactly as written.

## Manual Gate Status

**PENDING.** The human-verify checkpoint (Task 3 in 10-03-PLAN.md) is blocking and has not yet been signed off. Both intrinsic manual checks (visual recognizability + throttled-mobile performance) require a human to open the map in a real browser and verify. See `10-HUMAN-UAT.md` for complete instructions.

## Known Stubs

None. The attribution text is fully wired and visible in the built pages.

## Threat Flags

None. T-10-LICENSE (GPL-3 chilemapas attribution obligation) is now mitigated — both locales carry the visible credit. No new network endpoints or auth surfaces introduced.

## Self-Check: PASSED

- `site/src/pages/methodology.astro` modified — commit 08f67e3 confirmed
- `site/src/pages/es/metodologia.astro` modified — commit 08f67e3 confirmed
- `.planning/phases/10-high-resolution-commune-geometry/10-HUMAN-UAT.md` created — commit 1704cef confirmed
- Build exits 0; both dist methodology pages contain "chilemapas" and "GPL-3"
- 10-HUMAN-UAT.md contains "recognizable" and "Fast 3G" gate references
