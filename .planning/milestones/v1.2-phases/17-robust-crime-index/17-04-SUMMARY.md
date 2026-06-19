---
phase: 17-robust-crime-index
plan: "04"
subsystem: methodology-pages
tags: [methodology, i18n, attribution, data-quality, legal-safe]
dependency_graph:
  requires: ["17-02", "17-03"]
  provides: ["DQ-03"]
  affects: []
tech_stack:
  added: []
  patterns: ["bilingual-parity-edit", "clickable-source-attribution"]
key_files:
  modified:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - "Rewrote 'does NOT say' section to remove any absolute safe/dangerous framing; used 'absolute level of risk' and 'free of crime' phrasing instead"
  - "Population-weighted mean wording used consistently (EN + ES) — corrects prior 'unweighted' language"
  - "target='_blank' added to all external source links alongside rel='noopener noreferrer'"
metrics:
  duration: "10m"
  completed: "2026-06-18"
  tasks: 1
  files: 2
---

# Phase 17 Plan 04: Bilingual Methodology Rewrite Summary

Atomic bilingual rewrite of both methodology pages to correct the CEAD host, document data-quality caveats, and add clickable multi-source attribution — in legal-safe tone with EN/ES parity.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Atomic bilingual methodology rewrite (EN + ES) | ef470eb | site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro |

## What Was Built

**EN page (`/methodology/`)** and **ES page (`/es/metodologia/`)** rewritten as one atomic commit:

- **Correct CEAD host**: `cead.ministeriointerior.gob.cl` replaced by clickable `<a href="https://cead.minsegpublica.gob.cl/estadisticas-delictuales/">` in both pages.
- **casos-policiales semantics**: explicit explanation that `tipoVal=1` (denuncias) + `tipoVal=2` (detenciones flagrantes) are summed additively; `tipoVal=3` (aprehendidos) excluded to avoid double-counting.
- **Partial-year note**: current calendar year excluded as partial; most recent complete year (2025) may not yet be CEAD's final closed series.
- **Low-count volatility caveat**: single incident can swing small-commune rate; low-population communes excluded from rankings.
- **Drug-scope caveat**: CEAD "Drogas" = Ley 20.000 (grupo 401, trafficking/supply only); drug consumption is grupo 702 under Incivilidades and is NOT included.
- **Floating-population denominator caveat**: Providencia/Las Condes business-hub effect explained; rate is correct on official INE figure but reflects visitor/worker exposure.
- **Multi-source attribution** with clickable links (both pages):
  - CEAD: https://cead.minsegpublica.gob.cl/estadisticas-delictuales/
  - SPD (homicides): https://prevenciondehomicidios.cl
  - SII (economic exposure): https://www.sii.cl/sobre_el_sii/estadisticas_de_empresas.html
  - Fiscalía (secuestro): https://www.fiscaliadechile.cl/persecucion-penal/estadisticas
- **Legal-safe tone**: "does NOT say" section rewritten to remove any absolute safe/dangerous framing; uses "absolute level of risk" and "free of crime" language instead. No forbidden terms introduced.
- **EN/ES parity**: 7 H2 sections in each page (verified by automated check).

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Methodology pages are static text only; no data wiring.

## Threat Flags

None. Static Astro content pages with `<a>`/`<code>`/`<ul>` only. No new network endpoints, no client-side JS, no auth paths.

## Self-Check: PASSED

- `site/src/pages/methodology.astro` — FOUND
- `site/src/pages/es/metodologia.astro` — FOUND
- Commit ef470eb — FOUND
- Automated Python assertion: OK (h2 count EN=7 ES=7, all 4 source links present in both pages, old host absent)
