# Requirements: Chile Safety Map (ischilesafe.com) — Milestone v1.2 Map Fidelity, Findability & News

**Defined:** 2026-06-15 (incrementally, as each phase is planned)
**Core Value:** Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa.

**Milestone goal:** El sitio tiene material rico pero "perdido" — geometría blocky, comunas inalcanzables, rankings que no enlazan comunas, capa de noticias construida pero apagada. v1.2 lo arregla: geometría real (10) → publicar las 346 + finder (11) → home/IA + SEO de rankings (12, 13) → homicidio + SEO por delito (14, 15) → activar noticias (16).

> v1.1 (Polish & QA, Phases 7–9) shipped 2026-06-15 — archived in
> `milestones/v1.1-REQUIREMENTS.md`.

## v1.2 Requirements

### Map Geometry (GEO) — Phase 10 ✅

- [x] **GEO-01**: El asset de geometría comunal (`data/cead/geo/communes.topo.json` + espejo en `site/public/`) se regenera desde fuente oficial de límites comunales chilenos (INE/BCN/IGM), cubre todas las comunas CEAD, conserva la clave de código comunal del join (ninguna comuna perdida ni mal-asociada); polígonos reconocibles como formas comunales reales.
- [x] **GEO-02**: El asset respeta un presupuesto de tamaño/rendimiento (tradeoff fidelidad↔KB documentado); pan/zoom/hover fluido sin regresión ni nuevos errores de consola; procedimiento de regeneración reproducible.

### Findability — Comunas (COMU) — Phase 11 ✅

- [x] **COMU-01**: Página propia para las 346 comunas CEAD (EN `/commune/[slug]`, ES `/es/comuna/[slug]`); clic en cualquier polígono o fila de ranking llega a página real (0 dead-links/404); sitemap incluye todas las URLs en ambos locales.
- [x] **COMU-02**: Directorio de comunas buscable (búsqueda sin acentos + vistas A–Z y por región/16), enlazado desde nav y home; cualquier comuna en ≤2 interacciones; incluye comunas de baja población.
- [x] **COMU-03**: Tablas de ranking de región y delito enlazan TODAS las comunas (sin "Showing N of M"); thin-content mitigado; validador asegura ≈346×2 páginas y cero enlaces a slugs no generados.

### Arquitectura de Información (IA) — Phase 12

- [ ] **IA-01**: Home reconstruido con framing Hybrid C+B (editorial/SEO arriba + hero "busca tu comuna" + mapa como CTA de primera clase), bilingüe con paridad, un solo H1, estático/indexable.
- [ ] **IA-02**: Cada ficha de comuna es un hub que enlaza a mapa (centrado), ranking regional, comunas similares, rankings por delito, y sus noticias; breadcrumb Inicio › Comunas › Región › Comuna en ambos locales.
- [ ] **IA-03**: Spine de navegación coherente mapa↔comuna↔ranking↔región↔noticias en ambos locales; nav incluye "Comunas"; enlaces recíprocos y sin 404.

### SEO de Rankings (RSEO) — Phase 13

- [ ] **RSEO-01**: OpenGraph + Twitter Card site-wide vía layout base (title/description/image/url/type), valores correctos por locale; verificado en ranking/editorial/comuna/región.
- [ ] **RSEO-02**: `ItemList` JSON-LD en tablas de ranking y `BreadcrumbList` JSON-LD donde hay breadcrumb visual; validan contra schema.org; check de build asegura presencia en plantillas muestreadas.

### Homicidio (HOM) — Phase 14

- [ ] **HOM-01**: `homicidios` (subgrupo destacado 101) seleccionable como filtro/capa propia con su coroplético, distinto de "vida"; pipeline emite la tasa de homicidios por comuna al map-payload.
- [ ] **HOM-02**: El panel de comuna muestra cifra/desglose de homicidios separado (no solo "vida" agregada), con fuente CEAD + año; sin regresión al render de familias.

