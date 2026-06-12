# REQUIREMENTS — Chile Safety Map (ischilesafe.com) v1

## v1 Requirements

### Datos CEAD (DATA)

- [ ] **DATA-01**: Scraper Python extrae frecuencias y casos policiales desde los endpoints CEAD (`get_estadisticas_delictuales*.php`) para las 346 comunas, 16 regiones y total país, todos los años disponibles (2005–presente) y las 7 familias de delito
- [ ] **DATA-02**: Cada scrape se valida con esquema Pydantic (346 comunas presentes, claves esperadas, tasas dentro de rangos plausibles); ante fallo el pipeline termina con error sin commitear, preservando el último JSON bueno
- [ ] **DATA-03**: Datos normalizados a JSON estático versionado en el repo: un archivo por comuna, por región, agregado nacional y un payload de mapa pre-agregado (~28 KB)
- [ ] **DATA-04**: La tasa por 100.000 habitantes es la métrica canónica del data contract; los rankings nacionales aplican filtro de población mínima (10.000 hab) y nunca ordenan por conteo absoluto

### Capa de noticias (NEWS)

- [ ] **NEWS-01**: Pipeline ingesta RSS de fuentes confirmadas (BioBíoChile, Cooperativa Policial, La Tercera Nacional) con fallback por feed: un feed caído se salta y registra sin bloquear el pipeline
- [ ] **NEWS-02**: DeepSeek v4-flash clasifica cada noticia policial: tipo de delito, comuna contra lista cerrada de 346 valores canónicos (temperatura 0.0), geolocalización aproximada y resumen; incidentes con comuna no-match se rechazan
- [ ] **NEWS-03**: Incidentes duplicados entre fuentes se deduplican antes de publicar
- [ ] **NEWS-04**: `incidents/current.json` mantiene ventana móvil de 30 días con archivo mensual (`archive/YYYY-MM.json`)
- [ ] **NEWS-05**: Cada incidente publicado cita y enlaza su fuente de prensa con fecha

### Mapa interactivo (MAP)

- [ ] **MAP-01**: Usuario puede explorar un mapa coroplético nacional con comunas coloreadas según incidencia relativa
- [ ] **MAP-02**: Usuario puede filtrar el mapa por año y por tipo de delito
- [ ] **MAP-03**: Usuario puede abrir un panel territorial por comuna con tasa, tendencia, ranking, evolución temporal (sparkline) y desglose por tipo de delito
- [ ] **MAP-04**: Usuario puede ver pins de incidentes recientes de noticias con fuente y fecha en el mapa
- [ ] **MAP-05**: Usuario puede pulsar "mostrar mi ubicación" y el sitio identifica y resalta su comuna
- [ ] **MAP-06**: El mapa es usable en móvil de gama media: GeoJSON simplificado (<100 KB), estilos memoizados

### Páginas programáticas (PAGES)

- [ ] **PAGES-01**: 346 páginas de comuna en ES y EN generadas con datos reales, cada una con 500+ palabras y 5+ dimensiones únicas (tasa vs promedio nacional/regional, tendencia, delito dominante, contexto regional, comuna comparable)
- [ ] **PAGES-02**: 16 páginas de región en ES y EN con agregados y ranking de sus comunas
- [ ] **PAGES-03**: Páginas por tipo de delito (ES/EN) con mapa y ranking filtrados
- [ ] **PAGES-04**: Despliegue de páginas programáticas por lotes: 10–20 primero, verificar indexación en Google Search Console antes de generar las 346

### Páginas editoriales (EDIT)

- [ ] **EDIT-01**: 10 páginas editoriales EN prioritarias: `/`, `/chile-crime-map/`, `/is-chile-safe/`, `/santiago-safety-map/`, `/is-santiago-safe/`, `/valparaiso-safety/`, `/vina-del-mar-safety/`, `/concepcion-safety/`, `/safest-cities-in-chile/`, `/methodology/`
- [ ] **EDIT-02**: 10 páginas editoriales ES prioritarias: `/es/`, `/es/mapa-delito-chile/`, `/es/delitos-por-comuna/`, `/es/delitos-por-region/`, `/es/comunas-mas-seguras-chile/`, `/es/mapa-seguridad-santiago/`, `/es/seguridad-valparaiso/`, `/es/seguridad-vina-del-mar/`, `/es/seguridad-concepcion/`, `/es/metodologia/`
- [ ] **EDIT-03**: Página metodológica documenta fuentes, límites, cálculo de tasas, subregistro y criterios de comparación
- [ ] **EDIT-04**: Páginas legales: Privacy Policy, Terms, About y Contact (requisito AdSense)
- [ ] **EDIT-05**: El build falla si una página usa lenguaje editorial prohibido ("zona peligrosa", "comunas peligrosas", "ranking definitivo", "zona segura garantizada")

