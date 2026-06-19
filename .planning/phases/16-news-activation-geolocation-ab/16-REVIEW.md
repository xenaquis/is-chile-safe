---
phase: 16-news-activation-geolocation-ab
reviewed: 2026-06-18T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - pipeline/news/resolver.py
  - pipeline/news/classifier.py
  - pipeline/news/schema.py
  - pipeline/news/store.py
  - pipeline/scrape_news.py
  - pipeline/experiments/ab_score.py
  - site/src/components/map/IncidentsList.tsx
  - site/src/components/map/IncidentPinLayer.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
findings:
  critical: 3
  warning: 4
  info: 3
  total: 10
status: resolved
resolution: "All 3 criticals + WR-01/02/03 + IN-01/02 fixed (commits 52dae23, b2f3693, 33a7b3e, 14aa953, 62b488b, 40d662b, 4b263a5); pytest 158 pass; build 12/12. CR-02 (resolver ambiguity→None) + CR-01 (url scheme validation) close the anti-hallucination + injection gaps. IN-03 (sort order) deferred."
---

# Phase 16: Code Review Report

**Reviewed:** 2026-06-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 16 delivers a solid anti-hallucination redesign: the deterministic name→CUT resolver correctly gates hallucinated commune names before they reach the store, `resolve_cut` returns None for unknowns, the seen-URL ledger is written before classification so rejected items do not re-burn quota, and both news pages use `process.cwd()` to avoid the previously broken `import.meta.url` drift. XSS handling in the Leaflet popup is mostly correct and the `safeUrl` guard is a genuine improvement.

Three blockers remain: the source URL from LLM-derived data is rendered unescaped in the Astro news pages (bypassing the `safeUrl` guard that exists in the Leaflet layer); the resolver silently falls back to the first entry when disambiguation fails, allowing the wrong commune to silently win for any genuinely ambiguous normalized name; and `importlib.reload()` inside the A/B harness is inherently unreliable for re-picking a different provider's client — it will silently score the wrong provider in multi-import scenarios.

---

## Critical Issues

### CR-01: `incident.url` rendered unescaped in Astro news pages — javascript: injection via LLM data

**File:** `site/src/pages/news.astro:105-110` and `site/src/pages/es/noticias.astro:105-110`

**Issue:** Both news pages render `incident.url` directly as the `href` of an anchor tag via Astro JSX:

```astro
<a href={incident.url} target="_blank" rel="noopener noreferrer" ...>
```

`incident.url` is LLM-derived data stored in `current.json`. The `IncidentPinLayer.ts` Leaflet layer correctly runs URLs through `safeUrl()` which rejects non-http/https schemes, but the static Astro pages have no equivalent guard. A `javascript:alert(1)` value stored in `url` by a malicious news item would survive JSON storage and be emitted as a live `javascript:` href into the pre-rendered static HTML. Astro's JSX auto-escaping only prevents HTML-entity injection; it does not block protocol-switching href values.

The `url_must_not_be_empty` validator in `IncidentRecord` (schema.py:76-79) only rejects empty strings — it does not validate the URL scheme.

**Fix:**

Add scheme validation to `IncidentRecord.url_must_not_be_empty` in `pipeline/news/schema.py`:

```python
@field_validator("url")
@classmethod
def url_must_not_be_empty(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("url must not be empty (NEWS-05)")
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError(f"url must be http/https, got: {v!r}")
    return v
```

This blocks any non-http/https URL from reaching `current.json`. In the Astro pages, additionally add a build-time guard:

```astro
{incident.slug && (
  <a
    href={incident.url.startsWith('http://') || incident.url.startsWith('https://')
      ? incident.url : '#'}
    ...
  >
```

---

### CR-02: `resolver.py` falls back to first entry when disambiguation fails — wrong commune silently wins

**File:** `pipeline/news/resolver.py:109-111`

**Issue:** When `len(entries) > 1` (normalized name collision) and `region_hint` does not match any entry, the code falls back to `entries[0]` and returns a CUT:

```python
# Fall back to first entry if disambiguation fails
entry = entries[0]
return (entry["cut"], entry["slug"])
```

The docstring for `resolve_cut` promises that `None` is returned for "unknown" names. Returning a non-None result when disambiguation fails violates that contract and assigns the wrong commune's CUT to the incident without any log entry. In the current 346-commune index there may be no normalized collisions, but the code explicitly handles `len(entries) > 1` — meaning the author anticipated it. If a collision exists and `region_hint` is absent or wrong, a hallucinated-by-proximity CUT silently enters the store. This is the exact anti-hallucination failure the redesign was intended to prevent.

