<!-- GSD:project-start source:PROJECT.md -->

## Project

**Chile Safety Map (ischilesafe.com)**

Plataforma bilingüe (ES/EN) que visualiza la seguridad territorial de Chile combinando dos capas: **cuantitativa** (estadísticas oficiales de incidencia delictiva del CEAD por comuna, región y país, mediante mapa coroplético, rankings y series temporales) y **cualitativa** (incidentes recientes extraídos de RSS de medios de prensa, clasificados y geolocalizados con DeepSeek v4, mostrados como pins en el mapa). Sirve a residentes, turistas, expats, estudiantes y personas evaluando dónde vivir, alojarse o viajar.

El sitio captura tráfico SEO mediante páginas programáticas bilingües (por comuna, región y tipo de delito) y páginas editoriales prioritarias ("Is Santiago safe", "comunas más seguras de Chile"). Monetización inicial: AdSense.

**Core Value:** Un mapa nacional interactivo con datos delictivos oficiales reales por comuna, servido en páginas estáticas bilingües que Google indexa — si el mapa con datos CEAD reales y las páginas SEO funcionan, el resto puede esperar.

### Constraints

- **Presupuesto**: Infraestructura ~$0 — Cloudflare Pages gratis, GitHub Actions gratis; único costo variable es API DeepSeek v4 (económica) para procesamiento de noticias
- **Tech stack**: Astro + islas React + Leaflet (frontend); Python (scrapers CEAD y RSS); JSON estático en repo como almacén de datos — sin servidor ni DB en MVP
- **Dependencias**: CEAD es fuente única cuanti — endpoints no oficiales pueden cambiar sin aviso; pipeline debe fallar con gracia y alertar
- **SEO**: Todas las páginas deben ser HTML estático pre-renderizado e indexable — nada de contenido crítico render-only en cliente
- **Cortesía de scraping**: delays entre requests a CEAD (servidor gubernamental) y respeto a robots/RSS de medios
- **Editorial/legal**: nunca calificar territorios como "peligrosos/seguros" en absoluto; siempre atribuir fuentes (CEAD, medio de prensa); incidentes de noticias citan y enlazan la fuente

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Astro | 6.4.x (latest stable) | Static site framework, programmatic page generation | Current major version (v6.4.6 as of June 2026). Pre-renders all pages to HTML — mandatory for SEO indexability. Native i18n routing built in since v4; islands architecture lets us isolate React/Leaflet to map components only. Do NOT use v5 — v6 is stable and current. |
| @astrojs/react | 5.0.x | React island integration | Official Astro integration; v5.0.7 published June 2026. Allows React components (map, charts) with `client:load` / `client:visible` directives. Server-renders by default, hydrates selectively. |
| React | 19.x | UI for interactive islands | Required peer dep of @astrojs/react v5. Only loaded in browser for map island — the rest of the site ships zero React JS. |
| Leaflet | 1.9.x | Choropleth map, pins | Mature, battle-tested. 346 comunas is ~350 polygons — well within Leaflet's performance envelope for canvas rendering. Lighter than Mapbox GL for this polygon count. |
| react-leaflet | 4.x | React wrapper for Leaflet | Use with caution (see Pitfalls). Pin to v4 for React 19 compat. Use native Leaflet `L.geoJSON()` layer directly (not `<GeoJSON>` component) to avoid per-hover re-render issue. |

### i18n Approach

- `prefixDefaultLocale: false` — English (primary SEO target) gets clean URLs (`/is-santiago-safe/`), Spanish gets `/es/` prefix. This maximizes EN Google ranking signal on root paths.
- Use `getRelativeLocaleUrl()` from `astro:i18n` for all internal links.
- hreflang tags: inject manually in `<head>` via layout component using `Astro.currentLocale` and canonical page path — Astro does not auto-inject hreflang.
- Sitemaps: use `@astrojs/sitemap` integration — it respects i18n routes automatically and generates per-locale sitemap entries.

### Programmatic Pages

