# Requirements: Chile Safety Map (ischilesafe.com) — Milestone v1.1 Polish & QA

**Defined:** 2026-06-13
**Core Value:** Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa.

**Milestone goal:** Recorrer todo el sitio renderizado (ES/EN) con navegador, cazar bugs, reducir carga cognitiva y dejarlo agradable de leer — antes del go-live. Insumo: `.planning/REVIEW-E2E-BRIEF.md`.

> Naturaleza del milestone: **QA/polish**, no features nuevas. Los requisitos de revisión (REVIEW-*) producen hallazgos; los requisitos de corrección (BUGFIX/UX/READ/A11Y) se cumplen aplicando y verificando esos hallazgos.

## v1.1 Requirements

### E2E Review (REVIEW)

- [x] **REVIEW-01**: Todas las páginas del inventario (10 editoriales EN + 10 ES + /map/ + /es/mapa/ + 8 legales) recorridas en navegador real, ES y EN, con screenshot y consola revisada.
- [x] **REVIEW-02**: Muestreo representativo de páginas programáticas verificado contra plantilla (≥3 comunas alta/media/baja población, ≥2 regiones, ≥2 tipos de delito, en ES y EN); muestra declarada explícitamente.
- [x] **REVIEW-03**: Comportamiento dinámico del mapa verificado en navegador: cambio de año, cambio de tipo de delito, panel de comuna (tasa/tendencia/ranking/sparkline/familias), búsqueda, geolocalización, capa de incidentes en estado vacío sin error.
- [x] **REVIEW-04**: Render responsive móvil (~375px) verificado en money pages y mapa: sin desbordes, mapa usable, targets táctiles ≥44px. Cierra el UAT visual/móvil de Phase 3 diferido de v1.0.
- [x] **REVIEW-05**: Hallazgos consolidados en `.planning/REVIEW-E2E-FINDINGS.md` con severidad (Critical / Warning / Polish), página afectada, referencia de screenshot y recomendación concreta.

### Correctitud / Bugs (BUGFIX)

- [x] **BUGFIX-01**: Cero errores de consola del navegador en money pages y en el mapa; warnings revisados y triados.
- [x] **BUGFIX-02**: Enlaces internos (header, footer, cross-links, language switcher) resuelven sin rotos; hreflang recíproco correcto (respetando auto-referencias intencionales).
- [x] **BUGFIX-03**: Datos correctos verificados — tasas usan media nacional (`loadNationalAverage`, no la SUMA), ranking por tasa/100k, cifras coinciden con `data/cead/`.
- [x] **BUGFIX-04**: Sin CLS por anuncios — los AdSlot reservan altura; con AdSense OFF se muestra placeholder y ningún `adsbygoogle` queda visible.
- [x] **BUGFIX-05**: Todos los hallazgos de severidad Critical quedan corregidos y re-verificados en navegador; los Warning se corrigen o se difieren con justificación explícita.

### Carga cognitiva (UX)

- [x] **UX-01**: Jerarquía clara en money pages — un solo H1, H2/H3 escaneables; el lector entiende la página en ~5 segundos.
- [x] **UX-02**: Densidad de información reducida donde el review la marque — DataCallout/StatCard comunican una idea clara con su fuente (CEAD + año); redundancia callout↔prosa eliminada.

### Lectura / Editorial (READ)

- [x] **READ-01**: Columna de prosa legible en editoriales (~720px, ritmo de párrafos, sin muros de texto).
- [x] **READ-02**: Paridad ES/EN — contenido, estructura y tono equivalentes entre cada par de páginas; sin secciones faltantes en un idioma.
- [x] **READ-03**: Tono editorial sobrio respetado en todo el sitio (sin "peligroso/seguro" absoluto; usa "incidencia reportada", "comparación relativa"); jerga explicada.

### Accesibilidad / SEO (A11Y)

- [x] **A11Y-01**: En páginas muestreadas — contraste de color (paleta teal `--primary #0f766e`), focus states visibles, alt text presente, y aria en los controles del mapa.
- [x] **A11Y-02**: En plantillas muestreadas — `<title>`, meta description, canonical, hreflang y JSON-LD (FAQPage en question-pages) presentes y válidos.

## v1.2 Requirements

Milestone **v1.2 Map Fidelity & Crime-Type SEO** — surfaced by the Phase-9 live review (2026-06-15). Defined incrementally as each phase is planned.

### Map Geometry (GEO) — Phase 10