**Fix:**

```python
# Disambiguation failed — return None to avoid assigning wrong commune
logger.debug(
    "Ambiguous commune name %r matched %d entries; region_hint=%r did not resolve — dropping",
    name, len(entries), region_hint,
)
return None
```

If a future genuine collision needs resolution it should be handled by adding a region_hint to the prompt, not by silently picking the first entry.

---

### CR-03: `importlib.reload()` in `ab_score.py` does not re-initialize the module-level `client` object — wrong provider may be scored silently

**File:** `pipeline/experiments/ab_score.py:111`

**Issue:** `_run_scoring` calls `importlib.reload(classifier_mod)` to re-pick the provider. However, `reload()` re-executes module-level code only if the module has not already been imported in the same process. Because `ab_score.py` itself sets `os.environ["NEWS_PROVIDER"]` before importing `pipeline.news.classifier`, the first import path works correctly for a single invocation. The bug is: `reload()` at line 111 re-executes the module body, which re-reads `os.environ.get("NEWS_PROVIDER")` — but `resolver.py` and `schema.py` are imported transitively inside `classifier.py` and are NOT reloaded. If those modules raise at import time (e.g., missing index.json), the reload throws and scoring silently never runs. More critically, if `ab_score` is ever called twice in one process (e.g., from a test suite or wrapper script), the already-imported `OpenAI` client instance bound to the first provider is reused because `reload()` does not reset already-bound names in *callers'* namespaces. `classify = classifier_mod.classify` at line 112 captures the newly reloaded function, but the module-level `client` object inside `classifier.py` now points to whatever the reload left behind — which depends on CPython's module dict replacement behavior, not on any stable contract. This is undefined behavior for multi-provider use from a single process.

**Fix:** Run each provider as a separate subprocess invocation, which is already how the usage docs describe it. Remove `importlib.reload()` and add a guard:

```python
# ab_score.py _run_scoring — replace reload pattern:
if "pipeline.news.classifier" in sys.modules:
    print(
        "[ab_score] ERROR: classifier already imported. "
        "Run each provider in a separate process invocation.",
        file=sys.stderr,
    )
    sys.exit(1)
import pipeline.news.classifier as classifier_mod
classify = classifier_mod.classify
```

This makes the failure loud rather than silently scoring the wrong provider.

---

## Warnings

### WR-01: `classifier.py` catches all exceptions from the API call — network details and auth errors invisible in logs

**File:** `pipeline/news/classifier.py:194-196`

**Issue:** `_call_api` wraps the entire `client.chat.completions.create(...)` call in `except Exception as exc` and logs only a single `WARNING` line with the exception string. HTTP 401 (bad API key), HTTP 429 (rate limit), and HTTP 500 (server error) all produce identical log lines with no differentiation. In a GitHub Actions cron run where the key might be rotated or the account suspended, every item will log "API call failed" at WARNING, total classified=0, and the pipeline will exit 0 — appearing clean. The scrape_news.py key-presence check (line 89-97) only verifies the key is non-empty, not that it is valid.

**Fix:** Differentiate HTTP status codes from the openai SDK's exception hierarchy:

```python
from openai import AuthenticationError, RateLimitError, APIStatusError
except AuthenticationError:
    logger.error("%s API call: authentication failed — check %s_API_KEY", _PROVIDER, _PROVIDER.upper())
    return None
except RateLimitError:
    logger.warning("%s API call: rate limited — will retry next run", _PROVIDER)
    return None
except APIStatusError as exc:
    logger.warning("%s API call failed HTTP %s: %s", _PROVIDER, exc.status_code, exc.message)
    return None
except Exception as exc:
    logger.warning("%s API call failed (unexpected): %s", _PROVIDER, exc)
    return None
```

---

### WR-02: `schema.py` loads `cut_list.json` from `data/incidents/` but `resolver.py` loads `index.json` from `data/cead/meta/` — two sources of truth for valid CUTs

**File:** `pipeline/news/schema.py:22-30`

**Issue:** `IncidentRecord.cut_must_be_valid` validates against `VALID_CUTS` loaded from `data/incidents/cut_list.json`. `resolver.py` builds its lookup from `data/cead/meta/index.json`. If these two files ever diverge (e.g., cut_list.json is stale or a new commune is added to index.json but not cut_list.json), a CUT that `resolver.py` resolves correctly will be rejected by `IncidentRecord` validation at write-time and silently dropped — logged as a ValidationError with no actionable cause. The CUT that `resolver.py` resolves is always derived from `index.json`; `cut_list.json` is a redundant derived artifact.

