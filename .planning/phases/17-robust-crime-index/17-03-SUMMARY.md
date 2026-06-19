---
phase: 17-robust-crime-index
plan: "03"
subsystem: data-provenance
tags: [sources, cead-host-fix, terms-pages, bilingual]
dependency_graph:
  requires: []
  provides: [data/SOURCES.md, correct-cead-host-in-terms]
  affects: [site/src/pages/terms.astro, site/src/pages/es/terminos.astro]
tech_stack:
  added: []
  patterns: [canonical-source-registry]
key_files:
  created:
    - data/SOURCES.md
  modified:
    - site/src/pages/terms.astro
    - site/src/pages/es/terminos.astro
decisions:
  - "SOURCES.md is the single authoritative provenance file for all data classes; lives at data/SOURCES.md alongside the data store"
  - "SPD, SII, and Fiscalia sections marked reference-snapshot-only (not wired to displayed metric) — to be wired in Phase 18"
metrics:
  duration: 8m
  completed: 2026-06-18
  tasks_completed: 2
  files_changed: 3
---

# Phase 17 Plan 03: Source Registry + Terms Host Fix Summary

**One-liner:** Canonical 5-class source registry at data/SOURCES.md (CEAD/SPD/SII/Fiscalia/chilemapas) plus wrong CEAD host corrected in both EN/ES terms pages (ministeriointerior → minsegpublica).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write canonical source registry data/SOURCES.md | 2090b8a | data/SOURCES.md |
| 2 | Fix wrong CEAD host in terms.astro + es/terminos.astro | 529fba0 | site/src/pages/terms.astro, site/src/pages/es/terminos.astro |

## What Was Built

### Task 1: data/SOURCES.md

Created the project's canonical provenance companion to the `data/` store. Five `##` sections:

- **CEAD**: host `cead.minsegpublica.gob.cl`; primary endpoint `get_estadisticas_delictuales.php`; catalog endpoint `ajax_2.php seleccion=9`. Measure semantics: `tipoVal=1,2` = casos policiales (denuncias+detenciones, additive and confirmed); `medida=2` = tasa/100k with INE resident-population denominator. Drug scope: Familia 4 / Ley 20.000 grupo 401 (consumption = grupo 702 under incivilidades, distinct). Lesiones = grupos 103+104+105. Secuestro absent from CEAD entirely.
- **SPD** (reference snapshot, not wired): VHC xlsx, `prevenciondehomicidios.cl`, commune-level, 2018–2025, victim microdata, count = row count per COMUN_AGR+ID_ANO.
- **SII** (reference snapshot, not wired): `PUB_COMU.xlsb`, `sii.cl`, working-population exposure proxy, 2005–2024, 346 communes; domicile-artifact caveat documented.
- **Fiscalia** (reference snapshot, not wired): secuestro, `fiscaliadechile.cl`, regional-only, 868 cases in 2024; commune-level not confirmed (S5b pending).
- **chilemapas**: GPL-3 geometry, 346 communes, `build-topojson.mjs` pipeline entry, attribution requirement stated.

### Task 2: Terms pages host correction

Replaced `cead.ministeriointerior.gob.cl` with `cead.minsegpublica.gob.cl` in both:
- `site/src/pages/terms.astro` (lines 65–66): href and visible text
- `site/src/pages/es/terminos.astro` (lines 71–72): href and visible text

Bilingual parity maintained. No other copy changed. Methodology pages (methodology.astro / es/metodologia.astro) left untouched per plan boundary — those are corrected in Plan 04.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan creates a documentation file and fixes string literals. No data wiring or UI rendering changes.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced.

## Self-Check: PASSED

- data/SOURCES.md exists and contains `minsegpublica`, all 5 data-class sections, `tipoVal=1,2`, `medida=2`, `grupo 401`
- `ministeriointerior` absent from both terms pages; `minsegpublica.gob.cl` present in both
- Commits 2090b8a and 529fba0 verified in git log
