# Quick Task 260620-hrh: Year selector + longitudinal crime-evolution charts per comuna — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning

<domain>
## Task Boundary

Cada página de comuna (EN `/commune/{slug}/` y ES `/es/comuna/{slug}/`) debe:
1. Permitir **cambiar el año de análisis** mediante un selector.
2. Tener una **sección de gráficos de evolución longitudinal** por grupo de delito (las 7 familias) **incluido homicidio por año**.

**Pure frontend.** Toda la data ya existe en cada `data/cead/comunas/{cut}.json`:
- `series[]`: `{ year, rate_per_100k, by_family{vida,robos_violentos,vif,drogas,armas,propiedad,incivilidades}, partial }` para 2005–2026.
- `featured_rates.homicidios` y `featured_rates.homicidios_count`: dicts year→valor.
No se requiere trabajo de scraper ni de datos.
</domain>

<decisions>
## Implementation Decisions

### Alcance del selector de año (DECIDIDO: toda la página)
- Al cambiar el año se recalculan: **StatCard de tasa**, **FamilyBreakdownBars** (valores + ancho de barras + año del encabezado), **sección de homicidio** (tasa/conteo/encabezado/fuente), y el **resaltado de año del Sparkline**.
- El **año por defecto = `data.latestCompleteYear`** se renderiza server-side en HTML estático → SEO intacto. El selector es progressive enhancement.
- Mecanismo: **JS vanilla** (NO isla React) — respeta D-09 (zero `client:*` en páginas de comuna). Datos por año embebidos como `<script type="application/json">` o atributos `data-*`.
  - ⚠️ Memory [[astro-script-no-expr-interpolation]]: Astro renderiza `{expr}` literal dentro de `<script>`. Pasar la data server→cliente vía `set:html` (JSON) o `data-*`, nunca interpolando en el `<script>`.

### Secciones que NO cambian con el año (se mantienen en último año / año fijo, documentado)
- **ComparisonCallouts** (vs nacional / vs regional): requieren promedios nacional/regional **por año** que no están disponibles barato (`loadNationalAverage`/`loadRegionalAverage` devuelven solo el último año). Se mantienen en el último año.
- **LevelChip / nivel de color**: el nivel se calcula contra la distribución de todas las comunas en el último año; recomputar por año en cliente es caro. Se mantiene fijo; las barras de familia solo cambian valores/ancho, no el color (`var(--s{level})`).
- **Composite index** (fijo 2024), **ENUSC VHDV** (fijo 2024), **rankings/comparables**: sin cambios.

### Gráficos longitudinales (DECIDIDO: SVG estático server-side)
- Nuevo componente `.astro` server-rendered, **cero JS**, patrón consistente con `Sparkline.astro` (viewBox, escala a max, años parciales a opacidad 0.5).
- Una mini-gráfica por familia (7) **+ una de homicidio por año** (de `featured_rates.homicidios`).
- Bilingüe vía las etiquetas de familia ya existentes (`FAMILY_LABELS` en `FamilyBreakdownBars.astro` → considerar extraer a `site/src/lib/familyDefs.ts` para no duplicar).
- `aria-label` adecuado; indexable por Google.

### Claude's Discretion
- UX exacta del selector (`<select>` vs botones de año), posición en la página, y si los gráficos son líneas o barras.
- Si extraer `FAMILY_LABELS` a `familyDefs.ts` o duplicar (preferir extraer).
- Naming de componentes nuevos.
</decisions>

<specifics>
## Specific Ideas

- Extender el patrón SVG de `site/src/components/Sparkline.astro`.
- Etiquetas/orden de familia en `site/src/components/FamilyBreakdownBars.astro` (`FAMILY_ORDER`, `FAMILY_LABELS`).
- Strings i18n en `site/src/config/i18n.ts` (`rate_label`, `family_breakdown_heading`, `sparkline_heading` ya usan `{year}` placeholder) — agregar string del encabezado de gráficos y label del selector para EN y ES.
- Ambas páginas (`site/src/pages/commune/[slug].astro` y `site/src/pages/es/comuna/[slug].astro`) son espejo — aplicar cambios paralelos.
</specifics>

<canonical_refs>
## Canonical References

- CLAUDE.md: SEO constraint — "Todas las páginas deben ser HTML estático pre-renderizado e indexable — nada de contenido crítico render-only en cliente."
- D-09: páginas de comuna con **zero `client:*` directives**. El selector de año debe ser JS vanilla con degradación: el año por defecto vive en el HTML estático.
- Memory [[crime-rates-already-per-100k]]: `by_family`/`featured_rates` ya son tasas per-100k — nunca reescalar.
- Memory [[onedrive-build-artifacts-desync]]: encadenar build+validate en un solo comando o `dist/` desaparece.
- Memory [[vida-homicide-slug-collision]]: en loops `byFamily`, `vida` ≠ homicidio; el ranking de homicidio se trata aparte.
</canonical_refs>
