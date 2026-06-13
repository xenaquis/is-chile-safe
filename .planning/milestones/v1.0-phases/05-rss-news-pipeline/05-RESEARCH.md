# Phase 5: RSS News Pipeline — Research

**Researched:** 2026-06-13
**Domain:** Python RSS ingestion · DeepSeek v4-flash classification · commune centroid geometry · JSON store
**Confidence:** HIGH (all feed URLs live-verified; TopoJSON property key confirmed; DeepSeek JSON mode confirmed via official docs; existing pipeline patterns read directly from source)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** LLM input = headline + RSS `<description>`/summary only — no full-article scrape.
- **D-02:** Keyword pre-filter applied before classification; clearly non-crime items skipped without API call.
- **D-03:** Seen-URL ledger (`data/incidents/seen.json` or `pipeline/cache/`) — already-processed URLs skipped.
- **D-04:** Polite fetch: custom User-Agent, ~10s timeout, tenacity retry, per-feed try/except.
- **D-05:** Model = `deepseek-v4-flash`. openai SDK, `base_url="https://api.deepseek.com"`, key from `DEEPSEEK_API_KEY`.
- **D-06:** Strict JSON output, Pydantic v2-validated: `{commune_cut, family, title_es, title_en, summary, confidence}`. Temperature 0.0.
- **D-07:** Closed list of 346 canonical CUT codes embedded in prompt. Incident rejected if no exact CUT match OR confidence below threshold.
- **D-08:** Pin coordinates are deterministic commune centroids precomputed from Phase-3 GADM-L3 TopoJSON. LLM never emits lat/lng.
- **D-09:** Crime type maps to 7 CEAD families: `vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades`.
- **D-10:** Cross-source dedup is heuristic: canonical-URL match + normalized-title similarity within commune + date window.
- **D-11:** Incident `id` = deterministic hash of source URL.
- **D-12:** Retention: each run drops incidents older than 30 days from `current.json`; appends aged-out incidents to `archive/YYYY-MM.json`.
- **D-13:** Output path = `data/incidents/current.json` + `data/incidents/archive/YYYY-MM.json`.
- **D-14:** Module layout: `pipeline/news/` + `pipeline/scrape_news.py` orchestrator, mirroring `pipeline/scrape_cead.py`.
- **D-15:** Pydantic v2 validation gate; atomic write; batch rejected / last-good preserved on schema violation.
- **D-16:** 50-incident manual audit via `pipeline/scripts/audit_incidents.py` is human-UAT gate.
- **D-17:** Per-run classification cap; `DEEPSEEK_API_KEY` from env/dotenv/repo secret.

### Claude's Discretion

- Exact keyword pre-filter list and confidence threshold value.
- Exact RSS feed endpoint URLs (confirm live — this research does that).
- Centroid computation method (polygon centroid vs label-point) from the TopoJSON.
- Title-similarity algorithm/threshold for dedup.
- Whether seen-ledger lives in `data/` (committed) or `pipeline/cache/` (gitignored).

### Deferred Ideas (OUT OF SCOPE)

- GitHub Actions cron scheduling + Cloudflare deploy hook — Phase 6.
- Additional/secondary feeds (T13, 24Horas, Meganoticias, SoyChile) — only if 3 confirmed feeds underperform.
- Incident detail pages / per-incident SEO pages — v2.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NEWS-01 | Pipeline ingests RSS from confirmed sources (BioBíoChile, Cooperativa Policial, La Tercera Nacional) with per-feed fallback | Feed URLs live-verified (section below). feedparser 6.x handles all RSS 2.0 variants; per-feed try/except pattern mirrors cead/client.py |
| NEWS-02 | DeepSeek v4-flash classifies each policial item: crime type, commune against closed 346-CUT list (temp 0.0), geoloc, summary | `json_object` response_format confirmed via DeepSeek official docs; closed-list prompt strategy documented; centroid lookup from TopoJSON removes LLM coordinate emission |
| NEWS-03 | Cross-source dedup before publish | difflib.SequenceMatcher (stdlib, no new dep) sufficient; threshold and normalization strategy documented |
| NEWS-04 | `current.json` maintains 30-day rolling window; archive YYYY-MM.json | Merge-and-partition pattern using existing `atomic_write_json`; idempotent via D-11 URL-hash ID |
| NEWS-05 | Each incident cites and links its source with date | Outlet + url + date fields are non-nullable in Pydantic IncidentRecord model; schema gate enforces presence |
</phase_requirements>

---

## Summary

Phase 5 builds the Python pipeline that transforms Chilean press RSS feeds into `data/incidents/current.json`, which the Phase-3 map island's `IncidentPinLayer` already consumes. All three confirmed feed sources are live and parseable as of 2026-06-13. The DeepSeek v4-flash JSON mode uses `response_format={'type': 'json_object'}` (the only supported type per official docs — `json_schema` is NOT listed). Commune centroids are computed once from `data/cead/geo/communes.topo.json` (property key `id`, 346 features) using the Shoelace formula on polygon rings — shapely is not required. Deduplication uses `difflib.SequenceMatcher` (stdlib) over title pairs normalized to ASCII+lowercase within the same commune+date bucket. The pipeline reuses `atomic_write_json`, the Pydantic v2 schema gate pattern from `shared/schema.py`, and the tenacity retry decorator from `cead/client.py` with no structural novelty.

**Primary recommendation:** Mirror `scrape_cead.py`'s orchestrator + per-module layout exactly. The only genuinely new engineering surface is the DeepSeek classifier prompt (closed-list CUT injection) and the centroid precomputation script.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| RSS fetch + keyword pre-filter | Pipeline (Python) | — | Server-side I/O; not a browser concern |
| DeepSeek classification | Pipeline (Python) | — | API call with secret key — never in browser |
| Centroid precomputation | Pipeline (Python, one-shot script) | — | Offline transform; produces a static JSON lookup |
| Seen-ledger read/write | Pipeline (Python) | — | Persistent state; needs atomic update |
| current.json / archive write | Pipeline (Python) | — | Atomic file output; synced to public/ by existing sync-data.mjs |
| Pin rendering | Browser (Leaflet, already shipped) | — | Phase 3 IncidentPinLayer — not touched in Phase 5 |

