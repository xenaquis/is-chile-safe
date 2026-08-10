---
id: 260810-pz5
status: complete
verdict: PASS_WITH_NOTES (verificador opus) → 3 de 4 notas resueltas por el estratega en 0056772; V-01 aceptada con corrección de alcance
commits: bb10c6d (mapa+comparador), 1381839 (rankings), fcde332 (noticias), 0056772 (cierre verificador)
date: 2026-08-10
---

# Summary: barrido de deuda técnica de los 4 installs v2 (2026-08-10)

Pipeline: pase visual del estratega (BrowserOS sobre dist/) → PLAN con 21 ítems locked (Fable) → 3 ejecutores Sonnet secuenciales con gates+commit por área (wf_e873bc70-e66) → verificación adversarial Opus → cierre Fable.

## Deuda eliminada SIN código (pase visual del estratega)

- **VERIF-UI (pbj)**: los 10 fixes CSS + 4 de franja verificados en navegador, EN y ES — rail sin overflow (0px en 481–1280), swatches 14×14, band-btns 44px, aislamiento + "Aislado ×", fila "Sin homicidios reportados: 163" (suma 346), franja con 31 barras (día más antiguo presente), hint sr-only invisible, scope `vida` correcto en capa Homicidios.
- **Medición real de `--map-topbar-h`**: topbar real 343/293/243/217px por tramo (EN≡ES) vs var 200/117 — solape confirmado en todos los tramos ≥481px; produjo los valores de MAP-01.

## Deuda eliminada con código (21 ítems, 4 commits)

**bb10c6d — mapa+comparador**: MAP-01 tiers medidos+8px de `--map-topbar-h` (351/301/251/225 en min-width 481/560/720/1024; ≤480 intacto — re-verificado en navegador post-fix: var ≥ real en los 4 tramos); MAP-02 claves huérfanas `map_entry_family`/`map_entry_mode` fuera de i18n.ts; CMP-01 prop muerta `cmp_avg_column` fuera de ambas páginas E i18n.ts (cero consumidores); CMP-02 `cmp_homicide_no_data` ya no afirma "Sin casos reportados" ante dato AUSENTE → "Sin datos de homicidios — CEAD {year}" / "No homicide data — CEAD {year}" (corrige island + las 4 páginas [pair], semántica `!== undefined` verificada antes del reword); CMP-03 span de año no se renderiza vacío con national.json caído.

**1381839 — rankings (13/13 del REVIEW l3e)**: F-01 hub re-enlaza homicidios (≥2 entrantes, sin re-introducir la colisión vida/homicide); F-02 H2 visibles en las 16 páginas; F-03 ctrl/cmd-click respetado + aria-current; F-04 foco no cae al body; F-05 scope="col"; F-06 dirty incluye dir; F-07 año del H2 sincronizado; F-08 guardia `[hidden]{display:none}` (pitfall Astro scoped-style); F-09 B-07/B-08 retro-portados al directorio; F-10 sin `<mark>` vacío; F-15 aria-label diferenciado en los 6 enlaces; F-16 enlace /es/mapa/ + "Fuente: CEAD" en ambos hubs; B-09 hint de estado vacío con hideLowpop. Claves nuevas en rankingStrings.ts (i18n.ts intacto por diseño).

**fcde332 — noticias**: NWS-01 (WR-02) `homicidios` re-hue + anillo blanco (segundo canal visual vs `vida`) y title en los fam-dots, ambas páginas. **NWS-02/03 ABORTADOS con causa**: la extracción del script gemelo a módulo compartido la BLOQUEA el validador protegido facets.mjs assertion 22 (WR2-01), que exige el patrón `history.replaceState` inline en CADA .astro como guardia deliberada — extracción revertida byte-a-byte, gates verdes. No es deuda: es un contrato del repo.

**0056772 — cierre de notas del verificador**: V-02 `:global(mark)` acotado a `.dir-table`/`.rk-table` (evita sangrado a cualquier `<mark>` futuro); V-03 crime.mjs gana asserción de piso ≥2 enlaces entrantes a /crime/homicide/ y /es/delito/homicidios/ (corre con conteos reales: 2/2); V-04 tiers re-verificados en navegador post-build. V-01 aceptada con corrección: el `title` sobre span aria-hidden es solo tooltip de ratón (el canal AT sigue siendo el `.news-sr` preexistente, que ya nombra la familia) — el fix real de WR-02 es el canal visual, que sí está.

## Gates

4 corridas independientes (una por ejecutor + verificador) + 1 final del estratega: astro check 0 errores · vitest 86/86 · build 834 páginas · validate 16/16 (crime.mjs ahora con la asserción de piso). mapFilterDefs.test.ts y newsFilterLogic.test.ts sin diff.

## Fuera de alcance (decisión documentada, no es deuda accionable)

- Barras-día <44px de ancho (tradeoff de diseño mitigado y comentado en CSS).
- F-11/F-12/F-13 (INFO l3e): controles inertes sin JS, columnas móviles, 220KB data-rates — fase propia si se quiere.
- Duplicación script/CSS de noticias: protegida a propósito por facets.mjs WR2-01 (contrato, no descuido).
- Topbar de ~343px en 481–559px: coste del wrap de 10 chips; iteración de diseño aparte si molesta.
