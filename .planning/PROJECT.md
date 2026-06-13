# Chile Safety Map (ischilesafe.com)

## What This Is

Plataforma bilingüe (ES/EN) que visualiza la seguridad territorial de Chile combinando dos capas: **cuantitativa** (estadísticas oficiales de incidencia delictiva del CEAD por comuna, región y país, mediante mapa coroplético, rankings y series temporales) y **cualitativa** (incidentes recientes extraídos de RSS de medios de prensa, clasificados y geolocalizados con DeepSeek v4, mostrados como pins en el mapa). Sirve a residentes, turistas, expats, estudiantes y personas evaluando dónde vivir, alojarse o viajar.

El sitio captura tráfico SEO mediante páginas programáticas bilingües (por comuna, región y tipo de delito) y páginas editoriales prioritarias ("Is Santiago safe", "comunas más seguras de Chile"). Monetización inicial: AdSense.

## Core Value

Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

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

### Active (next — launch + v1.1 candidates)

- [ ] **Go-live `ischilesafe.com`** (human): ejecutar `DEPLOYMENT.md` — CF Pages + DNS + secrets; corre la pipeline en vivo + auditoría de 50 incidentes (DeepSeek key); GSC submission; flip `ADSENSE_ENABLED` + AdSense Consent Mode tras la primera ola de indexación.
- [ ] Phase-3 visual/mobile UAT (render/jank/geoloc/3G) — verificación manual diferida.
- [ ] Deuda técnica: aserción CI de orden FAMILY_KEYS; tipado `by_family`; `AVAILABLE_YEARS` dinámico; flip de `nyquist_compliant` en VALIDATION.md (fases 4–6).

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

**Shipped:** v1.0 MVP — code-complete 2026-06-13 (6 phases, 28 plans). All 32 requirements code-complete; all cross-phase contracts wired and E2E flows sound (milestone audit). Phases 1–3 verified `passed`; Phases 4–6 `human_needed` (deferred live go-live gates only — not code gaps).

**Stack as built:** Astro 6.4 + React islands + Leaflet (frontend, `site/`); Python 3.12 pipeline (CEAD scraper + RSS/DeepSeek news, `pipeline/`, Pydantic v2, pytest); JSON-in-repo data store; GitHub Actions cron + Cloudflare Pages Deploy-Hook deploy (`.github/workflows/`, `DEPLOYMENT.md`). ~135 pipeline tests + 9 frontend validators green; ~100 site pages build clean.

**Not yet live:** the site is not deployed — go-live requires a Cloudflare account, DNS for `ischilesafe.com`, and the `DEEPSEEK_API_KEY` / `CF_DEPLOY_HOOK_URL` secrets (all documented in `DEPLOYMENT.md`). That single human step also unblocks the news live-run + 50-incident audit and AdSense activation.

---
*Last updated: 2026-06-13 after v1.0 milestone*