### SEO por Tipo de Delito (CSEO) — Phase 15

- [ ] **CSEO-01**: Páginas programáticas bilingües "las N comunas con más {delito}" (homicidio primero) con internal linking a comuna/región, hreflang recíproco y sitemap.
- [ ] **CSEO-02**: Cada página estática/indexable con un solo H1 con keyword, title/meta/canonical únicos, e `ItemList` JSON-LD; tono sobrio preservado.

### Noticias (NEWS) — Phase 16

- [ ] **NEWS-01**: Geolocalización rediseñada — el LLM emite el NOMBRE de la comuna (+ hint de región), resuelto por lookup determinista nombre→CUT; precisión medida contra golden set y supera el enfoque actual.
- [ ] **NEWS-02**: Golden set etiquetado (30–50 incidentes con comuna+familia ground-truth) + script de scoring; proveedor LLM configurable por env; A/B DeepSeek vs MiniMax; ganador documentado y default.
- [ ] **NEWS-03**: El pipeline corre de verdad (gated por API keys) produciendo `data/incidents/current.json`; pins + "incidentes recientes" renderizan incidentes reales geolocalizados, sin errores de consola.
- [ ] **NEWS-04**: Cada incidente enlaza a su fuente ↗ Y a la ficha de su comuna; página de noticias dedicada (bilingüe); indicador de frescura; todos citan y enlazan la fuente.

## Backlog / Tech Debt (carried into v1.2)

- **BUGFIX-999.1**: Comunas de Tarapacá mal-asignadas a Aysén/Los Ríos. `region_id` usa código de provincia de 2 dígitos que colisiona con los números de región 11 (Aysén) y 14 (Los Ríos). El resolver de región agrupa Iquique/Alto Hospicio→Aysén y Pozo Almonte/Pica/Huara/Camiña/Colchane→Los Ríos; la página de región Tarapacá queda vacía. Fix: derivar región del CUT (longitud desambigua) en vez del `region_id` almacenado. Capa de datos; encontrado 2026-06-15 en el cierre de v1.1.
- **TECHDEBT-01**: Aserción CI del orden de `FAMILY_KEYS` (duplicado pipeline ↔ `FiltersRow.tsx`).
- **TECHDEBT-02**: Tipado de `by_family` (`number[]` vs `float|None`) unificado.
- **TECHDEBT-03**: `AVAILABLE_YEARS` derivado dinámicamente de los datos (hoy hardcodeado 2005–2025).
- **TECHDEBT-04**: Flip de `nyquist_compliant` en VALIDATION.md (fases 4–6); 08-VALIDATION.md ausente.
- **F-002 / F-004** (de v1.1): páginas legales cookie/accesibilidad inexistentes; páginas de contacto delgadas. Polish, no bloqueantes.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Go-live `ischilesafe.com` (CF Pages + DNS + secrets) | Trabajo humano (`DEPLOYMENT.md`); gated por humano. |
| Flip de `ADSENSE_ENABLED` + AdSense Consent Mode | Post-indexación, trabajo de go-live. |
| Features nuevas (capa social, comentarios, comparador) | Diferidas post-MVP. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GEO-01, GEO-02 | Phase 10 | Complete |
| COMU-01, COMU-02, COMU-03 | Phase 11 | Complete |
| IA-01, IA-02, IA-03 | Phase 12 | Pending |
| RSEO-01, RSEO-02 | Phase 13 | Pending |
| HOM-01, HOM-02 | Phase 14 | Pending |
| CSEO-01, CSEO-02 | Phase 15 | Pending |
| NEWS-01..04 | Phase 16 | Pending |

**Coverage:** v1.2 = 19 requirements across Phases 10–16. Complete: 5 (GEO×2, COMU×3). Pending: 14. All mapped; unmapped: 0 ✓

---
*Requirements re-scoped to v1.2 on 2026-06-15 at v1.1 milestone close. v1.1 requirements archived in milestones/v1.1-REQUIREMENTS.md.*