---

## RSS Feed Endpoints (NEWS-01) — Live-Verified 2026-06-13

### Confirmed Live Feeds

| Source | Feed URL | Type | Items/fetch | Description field | pubDate format |
|--------|----------|------|-------------|------------------|----------------|
| **BioBíoChile** | `https://www.biobiochile.cl/static/feed-rss` | General (needs keyword filter) | ~20 | ~1054 chars, HTML in `<description>` | RFC 2822 (`+0000`) |
| **Cooperativa Policial** | `https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3_158__1.xml` | Crime-specific | ~15 | ~180–1800 chars plain text | RFC 2822 (`-0400`) |
| **La Tercera Nacional** | `https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml` | General (needs keyword filter) | ~41 | Full `<description>` CDATA + `<content:encoded>` | RFC 2822 (`+0000`) |

**[VERIFIED: live HTTP 200 probe 2026-06-13]**

### Feed Structure Notes

**BioBíoChile:**
- `<guid isPermaLink="false">` contains a WordPress post ID URL (e.g. `https://www.biobiochile.cl/?p=6858688`) — NOT the canonical article URL. Use `<link>` for the seen-ledger and the published `url` field.
- `<description>` is HTML-encoded, ~1000 chars. Strip HTML tags before feeding to LLM.
- Multiple `<category>` tags per item — can be inspected for pre-filter but keyword match on title+description is simpler.
- General feed; keyword pre-filter required to isolate crime items.

**Cooperativa Policial (`rss_3_158__1.xml`):**
- Crime-specific feed — every item is policial. No pre-filter needed, though D-02 keyword gate still applies as sanity check.
- `<description>` is plain text (no HTML), 180–1800 chars. High quality signal for the LLM.
- `<guid>` is the canonical article URL (permalink). Use `<guid>` directly for seen-ledger and `url` field.
- pubDate offset is -0400 (Santiago local time) — normalize to UTC on ingest.

**La Tercera Nacional:**
- General feed. ~41 items including politics, crime, disasters. Keyword filter required.
- `<description>` is CDATA plain text, quality varies. `<content:encoded>` contains full article HTML — do NOT use (D-01: headline + description only).
- `<guid isPermaLink="true">` IS the canonical article URL. Use `<guid>` for seen-ledger and `url` field.
- `<dc:creator>` available for author attribution (not needed in output schema).
- Encoding anomaly: content sometimes appears as latin-1 despite UTF-8 declaration. feedparser handles this transparently.

### Cooperativa "Seguridad ciudadana" Secondary Feed

`https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3_174__1.xml` — additional crime-adjacent feed (citizen security). Treat as optional/future. Not in Phase 5 scope (deferred).

### Feed URL Derivation (Cooperativa)

Cooperativa's RSS system follows the pattern `/noticias/site/tax/port/all/rss_{section}_{category}_{page}.xml`. The policial feed is `rss_3_158__1.xml`. If this URL stops working, the RSS customization page is `https://www.cooperativa.cl/noticias/stat/rss/rss.html`. **[VERIFIED: live probe 2026-06-13]**

---

## Standard Stack

### Core (all already in `pipeline/requirements.txt` except feedparser)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| feedparser | 6.0.x | Parse RSS 2.0/Atom from all three feeds | **NEW — add to requirements.txt** |
| openai | 1.x | DeepSeek API client (base_url override) | Already present (CLAUDE.md) |
| tenacity | 9.1.4 | Retry decorator for feed fetch + DeepSeek calls | Already in requirements.txt |
| python-dotenv | 1.2.2 | Load DEEPSEEK_API_KEY in dev | Already in requirements.txt |
| pydantic | 2.13.4 | IncidentRecord schema gate | Already in requirements.txt |
| requests | 2.34.2 | Used by existing pipeline; feedparser handles RSS HTTP internally | Already in requirements.txt |
| difflib | stdlib | Title similarity for dedup (SequenceMatcher) | stdlib — no install |
| hashlib | stdlib | URL hash for incident `id` (D-11) | stdlib — no install |
| json | stdlib | seen-ledger read/write | stdlib — no install |

**feedparser is NOT in requirements.txt yet — it must be added.**

CLAUDE.md lists feedparser 6.0.x as the standard RSS library. **[CITED: CLAUDE.md project instructions]**

### Why NOT rapidfuzz for dedup

`rapidfuzz` is installed in the local dev environment but is NOT in `pipeline/requirements.txt` and is an unnecessary C extension dependency for this use case. `difflib.SequenceMatcher` from the Python stdlib is sufficient for comparing ~20–60 deduplicated titles per run. The per-run item count is small enough that stdlib performance is indistinguishable from rapidfuzz. Keeping dedup in pure stdlib avoids a new dependency and potential CI issues. **[ASSUMED: performance claim; not benchmarked. If run batch exceeds ~500 items, consider rapidfuzz.]**

### Why NOT shapely for centroids

`shapely` is not installed and would be a heavy C extension dependency for a one-time computation. The ring centroid for a polygon can be computed with 15 lines of pure Python using the Shoelace formula (see Code Examples). The TopoJSON geometry is already decoded to GeoJSON-style coordinates by `topojson-client` in the browser; for Python, we read the TopoJSON arc arrays directly. Given 346 polygons computed once and stored as a static JSON lookup, performance is irrelevant. **[ASSUMED: pure-Python centroid accuracy is sufficient for commune-level pin placement; not an exact centroid but within polygon bounds for all convex/near-convex communes.]**

### Installation (additions only)

