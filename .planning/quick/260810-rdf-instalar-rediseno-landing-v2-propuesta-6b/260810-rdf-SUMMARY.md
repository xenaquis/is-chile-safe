---
id: 260810-rdf
title: Instalar rediseño Landing v2 (propuesta 6b) desde paquete install-landing
status: complete
date: 2026-08-10
commits:
  - 21ab2be feat(home): install Landing v2 (propuesta 6b) from install-landing package
  - 5ca58d1 fix(home): close verifier LOW findings V-01/V-02 on Landing v2
executed_via: dynamic-workflow (sonnet ejecutor, opus verificador, fable estratega/validador)
workflows:
  - wf_4283fe0e-96c (premortem, 3 opus, 32 hallazgos)
  - wf_fc6a3081-e00 (ejecución sonnet + verificación opus → PASS)
---

# Resumen

Home EN/ES pasa de 4 pantallas de scroll a panel de una pantalla (propuesta 6b,
paquete `Downloads/Optimizar diseño de comunas (6)/install-landing`): hero +
búsqueda con sugerencias en vivo, franja de stats, píldoras de exploración,
mini-mapa SVG build-time con franja de quintiles (aísla banda + filtra
extremos), lista de extremos con toggle Mayor/Menor, y pulso de noticias
(histograma 30 días + top-5 chips + 4 titulares). Cero `client:*`; todo
mejora progresiva vanilla con baseline server-rendered.

## Qué se hizo

1. **Premortem** (3 Opus): 32 hallazgos → 21 fixes consolidados LPX-1..20 en
   PLAN.md (1 rechazado: C9 peso SVG/blob — los `<title>` son el tooltip del
   spec). BLOCKERs: CSS scoped no alcanza nodos `createElement` (→ `:global()`
   namespaced), `[hidden]` derrotado por `display:flex` scoped (gotcha
   documentado), grid de 954px mínimos dentro del cap 860px de `.page-content`
   (→ `:global(main.page-content:has(.home-wide)){max-width:1240px}` +
   `minmax(0,…)` + mini-mapa W 190→110).
2. **Ejecución** (Sonnet): 8 archivos instalados + 20 fixes + gates verdes +
   commit atómico `21ab2be`. Desviaciones legítimas: 10 errores astro-check
   preexistentes del propio paquete corregidos (implicit-any + narrowing de
   null en funciones anidadas — sin @ts-ignore); FAM_DOT duplicado con
   comentario porque `rankingStrings.FAMILY_ACCENT` NO está sincronizado con
   noticias.astro (deuda anotada abajo).
3. **Verificación** (Opus): PASS. 20/20 greps con evidencia, diff limitado a
   los 8 archivos, archivos compartidos intactos, dist/ con 1 h1 por locale y
   JSON-LD correcto, tone guard limpio, gates re-corridos. 2 LOW residuales.
4. **Cierre de residuales** (Fable): `5ca58d1` — V-01 regla `li:last-child`
   dentro de `:global()` (el `<li>` también es client-created); V-02 aria-live
   pluralizado y con strings desde homeV2Strings vía `data-*`.

## Gates finales

`npm run check` 0 errores · `npm test` 86/86 · `npm run build` 835 páginas ·
`npm run validate` 16/16.

## Notas / deuda anotada

- **Verificación manual local**: usar `npm run build && npx astro preview`
  (build lleva `ROLLOUT_ALL=true`); en `npm run dev` 334/346 fichas dan 404
  por el gate de rollout de 12 comunas — no es regresión.
- **Paleta de familias triplicada**: news.astro/es/noticias.astro,
  `rankingStrings.FAMILY_ACCENT` (desincronizado) y ahora FAM_DOT del pulso.
  Candidato a módulo único client-safe.
- **Pérdida SEO aceptada** (LPX-15 mitigado): píldoras recuperan anchors
  descriptivos verbatim; se pierden h2+párrafo del CTA del mapa, subheads de
  tablas, columnas rank/tendencia y el selector de año del home (INSTALL.md lo
  asume; la exploración por año vive en rankings y mapa).
- **Centroides**: comuna Antártica (12202) sin centroide en
  `comuna-centroids.json` (345/346); mini-mapa dibuja 343 puntos (excluye
  además Rapa Nui y Juan Fernández por encuadre) — aria-label lo califica
  como continental.

## Rollback

`git revert 5ca58d1 21ab2be`.
