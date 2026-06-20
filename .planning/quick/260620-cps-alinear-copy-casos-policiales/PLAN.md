---
id: 260620-cps
title: Alinear copy de medida a "casos policiales" (denuncias + detenciones flagrantes)
type: quick
status: in-progress
created: 2026-06-20
---

# Quick Task: Alinear copy de medida — "casos policiales", no "denuncias"

## Problem

El pipeline scrapea **casos policiales** (`tipoVal="1,2"` en `pipeline/cead/client.py:111`),
es decir **denuncias + detenciones por flagrancia** sumadas a nivel de delito. La página
de metodología (`methodology.astro` / `metodologia.astro`) lo describe correctamente.

Pero superficies secundarias de alto tráfico SEO (descripciones de ranking, rate explainer,
y un par de líneas dentro de la propia metodología) todavía dicen que la cifra mostrada es
**"denuncias" / "reported complaints (denuncias)"**. Eso contradice la medida real, subrepresenta
qué capturamos (los delitos detectados por flagrancia: drogas/armas), y crea inconsistencia
editorial ("denuncias, no condenas" cuando en realidad es casos policiales).

Origen: el copy fue introducido en quick `260616-huj` (clarify rate labels) antes de que la
medida quedara documentada como casos policiales.

## Scope (copy-only, bilingüe — CERO cambios en datos/lógica/pipeline)

Mantener D-08 (no mostrar split denuncias vs detenciones; solo el total casos policiales).

### 1. `site/src/lib/familyDefs.ts` (núcleo)
- `RANKING_METHODOLOGY_EN` ×7: `Figures represent police reports (denuncias), not convictions.`
  → `Figures represent police-recorded cases (casos policiales — complaints plus arrests in the act), not convictions.`
- `RANKING_METHODOLOGY_ES` ×7: `Las cifras corresponden a denuncias policiales, no a condenas.`
  → `Las cifras corresponden a casos policiales (denuncias más detenciones flagrantes), no a condenas.`
- `RANKING_RATE_EXPLAINER_EN`: `reported complaints (denuncias) per 100,000 residents`
  → `police-recorded cases (casos policiales) per 100,000 residents`
- `RANKING_RATE_EXPLAINER_ES`: `denuncias por 100.000 residentes`
  → `casos policiales (denuncias más detenciones flagrantes) por 100.000 residentes`
- `FAMILY_DEFS_ES.vif` (L57): `Denuncias de violencia doméstica e intrafamiliar...`
  → `Incidentes reportados de violencia doméstica e intrafamiliar...` (consistencia con las otras familias que dicen "reportados")

### 2. `site/src/pages/methodology.astro` (L248)
- `...the CEAD-based crime index (which reports police denuncias per 100,000 population, a distinct measurement).`
  → `...the CEAD-based crime index (which reports police-recorded cases — casos policiales — per 100,000 population, a distinct measurement).`

### 3. `site/src/pages/es/metodologia.astro` (L256)
- `...el índice delictivo basado en CEAD (que reporta denuncias policiales por 100.000 habitantes, una medición distinta).`
  → `...el índice delictivo basado en CEAD (que reporta casos policiales por 100.000 habitantes, una medición distinta).`

### 4. `site/src/pages/es/rankings.astro` (L50)
- `...reflejan denuncias registradas, no una medida absoluta de riesgo.`
  → `...reflejan registros policiales (casos policiales), no una medida absoluta de riesgo.`
  (alinea con su gemelo EN `rankings.astro:48` que ya dice "reported counts")

## Explicitly OUT of scope (editorial prose sobre conducta de denuncia — correcto, NO tocar)
- `es/glosario.astro` (cultura de denuncia, subregistro)
- `es/delitos-por-comuna.astro` (campañas de denuncia)
- `es/mapa-seguridad-santiago.astro` (campañas de denuncia, subregistro)
- `es/comunas-mas-seguras-chile.astro` (menor propensión a denunciar)
- `is-chile-safe.astro` (formal complaint rates — contexto histórico)
- `methodology.astro:85` / `metodologia.astro:77` (definen denuncias como sub-medida de casos policiales — correcto)

## Verification
1. `cd site && npm run build && npm run validate` (un solo comando — OneDrive desync).
2. Grep post-fix: ninguna de las strings de medida mislabel queda en familyDefs.ts / los 3 pages.
3. Build verde, validators verdes.

## Commit
Atomic: `fix(260620-cps): describe displayed measure as casos policiales (not denuncias) across ranking/methodology copy, EN+ES`
