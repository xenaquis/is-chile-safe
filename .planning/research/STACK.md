# Stack Research

**Domain:** Bilingual crime-data visualization + programmatic SEO static site (Chile)
**Researched:** 2026-06-12
**Confidence:** HIGH (all major decisions verified against official docs or npm registry)

---

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

**Use Astro's built-in i18n routing.** Do NOT reach for third-party libraries (astro-i18next, paraglide) — the built-in system handles this project's needs fully.

Configuration:
```js
// astro.config.mjs
export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    routing: {
      prefixDefaultLocale: false  // EN at /comune/providencia, ES at /es/comuna/providencia
    }
  }
})
```

- `prefixDefaultLocale: false` — English (primary SEO target) gets clean URLs (`/is-santiago-safe/`), Spanish gets `/es/` prefix. This maximizes EN Google ranking signal on root paths.
- Use `getRelativeLocaleUrl()` from `astro:i18n` for all internal links.
- hreflang tags: inject manually in `<head>` via layout component using `Astro.currentLocale` and canonical page path — Astro does not auto-inject hreflang.
- Sitemaps: use `@astrojs/sitemap` integration — it respects i18n routes automatically and generates per-locale sitemap entries.

### Programmatic Pages

Generate ~750 pages total (346 comunas × 2 langs + 16 regions × 2 + ~20 editorial × 2):

```
src/pages/
  [comuna].astro          → /providencia, /santiago, ...  (EN)
  es/[comuna].astro       → /es/providencia, ...          (ES)
  [region].astro
  es/[region].astro
  is-santiago-safe.astro
  es/seguridad-santiago.astro
```

Use `getStaticPaths()` in each dynamic route — reads from static JSON at build time.

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

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# For news classification: use deepseek-v4-flash (faster, cheaper)
# For complex geolocation extraction: use deepseek-v4-pro
response = client.chat.completions.create(
    model="deepseek-v4-flash",   # NOT deepseek-chat — deprecated 2026-07-24
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": news_text}
    ],
    temperature=0.1,   # deterministic for classification tasks
    max_tokens=200
)
```

**Model selection:**
- `deepseek-v4-flash` — classification, geolocation extraction, deduplication (cheaper, fast)
- `deepseek-v4-pro` — only if flash quality is insufficient for complex Chilean place-name resolution

**CRITICAL:** `deepseek-chat` and `deepseek-reasoner` are deprecated and will stop working 2026-07-24. Never commit these model names to code.

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

---

## Cloudflare Pages Limits — Critical Numbers

| Limit | Free | Paid (Workers Paid) |
|-------|------|---------------------|
| Files per deployment | 20,000 | 100,000 |
| Max individual file size | 25 MiB | 25 MiB |
| Builds per month | 500 | 5,000 |
| Build timeout | 20 min | 20 min |
| Concurrent builds | 1 | 5 |

**This project's file count:** ~750 HTML pages + JSON data files + assets ≈ 1,000-2,000 files total. **Comfortably within the free tier 20,000 limit.**

**Build time risk:** 346 + 32 + 40 = ~420 route files × 2 locales = ~840 pages to render. Astro 6 parallel rendering handles this in under 2 minutes. Monitor if CEAD data JSON grows very large.

**Rebuild trigger:** GitHub Actions commits updated JSON → Cloudflare Pages build webhook or `wrangler pages deploy` step triggers rebuild. Every commit to `main` rebuilds.

---

## GitHub Actions Cron Patterns

```yaml
# .github/workflows/scrape-news.yml
on:
  schedule:
    - cron: '0 */4 * * *'   # RSS every 4 hours (UTC)
  workflow_dispatch:          # manual trigger for testing

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python scripts/scrape_news.py
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
      - name: Commit if data changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "data: update news $(date -u +'%Y-%m-%d %H:%M UTC')"
          git push
```

```yaml
# .github/workflows/scrape-cead.yml
on:
  schedule:
    - cron: '0 6 1 */3 *'   # CEAD quarterly (1st of Jan/Apr/Jul/Oct at 06:00 UTC)
  workflow_dispatch:
```

**Key patterns:**
- `git diff --staged --quiet || git commit` — only commits if data actually changed. Prevents empty commits that spam rebuilds.
- Use `actions/checkout@v4` with `persist-credentials: true` (default) for the push to work.
- Store `DEEPSEEK_API_KEY` in repo Settings > Secrets > Actions.
- GitHub does not guarantee exact cron timing — up to 15-30 min delay under load is normal.

---

## GeoJSON Performance for 346 Comunas

The existing prototype uses `geo-data.js` at ~222 KB. This is fine for initial load.

**Optimization strategy (in order):**

1. **Pre-process with Mapshaper** (offline, one-time): Simplify tolerance ~0.0005° and reduce coordinate precision to 5 decimal places. Target: < 150 KB raw GeoJSON.
2. **Serve as static JSON** from `/public/data/comunas.json` — Astro copies it as-is; Cloudflare CDN caches it globally.
3. **Use native Leaflet, not `<GeoJSON>` component**: Call `L.geoJSON(data, { style, onEachFeature })` directly inside a React `useEffect` — this bypasses react-leaflet's per-feature re-render overhead.
4. **TopoJSON fallback**: If simplified GeoJSON is still > 300 KB, use `topojson-client` to convert TopoJSON at runtime (80% size reduction over GeoJSON without visual quality loss). Convert offline with `geo2topo` CLI.

At 346 polygons, canvas rendering is NOT needed — SVG (Leaflet default) renders this count without frame rate issues on any modern device.

---

## Installation

```bash
# Astro project bootstrap
npm create astro@latest -- --template minimal
npx astro add react
npx astro add sitemap

# Core frontend deps
npm install leaflet react-leaflet chroma-js

# Types
npm install -D @types/leaflet

# Astro check
npm install -D @astrojs/check typescript
```

```bash
# Python scraper deps (requirements.txt)
requests==2.32.*
beautifulsoup4==4.14.*
lxml==5.*
feedparser==6.0.*
openai==1.*
tenacity==8.*
python-dotenv==1.*
```

---

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

---

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

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| @astrojs/react 5.x | React 19.x, Astro 6.x | Do not mix with React 18 — peer dep requires 19 |
| react-leaflet 4.x | React 18/19, Leaflet 1.9.x | v4 is the current stable branch; v5 was not released as of research date |
| Astro 6.x | Node.js >= 20.x | Node 18 is EOL; pin to 20 LTS or 22 LTS in .nvmrc |
| feedparser 6.x | Python 3.6+ | No issues; install via pip |
| openai 1.x | Python 3.8+ | Works fine with Python 3.12 |

---

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

---

*Stack research for: Chile Safety Map (ischilesafe.com) — bilingual crime-data visualization + programmatic SEO*
*Researched: 2026-06-12*
