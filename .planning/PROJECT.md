# Chile Safety Map (ischilesafe.com)

## What This Is

Plataforma bilingüe (ES/EN) que visualiza la seguridad territorial de Chile combinando dos capas: **cuantitativa** (estadísticas oficiales de incidencia delictiva del CEAD por comuna, región y país, mediante mapa coroplético, rankings y series temporales) y **cualitativa** (incidentes recientes extraídos de RSS de medios de prensa, clasificados y geolocalizados con DeepSeek v4, mostrados como pins en el mapa). Sirve a residentes, turistas, expats, estudiantes y personas evaluando dónde vivir, alojarse o viajar.

El sitio captura tráfico SEO mediante páginas programáticas bilingües (por comuna, región y tipo de delito) y páginas editoriales prioritarias ("Is Santiago safe", "comunas más seguras de Chile"). Monetización inicial: AdSense.

## Core Value

Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

## Current Milestone: v1.2 Map Fidelity, Findability & News

**Goal:** El sitio tiene material rico pero "perdido" — geometría blocky, comunas inalcanzables, rankings que no enlazan comunas, capa de noticias construida pero apagada. v1.2 lo conecta y lo activa.

**Sequence:** geometría real (10 ✓) → publicar 346 + finder (11 ✓) → home/IA hub-and-spoke (12) → SEO de rankings (13) → homicidio como categoría (14) → SEO por tipo de delito (15) → activar noticias + geolocalización rediseñada + A/B de modelos (16).

**Status:** Phases 10–11 shipped 2026-06-15; next active phase = 12. Excluye go-live (humano, `DEPLOYMENT.md`).

## Requirements

### Validated (v1.0 — code-complete 2026-06-13)

**Datos cuantitativos (CEAD)**
- ✓ Scraper Python CEAD → JSON estático versionado (frecuencias/tasas por comuna/región/país, familias, 2005–presente) — v1.0 (Phase 1, DATA-01..04)
- ✓ Mapa coroplético nacional interactivo (Leaflet) región + comuna — v1.0 (Phase 3, MAP-01)
- ✓ Filtros por año y tipo de delito; color por incidencia relativa — v1.0 (Phase 3, MAP-02/03)
- ✓ Popup/panel territorial: tasa, tendencia, ranking, sparkline, desglose por familia — v1.0 (Phase 3, MAP-04)
- ✓ Ranking nacional y regional por incidencia (tasa/100k, excluye <10k hab) — v1.0 (Phase 2/3)
- ✓ Geolocalización "mostrar mi ubicación" + identificación de comuna (ray-cast PiP) — v1.0 (Phase 3, MAP-05)

**Datos cualitativos (noticias)**
- ✓ Pipeline RSS (BioBíoChile, Cooperativa Policial, La Tercera) con fallback por feed — v1.0 (Phase 5, NEWS-01)
- ✓ DeepSeek v4-flash: clasificar/extraer comuna (lista cerrada 346, temp 0.0)/geolocalizar/deduplicar/resumir — v1.0 (Phase 5, NEWS-02/03)
- ✓ Pins de incidentes con fuente + fecha; ventana 30 días + archivo mensual — v1.0 (Phase 5, NEWS-04/05; Phase 3, MAP-05/06)
- ✓ Cron GitHub Actions (noticias ~6h, CEAD trimestral) → commit datos → Deploy Hook (sin rebuild loop) — v1.0 (Phase 6, INFRA-01/02)

**Sitio y SEO**
- ✓ Sitio Astro estático + islas React (mapa) — v1.0 (Phase 2/3)
- ✓ Páginas programáticas 346 comunas + 16 regiones + tipos de delito, ES/EN — v1.0 (Phase 2, PAGES-01..04)
- ✓ 10 páginas editoriales EN + 10 ES prioritarias — v1.0 (Phase 4, EDIT-01/02)
- ✓ Página metodológica (fuentes, tasas, subregistro, criterios) — v1.0 (Phase 4, EDIT-03)
- ✓ i18n ES/EN con hreflang, sitemap, Schema.org — v1.0 (Phase 2, SEO-01..04)
- ✓ Integración AdSense (env-gated, gate de lenguaje prohibido) — v1.0 code-complete (Phase 4, EDIT-05/MON-01)

### Validated (v1.1 Polish & QA — shipped 2026-06-15)

- ✓ E2E browser review (ES/EN) → consolidated findings; deferred Phase-3 visual/mobile UAT closed — v1.1 (Phase 7, REVIEW-01..05)
- ✓ Data correctness: rates use national MEAN ranked by rate/100k; 0 console errors; dead ranking links gated; AdSlot no-CLS / 0 adsbygoogle disabled — v1.1 (Phase 8, BUGFIX-01..05)
- ✓ UX/readability/a11y: single-H1 hierarchy, 720px prose, bilingual glossary, sober tone, WCAG-AA contrast, map-control aria, meta/JSON-LD; grammatical ES region naming (F-006) + keyboard-operable mobile nav (WR-03) — v1.1 (Phase 9, UX/READ/A11Y)

