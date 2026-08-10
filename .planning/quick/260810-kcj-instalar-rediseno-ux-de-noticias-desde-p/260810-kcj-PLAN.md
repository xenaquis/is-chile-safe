---
id: 260810-kcj
type: quick-full
title: Instalar rediseño UX de /news/ y /es/noticias/
autonomous: true
files_modified:
  - site/src/lib/newsDayFacets.ts
  - site/src/lib/newsDayFacets.test.ts
  - site/src/lib/newsFilterLogicDay.test.ts
  - site/src/lib/newsFilterLogic.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - site/src/config/i18n.ts

must_haves:
  truths:
    - "Las páginas /news/ y /es/noticias/ renderizan la barra de filtros compacta (buscador + desplegable de región + presets) en vez de las 28 casillas apiladas"
    - "Existe un histograma de 30 días cuyas barras aíslan una fecha vía ?day=YYYY-MM-DD"
    - "El type-check del proyecto (npm run check) pasa sin errores nuevos"
    - "npm test pasa, incluyendo las dos suites nuevas (newsDayFacets.test.ts, newsFilterLogicDay.test.ts) y la suite intacta newsFilterLogic.test.ts"
    - "site/src/lib/newsFilterLogic.test.ts no tiene diff alguno y sigue verde: el paquete se instala con EXACTAMENTE DOS desviaciones deliberadas — el fix (a) en parseFilterParams y una única aserción ajustada en newsFilterLogicDay.test.ts línea 34"
    - "parseFilterParams NO emite la propiedad day cuando el parámetro está ausente o es malformado (nada de day: '')"
    - "npm run build completa; node scripts/validate/facets.mjs y npm run validate salen ambos con código 0 sobre ese mismo dist/"
  artifacts:
    - path: "site/src/lib/newsDayFacets.ts"
      provides: "Conteos por día con auto-exclusión F-28 sobre la dimensión day"
      exports: ["(según el paquete)"]
    - path: "site/src/lib/newsFilterLogic.ts"
      provides: "FilterParams con day?: string opcional, emitido SÓLO cuando es no vacío (fix a); FILTER_LOGIC_MARKER sigue siendo 'newsFilterLogic/v1'"
      contains: "newsFilterLogic/v1"
    - path: "site/src/lib/newsFilterLogicDay.test.ts"
      provides: "Cobertura aditiva de la dimensión day, con la aserción de 'defaults to empty when absent' ajustada a toBeFalsy() para acompañar el fix (a)"
      contains: "toBeFalsy"
    - path: "site/src/pages/news.astro"
      provides: "Página EN rediseñada"
    - path: "site/src/pages/es/noticias.astro"
      provides: "Página ES rediseñada"
    - path: "site/src/config/i18n.ts"
      provides: "6 claves nuevas en I18nStrings + EN_STRINGS + ES_STRINGS, con valores ES distintos de los EN"
      contains: "news_histogram_peak"
  key_links:
    - from: "site/src/pages/news.astro"
      to: "site/src/lib/newsDayFacets.ts"
      via: "import del cálculo de barras"
      pattern: "newsDayFacets"
    - from: "site/src/pages/news.astro"
      to: "site/src/config/i18n.ts"
      via: "news_histogram_peak sustituido en build (sin {n}/{date} residual en el HTML)"
      pattern: "news_histogram_peak"
    - from: "site/src/lib/newsFilterLogic.ts"
      to: "site/scripts/validate/facets.mjs"
      via: "assertion 17 lee FILTER_LOGIC_MARKER"
      pattern: "newsFilterLogic/v1"
---

<objective>
Instalar el rediseño UX de las páginas de noticias desde el paquete externo
`C:\Users\Carlo\Downloads\Optimizar diseño de comunas (1)\patch-noticias`.

Propósito: reducir de 28 controles apilados a una barra de filtros de una línea,
añadir histograma de 30 días y densificar la lista de incidentes, sin romper
ninguna de las 23+ aserciones de `scripts/validate/facets.mjs` ni la red de
seguridad `newsFilterLogic.test.ts`.

Salida: 3 archivos nuevos, 3 reemplazados, 1 parcheado a mano; build verde y
validadores en 0.
</objective>

