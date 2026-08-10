---
id: 260810-ocs
title: Instalar rediseño Comparador v2 (propuesta 4b) desde paquete install-comparar
type: quick
executed_via: dynamic-workflow (sonnet ejecutor, opus verificador, fable estratega/validador)
premortem: wf_5d4dbfb6-e5f (3 revisores opus — 27 hallazgos, 1 BLOCKER, consolidados abajo)
must_haves:
  truths:
    - "Color de comuna = SIEMPRE posición en `selected` (píldora, punto, cifra, tarjeta, homicidios) — CX-A1 BLOCKER."
    - "?a=&b=(&c=) precarga: el efecto de sincronía de URL NO borra la query antes de la preselección — CX-A3/C1."
    - "latestCompleteYear por VALOR (Math.max de no-partial); composite_index por su propia última clave; homicidios solo de featured_rates, tasa gate (0 válido), conteo opcional (WR-01/WR-05/HOM-02/Pitfall 1)."
    - "FAMILY_KEYS = las mismas 7 claves CEAD (sin sexuales); ninguna tasa se re-escala."
    - "Nunca calificar comunas de 'seguras/peligrosas'; puesto nacional direccional y atribuido (1 = mayor incidencia reportada, CEAD)."
    - "El island NO importa config/i18n.ts; cmp_* llegan por prop; cx_* desde comparatorStrings.ts sin imports."
    - "No se tocan: [pair].astro (EN/ES), i18n.ts, data.ts, formatNumber.ts, global.css, BaseLayout, MethodologyCaveat, ComparatorPairsLinks, comparator-pairs.json, mapa."
  artifacts:
    - "site/src/config/comparatorStrings.ts"
    - "site/src/islands/ComparatorIsland.tsx"
    - "site/src/pages/compare/index.astro"
    - "site/src/pages/es/comparar/index.astro"
  key_links:
    - "site/scripts/validate/all.mjs (16 validadores; avs-b-budget CMP-03/CMP-05, spine, figure-registry, forbidden-language)"
---

# Plan: instalar Comparador v2 (4b) + fixes de premortem

## Contexto

Paquete: `C:/Users/Carlo/Downloads/Optimizar diseño de comunas (3)/install-comparar` (INSTALL.md es la autoridad de alcance).
Repo: `C:/Users/Carlo/OneDrive - pjud.cl/Documentos/GitHub/Is Chile Safe` (OneDrive: encadenar build+validate en UN comando; citar TODAS las rutas — llevan espacios y paréntesis).

Premortem (3 opus) verificó limpio: firmas loadIndex/loadRegion/regionFileId y campo low_population existen; title/description/hreflang/noscript byte-idénticos; 19 claves cx_* completas EN/ES; ningún validador depende del island (avs-b-budget cuenta archivos y dirs `*-vs-*` de [pair].astro, que no se toca); figure-registry barre los archivos nuevos → 0 matches; tokens CSS todos existentes; sharedYear real = 2025 (2026 partial).

## Tarea 1 — Copiar los 4 archivos del paquete

```bash
cp "C:/Users/Carlo/Downloads/Optimizar diseño de comunas (3)/install-comparar/site/src/config/comparatorStrings.ts"  "site/src/config/"
cp "C:/Users/Carlo/Downloads/Optimizar diseño de comunas (3)/install-comparar/site/src/islands/ComparatorIsland.tsx" "site/src/islands/"
cp "C:/Users/Carlo/Downloads/Optimizar diseño de comunas (3)/install-comparar/site/src/pages/compare/index.astro"    "site/src/pages/compare/"
cp "C:/Users/Carlo/Downloads/Optimizar diseño de comunas (3)/install-comparar/site/src/pages/es/comparar/index.astro" "site/src/pages/es/comparar/"
```

## Tarea 2 — Aplicar fixes del premortem (sobre los archivos copiados)

Todos en `site/src/islands/ComparatorIsland.tsx` salvo donde se indique.

