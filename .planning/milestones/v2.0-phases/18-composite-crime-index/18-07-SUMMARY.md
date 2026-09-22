---
phase: 18-composite-crime-index
plan: "07"
subsystem: documentation
tags: [gap-closure, sii-cap, methodology, sources, bilingual-parity]
dependency_graph:
  requires: [18-01]
  provides: [CI-04, CI-08]
  affects: [data/SOURCES.md, site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro]
tech_stack:
  added: []
  patterns: [documentation-correction, bilingual-parity]
key_files:
  modified:
    - data/SOURCES.md
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - "SII cap documentation corrected: 5.0 is a fallback trigger threshold, not a multiplier. When sii_workers/ine_population > 5.0, the denominator falls back to raw INE resident population — matching D-03 and composite_index.py:84."
metrics:
  duration: "~10 minutes"
  completed: "2026-06-19"
  tasks_completed: 2
  files_modified: 3
---

# Phase 18 Plan 07: SII Exposure Cap Documentation Correction Summary

**One-liner:** Corrected three doc files that misrepresented the SII cap as "5.0 × INE multiplier" — it is an INE-fallback trigger (matching D-03 and composite_index.py:84).

## What Was Done

Gap 2 (CI-04, CI-08): The pipeline code was correct but three documentation files described the SII exposure cap incorrectly, stating the denominator was "clamped to cap 5.0" or "5.0 × INE resident population". The correct behavior (per locked decision D-03 and `composite_index.py:84`) is that when `sii_workers / ine_population > 5.0`, the metric FALLS BACK to the raw INE resident population as the denominator — 5.0 is a threshold trigger, not a multiplier.

For Providencia (ratio 5.186, CUT 13123), the false docs implied a denominator of ~581,010 while the code uses 116,202 (raw INE). This plan corrected all three docs without touching any pipeline code.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Corrected SII cap clause in data/SOURCES.md to INE-fallback wording | e748c89 |
| 2 | Corrected EN (methodology.astro) and ES (metodologia.astro) methodology pages; bilingual parity maintained | 16357b2 |

## Deviations from Plan

None — plan executed exactly as written. The automated verify regex in Task 1 had a false-positive match on the new correct text (the pattern `5\.0.*INE.*resident` matched the corrected wording which legitimately mentions those tokens), but the actual acceptance criteria were fully met: the wrong phrases ("clamped to cap 5.0", "5.0 × INE") are gone and "falls back" is present. Task 2 astro check confirmed 0 new errors (9 pre-existing errors in unrelated files remain).

## Verification

- `data/SOURCES.md`: no "clamped to cap 5.0" / "5.0 x INE multiplier"; "falls back" present; F14 tokens (SII+trabajadores, SII+exposicion) intact and accent-free.
- `methodology.astro`: no "capped at 5.0 x" phrasing; INE-fallback wording present.
- `es/metodologia.astro`: no "5,0 veces la poblacion residente INE"; Spanish INE-fallback wording present.
- `npx astro check`: 0 new errors introduced (9 pre-existing unrelated errors unchanged).
- `composite_index.py`: not touched.

## Self-Check: PASSED

- data/SOURCES.md: modified (commit e748c89)
- site/src/pages/methodology.astro: modified (commit 16357b2)
- site/src/pages/es/metodologia.astro: modified (commit 16357b2)
- Both commits exist in git log
