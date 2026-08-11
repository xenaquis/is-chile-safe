---
id: 260810-tqr
slug: seccion-noticias-comuna
status: complete
completed: 2026-08-11
commit: 671cc75
workflow: dynamic (sonnet executor, opus verifier, fable strategist/validator)
---

# Summary: sección de noticias geolocalizadas en páginas de comuna

## Qué se hizo

- **Nuevo** `site/src/components/CommuneNewsSection.astro`: sección estática con los 6 incidentes de prensa más recientes de la comuna (desde `incidents/current.json`, memo módulo-scope `Map<cut, Incident[]>` — una lectura por build, no por página). Dot de color por familia (paleta espejo de news.astro), título por locale, outlet + fecha (UTC), link a fuente (`safeUrl`, `noopener noreferrer`), link "ver todos" → `/news/?q={comuna}` / `/es/noticias/?q=`, caveat legal. 0 incidentes → no renderiza nada. Prefijo `cnews-` (evita assertions de facets.mjs sobre `.news-card`). Cero JS cliente.
- **i18n**: 5 claves nuevas en interfaz + EN_STRINGS + ES_STRINGS.
- **Integración**: sección 6d (entre ENUSC y ComparableCommune) en `commune/[slug].astro` y `es/comuna/[slug].astro`.
- **Guard defensivo**: filtro build-time de titulares con términos prohibidos (lista espejo de forbidden-language.mjs) — un titular hostil degrada a un item menos, no a build rojo.

## Verificación

- Build 834 páginas OK; `facets.mjs` PASS (24 assertions), `commune.mjs` PASS (346 EN + 346 ES), `forbidden-language.mjs` PASS (835 páginas), `astro check` 0 errores.
- Dist: Santiago EN/ES con sección + 6 items + rel seguro; Antártica (0 incidentes) sin sección.
- Workflow: Opus (verificador adversarial) → PASS con 3 MEDIUM corregidos por fixer (h2 sin estilo scoped, sobre-match documentado del `?q=` substring, exposición a titulares prohibidos) + 2 LOW aceptados (año de referencia = incidente más reciente; CSS inerte `homicidios`).

## Deuda aceptada (LOW)

- `?q=` es substring: página de Talca lista también Talcahuano en "ver todos" (el input muestra el texto de búsqueda, filtro legible). Fix real requeriría parámetro `?commune={slug}` en el contrato de la página news.
- Lista FORBIDDEN_TERMS duplicada manualmente (comentario de sync en ambos archivos).
