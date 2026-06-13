# Brief — Revisión End-to-End (v1.1 Polish & QA)

> **Para el próximo contexto (post `/clear`).** Este documento es autosuficiente: contiene el objetivo, el método, el inventario de páginas, el checklist por dimensión, los prerrequisitos y cómo arrancar. Léelo completo antes de empezar.

## Objetivo

Recorrer **toda** la página renderizada, con paciencia y exhaustividad, para:
1. **Cazar bugs** — errores de consola, enlaces rotos, datos incorrectos, interacciones del mapa, filtros, geolocalización, hreflang, responsive/móvil, 404, estados vacíos.
2. **Reducir carga cognitiva** — densidad de información, jerarquía visual, divulgación progresiva, redundancia, jerga, legibilidad de gráficos/tablas.
3. **Hacerla un agrado de leer** — ritmo tipográfico, longitud de línea, espacio en blanco, escaneabilidad, tono editorial sobrio y claro, paridad ES/EN.

Resultado esperado: un **documento de hallazgos priorizados** (`.planning/REVIEW-E2E-FINDINGS.md`) y, tras aprobación, un **plan de correcciones** ejecutado por fases GSD.

## Método (MCP de navegador — paciente y exhaustivo)

- Conducir la revisión con el **MCP `pbrowseros` / BrowserOS** (ver prerrequisitos). Navegar página por página, tomar screenshot, leer el render real (no solo el código), abrir la consola del navegador para errores/warnings, redimensionar a móvil (~375px) y desktop.
- **Una página a la vez, sin apurar.** Por cada página: capturar, leer en voz baja como lector real, anotar fricción cognitiva y bugs con severidad (Critical / Warning / Polish) y una recomendación concreta.
- Verificar **comportamiento dinámico** del mapa (no solo estático): cambiar año, cambiar tipo de delito, click en comuna (panel: tasa/tendencia/ranking/sparkline/familias), búsqueda, "mostrar mi ubicación", capa de incidentes (estado vacío esperado sin pipeline en vivo).
- Para barrido amplio (las 740 páginas programáticas) usar **muestreo representativo** + verificación de plantilla, no las 740 una por una: revisar a fondo ~3 comunas (alta/medio/baja población, ej. Santiago 13101, Sierra Gorda micro, una RM), ~2 regiones, ~2 tipos de delito en ES y EN, y confiar en que la plantilla se repite. Declarar explícitamente qué se muestreó.

## Prerrequisitos (resolver ANTES de revisar)

1. **MCP de navegador conectado.** El MCP `pbrowseros`/BrowserOS **no estaba conectado** en la sesión que dejó este brief. Verifica con una `ToolSearch` (query: "browseros browser navigate screenshot") que existan herramientas `mcp__*browseros*__*` (navigate, screenshot, console, resize). Si no aparecen, conéctalo/instálalo primero (Claude Code → MCP settings) o pídele al usuario que lo habilite. Si no hay MCP de navegador disponible, alternativa: Playwright-MCP; si tampoco, hacer la revisión sobre el HTML de `dist/` + lectura de código (menos fiel — avísalo).
2. **Servidor dev corriendo.** En una terminal: `cd site && npm run dev` (Astro, normalmente `http://localhost:4321`). El hook `predev` corre `sync-data.mjs` y copia `data/` → `public/data/`, así el mapa puede hacer fetch de `/data/cead/*`. La capa de incidentes (`/data/incidents/current.json`) mostrará estado vacío (esperado — la pipeline de noticias no ha corrido en vivo).
3. (Opcional) Para ver pins de incidentes reales: setear `DEEPSEEK_API_KEY` y correr `python pipeline/scrape_news.py` una vez. No es necesario para la revisión de UX/lectura.

## Inventario de páginas a revisar

**Editoriales EN (10 — alta prioridad, son las "money pages"):**
`/` · `/is-chile-safe/` · `/is-santiago-safe/` · `/valparaiso-safety/` · `/vina-del-mar-safety/` · `/concepcion-safety/` · `/chile-crime-map/` · `/santiago-safety-map/` · `/safest-cities-in-chile/` · `/methodology/`

**Editoriales ES (10):**
`/es/` · `/es/mapa-delito-chile/` · `/es/delitos-por-comuna/` · `/es/delitos-por-region/` · `/es/comunas-mas-seguras-chile/` · `/es/mapa-seguridad-santiago/` · `/es/seguridad-valparaiso/` · `/es/seguridad-vina-del-mar/` · `/es/seguridad-concepcion/` · `/es/metodologia/`

**Mapa (island interactivo):** `/map/` · `/es/mapa/`

