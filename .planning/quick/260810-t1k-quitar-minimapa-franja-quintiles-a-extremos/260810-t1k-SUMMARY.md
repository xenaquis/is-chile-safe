---
id: 260810-t1k
title: Quitar mini-mapa SVG del home; franja de quintiles migra al card de Extremos
status: complete
date: 2026-08-10
commits:
  - 348c6e1 fix(home): replace broken Chile silhouette with quintile strip in extremes card
executed_via: dynamic-workflow (sonnet ejecutor, opus verificador, fable estratega/validador)
workflows:
  - wf_05826bdb-e79 (ejecución sonnet + verificación opus → PASS)
---

# Resumen

Reporte del usuario tras el deploy de Landing v2: "el mapa se ve raro, quizás
por la forma de Chile". Verificado por el estratega en browser a 1280px: la
silueta 39:1 de Chile en 110px de ancho era una columna de puntos solapados
con aspecto de bug.

**Decisión (Fable)**: eliminar la geografía, conservar la función. El card
"Chile en un vistazo" desaparece; la franja de quintiles con conteos migra al
card de Extremos — la lista que efectivamente filtra. La alternativa
region-zoom (Metropolitana default) se RECHAZÓ: exigía 17 SVGs pre-renderizados
o re-proyección cliente con lat/lng en el blob, dejaba los conteos nacionales
inconsistentes con la región visible, y el módulo está oculto <1024px.

Bonus estructural: los conteos de la franja pasan a universo elegible
(!low_population, 256) — botón y nota de banda muestran ahora el mismo número,
cerrando de raíz la contradicción 346-vs-256 que LPX-5 solo había rotulado.

## Cambios (commit 348c6e1, 6 rutas)

- `HomeMiniMap.astro` eliminado (git rm).
- `HomeExtremes.astro`: franja de 5 botones (conteo en píldora `.mm-count`,
  `data-band-label`, aria "filtrar la lista", focus-visible inset, atenuado por
  overlay, reduced-motion) + fila Menor/Mayor; enhancer absorbe el toggle de
  banda; evento `home:band` eliminado (emisor y receptor son el mismo módulo).
- `homeData.ts`: bandCounts solo sobre elegibles.
- `homeV2Strings.ts`: fuera glance_title/note/svg_aria/open_map; band_aria
  reescrito.
- Ambos `index.astro`: grid a `minmax(0,420px) minmax(0,1fr)`; sin `.hv2-map`.

## Verificación

Opus PASS: dist sin rastro del minimapa, franja SSR con disabled y conteos que
suman 256 = tally real del blob, JSON-LD intacto, CSS scoped sin fugas,
baseline sin JS íntegro, enhancer compilado auditado (sin estado residual, aria
sincronizado), 4 gates re-corridos (check 0 err, 86/86, 834 páginas, 16/16).
Validación visual del estratega en preview 1280px: layout 2 columnas correcto.

3 LOW documentados (no bugs): `search_no_match` huérfano PRE-existente (las
páginas pasan el literal por prop), `HomeCommune.lat/lng` sin consumidor tras
retirar el minimapa (build-time, cero bytes en HTML), transición `opacity`
vestigial en `.mm-band` (el atenuado ya no usa opacity).

## Rollback

`git revert 348c6e1` (HomeMiniMap vuelve con el revert).
