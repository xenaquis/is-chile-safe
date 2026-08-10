---
quick_id: 260810-j51
slug: directorio-comunas-v2
date: 2026-08-10
status: complete
commits:
  - 62d659e feat(directory): centroid builder for "near me"
  - a2084eb feat(directory): commune directory v2 — one sortable 346-row table
---

# SUMMARY — Directorio de comunas v2

Instalado el rediseño 1b. Ambas páginas índice (`/communes/`, `/es/comunas/`)
quedan en 21 líneas y comparten `CommuneDirectory.astro`.

## Un desvío del paquete: dirección del ranking

El paquete definía `rank 1 = tasa más baja` (`dir_rank_title`, y el `sort`
ascendente de `ranked`). El validador `figure-registry` lo rechaza por el guard
DOCS-01: en todo el sitio `national_rank` es descendente, **rank 1 = tasa más
alta**. Se alineó el componente al sitio (no al revés):

- `ranked` ordena `b.rate - a.rate`
- `dir_rank_title` EN/ES pasa a "1 = highest" / "1 = más alta"
- `DEFAULT_DIR.rank = -1` (rank ascendente == tasa descendente)
- se añadió `state.col` para que la flecha del encabezado pertenezca a la
  columna clicada — antes `#` y `Tasa` compartían la clave `rate` y ninguna de
  las dos mostraba la flecha de forma consistente

## Gates

| Gate | Resultado |
|---|---|
| `astro check` | 0 errores / 0 warnings (baseline previo: 4/0) |
| `npm run build` | 834 páginas, OK |
| links por página | **346** EN y ES (antes 692) |
| `npm run validate` | 15/16 — solo `freshness` roja |
| `npm test` (vitest) | 59/59 |

`freshness` falla porque `data/incidents/current.json` tiene 3,2 días (máx. 3):
es la exclusión ambiental pre-declarada F-19, ajena a este cambio. `data/` no
fue tocado.

## Pendiente para el usuario

- Verificación visual/manual de INSTALL.md §5 (teclado, 375px, `?q=`, `<mark>`)
  — no ejecutada aquí.
- `dir_view_az` y `dir_view_region` quedan huérfanas en `config/i18n.ts`; el
  paquete recomienda borrarlas en una limpieza aparte.
- El paquete deja fuera de alcance alinear el mapa (`EntryPointsRail.tsx`,
  `FilterSheet.tsx`, `Legend.tsx`) con el mismo lenguaje de filtros — atado a
  los umbrales F-50/STRESS.md, requiere su propio paquete.
- Sin `git push` (no se solicitó).
</content>
</invoke>