### Python Scraper Stack

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| requests | 2.32.x | HTTP client for CEAD POST endpoints | Standard; handles sessions, timeouts, proxies. CEAD uses POST forms — requests handles this cleanly. |
| beautifulsoup4 | 4.14.x | Parse CEAD HTML table responses | `get_estadisticas_delictuales.php` returns HTML tables; bs4 + lxml parser is the fastest option. |
| lxml | 5.x | bs4 HTML parser backend | 5-10x faster than html.parser for large HTML; install alongside bs4. |
| feedparser | 6.0.x | RSS/Atom feed parsing | Handles all RSS variants (Emol, BioBio, T13, Cooperativa); robust against malformed feeds. |
| openai | 1.x | DeepSeek API client | DeepSeek's API is OpenAI-compatible; use `openai` SDK with `base_url="https://api.deepseek.com"` and `DEEPSEEK_API_KEY`. No DeepSeek-specific SDK needed. |
| tenacity | 8.x | Retry logic for API calls | Rate limiting and transient errors from CEAD + DeepSeek; exponential backoff without boilerplate. |
| python-dotenv | 1.x | Load DEEPSEEK_API_KEY in dev | Keep keys out of code; GitHub Actions uses repo secrets. |

### DeepSeek API Usage Pattern

# For news classification: use deepseek-v4-flash (faster, cheaper)

# For complex geolocation extraction: use deepseek-v4-pro

- `deepseek-v4-flash` — classification, geolocation extraction, deduplication (cheaper, fast)
- `deepseek-v4-pro` — only if flash quality is insufficient for complex Chilean place-name resolution

### Frontend Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @astrojs/sitemap | 3.x | Auto-generate sitemap.xml respecting i18n | Always — include from day 1 for SEO |
| chroma-js | 3.x | Color scale for choropleth | Generate 5-level incidence color scale (matches existing prototype palette). Use `chroma.scale(['#teal','#red']).classes(5)` |
| topojson-client | 3.x | Convert TopoJSON → GeoJSON at runtime | If GeoJSON > 500KB, pre-process to TopoJSON offline and decode in browser. See GeoJSON section below. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Node.js | 20 LTS or 22 LTS | Astro build runtime | v20 minimum required by Astro 6. Use `.nvmrc` to pin. |
| Python | 3.12+ | Scraper runtime | GitHub Actions ubuntu-latest ships 3.12. Use `pyproject.toml` or `requirements.txt`. |
| @astrojs/check | current | TypeScript checking for .astro files | Run in CI before deploy. |

## Cloudflare Pages Limits — Critical Numbers

| Limit | Free | Paid (Workers Paid) |
|-------|------|---------------------|
| Files per deployment | 20,000 | 100,000 |
| Max individual file size | 25 MiB | 25 MiB |
| Builds per month | 500 | 5,000 |
| Build timeout | 20 min | 20 min |
| Concurrent builds | 1 | 5 |

## GitHub Actions Cron Patterns

# .github/workflows/scrape-news.yml

# .github/workflows/scrape-cead.yml

- `git diff --staged --quiet || git commit` — only commits if data actually changed. Prevents empty commits that spam rebuilds.
- Use `actions/checkout@v4` with `persist-credentials: true` (default) for the push to work.
- Store `DEEPSEEK_API_KEY` in repo Settings > Secrets > Actions.
- GitHub does not guarantee exact cron timing — up to 15-30 min delay under load is normal.

## GeoJSON Performance for 346 Comunas

## Installation

# Astro project bootstrap

# Core frontend deps

# Types

# Astro check

