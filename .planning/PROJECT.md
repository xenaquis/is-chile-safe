# Chile Safety Map (ischilesafe.com)

## What This Is

Plataforma bilingüe (ES/EN) que visualiza la seguridad territorial de Chile combinando dos capas: **cuantitativa** (estadísticas oficiales de incidencia delictiva del CEAD por comuna, región y país, mediante mapa coroplético, rankings y series temporales) y **cualitativa** (incidentes recientes extraídos de RSS de medios de prensa, clasificados y geolocalizados con DeepSeek v4, mostrados como pins en el mapa). Sirve a residentes, turistas, expats, estudiantes y personas evaluando dónde vivir, alojarse o viajar.

El sitio captura tráfico SEO mediante páginas programáticas bilingües (por comuna, región y tipo de delito) y páginas editoriales prioritarias ("Is Santiago safe", "comunas más seguras de Chile"). Monetización inicial: AdSense.

## Core Value

Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

## Last Milestone: v2.1 News Intelligence, Map UX & Ops Hardening (SHIPPED 2026-08-05)

**Goal:** Make the news layer explorable (facet by time / geography / crime family, and group reports of the same real-world event), make the map genuinely usable (news toggle and filters discoverable on desktop and 375px mobile), and close the outstanding documentation, cron-consistency and security-posture debt.