**Fix:** Derive `VALID_CUTS` from the same `index.json` that `resolver.py` uses:

```python
# schema.py — replace cut_list.json loading with:
_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
VALID_CUTS: set[str] = {entry["cut"] for entry in json.loads(_INDEX_FILE.read_text(encoding="utf-8"))}
```

This eliminates the dual source of truth and ensures the validator and resolver are always aligned.

---

### WR-03: `IncidentsList.tsx` renders `incident.url` as href without scheme validation — same vector as CR-01

**File:** `site/src/components/map/IncidentsList.tsx:40-45`

**Issue:** The React `IncidentsList` component renders `e.url` directly as the anchor href:

```tsx
<a href={e.url} target="_blank" rel="noopener noreferrer" ...>
```

React's JSX escaping prevents HTML injection but does not block `javascript:` scheme hrefs. This is the same vector as CR-01 in the Astro pages. If the React panel is rendered with incidents loaded from `current.json` (where a `javascript:` URL survived schema validation), the link is live. The fix applied to `schema.py` in CR-01 eliminates the root cause; this component should also add a prop-level guard for defense-in-depth:

**Fix:**

```tsx
const safeHref = (url: string) =>
  url.startsWith('http://') || url.startsWith('https://') ? url : '#';

// then:
<a href={safeHref(e.url)} target="_blank" rel="noopener noreferrer" ...>
```

---

### WR-04: `store.py` uses `datetime.datetime.now(datetime.timezone.utc)` twice in one `merge_and_write` call — archive and current timestamps may differ

**File:** `pipeline/news/store.py:157` and `store.py:175`

**Issue:** The `generated` timestamp is computed independently for the archive payload (line 157) and the current.json payload (line 175). In practice the difference is microseconds, but if the function ever takes longer (large archive merge), two calls to `merge_and_write` in the same pipeline run will produce slightly different timestamps in archive vs. current, making forensic comparison harder than needed.

**Fix:** Capture one timestamp at the top of the function:

```python
_now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
# then use _now_iso for both payloads
```

---

## Info

### IN-01: `classifier.py` module-level client initialization runs at import time — any import of `classifier` fails loudly if index.json is absent

**File:** `pipeline/news/classifier.py:68-72`

**Issue:** `_INDEX_FILE.read_text()` runs at module load time. If `data/cead/meta/index.json` is absent (e.g., a fresh clone before `scrape_cead` has run), importing `pipeline.news.classifier` raises an exception, which propagates through any test that imports the module. This is consistent with `resolver.py`'s behavior (also loads at import time), but worth noting for CI bootstrap documentation.

**Fix:** Add a `FileNotFoundError` guard matching the pattern in `resolver.py` lines 23-27, with an actionable error message.

---

### IN-02: `ab_score.py` commune_accuracy metric compares predicted_cut == ground_truth.cut but golden set stores `cut` not `commune_name` — metric definition mismatch with NEWS-01 redesign

**File:** `pipeline/experiments/ab_score.py:148`

**Issue:** The redesign changed the LLM from emitting CUT codes to emitting commune names. The harness correctly resolves `commune_name → cut` via `resolve_cut`. However the `commune_accuracy` metric label and the `ground_truth["cut"]` field in the golden set implies the golden set was authored with raw CUT values. If the golden set was written before the redesign (when the LLM emitted CUTs directly), and `ground_truth["commune_name"]` is used to filter labelled vs null items (line 119), a golden set with `commune_name: null` but `cut: "13101"` would be misclassified as a null item and excluded from commune_accuracy scoring. The metric docstring says `commune_name is not None` gates labelled items, which is correct, but golden set authoring instructions should explicitly require both fields.

**Fix:** Add a validation check at golden set load time:

```python
for item in golden:
    gt = item["ground_truth"]
    if gt.get("commune_name") is not None and not gt.get("cut"):
        print(f"[ab_score] WARNING: item {item['id']} has commune_name but no cut — commune_accuracy will be wrong", file=sys.stderr)
```

---

### IN-03: `news.astro` and `noticias.astro` sort order is undefined — newest incidents not guaranteed first

**File:** `site/src/pages/news.astro:97` and `site/src/pages/es/noticias.astro:99`

**Issue:** `incidents` is rendered in the order returned from `current.json`, which is the insertion order from `merge_and_write`. Because `_merge_by_id` preserves existing order and appends new items at the end, the most recent incidents may appear at the bottom of the page rather than the top. For a news page, readers expect reverse-chronological order.

**Fix:**

```astro
// After loading incidents:
incidents = incidents.sort((a, b) => b.date.localeCompare(a.date));
```

---

_Reviewed: 2026-06-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