```bash
# In pipeline/ directory
pip install feedparser==6.0.11
# Then update requirements.txt:
# feedparser==6.0.11
```

---

## Package Legitimacy Audit

| Package | Registry | Notes | slopcheck | Disposition |
|---------|----------|-------|-----------|-------------|
| feedparser | PyPI | Established library, ~10+ years, thousands of dependents | Not run (slopcheck unavailable on this machine) | Approved — CITED in CLAUDE.md project instructions as standard RSS library |

*slopcheck was unavailable at research time. feedparser is cited in CLAUDE.md (project instructions), which is an authoritative local source for this project. No other new packages are introduced.*

---

## Architecture Patterns

### System Architecture Diagram

```
[GitHub Actions cron / manual run]
        │
        ▼
scrape_news.py (orchestrator)
        │
        ├─► pipeline/news/feeds.py
        │     feedparser.parse(url) per feed
        │     per-feed try/except → skip + log on failure
        │     keyword pre-filter (D-02)
        │     seen-ledger dedup (D-03)
        │         └─► data/incidents/seen.json (or pipeline/cache/seen.json)
        │
        ├─► pipeline/news/classifier.py
        │     openai.Client(base_url=deepseek, key=env)
        │     chat.completions.create(model=deepseek-v4-flash, temp=0.0,
        │       response_format={type:json_object})
        │     → {commune_cut, family, title_es, title_en, summary, confidence}
        │     Pydantic ClassifierOutput.model_validate()
        │     reject if no CUT match or confidence < threshold
        │         │
        │         ├─► pipeline/news/centroids.py (lookup only)
        │         │     CUT → (lat, lng) from precomputed centroid map
        │         │     data/incidents/centroids.json (generated by scripts/build_centroids.py)
        │         │
        │         └─► IncidentRecord (Pydantic)
        │               id = sha256(url)[:16]
        │               cut, lat, lng, title_es, title_en, date, outlet, url, family
        │
        ├─► pipeline/news/dedup.py
        │     canonical-URL dedup (exact match)
        │     title similarity within commune+date bucket
        │     (difflib.SequenceMatcher, threshold ~0.85)
        │
        └─► pipeline/news/store.py
              load data/incidents/current.json (or [] if absent)
              merge new incidents (D-11 id = dedup key)
              partition: 30-day window → current; older → archive/YYYY-MM.json
              atomic_write_json(current.json)
              atomic_write_json(archive/YYYY-MM.json)  [append-merge idempotently]
              update seen-ledger
```

### Recommended Project Structure

```
pipeline/
├── news/
│   ├── __init__.py
│   ├── feeds.py          # feedparser fetch + keyword pre-filter + seen-ledger
│   ├── classifier.py     # DeepSeek v4-flash JSON classification
│   ├── centroids.py      # CUT → (lat, lng) lookup from precomputed map
│   ├── dedup.py          # cross-source deduplication
│   └── store.py          # rolling window + archive merge + atomic write
├── scripts/
│   ├── build_centroids.py  # one-shot: TopoJSON → data/incidents/centroids.json
│   └── audit_incidents.py  # D-16: dump 50 random incidents for human spot-check
├── tests/
│   ├── conftest.py       # extend existing fixtures
│   ├── fixtures/
│   │   ├── feed_biobio_sample.xml    # 5-item RSS sample
│   │   ├── feed_cooperativa_sample.xml
│   │   └── feed_latercera_sample.xml
│   ├── test_feeds.py
│   ├── test_classifier.py
│   ├── test_dedup.py
│   ├── test_store.py
│   └── test_centroids.py
├── scrape_news.py        # orchestrator (mirrors scrape_cead.py)
└── requirements.txt      # add feedparser==6.0.11
data/incidents/
├── current.json          # rolling 30-day window (Phase-3 contract)
├── seen.json             # seen-URL ledger (committed; survives redeploy)
├── centroids.json        # CUT → {lat, lng} (generated once by build_centroids.py)
└── archive/
    └── YYYY-MM.json      # monthly archives
```

---

## DeepSeek Classification (NEWS-02) — Confirmed Pattern

### JSON Mode

DeepSeek API supports `response_format={'type': 'json_object'}` only. The `json_schema` type is **not documented** for DeepSeek — do not use it. **[VERIFIED: api-docs.deepseek.com/guides/json_mode]**

Requirements per official docs:
1. The prompt (system or user) MUST contain the word "json".
2. Include an example of the desired JSON structure in the prompt.
3. Set `max_tokens` high enough to avoid truncated JSON (recommend 512 for this schema).
4. The API "may occasionally return empty content" — wrap `json.loads()` in try/except with retry.

### CUT List Embedding Strategy

346 CUT codes × ~5 digits each + comma = ~2000 chars (~500 tokens). This fits comfortably within the context window and is cheaper than any alternative. Embed as a newline-separated list in the system prompt. Do NOT send commune names in the CUT list — names add tokens and introduce confusion (accent variations). The model maps the news text to CUT numerically.

A compact prompt approach embeds just the code strings:

```
VALID_CUTS = [2101, 2102, ..., 13101, ...]  # 346 values
```

The user message contains: `HEADLINE: {title}\nSUMMARY: {description_stripped}`

### Output Schema (D-06)

```json
{
  "commune_cut": "13101",
  "family": "propiedad",
  "title_es": "...",
  "title_en": "...",
  "summary": "...",
  "confidence": 0.87
}
```

