---
id: 260810-pbj
title: Instalar rediseño Mapa v2 (propuesta 5b) desde paquete install-mapa
type: quick
executed_via: dynamic-workflow (sonnet ejecutor, opus verificador, fable estratega/validador)
premortem: wf_f12426e9-35d (3 revisores opus — 25 hallazgos: 4 HIGH, 11 MEDIUM, 10 LOW, 0 BLOCKER; consolidados abajo)
must_haves:
  truths:
    - "D-12: el coropletas se monta UNA vez y jamás se re-monta; el aislamiento de banda muta el style map ANTES de la única pasada applyStyleMap."
    - "CHIP_DEFS y AVAILABLE_YEARS quedan byte-a-byte verbatim → mapFilterDefs.test.ts pasa sin cambios; FAMILY_KEYS CEAD siguen siendo 7 (sexuales solo prensa)."
    - "Ningún listener de teclado a nivel document (F-49); centinelas data-role=filter-entry (rail + FAB), locate-btn y StateSummary aria-live conservados."
    - "Tasas per-100k nunca se re-escalan; nunca calificar territorios de seguros/peligrosos; prensa con escape HTML + noopener (T-03-03-02/03)."
    - "map.css, config/i18n.ts, map.astro, es/mapa.astro, ResultPanel.tsx, ChoroplethLayer.ts, colors.ts NO se tocan."
    - "El rail de capas NO desborda horizontalmente (criterio 2 del rubric de fase 29/30): chips con flex-wrap, sin overflow-x."
    - "Targets táctiles propios del mapa ≥44px (F-51) salvo la excepción documentada de las barras-día del NewsStrip (ancho <44 imposible con 30+ barras en 440px; hit-area de alto completo + aria-label + oculto ≤960px)."
  artifacts:
    - "site/src/config/mapV2Strings.ts"
    - "site/src/components/map/LayerRail.tsx"
    - "site/src/components/map/LegendHistogram.tsx"
    - "site/src/components/map/NewsStrip.tsx"
    - "site/src/components/map/bandStats.ts"
    - "site/src/components/map/map-v2.css"
    - "site/src/lib/mapFilterDefsV2.test.ts"
    - "site/src/components/map/MapIsland.tsx"
    - "site/src/components/map/MapTopbar.tsx"
    - "site/src/components/map/FilterSheet.tsx"
    - "site/src/components/map/FilterFields.tsx"
    - "site/src/components/map/IncidentPinLayer.ts"
    - "site/src/components/map/LowZoomDotLayer.ts"
    - "site/src/lib/mapFilterDefs.ts"
  key_links:
    - "site/scripts/validate/all.mjs (validadores; map.mjs gana asserción de igualdad de ids topo↔payload — fix MPX-A6)"
    - "EntryPointsRail.tsx y Legend.tsx se eliminan (git rm) — grep confirmó cero importadores restantes"
---

# Plan: instalar Mapa v2 (5b) + fixes de premortem

## Contexto

Paquete: `C:/Users/Carlo/Downloads/Optimizar diseño de comunas (5)/install-mapa` (INSTALL.md es la autoridad de alcance).
Repo: `C:/Users/Carlo/OneDrive - pjud.cl/Documentos/GitHub/Is Chile Safe` (OneDrive: encadenar los gates en UN comando; citar TODAS las rutas — llevan espacios y paréntesis).

El premortem (3 opus, wf_f12426e9-35d) verificó limpio lo estructural: máquina de estados coherente para las 10 capas de LAYER_DEFS; D-12/D-08/D-13/D-15, Pitfalls 5/6/7, F-49, H-02, T-03-03-02/03 respetados; CHIP_DEFS/AVAILABLE_YEARS verbatim (tests del repo pasan); schemas de map-payload*.json y current.json compatibles; props de MapIsland idénticos (map.astro/es/mapa.astro no requieren cambios); git rm seguro (cero importadores); validadores de scripts/validate/ no dependen de los archivos tocados; sin lenguaje calificativo en strings nuevas.