<context>
@./CLAUDE.md
@.planning/STATE.md

Paquete (leer completo antes de tocar nada):
@C:\Users\Carlo\Downloads\Optimizar diseño de comunas (1)\patch-noticias\INSTALL.md
@C:\Users\Carlo\Downloads\Optimizar diseño de comunas (1)\patch-noticias\src\config\i18n.patch.md

Hechos verificados durante la planificación (no re-descubrir):
- `git status` limpio al planificar. Rollback = `git checkout -- <rutas>` + borrar los 3 nuevos.
- Scripts reales en `site/package.json`: `check` = `astro check`, `test` = `vitest run`,
  `build` = `cross-env ROLLOUT_ALL=true astro build`, `validate` = `node scripts/validate/all.mjs`.
- El validador vive en `site/scripts/validate/facets.mjs` (se invoca desde `site/`).
- Anclas de i18n confirmadas en `site/src/config/i18n.ts`:
  línea 151 (`I18nStrings`), línea 380 (`EN_STRINGS`), línea 614 (`ES_STRINGS`);
  las tres son la entrada `news_facet_semantics_note`. Las 6 claves son NUEVAS —
  no se edita, renombra ni borra ninguna clave existente.
- `site/src/lib/newsFilterLogic.ts` actual declara `FILTER_LOGIC_MARKER = 'newsFilterLogic/v1'`
  y el archivo del paquete lo conserva idéntico (cambio aditivo, no ruptura de contrato).
</context>

<known_defect_in_package>
**El paquete, tal cual, rompe `newsFilterLogic.test.ts`. Verificado, no hipotético.**

`parseFilterParams` del paquete (línea ~111) termina en
`return { family, region, window, q, day };` — devuelve SIEMPRE la propiedad
`day`, con valor `''` cuando el parámetro está ausente. Los tests
`site/src/lib/newsFilterLogic.test.ts:40` y `:51` comparan con `toEqual` contra
objetos literales que no incluyen `day`. Vitest ignora propiedades con valor
`undefined`, pero NO ignora una propiedad presente con valor `''`: esos dos
tests fallan de forma determinista. Y ese archivo es intocable por diseño (es
precisamente la prueba de que `day` no alteró nada previamente especificado).

**Decisión de diseño LOCKED — fix (a), no reabrir.** Se modifica el paquete, no
el test protegido. En `site/src/lib/newsFilterLogic.ts`, sustituir la línea
`return { family, region, window, q, day };` por:

```ts
  const out: FilterParams = { family, region, window, q };
  if (day) out.day = day;
  return out;
```

Nada más cambia: `serializeFilterParams` ya usa `if (params.day)` y
`cardMatchesFilters` ya evalúa `active.day` por truthiness, así que ambos siguen
siendo correctos con `day` ausente.

**Consecuencia obligatoria en el otro archivo del paquete.**
`newsFilterLogicDay.test.ts:34` afirma
`expect(parseFilterParams('').day).toBe('')`, que con el fix (a) pasa a ser
`undefined`. Ese archivo es NUEVO y del paquete — no es la red de seguridad
protegida — así que se ajusta esa ÚNICA aserción a:

```ts
    expect(parseFilterParams('').day).toBeFalsy();
```

Ninguna otra línea de ese test se toca. Las aserciones de degradación de la
línea 37-41 (`?day=yesterday`, etc.) también pasan a `undefined`; si alguna de
ellas usa `toBe('')` en el archivo real, aplicar el mismo `toBeFalsy()` y
declararlo en el SUMMARY.

Estas dos desviaciones respecto al paquete DEBEN quedar documentadas en el
SUMMARY: qué se cambió, por qué, y que `newsFilterLogic.test.ts` quedó intacto.
</known_defect_in_package>

<invariants>
Tres restricciones que impone `scripts/validate/facets.mjs`. El ejecutor NO debe
romperlas si necesita ajustar algo del markup o del CSS:

1. **La región no puede ser un `<select>`.** Assertion 18 (líneas ~774-790) exige
   `<input type="checkbox">` dentro del fieldset `data-facet="region"`, e igual
   para `data-facet="family"`. El colapso a 48 px se logra con un `<details>` que
   envuelve los MISMOS checkboxes.
