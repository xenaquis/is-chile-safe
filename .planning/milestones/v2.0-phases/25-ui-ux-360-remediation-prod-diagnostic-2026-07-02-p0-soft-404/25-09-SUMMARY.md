---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
plan: "09"
subsystem: verification
tags: [e2e, browseros, build-gate, pytest, p25-acceptance]
dependency_graph:
  requires: [25-01, 25-02, 25-03, 25-04, 25-05, 25-06, 25-07, 25-08]
  provides: [phase-25-acceptance-evidence]
  affects: []
tech_stack:
  added: []
  patterns: [inline-browseros-review, chained-build-validate]
key_files:
  created: []
  modified:
    - site/src/pages/news.astro (gap fix during review)
    - site/src/pages/es/noticias.astro (gap fix during review)
    - site/src/components/map/MapIsland.tsx (gap fix during wave 3)
decisions:
  - astro check's 8 TypeScript errors are pre-existing tech debt (documented 260620-hrh as 9; none in phase-25 files) — accepted, not a phase regression
  - "?cut= and ?a=&b= guards widened to /^\\d{4,5}$/ — CUTs are unpadded (Valparaíso 5101)"
  - skip-link/:focus-visible verified via CSS rules (JS .focus() in a background tab cannot match :focus — test artifact, not a bug)
metrics:
  duration: "~35m"
  completed: "2026-07-03"
  tasks_completed: 2
  files_modified: 3
---

# Plan 25-09 Summary — Final integrated verification

## Task 1 — Automated suite

- `npm run build`: 834 pages, exit 0.
- `npm run validate`: 14/14 validators (incl. forbidden-language) — green on every wave and on final integration.
- `npm run check`: 8 errors, ALL pre-existing (ComparatorPairsLinks, RankingTableEnhancer, commune/[slug] RankingRow, es/comuna/[slug]); count went 9 → 8 vs the 260620-hrh baseline. No new errors from Phase 25.
- `python -m pytest -q` (pipeline): **210 passed** incl. traffic-accident exclusion regression tests.
- Build-grep contract (all pass): `dist/404.html` exists; `rel="icon"` ×2; PageHeader `min-width: 1100px` ×4; `es-CL` in ResultPanel = 0; fitBounds+maxBounds present; `<table>` on is-santiago-safe (2), is-chile-safe (2), safest-cities (1); news h2=1 + h3=42 + chips=43 (EN) / h3=42 + chips=43 (ES); JSON-LD WebSite+Organization on home; 16 `/region/` links in rankings; skip-link in every page.

## Task 2 — BrowserOS inline visual review (localhost:4321 preview)

| # | Check | Result |
|---|-------|--------|
| 1 | P0-1 `/404-test-nonexistent/` | **404 real** (fetch status 404), página bilingüe, 3 CTAs |
| 2 | P0-3 favicon | `/favicon.svg` 200, 2 `<link rel=icon>` |
| 3 | P0-2 @772px (ancho del diagnóstico) | overflow **0px** (era ~305px), hamburguesa, "Glossary", lead-tables apiladas; 375px overflow 0 |
| 4 | P1-1/P1-4 panel mapa | EN "4,984", sin "~", badges 2024/2025 + tooltip "?"; ES hero "4.984", Similar "4.991/5.017" (bug exacto corregido) |
| 5 | P1-3 mapa | Chile centrado (screenshot), 42 pins **#6d28d9** borde blanco, leyenda "Reported incidents"; móvil: leyenda `<details>` colapsada (6% altura, era ~40%), pills bajo el buscador sin overlap; `?cut=13120` deep-link OK |
| 6 | P1-5 editoriales | tablas + sparkline presentes, CEAD atribuido |
| 7 | P1-6 news | h2 mes + 42 h3 + chips tipo/comuna con labels localizados EN+ES |
| 8 | P1-2 compare | click chip → URL `?a=13101&b=13114`; label "Composite Crime Index" ×3 + link metodología; "2,871.5"; homicidio "8.7 (48 cases)"; chips populares ×3 |
| 9 | P2-1 a11y | markers con aria-label (titular); skip-link → `#main-content` presente; `:focus-visible` global 2px + `.skip-link:focus` reveal (reglas CSS verificadas; JS-focus en tab background no activa `:focus` — artefacto) |
| 10 | P2-2/P2-3 región | "(1 = highest reported)", "Annual evolution (2005–2026*)" + footnote parcial, CTA "View interactive map →" con estilo card |

Screenshots: `C:\Users\Carlo\bos-shots\p25-404.png`, `p25-map-panel.png` (capturas adicionales fallaron por CDP timeout — verificación estructural via evaluate_script cubre cada ítem).

## Gap fixes applied during review (committed)

1. `9aeb8f5` — `?cut=` guard `/^\d{5}$/` → `/^\d{4,5}$/` (CUTs sin zero-pad).
2. `ebc54d8` — news chips EN mostraban claves crudas ("Vida", "Robos_violentos") → `FAMILY_LABELS_EN`; `/es/noticias/` seguía con lista plana → portada estructura semántica completa (h2 mes, h3, chips `FAMILY_LABELS_ES`, chip comuna nombrada). Paridad bilingüe verificada en dist.

## Deferred / notes

- Cosmético: heading "Composite Crime Index (2024)" + badge "2024" duplican el año en el panel del mapa.
- 8 errores `astro check` preexistentes — candidatos a sweep de deuda técnica futuro.
- Verificación en PROD del status 404 (Cloudflare) queda para el deploy (curl -I tras publicar).