## Tarea 1 — Copiar los 14 archivos del paquete + eliminar 2

```bash
PKG="C:/Users/Carlo/Downloads/Optimizar diseño de comunas (5)/install-mapa"
# nuevos
cp "$PKG/site/src/config/mapV2Strings.ts"                 "site/src/config/"
cp "$PKG/site/src/components/map/LayerRail.tsx"           "site/src/components/map/"
cp "$PKG/site/src/components/map/LegendHistogram.tsx"     "site/src/components/map/"
cp "$PKG/site/src/components/map/NewsStrip.tsx"           "site/src/components/map/"
cp "$PKG/site/src/components/map/bandStats.ts"            "site/src/components/map/"
cp "$PKG/site/src/components/map/map-v2.css"              "site/src/components/map/"
cp "$PKG/site/src/lib/mapFilterDefsV2.test.ts"            "site/src/lib/"
# reemplazos
cp "$PKG/site/src/components/map/MapIsland.tsx"           "site/src/components/map/"
cp "$PKG/site/src/components/map/MapTopbar.tsx"           "site/src/components/map/"
cp "$PKG/site/src/components/map/FilterSheet.tsx"         "site/src/components/map/"
cp "$PKG/site/src/components/map/FilterFields.tsx"        "site/src/components/map/"
cp "$PKG/site/src/components/map/IncidentPinLayer.ts"     "site/src/components/map/"
cp "$PKG/site/src/components/map/LowZoomDotLayer.ts"      "site/src/components/map/"
cp "$PKG/site/src/lib/mapFilterDefs.ts"                   "site/src/lib/"
# eliminados
git rm "site/src/components/map/EntryPointsRail.tsx" "site/src/components/map/Legend.tsx"
```

## Tarea 2 — Aplicar fixes del premortem (sobre los archivos copiados)

Decisiones LOCKED del estratega. Los IDs referencian el premortem; la evidencia completa vive en el output del workflow wf_f12426e9-35d.

### Lógica / estado (MapIsland.tsx, bandStats.ts)

1. **MPX-A1 (MEDIUM) efecto de año inerte.** Añadir `const [layerMounted, setLayerMounted] = useState(false)`, ponerlo a `true` justo después de `layerRef.current = mountChoroplethLayer(...)` dentro de `loadData`; en el efecto de año cambiar el guard a `if (!mapReady || !layerMounted) return;` y deps a `[year, mapReady, layerMounted]`. NO quitar el guard sin el gate (race con loadData sobre `payloadRef`).
2. **MPX-A2 (MEDIUM) aislamiento borra highlight de selección.** `const selectedRef = useRef<string|null>(null)` actualizado junto a `setSelected`; al final del efecto central de restyle (tras `applyStyleMap`), reaplicar `highlightSelected(...)` si `selectedRef.current` existe en `polyIdxRef`. Usar el ref, no el estado (no añadir `selected` a deps).
3. **MPX-A3 (MEDIUM) puntos de zoom bajo: doble re-mount + levelIdx viejo.** Añadir `band: number | null` a `LayerStats` (bandStats.ts); en el efecto de restyle `setStats({ ...st, band })`; deps del efecto de puntos = `[lowZoom, stats]` leyendo `stats.band` — un solo re-mount por interacción, siempre con el levelIdx correcto.
4. **MPX-A4 (MEDIUM) homicidios: cero ≠ banda 1.** En `computeLayerStats` rama homicidios: clasificar con `levelFromBreaks` para el color, pero contar solo `v > 0` en `counts`; añadir `zeroCount` a `LayerStats` y en LegendHistogram mostrar fila propia "Sin homicidios reportados: N" / "No homicides reported: N" (claves nuevas en mapV2Strings.ts EN/ES). Coherente con el fillOpacity 0.25 del coropletas.
5. **MPX-A5 (LOW) capa Tasa total: cortes ≠ clasificación precalculada.** Derivar breaks de la partición por `c.level`: `[1,2,3,4].map(l => Math.max(...rates de nivel l))` con guarda para banda vacía — rango, color y conteo describen la misma clasificación.
6. **MPX-A7 (LOW) toggle rápido de noticias = N fetches/toasts.** Guardar la petición en `useRef<Promise<...>|null>`; si ya hay una en vuelo o hecha, no relanzar. Un solo toast D-15 por sesión.
7. **MPX-C5 (LOW) composite: conteos no sumaban 346 con ci null.** Contar TODAS las comunas (las `ci === null` se pintan banda 3 y se cuentan ahí) — el conteo describe lo pintado. Hoy hay 0 nulls; es blindaje.