2. **Ninguna regla CSS cuyo selector contenga `.news-card` puede fijar `display`.**
   Assertion 12 (línea ~573) lo comprueba por texto. El ocultado depende de
   `[hidden] { display: none }` del user agent. El grid de 4 columnas vive en
   `.news-row` (hijo). Cuidado: `.news-card > .news-row { display: grid }` TAMBIÉN
   daría rojo, porque el texto del selector contiene `.news-card`.
3. **Solo puede existir un `data-result-count-template`.** Assertion 18 quita ese
   único atributo y luego falla si queda cualquier `{n}` o `{date}` en el HTML,
   incluido el JSON inerte de `#news-facets`. Por eso `news_histogram_peak` se
   sustituye en build y el contador del desplegable de región añade un numeral
   pelado desde el cliente. No añadir una clave tipo `news_region_selected: '{n} selected'`.

También se preservan: assertion 11 (`toLocaleDateString` con `month:` siempre con
`timeZone: 'UTC'`), assertion 17 (`FILTER_LOGIC_MARKER` = `newsFilterLogic/v1`),
assertion 19 (canonical y rutas intactos; no se emite ningún enlace con `?day=` en
el markup), assertion 23/23b (`#news-facet-semantics` presente con textos EN/ES distintos).

NO TOCAR: `site/src/lib/newsFacets.ts` (contrato F-20 publicado) ni
`site/src/lib/newsFilterLogic.test.ts` (red de seguridad que demuestra que `day`
no alteró nada previamente especificado).
</invariants>

<tasks>

<task type="auto">
  <name>Tarea 1: Copiar los 6 archivos, aplicar el fix (a) y pasar el gate temprano</name>
  <files>site/src/lib/newsDayFacets.ts, site/src/lib/newsDayFacets.test.ts, site/src/lib/newsFilterLogicDay.test.ts, site/src/lib/newsFilterLogic.ts, site/src/pages/news.astro, site/src/pages/es/noticias.astro</files>
  <action>
**Paso 1 — árbol limpio.** Ejecutar `git status --porcelain` desde la raíz del
repo. Si devuelve CUALQUIER línea, DETENERSE y reportar: el rollback por
`git checkout` deja de ser seguro y el usuario debe decidir.

**Paso 2 — copiar.** Copiar los seis archivos del paquete sobre `site/src/`.
Rutas de origen con espacios y paréntesis — citarlas SIEMPRE. Origen base:
`C:/Users/Carlo/Downloads/Optimizar diseño de comunas (1)/patch-noticias/src/`

  lib/newsDayFacets.ts           -> site/src/lib/newsDayFacets.ts        (nuevo)
  lib/newsDayFacets.test.ts      -> site/src/lib/newsDayFacets.test.ts   (nuevo)
  lib/newsFilterLogicDay.test.ts -> site/src/lib/newsFilterLogicDay.test.ts (nuevo)
  lib/newsFilterLogic.ts         -> site/src/lib/newsFilterLogic.ts      (REEMPLAZA)
  pages/news.astro               -> site/src/pages/news.astro            (REEMPLAZA)
  pages/es/noticias.astro        -> site/src/pages/es/noticias.astro     (REEMPLAZA)

No copiar `INSTALL.md` ni `i18n.patch.md` al repo. No copiar el directorio
`patch-noticias` dentro de `site/`. No tocar `newsFacets.ts` ni
`newsFilterLogic.test.ts`.

**Paso 3 — fix (a), obligatorio.** En `site/src/lib/newsFilterLogic.ts`,
localizar el final de `parseFilterParams` y reemplazar

    return { family, region, window, q, day };

por

    const out: FilterParams = { family, region, window, q };
    if (day) out.day = day;
    return out;

Sin este paso, `newsFilterLogic.test.ts:40` y `:51` fallan de forma
determinista (ver `<known_defect_in_package>`). No tocar ninguna otra línea del
archivo — en particular, `FILTER_LOGIC_MARKER` y la firma de `FilterParams`
quedan como vienen del paquete.

