---
id: 260810-rdf
title: Instalar rediseño Landing v2 (propuesta 6b) desde paquete install-landing
type: quick
executed_via: dynamic-workflow (sonnet ejecutor, opus verificador, fable estratega/validador)
premortem: wf_4283fe0e-96c (3 revisores opus — 32 hallazgos: 3+2+3 BLOCKER dedup a 3, resto HIGH/MEDIUM/LOW; consolidados abajo)
must_haves:
  truths:
    - "Cero directivas client:* en el home (D-05/D-06); toda la interactividad es <script> vanilla con baseline server-rendered."
    - "Un solo H1 por página, verbatim el actual; prosa 'Sobre los datos'/'About the Data' verbatim."
    - "Form GET baseline idéntico: /communes/?q= | /es/comunas/?q= — Enter sin sugerencia funciona igual que hoy."
    - "Tone Guard: ninguna string nueva califica territorios; atribución CEAD presente; tasas per-100k jamás re-escaladas."
    - "hrefs hardcodeados por locale; texto de incidentes vía textContent; enlaces externos rel=noopener; fetch de current.json falla en silencio (D-15)."
    - "Ningún archivo compartido se toca: HomeLayout, BaseLayout, global.css, i18n.ts, data.ts, jsonld.ts, colorScale.ts, familyDefs.ts, CommuneRankingTable, RankingTableEnhancer quedan intactos. Cero ediciones fuera de los 8 archivos del paquete."
    - "Todo nodo creado por JS debe recibir estilo: reglas de clases runtime en :global() namespaced (LPX-1) — verificar en dist/ que no queden compiladas con [data-astro-cid-*]."
    - "El home no desborda horizontalmente en ningún ancho; el grid no usa minmax con mínimo fijo."
  artifacts:
    - "site/src/config/homeV2Strings.ts"
    - "site/src/components/home/homeData.ts"
    - "site/src/components/home/HomeSearchLive.astro"
    - "site/src/components/home/HomeMiniMap.astro"
    - "site/src/components/home/HomeExtremes.astro"
    - "site/src/components/home/HomeNewsPulse.astro"
    - "site/src/pages/index.astro"
    - "site/src/pages/es/index.astro"
  key_links:
    - "Paquete: C:/Users/Carlo/Downloads/Optimizar diseño de comunas (6)/install-landing (INSTALL.md = autoridad de alcance)"
    - "Premortem completo: subagents/workflows/wf_4283fe0e-96c/premortem-findings.txt"
---

# Plan: instalar Landing v2 (6b) + fixes de premortem

## Contexto

Home 4-pantallas → panel de una pantalla: hero + búsqueda viva, franja de stats,
píldoras de exploración, mini-mapa SVG build-time, extremos con toggle
Mayor/Menor, pulso de noticias. Repo en OneDrive: encadenar gates en UN comando;
citar TODAS las rutas (espacios y paréntesis).

El premortem verificó limpio: firmas de data.ts/jsonld.ts/colorScale.ts, tokens
CSS (24/24 existen), H1 y prosa verbatim, contrato HomeLayout idéntico, todas
las rutas de píldoras existen, NFD de búsqueda, patrón script-JSON, no hay
loops byFamily (colisión vida/homicide no aplica), sitemap/robots sin impacto,
CommuneRankingTable sigue usado en región/rankings (no queda huérfano).

## Tarea 1 — Copiar los 8 archivos del paquete

```bash
PKG="C:/Users/Carlo/Downloads/Optimizar diseño de comunas (6)/install-landing"
mkdir -p site/src/components/home
cp "$PKG/site/src/config/homeV2Strings.ts"               site/src/config/
cp "$PKG/site/src/components/home/homeData.ts"           site/src/components/home/
cp "$PKG/site/src/components/home/HomeSearchLive.astro"  site/src/components/home/
cp "$PKG/site/src/components/home/HomeMiniMap.astro"     site/src/components/home/
cp "$PKG/site/src/components/home/HomeExtremes.astro"    site/src/components/home/
cp "$PKG/site/src/components/home/HomeNewsPulse.astro"   site/src/components/home/
cp "$PKG/site/src/pages/index.astro"                     site/src/pages/
cp "$PKG/site/src/pages/es/index.astro"                  site/src/pages/es/
```