### CSS / layout (map-v2.css; map.css intacto)

8. **MPX-B1/C1 (HIGH) swatch de leyenda se estira.** Añadir `.legend-band-btn .legend-swatch { width:14px; height:14px; border-radius:2px; flex:0 0 auto; }`.
9. **MPX-B2 (HIGH) min-width 208px rompe el tope móvil de 160px.** Envolver: `@media (min-width:481px) { .legend-v2 { min-width:208px } }`.
10. **MPX-B3 + B5 + C8 (HIGH) rail desborda horizontal (FAIL criterio 2) + anillo de foco recortado + --map-topbar-h desactualizada.** Eliminar `overflow-x:auto` del rail: `.layer-rail-chips > div[role=radiogroup] { display:flex; flex-wrap:wrap; gap:6px; width:auto }` y `.layer-rail { flex-wrap:wrap }`. Con el overflow fuera, el outline de foco deja de recortarse (B5 resuelto de gratis). Redefinir la variable en map-v2.css sobre el mismo ancestro que map.css usa (p.ej. `.map-stage`): estimar altura real del rail envuelto a 1280px (1 fila ≈ igual que hoy) y a ~700px (2 filas) — override con slack: `--map-topbar-h: 200px` en 481–1023px si hay 2 filas, manteniendo el valor actual donde quepa en 1; ≤480px el rail está oculto (FAB) y rige el valor móvil existente. El badge de año parcial consume la variable, así que solo debe quedar POR DEBAJO de la topbar, nunca encima.
11. **MPX-B4 (HIGH) targets <44px.** `.legend-band-btn`, `.legend-clear`, `.news-strip-clear` → `min-height:44px`. Barras-día del NewsStrip: hit-area de alto completo (botón 44px de alto con la barra visual dentro); el ancho <44px queda como **excepción documentada** (30+ barras × 44px = 1320px no caben en 440px; el control está oculto ≤960px tras el fix 12 y cada barra gana aria-label con el fix 13). Documentar en SUMMARY.
12. **MPX-B6 (MEDIUM) franja tapada por/tapando la leyenda en 641–860px.** Subir la ocultación de la franja de `max-width:640px` a `max-width:960px` (a 961px+ la franja centrada de 440px ya no intersecta la leyenda de 208px) y darle `z-index:760` como cinturón. Los pines siguen visibles en todos los anchos.
13. **MPX-B9 (LOW) leyenda móvil sin margen en secciones nuevas.** `@media (max-width:480px){ details.legend-mobile[open] .legend-hist, details.legend-mobile[open] .legend-clear { margin-top:6px } }`.
14. **MPX-B10 (LOW) transiciones sin reduced-motion.** `@media (prefers-reduced-motion: reduce) { .legend-hist-bin, .legend-band-btn, .news-strip-bar > span { transition:none } }`.

### UI / a11y / strings (LayerRail.tsx, NewsStrip.tsx, mapV2Strings.ts)