# Python scraper deps (requirements.txt)

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Astro 6 | Next.js 15 | Next.js ISR adds complexity; App Router static export loses edge cases; Astro's island model ships less JS and is simpler for content sites |
| Astro 6 | Nuxt 3 / SvelteKit | Vue/Svelte components can't reuse the existing React prototype directly; Astro lets us port React components as-is |
| Leaflet | Mapbox GL JS | Mapbox requires API key + paid plan for traffic; Leaflet is fully open source. At 346 polygons, Leaflet performance is adequate. |
| Leaflet | MapLibre GL JS | Adds WebGL complexity; no benefit at this polygon count; harder to integrate existing react-leaflet prototype code |
| openai SDK → DeepSeek | httpx + raw requests | The openai SDK handles retries, streaming, token counting, and is battle-tested. DeepSeek's API is explicitly OpenAI-compatible. |
| Astro built-in i18n | astro-i18next | astro-i18next adds a dependency and indirection. Built-in routing is sufficient for two locales with static generation. |
| Astro built-in i18n | Paraglide + Astro | Paraglide's type-safe messages are overkill for a two-locale site where most content comes from data JSON, not UI strings. |
| Cloudflare Pages | Vercel | Vercel free tier has bandwidth limits and function invocation caps that would break with AdSense traffic spikes. Cloudflare Pages is truly free for static. |
| Static JSON in repo | Cloudflare KV / D1 | Adds backend complexity and cost; CEAD data changes quarterly, news daily — a JSON commit + rebuild is simpler and fully auditable via git history. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `deepseek-chat` / `deepseek-reasoner` model IDs | Deprecated, stop working 2026-07-24 | `deepseek-v4-flash` or `deepseek-v4-pro` |
| `<GeoJSON>` component from react-leaflet | Triggers re-render on every hover event; causes jank with 346 features | Native `L.geoJSON()` inside `useEffect` |
| `prefixDefaultLocale: true` | Forces `/en/` prefix on English URLs, hurting SEO for primary target audience | `prefixDefaultLocale: false` (default) |
| hash-routing SPAs (Vite + React alone) | Google cannot index hash-routed pages — the prototype's routing would fail SEO | Astro static pre-rendering |
| BeautifulSoup html.parser | 5-10x slower than lxml for CEAD HTML tables | bs4 + lxml backend |
| Scrapy | Overkill framework for 1 government endpoint + 5 RSS feeds; adds complexity | requests + feedparser |
| `client:load` on map island | Loads Leaflet JS on every page, including the 346 comunas landing pages that don't show the map | `client:only="react"` on map island; `client:visible` on optional components |

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| @astrojs/react 5.x | React 19.x, Astro 6.x | Do not mix with React 18 — peer dep requires 19 |
| react-leaflet 4.x | React 18/19, Leaflet 1.9.x | v4 is the current stable branch; v5 was not released as of research date |
| Astro 6.x | Node.js >= 20.x | Node 18 is EOL; pin to 20 LTS or 22 LTS in .nvmrc |
| feedparser 6.x | Python 3.6+ | No issues; install via pip |
| openai 1.x | Python 3.8+ | Works fine with Python 3.12 |

## Sources

- [Astro npm registry](https://www.npmjs.com/package/astro) — confirmed v6.4.6 latest stable June 2026
- [@astrojs/react npm](https://www.npmjs.com/package/@astrojs/react) — confirmed v5.0.7 June 2026
- [Astro i18n routing docs](https://docs.astro.build/en/guides/internationalization/) — prefixDefaultLocale, helper functions
- [Cloudflare Pages limits (official)](https://developers.cloudflare.com/pages/platform/limits/index.md) — 20K free / 100K paid, 25 MiB file, 500 builds/month
- [Cloudflare Pages file limit increase changelog](https://developers.cloudflare.com/changelog/post/2026-01-23-pages-file-limit-increase/) — 100K paid plan confirmed Jan 2026
- [DeepSeek API docs](https://api-docs.deepseek.com/) — model IDs, base URL, deprecation timeline
- [WaveSpeed blog: DeepSeek V4 Python](https://wavespeed.ai/blog/posts/blog-deepseek-v4-api-python/) — confirmed openai SDK pattern
- [react-leaflet choropleth performance analysis](https://tmsvr.com/react-leaflet-map-performance-issues/) — re-render issue documented
- [2025 vector rendering performance study](https://agris.fao.org/search/fr/records/68caacf6f61e5b80b5e8f917) — Leaflet adequate below 10K features
- [GitHub Actions cron patterns](https://dev.to/0012303/how-i-run-web-scrapers-for-free-using-github-actions-complete-setup-2e30) — commit-only-if-changed pattern

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
