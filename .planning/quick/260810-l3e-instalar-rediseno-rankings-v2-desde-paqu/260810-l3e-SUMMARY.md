# Quick Task 260810-l3e: Instalar Rankings v2 (propuesta 3b) — Summary

**One-liner:** Rankings v2 (tabla+filtros+panel regional en `RankingBoard.astro`, hub de 8 tarjetas en `RankingHub.astro`) instalado desde el paquete `install-rankings`, con los 6 fixes BLOCKER/MEDIUM del premortem aplicados y la decisión locked de Fable (rank='—' fuera del último año, sin recálculo) implementada.

## Qué se hizo

Se copiaron los 7 archivos del paquete (`RankingBoard.astro`, `RankingHub.astro`, `rankingStrings.ts`, ambos `[crime].astro`, `rankings.astro` EN/ES) y se aplicaron los fixes de premortem sobre los archivos ya copiados, antes de correr los gates.

## Commits

- `d361a1a` feat(rankings): install Rankings v2 (propuesta 3b) from install-rankings package
  - Único commit atómico: los 7 archivos del paquete + todos los fixes de premortem juntos (el plan no pedía separar el commit de instalación del de fixes; Tarea 1 explícitamente decía "commit atómico aún no requerido hasta pasar Tarea 2").

## Desviaciones respecto al paquete original (`install-rankings`)

Todas explícitas y ya previstas por el plan (fixes de premortem), más una extensión de alcance justificada:

1. **B-01 (HIGH, timebomb `latestYear`)** — aplicado en `crime-ranking/[crime].astro` y `es/ranking-delito/[crime].astro`: `let latestYear = new Date().getFullYear() - 1` → `let latestYear = 0`, dejando que el `Math.max` posterior lo derive 100% del dato.
   - **Extensión no listada explícitamente en Tarea 1 pero de la misma clase de bug (Rule 1)**: `RankingHub.astro` traía el mismo patrón `new Date().getFullYear() - 1` (usado para el pie de página "año X" del hub, no para el ranking en sí). Se corrigió con el mismo criterio, ya que es el mismo timebomb (B-01) en un archivo que el propio plan ya listaba como "a editar".
2. **B-01 defensa en profundidad** — en `RankingBoard.astro`: se exportó `years` en `scriptData` y se agregó, antes del primer `render()`, el fallback `state.year = D.years.includes(state.year) ? state.year : Math.max(...D.years)` + `yearSel.value = String(state.year)`.
3. **Decisión locked (rank `—` fuera del último año)** — una línea en `render()`: `r.rank.textContent = r.lowpop || state.year !== D.latestYear ? '—' : '#' + rankOf.get(r)`. Reescritos `rk_rank_year_note` EN/ES para explicar ocultación, no cálculo. `rk_source_note` no se tocó.
4. **B-02 (denominador)** — `.replace('{total}', ...)` del cliente ahora usa siempre `D.total`, sin la bifurcación `state.hideLowpop ? D.eligible : D.total`.
5. **B-03 (vida→homicide)** — `RankingHub.astro`: `familyHref` ahora también excluye `def.familyKey === 'vida'` (antes solo excluía cuando no había slug), con comentario in-code citando la colisión de slug vida/homicide de la memoria del proyecto. Se usó `null` (no se inventó un anchor de metodología).
6. **B-04 (asterisco huérfano)** — chip de baja población ahora imprime `*{t.dir_lowpop_tag}` en vez de `{t.dir_lowpop_tag}` sin marcador.
7. **B-05 (gramática regiones ES)** — `RankingHub.astro` importa `regionNameEs` de `config/i18n.ts` y renderiza los 16 enlaces de región como `regionNameEs(x.name)` (ES) / `` `${x.name} Region` `` (EN). Verificado en `dist/es/rankings/index.html`: "Región de Tarapacá", "Región del Maule", "Región del Biobío", "Región Metropolitana", etc. — todas correctas.
   - En `RankingBoard.astro` se dejó el nombre corto de región en el panel/`<select>` (250px), con comentario in-code explicando la omisión deliberada, tal como el plan permitía.
8. **B-07 (selector `mark`)** — `mark { ... }` → `:global(mark) { ... }` en el `<style>` de `RankingBoard.astro`.
9. **B-08 (slice de highlight)** — en `paint()`, el slice ahora usa `nq.length` (longitud de la query normalizada) en vez de `q.length` (longitud de la query cruda), evitando desalineación cuando la búsqueda tiene acentos.
10. **B-09 (LOW)** — no aplicado; no costó tiempo adicional pero se priorizaron los fixes de mayor severidad y el tiempo se usó en gates. Queda como deuda conocida (reservar altura en `.rk-table tbody` / pista condicional en estado vacío con `hideLowpop` activo).

