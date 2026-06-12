# Architecture Research

**Domain:** Static data-publishing platform with scheduled ingestion pipelines + programmatic SEO
**Researched:** 2026-06-12
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                               │
│                    (GitHub Actions cron jobs)                        │
├──────────────────────────────┬──────────────────────────────────────┤
│  CEAD Scraper (quarterly)    │  RSS News Pipeline (every 4-6 hrs)   │
│  Python / BeautifulSoup      │  Python / feedparser + DeepSeek v4   │
│  POST → HTML tables + JSON   │  classify → extract → dedup → geo    │
└──────────────┬───────────────┴──────────────┬───────────────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA STORE                                   │
│                  (JSON files in Git repo /data/)                     │
│                                                                      │
│  /data/cead/                      /data/incidents/                  │
│    comunas/{id}.json                current.json  (rolling 30 days) │
│    regions/{id}.json                archive/YYYY-MM.json            │
│    national.json                                                     │
│    meta/crime-types.json                                             │
│    meta/catalog.json                                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  (git commit by pipeline)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BUILD TRIGGER                                  │
│  Pipeline workflow uses GITHUB_TOKEN to commit →                    │
│  Cloudflare Pages Deploy Hook (POST to CF URL) called explicitly    │
│  OR: separate CF Pages project connected to repo, auto-builds       │
│  on push to main (scoped to /data/** and /site/** paths only)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BUILD LAYER                                    │
│                   Astro SSG (build-time)                             │
│                                                                      │
│  getStaticPaths() reads /data/ JSON                                 │
│  → generates ~750+ HTML pages (346 comunas × 2 langs + regions)    │
│  → embeds summary stats into HTML (SEO-critical)                    │
│  → client bundle: Leaflet React island (loads JSON at runtime)      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DELIVERY LAYER                                  │
│                    Cloudflare Pages CDN                              │
│                                                                      │
│  Static HTML pages (indexed by Google)                              │
│  /data/*.json served as static assets (client-side map loads)       │
│  Edge caching, global CDN, zero infrastructure cost                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| CEAD Scraper | POST to CEAD PHP endpoints, parse HTML/JSON, normalize to comuna/region/national JSON schema | Writes to /data/cead/ |
| RSS News Pipeline | Fetch RSS feeds, call DeepSeek v4 API, classify/extract/dedup incidents, write rolling JSON | Reads /data/incidents/current.json (for dedup), writes back |
| GitHub Actions (cron) | Orchestrates both pipelines on schedule; commits data files; triggers CF Pages build | Calls both pipelines, commits to repo, POSTs to CF deploy hook |
| /data/ JSON store | Version-controlled source of truth for all data; consumed by both build and client | Read by Astro at build time, served as static assets at runtime |
| Astro SSG | Generates all static HTML pages from JSON at build time; bundles React islands | Reads /data/ JSON files |
| Leaflet React island | Interactive map rendered client-side; loads JSON payloads via fetch | Fetches /data/cead/map-payload.json and /data/incidents/current.json |
| Cloudflare Pages | CDN delivery for all static assets including HTML, JS, and JSON data files | Serves to browsers |

---

## Recommended Project Structure

```
/                                   # repo root
├── .github/
│   └── workflows/
│       ├── cead-scraper.yml        # quarterly cron, runs pipeline/scrape_cead.py
│       ├── news-pipeline.yml       # every 4-6h cron, runs pipeline/scrape_news.py
│       └── deploy.yml              # (optional) explicit CF deploy hook trigger
├── pipeline/                       # Python ingestion code
│   ├── scrape_cead.py              # CEAD scraper entrypoint
│   ├── scrape_news.py              # RSS + DeepSeek pipeline entrypoint
│   ├── cead/
│   │   ├── client.py               # CEAD HTTP client (POST endpoints, rate limiting)
│   │   ├── parser.py               # HTML table parser (BeautifulSoup)
│   │   └── normalizer.py           # raw → normalized schema
│   ├── news/
│   │   ├── feeds.py                # RSS feed fetcher (feedparser)
│   │   ├── llm.py                  # DeepSeek v4 API wrapper
│   │   ├── classifier.py           # classify + extract + geolocate
│   │   └── deduplicator.py         # URL hash + semantic dedup
│   ├── shared/
│   │   ├── geo.py                  # comuna name → ID lookup table
│   │   └── schema.py               # Pydantic models for JSON output
│   └── requirements.txt
├── data/                           # generated JSON store (committed to repo)
│   ├── cead/
│   │   ├── national.json           # country-level aggregates
│   │   ├── comunas/
│   │   │   └── {comuna-id}.json    # one file per comuna
│   │   ├── regions/
│   │   │   └── {region-id}.json    # one file per region
│   │   ├── map-payload.json        # pre-aggregated choropleth payload
│   │   └── meta/
│   │       ├── catalog.json        # crime type taxonomy
│   │       └── index.json          # all comunas with IDs, region mapping
│   └── incidents/
│       ├── current.json            # rolling 30-day window (client loads this)
│       └── archive/
│           └── YYYY-MM.json        # monthly archives (not loaded client-side)
├── site/                           # Astro site
│   ├── astro.config.mjs
│   ├── package.json
│   ├── public/
│   │   └── data -> ../../data/     # symlink or CI copy: serve /data/ as static
│   └── src/
│       ├── pages/
│       │   ├── index.astro         # EN homepage
│       │   ├── es/
│       │   │   └── index.astro     # ES homepage
│       │   ├── comuna/
│       │   │   └── [slug].astro    # EN comuna pages (getStaticPaths reads index.json)
│       │   └── es/
│       │       └── comuna/
│       │           └── [slug].astro
│       ├── components/
│       │   ├── Map.tsx             # Leaflet React island (client:load)
│       │   ├── ChoroplethLayer.tsx
│       │   ├── IncidentPins.tsx
│       │   └── StatPanel.tsx
│       ├── layouts/
│       │   └── PageLayout.astro
│       └── lib/
│           ├── data.ts             # build-time JSON loading helpers
│           └── i18n.ts             # translation helpers
└── README.md
```

### Structure Rationale

- **/pipeline/:** Isolated Python package; no Node.js dependencies; can run and test independently of the site. Subdirectory per data source keeps scraper logic separate from shared utilities.
- **/data/:** Lives in the repo root (not inside /site/) so GitHub Actions can commit it without triggering a full npm install. The site references it via symlink or CI copy step.
- **/site/:** Self-contained Astro project; `npm install` and `npm run build` work inside this directory from Cloudflare Pages build settings.
- **Flat commune files:** One JSON file per comuna (see Data Schema section) rather than one giant file — Astro loads only what each page needs; client map loads the separate pre-aggregated payload.

---

## Data Schema Design

### Per-Comuna File: `/data/cead/comunas/{id}.json`

```json
{
  "id": "13101",
  "name": "Santiago",
  "region_id": "13",
  "population": 404495,
  "centroid": [-33.4378, -70.6505],
  "series": [
    {
      "year": 2024,
      "total_incidents": 45230,
      "rate_per_100k": 11181,
      "by_crime_family": {
        "robos": 18450,
        "lesiones": 8200,
        "hurtos": 7100,
        "drogas": 4300,
        "otros": 7180
      }
    }
  ],
  "national_rank": 3,
  "regional_rank": 1,
  "trend": "decreasing",
  "last_updated": "2026-06-01"
}
```

**Rationale:** Per-file layout means Astro's `getStaticPaths()` reads one file per page generation — avoids loading all 346 comunas into memory simultaneously. Per the Solita/Astro research, loading data per-page (not all-at-once) prevents memory issues at 750+ page builds.

### Map Payload: `/data/cead/map-payload.json`

Pre-aggregated, stripped-down file loaded by the Leaflet island client-side. Contains only what the choropleth needs — no time series, no breakdowns.

```json
{
  "generated": "2026-06-01T12:00:00Z",
  "year": 2024,
  "comunas": [
    {
      "id": "13101",
      "rate": 11181,
      "level": 5,
      "centroid": [-33.4378, -70.6505]
    }
  ]
}
```

**Size budget:** 346 comunas × ~80 bytes/entry = ~28 KB uncompressed; with Brotli compression on Cloudflare edge, ~6-8 KB. Well within a 100 KB budget. The GeoJSON boundary layer (~222 KB as referenced in PROJECT.md) is loaded separately and cached aggressively.

### Incidents File: `/data/incidents/current.json`

```json
{
  "generated": "2026-06-12T08:00:00Z",
  "retention_days": 30,
  "incidents": [
    {
      "id": "sha256-truncated-12chars",
      "title": "Asalto en Las Condes",
      "source": "emol.com",
      "source_url": "https://emol.com/...",
      "published": "2026-06-11T14:30:00Z",
      "crime_type": "robo",
      "crime_family": "robos",
      "comuna_id": "13114",
      "lat": -33.415,
      "lng": -70.601,
      "geo_confidence": "commune-centroid",
      "summary_es": "...",
      "summary_en": "..."
    }
  ]
}
```

**Retention policy:** Keep 30 rolling days in `current.json`. On each pipeline run, prune entries where `published` is older than 30 days. Monthly archives written to `/data/incidents/archive/YYYY-MM.json` before pruning. Rationale: 30 days matches user expectation of "recent incidents"; older data becomes noise without contextual investigation. Archives preserve provenance without bloating the client payload.

**Size budget:** Assume 20-50 new incidents/day × 30 days = 600-1500 entries × ~400 bytes = 240-600 KB uncompressed. Target: keep under 500 KB by being conservative with the 30-day window. If needed, cap at 1000 most recent entries.

---

## Data Flow

### CEAD Quarterly Ingestion

```
GitHub Actions (schedule: quarterly)
    │
    ▼
pipeline/scrape_cead.py
    │  POST get_estadisticas_delictuales.php (HTML tables)
    │  POST get_estadisticas_delictuales_mapa.php (JSON)
    │  POST ajax_2.php (catalogs)
    ▼
BeautifulSoup parse → Pydantic normalization
    │
    ▼
Write /data/cead/comunas/*.json  (346 files)
    /data/cead/regions/*.json    (16 files)
    /data/cead/national.json
    /data/cead/map-payload.json  (pre-aggregated)
    /data/cead/meta/catalog.json
    │
    ▼
git commit -m "data: CEAD quarterly update [skip ci]"  ← GITHUB_TOKEN (no loop)
    │
    ▼
POST to Cloudflare Pages Deploy Hook URL  ← explicit trigger
    │
    ▼
Cloudflare Pages build runs Astro SSG
```

### News RSS Ingestion (Every 4-6 Hours)

```
GitHub Actions (schedule: every 4-6h)
    │
    ▼
pipeline/scrape_news.py
    │  fetch RSS feeds (5+ sources)
    │  filter: only new URLs not in current.json (URL hash dedup)
    ▼
For each new item:
    DeepSeek v4 API call (batch where possible)
    → crime_type, crime_family, comuna_name, lat/lng, summaries
    │
    ▼
Merge into /data/incidents/current.json
    Prune entries > 30 days old
    Write archive if month boundary crossed
    │
    ▼
git commit -m "data: news update $(date -u +%Y-%m-%dT%H:%M)" [skip ci]
    │  (only commits if file actually changed — use git diff check)
    ▼
POST to Cloudflare Pages Deploy Hook  (only if commit happened)
```

### Build-Time Page Generation

```
Cloudflare Pages triggers Astro build
    │
    ▼
Astro getStaticPaths() in [slug].astro
    │  reads /data/cead/meta/index.json  (all 346 comuna IDs)
    │  generates path params for all comunas × 2 langs
    ▼
For each page:
    reads /data/cead/comunas/{id}.json  (one file, not all)
    embeds: name, rate, trend, rank, crime breakdown, 5-year series
    → pre-rendered HTML with full structured data (JSON-LD)
    → hreflang links to ES/EN counterpart
    │
    ▼
Leaflet React island bundled as JS chunk
    (data NOT embedded — loaded client-side via fetch)
    │
    ▼
Output: 750+ static HTML files + JS islands + /data/ JSON assets
    │
    ▼
Deployed to Cloudflare CDN edge
```

### Client-Side Map Loading

```
Browser loads /chile-crime-map/ (or any page with map)
    │
    ▼
React island hydrates (client:load)
    │  fetch("/data/cead/map-payload.json")      ~6-8 KB gzipped
    │  fetch("/data/cead/geo-data.json")          ~60 KB gzipped (GeoJSON boundaries)
    │  fetch("/data/incidents/current.json")      variable, <200 KB gzipped
    ▼
Leaflet renders choropleth + incident pins
User interactions (filter year, crime type) work against already-loaded JSON
```

---

## Infinite Loop Prevention

This is the central operational risk. The pattern:

**Pipeline commits data → GitHub detects push → triggers build workflow → build workflow shouldn't re-run the pipeline.**

### Recommended Solution: Two Separate Workflows + GITHUB_TOKEN

1. **Pipeline workflows** (`cead-scraper.yml`, `news-pipeline.yml`) run on `schedule` trigger only. They commit using the built-in `GITHUB_TOKEN`. GitHub's documented behavior: commits made with `GITHUB_TOKEN` do NOT trigger other workflow runs. This breaks the loop automatically.

2. **Do NOT use a `push`-triggered build workflow.** Instead, pipeline workflows explicitly POST to the Cloudflare Pages Deploy Hook at the end of a successful commit. Cloudflare Pages does the build.

3. **Conditional commit + deploy:** Only commit if data actually changed (`git diff --quiet` check). Only POST the deploy hook if the commit happened. This prevents unnecessary builds when CEAD returns no new data.

4. **Commit message `[skip ci]`** as defense-in-depth (some CI systems check this).

```yaml
# In cead-scraper.yml (simplified)
- name: Commit if changed
  id: commit
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/
    if git diff --staged --quiet; then
      echo "changed=false" >> $GITHUB_OUTPUT
    else
      git commit -m "data: CEAD update [skip ci]"
      git push
      echo "changed=true" >> $GITHUB_OUTPUT
    fi

- name: Trigger Cloudflare deploy
  if: steps.commit.outputs.changed == 'true'
  run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

---

## Architectural Patterns

### Pattern 1: Pre-aggregated Map Payload (Separate from Detail Files)

**What:** Maintain two data shapes — per-entity detail files (one per comuna) and a single pre-aggregated map payload containing only what the client map needs.
**When to use:** Always in this system. The map needs 346 rate values; the detail page needs full time series. Conflating them bloats the client payload with unused data.
**Trade-offs:** Requires the pipeline to write two outputs; adds ~10 lines of pipeline code. Worth it: map payload stays under 30 KB uncompressed vs potentially 2+ MB if full detail files were concatenated.

### Pattern 2: Build-Time Data Embedding for SEO, Client-Side Loading for Interactivity

**What:** At build time, Astro reads JSON and embeds structured data directly in HTML (rates, rankings, summaries, JSON-LD). The interactive map loads the same/similar data client-side via fetch for Leaflet rendering.
**When to use:** Whenever content must be indexed AND interactive. Never use client-only rendering for SEO-critical data.
**Trade-offs:** Slight duplication of data (in HTML and in JSON assets). Acceptable — it's the only way to satisfy both "Google reads it" and "Leaflet draws it."

### Pattern 3: Rolling Window + Monthly Archive for Incident Retention

**What:** `current.json` is a bounded rolling window (30 days). On each pipeline run, prune stale entries and write full months to `archive/YYYY-MM.json` before pruning.
**When to use:** Any live data feed with no backend. Prevents unbounded file growth while preserving historical provenance.
**Trade-offs:** Archives are not surfaced in the MVP UI. They exist for auditability and potential future "historical incidents" feature.

### Pattern 4: Pydantic Schema Validation at Pipeline Output

**What:** All JSON written by the pipeline is validated against Pydantic models before writing to disk. If validation fails, the pipeline exits non-zero — GitHub Actions marks the run as failed rather than writing corrupt data.
**When to use:** Always. Silent data corruption is harder to debug than a failed CI run.

---

## Anti-Patterns

### Anti-Pattern 1: Single Monolithic Data File

**What people do:** Write all 346 comunas into a single `all-comunas.json` file, load it in every `getStaticPaths()` call.
**Why it's wrong:** Astro loads it once per page in some configurations, causing memory pressure during 750+ page builds. A 2 MB file loaded 750 times = 1.5 GB memory churn. Also forces the client map to download unnecessary time series data.
**Do this instead:** Per-entity files for page generation; pre-aggregated payload for the map client.

### Anti-Pattern 2: Push-Triggered Rebuild Workflow

**What people do:** Add a `on: push` workflow that runs `npm run build` and deploys. Then the pipeline commits → push event → rebuild workflow → rebuild runs the pipeline again.
**Why it's wrong:** Creates an infinite loop (or at minimum causes unnecessary builds).
**Do this instead:** No push-triggered build workflow. Pipeline explicitly calls the Cloudflare Pages Deploy Hook. Cloudflare Pages git integration auto-build should be DISABLED or the pipeline commit should use `[skip ci]` + GITHUB_TOKEN.

### Anti-Pattern 3: Committing With a Personal Access Token (PAT)

**What people do:** Use a PAT to make the commit so it "looks like a real user" — which then DOES trigger push-based workflows, creating a loop.
**Why it's wrong:** PAT commits trigger push events; GITHUB_TOKEN commits do not.
**Do this instead:** Use `GITHUB_TOKEN` for all data commits from the pipeline.

### Anti-Pattern 4: Embedding Full Incident Data in Every Page

**What people do:** Pre-render all incidents into every page's HTML so there's "no client fetch."
**Why it's wrong:** 600+ incidents × 400 bytes = 240 KB of raw text added to every page's HTML. Ruins page weight, Time to First Byte, and LCP scores.
**Do this instead:** Embed only incident count and most recent 3-5 in static HTML (for SEO snippet). Load full incident list client-side for the map.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| CEAD PHP endpoints | Python POST requests (requests library), no auth, rate-limit with 2-3s delay between calls | Endpoints undocumented/unofficial — build defensive error handling, log full response on failure |
| RSS feeds (Emol, BioBioCl, etc.) | feedparser library, simple GET, no auth | Respect robots.txt; some feeds may require User-Agent header |
| DeepSeek v4 API | REST API, batch where possible (send multiple items per call to reduce cost) | Store API key in GitHub Actions secrets; validate JSON response schema before writing |
| Cloudflare Pages | Deploy Hook (HTTP POST) called by pipeline after successful data commit | Store hook URL as GitHub Actions secret; log response status |
| GitHub Actions | GITHUB_TOKEN for commits; schedule triggers for cron | GITHUB_TOKEN commits do NOT trigger push-based workflows — use this, not a PAT |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| pipeline → data store | Write JSON files to /data/ directory | Validate with Pydantic before writing; atomic writes (write temp then rename) to avoid partial reads |
| data store → Astro build | Astro reads files at build time via Node.js fs | Use relative paths from repo root; Cloudflare Pages build runs `npm run build` inside /site/ — configure base path or CI copy step |
| Astro build → client | Pre-aggregated JSON files served as static assets alongside HTML | JSON files live in /data/ and must be copied to or accessible from the Astro build output |
| client → data assets | Browser fetch() to /data/*.json | Served by Cloudflare CDN; set Cache-Control headers (map-payload: 1 hour, incidents: 30 min) |

---

## Build Order (Component Dependencies)

Build in this order — each step is a prerequisite for the next:

1. **Pipeline: CEAD Scraper** — Foundation. No CEAD data means no choropleth, no commune pages with real stats, no meaningful SEO content. Build and validate this first; mock data for site dev is acceptable but real data is needed for SEO validation.

2. **Data Schema + Pydantic Models** — Define the JSON contract before both pipeline and site consume it. Changes to schema after both sides are built are expensive.

3. **Astro Site: Static Shell + Programmatic Page Generator** — Once schema is defined and even one real CEAD file exists, build the page generation machinery. A single real `13101.json` (Santiago) is enough to develop all templates.

4. **Leaflet Map Island** — Depends on `map-payload.json` existing (from CEAD scraper) and GeoJSON boundary file. Develop against real data from the start.

5. **GitHub Actions Workflows** — Wire up the cron schedules, commit logic, and deploy hook call only after the pipeline and site work locally. Getting the loop-prevention right requires understanding both sides.

6. **Pipeline: RSS News + DeepSeek** — Can be built in parallel with steps 3-4 but depends on the shared schema (step 2) and the `incidents/current.json` format. The site can initially render with an empty incidents array.

7. **Cloudflare Pages Configuration** — Final step. Connect repo, set build command (`npm run build` inside /site/), configure deploy hook, disable auto-deploy on push (rely on explicit hook calls from pipeline).

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-10k users/month | Current architecture is ideal — static files + CDN handles this trivially |
| 10k-500k users/month | Cloudflare Pages still handles this; monitor CDN bandwidth; consider splitting incidents JSON if it grows beyond 1 MB |
| 500k+ users/month | Investigate Cloudflare Workers for on-demand regional aggregations; consider splitting data store to R2 bucket instead of repo if file count grows beyond 1000 |

**First bottleneck:** Not traffic — it's the GitHub Actions build time for 750+ pages. If Astro build exceeds Cloudflare Pages 25-minute build timeout, optimize by pre-computing all derived values in the pipeline (so Astro does only templating, no computation).

**Second bottleneck:** Git repo size if data grows unboundedly. Mitigation: archive old incident files outside repo (Cloudflare R2 or GitHub Releases assets) if /data/ exceeds 500 MB.

---

## Sources

- Astro build-time data loading patterns: https://dev.solita.fi/2024/12/02/building-static-websites-with-astro.html
- Cloudflare Pages Deploy Hooks: https://developers.cloudflare.com/pages/configuration/deploy-hooks/
- GitHub Actions GITHUB_TOKEN commit loop prevention: https://github.com/stefanzweifel/git-auto-commit-action/discussions/238
- GitHub community discussion on workflow loop prevention: https://github.com/orgs/community/discussions/74772
- MapLibre/Leaflet large GeoJSON optimization: https://maplibre.org/maplibre-gl-js/docs/guides/large-data/
- Astro official docs (why Astro, SSG): https://docs.astro.build/en/concepts/why-astro/

---
*Architecture research for: Chile Safety Map — static data publishing + programmatic SEO platform*
*Researched: 2026-06-12*