- [x] **GEO-01**: El asset de geometría comunal (`data/cead/geo/communes.topo.json` + su espejo en `site/public/`) se regenera desde una fuente oficial de límites comunales chilenos (INE/BCN/IGM), cubre todas las comunas presentes en los datos CEAD, y conserva la misma clave de código comunal con la que el mapa hace join (ninguna comuna se pierde ni se mal-asocia). Los polígonos renderizados se reconocen como formas comunales reales (costa, bordes) frente a la simplificación blocky actual.
- [x] **GEO-02**: El asset publicado respeta un presupuesto de tamaño/rendimiento (objetivo documentado en research; tradeoff fidelidad↔KB registrado); el mapa mantiene pan/zoom/hover fluido sin regresión perceptible y sin nuevos errores de consola, con un procedimiento de regeneración reproducible (script o pasos documentados).

### Findability — Comunas (COMU) — Phase 11

- [ ] **COMU-01**: Se publica página propia para las 346 comunas con datos CEAD (EN `/commune/[slug]`, ES `/es/comuna/[slug]`); clic en cualquier polígono del mapa o fila de ranking llega a una página real (0 dead-links/404); el sitemap incluye todas las URLs de comuna en ambos locales.
- [ ] **COMU-02**: Existe un directorio de comunas buscable (búsqueda sin acentos + vistas A–Z y por región/16), enlazado desde nav y home; cualquier comuna alcanzable en ≤2 interacciones; incluye comunas de baja población (tienen página aunque no entren en rankings).
- [ ] **COMU-03**: Las tablas de ranking de región y de delito enlazan TODAS las comunas (sin "Showing N of M — more coming soon"); thin-content mitigado (cada ficha con datos/prosa únicos + title/meta/canonical/hreflang propios); un validador asegura conteo de páginas ≈346×2 y cero enlaces internos a slugs de comuna no generados.

### Arquitectura de Información (IA) — Phase 12

- [ ] **IA-01**: Home reconstruido con el framing Hybrid C+B (editorial/SEO arriba + hero "busca tu comuna" + mapa como CTA de primera clase), bilingüe con paridad, un solo H1, estático/indexable.
- [ ] **IA-02**: Cada ficha de comuna es un hub que enlaza a mapa (centrado), ranking regional, comunas similares, rankings por delito, y sus noticias; con breadcrumb Inicio › Comunas › Región › Comuna en ambos locales.
- [ ] **IA-03**: Spine de navegación coherente mapa↔comuna↔ranking↔región↔noticias en ambos locales; nav principal incluye "Comunas" (directorio); enlaces internos recíprocos y sin 404.

### SEO de Rankings (RSEO) — Phase 13

- [ ] **RSEO-01**: OpenGraph + Twitter Card inyectados site-wide vía layout base (title/description/image/url/type), con valores correctos por locale; verificado en muestras de páginas de ranking, editoriales, comuna y región.
- [ ] **RSEO-02**: `ItemList` JSON-LD envuelve las tablas de ranking y `BreadcrumbList` JSON-LD se emite donde hay breadcrumb visual; ambos validan contra schema.org y un check de build asegura su presencia en plantillas muestreadas.

### Homicidio (HOM) — Phase 14

- [ ] **HOM-01**: `homicidios` (subgrupo destacado 101) seleccionable como filtro/capa propia en el mapa con su propio coroplético, distinto de "vida"; el pipeline emite la tasa de homicidios por comuna al map-payload.
- [ ] **HOM-02**: El panel de comuna muestra una cifra/desglose de homicidios separada (no solo la familia "vida" agregada), con fuente CEAD + año citados; sin regresión al render de familias existente.

### SEO por Tipo de Delito (CSEO) — Phase 15

- [ ] **CSEO-01**: Páginas programáticas bilingües "las N comunas con más {delito}" (homicidio primero) con internal linking a comuna/región, hreflang recíproco y entradas de sitemap.
- [ ] **CSEO-02**: Cada página estática/indexable con un solo H1 con keyword, title/meta/canonical únicos, e `ItemList` JSON-LD; tono sobrio preservado (incidencia reportada, fuentes citadas).

### Noticias (NEWS) — Phase 16