15. **MPX-B7/C6 (MEDIUM) StateSummary redundante y sin variante corta.** En modo composite omitir el prefijo de modo (la capa ya lo dice); restaurar la banda `narrow` con etiqueta corta: `wide` → `(mode==='composite' ? fLabel : mLabel+' · '+fLabel)+' · '+year`; `mid`/`narrow` → `fLabel+' · '+year` con fLabel corto en narrow (usar labels de CHIP_DEFS cortos o recortar). La cadena debe CABER sin truncar (F-46).
16. **MPX-B8 (MEDIUM) barras-día sin nombre accesible.** Cada botón: `aria-label={dayLabel + ': ' + n + ' ' + strings de incidentes}`; `aria-hidden="true"` al `<span>` visual; el hint del contenedor pasa de `title` en div a `aria-describedby` o texto visible.
17. **MPX-C2 (MEDIUM) se pierde el día más antiguo (31 fechas reales con window_days=30).** Construir el rango de días desde min→max de `incidents[].date` (window_days solo como texto del rótulo). Titular y barras deben sumar lo mismo.
18. **MPX-C3 (MEDIUM) capa Homicidios rotula "Homicidios" pero muestra prensa `vida`.** Cuando `crimeIsHomicide`, el `scopeLabel` de la franja usa la etiqueta de la familia de prensa realmente aplicada (`vida`: "Vida y convivencia" / equivalente EN de CHIP_DEFS), no "Homicidios".
19. **MPX-C4 (MEDIUM) ancla temporal derivada del subconjunto filtrado.** Pasar `anchor` como prop desde MapIsland (máx de `incidentsFile.incidents[].date` SIN filtrar); NewsStrip usa `incidents` filtrados solo para conteos.
20. **MPX-C7 (LOW) `year_label` duplica `map_entry_year`.** Eliminar `year_label` de mapV2Strings.ts; LayerRail lee `map_entry_year` de la misma fuente i18n que ya usa FilterSheet (i18n.ts NO se edita).

### Validadores (única edición fuera del paquete)

21. **MPX-A6 (LOW) blindaje del aislamiento de banda.** Añadir en `site/scripts/validate/map.mjs` una asserción de igualdad de conjuntos entre los ids del TopoJSON y los de map-payload.json (hoy 346↔346 1:1 verificado). Es un refuerzo de gate, no un parche para pasar.

**Rechazado:** nada — los 25 hallazgos se aplican (2 pares deduplicados: B1≡C1, B7≡C6; B5 se resuelve vía el fix 10).

## Tarea 3 — Gates

Desde `site/`, UN comando encadenado (OneDrive): `npm run check && npm test && npm run build && npm run validate`.
Baseline conocido: 0 errores astro check, 82+ tests verdes (se suman los de mapFilterDefsV2.test.ts), validadores verdes.
Si falla algo nuevo → corregir en los archivos instalados; nunca parchear validadores para que pasen ni suprimir con @ts-ignore (la asserción del fix 21 se AÑADE, no se relaja nada).

Commit atómico al pasar: `feat(mapa): install Mapa v2 (propuesta 5b) from install-mapa package` + cuerpo con lista de fixes MPX-* aplicados. El commit toca exactamente: los 14 archivos del paquete + 2 eliminaciones + scripts/validate/map.mjs.

## Verificación (opus, post-ejecución)

- `git diff --stat HEAD~1` toca EXACTAMENTE 17 rutas (14 paquete + 2 borradas + map.mjs).
- map.css, config/i18n.ts, map.astro, es/mapa.astro, ResultPanel.tsx, ChoroplethLayer.ts, colors.ts intactos.
- Greps: `layerMounted` en guard+deps del efecto de año; `selectedRef` reaplicado tras `applyStyleMap`; `band` dentro de `LayerStats`/`setStats`; `zeroCount`; sin `overflow-x` en `.layer-rail-chips`; `min-height:44px` en band-btn/clear; ocultación de franja a 960px; `aria-label` en barras-día; rango de días min→max; `anchor` prop; sin `year_label`; asserción de ids en map.mjs.
- F-49: cero `document.addEventListener` de teclado en site/src/components/map/.
- CHIP_DEFS/AVAILABLE_YEARS byte-idénticos al repo previo (git diff del hunk).
- Sin "seguro/peligroso" calificativo (ES/EN) en los archivos nuevos.
- Re-correr los 4 gates de forma independiente.

## Rollback

`git revert <commit>` (los 2 archivos borrados vuelven con el revert). Pre-commit: `git checkout -- site/ && rm` de los 7 archivos nuevos.
