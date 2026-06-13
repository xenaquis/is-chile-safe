# Phase 1: Data Foundation - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

CEAD scraper (Python) extracts and validates all quantitative crime data into a stable, versioned JSON schema in `/data/cead/` that every downstream component (Astro pages, Leaflet map, news pipeline commune list) can consume. Covers all 346 comunas, 16 regions, and national aggregates, 2005–present. Requirements: DATA-01, DATA-02, DATA-03, DATA-04.

Out of this phase: the Astro site, the map UI, RSS/news pipeline, GitHub Actions cron wiring (Phase 6 — but the scraper must be runnable both locally and in CI).

</domain>

<decisions>
## Implementation Decisions

### Estrategia de extracción
- **D-01:** Método principal: descarga Excel bulk (`descarga=true`) — minimiza requests al servidor gubernamental y evita parsing frágil de HTML.
- **D-02:** Fallback automático a scraping de tablas HTML (`get_estadisticas_delictuales.php` + bs4/lxml) en el mismo run si el Excel falla o cambia de formato. El run trimestral no muere por un cambio de formato.
- **D-03:** Rate limiting cortés: 2–3 s de delay fijo entre requests + retry con backoff exponencial (tenacity).
- **D-04:** Respuestas crudas (Excel/HTML) se cachean en carpeta local ignorada por git (debug y re-parseo sin re-scrapear). El repo solo versiona JSON normalizado.

### Alcance y granularidad
- **D-05:** Taxonomía: 7 familias + 22 grupos. Subgrupos NO se almacenan en general, con excepción selectiva (D-06).
- **D-06:** Categorías destacadas: **homicidios, secuestros y delitos contra la propiedad**. Si CEAD expone homicidios/secuestros solo a nivel subgrupo, incluir esos subgrupos específicos. El schema marca estas categorías con flag `featured` para que páginas y mapa las prioricen. Razón del usuario: homicidios es el delito con menor cifra negra (subregistro mínimo) — máxima confiabilidad estadística.
- **D-07:** Granularidad temporal: series anuales 2005–presente solamente. Sin trimestral/mensual en MVP.
- **D-08:** Tipo de dato: solo casos policiales (`tipoVal=1,2`). Sin series separadas de denuncias/detenciones.
- **D-09:** `map-payload.json`: último año completo, con tasa total + 7 tasas por familia por comuna (<30 KB). Además, el pipeline escribe `map-payload-{año}.json` por cada año disponible (mismo formato, <30 KB c/u) para que el filtro de año del mapa (Fase 3, MAP-02) funcione sin recalcular.

### Población y cálculo de tasas
- **D-10:** Tasas por 100k: usar las tasas oficiales que CEAD ya calcula (`medida=2`) — consistencia con la fuente citada. No calcular tasas propias.
- **D-11:** Población comunal: proyecciones oficiales INE como archivo estático de referencia commiteado en `/data/` (sin scraping adicional). Usada SOLO para el filtro de ranking y contexto en páginas. El researcher debe localizar el dataset descargable oficial del INE.
- **D-12:** Comunas <10.000 hab: excluidas de rankings nacional/regional (`rank: null` + flag `low_population: true`), pero su archivo igual contiene tasas — la página mostrará la tasa con caveat de volatilidad estadística.
- **D-13:** Tendencia (`trend`): variación % de la tasa total en los últimos 3 años con umbral (~5%): `up`/`down`/`stable`. Fórmula exacta a documentar en la página de metodología (Fase 4).

