---
id: 260810-kcj
title: Instalar rediseño UX de /news/ y /es/noticias/
type: quick-full
status: COMPLETE
files_modified:
  - site/src/lib/newsDayFacets.ts (nuevo)
  - site/src/lib/newsDayFacets.test.ts (nuevo)
  - site/src/lib/newsFilterLogicDay.test.ts (nuevo)
  - site/src/lib/newsFilterLogic.ts (reemplazado + fix a)
  - site/src/pages/news.astro (reemplazado)
  - site/src/pages/es/noticias.astro (reemplazado)
  - site/src/config/i18n.ts (3 inserciones aditivas)
commits:
  - af14343: "feat(260810-kcj): install news UX redesign (filter bar + day histogram)"
  - a46f436: "feat(260810-kcj): add 6 news UX i18n keys (histogram + column headers)"
---

# Quick 260810-kcj: Instalar rediseño UX de noticias — Summary

Rediseño UX de `/news/` y `/es/noticias/` instalado desde el paquete externo
`patch-noticias`: barra de filtros compacta (buscador + desplegable de región +
presets) reemplazando las 28 casillas apiladas, histograma de 30 días con
aislamiento por `?day=YYYY-MM-DD`, y lista de incidentes densificada con
columnas explícitas (hecho/comuna/medio/fecha), todo bilingüe.

## Tareas ejecutadas

1. **Copia de 6 archivos + fix (a) + gate temprano.** Copiados los seis
   archivos del paquete a `site/src/`. Aplicado el fix (a) en
   `newsFilterLogic.ts` y ajustadas 4 aserciones en
   `newsFilterLogicDay.test.ts`. Gate temprano
   `npx vitest run src/lib/newsFilterLogic.test.ts` → **16/16 tests VERDE**,
   sin diff en el archivo. Commit `af14343`.
2. **Inserciones i18n.** 6 claves nuevas añadidas a `I18nStrings`,
   `EN_STRINGS` y `ES_STRINGS` (histograma + encabezados de columna), cero
   claves existentes tocadas. `npm run check` → **0 errores, 0 warnings, 44
   hints** (hints preexistentes, no relacionados). Commit `a46f436`.
3. **Verificación completa encadenada.** `npm test && npm run build && node
   scripts/validate/facets.mjs && npm run validate` → todo verde, sin
   commits de código (tarea de sólo verificación).

## Salida real de cada gate

- **test:** `npm test` → **8 test files passed, 82 tests passed** (incluye
  `newsDayFacets.test.ts`, `newsFilterLogicDay.test.ts` y
  `newsFilterLogic.test.ts` intacta y verde).
- **build:** `npm run build` completó sin errores (Astro 7, salida estática,
  `dist/` generado con 1275 archivos totales).
- **facets (standalone):** `node scripts/validate/facets.mjs` →
  **PASS — 1529 incidentes, 8 familias, 346 comunas, 24 aserciones
  pasadas** (venía de 22 en la última referencia de STATE.md; el paquete
  sumó 2 aserciones nuevas relacionadas con la dimensión `day`, sin romper
  ninguna previa).
- **validate:** `npm run validate` → **16/16 validadores PASS**
  (`structure, commune, rollout, region, crime, hreflang, schema, map,
  forbidden-language, coverage, spine, seo, figure-registry, avs-b-budget,
  freshness, facets`), terminó imprimiendo `VALIDATE_OK`.

## Desviaciones respecto al paquete original (2, ambas ya previstas y
autorizadas en `<known_defect_in_package>` del plan)

### Desviación 1 — Fix (a) en `parseFilterParams` (`site/src/lib/newsFilterLogic.ts`)

- **Problema:** el paquete original terminaba `parseFilterParams` con
  `return { family, region, window, q, day };`, que siempre incluye la
  propiedad `day` (valor `''` cuando el parámetro está ausente). Vitest
  `toEqual` no ignora propiedades presentes con valor `''` (sólo
  `undefined`), así que `newsFilterLogic.test.ts:40` y `:51` fallaban de
  forma determinista.