`confidence` is a float 0.0–1.0. Recommended rejection threshold: **0.6** (Claude's discretion). Items with confidence < 0.6 are logged but not committed. Items where `commune_cut` is not in the 346-CUT set are always rejected regardless of confidence.

**FAMILY_KEYS** from `pipeline/shared/schema.py` are the only valid `family` values:
`vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades`

Include this list verbatim in the system prompt as the enum constraint.

---

## Commune Centroids (D-08) — Confirmed Approach

### TopoJSON File

**Path:** `data/cead/geo/communes.topo.json`  
**Also at:** `site/public/data/cead/geo/communes.topo.json` (synced copy)

**[VERIFIED: direct Python probe 2026-06-13]**

- Object key: `communes-rekeyed`
- Feature count: 346
- Property keys per feature: `['id', 'name']`
- `id` is the CUT code string (e.g. `'2101'`)

### Centroid Computation (build_centroids.py)

The TopoJSON arcs must be decoded before polygon access. The simplest approach is to decode TopoJSON to GeoJSON using the `topojson` Python library OR by using the `topojson-client` JS approach. Since we want pure Python and are avoiding new heavy deps, use the `topojson` Python package (a lightweight pure-Python implementation). **[ASSUMED: verify topojson PyPI package legitimacy before adding to requirements.txt]**

**Alternative (avoids new dep entirely):** Read the GeoJSON variant if available. The site already has `communes.topo.json`; run `node -e "..."` during the build_centroids one-shot script to decode TopoJSON to GeoJSON using the existing `topojson-client` npm package (already installed in `site/node_modules/`).

**Recommended approach** (Claude's discretion): Use Node.js one-shot decode since `topojson-client` is already present:

```bash
# scripts/build_centroids.py calls this internally:
node -e "
const topo = require('./site/node_modules/topojson-client');
const fs = require('fs');
const t = JSON.parse(fs.readFileSync('data/cead/geo/communes.topo.json','utf8'));
const geo = topo.feature(t, t.objects['communes-rekeyed']);
fs.writeFileSync('/tmp/communes_geo.json', JSON.stringify(geo));
"
```

Then Python computes centroids from the GeoJSON FeatureCollection using the Shoelace formula (ring centroid). This requires zero new Python dependencies.

**Fallback (pure-Python, slightly less accurate):** Use the bounding-box center: `lat = (minLat + maxLat) / 2`, `lng = (minLng + maxLng) / 2`. Sufficient for commune-level pin placement where exact centroid doesn't matter.

### Shoelace Centroid (Pure Python, no deps)

```python
def ring_centroid(coords: list[list[float]]) -> tuple[float, float]:
    """Compute centroid of a polygon ring using the Shoelace formula."""
    area = 0.0
    cx = cy = 0.0
    n = len(coords)
    for i in range(n):
        x0, y0 = coords[i][0], coords[i][1]
        x1, y1 = coords[(i + 1) % n][0], coords[(i + 1) % n][1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area /= 2.0
    if abs(area) < 1e-10:
        # Degenerate — fall back to first coordinate
        return coords[0][1], coords[0][0]
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return cy, cx  # (lat, lng) — GeoJSON is [lng, lat]
```

For MultiPolygon features, use the ring of the largest sub-polygon (by area) as the centroid source.

**Output format:** `data/incidents/centroids.json`
```json
{"13101": {"lat": -33.456, "lng": -70.654}, "2101": {...}, ...}
```

---

## Output Schema Fidelity (D-15)

The Pydantic `IncidentRecord` model MUST serialize to exactly match the `Incident` TypeScript interface in `site/src/components/map/IncidentPinLayer.ts`:

```python
# pipeline/news/classifier.py (or shared/schema.py extension)
from pydantic import BaseModel, field_validator
import hashlib, datetime

VALID_FAMILIES = {"vida","robos_violentos","vif","drogas","armas","propiedad","incivilidades"}
VALID_CUTS: set[str]  # loaded from pipeline/cead/catalog.py at startup

class IncidentRecord(BaseModel):
    id: str          # sha256(url)[:16]
    cut: str         # validated against VALID_CUTS
    lat: float
    lng: float
    title_es: str
    title_en: str
    date: str        # YYYY-MM-DD
    outlet: str
    url: str
    family: str      # validated against VALID_FAMILIES

class IncidentsFile(BaseModel):
    generated: str   # ISO-8601 timestamp
    window_days: int # = 30
    incidents: list[IncidentRecord]
```

**IncidentsFile wraps current.json** — validate the entire file with `IncidentsFile.model_validate(data)` before atomic write. This matches the `IncidentsFile` interface in IncidentPinLayer.ts exactly.

---

## Seen-Ledger Placement (Claude's Discretion)

**Recommendation: `data/incidents/seen.json` (committed to repo)**

Rationale: `pipeline/cache/` is gitignored (per cead/client.py `CACHE_DIR`). If the seen-ledger is gitignored, every GitHub Actions run starts with an empty ledger and re-classifies all articles, blowing through the classification cap (D-17) and generating duplicate incidents on every run. The ledger MUST persist across CI runs. Since the data/ directory is committed and already contains `incidents/current.json`, committing `seen.json` alongside it is consistent and requires zero extra infrastructure.

Format: `{"https://article.url": "2026-06-13"}` — URL → date first seen. On each run, prune entries older than 60 days to prevent unbounded growth.

---

## Deduplication (NEWS-03)

### Canonical-URL Dedup

Check `url` (normalized: strip query params tracking tokens like `utm_*`) against the seen-ledger. This handles same-article-same-URL case.

### Title Similarity Dedup

Within a bucket of `(commune_cut, date)`, compare title pairs using `difflib.SequenceMatcher.ratio()`. Threshold recommendation: **0.82** (catches rewrites like "Robo en Santiago deja un herido" vs "Robo en Santiago deja herido a hombre", rejects false positives between different incidents in the same commune).

**Normalization before comparison:**
1. Lowercase
2. Normalize Unicode to ASCII (remove accents): `unicodedata.normalize('NFD', s).encode('ascii', 'errors='ignore').decode()`
3. Strip punctuation
4. Collapse whitespace

```python
import difflib, unicodedata, re

def normalize_title(t: str) -> str:
    t = unicodedata.normalize('NFD', t.lower()).encode('ascii', errors='ignore').decode()
    t = re.sub(r'[^\w\s]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def are_duplicates(t1: str, t2: str, threshold: float = 0.82) -> bool:
    return difflib.SequenceMatcher(None, normalize_title(t1), normalize_title(t2)).ratio() >= threshold
```

`difflib` is stdlib — no new dependency. **[VERIFIED: stdlib availability confirmed 2026-06-13]**

---

## Rolling Window + Archive (NEWS-04)

### Merge Algorithm (idempotent)

```
1. Load data/incidents/current.json → existing: list[Incident] (or [] if absent)
2. Deduplicate new incidents against existing by id (D-11 hash)
3. Merge: combined = existing + new_unique
4. now = datetime.utcnow().date()
5. cutoff = now - timedelta(days=30)
6. current = [i for i in combined if date.fromisoformat(i['date']) >= cutoff]
7. aged_out = [i for i in combined if date.fromisoformat(i['date']) < cutoff]
8. For aged_out grouped by YYYY-MM:
   a. Load data/incidents/archive/YYYY-MM.json (or [])
   b. Merge (dedup by id)
   c. atomic_write_json(archive/YYYY-MM.json)
9. atomic_write_json(current.json, {generated, window_days:30, incidents:current})
```

The use of `id = sha256(url)[:16]` (D-11) makes this idempotent: re-running with the same articles produces the same ids and the merge step deduplicates them.

**`atomic_write_json` signature** (from `pipeline/shared/atomic_write.py`):
```python
def atomic_write_json(path: pathlib.Path, data: dict | list, compact: bool = False) -> None
```
Reuse directly. No changes needed.

---

## Keyword Pre-Filter (D-02) — Recommended List

**Claude's discretion.** Recommended initial list (tune during implementation):

```python
CRIME_KEYWORDS = {
    # Violent crime
    "homicidio","asesinato","femicidio","balacera","tiroteo","disparo",
    "herido a bala","matar","muerto","fallecido",
    # Property crime
    "robo","asalto","hurto","portonazo","encerronas","carjacking","encerronas",
    "receptacion","receptación",
    # Drugs / weapons
    "narco","droga","cocaine","cocaina","cocaína","marihuana","fentanilo",
    "armas","tráfico","trafico",
    # Violence / crime terms
    "delito","delincuente","imputado","detenido","detenidos",
    "carabinero","pdi","investigaciones","fiscalia","fiscalía",
    "formalizacion","formalización","condena","prisión","prision",
    # Crime gangs
    "tren de aragua","pandilla","banda criminal",
    "crimen organizado","narcocorridos",
    # Generic crime
    "victima","víctima","agresor","portonazo",
    "encubrimiento","receptación"
}
```

Match on `(title + " " + description_text).lower()`. Any keyword hit → send to classifier. No hit → skip (D-02). Cooperativa Policial items pass even without keyword match (feed is crime-specific) — but apply filter anyway as sanity check.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSS parsing | Custom XML parser / requests+BeautifulSoup | feedparser 6.x | Handles malformed XML, encoding detection, date normalization across all RSS variants; explicitly listed in CLAUDE.md |
| HTTP retry on feed fetch | Custom retry loop | tenacity (already installed) | Same decorator pattern as cead/client.py — `retry_if_exception_type((requests.Timeout, requests.ConnectionError))` |
| Atomic file write | open() + write() | `atomic_write_json` from `pipeline/shared/atomic_write.py` | Already handles .tmp + os.replace; Windows + POSIX safe |
| Pydantic schema gate | Manual dict key checks | `IncidentsFile.model_validate()` | All-or-nothing reject pattern from Phase 1 |
| DeepSeek client setup | httpx + raw JSON | openai SDK with base_url override | Handles retries, token counting, auth header; pattern in CLAUDE.md |

---

## Common Pitfalls

### Pitfall 1: feedparser vs requests for RSS fetch
**What goes wrong:** Using `requests.get(url)` + BeautifulSoup to parse RSS — broken by encoding issues, malformed XML, gzip responses.
**Why it happens:** Devs assume RSS is just XML over HTTP.
**How to avoid:** Always use `feedparser.parse(url)` — it handles all of this transparently, including gzip, charset detection, and partial-feed XML errors.
**Warning signs:** UnicodeDecodeError, xml.etree.ElementTree errors on live feeds.

### Pitfall 2: Using `guid` vs `link` for the seen-ledger URL
**What goes wrong:** BioBíoChile's `<guid>` is a non-permalink WordPress post ID URL (`?p=12345`), not the canonical article URL. Storing the guid causes missed dedup when the same article appears with a different guid.
**How to avoid:** For BioBíoChile, use `entry.link` (feedparser attribute). For Cooperativa and La Tercera, `entry.id` (the guid) IS the canonical URL. Normalize per-feed.
**Detection:** Inspect first 3 items of each feed; check if `entry.id` starts with `?p=`.

### Pitfall 3: LLM returning a CUT code outside the 346-item list
**What goes wrong:** DeepSeek invents plausible-looking CUT codes (e.g., `13150` for a non-existent Santiago commune). The pin appears at a wrong or null centroid.
**How to avoid (D-07):** After `json.loads()`, validate `commune_cut in VALID_CUTS_SET` before building the IncidentRecord. Reject if not in set.
**Why temp 0.0:** Reduces hallucination of codes outside the list. Not a guarantee — still needs the validation gate.

### Pitfall 4: Truncated JSON from DeepSeek
**What goes wrong:** DeepSeek occasionally returns empty content or truncated JSON when `max_tokens` is too low.
**How to avoid:** Set `max_tokens=512` (the schema is small). Wrap `json.loads()` in try/except; on empty response or JSONDecodeError, retry once with tenacity.
**Warning signs:** `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

### Pitfall 5: pubDate timezone inconsistency
**What goes wrong:** Cooperativa uses `-0400` (Santiago summer time), La Tercera uses `+0000` (UTC). Comparing dates across feeds without normalization causes wrong 30-day window partitioning.
**How to avoid:** Parse `entry.published_parsed` (feedparser returns a `time.struct_time` in UTC) — feedparser normalizes timezones. Convert to `datetime.date` via `datetime.datetime(*entry.published_parsed[:6]).date()`.

### Pitfall 6: Seen-ledger unbounded growth
**What goes wrong:** Committing every seen URL indefinitely makes `seen.json` grow without bound. After 1 year at 4-6 runs/day × ~40 items = ~60K–90K URLs.
**How to avoid:** Prune entries older than 60 days at the end of each run before writing seen.json.

### Pitfall 7: Re-classifying the same article on every CI run
**What goes wrong:** If seen-ledger is gitignored (pipeline/cache/), every GitHub Actions run starts fresh and re-classifies all articles that appear in the current feeds (~40–60 items × $0.001/call = ~$0.04/run × 6 runs/day = ~$0.24/day wasted and duplicates in current.json).
**How to avoid:** Commit seen.json to `data/incidents/seen.json` so it persists across runs.

### Pitfall 8: HTML in BioBíoChile description field
**What goes wrong:** `entry.description` from BioBíoChile contains HTML tags (`<p>`, `<a>`, `<strong>`). Sending raw HTML to DeepSeek wastes tokens and confuses classification.
**How to avoid:** Strip HTML before building the LLM prompt: `re.sub(r'<[^>]+>', '', description)`. Or use `feedparser`'s `entry.summary` which may be pre-stripped.

---

## Code Examples

### Feed Fetch Pattern (mirrors cead/client.py)

```python
# pipeline/news/feeds.py
import feedparser
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

FEEDS = {
    "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
    "Cooperativa": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3_158__1.xml",
    "LaTercera":   "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml",
}

USER_AGENT = "IsChileSafe-news-pipeline/1.0 (+https://ischilesafe.com)"

def fetch_feed(name: str, url: str) -> list[dict]:
    """Fetch and parse one RSS feed. Returns [] on any error (D-04 fallback)."""
    try:
        d = feedparser.parse(url, agent=USER_AGENT, request_headers={"Accept": "application/rss+xml, application/xml, text/xml"})
        if d.bozo:
            logger.warning("[%s] Feed parse warning: %s", name, d.bozo_exception)
        return d.entries
    except Exception as exc:
        logger.warning("[%s] Feed fetch failed: %s", name, exc)
        return []
```

### DeepSeek Classifier Pattern

```python
# pipeline/news/classifier.py
import json, os
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

SYSTEM_PROMPT = """You are a Chilean crime news classifier. Return JSON only.

Given a news headline and summary, output exactly this JSON structure:
{
  "commune_cut": "<5-digit CUT code from VALID_CUTS or null>",
  "family": "<one of: vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades>",
  "title_es": "<concise Spanish headline, max 120 chars>",
  "title_en": "<English translation of title_es, max 120 chars>",
  "summary": "<1-2 sentence neutral summary in English>",
  "confidence": <float 0.0-1.0 indicating location confidence>
}

VALID_CUTS: {cut_list}

Rules:
- commune_cut MUST be from VALID_CUTS exactly, or null if location unknown.
- family MUST be one of the 7 listed values.
- If the article is not about a crime incident, set commune_cut to null.
- Never invent CUT codes.
"""

def classify(title: str, description: str, cut_list: list[str]) -> dict | None:
    prompt = SYSTEM_PROMPT.format(cut_list=",".join(cut_list))
    try:
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            temperature=0.0,
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"HEADLINE: {title}\nSUMMARY: {description[:500]}"},
            ],
        )
        content = resp.choices[0].message.content
        if not content:
            return None
        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return None