## Tarea 2 — Fixes del premortem (decisiones LOCKED del estratega)

### BLOCKERS

1. **LPX-1 (B1≡C1) CSS scoped no alcanza nodos createElement.** Astro compila
   scoped con estrategia attribute; los nodos de los 3 enhancers no llevan
   `data-astro-cid-*` → salen sin estilo. Envolver en `:global()` namespaced
   bajo el ancestro server-rendered TODAS las reglas de clases que el JS crea:
   `.extremes-card :global(.ext-row)` (y ext-dot/ext-bar/ext-fill/ext-rate/
   ext-name-wrap/ext-name/ext-region/.s1..s5), `.search-hero-form
   :global(.search-suggestion)` (y search-dot/name/region/rate/suggestion-empty),
   `.pulse-card :global(.pulse-bar)` (y pulse-chip/pulse-dot/pulse-item/
   pulse-headline/pulse-meta). Mismo recurso que RankingTableEnhancer. Las
   reglas de nodos solo-SSR (contenedores) quedan scoped normal.
2. **LPX-2 (A1≡B3≡C2) `[hidden]` derrotado por display scoped.** Añadir
   `.pulse-card[hidden] { display: none; }`. Cinturón también en los demás
   nodos con hidden que pudieran ganar display en el futuro: `.extremes-note[hidden]`,
   `[data-noscript-only][hidden]`, `.search-suggestions[hidden]`,
   `.hv2-stat[hidden]` → `display:none`.
3. **LPX-3 (B2+B8) grid 954px mínimos dentro de page-content 860px.** Tres
   cambios juntos: (a) en el `<style>` de AMBOS index.astro:
   `:global(main.page-content:has(.home-wide)) { max-width: 1240px; }` — libera
   el cap SOLO en el home (intención D-16), sin tocar global.css ni HomeLayout;
   (b) grid → `grid-template-columns: minmax(0, 360px) 120px minmax(0, 1fr)`
   (ningún mínimo fijo = imposible desbordar); (c) mini-mapa `W = 110`
   (silueta real ~74px) y `.minimap-svg { width: 110px }` — la columna de
   226px era ~60% aire.

### HIGH

4. **LPX-4 (A2≡C3) chip "sexuales" sin label.** `FAMILY_LABELS_PAGE` no trae
   `sexuales` (y sexuales SÍ está en el top-5 real de prensa: 49 incidentes).
   En HomeNewsPulse usar los labels que sí lo traen (`FAMILY_LABELS_EN/ES` u
   objeto equivalente de familyDefs.ts — verificar export real y reusar el
   string shippeado 'Sexual Crimes'/'Delitos Sexuales'). NO tocar familyDefs.ts
   ni los 7 FAMILY_KEYS de CEAD.
5. **LPX-5 (A3≡C4) conteos de banda contradictorios (346 vs 256).** La franja
   del mini-mapa sigue contando las 346 (describe los puntos pintados); la nota
   de extremos explicita su universo: `extremes_band_note` pasa a
   `'{label} · {n} comunas (excl. baja población)'` ES /
   `'{label} · {n} communes (excl. low population)'` EN.
6. **LPX-6 (B4) foco invisible por overflow:hidden.** `.mm-band:focus-visible`
   y `.extremes-toggle button:focus-visible` → `outline: none; box-shadow:
   inset 0 0 0 2px var(--primary)` (compatible con el inset de aria-pressed).