### Validated (v1.2 — partial, shipped 2026-06-15)

- ✓ High-resolution commune geometry from chilemapas (real boundaries, 85.6KB gzip, 346/0/0/0 join) — v1.2 (Phase 10, GEO-01/02)
- ✓ All 346 comunas published + searchable directory (A–Z + by-region, accent-insensitive); rankings link every comuna; sitemap covers all — v1.2 (Phase 11, COMU-01/02/03)

### Active (v1.2 remaining + launch)

- [ ] **Phase 12** Home/IA redesign (Hybrid C+B) + comuna hub-and-spoke [IA-01..03]
- [ ] **Phase 13** Ranking SEO hardening (OG/Twitter cards, ItemList/BreadcrumbList JSON-LD) [RSEO-01/02]
- [ ] **Phase 14** Homicide as a first-class map category [HOM-01/02]
- [ ] **Phase 15** Crime-type SEO ranking pages [CSEO-01/02]
- [ ] **Phase 16** News activation + geolocation redesign + DeepSeek/MiniMax A/B [NEWS-01..04]
- [ ] **BUGFIX-999.1** Tarapacá comunas mis-assigned to Aysén/Los Ríos (region_id 11/14 collision) — derive region from CUT. Found at v1.1 close.
- [ ] **Go-live `ischilesafe.com`** (human): `DEPLOYMENT.md` — CF Pages + DNS + secrets; live pipeline + 50-incident audit; GSC submission; flip `ADSENSE_ENABLED` + Consent Mode.
- [ ] Deuda técnica: aserción CI de orden FAMILY_KEYS; tipado `by_family`; `AVAILABLE_YEARS` dinámico; flip `nyquist_compliant` (fases 4–6); 08-VALIDATION.md.

### Out of Scope

- **Capa social (reportes de usuarios, tipo Waze de seguridad)** — requiere backend, moderación y masa crítica de usuarios; anotada como dirección futura post-MVP
- **Comentarios/discusión comunitaria** — misma razón; futuro
- **Backend dedicado / base de datos viva** — el MVP es 100% estático (JSON en repo + rebuilds); revisar solo si la capa social se activa
- **Calificaciones absolutas "seguro/peligroso"** — decisión editorial: solo incidencia reportada, comparación relativa y contexto; reduce riesgo reputacional y legal
- **Reportes descargables, newsletter, comparador avanzado, leads** — monetización futura, no MVP
- **App móvil** — web responsive es suficiente para validar

## Context

