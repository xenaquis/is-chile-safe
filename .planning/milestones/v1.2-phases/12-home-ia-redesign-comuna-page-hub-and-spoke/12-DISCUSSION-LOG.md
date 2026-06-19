# Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 12-home-ia-redesign-comuna-page-hub-and-spoke
**Areas discussed:** Layout del home, Hero busca-comuna, Spokes de la ficha, Spine de navegación

---

## Layout del home

| Option | Description | Selected |
|--------|-------------|----------|
| Layout home nuevo (ancho) | Nuevo HomeLayout/full-width; EditorialLayout queda para texto | ✓ |
| Extender EditorialLayout | Reusar/ensanchar el layout editorial actual | |
| Tú decides | Dejar al planner | |

| Option | Description | Selected |
|--------|-------------|----------|
| Recortar y bajar | Prosa condensada debajo del fold para SEO | ✓ |
| Mantener todo abajo | 5 secciones íntegras bajo el fold | |
| Mover a /is-chile-safe/ | Sacar la prosa larga del home | |

| Option | Description | Selected |
|--------|-------------|----------|
| Más seguras + mayor incidencia | Dos tablas cortas lado a lado | ✓ |
| Solo más seguras | Una sola tabla | |
| Tú decides | Planner elige | |

| Option | Description | Selected |
|--------|-------------|----------|
| Páginas editoriales existentes | Cards a editoriales existentes, cero contenido nuevo | ✓ |
| Editoriales + directorio + regiones | Añade directorio y regiones | |
| Tú decides | Planner elige | |

**User's choice:** Wide new home layout; condense editorial prose below the fold; two lead-ranking tables (safest + highest); guide cards to existing editorial pages only.
**Notes:** Above the fold = hero + rankings + map + guides. Reuse CommuneRankingTable.

---

## Hero busca-comuna

| Option | Description | Selected |
|--------|-------------|----------|
| Caja → directorio (estática) | Form que enruta a /communes/; cero JS, indexable | ✓ |
| Filtro inline (isla) | Reusar isla del finder en el home | |
| Tú decides | Planner elige | |

| Option | Description | Selected |
|--------|-------------|----------|
| Va al directorio filtrado | Siempre aterriza en /communes/ con resultados | ✓ |
| Va directo a la ficha | Match exacto salta a /commune/[slug] | |
| Tú decides | Planner elige | |

**User's choice:** Static box routing to the directory; even exact matches land on the filtered directory (≤2 interactions).
**Notes:** Avoids name→slug resolution and JS in the home root; no finder-island duplication.

---

## Spokes de la ficha

| Option | Description | Selected |
|--------|-------------|----------|
| Misma región, tasa cercana | Same-region ordered by nearest rate/100k | ✓ |
| Tasa cercana nacional | Nearest rate nationally | |
| Vecindad geográfica | Geometric adjacency (needs new computation) | |

| Option | Description | Selected |
|--------|-------------|----------|
| Diferir entera a Phase 16 | No news section now | ✓ |
| Construir con estado vacío | Mockup with empty-state now | |
| Tú decides | Planner elige | |

| Option | Description | Selected |
|--------|-------------|----------|
| Link a /map/ con foco | CTA a /map/ con ?cut/#slug; sin Leaflet en la ficha | ✓ |
| Embeber mini-mapa | Isla Leaflet en la ficha | |
| Tú decides | Planner elige | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sí, insertar nivel Comunas | Inicio › Comunas › Región › Comuna | ✓ |
| Dejar como está | Breadcrumb actual sin nivel Comunas | |

**User's choice:** Similar = same region/nearest rate; news deferred entirely to Phase 16; map spoke is a focus-param link (no embed); breadcrumb gains the Comunas level.
**Notes:** Deferring news shifts IA-02 news spoke + IA-03 noticias node to Phase 16 — captured as a boundary adjustment in CONTEXT.

---

## Spine de navegación

| Option | Description | Selected |
|--------|-------------|----------|
| Agregar 'Rankings' | Nueva entrada de nav | ✓ |
| No tocar el nav primario | Spine vía home rankings + cross-links | |
| Tú decides | Planner elige | |

| Option | Description | Selected |
|--------|-------------|----------|
| Footer spine + validador | Footer común + extender no-orphan-link validator | ✓ |
| Solo validador | Sin footer, solo validador | |
| Tú decides | Planner elige | |

**Follow-up — destino de "Rankings":**

| Option | Description | Selected |
|--------|-------------|----------|
| Nueva página hub de rankings | Crear /rankings/ + /es/rankings/ índice estático | ✓ |
| Apuntar a /safest-cities-in-chile/ | Reusar editorial existente | |
| Anclar al bloque del home | /#rankings | |

**User's choice:** Add "Rankings" nav → new static `/rankings/` (+ES) index over existing rankings; add a footer spine + extend the validator for reciprocity/404; no Noticias nav (deferred to Phase 16).
**Notes:** The /rankings/ index is a consciously accepted scope addition serving IA-03's "ranking" spine node; no new ranking data.

---

## Claude's Discretion

- Exact map focus-param syntax (`?cut=` vs `#slug`) — match what the map island supports.
- Exact `/rankings/` page composition and footer link set — minimal, reuse existing pages.
- Reuse vs light extension of CommuneRankingTable.astro and ComparableCommune.astro.

## Deferred Ideas

- Comuna-page news spoke + dedicated news page → Phase 16 (needs name→CUT geolocation fix).
- "Noticias" nav/spine node → Phase 16.
- OpenGraph/Twitter + ItemList/BreadcrumbList JSON-LD → Phase 13.
