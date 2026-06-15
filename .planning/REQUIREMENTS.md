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

- [ ] **UX-01**: Jerarquía clara en money pages — un solo H1, H2/H3 escaneables; el lector entiende la página en ~5 segundos.
- [x] **UX-02**: Densidad de información reducida donde el review la marque — DataCallout/StatCard comunican una idea clara con su fuente (CEAD + año); redundancia callout↔prosa eliminada.

### Lectura / Editorial (READ)

- [x] **READ-01**: Columna de prosa legible en editoriales (~720px, ritmo de párrafos, sin muros de texto).
- [ ] **READ-02**: Paridad ES/EN — contenido, estructura y tono equivalentes entre cada par de páginas; sin secciones faltantes en un idioma.
- [ ] **READ-03**: Tono editorial sobrio respetado en todo el sitio (sin "peligroso/seguro" absoluto; usa "incidencia reportada", "comparación relativa"); jerga explicada.

### Accesibilidad / SEO (A11Y)

- [x] **A11Y-01**: En páginas muestreadas — contraste de color (paleta teal `--primary #0f766e`), focus states visibles, alt text presente, y aria en los controles del mapa.
- [ ] **A11Y-02**: En plantillas muestreadas — `<title>`, meta description, canonical, hreflang y JSON-LD (FAQPage en question-pages) presentes y válidos.

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
| UX-01 | Phase 9 | Pending |
| UX-02 | Phase 9 | Complete |
| READ-01 | Phase 9 | Complete |
| READ-02 | Phase 9 | Pending |
| READ-03 | Phase 9 | Pending |
| A11Y-01 | Phase 9 | Complete |
| A11Y-02 | Phase 9 | Pending |

**Coverage:**

- v1.1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-13*
*Last updated: 2026-06-13 — traceability filled after roadmap creation*
