---
id: 260810-pbj
status: complete
verdict: PASS_WITH_NOTES (verificador opus) → notas resueltas por el estratega en 79bb23c
commit: 6b0bc92 (+ 79bb23c fix post-verificación)
date: 2026-08-10
---

# Summary: Mapa v2 (propuesta 5b) instalado vía dynamic workflow

Pipeline: premortem (3 revisores Opus, wf_f12426e9-35d) → decisiones locked + PLAN.md (Fable) → ejecución (Sonnet, wf_36182dfc-314) → verificación adversarial (Opus, misma wf) → validación final + fixes residuales (Fable).

## Qué se instaló

Rediseño de la sección mapa (`/map/`, `/es/mapa/`): los tres `<details>` cerrados (Año/Tipo/Modo) se sustituyen por un **rail de chips siempre visible** (`LayerRail`, 10 capas hermanas en `LAYER_DEFS`: índice, tasa total, 7 familias CEAD, homicidios — el modo se deriva de la capa); **leyenda-histograma** interactiva (`LegendHistogram`: distribución de 346 comunas, conteo por banda, clic aísla la banda en polígonos Y puntos de zoom bajo); **franja de prensa** (`NewsStrip`: conteo, ámbito heredado del filtro de familia, barras por día clicables); un solo efecto central de restyle en `MapIsland` (antes 3 bloques duplicados).

- Nuevos: `mapV2Strings.ts`, `LayerRail.tsx`, `LegendHistogram.tsx`, `NewsStrip.tsx`, `bandStats.ts`, `map-v2.css`, `mapFilterDefsV2.test.ts`
- Reemplazados: `MapIsland.tsx`, `MapTopbar.tsx`, `FilterSheet.tsx`, `FilterFields.tsx`, `IncidentPinLayer.ts`, `LowZoomDotLayer.ts`, `mapFilterDefs.ts`
- Eliminados: `EntryPointsRail.tsx`, `Legend.tsx`
- Única edición fuera del paquete: `scripts/validate/map.mjs` gana Check 10 (igualdad de conjuntos ids topo↔payload, MPX-A6)

## Premortem: 25 hallazgos (4 HIGH, 11 MEDIUM, 10 LOW, 0 BLOCKER), 21 fixes aplicados

HIGH (CSS/UI): swatch de leyenda estirado (regla anclada a `.legend-band-row` antigua → regla nueva 14×14); `min-width:208px` pisaba el tope móvil 160px (→ media query ≥481px); rail de 10 chips con overflow-x = FAIL criterio 2 del rubric fase 29/30 (→ flex-wrap sin overflow + override `--map-topbar-h` en 481–1023px, resuelve de paso el anillo de foco recortado); targets <44px en band-btn/clear/strip-clear (→ 44px).

MEDIUM (lógica/datos): efecto de año permanentemente inerte por race (→ gate `layerMounted`); aislar banda borraba el highlight de la comuna seleccionada (→ `selectedRef` reaplicado tras `applyStyleMap`); puntos de zoom bajo re-montados 2× con levelIdx viejo (→ `band` viaja dentro de `stats`); homicidios contaba los 163 ceros como banda 1 (→ `zeroCount` con fila propia); franja tapada por la leyenda en 641–860px (→ oculta ≤960px + z-index 760); StateSummary redundante en composite; barras-día sin nombre accesible; franja perdía el día más antiguo (31 fechas reales en window de 30); capa Homicidios rotulaba "Homicidios" mostrando prensa `vida` (→ etiqueta de familia vida); ancla temporal derivada del subconjunto filtrado (→ prop `anchor` sin filtrar).

LOW: cortes de capa total coherentes con `c.level` precalculado; guard de fetch de incidentes (1 toast D-15 por sesión); conteo composite suma 346 con ci null; márgenes leyenda móvil; prefers-reduced-motion; `year_label` duplicado eliminado; asserción de ids en validador.

## Verificación (Opus) y cierre (Fable)

Verificador: PASS_WITH_NOTES. Confirmó los 21 fixes por grep, diff exacto de 17 rutas, intactos (map.css, i18n.ts, map.astro, es/mapa.astro, ResultPanel, ChoroplethLayer, colors.ts), CHIP_DEFS/AVAILABLE_YEARS byte-idénticos, F-49, sin lenguaje calificativo, y re-corrió los gates de forma independiente.

Encontró 1 regresión del ejecutor + 1 gap, resueltos en `79bb23c`:
- **MPX-B8-CSS (MEDIUM)**: `.sr-only` no existía en ningún CSS global → el hint de barras-día se veía. Regla añadida a map-v2.css.
- **MPX-C2-RANGE (LOW)**: rango de días sin cota ante una fecha antigua malformada → cap a 2× window_days.

## Gates (última corrida, post-79bb23c)

`npm run check` 0 errores (solo warnings preexistentes MutableRefObject) · `npm test` 86/86 (9 files, incluye mapFilterDefsV2) · `npm run build` verde · `npm run validate` 16/16.

## Excepción documentada / deuda conocida (LOW, sin acción)

- Barras-día del NewsStrip con ancho <44px: 30+ barras × 44px no caben en 440px; mitigado con hit-area de alto completo, aria-label por barra y ocultación ≤960px (desktop-only). Comentado en map-v2.css.
- VERIF-UI: los 10 fixes CSS se verificaron estáticamente (grep + orden de cascada); sin pase visual E2E — candidato a `/gsd:ui-review` o revisión BrowserOS aparte.
- `map_entry_family`/`map_entry_mode` quedan huérfanas en i18n.ts (sin validador que lo penalice; i18n.ts no se toca por contrato del paquete).
- `--map-topbar-h: 200px` en 481–1023px es una estimación con slack, no medida en navegador — si el badge de año parcial flota alto en tablet, ajustar ahí.