Ningún cambio tocó `config/i18n.ts`, `lib/data.ts`, `lib/familyDefs.ts`, `lib/jsonld.ts` — confirmado con `git diff --stat` (Tarea 1, verify) y con el `git status --short` final (limpio salvo la carpeta `.planning/`, no commiteada por regla). `RankingTableEnhancer.astro` y `TrendChip.astro` no fueron tocados y siguen siendo importados por `safest-cities-in-chile.astro` y `es/comunas-mas-seguras-chile.astro`.

## Salida real de los gates (Tarea 2)

### `npm run check` (astro check)
```
Result (147 files):
- 0 errors
- 0 warnings
- 44 hints
```
Baseline de 0 errores mantenido.

### `npm test`
```
Test Files  8 passed (8)
     Tests  82 passed (82)
```

### `npm run build`
```
[build] 834 page(s) built in 15.89s
[build] Complete!
```

### `npm run validate` (18 validadores, script imprime 16 líneas de resumen — algunos validadores corren agrupados)
```
VALIDATION SUITE SUMMARY
  PASS  structure
  PASS  commune
  PASS  rollout
  PASS  region
  PASS  crime
  PASS  hreflang
  PASS  schema
  PASS  map
  PASS  forbidden-language
  PASS  coverage
  PASS  spine
  PASS  seo
  PASS  figure-registry
  PASS  avs-b-budget
  PASS  freshness
  PASS  facets
────────────────────────────────────────────────────────────
  16/16 validators passed

All validators passed.
```

Detalle relevante dentro de `seo.mjs` (muestrea el primer subdir de `crime-ranking/` y `ranking-delito/` por orden de `readdirSync`):
```
PASS [OG] crime-ranking/disorder (EN): OG/Twitter meta present and locale-correct
PASS [OG] ranking-delito/armas (ES): OG/Twitter meta present and locale-correct
PASS [R] crime-ranking/disorder (EN): ItemList shape valid
PASS [S] crime-ranking/disorder (EN): BreadcrumbList shape valid
PASS [Q] crime-ranking/disorder (EN): all 3 ld+json block(s) parse cleanly
PASS [R] ranking-delito/armas (ES): ItemList shape valid
PASS [S] ranking-delito/armas (ES): BreadcrumbList shape valid
PASS [Q] ranking-delito/armas (ES): all 3 ld+json block(s) parse cleanly
```
Detalle relevante dentro de `spine.mjs` (checks G/H/L sobre `/rankings/`):
```
PASS [L] rankings-nav: all sampled ES pages contain href="/es/rankings/"
```
(checks G/H se satisfacen implícitamente — la ejecución global de `spine.mjs` reportó PASSED sin fallos individuales listados para G/H en este run).

`figure-registry.mjs` (DOCS-01) — barrido de 125 archivos fuente, sin marcar ninguna prosa invertida en `rk_rank_year_note` ni en las tarjetas del hub:
```
figure-registry: PASS — all 16 in-scope figures (F1-F16) have registered sources in data/SOURCES.md (zero orphans)
  [DOCS-01] swept 125 source files under site/src for inverted rank-direction claims
PASS [DOCS-01] methodology.astro contains "highest reported rate in Chile"
PASS [DOCS-01] metodologia.astro contains "mayor tasa reportada en Chile"
PASS [DOCS-01] safest-cities-in-chile.astro contains "highest reported rate nationwide"
PASS [DOCS-01] es/comunas-mas-seguras-chile.astro contains "mayor tasa reportada a nivel nacional"
```

## Verificaciones manuales de INSTALL.md §6 (sobre `dist/` real, gate de build ya corrido)

- `grep -o 'href="/es/comuna/' "dist/es/ranking-delito/robos-violentos/index.html" | wc -l` → **346**
  (nota: `grep -c` cuenta *líneas* con al menos un match, no ocurrencias; el HTML de build viene minificado en pocas líneas por página, así que se usó `grep -o | wc -l` para contar ocurrencias reales — se documenta como aclaración de método, no como desviación del contenido esperado por el plan).