- [ ] **NEWS-01**: Geolocalización rediseñada — el LLM emite el NOMBRE de la comuna (+ hint de región), resuelto por lookup determinista nombre→CUT (espejo del re-key de geometría) en vez de adivinar el CUT; precisión medida contra golden set y supera el enfoque actual (smoke test: ambos modelos erran ~60–70% del CUT con códigos pelados).
- [ ] **NEWS-02**: Golden set etiquetado (30–50 incidentes reales con comuna+familia ground-truth) + script de scoring; proveedor LLM configurable por env; A/B DeepSeek vs MiniMax en precisión de comuna, familia, latencia, costo y fiabilidad; ganador documentado y cableado como default.
- [ ] **NEWS-03**: El pipeline corre de verdad (gated por el paso humano de go-live con las API keys) produciendo `data/incidents/current.json`; la capa de pins y la sección "incidentes recientes" de la ficha renderizan incidentes reales correctamente geolocalizados, sin errores de consola.
- [ ] **NEWS-04**: Cada incidente enlaza a su fuente ↗ Y de vuelta a la ficha de su comuna; existe página de noticias dedicada (bilingüe); indicador de frescura ("actualizado …"); todos los incidentes citan y enlazan la fuente de prensa.

## Future Requirements

Deuda técnica registrada — oportunista en v1.1, difiérase a v1.2 si no cabe:

- **TECHDEBT-01**: Aserción CI del orden de `FAMILY_KEYS` (duplicado pipeline ↔ `FiltersRow.tsx`).
- **TECHDEBT-02**: Tipado de `by_family` (`number[]` vs `float|None`) unificado.
- **TECHDEBT-03**: `AVAILABLE_YEARS` derivado dinámicamente de los datos (hoy hardcodeado 2005–2025).
- **TECHDEBT-04**: Flip de `nyquist_compliant` en VALIDATION.md (fases 4–6).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Go-live `ischilesafe.com` (CF Pages + DNS + secrets) | Trabajo humano, documentado en `DEPLOYMENT.md`; no es revisión de código. v1.1 es polish local pre-deploy. |
| Pipeline de noticias en vivo + auditoría 50 incidentes | Requiere `DEEPSEEK_API_KEY` y go-live; gated por humano. Capa de incidentes se revisa en estado vacío. |
| Flip de `ADSENSE_ENABLED` + AdSense Consent Mode | Post-indexación, trabajo de go-live (todo `adsense-consent-mode-phase6`). |
| Features nuevas (capa social, comentarios, comparador) | Fuera del alcance de un milestone de QA; siguen diferidas post-MVP. |
| Las 740 páginas programáticas una por una | Se cubre por muestreo + verificación de plantilla (REVIEW-02); revisar todas no aporta señal. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REVIEW-01 | Phase 7 | Complete |
| REVIEW-02 | Phase 7 | Complete |
| REVIEW-03 | Phase 7 | Complete |
| REVIEW-04 | Phase 7 | Complete |
| REVIEW-05 | Phase 7 | Complete |
| BUGFIX-01 | Phase 8 | Complete |
| BUGFIX-02 | Phase 8 | Complete |
| BUGFIX-03 | Phase 8 | Complete |
| BUGFIX-04 | Phase 8 | Complete |
| BUGFIX-05 | Phase 8 | Complete |
| UX-01 | Phase 9 | Complete |
| UX-02 | Phase 9 | Complete |
| READ-01 | Phase 9 | Complete |
| READ-02 | Phase 9 | Complete |
| READ-03 | Phase 9 | Complete |
| A11Y-01 | Phase 9 | Complete |
| A11Y-02 | Phase 9 | Complete |
| GEO-01 | Phase 10 | Complete |
| GEO-02 | Phase 10 | Complete |
| COMU-01 | Phase 11 | Pending |
| COMU-02 | Phase 11 | Pending |
| COMU-03 | Phase 11 | Pending |
| IA-01 | Phase 12 | Pending |
| IA-02 | Phase 12 | Pending |
| IA-03 | Phase 12 | Pending |
| RSEO-01 | Phase 13 | Pending |
| RSEO-02 | Phase 13 | Pending |
| HOM-01 | Phase 14 | Pending |
| HOM-02 | Phase 14 | Pending |
| CSEO-01 | Phase 15 | Pending |
| CSEO-02 | Phase 15 | Pending |
| NEWS-01 | Phase 16 | Pending |
| NEWS-02 | Phase 16 | Pending |
| NEWS-03 | Phase 16 | Pending |
| NEWS-04 | Phase 16 | Pending |

**Coverage:**

- v1.1 requirements: 17 total (mapped: 17, unmapped: 0 ✓)
- v1.2 requirements: 19 total across Phases 10–16 — GEO (2, Complete), COMU (3), IA (3), RSEO (2), HOM (2), CSEO (2), NEWS (4). All mapped to a phase; unmapped: 0 ✓

---
*Requirements defined: 2026-06-13*
*Last updated: 2026-06-13 — traceability filled after roadmap creation*