### Fallos, validación y alertas
- **D-14:** Política todo-o-nada: cualquier violación del schema Pydantic (conteo ≠346 comunas, claves faltantes, tasas implausibles) → exit no-cero, sin commit, último JSON bueno intacto. Datos congelados > datos corruptos.
- **D-15:** Alertas: email nativo de GitHub Actions al fallar + el workflow crea/actualiza un GitHub issue automático con el log del error. Sin webhooks externos.
- **D-16:** Plausibilidad de tasas: validación contra rango histórico por comuna/familia (ej. ±3x del máximo histórico) para detectar corrupción del endpoint; la primera corrida usa límites absolutos amplios y fija la línea base histórica.
- **D-17:** ID canónico de comuna: código CUT oficial (Código Único Territorial INE, ej. `13101` = Santiago) como `id`, más `slug` derivado del nombre para URLs. El CUT es la clave de cruce con GeoJSON, INE y la lista cerrada de 346 valores para DeepSeek (Fase 5).

### Claude's Discretion
- Estructura interna exacta de los modelos Pydantic, naming de campos y layout de `/data/cead/meta/` (catalog.json, index.json) — seguir el schema propuesto en `.planning/research/ARCHITECTURE.md` como base.
- Manejo del año en curso parcial (incluirlo marcado como parcial o excluirlo) — decidir según cómo CEAD lo expone.
- Umbral exacto de la tendencia y márgenes exactos de plausibilidad — fijar en planning con datos reales.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Endpoints CEAD y estrategia de scraping
- `como scrap.txt` — Hallazgos completos de scrapeabilidad: los 4 endpoints POST (`ajax_2.php`, `get_estadisticas_delictuales.php`, `get_estadisticas_delictuales_mapa.php`, `_mapa_titulo.php`), parámetros (`medida`, `tipoVal`, `anio[]`, `region[]`, `familia[]`, `descarga`), mapa de IDs de regiones, taxonomía 7/22/45+. **El researcher debe validar en vivo los nombres de parámetros y campos de respuesta antes de implementar** (flag en STATE.md).

### Arquitectura y schema de datos
- `.planning/research/ARCHITECTURE.md` — Layout de `/data/cead/` (por comuna/región/nacional/map-payload/meta), schemas JSON de ejemplo, estructura `/pipeline/`, patrón Pydantic-validate-before-write, escritura atómica (temp + rename), prevención de loops de rebuild.
- `.planning/research/STACK.md` — Versiones y librerías Python: requests 2.32.x, bs4 4.14.x + lxml, tenacity 8.x, python-dotenv.
- `.planning/research/PITFALLS.md` — Pitfalls conocidos del dominio (validar conteo 346 tras cada scrape, error frecuencia-vs-tasa).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ischilesafe.com/` (prototipo React+Leaflet con datos placeholder): `data.js` define la forma que la UI consume (comuna con `id`, `name`, `region`, `lat/lng`, `level` 1–5, `trend` -1/0/1) y `geo-data.js` (~222 KB GeoJSON). El schema de Fase 1 debe poder derivar `level` (quintil de incidencia) y `trend` que el prototipo ya usa.
- No existe código de pipeline aún — greenfield en `/pipeline/`.

### Established Patterns
- Layout de proyecto definido en research: `/pipeline/` (Python aislado), `/data/` (JSON versionado en raíz del repo), `/site/` (Astro, fases posteriores).
- Patrón de validación: Pydantic antes de escribir; escritura atómica; exit no-cero ante fallo.

### Integration Points
- `/data/cead/comunas/{cut}.json`, `regions/{id}.json`, `national.json`, `map-payload.json` + `map-payload-{año}.json`, `meta/index.json`, `meta/catalog.json` — contrato consumido por Fase 2 (getStaticPaths), Fase 3 (mapa) y Fase 5 (lista canónica de comunas).
- `meta/index.json` con los 346 CUT + nombres + slug + región es la fuente de la lista cerrada para DeepSeek en Fase 5.

</code_context>

<specifics>
## Specific Ideas

- Homicidios como categoría estrella por menor cifra negra — el usuario quiere que el dato más confiable estadísticamente tenga visibilidad prioritaria (junto a secuestros y delitos contra la propiedad).
- Las tasas publicadas deben coincidir con las que CEAD publica (medida=2), para que cualquier verificación contra la fuente oficial cuadre exacto.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Data Foundation*
*Context gathered: 2026-06-12*