```

### Centroid Lookup

```python
# pipeline/news/centroids.py
import json, pathlib

_CENTROIDS: dict[str, dict] | None = None

def get_centroid(cut: str) -> tuple[float, float] | None:
    global _CENTROIDS
    if _CENTROIDS is None:
        path = pathlib.Path(__file__).parents[2] / "data" / "incidents" / "centroids.json"
        _CENTROIDS = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    entry = _CENTROIDS.get(cut)
    return (entry["lat"], entry["lng"]) if entry else None
```

### Orchestrator skeleton (mirrors scrape_cead.py)

```python
# pipeline/scrape_news.py
import datetime, logging, sys, pathlib
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def main() -> int:
    from pipeline.news.feeds import FEEDS, fetch_feed
    from pipeline.news.classifier import classify
    from pipeline.news.centroids import get_centroid
    from pipeline.news.dedup import deduplicate
    from pipeline.news.store import merge_and_write
    from pipeline.cead.catalog import get_commune_catalog  # reuse for CUT list

    run_date = datetime.date.today()
    # ... orchestration logic
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| `deepseek-chat` model ID | `deepseek-v4-flash` | deepseek-chat deprecated 2026-07-24 — never commit old ID |
| `json_schema` response format | `json_object` only (DeepSeek) | json_schema not supported by DeepSeek API |
| Shapely for polygon centroids | Pure-Python Shoelace formula | Avoids heavy C extension; adequate for commune-level precision |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `difflib.SequenceMatcher` performance is adequate for per-run item counts | Deduplication | If batch exceeds ~500 items, consider rapidfuzz; current feeds yield ~75 items/run |
| A2 | Pure-Python Shoelace centroid is within acceptable accuracy for commune pin placement | Centroids | For elongated/island communes (Juan Fernández, Isla de Pascua), centroid may fall outside the polygon — use bounding-box fallback for those |
| A3 | Confidence threshold of 0.6 rejects hallucinated communes without excessive false rejections | Classifier | Tune after first live run; too high wastes items, too low introduces garbage pins |
| A4 | Keyword pre-filter list covers the majority of crime article vocabulary | Pre-filter | Missing keywords pass non-crime items to the LLM (wasted API call) but the classifier's `commune_cut: null` rejection handles them |
| A5 | `topojson` Python package (if needed for centroid script) is a legitimate package | Centroids | Run slopcheck before adding; alternatively use the Node.js decode approach which avoids this dependency |
| A6 | La Tercera encoding anomaly is handled transparently by feedparser | Feed fetch | If feedparser version < 6.0 on CI, encoding may break — pin feedparser==6.0.11 in requirements.txt |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Pipeline runtime | ✓ (local) | system Python | — |
| feedparser | Feed fetch | ✗ (not in requirements.txt) | — | Must install — no fallback |
| openai SDK | DeepSeek client | listed in CLAUDE.md | 1.x | — |
| tenacity | Retry | ✓ in requirements.txt | 9.1.4 | — |
| difflib | Dedup | ✓ stdlib | stdlib | — |
| hashlib | Incident ID | ✓ stdlib | stdlib | — |
| DEEPSEEK_API_KEY | Classification | dev: dotenv; CI: repo secret | — | Pipeline must exit gracefully if absent |
| data/cead/geo/communes.topo.json | Centroid build | ✓ | confirmed | — |
| Node.js (for centroid build script) | build_centroids.py | ✓ (Astro project) | 20+ LTS | Pure-Python Shoelace fallback |