**Legales (EN+ES):** `/privacy-policy/` · `/terms/` · `/about/` · `/contact/` · `/es/politica-privacidad/` · `/es/terminos/` · `/es/acerca-de/` · `/es/contacto/`

**Programáticas (muestreo):** `commune/[slug]` (346×2) · `region/[slug]` (16×2) · crime-type (7×2). Confirmar slugs reales en `site/src/pages/` y `data/cead/meta/index.json`.

> Inventario completo de páginas y slugs LOCKED: `.planning/milestones/v1.0-REQUIREMENTS.md` (EDIT-01/02) y `site/src/pages/`.

## Checklist por dimensión (aplicar a cada página)

**A. Lectura / agrado (carga cognitiva)**
- ¿La columna de prosa respeta ~720px (no líneas eternas)? ¿Ritmo de párrafos, no muros de texto?
- ¿Un solo H1, jerarquía H2/H3 clara y escaneable? ¿El lector entiende la página en 5 segundos?
- ¿Hay redundancia entre callouts y prosa? ¿Jerga sin explicar? ¿Demasiados números juntos?
- ¿Los DataCallout/StatCard comunican UNA idea clara con su fuente (CEAD + año)?
- ¿Tono editorial sobrio (sin "peligroso/seguro" absoluto), claro y útil?

**B. Bugs / correctitud**
- Consola del navegador: 0 errores, warnings revisados.
- Enlaces internos (header, footer, cross-links, language switcher) resuelven; hreflang recíproco correcto (ojo `is-santiago-safe` y `es/delitos-por-region` se auto-referencian a propósito).
- Datos correctos: las tasas usan media nacional (`loadNationalAverage`), no la SUMA; ranking por tasa/100k; cifras coinciden con `data/cead/`.
- Mapa: choropleth carga 346 comunas; cambio de año/delito sin recargar; panel comuna completo; búsqueda; geolocalización; capa incidentes estado vacío sin error.
- Sin CLS (los AdSlot reservan altura; AdSense OFF → placeholder, nada de `adsbygoogle` visible).
- Responsive móvil ~375px: nada se desborda; mapa usable; menús/botones ≥44px.

**C. SEO / accesibilidad**
- `<title>`, meta description, canonical, hreflang, JSON-LD (FAQPage en las question-pages) presentes y válidos.
- Contraste de color (paleta teal `--primary #0f766e`), focus states visibles, alt text, aria en controles del mapa.

## Cómo arrancar (kickoff sugerido)

Recomendado: formalizar como **milestone v1.1** con esta revisión como primera fase, para mantener trazabilidad GSD:

```
/gsd:new-milestone
```
…y usar este brief como insumo (objetivo = revisión E2E + polish; requisitos = bugs 0, carga cognitiva reducida, lectura agradable, paridad ES/EN). La fase de discuss será corta porque casi todo está aquí.

Alternativa más ligera (sin milestone): ejecutar la revisión directamente con el MCP de navegador, escribir `.planning/REVIEW-E2E-FINDINGS.md` (hallazgos con severidad + recomendación + screenshot ref), y luego abrir una fase de fixes con `/gsd:plan-phase` sobre esos hallazgos.

En ambos casos: **primero verifica el MCP de navegador y levanta el dev server** (prerrequisitos), luego revisa según el inventario + checklist, una página a la vez.

## Estado conocido / pitfalls (no son hallazgos nuevos)

- Repo dentro de OneDrive: encadenar SIEMPRE build+validate en un comando (`cd site && npm run build && node scripts/validate/all.mjs`). El dev server no sufre esto.
- v1.0 está **code-complete pero NO desplegado**. Go-live pendiente (humano): ejecutar `DEPLOYMENT.md`. No bloquea la revisión local.
- Deuda técnica ya registrada (no re-reportar como bug nuevo, pero puede abordarse en v1.1): aserción CI de orden `FAMILY_KEYS` (duplicado pipeline ↔ `FiltersRow.tsx`), tipado `by_family` (`number[]` vs `float|None`), `AVAILABLE_YEARS` hardcodeado (2005–2025), flip de `nyquist_compliant` en VALIDATION.md fases 4–6.
- UAT visual/móvil de Phase 3 quedó **diferido** — esta revisión E2E es justamente el lugar para cerrarlo.
- Referencias clave: `.planning/RETROSPECTIVE.md` (lecciones v1.0), `.planning/milestones/v1.0-MILESTONE-AUDIT.md` (contratos cross-fase verificados), `.planning/PROJECT.md` (estado actual + constraints).

---
*Brief creado 2026-06-13 al cierre de v1.0, para una fase de revisión end-to-end en el siguiente contexto.*
