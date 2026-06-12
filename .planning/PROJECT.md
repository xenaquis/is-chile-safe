# Chile Safety Map (ischilesafe.com)

## What This Is

Plataforma bilingüe (ES/EN) que visualiza la seguridad territorial de Chile combinando dos capas: **cuantitativa** (estadísticas oficiales de incidencia delictiva del CEAD por comuna, región y país, mediante mapa coroplético, rankings y series temporales) y **cualitativa** (incidentes recientes extraídos de RSS de medios de prensa, clasificados y geolocalizados con DeepSeek v4, mostrados como pins en el mapa). Sirve a residentes, turistas, expats, estudiantes y personas evaluando dónde vivir, alojarse o viajar.

El sitio captura tráfico SEO mediante páginas programáticas bilingües (por comuna, región y tipo de delito) y páginas editoriales prioritarias ("Is Santiago safe", "comunas más seguras de Chile"). Monetización inicial: AdSense.

## Core Value

Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Datos cuantitativos (CEAD)**
- [ ] Scraper Python de endpoints CEAD (get_estadisticas_delictuales*.php) → JSON estático versionado: frecuencias y tasas por comuna/región/país, por familia/grupo de delito, años 2005–presente
- [ ] Mapa coroplético nacional interactivo (Leaflet) con vista región y comuna
- [ ] Filtros por año y tipo de delito; colores según incidencia relativa
- [ ] Popup/panel territorial: tasa, tendencia, ranking, evolución temporal, desglose por tipo de delito
- [ ] Ranking nacional y regional de comunas por incidencia reportada
- [ ] Geolocalización: botón "mostrar mi ubicación" e identificación de la comuna del usuario

**Datos cualitativos (noticias)**
- [ ] Pipeline RSS: scraper de medios nacionales (Emol, BioBío, Cooperativa, T13, 24Horas) y regionales — research decide lista final según disponibilidad de RSS
- [ ] Procesamiento DeepSeek v4: clasificar tipo de delito, extraer comuna, geolocalizar aproximado, deduplicar, resumir
- [ ] Pins de incidentes recientes en el mapa con fuente y fecha
- [ ] Cron GitHub Actions: RSS cada pocas horas, CEAD trimestral → commit JSON → rebuild Cloudflare Pages

**Sitio y SEO**
- [ ] Sitio Astro estático con islas React (mapa), desplegado en Cloudflare Pages
- [ ] Páginas programáticas: 346 comunas + 16 regiones + tipos de delito, en ES y EN, generadas de plantilla con datos reales
- [ ] Páginas editoriales prioritarias EN: /, /chile-crime-map/, /is-chile-safe/, /santiago-safety-map/, /is-santiago-safe/, /valparaiso-safety/, /vina-del-mar-safety/, /concepcion-safety/, /safest-cities-in-chile/, /methodology/
- [ ] Páginas editoriales prioritarias ES: /es/, /es/mapa-delito-chile/, /es/delitos-por-comuna/, /es/delitos-por-region/, /es/comunas-mas-seguras-chile/, /es/mapa-seguridad-santiago/, /es/seguridad-valparaiso/, /es/seguridad-vina-del-mar/, /es/seguridad-concepcion/, /es/metodologia/
- [ ] Página metodológica: fuentes, límites, tasas, subregistro, criterios de comparación
- [ ] i18n ES/EN completo con hreflang, sitemap, metadatos SEO
- [ ] Integración AdSense

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
| Astro + islas React en vez de SPA del prototipo | El tráfico esperado es 100% búsqueda orgánica; hash-routing no indexa. Astro pre-renderiza miles de páginas programáticas y reutiliza los componentes React del prototipo como islas | — Pending |
| Scrape → JSON estático versionado (sin backend/DB) | Costo cero, simplicidad, los datos CEAD cambian trimestralmente; GitHub Actions + rebuild cubre la frecuencia de noticias | — Pending |
| Capa de noticias (RSS + DeepSeek v4) en MVP v1 | Es la diferenciación del producto: cuanti + cuali; CEAD solo da agregados, las noticias dan el "qué está pasando ahora" | — Pending |
| Pipeline en GitHub Actions cron | RSS cada pocas horas → DeepSeek → commit JSON → rebuild; CEAD trimestral. Sin servidor que mantener | — Pending |
| Hosting Cloudflare Pages | Gratis, CDN global, soporta miles de páginas estáticas, compatible AdSense | — Pending |
| Páginas programáticas para las 346 comunas desde v1 | Máximo footprint SEO con datos reales de plantilla; editorial manual solo en ~10 prioritarias | — Pending |
| Capa social diferida (reportes de usuarios) | Requiere backend y masa crítica; el MVP valida demanda SEO primero | — Pending |
| DeepSeek v4 como LLM de procesamiento | Costo bajo por volumen de noticias diario; tareas acotadas (clasificar, extraer comuna, geolocalizar, deduplicar) | — Pending |

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

---
*Last updated: 2026-06-12 after initialization*
