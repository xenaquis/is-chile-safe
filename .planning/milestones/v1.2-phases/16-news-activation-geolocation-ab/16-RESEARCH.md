# Phase 16: News Activation + Geolocation Redesign + Model A/B — Research

**Researched:** 2026-06-18
**Domain:** Python news pipeline (geolocation redesign, A/B harness) + Astro static pages (bilingual news page, incident linking)
**Confidence:** HIGH — all findings from direct codebase inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Keys available** — run live pipeline + A/B in this autonomous run.
- **Geolocation:** name-emit + deterministic name→CUT (do NOT just switch models — that won't fix it). Keep centroid-from-CUT for coordinates.
- **Reuse**, don't rebuild: extend `IncidentsList.tsx` (add comuna link) and the existing pipeline modules; keep the anti-hallucination centroid design.
- **Depends on Phase 17** (source registry + methodology) and Phase 11 (comuna pages exist to link incidents to).
- **Verify with BrowserOS** (EN+ES news page, pins, both link types).
- Editorial/legal: every incident cites + links its press source; sober tone; attribute the medium.

### Claude's Discretion
(none stated — all areas are either locked or deferred)

### Deferred Ideas (OUT OF SCOPE)
- Composite crime index / metric redesign (Phase 17 / future Phase 18).
- Go-live infra cutover (DEPLOYMENT.md; human gate).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NEWS-01 | Geolocation redesign — LLM emits commune NAME + region hint; deterministic name→CUT resolver; accuracy beats bare-CUT baseline on golden set | Classifier prompt rewrite (classifier.py lines 52-73); resolver mirrors index.json name field + NFD normalization pattern from communes/index.astro |
| NEWS-02 | Golden set (30-50 incidents, ground-truth cut+family) + scoring script; env-configurable provider; A/B DeepSeek vs MiniMax; winner documented + wired as default | classifier.py `client` construction; MiniMax call differences; fixtures dir pattern |
| NEWS-03 | Live pipeline run → `data/incidents/current.json`; pins + recent-incidents render real geolocated incidents; no console errors | scrape_news.py orchestrator; sync-data.mjs prebuild; dotenv loading at line 76 |
| NEWS-04 | Each incident links to source AND to its commune page; dedicated bilingual /news/ + /es/noticias/ page; freshness indicator; all incidents cite+link source | IncidentsList.tsx extend; BaseLayout props; PageHeader nav wiring; sitemap filter |
</phase_requirements>

---

## Summary

Phase 16 activates the built-but-dark news layer. The pipeline, frontend components, and data sync are all already wired — what's missing is: (1) a fixed geolocation strategy, (2) evidence-backed provider selection, (3) a real production run, and (4) a surface for the incidents outside the map.

The root cause of ~60-70% wrong CUT geolocation is definitively in `pipeline/news/classifier.py` lines 33-34 and 52-73: `_CUT_LIST_STR` is built as comma-joined bare CUT codes with no names, and the prompt asks the model to pick from these opaque codes. The fix is to change the prompt so the model emits a commune name (and optional region hint), then resolve that name deterministically against `data/cead/meta/index.json` — the same 346-entry source of truth already used everywhere else. The centroid lookup (`pipeline/news/centroids.py`) remains unchanged.

For the bilingual news page (NEWS-04), the pattern is well-established: two `.astro` files (`site/src/pages/news.astro` + `site/src/pages/es/noticias.astro`), both using `BaseLayout` with explicit `enPath`/`esPath` props and hardcoded locale slugs (per the localized-slug pitfall documented in project memory). The `PageHeader.astro` nav needs two new hardcoded href constants. The `sitemapFilter` in `astro.config.mjs` passes unknown pages by default — no change needed unless the news page URLs need to be explicitly included.

**Primary recommendation:** The geolocation fix lives entirely in `pipeline/news/classifier.py` (prompt change) plus a new `pipeline/news/resolver.py` module (name→CUT lookup). Everything else — centroid lookup, store, schema, sync, Astro routing — is already correct and must not be changed.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CUT geolocation (name→CUT) | Pipeline / Python | — | Deterministic; runs offline before data is committed |
| Centroid resolution (CUT→lat,lng) | Pipeline / Python | — | Anti-hallucination; LLM never emits coordinates |
| A/B provider selection | Pipeline / Python | — | `os.environ.get("NEWS_PROVIDER")` flag at module load |
| Golden set + scoring | Pipeline / Python script | — | Offline evaluation; no frontend involvement |
| Incident storage | Static JSON (data/incidents/) | — | `current.json` is the contract between pipeline and frontend |
| Data sync to site | Site prebuild script | — | `site/scripts/sync-data.mjs` copies `data/incidents/` → `site/public/data/incidents/` |
| Map pins | Browser / Leaflet island | — | `IncidentPinLayer.ts` fetches `/data/incidents/current.json` at runtime |
| "Recent incidents" on commune pages | Frontend Server (Astro SSG) | — | Static page reads incidents JSON at build time (needs build-time access) |
| Dedicated news page | Frontend Server (Astro SSG) | — | Two .astro files, one per locale |
| Incident→commune link | Browser / React island + Static Astro | — | Both IncidentsList.tsx (map popup) and news page template |

---

## NEWS-01: Geolocation Redesign — Code Map

### Current Broken State

**File:** `pipeline/news/classifier.py`

- **Line 34:** `_CUT_LIST_STR: str = ",".join(sorted(VALID_CUTS))` — builds a bare comma-joined list of 346 opaque 5-digit codes. No names.
- **Lines 64-65 (system prompt):** `"VALID_CUTS (346 Chilean commune CUT codes — commune_cut MUST be from this list or null):\n{_CUT_LIST_STR}"` — the model sees codes like `10101,10102,10103,...` with no place names. It must recall "Las Condes=13114" from parametric memory, which fails at 60-70%.
- **`ClassifierOutput` schema** (`pipeline/news/schema.py` line 82): `commune_cut: str | None` — the output field that must change to `commune_name: str | None` in the redesign.

### Required Changes

**1. New module: `pipeline/news/resolver.py`**

Build a deterministic name→CUT lookup from `data/cead/meta/index.json`. The index schema is:
```json
{"cut": "10101", "name": "Puerto Montt", "slug": "puerto-montt", "region_id": "10", ...}
```

The normalization function pattern already exists in the frontend:
- `site/src/pages/communes/index.astro` line: `const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();`

Python equivalent (accent-insensitive, already used in `pipeline/tests/test_atomic_write.py` for UTF-8 round-trip testing):
```python
import unicodedata

def _normalize(s: str) -> str:
    """Lowercase + strip combining diacritics (NFD decompose → strip Mn category)."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s.lower())
        if unicodedata.category(c) != 'Mn'
    )
```

The resolver loads `data/cead/meta/index.json` (same path logic as `pipeline/news/schema.py` line 22: `pathlib.Path(__file__).parents[2] / "data" / ...`), builds `{normalized_name: cut}` and `{normalized_name: (cut, region_id)}` maps at module load, then exposes:
```python
def resolve_cut(commune_name: str, region_hint: str | None = None) -> str | None
```

Disambiguation strategy: if a normalized name maps to multiple CUTs (e.g. "villa alemana" doesn't, but edge cases can exist), use `region_hint` to filter. Return `None` if no match.

**2. Classifier prompt change (`pipeline/news/classifier.py`)**

Replace the current opaque CUT-code prompt with:
```
Output exactly this JSON structure:
{
  "commune_name": "<exact commune name in Spanish, e.g. 'Las Condes', or null if location unknown>",
  "region_hint": "<region name or number, e.g. 'Metropolitana' or '13', or null>",
  "family": "<one of: vida, propiedad, ...>",
  "title_es": "...",
  "title_en": "...",
  "summary": "...",
  "confidence": <float 0.0-1.0>
}

Rules:
- commune_name MUST be a real Chilean commune name, spelled in Spanish. Do NOT invent names.
- If location is unknown or article is not a crime incident, set commune_name to null.
- region_hint helps disambiguation — provide it when the article mentions the region.
```

Also build and inject a plain-language reference list for the prompt: `_COMMUNE_LIST_STR` = one name per line, e.g. `"Las Condes (Región Metropolitana)"` — this gives the model correct spellings without the opaque code problem.

**3. `ClassifierOutput` schema change (`pipeline/news/schema.py`)**

Replace `commune_cut: str | None` with `commune_name: str | None` and `region_hint: str | None`. Remove the `VALID_CUTS` membership check in `classifier.py` lines 119-125 (now done in resolver).

**4. `scrape_news.py` orchestrator change (lines 208-210)**

Replace:
```python
cut = result.commune_cut
```
with:
```python
from pipeline.news.resolver import resolve_cut
cut = resolve_cut(result.commune_name, result.region_hint) if result.commune_name else None
```

The rest of the orchestrator (centroid lookup, build_incident, merge_and_write) is **unchanged**.

### Deterministic Lookup Mirror: `srcCodeToCut` (Phase 10)

The geometry re-key in `scripts/build-topojson.mjs` line 67:
```javascript
function srcCodeToCut(code) {
  return String(parseInt(code, 10));  // strips leading zeros
}
```
This is a CUT normalizer (chilemapas zero-padded → CEAD unpadded). The name→CUT resolver is conceptually similar: a pure lookup with no external state. Both are deterministic, module-level, single-function maps. Mirror the pattern: load once at module import, expose a single pure function.

---

## NEWS-02: Golden Set + A/B Harness — Code Map

### Existing Fixture Infrastructure

- **Fixtures dir:** `pipeline/tests/fixtures/`
- **Existing fixture:** `deepseek_response_sample.json` — one classified incident `{"commune_cut": "13101", "family": "propiedad", ...}`. This is the existing schema (pre-redesign). After NEWS-01, the golden set schema changes to `commune_name`/`region_hint`.
- **Test pattern:** `pipeline/tests/test_classifier.py` — mocks `pipeline.news.classifier.client` via `unittest.mock.patch`. All tests avoid live API calls.

### Golden Set Format

New file: `pipeline/tests/fixtures/golden_set.json`

```json
[
  {
    "id": "g001",
    "headline": "Robo con violencia en Las Condes dejó un herido",
    "description": "Un hombre fue víctima de robo con violencia en la comuna de Las Condes...",
    "ground_truth": {
      "commune_name": "Las Condes",
      "cut": "13114",
      "family": "propiedad"
    },
    "source_outlet": "BioBioChile",
    "source_url": "https://..."
  }
]
```

30-50 real incidents, covering: (a) major cities where the model is likely to succeed, (b) smaller communes where it's likely to fail, (c) incidents with ambiguous location, (d) non-crime items (should get null commune_name). Ground-truth `cut` is the resolver output for ground-truth `commune_name`.

### Provider Selection (env-configurable)

**Current state:** `pipeline/news/classifier.py` hardcodes the DeepSeek client at module load (lines 43-46):
```python
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)
```

**Redesign pattern:** Add `NEWS_PROVIDER` env var (`"deepseek"` | `"minimax"`, default `"deepseek"`). At module load:
```python
_PROVIDER = os.environ.get("NEWS_PROVIDER", "deepseek").lower()

if _PROVIDER == "minimax":
    client = OpenAI(
        api_key=os.environ.get("MINIMAX_API_KEY", ""),
        base_url="https://api.minimaxi.chat/v1",
    )
    _MODEL = "MiniMax-Text-01"
else:
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
    )
    _MODEL = "deepseek-v4-flash"
```

### MiniMax Call Differences (from CONTEXT.md Wave-0 findings)

| Parameter | DeepSeek | MiniMax |
|-----------|----------|---------|
| `model` | `"deepseek-v4-flash"` | `"MiniMax-Text-01"` |
| `base_url` | `"https://api.deepseek.com"` | `"https://api.minimaxi.chat/v1"` |
| `api_key` env | `DEEPSEEK_API_KEY` | `MINIMAX_API_KEY` |
| `response_format` | `{"type": "json_object"}` — SUPPORTED | **NOT supported** → remove; parse JSON from content string |

For MiniMax: the `_call_api` function must conditionally omit `response_format` and parse the JSON manually from content (which may be wrapped in ```json ... ``` markdown fences — strip with regex `r'```(?:json)?\s*([\s\S]*?)```'` or use `json.loads(content.strip().strip('`').strip('json').strip())`).

### Scoring Script

New file: `pipeline/experiments/ab_score.py`

Inputs: `--golden pipeline/tests/fixtures/golden_set.json`, `--provider deepseek|minimax`, `--output results/ab_{provider}.json`

Metrics per run:
- `commune_accuracy`: fraction where `resolve_cut(predicted_name) == ground_truth.cut`
- `family_accuracy`: fraction where `predicted_family == ground_truth.family`
- `null_rate`: fraction of non-crime items correctly getting null commune
- `parse_failure_rate`: fraction where response could not be parsed as JSON
- `empty_response_rate`: fraction where content was empty/truncated
- `mean_latency_ms`: wall-clock time per call
- `estimated_cost_usd`: based on token counts (DeepSeek pricing: ~$0.14/M input, ~$0.28/M output [ASSUMED]; MiniMax pricing [ASSUMED])

Output: a JSON report + a human-readable markdown table to stdout.

---

## NEWS-03: Live Pipeline Run — Code Map

### Key Wiring Already in Place

- **API key loading:** `pipeline/scrape_news.py` lines 75-78 — loads `.env` from `pipeline/.env` via `python-dotenv` (if installed). CI uses repo secrets directly.
- **Graceful key-absent exit:** lines 85-93 — `if not api_key: logger.warning(...); return 0`. Exit 0 = no commit/deploy triggered.
- **Output path:** `data/incidents/current.json` (lines 96-98).
- **Archive path:** `data/incidents/archive/YYYY-MM.json`.
- **Seen ledger:** `data/incidents/seen.json` — prevents re-classification of seen URLs.

### Data Sync to Site

**File:** `site/scripts/sync-data.mjs` lines 44-50.

The sync script copies `data/incidents/` → `site/public/data/incidents/` as part of `predev` + `prebuild`. No changes needed for NEWS-03. The `current.json` just needs to exist.

**package.json pattern (infer from sync-data.mjs comment):** `"predev": "node scripts/sync-data.mjs"`, `"prebuild": "node scripts/sync-data.mjs"`. This means: run `python pipeline/scrape_news.py` first, then `npm run build` inside `site/` — the sync happens automatically.

### OneDrive desync (project memory)

Chain `npm run build && npm run validate` in a single shell command (per `OneDrive build artifacts desync` memory note) to prevent `dist/` vanishing between processes.

### Schema After NEWS-01 Redesign

`IncidentRecord` in `pipeline/news/schema.py` gains a `slug: str` field (the commune slug for the frontend link). The `build_incident` function in `pipeline/news/store.py` must accept `slug` and pass it through. The `VALID_CUTS` validator on `IncidentRecord.cut` is unchanged.

The `IncidentsFile` Pydantic model and TypeScript `IncidentsFile` interface in `site/src/components/map/IncidentPinLayer.ts` must both be updated to include `slug` in `Incident`.

---

## NEWS-04: Surfacing + Linking — Code Map

### Incident Schema Extension

**Python side (`pipeline/news/schema.py`):**

Add `slug: str` to `IncidentRecord`. The `build_incident()` function (`pipeline/news/store.py` line 38) gets a `slug: str` parameter, sourced from `resolve_cut()` returning both `cut` and `slug` (look up in index.json by CUT after resolution).

**TypeScript side (`site/src/components/map/IncidentPinLayer.ts`):**

The `Incident` interface (lines 42-53) gains `slug: string`. The popup HTML in `fetchAndMountIncidents` (lines 131-141) gains a commune link:
```html
<a href="/commune/${escHtml(incident.slug)}/" ...>View commune page</a>
```
(with locale-awareness: if `lang === 'es'`, use `/es/comuna/${escHtml(incident.slug)}/`)

**React side (`site/src/components/map/IncidentsList.tsx`):**

The `Incident` interface (lines 8-14) gains `slug: string` and `cut: string`. The component gains a commune link below the existing source link:
```tsx
<a href={lang === 'es' ? `/es/comuna/${e.slug}/` : `/commune/${e.slug}/`}
   className="event-commune-link">
  {lang === 'es' ? 'Ver comuna' : 'View commune'}
</a>
```

### Dedicated Bilingual News Page

**Pattern to mirror:** `site/src/pages/methodology.astro` (EN) + `site/src/pages/es/metodologia.astro` (ES) — a two-file bilingual pair using `BaseLayout`.

**New files:**
- `site/src/pages/news.astro` — EN at `/news/`
- `site/src/pages/es/noticias.astro` — ES at `/es/noticias/`

**BaseLayout props pattern (from `methodology.astro` expected pattern):**
```astro
<BaseLayout
  lang="en"
  title="Chile Crime News — Chile Safety Map"
  description="..."
  enPath="/news/"
  esPath="/es/noticias/"
  pageType="editorial"
>
```

**Localized-slug pitfall (project memory):** `getRelativeLocaleUrl('/news')` would emit `/es/news/` for the ES locale — WRONG. Always hardcode the ES slug: `esPath="/es/noticias/"`.

**Freshness indicator:** Read `data.generated` from `current.json` at build time (Astro getStaticPaths / top-level script). Display as `<time datetime={data.generated}>Updated {formattedDate}</time>`.

**Build-time incident loading:** The news page reads incidents from `data/incidents/current.json` at build time, not via fetch. Use `fs.readFileSync` inside the Astro frontmatter (same pattern as `site/scripts/sync-data.mjs` uses `cpSync` — the data is in `site/public/data/incidents/` after the prebuild sync, or read directly from `../../data/incidents/current.json` using Astro's `@data` vite alias pointing to `data/`).

Actually, the `@data` vite alias is defined in `astro.config.mjs` lines 93-99: `'@data': path.resolve(__dirname, '..', 'data')`. This means Astro pages can `import incidents from '@data/incidents/current.json'` at build time. If `current.json` doesn't exist yet (first build before live run), the news page must handle this gracefully — wrap in `existsSync` check or provide an empty fallback.

**Filtering by commune:** The news page can show all incidents, or optionally link to "incidents in {commune}" by filtering `incidents` by `cut`. For the dedicated page, show all incidents in chronological order.

### PageHeader Nav Wiring

**File:** `site/src/components/PageHeader.astro` lines 24-27.

Add `newsHref` constant:
```javascript
// Hardcoded per-locale — getRelativeLocaleUrl does NOT translate ES slugs (Pitfall 3)
const newsHref = locale === 'en' ? '/news/' : '/es/noticias/';
```

Add nav link in the `<nav>` block (line 61):
```astro
<a href={newsHref} class="nav-link">{t.nav_news}</a>
```

Add to `I18nStrings` interface (`site/src/config/i18n.ts`): `nav_news: string` with values `"News"` (EN) and `"Noticias"` (ES).

### Sitemap Wiring

**File:** `site/astro.config.mjs` `sitemapFilter` function.

The current filter (lines 46-72) returns `true` for "all other pages" by default. The news pages `/news/` and `/es/noticias/` will be auto-included without any filter change. However, to be explicit and future-proof, add a news URL check:
```javascript
if (/\/news\/$/.test(url) || /\/es\/noticias\/$/.test(url)) return true;
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accent-insensitive name matching | Custom fuzzy match / Levenshtein | `unicodedata.normalize('NFD', s)` + strip Mn-category chars | Already in the frontend; exact match after normalization is sufficient for 346 known commune names |
| LLM coordinates | Ask model for lat/lng | `pipeline/news/centroids.py` `get_centroid(cut)` | Anti-hallucination design already in place; centroid.json has all 346 CUTs |
| JSON parsing from MiniMax | Custom parser | `json.loads(content)` after stripping optional markdown fences | The JSON is standard; MiniMax just doesn't guarantee `response_format` compliance |
| CUT validity check | Separate validator | `VALID_CUTS` set in `pipeline/news/schema.py` — already loaded | `IncidentRecord.cut_must_be_valid` validator runs on `build_incident` |
| Static page data access | API call / fetch | `@data` vite alias → `import ... from '@data/incidents/current.json'` at build time | Astro static generation; no runtime server |

---

## Common Pitfalls

### Pitfall 1: Changing `IncidentRecord` schema breaks existing `current.json`
**What goes wrong:** Adding `slug` to `IncidentRecord` and running `validate_incidents_file()` on an existing `current.json` that lacks `slug` fields causes `ValidationError`, blocking the merge.
**How to avoid:** Make `slug: str | None = None` optional in `IncidentRecord` for backwards-compat, or add a migration step that backfills `slug` from `cut` during `merge_and_write` load.

### Pitfall 2: MiniMax `response_format=json_object` → 400 error
**What goes wrong:** Passing `response_format={"type": "json_object"}` to MiniMax returns HTTP 400 (documented in CONTEXT.md Wave-0 findings).
**How to avoid:** In `_call_api`, conditionally include `response_format` only when `_PROVIDER == "deepseek"`. Always parse JSON from content string for MiniMax.

### Pitfall 3: Localized-slug 404 for ES news link
**What goes wrong:** `getRelativeLocaleUrl(locale, '/news')` emits `/es/news/` not `/es/noticias/`. 404 in production.
**How to avoid:** Hardcode `newsHref = locale === 'en' ? '/news/' : '/es/noticias/'` in `PageHeader.astro`. Never use `getRelativeLocaleUrl` for ES slugs that differ from EN (project memory: `i18n-localized-slug-pitfall.md`).

### Pitfall 4: `@data` import fails if `current.json` doesn't exist at build time
**What goes wrong:** `import incidents from '@data/incidents/current.json'` throws at build if the file is absent (first build before any pipeline run).
**How to avoid:** Use `existsSync` + conditional import in Astro frontmatter, or provide an empty fallback `{generated: null, window_days: 30, incidents: []}` that the news page renders as "no incidents yet".

### Pitfall 5: `IncidentPinLayer.ts` popup has commune link with wrong locale
**What goes wrong:** The popup is built in `fetchAndMountIncidents` with string interpolation. Using `/commune/${slug}/` always serves EN even for ES locale.
**How to avoid:** `lang` parameter is already passed to `fetchAndMountIncidents`. Use `lang === 'es' ? '/es/comuna/' : '/commune/'` as the commune URL prefix.

### Pitfall 6: `scrape_news.py` key check only checks `DEEPSEEK_API_KEY`
**What goes wrong:** When `NEWS_PROVIDER=minimax`, the key check at line 86 still looks for `DEEPSEEK_API_KEY` and exits early even if `MINIMAX_API_KEY` is set.
**How to avoid:** Change the key check to use the correct key env var based on `NEWS_PROVIDER`:
```python
key_env = "MINIMAX_API_KEY" if os.environ.get("NEWS_PROVIDER", "deepseek") == "minimax" else "DEEPSEEK_API_KEY"
api_key = os.environ.get(key_env, "").strip()
```

### Pitfall 7: Golden set CUT ground truth uses old classifier schema
**What goes wrong:** Fixture records use `commune_cut` (old schema) instead of `commune_name` + `cut` (new schema). Tests that compare model output to ground truth fail silently if the field names differ.
**How to avoid:** Design golden set with `ground_truth: {commune_name, cut, family}`. The scoring script resolves `predicted_name` → CUT via resolver and compares to `ground_truth.cut`.

---

## Code Examples

### Resolver module skeleton
```python
# pipeline/news/resolver.py
import json, pathlib, unicodedata

_INDEX_PATH = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
_NAME_TO_CUT: dict[str, str] = {}  # normalized_name → cut
_NAME_TO_SLUG: dict[str, str] = {}  # normalized_name → slug
_CUT_TO_SLUG: dict[str, str] = {}  # cut → slug

def _norm(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s.lower())
        if unicodedata.category(c) != 'Mn'
    )

def _load() -> None:
    global _NAME_TO_CUT, _NAME_TO_SLUG, _CUT_TO_SLUG
    entries = json.loads(_INDEX_PATH.read_text(encoding='utf-8'))
    for e in entries:
        key = _norm(e['name'])
        _NAME_TO_CUT[key] = e['cut']
        _NAME_TO_SLUG[key] = e['slug']
        _CUT_TO_SLUG[e['cut']] = e['slug']

_load()

def resolve_cut(name: str | None, region_hint: str | None = None) -> tuple[str, str] | None:
    """Returns (cut, slug) or None if no match."""
    if not name:
        return None
    key = _norm(name)
    cut = _NAME_TO_CUT.get(key)
    slug = _NAME_TO_SLUG.get(key)
    if cut and slug:
        return (cut, slug)
    return None

def slug_for_cut(cut: str) -> str | None:
    return _CUT_TO_SLUG.get(cut)
```
[VERIFIED: index.json schema confirmed `{"cut", "name", "slug", "region_id"}` from direct codebase read]

### Commune list string for prompt
```python
# In classifier.py — build a human-readable list for the prompt
import json, pathlib
_INDEX = json.loads(
    (pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json")
    .read_text(encoding="utf-8")
)
# E.g.: "Las Condes (Región Metropolitana, id:13)"
_COMMUNE_LIST_STR = "\n".join(
    f"{e['name']} (region_id:{e['region_id']})" for e in _INDEX
)
```

### MiniMax-compatible `_call_api`
```python
import re as _re

def _call_api(user_content: str) -> str | None:
    kwargs = dict(
        model=_MODEL,
        temperature=0.0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    if _PROVIDER == "deepseek":
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        if not content:
            return None
        # Strip markdown fences if MiniMax wraps output
        content = _re.sub(r'^```(?:json)?\s*', '', content.strip())
        content = _re.sub(r'\s*```$', '', content)
        return content.strip() or None
    except Exception as exc:
        logger.warning("API call failed (%s): %s", _PROVIDER, exc)
        return None
```

### News page build-time incident load (Astro frontmatter)
```astro
---
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const incidentPath = path.resolve(__dirname, '..', '..', '..', 'data', 'incidents', 'current.json');

let incidentData = { generated: null, incidents: [] };
if (existsSync(incidentPath)) {
  incidentData = JSON.parse(readFileSync(incidentPath, 'utf-8'));
}

const enPath = '/news/';
const esPath = '/es/noticias/';
---
```

---

## Validation Architecture

**nyquist_validation: true** (from `.planning/config.json`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (pipeline); existing tests in `pipeline/tests/` |
| Config file | `pipeline/pytest.ini` or `pipeline/pyproject.toml` (check existing) |
| Quick run command | `cd pipeline && python -m pytest tests/test_classifier.py tests/test_schema_incidents.py -x -q` |
| Full suite command | `cd pipeline && python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NEWS-01 | Resolver: known headline → correct CUT | unit | `pytest tests/test_resolver.py -x` | ❌ Wave 0 |
| NEWS-01 | Resolver: accent-insensitive match (Cochamó → cochamo) | unit | `pytest tests/test_resolver.py::test_accent_insensitive -x` | ❌ Wave 0 |
| NEWS-01 | Resolver: unknown name → None | unit | `pytest tests/test_resolver.py::test_unknown_name_returns_none -x` | ❌ Wave 0 |
| NEWS-01 | Classifier: invalid commune_name passes through (resolver rejects) | unit | `pytest tests/test_classifier.py -x` (extend existing) | existing |
| NEWS-02 | A/B scoring: DeepSeek commune accuracy > baseline (bare-CUT, expected ~30-40%) | integration | `python experiments/ab_score.py --provider deepseek` | ❌ Wave 0 |
| NEWS-02 | A/B scoring: MiniMax commune accuracy measured and documented | integration | `python experiments/ab_score.py --provider minimax` | ❌ Wave 0 |
| NEWS-03 | `current.json` validates against `IncidentsFile` schema | unit | `pytest tests/test_schema_incidents.py -x` | existing |
| NEWS-03 | Pipeline runs without errors with key set | smoke | `python pipeline/scrape_news.py` (with key) | manual |
| NEWS-04 | `IncidentsList.tsx` renders commune link | unit | Vitest / existing front-end tests | ❌ Wave 0 |
| NEWS-04 | `/news/` builds without error | smoke | `npm run build` in `site/` | automated by build |
| NEWS-04 | `/es/noticias/` builds and has correct hreflang | smoke | `npm run build` + validate | automated by validator |

### Observable Signals per Requirement

- **NEWS-01:** Golden set scoring script output: `commune_accuracy` with name-emit approach > 30-40% (bare-CUT baseline per CONTEXT.md ~30-40% at most). Target: > 70%.
- **NEWS-02:** `ab_score.py` produces `results/ab_deepseek.json` and `results/ab_minimax.json` with all 5 metrics. Winner is documented in `16-VERIFICATION.md`.
- **NEWS-03:** `data/incidents/current.json` exists after pipeline run; passes `validate_incidents_file()`; all incidents have non-null `cut` and `slug`; `IncidentPinLayer.ts` fetches it without console error.
- **NEWS-04:** BrowserOS: EN `/news/` renders incidents with source link + commune link; ES `/es/noticias/` same; map incident pin popup has working commune link; `PageHeader` shows "News"/"Noticias" nav item.

### Wave 0 Gaps
- [ ] `pipeline/news/resolver.py` — new module (NEWS-01)
- [ ] `pipeline/tests/test_resolver.py` — covers accent, exact, unknown, disambiguation
- [ ] `pipeline/tests/fixtures/golden_set.json` — 30-50 labelled incidents
- [ ] `pipeline/experiments/ab_score.py` — scoring harness
- [ ] `site/src/pages/news.astro` — EN news page
- [ ] `site/src/pages/es/noticias.astro` — ES news page

*(All existing test infrastructure passes; Wave 0 only needs the above new files.)*

### Sampling Rate
- **Per task commit:** `cd pipeline && python -m pytest tests/test_resolver.py tests/test_classifier.py -x -q`
- **Per wave merge:** `cd pipeline && python -m pytest tests/ -q`
- **Phase gate:** Full suite green + BrowserOS check + `16-VERIFICATION.md` before `/gsd:verify-work`

---

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1` (from config).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no user auth in news layer |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A — all read-only public data |
| V5 Input Validation | yes | LLM output validated via Pydantic (`ClassifierOutput`); resolver returns None for unknown names; HTML escaping in `IncidentPinLayer.ts` (`escHtml`) and `safeUrl()` already in place |
| V6 Cryptography | no | No secrets stored in output |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via LLM-generated incident title in popup HTML | Tampering | `escHtml()` in `IncidentPinLayer.ts` lines 65-72 already applied to all incident strings; extend to new fields (slug must be URL-safe, no escaping needed for path segment) |
| javascript: injection via incident URL | Tampering | `safeUrl()` in `IncidentPinLayer.ts` lines 76-87 already validates scheme. Unchanged. |
| Prompt injection via RSS headline | Spoofing | Pydantic validates all classifier output fields; resolver rejects unknown names; `commune_name` that doesn't resolve is dropped (no data written) |
| API key exposure | Info Disclosure | Keys only in `pipeline/.env` (gitignored) or CI secrets. `scrape_news.py` line 90 explicitly never logs key value. `MINIMAX_API_KEY` must follow same pattern. |
| Malicious commune slug in incident→commune link | Tampering | `slug` field comes from `index.json` (build-time resolved, closed set of 346 known slugs) — not from LLM output. No escaping risk beyond `escHtml()`. |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `DEEPSEEK_API_KEY` | NEWS-02 A/B, NEWS-03 live run | Available per CONTEXT.md | — | Exit 0 gracefully (line 93) |
| `MINIMAX_API_KEY` | NEWS-02 A/B (MiniMax side) | Available per CONTEXT.md | — | Skip MiniMax A/B leg, document |
| python-dotenv | `pipeline/scrape_news.py` line 76 | Likely installed (requirements.txt) | 1.x | try/except at line 76 already handles ImportError |
| `data/incidents/cut_list.json` | `pipeline/news/schema.py` line 23 | Exists (CR-03 guard raises FileNotFoundError if absent) | — | None — must exist |
| `data/cead/meta/index.json` | New resolver.py | Exists (used by astro.config.mjs + all pages) | 346 entries | None — must exist |
| `data/incidents/centroids.json` | `pipeline/news/centroids.py` | Exists (D-08 design) | — | `get_centroid()` returns None, incident skipped |
| BrowserOS MCP | Wave 5 visual verify | Available at `http://127.0.0.1:9200/mcp` (project memory) | — | Manual screenshot fallback |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | DeepSeek pricing ~$0.14/M input, ~$0.28/M output | NEWS-02 scoring | Cost estimate in A/B report would be wrong; doesn't affect correctness |
| A2 | MiniMax pricing for `MiniMax-Text-01` | NEWS-02 scoring | Same — only affects the cost column in the report |
| A3 | The `@data` vite alias resolves at Astro build time for `import` statements in `.astro` frontmatter | NEWS-04 | If wrong, use `fs.readFileSync` with explicit path instead of import |
| A4 | `pipeline/pytest.ini` or similar config exists (test discovery works with `python -m pytest tests/`) | Validation | If pytest config absent, add `-v tests/` or `pyproject.toml [tool.pytest]` section |

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)
- `pipeline/news/classifier.py` — current broken state (bare CUT list, prompt structure)
- `pipeline/news/schema.py` — `IncidentRecord`, `ClassifierOutput`, `IncidentsFile` models
- `pipeline/news/centroids.py` — `get_centroid(cut)` API
- `pipeline/news/store.py` — `build_incident()`, `merge_and_write()`
- `pipeline/news/feeds.py` — `FEEDS` registry
- `pipeline/scrape_news.py` — orchestrator, key check, dotenv loading, exit codes
- `site/scripts/sync-data.mjs` — incidents copy from `data/incidents/` to `site/public/data/incidents/`
- `site/src/components/map/IncidentsList.tsx` — existing `Incident` interface, source link rendering
- `site/src/components/map/IncidentPinLayer.ts` — `fetchAndMountIncidents`, popup HTML, `escHtml`, `safeUrl`
- `site/src/layouts/BaseLayout.astro` — props interface, hreflang injection, `enPath`/`esPath` pattern
- `site/src/components/PageHeader.astro` — nav hardcoded hrefs, localized-slug pattern
- `site/src/config/i18n.ts` — `I18nStrings` interface, `EN_STRINGS`/`ES_STRINGS` maps
- `site/astro.config.mjs` — `sitemapFilter`, `@data` vite alias, i18n config
- `site/src/pages/commune/[slug].astro` — commune page pattern (BaseLayout usage, enPath/esPath)
- `site/src/pages/communes/index.astro` — NFD normalization pattern `s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()`
- `scripts/build-topojson.mjs` — `srcCodeToCut()` deterministic lookup pattern
- `data/cead/meta/index.json` — schema `{cut, name, slug, region_id, population, low_population}` (346 entries)
- `pipeline/tests/fixtures/deepseek_response_sample.json` — existing fixture format
- `.planning/config.json` — `nyquist_validation: true`, `security_enforcement: true`

### Secondary (MEDIUM confidence — CONTEXT.md + project memory)
- CONTEXT.md Wave-0 findings: MiniMax call differences (no `response_format`, `MiniMax-Text-01` model, `api.minimaxi.chat/v1` base URL)
- Project memory `i18n-localized-slug-pitfall.md` — hardcode ES slugs
- Project memory `OneDrive build artifacts desync` — chain build+validate

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all existing modules read directly
- Architecture: HIGH — all integration points verified from source files
- Pitfalls: HIGH — derived from actual code paths, not speculation
- MiniMax call differences: MEDIUM — from CONTEXT.md Wave-0 findings (not re-verified in this session)

**Research date:** 2026-06-18
**Valid until:** 2026-07-18 (stable codebase; MiniMax API may change sooner)

---

## RESEARCH COMPLETE

**Phase:** 16 — News Activation + Geolocation Redesign + Model A/B
**Confidence:** HIGH

### Key Findings

1. **Root cause is in 2 lines of `classifier.py`:** `_CUT_LIST_STR = ",".join(sorted(VALID_CUTS))` (line 34) and the prompt block (lines 64-65). The fix is a new `pipeline/news/resolver.py` module + prompt change — no other pipeline module needs structural changes.

2. **`data/cead/meta/index.json` already has everything the resolver needs:** `{cut, name, slug, region_id}` for all 346 communes. The normalization pattern (NFD + strip Mn category) is established in `site/src/pages/communes/index.astro`.

3. **MiniMax requires removing `response_format` from the API call** — conditional on `_PROVIDER` env var. JSON must be parsed from content string (may include markdown fences).

4. **`IncidentRecord` schema needs `slug: str`** to enable incident→commune links. Make it `Optional` for backwards-compat with any existing `current.json`.

5. **Bilingual news page follows methodology.astro pattern** with hardcoded `enPath="/news/"`, `esPath="/es/noticias/"`. Nav wiring: two hardcoded hrefs in `PageHeader.astro` + one new `nav_news` string in `i18n.ts`.

6. **Sync to site is already wired** — `site/scripts/sync-data.mjs` lines 44-50 already copies `data/incidents/` to `site/public/data/incidents/` as part of prebuild.

### Files Created
`.planning/phases/16-news-activation-geolocation-ab/16-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Geolocation fix pattern | HIGH | Exact lines identified in classifier.py; index.json schema verified |
| A/B harness | HIGH | Existing fixture + test patterns; MiniMax differences from CONTEXT.md |
| Pipeline live run | HIGH | scrape_news.py orchestrator + sync-data.mjs read directly |
| Surfacing/linking | HIGH | IncidentsList.tsx, IncidentPinLayer.ts, BaseLayout all read directly |
| MiniMax specifics | MEDIUM | From CONTEXT.md Wave-0; not re-verified against MiniMax docs this session |

### Open Questions
None that block planning — all integration points mapped.

### Ready for Planning
Research complete. Planner can now create PLAN.md files for all 5 waves.