**Missing with no fallback:** `feedparser` — must be added to `pipeline/requirements.txt`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (already in requirements.txt) |
| Config file | none (runs via `pytest pipeline/tests/`) |
| Quick run command | `pytest pipeline/tests/ -x -q` |
| Full suite command | `pytest pipeline/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NEWS-01 | Feed fetch returns entries; feed failure returns [] not exception | unit | `pytest pipeline/tests/test_feeds.py -x` | ❌ Wave 0 |
| NEWS-01 | Keyword pre-filter passes crime items, blocks sports/politics | unit | `pytest pipeline/tests/test_feeds.py::test_keyword_filter -x` | ❌ Wave 0 |
| NEWS-01 | Seen-ledger dedup skips already-seen URLs | unit | `pytest pipeline/tests/test_feeds.py::test_seen_ledger -x` | ❌ Wave 0 |
| NEWS-02 | Classifier rejects item when commune_cut not in 346-CUT set | unit | `pytest pipeline/tests/test_classifier.py::test_invalid_cut_rejected -x` | ❌ Wave 0 |
| NEWS-02 | Classifier rejects item when confidence < threshold | unit | `pytest pipeline/tests/test_classifier.py::test_low_confidence_rejected -x` | ❌ Wave 0 |
| NEWS-02 | IncidentRecord Pydantic model rejects invalid family key | unit | `pytest pipeline/tests/test_classifier.py::test_invalid_family -x` | ❌ Wave 0 |
| NEWS-02 | Centroid lookup returns (lat, lng) for valid CUT | unit | `pytest pipeline/tests/test_centroids.py -x` | ❌ Wave 0 |
| NEWS-03 | Dedup blocks same-url duplicate across outlets | unit | `pytest pipeline/tests/test_dedup.py::test_url_dedup -x` | ❌ Wave 0 |
| NEWS-03 | Dedup blocks near-identical title in same commune+date | unit | `pytest pipeline/tests/test_dedup.py::test_title_similarity -x` | ❌ Wave 0 |
| NEWS-03 | Dedup passes different incidents in same commune | unit | `pytest pipeline/tests/test_dedup.py::test_no_false_positive -x` | ❌ Wave 0 |
| NEWS-04 | Store: incidents older than 30 days move to archive | unit | `pytest pipeline/tests/test_store.py::test_30day_window -x` | ❌ Wave 0 |
| NEWS-04 | Store: merge is idempotent (same ids not duplicated) | unit | `pytest pipeline/tests/test_store.py::test_idempotent_merge -x` | ❌ Wave 0 |
| NEWS-04 | Store: archive YYYY-MM.json created and appended correctly | unit | `pytest pipeline/tests/test_store.py::test_archive_write -x` | ❌ Wave 0 |
| NEWS-05 | IncidentsFile schema gate: outlet/url/date non-nullable | unit | `pytest pipeline/tests/test_schema.py::test_attribution_fields -x` | ❌ Wave 0 |
| NEWS-05 | IncidentsFile serializes to exact TS interface field names | unit | `pytest pipeline/tests/test_schema.py::test_output_field_names -x` | ❌ Wave 0 |
| D-16 | 50-incident manual audit (human-UAT gate) | manual | `python pipeline/scripts/audit_incidents.py` | ❌ Wave 0 |

### DeepSeek Classifier Test Strategy

Do NOT call the live DeepSeek API in unit tests. Use a fixture that mocks `openai.Client.chat.completions.create` to return a known JSON response. Test only the classifier wrapper logic (validation, rejection, schema mapping) — not the model's classification quality.

### Schema Gate Integration Test

Add one integration-level test that:
1. Constructs a minimal `IncidentsFile` dict with one valid and one invalid incident
2. Calls `IncidentsFile.model_validate()` and asserts `ValidationError` on the invalid case
3. Serializes the valid case to dict and checks all field names match the TS interface

### Sampling Rate

- **Per task commit:** `pytest pipeline/tests/ -x -q`
- **Per wave merge:** `pytest pipeline/tests/ -v`
- **Phase gate:** Full suite green + D-16 manual audit complete before close

### Wave 0 Gaps (all test files are new)

- [ ] `pipeline/tests/test_feeds.py` — fixtures: sample XML files in `pipeline/tests/fixtures/`
- [ ] `pipeline/tests/test_classifier.py` — fixtures: mock openai response + invalid CUT/family cases
- [ ] `pipeline/tests/test_dedup.py` — fixtures: incident dicts with controlled title/url/cut/date values
- [ ] `pipeline/tests/test_store.py` — fixtures: temp directory + pre-populated current.json
- [ ] `pipeline/tests/test_centroids.py` — fixture: minimal centroids.json with 2-3 known CUT entries
- [ ] `pipeline/tests/test_schema.py` — uses existing conftest.py patterns; validates IncidentsFile model
- [ ] `pipeline/tests/fixtures/feed_biobio_sample.xml` — 5-item RSS with 2 crime + 2 sport + 1 ambiguous
- [ ] `pipeline/tests/fixtures/feed_cooperativa_sample.xml` — 5-item policial RSS
- [ ] `pipeline/tests/fixtures/feed_latercera_sample.xml` — 5-item general RSS with 2 crime items
- [ ] `pipeline/scripts/audit_incidents.py` — D-16 manual audit tool

---

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | Pydantic v2 `IncidentsFile.model_validate()` before any write; reject on schema violation |
| V6 Cryptography | No | SHA-256 for incident ID (not a security primitive; stdlib `hashlib`) |
| V2 Authentication | Partial | `DEEPSEEK_API_KEY` from env — never hardcoded; dotenv in dev, repo secret in CI |
| V4 Access Control | No | Pipeline is a batch script; no user-facing access control surface |

**Key threat pattern:** The pipeline writes to `data/incidents/current.json` which is served publicly. Ensure incident strings are Pydantic-validated before write (V5). The Phase-3 IncidentPinLayer already HTML-escapes all incident strings before DOM insertion (T-03-03-02) — Phase 5 does not need to double-escape, but MUST NOT inject raw HTML into the JSON fields (`title_es`, `title_en`, `summary` must be plain text strings, not HTML).

---

## Project Constraints (from CLAUDE.md)

- Model MUST be `deepseek-v4-flash` — never `deepseek-chat`, `deepseek-reasoner`, or `deepseek-v4-pro` (unless flash quality is insufficient).
- openai SDK with `base_url="https://api.deepseek.com"` and `DEEPSEEK_API_KEY` from env.
- feedparser 6.0.x is the mandated RSS library.
- tenacity for retry logic.
- python-dotenv for dev key loading.
- Scraping courtesy: custom User-Agent string identifying the bot + project URL.
- Editorial rule: incident `outlet` + `url` + `date` must always be present; never editorialize beyond the source.
- Pydantic v2 exclusively — no v1 `@validator`, no `parse_obj`.
- JSON in repo as data store — no backend/DB.
- `deepseek-chat` deprecated 2026-07-24 — must not appear in any committed code.

---

## Open Questions

1. **Confidence threshold calibration**
   - What we know: threshold of 0.6 is a reasonable starting point.
   - What's unclear: DeepSeek v4-flash's calibration may mean confidence > 0.9 for known communes and < 0.3 for unknown — or it may cluster near 0.5. No empirical data.
   - Recommendation: start at 0.6; log all rejected items with their confidence in the first live run; adjust after the D-16 manual audit.

2. **CUT catalog source for the classifier prompt**
   - What we know: `pipeline/cead/catalog.py:get_commune_catalog()` requires a live CEAD session (HTTP call).
   - What's unclear: whether to call CEAD on every news pipeline run (expensive) or cache the 346-CUT list as a static asset.
   - Recommendation: extract the 346-CUT list to a static `data/incidents/cut_list.json` generated once by the CEAD pipeline. The news pipeline reads this file (no live CEAD call needed per run).

3. **Seen-ledger git commit pattern**
   - What we know: Phase 6 will handle the GitHub Actions cron + commit pattern.
   - What's unclear: Phase 5's `scrape_news.py` should not need to know about git. The commit (including seen.json + current.json) should be triggered from the GitHub Actions workflow.
   - Recommendation: `scrape_news.py` writes all files atomically; Phase 6 workflow adds the git commit step. Document the expected commit pattern in the Phase 6 handoff.

---

## Sources

### Primary (HIGH confidence)
- Live HTTP probe of all 3 RSS feeds — 2026-06-13 (BioBíoChile 200/20 items, Cooperativa Policial 200/15 items, La Tercera 200/41 items)
- `data/cead/geo/communes.topo.json` Python probe — object key `communes-rekeyed`, property key `id`, 346 features (2026-06-13)
- `site/src/components/map/IncidentPinLayer.ts` — authoritative TS interface (read directly)
- `pipeline/shared/atomic_write.py`, `pipeline/shared/schema.py`, `pipeline/cead/catalog.py`, `pipeline/cead/client.py`, `pipeline/scrape_cead.py` — all read directly from codebase
- `pipeline/requirements.txt` — read directly; confirms feedparser absent
- [DeepSeek JSON Mode docs](https://api-docs.deepseek.com/guides/json_mode) — json_object only, prompt must contain "json", occasional empty responses
- [Cooperativa RSS page](https://www.cooperativa.cl/noticias/stat/rss/rss.html) — policial feed URL `rss_3_158__1.xml` confirmed

### Secondary (MEDIUM confidence)
- [CLAUDE.md project instructions] — feedparser 6.0.x, openai SDK base_url pattern, DeepSeek model IDs, editorial rules
- [DeepSeek API Docs root](https://api-docs.deepseek.com/) — model names and base_url

### Tertiary (LOW confidence / ASSUMED)
- Confidence threshold 0.6 — untested against actual DeepSeek v4-flash output
- Keyword pre-filter list — initial approximation; requires tuning after first live run

---

## Metadata

**Confidence breakdown:**
- Feed URLs: HIGH — live-verified 2026-06-13
- Feed structure (field names, item counts): HIGH — live-verified
- DeepSeek json_object mode: HIGH — official docs
- TopoJSON property key / feature count: HIGH — Python probe
- Dedup algorithm: MEDIUM — stdlib difflib is well-understood; threshold is ASSUMED
- Confidence threshold: LOW — requires empirical calibration

**Research date:** 2026-06-13
**Valid until:** Feed URLs should be re-verified before implementation (30 days). DeepSeek API docs: stable.
