# Quick 260810-l3e — Revisión adversarial contra el código real

**Alcance:** commit `d361a1a` (`feat(rankings): install Rankings v2 ...`), 7 archivos.
**Método:** lectura del diff real contra `d361a1a^`, inspección del `dist/` construido a las 15:37
(mismo build que pasó los gates), diff estructural normalizado EN/ES, y verificación de datos contra
`data/cead/comunas/*.json`.
**Explícitamente NO repetido:** todo lo que cubren los 16 validadores (`crime.mjs`, `spine.mjs` G/H/L,
`seo.mjs`, `coverage.mjs`, `hreflang.mjs`, `schema.mjs`, `forbidden-language.mjs`, `figure-registry`
DOCS-01), `astro check` y `vitest`. Todos verdes; no se re-auditó lo que ya asertan.

---

## 1. XSS — limpio (sin hallazgos)

Se rastreó el término del usuario extremo a extremo:

| Punto | Verificado |
|---|---|
| `?q=` (URL) → `input.value` | asignación a la propiedad `value`, nunca `innerHTML` (`RankingBoard.astro:459-460`) |
| `input.value` → `state.q` | `input` listener, sin interpolación (`:405`) |
| `state.q` → filtrado | `norm()` + `indexOf`, sin `RegExp` construido con la query (no hay ReDoS ni inyección de patrón) |
| `state.q` → DOM | `paint()` (`:315-332`) **nunca inserta la query**: parte el `data-name` *confiable* por índice, con `createTextNode` + `document.createElement('mark')` + `textContent`. El `<mark>` no lleva ni un carácter proveniente del usuario |
| Payload servidor→cliente | `<script type="application/json" id="rk-data" set:html={JSON.stringify(...).replace(/</g,'\\u003c')}>` (`:231`). El escape de `<` cierra la vía `</script>`; se verificó en `dist/**/index.html` que el JSON servido no contiene ningún `<` literal |
| Atributos `style` inline | sólo `FAMILY_ACCENT` (constante del repo) y números calculados |
| `title={c.def}` (hub) | atributo, escapado por Astro |

`<img src=x onerror=alert(1)>` como query: no coincide con ningún `data-norm`, la tabla queda vacía y
no se escribe nada en el DOM. **Sin hallazgos de XSS.**

Detalle menor: una query compuesta **sólo** por combining marks (p. ej. pegar `U+0301`) normaliza a `''`;
`indexOf('')` devuelve 0 y `paint()` inserta un `<mark>` vacío en cada fila visible. Inocuo, pero es
código muerto evitable → F-10.

---

## 2. Corrección al combinar año + región + excluir + orden + buscar

Se recorrió `render()` (`:334-403`) buscando estados alcanzables incoherentes.

**Lo que está bien y conviene dejar registrado:**

- **No hay flicker de hidratación.** Se verificó contra el dato: los 346 comunas tienen
  `latestCompleteYear = 2025` y ninguna carece de `featured_rates.homicidios[2025]`, así que
  `rate` (servidor) === `ratesByYear[latestYear]` (cliente) para las 8 familias. El `mean`, el
  `maxRate`, el `count` (256 de 346) y el rank que recalcula el cliente en el primer `render()`
  coinciden exactamente con lo pre-renderizado. B-02 quedó bien resuelto.
- **El orden de desempate es estable.** `rows` se construye una sola vez desde el DOM servidor
  (ya ordenado desc), y `render()` reordena nodos sin reconstruir `rows`; `Array.sort` es estable,
  así que los empates (muchos ceros en homicidios) no bailan entre renders.
- **`rows.forEach(hidden=true)` + re-append por `DocumentFragment`** es correcto: las filas ocultas
  quedan al principio del `<tbody>` y las visibles al final en orden; el crawler sin JS ve el orden
  servidor.