1. **CX-A1 (BLOCKER) color por slot.** Sustituir todo uso de `colorOf(i)` donde `i` es índice de `loadedRows` (chartRows cells, tarjetas, homicidios) por color derivado de la posición en `selected`: `const colorFor = (id: string) => colorOf(selected.findIndex(c => c.id === id));`. Las píldoras pueden seguir con `colorOf(i)` sobre `selected`.
2. **CX-A3/C1 (HIGH) preselección URL.** Añadir `const initializedRef = useRef(false);` — primera línea del efecto de sincronía de URL: `if (!initializedRef.current) return;`. En el efecto de preselección, poner `initializedRef.current = true;` SIEMPRE (haya o no params válidos), tras procesarlos.
3. **CX-B6 (LOW, junto con el anterior) URL no destructiva.** Reescribir el efecto de sincronía con `const u = new URL(window.location.href); u.searchParams.delete('a'); ...delete('b'); ...delete('c');` luego `set` solo los presentes; `replaceState(null, '', u.pathname + u.search)`. Conserva utm_* y demás.
4. **CX-A2/C3 (HIGH) ordenar sin perder comunas.** El onClick de `.cmp-sort` ordena `selected` completo: cargadas por `rate_per_100k` desc, no-cargadas al final en su orden actual. Nunca eliminar entradas.
5. **CX-A4 (HIGH) national ausente ≠ años mixtos.** `const natMissing = nationalData === null || natYear === null;` y `const mixedYears = !natMissing && sharedYear === null && loadedRows.length > 0;`. Con `natMissing`, no mostrar `cx_mixed_years` ni la leyenda de línea nacional (no hay línea); las cifras siguen rotuladas por año de comuna (ver 6).
6. **CX-C4/A8/B2/B3 (HIGH) coherencia de año en modo mixto.** Cuando `mixedYears`: (a) la cabecera NO imprime `cx_reference_year` (el aviso `cx_mixed_years` ya enumera comuna+año) — eliminar el fallback `natYear` de ese span; (b) bloque homicidios: año por ítem (`{name} · {year}`) y suprimir la nota global `cmp_homicide_row` con año único; con año compartido, conservar conducta actual; (c) tarjetas: ocultar el % sobre/bajo la nacional (`diff`) cuando `mixedYears || natMissing`.
7. **CX-A5/C5 (MEDIUM) año del índice compuesto.** El chip de banda añade su propio año: `{score} · {banda} ({ciYear})`.
8. **CX-A7/B1 (MEDIUM) enlace metodología.** Junto al chip: `<a className="cmp-what" href={lang === 'es' ? '/es/metodologia/' : '/methodology/'}>{s.cmp_what_is_this}</a>` (añadir clase con estilo discreto tipo texto-label).
9. **CX-A6/B4 (MEDIUM) rank direccional — editar `site/src/config/comparatorStrings.ts`.** `cx_rank_line` EN: `'Rank {rank} of 346 — 1 = highest reported incidence (CEAD)'`; ES: `'Puesto {rank} de 346 — 1 = mayor incidencia reportada (CEAD)'`.
10. **CX-A9 (MEDIUM) una sola etiqueta para la línea nacional.** Leyenda: solo `cx_national_line` (eliminar `· {s.cmp_avg_column}`). `<th>` final de la sr-table: `t.cx_national_line` en vez de `s.cmp_avg_column`.
11. **CX-A10/C8 (LOW) fuente y año en textos — `comparatorStrings.ts`.** `cx_scale_note` y `cx_table_caption`: añadir `' Fuente: CEAD.'` / `' Source: CEAD.'`. En la sr-table, cada `<th>` de comuna imprime `{name} ({yearFor})` cuando `mixedYears`.
12. **CX-A11/C6 (MEDIUM) targets 44px.** `.cmp-tag-x`: área táctil 44×44 (glifo 30px centrado, p.ej. `width:44px;height:44px;margin:-7px 0` o padding equivalente sin romper el alto de la píldora); `.cmp-sort { min-height: 44px; }`.
13. **CX-C7 (LOW) fallback oklch.** En el `<style>` del island, dar `background` hex de reserva a `.cmpx-dot`, `.cmp-tag-dot`, `.cmpx-val-dot` (gris neutro `#8892a0`): si el navegador descarta el oklch inline, cae al gris visible, no a transparente.
14. **CX-C10 (LOW) reintento tras fetch fallido.** En `fetchCommune`, si `data === null` → `requested.current.delete(id)`.
15. **CX-B5 (LOW) contexto baja población.** Pasar `low_pop_footnote` en el objeto `strings` de AMBAS páginas y usarlo como `title` del span `.cmp-option-lowpop`.

**Rechazado (no aplicar):** reformular `cmp_homicide_no_data` (CX-C9) — exigiría editar `i18n.ts`, fuera del alcance del paquete; paridad con conducta actual. Documentar como deuda conocida en SUMMARY.

## Tarea 3 — Gates

Desde `site/`, UN comando encadenado (OneDrive): `npm run check && npm test && npm run build && npm run validate`.
Baseline conocido: warning preexistente en `ComparatorPairsLinks.astro:27` (no lo toca este paquete); 16/16 validadores verdes.
Si falla algo nuevo → corregir en los archivos instalados, nunca parchear validadores ni suprimir con @ts-ignore.

Commit atómico al pasar: `feat(comparar): install Comparador v2 (propuesta 4b) from install-comparar package` + cuerpo con lista de fixes CX-* aplicados.

## Verificación (opus, post-ejecución)

- grep sin `getFullYear` nuevo; `colorFor(` usado en cells/tarjetas/homicidios; `initializedRef` presente y consultado en el efecto de sincronía; `searchParams.delete` presente.
- `git diff --stat HEAD~1` toca EXACTAMENTE los 4 archivos.
- `[pair].astro`, `i18n.ts`, `data.ts`, `global.css`, `MethodologyCaveat.astro`, `ComparatorPairsLinks.astro` intactos.
- En dist/: `/compare/` y `/es/comparar/` con h1/lead/caveat/noscript pre-renderizados; hreflang recíproco.
- Strings: `cx_rank_line` direccional+CEAD en EN y ES; sin "seguro/peligroso" (ni "safe/dangerous" calificativo) en los 4 archivos.
- sr-table conserva clip-rect (no display:none); `role="img"` + aria-label por fila.

## Rollback

`git checkout -- "site/src/islands/ComparatorIsland.tsx" "site/src/pages/compare/index.astro" "site/src/pages/es/comparar/index.astro" && rm "site/src/config/comparatorStrings.ts"` (o `git revert` si ya hay commit).
