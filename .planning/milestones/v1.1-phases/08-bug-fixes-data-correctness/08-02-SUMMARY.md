---
phase: 08-bug-fixes-data-correctness
plan: "02"
subsystem: frontend-i18n
tags: [i18n, a11y, bug-fix, astro, react]
dependency_graph:
  requires: []
  provides: [F-001-resolved, F-007-resolved]
  affects: [es/delitos-por-comuna, map/ResultPanel]
tech_stack:
  added: []
  patterns: [inline-locale-ternary]
key_files:
  created: []
  modified:
    - site/src/pages/es/delitos-por-comuna.astro
    - site/src/components/map/ResultPanel.tsx
key_decisions:
  - "No i18n dictionary entry needed — both fixes use inline string literals / ternary per PATTERNS.md"
  - "Function identifiers loadCommune / sampleCommune are code, not content — left unchanged"
metrics:
  duration: "8m"
  completed: "2026-06-15"
  tasks: 2
  files_changed: 2
requirements_closed: [BUGFIX-05]
---

# Phase 08 Plan 02: i18n/A11y String Fixes (F-001 + F-007) Summary

Corrected two string-level i18n leaks: ES heading used English "Commune" instead of "Comuna"; EN map close button had hardcoded Spanish `aria-label="Cerrar"` in all 3 render branches.

## What Was Built

**F-001 (ES H1 + body copy):** Changed `<h1>` on `/es/delitos-por-comuna/` from "Delitos en Chile por Commune" to "Delitos en Chile por **Comuna**". Also corrected 3 lowercase `commune` occurrences in body/FAQ text to `comuna`. Function identifiers (`loadCommune`, `sampleCommune`) are code — not content — and were left unchanged.

**F-007 (ResultPanel close button):** Replaced all 3 hardcoded `aria-label="Cerrar"` attributes in ResultPanel.tsx (skeleton branch line 138, error branch line 153, main panel line 215) with the existing inline-ternary locale pattern: `aria-label={lang === 'es' ? 'Cerrar' : 'Close'}`. EN map close button now resolves to "Close"; ES to "Cerrar".

## Tasks

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | ES H1 + body Commune → Comuna (F-001) | a9a5e3f | site/src/pages/es/delitos-por-comuna.astro |
| 2 | ResultPanel close-button locale-aware (F-007) | bb9dec1 | site/src/components/map/ResultPanel.tsx |

## Verification

- Build passed (42s, 100 pages).
- Built `dist/es/delitos-por-comuna/index.html` H1 confirmed "Delitos en Chile por Comuna".
- Source grep confirms 0 content-level "Commune"/"commune" tokens.
- `aria-label="Cerrar"` hardcoded occurrences: 0.
- `aria-label={lang === 'es' ? 'Cerrar' : 'Close'}` occurrences: 3.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — pure static literal replacements; no new attack surface per T-08-03 threat register entry.

## Self-Check: PASSED

- `site/src/pages/es/delitos-por-comuna.astro` — modified (5 strings corrected)
- `site/src/components/map/ResultPanel.tsx` — modified (3 aria-label replacements)
- Commit a9a5e3f exists
- Commit bb9dec1 exists