- **`hidden` no está saboteado por ninguna regla de autor.** Se revisó `global.css` (sólo
  `p { font-size/weight/line-height }`, sin `display`) y el `<style>` del componente: ni `tr`, ni
  `#rk-clear`, ni `#rk-more`, ni `#rk-empty`, ni `#rk-yearnote` reciben `display`. **No** se repite
  el bug de los chips fantasma. Pero tampoco hay guardia defensiva → F-08.
- **La media es nacional y NO se filtra por región** (a pesar de lo que sugiere el INSTALL.md §1),
  coherente con la etiqueta "Media nacional / National average". Correcto tal cual está.

**Hallazgos:** F-04 (foco), F-06 (`dirty` ignora el orden), F-07 (año en el H2 sr-only), F-10.
Un riesgo latente adicional: el rank del último año se **recalcula** en cliente y pisa el
`national_rank` pre-renderizado (`:339-341, :360`). Hoy coinciden al dígito, pero si el sitio cambia
la regla de `national_rank` (empates, exclusiones), el cliente lo sobrescribiría en silencio; lo más
barato sería leer el texto ya servido en vez de recalcularlo — anotado dentro de F-06.

---

## 3. Sin JS

Verificado sobre `dist/es/ranking-delito/robos-violentos/index.html` (536.919 bytes):

| Elemento | Resultado |
|---|---|
| Filas `<tr data-name>` | **346** |
| `href="/es/comuna/"` | **346** |
| Chips `<a class="rk-chip">` | **8** (reales, con `href`) |
| Panel regional `<a class="rk-reg">` | **16** (reales, a `/es/region/...`) |
| `#rk-more`, `#rk-clear`, `#rk-empty`, `#rk-yearnote` | salen con `hidden` → invisibles sin JS ✔ |
| Script cliente | `<script type="module" src>` (diferido, no bloquea) |

Es decir: el contrato SEO del INSTALL se cumple. **Pero** el buscador, el `<select>` de región, los
dos botones de orden, el toggle de baja población y el `<select>` de año se renderizan siempre y son
inertes sin JS → F-11 (INFO: es el mismo patrón que ya usan `CommuneDirectory` y `news.astro`, no es
una regresión de este commit).

---

## 4. Accesibilidad

Bien: `aria-current="page"` en el chip activo; `<nav aria-label>`; `<aside aria-label>` con nombre
accesible (por HTML-AAM sigue mapeando a `complementary` pese al anidamiento); `aria-pressed`
sincronizado en los botones de orden y en el toggle; `aria-live="polite"` en el contador;
`.sr-only` real (no `display:none`); el `<input type="search">` obtiene su nombre del `aria-label`
(el `<label>` que lo envuelve sólo contiene un SVG `aria-hidden`).

Hallazgos: F-03 (rol/estado del panel regional + ctrl+click), F-04 (pérdida de foco), F-05
(`<th>` sin `scope`), F-02 (jerarquía de encabezados / `p` haciendo de heading), F-07 (año obsoleto
en el H2 sr-only), F-15 (6 enlaces con el mismo texto en el hub).

---

## 5. Paridad EN/ES

Diff estructural normalizado (esqueleto de tags + `class` + `id`) entre
`dist/crime-ranking/violent-robbery/` y `dist/es/ranking-delito/robos-violentos/`:
**8.379 vs 8.377 nodos, 16 líneas de diff**, todas atribuibles al layout base
(un `<script>` extra en EN y el orden del `lang-toggle`). **Paridad estructural correcta.**

Hub: ambos con 1 `<h1>`, 6 enlaces `hub-card-def`, 16 enlaces de región. El ES gana los 16 enlaces
regionales (decisión locked del usuario) con `regionNameEs()` aplicado correctamente
("Región del Maule", "Región del Biobío", "Región Metropolitana"). ✔