### SEO e i18n (SEO)

- [ ] **SEO-01**: Sitio bilingüe ES/EN con hreflang correcto y recíproco en todas las páginas (EN en raíz, ES bajo `/es/`)
- [ ] **SEO-02**: sitemap.xml automático y canonical tags en todas las páginas
- [ ] **SEO-03**: Schema.org structured data (Dataset/Place) en páginas territoriales
- [ ] **SEO-04**: PWA meta básico: manifest y theme color (sin service worker)

### Infraestructura (INFRA)

- [ ] **INFRA-01**: GitHub Actions cron: pipeline de noticias cada 4–6 horas, scraper CEAD trimestral, con rate limiting cortés hacia CEAD
- [ ] **INFRA-02**: Prevención de loop de rebuilds: commits de datos con GITHUB_TOKEN, auto-build de Cloudflare Pages deshabilitado, Deploy Hook invocado solo cuando los datos cambiaron
- [ ] **INFRA-03**: Sitio desplegado en Cloudflare Pages bajo ischilesafe.com

### Monetización (MON)

- [ ] **MON-01**: Integración AdSense activada tras la primera ola de indexación (metodología y legales ya indexadas)

## v2 Requirements (deferred)

- **NEWS-v2**: Más fuentes RSS (T13, 24Horas, Meganoticias, SoyChile regionales) tras validación de URLs
- **SOCIAL-v2**: Reportes de usuarios (capa social tipo Waze de seguridad) — requiere backend y moderación
- **ALERT-v2**: Alertas por email por comuna
- **DL-v2**: Reportes descargables / API de datos
- **COMP-v2**: Comparador avanzado de comunas
- **NL-v2**: Newsletter

## Out of Scope

- **Calificaciones absolutas "seguro/peligroso" (grades A–F)** — exposición legal y editorial; solo incidencia reportada y comparación relativa
- **Calculadora de probabilidad de victimización** — falsa precisión dado el subregistro
- **Backend dedicado / DB viva** — MVP 100% estático; revisar solo si capa social se activa
- **App móvil nativa** — web responsive + PWA meta suficiente para validar
- **Comentarios/discusión comunitaria** — requiere moderación y masa crítica

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| PAGES-01 | Phase 2 | Pending |
| PAGES-02 | Phase 2 | Pending |
| PAGES-03 | Phase 2 | Pending |
| PAGES-04 | Phase 2 | Pending |
| SEO-01 | Phase 2 | Pending |
| SEO-02 | Phase 2 | Pending |
| SEO-03 | Phase 2 | Pending |
| SEO-04 | Phase 2 | Pending |
| MAP-01 | Phase 3 | Pending |
| MAP-02 | Phase 3 | Pending |
| MAP-03 | Phase 3 | Pending |
| MAP-04 | Phase 3 | Pending |
| MAP-05 | Phase 3 | Pending |
| MAP-06 | Phase 3 | Pending |
| EDIT-01 | Phase 4 | Pending |
| EDIT-02 | Phase 4 | Pending |
| EDIT-03 | Phase 4 | Pending |
| EDIT-04 | Phase 4 | Pending |
| EDIT-05 | Phase 4 | Pending |
| MON-01 | Phase 4 | Pending |
| NEWS-01 | Phase 5 | Pending |
| NEWS-02 | Phase 5 | Pending |
| NEWS-03 | Phase 5 | Pending |
| NEWS-04 | Phase 5 | Pending |
| NEWS-05 | Phase 5 | Pending |
| INFRA-01 | Phase 6 | Pending |
| INFRA-02 | Phase 6 | Pending |
| INFRA-03 | Phase 6 | Pending |

---
*Last updated: 2026-06-12 after roadmap creation*