7. **LPX-7 (B5) combobox ARIA inválido.** Simplificar a semántica honesta:
   quitar `role=combobox/listbox/option`, `aria-autocomplete`, `aria-controls`,
   `aria-expanded`; el ul queda lista simple de enlaces (focusables por
   naturaleza, flechas ↓↑ + Escape se mantienen); añadir región `aria-live=
   "polite"` sr-only que anuncia "N comunas" / "Ninguna comuna coincide" al
   renderizar sugerencias (reusar clase .sr-only si existe global, si no
   declararla en el componente).

### MEDIUM

8. **LPX-8 (A5) conteo ≠ histograma en el pulso.** Tras el fetch, recortar
   `all` a la ventana renderizada (`i.date >= anchor-29d`) ANTES de calcular
   pool/famCounts/countEl — conteo, chips, titulares e histograma hablan del
   mismo período (bug conocido: 31 fechas con window_days=30).
9. **LPX-9 (A6) tasa 0 → nivel 1.** Guarda del directorio replicada en
   homeData: `level: c.rate > 0 ? levelForRate(c.rate, sortedRates) : 3`
   (Río Verde y Antártica quedan banda 3 neutra, como el resto del sitio).
10. **LPX-10 (A7) baja población sin marcar en sugerencias.** Nueva key
    `suggest_lowpop` en homeV2Strings con los MISMOS strings de
    `dir_lowpop_tag` de i18n.ts (copiar valor exacto, no inventar); render como
    tag muted en la sugerencia cuando `c.p === 1`.
11. **LPX-11 (A4≡C7) 343 puntos vs "346".** `glance_note` se queda en 346 (es
    afirmación sobre el dataset, coherente con el hero); el `aria-label` del
    SVG gana el calificador continental: "… — comunas continentales" /
    "… — continental communes" (nueva key o sufijo en glance_title aria). No
    afirmar "346 puntos" en ninguna UI.
12. **LPX-12 (B6+B11) quintil 1 invisible + colores hardcodeados.**
    `.ext-dot`/`.search-dot` ganan anillo `box-shadow: inset 0 0 0 1px
    color-mix(in srgb, var(--ink) 35%, transparent)`; `.ext-bar` track con
    `border: 1px solid var(--line)`; sustituir los `rgba(28,42,43,…)` a mano
    por `color-mix(in srgb, var(--ink) N%, transparent)`.
13. **LPX-13 (B7) contraste de conteos en la franja.** Envolver el conteo en
    `<span class="mm-count">` con píldora `background: rgba(255,255,255,.78);
    color: var(--ink); border-radius: 999px; padding: 0 5px` — legible sobre
    cualquier banda; el atenuado de bandas inactivas pasa de `opacity: .3` del
    botón entero a overlay `background-image: linear-gradient(rgba(255,255,255,.72),
    rgba(255,255,255,.72))` manteniendo la píldora del número legible.
14. **LPX-14 (B9) paleta FAM_DOT desincronizada.** Alinear `homicidios` con la
    página de noticias (`oklch(0.45 0.16 12)`) y darle el anillo distintivo en
    `.pulse-dot` (box-shadow blanco+color, mismo criterio que noticias: vida y
    homicidios comparten tono). Si existe un módulo compartido client-safe con
    la paleta (config/rankingStrings.ts o similar), importarlo; si no, duplicar
    con comentario apuntando a la fuente canónica.
15. **LPX-15 (C6) pérdida de texto indexable.** Las píldoras recuperan el
    anchor text descriptivo VERBATIM de las guide cards actuales en ambos
    locales (p.ej. 'Chile Crime Map — interactive choropleth', 'Is Chile
    Safe? — national overview'; leer los index.astro actuales ANTES de
    reemplazarlos — `git show HEAD:site/src/pages/index.astro`). Pérdida
    aceptada y documentada: h2+párrafo del CTA del mapa, subheads de tablas,
    columnas rank/tendencia, selector de año (INSTALL.md ya lo asume).

### LOW

16. **LPX-16 (A9) parsing frágil del label de banda.** `data-band-label={t.bands[i]}`
    en los botones de la franja; ambos scripts leen `dataset.bandLabel` en vez
    de trocear `title` con separadores distintos.