**Paso 4 — aserción acompañante.** En `site/src/lib/newsFilterLogicDay.test.ts`,
en el test `defaults to empty when absent` (línea ~34), cambiar
`expect(parseFilterParams('').day).toBe('')` por
`expect(parseFilterParams('').day).toBeFalsy()`. Si los `toBe('')` del test de
degradación (líneas ~37-41) también rompen, aplicarles el mismo `toBeFalsy()`.
Ninguna otra línea de ese archivo se toca.

**Paso 5 — GATE TEMPRANO.** Antes de tocar i18n, ejecutar desde `site/`:
`npx vitest run src/lib/newsFilterLogic.test.ts`.
Si sale ROJO, DETENERSE y reportar como blocker — no continuar a la Tarea 2 ni
intentar arreglarlo modificando ese archivo.
  </action>
  <verify>
    <automated>cd site && git status --porcelain | sort && test -f src/lib/newsDayFacets.ts && test -f src/lib/newsDayFacets.test.ts && test -f src/lib/newsFilterLogicDay.test.ts && grep -q "newsFilterLogic/v1" src/lib/newsFilterLogic.ts && grep -q "day?: string" src/lib/newsFilterLogic.ts && grep -q "if (day) out.day = day;" src/lib/newsFilterLogic.ts && ! grep -q "return { family, region, window, q, day };" src/lib/newsFilterLogic.ts && grep -q "toBeFalsy" src/lib/newsFilterLogicDay.test.ts && git diff --name-only -- src/lib/newsFacets.ts src/lib/newsFilterLogic.test.ts | wc -l | grep -qx 0 && npx vitest run src/lib/newsFilterLogic.test.ts</automated>
  </verify>
  <done>`git status` lista exactamente 3 archivos nuevos sin trackear y 3 modificados; `newsFacets.ts` y `newsFilterLogic.test.ts` sin diff; `newsFilterLogic.ts` contiene el marcador v1, `day?: string` y el fix (a), y ya NO contiene el return con `day` incondicional; `newsFilterLogicDay.test.ts` usa `toBeFalsy`; la suite protegida `newsFilterLogic.test.ts` corre y sale VERDE.</done>
</task>

<task type="auto">
  <name>Tarea 2: Aplicar a mano las tres inserciones de i18n</name>
  <files>site/src/config/i18n.ts</files>
  <action>
Aplicar con la herramienta Edit las tres inserciones descritas en
`patch-noticias/src/config/i18n.patch.md`. Son puramente ADITIVAS: seis claves
nuevas, cero claves existentes editadas, renombradas o borradas.

1. Interfaz `I18nStrings` (~línea 151): después de `news_facet_semantics_note: string;`
   insertar el comentario NEWSUX y las declaraciones `news_histogram_label`,
   `news_histogram_peak`, `news_col_headline`, `news_col_commune`,
   `news_col_outlet`, `news_col_date` (todas `: string;`).
2. `EN_STRINGS` (~línea 380): inmediatamente DESPUÉS de la entrada
   `news_facet_semantics_note: '...'` insertar los seis valores EN literales del patch.
3. `ES_STRINGS` (~línea 614): lo mismo con los seis valores ES literales del patch.

Copiar los literales EXACTAMENTE como aparecen en el patch (incluidos los tokens
`{n}` y `{date}` de `news_histogram_peak`, y el guion largo de
`news_histogram_label`). Los valores ES son traducciones reales, NO copias del
EN: `Máximo {n} el {date}` frente a `Peak {n} on {date}`. Los números de línea
son referencias del patch: anclar por el texto de `news_facet_semantics_note`,
no por el número.

NO añadir ninguna otra clave — en particular NO añadir `news_region_selected`
(ver invariante 3).

