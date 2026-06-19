---
phase: 09-ux-readability-accessibility-polish
plan: "03"
subsystem: frontend-content
tags: [glossary, seo, a11y, tooltip, i18n, editorial]
dependency_graph:
  requires: ["09-01"]
  provides: ["/glossary/", "/es/glosario/", "rate-tooltip-in-tables", "glossary-cross-links"]
  affects: ["CommuneRankingTable", "MethodologyCaveat", "region pages", "crime pages"]
tech_stack:
  added: []
  patterns: ["EditorialLayout for static prose pages", "FAMILY_ORDER iteration for per-section anchors", "RateTooltip zero-JS details/summary"]
key_files:
  created:
    - site/src/pages/glossary.astro
    - site/src/pages/es/glosario.astro
  modified:
    - site/src/components/CommuneRankingTable.astro
    - site/src/components/MethodologyCaveat.astro
decisions:
  - "Used EditorialLayout (720px prose column) for both glossary pages — consistent with about/methodology pattern"
  - "Section id={key} matches FAMILY_ORDER keys so PanelFamilyBars #anchor deep-links land correctly"
  - "Links only to /crime/* and /es/delito/* — no /commune/* links (rollout 404 guard)"
  - "Added standalone glossary-footnote below table rather than inside thead to preserve table a11y structure"
metrics:
  duration: "18m"
  completed: "2026-06-15"
  tasks: 2
  files: 4
---

# Phase 09 Plan 03: Bilingual Glossary + Rate Tooltip Wiring Summary

**One-liner:** Bilingual CEAD-attributed crime-type glossary at /glossary/ and /es/glosario/ with per-family #anchors; zero-JS rate tooltip and glossary cross-links wired into ranking tables and methodology caveat.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build /glossary/ (EN) and /es/glosario/ (ES) bilingual glossary pages | 67b3668 | site/src/pages/glossary.astro, site/src/pages/es/glosario.astro |
| 2 | Add rate "?" tooltip + glossary cross-link to ranking tables and methodology caveat | 8a5491b | site/src/components/CommuneRankingTable.astro, site/src/components/MethodologyCaveat.astro |

## Acceptance Criteria Verified

- Both glossary pages import from familyDefs.ts (FAMILY_ORDER, FAMILY_LABELS_*, FAMILY_DEFS_*).
- Each page renders 7 family sections with id matching the family key (vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas).
- No /commune/ or /es/comuna/ links in either glossary page.
- No absolute "peligroso/dangerous" tone; sober "incidencia reportada" framing throughout.
- Build emits dist/glossary/index.html and dist/es/glosario/index.html.
- EN page hreflang references /es/glosario/ (3 occurrences in built HTML).
- CommuneRankingTable: RateTooltip imported and rendered in rate column header (zero-JS, no client:*).
- CommuneRankingTable: glossary footnote link below table (locale-aware).
- MethodologyCaveat: glossary_link appended after methodology link.
- Build exits 0 in 34.74s.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all 7 family sections have substantive prose (80–120 words each). Links resolve to existing /crime/* pages built in earlier phases.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes. All links target only existing public /crime/* and /es/delito/* routes.

## Self-Check: PASSED

- site/src/pages/glossary.astro — FOUND
- site/src/pages/es/glosario.astro — FOUND
- site/src/components/CommuneRankingTable.astro — FOUND (modified)
- site/src/components/MethodologyCaveat.astro — FOUND (modified)
- git log commit 67b3668 — FOUND
- git log commit 8a5491b — FOUND
- dist/glossary/index.html — FOUND (verified during build)
- dist/es/glosario/index.html — FOUND (verified during build)