- **Fuente cuanti:** CEAD (cead.minsegpublica.gob.cl) — endpoints POST PHP sin autenticación, documentados en `como scrap.txt`: `get_estadisticas_delictuales.php` (tablas HTML, parsear con BeautifulSoup), `get_estadisticas_delictuales_mapa.php` (JSON directo), `ajax_2.php` (catálogos). Datos 2005–2026, granularidad anual/trimestral/mensual, 7 familias / 22 grupos / 45+ subgrupos de delito, todas las comunas. Botón "Descargar Excel" (`descarga=true`) permite datasets completos. Sin ToS que prohíban scraping; aplicar rate limiting cortés.
- **Prototipo de diseño existente** en `ischilesafe.com/`: React + Leaflet con datos placeholder — home, vista mapa, panel de resultados (tasa, tendencia, ranking #, sparkline 2019–2024, barras por tipo), i18n ES/EN, paleta teal (#0f766e) con escala de incidencia de 5 niveles, basemap claro/detallado. Es la referencia visual y de UX; los componentes se portan a islas Astro/React.
- **GeoJSON de comunas/regiones:** disponible en repos públicos (ej. chile-geojson); el prototipo incluye `geo-data.js` (~222 KB).
- **Lenguaje editorial sobrio (crítico):** usar "incidencia reportada", "comparación relativa", "tasa por habitantes", "evolución anual", "precauciones prácticas". Evitar "zona peligrosa", "zona segura garantizada", "ranking definitivo", "comunas peligrosas".
- **Objetivo de validación SEO del MVP:** que Google responda en tres tipos de búsqueda — nacional ("Chile crime map", "mapa del delito Chile"), local ("seguridad en Providencia", "delitos por comuna"), turística ("is Santiago safe").
- **Prioridad editorial:** Santiago, Valparaíso, Viña del Mar, Concepción, La Serena, Antofagasta, Temuco, Puerto Montt, Punta Arenas y zonas turísticas (Pucón, Puerto Varas, San Pedro de Atacama).

## Constraints

- **Presupuesto**: Infraestructura ~$0 — Cloudflare Pages gratis, GitHub Actions gratis; único costo variable es API DeepSeek v4 (económica) para procesamiento de noticias
- **Tech stack**: Astro + islas React + Leaflet (frontend); Python (scrapers CEAD y RSS); JSON estático en repo como almacén de datos — sin servidor ni DB en MVP
- **Dependencias**: CEAD es fuente única cuanti — endpoints no oficiales pueden cambiar sin aviso; pipeline debe fallar con gracia y alertar
- **SEO**: Todas las páginas deben ser HTML estático pre-renderizado e indexable — nada de contenido crítico render-only en cliente
- **Cortesía de scraping**: delays entre requests a CEAD (servidor gubernamental) y respeto a robots/RSS de medios
- **Editorial/legal**: nunca calificar territorios como "peligrosos/seguros" en absoluto; siempre atribuir fuentes (CEAD, medio de prensa); incidentes de noticias citan y enlazan la fuente

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Astro + islas React en vez de SPA del prototipo | El tráfico esperado es 100% búsqueda orgánica; hash-routing no indexa. Astro pre-renderiza miles de páginas programáticas y reutiliza los componentes React del prototipo como islas | ✓ Good — v1.0 |
| Scrape → JSON estático versionado (sin backend/DB) | Costo cero, simplicidad, los datos CEAD cambian trimestralmente; GitHub Actions + rebuild cubre la frecuencia de noticias | ✓ Good — v1.0 |
| Capa de noticias (RSS + DeepSeek v4) en MVP v1 | Es la diferenciación del producto: cuanti + cuali; CEAD solo da agregados, las noticias dan el "qué está pasando ahora" | ✓ Good — v1.0 |
| Pipeline en GitHub Actions cron | RSS cada pocas horas → DeepSeek → commit JSON → rebuild; CEAD trimestral. Sin servidor que mantener | ✓ Good — v1.0 |
| Hosting Cloudflare Pages | Gratis, CDN global, soporta miles de páginas estáticas, compatible AdSense | ✓ Good — v1.0 |
| Páginas programáticas para las 346 comunas desde v1 | Máximo footprint SEO con datos reales de plantilla; editorial manual solo en ~10 prioritarias | ✓ Good — v1.0 |
| Capa social diferida (reportes de usuarios) | Requiere backend y masa crítica; el MVP valida demanda SEO primero | ✓ Good — v1.0 |
| DeepSeek v4 como LLM de procesamiento | Costo bajo por volumen de noticias diario; tareas acotadas (clasificar, extraer comuna, geolocalizar, deduplicar) | ✓ Good — v1.0 |
| Helper `regionNameEs()` para nombres de región en ES | "Región de {name}" es agramatical para Metropolitana/Maule/Biobío; un helper centraliza las 3 reglas (sin preposición / "del" / "de") y se usa en páginas de región + prose engine | ✓ Good — v1.1 (F-006) |
| Hamburger zero-JS keyboard-operable vía checkbox sr-only-but-focusable | Mantiene la restricción D-09 (zero-JS) y da ruta de teclado al menú móvil sin display:none | ✓ Good — v1.1 (WR-03) |
| chilemapas (GPL-3) como fuente de geometría comunal | Límites reales reconocibles dentro del presupuesto de tamaño; re-key de código a CUT con zero-pad | ✓ Good — v1.2 (Phase 10) |
| ROLLOUT_ALL=true como default de build | Publicar las 346 comunas; elimina el problema de "material perdido" (orphan pages) | ✓ Good — v1.2 (Phase 11) |
| `region_id` de 2 dígitos como clave de región | Códigos de provincia colisionan con números de región 10–16 (Tarapacá 11/14 ↔ Aysén/Los Ríos) | ⚠️ Revisit — v1.2 (BUGFIX-999.1: derivar región del CUT) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## Current State

**Shipped:** v1.0 MVP (2026-06-13, 6 phases) → v1.1 Polish & QA (2026-06-15, Phases 7–9) → v1.2 in progress (Phases 10–11 shipped 2026-06-15; next = Phase 12). v1.1 closed with the two audit-flagged defects fixed (F-006 ES region grammar, WR-03 hamburger keyboard); 10/10 validators pass.

**Stack as built:** Astro 6.4 + React islands + Leaflet (frontend, `site/`); Python 3.12 pipeline (CEAD scraper + RSS/DeepSeek news, `pipeline/`, Pydantic v2, pytest); JSON-in-repo data store; GitHub Actions cron + Cloudflare Pages Deploy-Hook deploy. Now publishing all 346 comunas (×2 locales) with real chilemapas geometry and a searchable directory; 772 pages build clean under the 20K Cloudflare limit; 10 frontend validators + pipeline tests green.

**Known data issue (v1.2 backlog 999.1):** Tarapacá comunas (Iquique, Alto Hospicio, Pozo Almonte, Pica, Huara, Camiña, Colchane) are mis-grouped under Aysén/Los Ríos because `region_id` stores ambiguous 2-digit province codes (11/14) that collide with region numbers. Fix = derive region from the CUT.

**Not yet live:** the site is not deployed — go-live requires a Cloudflare account, DNS for `ischilesafe.com`, and the `DEEPSEEK_API_KEY` / `CF_DEPLOY_HOOK_URL` secrets (all in `DEPLOYMENT.md`). That single human step also unblocks the news live-run + 50-incident audit and AdSense activation.

---
*Last updated: 2026-06-15 — after v1.1 Polish & QA milestone (v1.2 active)*