**Target features:**
- **Event clustering spike** (Phase 26) — can the LLMs we already pay for (Granite 4.1 8B via OpenRouter default, DeepSeek fallback) reliably group multiple articles covering the *same* incident? GO/NO-GO on cost, precision, and false-merge rate. Downstream integration only on GO.
- **News faceting data model** (Phase 27) — derive time / geography (comuna→region) / crime-family facets from the existing `incidents/current.json` + archive; no new upstream data. Facet counts computed at build time so pages stay static and indexable.
- **News visualizer UI** (Phase 28) — grouping + filtering UI on `/news/` and `/es/noticias/`, bilingual, SSG-safe (facets pre-rendered; JS only enhances). Clustered-event cards if Phase 26 is GO.
- **Map UX audit — iterative BrowserOS design loop** (Phase 29) — drive the real rendered site in BrowserOS, screenshot desktop + 375px, iterate the control-shell design with Fable, re-screenshot, and **repeat until the design is excellent**. Not a one-pass audit: the loop is the deliverable, with a human acceptance gate at the end.
- **Map control-shell rework** (Phase 30) — implement the accepted design. Leaflet logic in `MapIsland` is preserved; the filter panel and the news toggle are redesigned for discoverability, mobile 375px, keyboard and a11y.
- **Docs & methodology refresh** (Phase 31) — methodology, source registry, CEAD/press attribution, editorial + legal disclaimers brought current with everything shipped since v1.3.
- **Cron consistency** (Phase 32) — audit and reconcile the whole schedule surface: news daily, R2 research archive, CEAD quarterly reminder (runs local — Actions IPs are 403'd), and the freshness guard. One coherent story, no silent gaps.
- **Security posture** (Phase 33) — secrets hygiene, GitHub Actions permissions, rate limits, and scraping courtesy toward CEAD and press RSS, reviewed in detail.

**Key context:**
- **Per-phase protocol is mandatory** for every phase in this milestone: research → plan → premortem → plan review by a **Fable** agent → implementation by **Sonnet** → code review by **Opus** → GSD validation. Phases are deliberately granular so each cycle stays inside one context.
- **Phase 26 gates 27/28.** If clustering is NO-GO, the finding is documented and the visualizer ships with faceting only.
- **Phase 29 gates 30.** No map code is rewritten until a BrowserOS-verified design is accepted.
- **BrowserOS gotchas** (learned in v1.1/v1.2): run browser phases inline — `gsd-executor` has no BrowserOS tools; `save_screenshot` needs a path with no spaces; there is no viewport-resize, so emulate mobile via a 375px iframe. Serve the build with `npx astro preview --port 4321 --host` (there is no `npm run preview` script), and chain build+validate in one command because the repo lives in OneDrive and `dist/` desyncs between processes.
- **Non-negotiable constraints carried in:** never absolute "seguro/peligroso"; always attribute CEAD and the press outlet; every page stays pre-rendered and indexable; `sexuales` is a news-only family and CEAD `FAMILY_KEYS` stays at 7.
- **Regression surface:** 14 validators + ~179 pytest must stay green through every phase.

**Previous (v2.0, phases 18/21/22/23/24/25):** Composite Crime Index, ENUSC victimization layer, commune comparator + A-vs-B SEO, rankings UX, UI/UX 360 remediation, and go-live. Production is LIVE on v2.0 with both deploy secrets set.

**Carried-over deferred item:** Phase 22-03 — Google Search Console sitemap submission. Human/manual, not code; still outstanding.

**Known carry-over debt (candidates for this milestone's phases):** home-title cannibalization, 8 `astro-check` errors, `?region=` handling in `MapIsland`, `figure-registry.mjs` substring matching, and the unresolved ENUSC edition year in `SOURCES.md`.

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

### Validated (v1.2 Map Fidelity, Findability & News — shipped 2026-06-18)

- ✓ High-resolution commune geometry from chilemapas (real boundaries, 85.6KB gzip, 346/0/0/0 join) — v1.2 (Phase 10, GEO-01/02)
- ✓ All 346 comunas published + searchable directory (A–Z + by-region, accent-insensitive); rankings link every comuna; sitemap covers all — v1.2 (Phase 11, COMU-01/02/03)
- ✓ Home/IA redesign (Hybrid C+B) + comuna hub-and-spoke cross-linking — v1.2 (Phase 12, IA-01/02/03)
- ✓ Ranking SEO hardening: OG/Twitter cards site-wide, ItemList + BreadcrumbList JSON-LD — v1.2 (Phase 13, RSEO-01/02)
- ✓ Homicide as a first-class map category (own filter/layer + commune-panel breakdown) — v1.2 (Phase 14, HOM-01/02)
- ✓ Crime-type SEO ranking pages ("las N comunas con más {delito}", bilingual, homicide first) — v1.2 (Phase 15, CSEO-01/02)
- ✓ News activation: geolocation redesign (name→CUT resolver, 95.45% comuna acc), DeepSeek/MiniMax A/B (DeepSeek default), live pipeline (19 incidents), bilingual `/news/` + `/es/noticias/` with source + comuna links — v1.2 (Phase 16, NEWS-01..04)
- ✓ Data quality + source traceability + methodology: verified figures (`17-DATA-QUALITY.md`), canonical `data/SOURCES.md`, corrected CEAD host, reproducible source snapshots, rewritten bilingual methodology with clickable sources — v1.2 (Phase 17, DQ-01..04)
- ✓ **BUGFIX-999.1 resolved** Tarapacá region_id collision fixed (region derived from CUT length; all 16 regions populate) — 2026-06-16 (quick-260616-ldi)

### Active (next milestone + launch)

- [ ] **Phase 18 (proposed)** Composite Crime Index & Metric Redesign — exposure-adjusted composite index, SPD homicide-metric switch, `featured_rates`→7-metric schema migration, index-driven choropleth. High-risk/large — plan interactively. Sources + snapshots ready from Phase 17.
- [ ] **Go-live `ischilesafe.com`** (human): `DEPLOYMENT.md` — CF Pages + DNS + secrets; live pipeline + incident audit; GSC submission; flip `ADSENSE_ENABLED` + Consent Mode.
- ✓ Deuda técnica (RESUELTA en v1.3): aserción CI de orden FAMILY_KEYS, tipado `by_family`, `AVAILABLE_YEARS` dinámico, flip `nyquist_compliant` (fases 4–6), COMU-03 `/crime/homicide/` redirect, P15 advisory checks (P17-superseded) — todo cerrado en P19/P20.
- [ ] Deuda técnica residual (v1.4): endurecer `figure-registry.mjs` (match por substring → detección de section-stub); completar año de edición ENUSC en `SOURCES.md` (`[verify edition]`).

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
| `region_id` derivado del CUT (no del código de provincia) | Códigos de provincia de 2 dígitos colisionan con números de región 10–16 (Tarapacá 11/14 ↔ Aysén/Los Ríos); derivar del CUT lo resuelve | ✓ Good — v1.2 (BUGFIX-999.1 resuelto 2026-06-16) |
| LLM emite NOMBRE de comuna → resolver determinista nombre→CUT (no CUT crudo) | El modelo alucina CUTs crudos (~60-70% mal); emitir el nombre + lookup determinista (None si desconocido) sube la precisión a 95.45% — el diseño, no el proveedor, era el cuello de botella | ✓ Good — v1.2 (Phase 16, NEWS-01) |
| CEAD host correcto `cead.minsegpublica.gob.cl` + registro `data/SOURCES.md` | El sitio citaba el host equivocado (`ministeriointerior`); la afirmación "fuente de verdad" era ella misma no trazable | ✓ Good — v1.2 (Phase 17, DQ-02) |

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

**No milestone is currently open.** Six shipped and archived: v1.0 MVP (2026-06-13) → v1.1
Polish & QA (2026-06-15) → v1.2 Map Fidelity, Findability & News (2026-06-18) → v1.3 Data
Quality Hardening (2026-06-19) → **v2.0 Composite Index, Comparators & Launch** (production
live) → **v2.1 News Intelligence, Map UX & Ops Hardening** (2026-08-05, phases 26–33, executed
as an unattended autonomous run). Each is tagged in git and archived under
`.planning/milestones/` with its roadmap, requirements and audit.

**Stack as built:** Astro 6.4 + React islands + Leaflet (`site/`); Python 3.12 pipeline (CEAD
scraper, RSS + Granite-via-OpenRouter news classification, name→CUT resolver, R2 research
archive) in `pipeline/`; JSON-in-repo data store; GitHub Actions cron + Cloudflare Pages
deploy-hook. **Health, measured 2026-08-07:** pytest **395 passed / 1 skipped / 1 xfailed**,
vitest **59**, **16/16 validators**, `astro check` **0 errors / 0 warnings**, and four
workflow-security gates (`lint-workflows`, `check-sha-pins`, `check-secret-hygiene`, `zizmor`)
all exit 0. 1,271 built files against the 20K Cloudflare limit.

**Live:** `ischilesafe.com` on Cloudflare Pages. Auto-build is OFF; deploys fire from the
deploy hook — on `site/**` pushes via `deploy-on-code.yml`, and for data-only pushes via
`deploy-manual.yml` (`workflow_dispatch`, added 2026-08-06 to close H-05). Node pinned to
22.12.0 via `.nvmrc`, which CI now reads rather than hardcoding.

**Open for the operator, not for an agent:**

- Google Search Console sitemap submission — an operator monitoring task, not an indexing
  blocker (F-133: `robots.txt` already advertises the sitemap and Google discovers it).
- 12 Dependabot security alerts in `site/package-lock.json` (7 high) — pre-existing transitive
  dependencies whose only fix is an Astro 6 → 7 major; all three Astro advisories were verified
  unreachable in this codebase (`DEPLOYMENT.md` § Known Gaps, DEP-01).
- An Astro 7 migration, whenever it is wanted, as its own phase.

---
*Last updated: 2026-08-07 — v2.0 and v2.1 archived and tagged; no milestone open. Next step is `/gsd:new-milestone` when there is one.*