17. **LPX-17 (A10≡C8) blob sin escapar.** `JSON.stringify(homeBlob(rows)).replace(/</g,'\\u003c')`
    en ambas páginas (convención de CommuneDirectory/RankingBoard).
18. **LPX-18 (A11) strings muertos.** Las páginas consumen `stats_communes`,
    `stats_mean`, `stats_press`, `explore_title` desde homeV2Strings (con
    `fmt` para el año donde aplique) en vez de duplicar el texto a mano. El
    "30" de stats_press queda literal (window_days estable en 30).
19. **LPX-19 (B10) reduced-motion.** En cada `<style>` nuevo con transiciones:
    `@media (prefers-reduced-motion: reduce) { .mm-dot, .mm-band, .hv2-pills a
    { transition: none } }` (ajustar selectores por archivo).
20. **LPX-20 (B12) breakpoint muerto.** Colapsar:
    `@media (max-width:1023px) { .hv2-top { grid-template-columns: 1fr }
    .hv2-map { display: none } }` y borrar el bloque de 767px.

**Rechazado:** LPX-21 (C9, peso del SVG/blob): los `<title>` por punto son el
tooltip prometido por el spec y el blob es el patrón datos-en-HTML establecido;
el recorte de W en LPX-3 ya reduce el SVG. Trade-off documentado.

**Nota de verificación local (A8):** en `npm run dev` 334/346 fichas dan 404
por el gate de rollout (12 comunas) — NO es regresión del paquete; la
verificación manual usa `npm run build && npx astro preview` (build lleva
ROLLOUT_ALL=true).

## Tarea 3 — Gates

Desde `site/`, UN comando encadenado (OneDrive):
`npm run check && npm test && npm run build && npm run validate`.
Baseline: 0 errores astro check, suite verde, 16 validadores verdes (spine [K]
1 h1, seo [R] ItemList, forbidden-language, coverage).
Si falla algo → corregir en los archivos instalados; nunca parchear
validadores ni suprimir con @ts-ignore.

Commit atómico al pasar:
`feat(home): install Landing v2 (propuesta 6b) from install-landing package`
+ cuerpo con lista de fixes LPX-* aplicados. Toca exactamente 8 rutas (6
nuevas + 2 reemplazos). Cero ediciones fuera del paquete.

## Verificación (opus, post-ejecución)

- `git diff --stat HEAD~1` toca EXACTAMENTE los 8 archivos del paquete.
- HomeLayout, BaseLayout, global.css, i18n.ts, data.ts, jsonld.ts,
  colorScale.ts, familyDefs.ts, CommuneRankingTable, RankingTableEnhancer intactos.
- Greps: `:global(` presente en los 3 componentes con enhancer;
  `.pulse-card[hidden]`; `main.page-content:has(.home-wide)` en ambas páginas;
  `minmax(0,` sin mínimos fijos; sin `role="combobox"` ni `role="listbox"`;
  `aria-live` en búsqueda; `\\u003c` en ambas páginas; `data-band-label`;
  `suggest_lowpop`; `rate > 0 ?` en homeData; recorte de ventana en pulso;
  labels de sexuales resueltos; `prefers-reduced-motion`.
- dist/: `grep -c '<h1'` = 1 en index.html y es/index.html; JSON-LD
  WebSite+Organization+2 ItemList (EN) / 2 ItemList (ES); ninguna clase
  runtime (.ext-row, .pulse-bar, .search-suggestion) compilada con
  `[data-astro-cid-*]` en los CSS de dist.
- Tone Guard: sin "seguro/peligroso" calificativo (ES/EN) en strings nuevas.
- Re-correr los 4 gates de forma independiente.

## Rollback

`git revert <commit>` (los reemplazos vuelven; los 6 nuevos desaparecen del
tree). Pre-commit: `git checkout -- site/src/pages/index.astro
site/src/pages/es/index.astro && rm -rf site/src/components/home
site/src/config/homeV2Strings.ts`.