Divergencias de contenido (no estructurales): F-14 (gramática del H1 ES, preexistente) y F-16
(el hub ES perdió el enlace inline a `/es/mapa/`; ambos hubs perdieron la línea "Fuente: CEAD —" del
pie, aunque CEAD sigue atribuido en el párrafo lead).

---

## 6. Editorial

- Ninguna calificación absoluta de territorio: la palabra "seguro/peligroso/safe/dangerous" no
  aparece en `RankingBoard`, `RankingHub` ni `rankingStrings.ts` (y `forbidden-language.mjs` barre
  el `dist/`). ✔
- Atribución: `rk_source_note` ("Fuente: CEAD, casos policiales reportados") en cada página de
  ranking; `rk_hub_lead` nombra al CEAD en el hub; `Dataset` JSON-LD con `creator` CEAD. ✔ (ver F-16
  para el matiz del pie del hub).
- **Dirección del rank etiquetada:** el `<th>` sólo dice "Posición"/"Rank", pero la dirección está
  (a) en el H1 "…con mayor incidencia…/…highest reported…", (b) en `rk_source_note` "Posición 1 =
  mayor incidencia reportada del tipo de delito seleccionado", (c) en el `ItemList` con
  `order: Descending`. Cumple la convención `national_rank #1 = MÁS delito`. Con orden = "Menor"
  la columna sigue mostrando la posición descendente (#346, #345 …), que es lo correcto y no induce
  a error.
- Baja población: 90 filas con `data-lowpop="1"`, chip `*baja pob.` con el asterisco que la nota al
  pie referencia (B-04 ✔) y `—` en la columna de posición.

---

## 7. La decisión "guion" — implementada y coherente

`RankingBoard.astro:360`

```js
r.rank.textContent = r.lowpop || state.year !== D.latestYear ? '—' : '#' + rankOf.get(r);
```

Precedencia correcta (`(a||b) ? x : y`). La nota que la acompaña
(`rk_rank_year_note`, mostrada exactamente cuando `state.year !== D.latestYear`, `:380`) dice
*"La posición se publica solo para 2025 (CEAD, último año completo); para otros años compara la tasa
por 100.000"* — explica **ocultación**, no cálculo. Coherente con el guion, con `rk_source_note` y
con el comportamiento de `safest-cities-in-chile` (que no se tocó). **Decisión implementada de
verdad.** Dos matices menores: `rankOf` se sigue computando aunque no se use fuera del último año
(coste trivial), y el `—` del año no-último es tipográficamente indistinguible del `—` de baja
población — la nota lo desambigua, pero sólo si el usuario la lee.

---

## Hallazgos accionables

| ID | Sev | Dónde | Qué |
|---|---|---|---|
| F-01 | MEDIUM | `RankingHub.astro:77-80` | `/crime/homicide/` y `/es/delito/homicidios/` bajan de 2 a **1** enlace entrante en todo el sitio |
| F-02 | MEDIUM | `crime-ranking/[crime].astro:193-196` + gemela ES | 16 páginas quedan con 0 `<h2>` visibles |
| F-03 | MEDIUM | `RankingBoard.astro:433-442` | `preventDefault()` incondicional mata ctrl/cmd-click; estado del filtro sólo en una clase CSS |
| F-04 | LOW | `RankingBoard.astro:376-378, 400-401` | El botón activado se auto-oculta y el foco cae al `<body>` |
| F-05 | LOW | `RankingBoard.astro:190-195` | `<th>` perdió `scope="col"` respecto de la tabla que reemplaza |
| F-06 | LOW | `RankingBoard.astro:400` | `dirty` ignora `state.dir` (y el rank del último año se recalcula en cliente) |
| F-07 | LOW | `crime-ranking/[crime].astro:194` + ES | H2 sr-only fija `(2025)` y nunca se actualiza al cambiar de año |
| F-08 | LOW | `RankingBoard.astro:466-738` | Falta la guardia `[hidden]{display:none}` que sí tiene `CommuneDirectory` |
| F-09 | LOW | `CommuneDirectory.astro:333, 715` | B-07/B-08 no retro-portados al directorio |
| F-10 | LOW | `RankingBoard.astro:320-332` | `<mark>` vacío cuando la query normaliza a `''` |
| F-11 | INFO | `RankingBoard.astro:128-156` | 5 controles inertes sin JS (patrón ya existente en el sitio) |
| F-12 | INFO | `RankingBoard.astro:734-738` | En móvil se pierden región (columna) y tendencia (columna eliminada) |
| F-13 | INFO | build | 536 KB por página × 16; 220 KB son `data-rates` |
| F-14 | LOW | `es/ranking-delito/[crime].astro:182` | "de incivilidades **reportados**" (concordancia), preexistente |
| F-15 | LOW | `RankingHub.astro:107-109` | 6 enlaces con texto idéntico y destinos distintos |
| F-16 | INFO | `RankingHub.astro` | El hub ES perdió el enlace a `/es/mapa/`; ambos, la línea "Fuente: CEAD" del pie |

### F-01 — el hub dejó de enlazar la página de familia de homicidios

Antes (`d361a1a^:site/src/pages/rankings.astro`) el hub recorría las **7** entradas de
`FAMILY_SLUGS` y emitía 7 enlaces `/crime/{slug}/`, incluido `vida → /crime/homicide/`.
Ahora `familyHref` es `null` cuando `def.familyKey === 'vida'` (B-03) **y** cuando no hay slug
(caso `homicidios`, que no es clave de `FAMILY_SLUGS`), así que salen 6.

Medido sobre el `dist/` actual:

```
href="/crime/homicide/"        → 1 página entrante  (sólo dist/glossary/)
href="/es/delito/homicidios/"  → 1 página entrante
href="/crime/property/"        → 349 páginas entrantes
```

`coverage.mjs` sólo falla con **0** entrantes, por eso pasó en verde. La motivación de B-03 (la
memoria `vida/homicide slug collision`) es evitar emitir un enlace *duplicado y mal etiquetado* como
"Homicide"; aquí el texto del enlace es el genérico "What this category covers", así que enlazar la
tarjeta `vida` a `/crime/homicide/` no reproduce esa colisión.

**Fix:** en `RankingHub.astro:77-80`, permitir `vida` (`familySlug ? ... : null`, sin la exclusión de
`'vida'`) y dejar `homicidios` en `null`, o bien dar a la tarjeta `homicidios` el mismo destino con
un `aria-label` explícito. Volver a medir los entrantes tras el cambio.

### F-02 — las páginas de ranking se quedaron sin encabezados visibles

Encabezados reales de `dist/crime-ranking/violent-robbery/index.html`:

```
h1           Communes with the highest reported violent robbery incidence in Chile
h2 SR-ONLY   Communes ranked by violent robbery rate per 100,000 inhabitants (2025)
```

La versión anterior tenía dos `<h2>` visibles ("Communes ranked by …" y "Regional breakdown — …").
El título del panel regional es hoy un `<p class="rk-regions-h">` con estilo de encabezado
(`RankingBoard.astro:160`), así que tampoco aparece en el mapa de encabezados. Afecta a 16 páginas
programáticas cuyo contenido son 346 filas.

**Fix:** hacer visible el `<h2>` de la sección de ranking (o añadir uno) y convertir
`.rk-regions-h` en `<h3>` (o `<p role="heading" aria-level="3">` si el estilo lo exige).

### F-03 — el panel regional rompe ctrl+click y no expone su estado

```js
a.addEventListener('click', (ev) => { ev.preventDefault(); ... });
```

`preventDefault()` se ejecuta siempre, así que ctrl/cmd/shift+click sobre una barra regional ya no
abre `/region/...` en una pestaña nueva — pese a que el elemento es un `<a href>` y el INSTALL.md §5c
lo justifica precisamente como "enlaces útiles". Además, el estado activo del filtro se comunica sólo
con `a.classList.toggle('on', ...)` (`:397`): para un lector de pantalla el elemento sigue siendo un
enlace normal y no hay indicación de que 1 de las 16 regiones está seleccionada.

**Fix:** `if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0) return;` antes
del `preventDefault()`, y añadir `a.setAttribute('aria-current', on ? 'true' : 'false')` junto al
`classList.toggle` (`aria-pressed` no es válido en `role=link`).

### F-04 — el foco se pierde al ocultar el botón que el usuario acaba de pulsar

`moreBtn.hidden = rest <= 0` (`:377`) y `clearBtn.hidden = !dirty` (`:401`) se ejecutan dentro del
`render()` disparado por el click sobre esos mismos botones. Al último "Ver más" (o al pulsar
"Limpiar filtros"), el elemento enfocado desaparece y el foco vuelve al `<body>`: el usuario de
teclado pierde su posición y tiene que tabular desde el principio de la página.

**Fix:** antes de ocultar, mover el foco a un destino estable (p. ej. `#rk-count`, con `tabindex="-1"`,
o la primera fila recién añadida).

### F-05 — `<th>` sin `scope="col"`

La tabla anterior emitía `<th scope="col">` en las 5 columnas; la nueva
(`RankingBoard.astro:190-195`) emite `<th class="c-rank">` etc. sin `scope`. Es una regresión directa
sobre una tabla de datos de 346 filas y 4 columnas.

**Fix:** añadir `scope="col"` a los cuatro `<th>`.

### F-06 — "Limpiar filtros" ignora el orden (y el rank se recalcula)

`const dirty = !!(state.q.trim() || state.region || !state.hideLowpop || state.year !== D.latestYear);`
no incluye `state.dir`. Con sólo cambiar a "Menor" el botón sigue oculto, pero si más tarde aparece
por otro filtro y el usuario lo pulsa, el orden también se reinicia sin aviso.
En el mismo bloque: `rankOf` (`:339-341`) recalcula la posición del último año en cliente y pisa el
`national_rank` pre-renderizado; hoy coinciden exactamente, pero es una fuente de divergencia
silenciosa si cambia la regla del campo precalculado.

**Fix:** añadir `|| state.dir !== 'desc'` a `dirty`; opcionalmente, guardar el texto servido del rank
al construir `rows` y restaurarlo en vez de recalcularlo.

### F-07 — el año del H2 sr-only nunca se actualiza

`crime-ranking/[crime].astro:194` (y la gemela ES `:194`) interpolan `({latestYear})` en un `<h2>`
que el script no toca. Al elegir 2018 en el selector, la tabla, la media y el panel muestran 2018,
pero el único encabezado de la sección — el que oyen los usuarios de lector de pantalla — sigue
diciendo 2025. La versión anterior mantenía sincronizado un `<span data-year-target>`.

**Fix:** dar un `id` al año dentro del H2 y actualizarlo en `render()` (una línea), o quitar el año
del encabezado.

### F-08 — falta la guardia `[hidden]`

Hoy funciona: no hay regla de autor con `display` sobre `tr`, `p` o `button`. Pero el repo ya se
quemó con esto (memoria `Astro scoped style defeats [hidden]`) y `CommuneDirectory.astro:636-638`
lleva la guardia explícita; `RankingBoard` no. Cualquier futuro `display:flex` en `.rk-note`,
`.rk-empty` o en `tbody tr` reabre el bug con 286 filas fantasma.

**Fix:** añadir al `<style>`
`#rk-clear[hidden], #rk-more[hidden], #rk-empty[hidden], #rk-yearnote[hidden], .rk-table tbody tr[hidden] { display: none !important; }`.

### F-09 — retro-portar B-07 y B-08 al directorio de comunas

Los dos bugs que el premortem corrigió aquí siguen vivos en el componente hermano:

- `CommuneDirectory.astro:715` — `mark { background:#ffe9a8 }` se compila como
  `mark[data-astro-cid-jda2hpxv]` (verificado en `dist/_astro/CommuneDirectory.Bc8D7up0.css`), y el
  `<mark>` que crea el JS no lleva ese atributo: el resaltado del directorio nunca recibe el color
  de marca (queda con el amarillo por defecto del navegador). En `RankingBoard` el `:global(mark)`
  sí compila a `mark{...}`.
- `CommuneDirectory.astro:333` — `r.name.slice(i, i + q.length)` usa la longitud de la query **cruda**
  sobre un índice calculado con la query **normalizada** (exactamente B-08).

**Fix:** `:global(mark)` y `nq.length` en el directorio (dos líneas), fuera de este commit.

### F-10 — `<mark>` vacío

`paint()` entra en la rama de resaltado si `q` (crudo) es truthy, pero calcula el índice con `nq`
(normalizado). Si la query son sólo combining marks, `nq === ''`, `indexOf('') === 0` y se inserta un
`<mark></mark>` vacío en cada fila visible.

**Fix:** `if (!q || !nq) { r.nm.textContent = r.name; return; }`.

### F-11 / F-12 / F-13 / F-16 — informativos

- **F-11:** buscador, `<select>` de región, botones de orden, toggle de baja población y `<select>` de
  año se sirven siempre y no hacen nada sin JS. No es una regresión (mismo patrón que
  `CommuneDirectory` y `news.astro`), pero la checklist del INSTALL.md §6 no lo cubre; si se quiere
  cerrar, el patrón habitual es ocultar `.rk-bar` por defecto y desocultarla desde el script.
- **F-12:** bajo 700 px se ocultan `td.c-bar` y `.rg`. La región deja de estar en la tabla (antes tenía
  columna propia) y la tendencia desapareció del todo con `TrendChip`. En móvil, la única vía a la
  región es el panel lateral.
- **F-13:** `dist/crime-ranking/violent-robbery/index.html` = 536.178 B; `…/es/robos-violentos/` =
  536.919 B. De ahí, **220.630 B son los atributos `data-rates`** (21 años × 346 comunas). El
  `data-rates` ya existía (lo consumía `RankingTableEnhancer`), así que no es deuda nueva, pero es el
  80 % del margen de mejora si alguna vez hay presupuesto de página (p. ej. emitir un único
  `application/json` con la matriz año×comuna en lugar de 346 atributos).
- **F-16:** el hub ES anterior enlazaba `/es/mapa/` en el párrafo "Por región" y ambos hubs cerraban
  con "Fuente: CEAD — Centro de Estudios y Análisis del Delito." antes del enlace a Metodología.
  Lo primero es un enlace interno perdido; lo segundo no rompe la regla de atribución (CEAD sigue
  nombrado en `rk_hub_lead`), pero era una atribución explícita al pie.

### F-14 — concordancia del H1 ES (preexistente)

`Comunas con mayor incidencia de {familyLabel.toLowerCase()} reportados en Chile` produce
"…de incivilidades **reportados**…", "…de violencia intrafamiliar **reportados**…". Idéntico en
`d361a1a^` (no lo introduce este commit), pero está en el H1 de 8 páginas indexables en el idioma
principal del mercado local.

**Fix:** quitar "reportados" del H1 (la palabra "reportada" ya vive en el explainer y en
`rk_source_note`) o mover el participio al sustantivo neutro: "…de casos reportados de {familia}…".

### F-15 — 6 enlaces con el mismo texto

`RankingHub.astro:107-109` emite seis veces "What this category covers →" / "Qué incluye esta
categoría →" hacia seis URLs distintas. El `title={c.def}` no sustituye a un nombre accesible.

**Fix:** `aria-label={`${r.rk_hub_card_def} — ${c.label}`}` en cada enlace.