**Si `npm run check` falla:** ejecutar `git checkout -- src/config/i18n.ts` y
reportar como blocker. NUNCA parchear encima de una inserción a medio aplicar —
i18n.ts tiene 754 líneas y lo comparte todo el sitio.
  </action>
  <verify>
    <automated>cd site && test "$(grep -c '^\s*news_histogram_peak' src/config/i18n.ts)" = 3 && test "$(grep -c '^\s*news_col_date' src/config/i18n.ts)" = 3 && test "$(grep -c '^\s*news_histogram_label' src/config/i18n.ts)" = 3 && grep -q "Peak {n} on {date}" src/config/i18n.ts && grep -q "Máximo {n} el {date}" src/config/i18n.ts && ! grep -q 'news_region_selected' src/config/i18n.ts && npm run check</automated>
  </verify>
  <done>Las seis claves aparecen tres veces cada una como DECLARACIÓN (grep anclado a inicio de línea, inmune al comentario NEWSUX que menciona `news_histogram_peak` en prosa); los valores ES difieren de los EN (`Máximo…` y `Peak…` ambos presentes); `npm run check` (astro check) pasa sin errores — TypeScript es la red que detecta si interfaz y objetos derivan.</done>
</task>

<task type="auto">
  <name>Tarea 3: Verificación completa — tests, build y validadores encadenados</name>
  <files>(ninguno — solo verificación)</files>
  <action>
Ejecutar la suite completa de verificación. El repo vive dentro de OneDrive: el
build y AMBOS validadores DEBEN ir encadenados en un solo comando, o `dist/`
puede desaparecer entre procesos y los validadores fallarán leyendo un árbol
vacío. El orden también importa por sí mismo: `facets.mjs` y `all.mjs` leen
`dist/`.

Todo desde `site/`, en una sola cadena:
  npm test && npm run build && node scripts/validate/facets.mjs && npm run validate

`npm run validate` (= `node scripts/validate/all.mjs`) es OBLIGATORIO, no
opcional: es la batería completa que detecta daño colateral del rediseño en el
resto del sitio.

Confirmar en la salida de `npm test` que corrieron las dos suites nuevas
(`newsDayFacets.test.ts`, `newsFilterLogicDay.test.ts`) Y que
`newsFilterLogic.test.ts` sigue verde sin haber sido modificada.

Si `facets.mjs` o `all.mjs` salen distinto de 0, NO parchear el markup a ciegas:
leer qué assertion falló y contrastarla con el bloque `<invariants>` de este plan
antes de tocar nada. Las tres trampas conocidas (select de región, `display` bajo
`.news-card`, segundo `data-result-count-template`) explican la mayoría de los
rojos posibles.
  </action>
  <verify>
    <automated>cd site && npm test && npm run build && node scripts/validate/facets.mjs && npm run validate && echo VALIDATE_OK</automated>
  </verify>
  <done>`npm test` verde con las dos suites nuevas ejecutadas y `newsFilterLogic.test.ts` intacta y en verde; `npm run build` completa; `facets.mjs` y `npm run validate` salen ambos con código 0 y se imprime VALIDATE_OK.</done>
</task>

</tasks>

<verification>
- `git status` muestra exactamente 7 rutas afectadas (3 nuevas, 4 modificadas incl. i18n.ts).
- `site/src/lib/newsFacets.ts` y `site/src/lib/newsFilterLogic.test.ts` sin diff.
- `newsFilterLogic.ts` contiene el fix (a); `newsFilterLogicDay.test.ts` usa `toBeFalsy()`.
- `npm run check` limpio.
- `npm test` verde, con las 2 suites nuevas presentes en la salida.
- `npm run build && node scripts/validate/facets.mjs && npm run validate` termina en 0.
</verification>

<success_criteria>
Rediseño instalado, type-check limpio, suite de tests verde (incl. las dos nuevas
y la vieja intacta), build completa y ambos validadores en 0 — sin haber tocado
`newsFacets.ts` ni `newsFilterLogic.test.ts`, sin haber roto ninguno de los tres
invariantes documentados, y con las dos desviaciones respecto al paquete (fix (a)
y la aserción `toBeFalsy()`) documentadas en el SUMMARY.
</success_criteria>

<rollback>
git checkout -- site/src/pages/news.astro site/src/pages/es/noticias.astro site/src/lib/newsFilterLogic.ts site/src/config/i18n.ts
rm site/src/lib/newsDayFacets.ts site/src/lib/newsDayFacets.test.ts site/src/lib/newsFilterLogicDay.test.ts
No hay migraciones de datos ni cambios en `public/data/`.
</rollback>