- **Fix aplicado:**
  ```ts
  const out: FilterParams = { family, region, window, q };
  if (day) out.day = day;
  return out;
  ```
- **Archivo:** `site/src/lib/newsFilterLogic.ts`. `newsFilterLogic.test.ts`
  quedó **sin ningún diff** (verificado con `git diff --name-only`) y sigue
  verde. `FILTER_LOGIC_MARKER = 'newsFilterLogic/v1'` intacto.
- **Commit:** `af14343`.

### Desviación 2 — Ajuste de 4 aserciones en `newsFilterLogicDay.test.ts` (archivo NUEVO del paquete, no protegido)

Consecuencia directa de la desviación 1: con el fix (a), `day` pasa a ser
`undefined` (no `''`) cuando está ausente o es malformado. Se ajustaron
las comparaciones `toBe('')` → `toBeFalsy()` en:

- Línea ~34 — `'defaults to empty when absent'` (la exigida explícitamente
  por el plan).
- Líneas ~38-40 — `'degrades a malformed day to empty rather than
  throwing'` (3 aserciones adicionales: `?day=yesterday`,
  `?day=2026-8-5`, `?day=` + 500 nueves) — el plan anticipó este caso
  ("si alguna de ellas usa `toBe('')` en el archivo real, aplicar el mismo
  `toBeFalsy()` y declararlo en el SUMMARY").

Ninguna otra línea de ese archivo se tocó. `newsFilterLogic.test.ts` no fue
modificado.

**Commit:** `af14343`.

## Invariantes preservados

Verificado empíricamente vía `facets.mjs` (24/24 aserciones VERDE) que ninguno
de los tres invariantes documentados en el plan se rompió: región sigue siendo
checkboxes (no `<select>`), ninguna regla `display` bajo selector
`.news-card`, y un único `data-result-count-template`. `FILTER_LOGIC_MARKER`,
canonical/hreflang y `#news-facet-semantics` EN/ES también verificados por el
mismo validador.

## Archivos NO tocados (por diseño)

- `site/src/lib/newsFacets.ts` — sin diff, confirmado.
- `site/src/lib/newsFilterLogic.test.ts` — sin diff, confirmado, sigue verde.

## Self-Check

- FOUND: site/src/lib/newsDayFacets.ts
- FOUND: site/src/lib/newsDayFacets.test.ts
- FOUND: site/src/lib/newsFilterLogicDay.test.ts
- FOUND: site/src/lib/newsFilterLogic.ts (contiene `if (day) out.day = day;` y `newsFilterLogic/v1`)
- FOUND: site/src/pages/news.astro
- FOUND: site/src/pages/es/noticias.astro
- FOUND: site/src/config/i18n.ts (6 claves × 3 = 18 ocurrencias)
- FOUND commit af14343 en `git log --oneline`
- FOUND commit a46f436 en `git log --oneline`

## Self-Check: PASSED

## Blockers

Ninguno. Los tres gates (test temprano, `npm run check`, y la cadena
test+build+facets+validate) salieron verdes en el primer intento; no fue
necesario invocar el rollback.

## Fix round (2026-08-10, revisión CR-01/WR-01)

Ronda de fixes sobre la review `260810-kcj-REVIEW.md`, dos hallazgos, un
commit atómico por fix, sólo en `site/src/pages/news.astro` y
`site/src/pages/es/noticias.astro` (gemelos byte a byte en script/CSS,
sólo comentarios difieren por idioma, siguiendo el patrón ya validado por
la revisión de paridad EN/ES).

### Fix 1 — CR-01 (blocker editorial): atribución del medio oculta en móvil

- **Problema:** `@media (max-width: 860px) { .news-outlet { display: none } }`
  eliminaba el nombre del medio de prensa del árbol de accesibilidad y de la
  vista en la mayoría del tráfico (móvil), violando la regla del proyecto
  "siempre atribuir fuentes".
- **Fix:** reflow de `.news-row` en móvil — `.news-title` ocupa la fila
  completa, `.news-commune-chip` pasa a su propia línea, y `.news-outlet` +
  `.news-date` comparten una línea (`grid-column: 1` / `grid-column: 2`) en
  vez de eliminarse. Ninguna regla con `.news-card` en el selector declara
  `display` (invariante de la aserción 12 de `facets.mjs` preservado).
- **Archivos:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro`
  (sólo bloque `<style>`, media query 860px).
- **Commit:** `dcd619a` — "fix(news): keep outlet attribution visible on mobile (CR-01)".

### Fix 2 — WR-01: exclusión mutua `day`/`window` faltante en el bootstrap

- **Problema:** `parseFilterParams` en la carga inicial podía devolver `day`
  y `window` simultáneamente (URL compartida/editada a mano, o reescrita por
  `history.replaceState`), estado que los manejadores de eventos nunca
  producen y que ANDea ambos predicados en `cardMatchesFilters`
  (`newsFilterLogic.ts`), casi siempre lista vacía sin explicación, con un
  radio de `window` marcado y una barra del histograma fijada a la vez.
- **Precedencia aplicada:** la misma que ya usan los manejadores — `day`
  gana sobre `window` (el manejador de clic en la barra hace
  `active = { ...active, day: next, window: '' }`; el manejador de
  `window` hace `active = { ...active, window: ..., day: '' }`, es decir,
  el control que el usuario acciona limpia al otro). En el bootstrap, dado
  que no hay "control accionado", se replicó la prioridad que le da la
  interacción más específica: si `active.day` está presente, se limpia
  `active.window`. Además se descarta un `day` fijado que no está en
  `dayKeys` (la ventana de 30 días renderizada), evitando el caso
  `?day=1999-01-01` que vaciaba la lista sin ningún control visualmente
  activo.
- **Archivos:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro`
  (bloque `<script>`, justo después de `parseFilterParams`, antes de la
  pre-población de controles — así el resto del bootstrap ya ve el estado
  normalizado).
- **Commit:** `63e913b` — "fix(news): normalise day/window exclusivity on initial URL parse (WR-01)".

### Salida real de los gates (tras ambos commits)

- **`npm run check`** → `Result (144 files): 0 errors, 0 warnings, 44 hints`
  (hints preexistentes, no relacionados).
- **`npm test`** → `Test Files 8 passed (8)`, `Tests 82 passed (82)`.
- **`npm run build`** → `834 page(s) built` sin errores.
- **`node scripts/validate/facets.mjs`** → `PASS facets: 1529 incidentes, 8
  familias observadas, 346 comunas cross-checked, 4 meses en unión byMonth,
  window(today=16,7d=368,30d=1493), TZ-determinism verificado, **24
  aserciones pasadas** (mismo conteo que antes de la ronda de fixes — no se
  rompió ni se añadió ninguna).
- **`npm run validate`** → `16/16 validadores PASS` (`structure, commune,
  rollout, region, crime, hreflang, schema, map, forbidden-language,
  coverage, spine, seo, figure-registry, avs-b-budget, freshness, facets`),
  `All validators passed.`

### No tocado (por alcance explícito)

`newsFacets.ts`, `newsFilterLogic.test.ts`, la lógica de facetas en
`newsFilterLogic.ts`, los strings i18n, y el punto de color de familia
(WR-02, queda como seguimiento explícito de la review, sin tocar en esta
ronda).

### Self-Check (ronda de fixes)

- FOUND commit `dcd619a` en `git log --oneline`
- FOUND commit `63e913b` en `git log --oneline`
- FOUND: bloque `@media (max-width: 860px)` en `news.astro` sin `.news-outlet { display: none }`
- FOUND: bloque `@media (max-width: 860px)` en `es/noticias.astro` sin `.news-outlet { display: none }`
- FOUND: `if (active.day) active = { ...active, window: '' };` en ambas páginas

## Self-Check: PASSED