- `grep -o 'href="/commune/' "dist/crime-ranking/violent-robbery/index.html" | wc -l` → **346**
- `dist/es/rankings/index.html` contiene las 16 URLs `/es/region/*` con nombres gramaticales correctos vía `regionNameEs()` (spot-check: Tarapacá, Maule, Biobío, Metropolitana — las 4 reglas especiales de la función se ven aplicadas correctamente en el HTML servido).
- `safest-cities-in-chile.astro` / `es/comunas-mas-seguras-chile.astro` siguen importando `RankingTableEnhancer` (3 referencias cada uno) y no fueron modificados — el comportamiento `—` para baja población no cambió, no hay bifurcación nueva.

## Decisión abierta (no cerrada por este quick, según instrucción del usuario)

"Recálculo de posición al cambiar año vs '—'" — el plan ya trae la decisión de Fable (rank='—' fuera del último año, revirtiendo el default 3b.a del paquete) como **locked_decision** dentro del propio `260810-l3e-PLAN.md`, y se implementó exactamente así (punto 3 arriba). No quedó ninguna decisión abierta pendiente de otra fuente para este quick task; la nota del prompt de "PENDIENTE — la decide Fable con la evidencia del premortem" ya está resuelta en el plan que se ejecutó.

## Deuda conocida (no bloqueante)

- B-09 (LOW): reservar altura en `.rk-table tbody` / pista condicional en estado vacío con `hideLowpop` activo — no aplicado, no bloquea el gate, documentado aquí como follow-up opcional.

## Self-Check

- `site/src/components/RankingBoard.astro` → FOUND
- `site/src/components/RankingHub.astro` → FOUND
- `site/src/config/rankingStrings.ts` → FOUND
- `site/src/pages/crime-ranking/[crime].astro` → FOUND
- `site/src/pages/es/ranking-delito/[crime].astro` → FOUND
- `site/src/pages/rankings.astro` → FOUND
- `site/src/pages/es/rankings.astro` → FOUND
- Commit `d361a1a` → FOUND (`git log --oneline` lo confirma)

## Fix round (post-hoc QA — RKQA-01)

Hallazgo aplicado, tal como fue confirmado (nada más añadido):

**RKQA-01 (HIGH)** — Concordancia gramatical rota en el H1 de `site/src/pages/es/ranking-delito/[crime].astro:182`. `reportados` quedaba fijo en masculino plural mientras `familyLabel` varía en género/número, produciendo agramaticalidades en 4 de las 8 familias (`violencia intrafamiliar reportados`, `incivilidades reportados`, `drogas reportados`, `armas reportados`).

- **Fix:** se reordenó el participio para que concuerde con "incidencia" (invariable): `Comunas con mayor incidencia de {familyLabel.toLowerCase()} reportados en Chile` → `Comunas con mayor incidencia reportada de {familyLabel.toLowerCase()} en Chile`. Funciona para las 8 familias sin lógica condicional.
- `<title>` (línea 133) y el `<h2 class="sr-only">` (línea 194) ya no usaban "reportados" en esa posición — no requerían cambio, verificado por lectura directa antes del fix.
- **Archivo:** `site/src/pages/es/ranking-delito/[crime].astro` (única página tocada; la EN `crime-ranking/[crime].astro` no tiene el problema — el inglés no flexiona por género).
- **Commit:** `6765004` fix(quick-260810-l3e): correct gender agreement in ES ranking H1 (RKQA-01)

### Gates tras el fix (salida real)

`npm run check`:
```
Result (147 files):
- 0 errors
- 0 warnings
- 44 hints
```

`npm test && npm run build && npm run validate` (encadenado):
```
Test Files  8 passed (8)
     Tests  82 passed (82)

[build] 834 page(s) built in 13.30s
[build] Complete!

VALIDATION SUITE SUMMARY
  PASS  structure / commune / rollout / region / crime / hreflang / schema / map
  PASS  forbidden-language / coverage / spine / seo / figure-registry
  PASS  avs-b-budget / freshness / facets
  16/16 validators passed
All validators passed.
```

Grep de verificación (346 enlaces de comuna por página, no se tocó markup de tabla pero se confirmó igual):
```
grep -o "Comunas con mayor incidencia reportada de" dist/es/ranking-delito/*/index.html | wc -l
→ 8   (una por cada una de las 8 páginas de familia ES, H1 corregido en todas)
```

## Self-Check: PASSED (fix round)

- `site/src/pages/es/ranking-delito/[crime].astro` línea 182 → contiene "incidencia reportada de" → FOUND (verificado post-build en `dist/es/ranking-delito/*/index.html`, 8/8)
- Commit `6765004` → FOUND (`git log --oneline -1` lo confirma)
