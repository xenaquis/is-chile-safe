---
phase: 05-rss-news-pipeline
reviewed: 2026-06-13T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - pipeline/news/schema.py
  - pipeline/news/feeds.py
  - pipeline/news/classifier.py
  - pipeline/news/centroids.py
  - pipeline/news/dedup.py
  - pipeline/news/store.py
  - pipeline/scrape_news.py
  - pipeline/scripts/audit_incidents.py
  - pipeline/scripts/build_centroids.py
findings:
  critical: 4
  warning: 6
  info: 3
  total: 13
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-13T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The pipeline's core anti-hallucination, attribution, and atomic-write requirements are substantially met: the correct model ID (`deepseek-v4-flash`), `temperature=0.0`, `response_format=json_object`, the CUT-set gate, and the confidence gate are all present. The `IncidentsFile` Pydantic schema, `validate_incidents_file` gate, and `atomic_write_json` are wired correctly. The seen-ledger, 30-day window, archive idempotency, and per-feed try/except are all present.

However, four correctness/security defects must be fixed before this ships:

1. The Node script string in `build_centroids.py` is built by string concatenation of file-system paths without escaping — a path containing a single-quote (possible on some CI setups) would break the JS and could allow command injection via a crafted path.
2. `schema.py` loads `VALID_CUTS` at module import time using `_CUT_FILE.read_text()` with no fallback beyond an empty set; if the file is absent, **all CUT codes are silently accepted** by the classifier gate in `classifier.py` (which checks `result.commune_cut not in VALID_CUTS` — the `not in` of an empty set is always False for non-None values... wait — re-checking: `x not in set()` is `True` for any `x`, so the gate would reject everything). Actually the silent-empty-set scenario causes the classifier to **reject every incident** rather than accept hallucinated codes — this is safe-fail directionally, but the silent failure mode is still a correctness problem: the pipeline will silently produce zero incidents with no error log, making it indistinguishable from a successful run with no crime news.
3. The seen-ledger is updated only for **successfully classified** items, but `seen_set` (the in-memory dedup set used during the current run) is updated for **all unseen candidates before classification**. This means if a URL passes keyword filter but is later rejected by the classifier, it will NOT be written to `seen.json` — so the same rejected item will be re-sent to the classifier on every future run, burning API quota indefinitely.
4. `feedparser.parse()` does not have a configurable HTTP timeout — it uses the underlying `urllib` default (which is infinite on Python 3). A single hanging feed will block the entire pipeline run forever.

---

## Critical Issues

### CR-01: Infinite hang on RSS fetch — no HTTP timeout

**File:** `pipeline/news/feeds.py:105`
**Issue:** `feedparser.parse(url, ...)` is called with no timeout. `feedparser` delegates HTTP fetching to `urllib.request.urlopen`, which defaults to `socket.setdefaulttimeout()` or `None` (infinite). A single slow/hanging feed server blocks the entire pipeline run forever in CI, causing the GitHub Actions job to time out at 6 hours (or the runner-level limit), masking the real cause and consuming CI minutes.

**Fix:** Pass `handlers` with a timeout-enforcing opener, or set a global socket timeout at the top of the pipeline entry point before any network call:
```python
# pipeline/scrape_news.py — add near top of main(), before the feeds loop
import socket
socket.setdefaulttimeout(30)  # 30 s per RSS connection
```
Or, more targeted — use a `urllib.request` opener in `fetch_feed`:
```python
import urllib.request
def fetch_feed(name: str, url: str) -> list[Any]:
    try:
        opener = urllib.request.build_opener()
        d = feedparser.parse(
            url,
            agent=USER_AGENT,
            handlers=[urllib.request.HTTPHandler()],
            request_headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        ...
```
The simplest correct fix is `socket.setdefaulttimeout(30)` at the start of `main()`.

---

### CR-02: Rejected candidates re-classified on every run (API quota drain)

**File:** `pipeline/scrape_news.py:148-157` and `223-224`
**Issue:** `seen_set.add(url)` is called for every unseen candidate before classification (line 149), but `seen[item["url"]] = item["date"]` (the persistent ledger update) is called only inside the `if result is not None ... cut is not None ... centroid is not None` success path (lines 223-224). An item that passes keyword filter but is rejected by the classifier (wrong family, low confidence, no CUT, no centroid) is added to the in-memory `seen_set` for this run only. On the next run it is absent from the persisted `seen.json`, so it passes `filter_seen` again, is re-sent to DeepSeek, and re-rejected. This repeats on every run for the lifetime of the article in RSS.

For feeds that publish many non-crime articles with crime keywords (common for "carabinero" or "pdi"), this can consume a large portion of `MAX_CLASSIFICATIONS_PER_RUN` every run on stale rejected content.

**Fix:** Mark rejected URLs as seen in the persistent ledger too, using a sentinel date or the actual pub_date, so they are not re-classified:
```python
# After classify() returns None, still persist the URL so we skip it next run
seen[item["url"]] = item["date"]
rejected += 1
continue
```
Apply similarly after null-cut and missing-centroid rejections. (The "rejected" case does not need to be re-examined — the article content will not change.)

---

### CR-03: VALID_CUTS silently empty when cut_list.json is absent

**File:** `pipeline/news/schema.py:23`
**Issue:**
```python
VALID_CUTS: set[str] = set(json.loads(_CUT_FILE.read_text(encoding="utf-8")) if _CUT_FILE.exists() else [])
```
When `cut_list.json` is absent (fresh checkout, CI without data artifact), `VALID_CUTS` is an empty set. The classifier gate in `classifier.py:119` is:
```python
if result.commune_cut is not None and result.commune_cut not in VALID_CUTS:
    return None
```
With `VALID_CUTS = set()`, every non-None `commune_cut` fails `not in` (is True) and is rejected. The pipeline runs to completion with zero incidents and exit code 0 — indistinguishable from "no crime news today". No error is logged anywhere.

Additionally, the `IncidentRecord.cut_must_be_valid` validator (schema.py:47) uses the same empty set — so even if an incident somehow got through, Pydantic would reject it at the validation gate with a confusing `CUT '13101' not in 346-commune list` error.

**Fix:** Raise at import time if the file is absent, so the failure is loud:
```python
if not _CUT_FILE.exists():
    raise FileNotFoundError(
        f"cut_list.json not found at {_CUT_FILE}. "
        "Run build_centroids.py / data setup before the pipeline."
    )
VALID_CUTS: set[str] = set(json.loads(_CUT_FILE.read_text(encoding="utf-8")))
```

---

### CR-04: Path injection in Node script string (build_centroids.py)

**File:** `pipeline/scripts/build_centroids.py:49-55`
**Issue:** The Node `-e` script is constructed by string concatenation of `topo_posix` and `node_modules` paths:
```python
script = (
    "const topo = require('" + node_modules + "/topojson-client');\n"
    ...
    "const t = JSON.parse(fs.readFileSync('" + topo_posix + "', 'utf8'));\n"
    ...
)
```
If the repository is checked out to a path containing a single-quote (e.g., a user's home directory named `O'Brien` or a CI workspace path), the injected path will break the JS syntax and Node will throw. On an adversarial system where an attacker controls the filesystem path, this could be escalated to JavaScript injection executed by Node. While the paths here are derived from `__file__` (not user input), the pattern is fragile — and on Windows+OneDrive paths this exact repo lives under a path with spaces (per the env block) which, if quoted differently, could cause issues.

**Fix:** Pass the paths as environment variables or command-line arguments to Node rather than inline string interpolation:
```python
result = subprocess.run(
    ["node", "--input-type=module"],
    input=script_template,  # use placeholder strings, inject via env
    env={**os.environ, "TOPO_PATH": str(topo_path), "NM_PATH": node_modules},
    ...
)
```
Or at minimum, escape single-quotes in the paths:
```python
topo_posix_escaped = topo_posix.replace("'", "\\'")
node_modules_escaped = node_modules.replace("'", "\\'")
```

---

## Warnings

### WR-01: Confidence gate does not reject commune_cut=None correctly

**File:** `pipeline/news/classifier.py:127-135`
**Issue:** The confidence threshold check fires for ALL results, including those where `commune_cut is None`. A result with `commune_cut=None` and `confidence=0.9` (e.g., the model is confident it's not a locatable incident) passes the confidence gate and returns a non-None `ClassifierOutput`. The caller in `scrape_news.py:193-196` then correctly handles `cut is None` → reject. This is functionally correct but the SYSTEM_PROMPT instructs: "If the article is not about a crime incident, set commune_cut to null and confidence to 0.0." So a well-behaved model returns `confidence=0.0` for non-crime, which is rejected by the confidence gate. However, if the model returns `confidence=0.7, commune_cut=null` (partially confident it's crime but can't locate it), the item passes `classify()` as a non-None result and is rejected in `scrape_news.py` for null cut — this is correct. The concern is that the confidence gate rejects legitimate locatable incidents when `commune_cut` is valid but `confidence` is 0.55, while allowing through non-locatable items with higher confidence. This asymmetry is by design but the comment on line 127 says "Reject if confidence below threshold" without clarifying the `commune_cut=None` interaction, which will confuse maintainers.

More importantly: the confidence gate currently applies the same `CONFIDENCE_THRESHOLD` regardless of whether `commune_cut` is None or not. A null-cut result with confidence < threshold is also logged as a rejection with "confidence=... < ...". This is misleading — the item would have been rejected anyway for null cut. Minor, but the gate ordering (confidence check before null-cut check in `scrape_news.py`) means some null-cut items are logged under the wrong rejection reason.

**Fix:** Reorder in `scrape_news.py` so null-cut is checked before the confidence gate, or add a note in the classifier that null-cut results with any confidence are valid "not-locatable" outputs and should only be logged as such, not as confidence failures.

---

### WR-02: Dedup buckets keyed on LLM-supplied `date` field (scrape_news.py injected date vs classifier date)

**File:** `pipeline/news/dedup.py:91-103`
**Issue:** Title-similarity dedup is bucketed by `(cut, date)`. The `date` in an incident is the RSS `published_parsed` date (set in `scrape_news.py:155-156` as `pub_date.isoformat()`), not a date from the LLM. However, if two outlets publish the same incident on different UTC dates (e.g., a shooting at 23:50 UTC-3 = 02:50 UTC next day), the bucket split by date means the near-duplicate check never fires — two near-identical articles from BioBio and Cooperativa can both pass into `current.json` with the same `cut` but different `date` values. This is a latent deduplication gap, not a crash, but leads to double-pinning on the map.

**Fix:** Bucket by `cut` alone (dropping the date dimension) to catch cross-day duplicates, or expand to a ±1 day window. Given the plan cites threshold 0.82 as a "start value", the bucket logic should at minimum be documented as a known limitation.

---

### WR-03: `ring_centroid` returns wrong coordinate for degenerate ring

**File:** `pipeline/scripts/build_centroids.py:83-84`
**Issue:** When `abs(area) < 1e-10` (degenerate ring), the fallback is:
```python
return coords[0][1], coords[0][0]
```
This returns `(lat, lng)` from `coords[0]` assuming GeoJSON `[lng, lat]` layout — correct. However, `ring_centroid` is only called from `feature_centroid` which then calls `centroid_in_bbox` on the result. For a degenerate ring with a single repeated point, `centroid_in_bbox` will return True (the point is trivially within its own bounding box), so the early-return is fine. But a degenerate ring with `n < 2` would cause `coords[0]` to exist but `coords[(i+1) % n]` on the first iteration with `n=1` to always be `coords[0]` — the loop still terminates correctly. The edge case of `n=0` (empty ring) would raise `IndexError` at `coords[0]`. This is only possible if the TopoJSON has a polygon feature with zero coordinates, which is malformed, but the code should guard against it.

**Fix:** Add a guard at the top of `ring_centroid`:
```python
if not coords:
    raise ValueError("ring_centroid called with empty coordinate list")
```

---

### WR-04: `parse_pub_date` falls back to `datetime.date.today()` silently

**File:** `pipeline/news/feeds.py:137-149`
**Issue:** When `published_parsed` is absent or unparseable, `parse_pub_date` returns today's date with no warning log. Entries without a publication date — which feedparser returns as `None` for `published_parsed` — are silently assigned today's date. This is especially problematic for archive correctness: an old article re-appearing in an RSS feed without a date will be dated today and stay in the 30-day rolling window longer than it should, or conversely, an undated article that is actually old will inflate the current window.

**Fix:** Log a warning when falling back to today:
```python
if pp:
    try:
        return datetime.datetime(*pp[:6]).date()
    except Exception:
        pass
logger.warning("[parse_pub_date] No valid date for entry; falling back to today()")
return datetime.date.today()
```

---

### WR-05: `save_seen` silently drops entries with malformed dates (data loss)

**File:** `pipeline/news/feeds.py:178-185`
**Issue:** The pruning loop in `save_seen` filters by `_parse_date_str(date_str) >= cutoff`. `_parse_date_str` returns `datetime.date(1970, 1, 1)` for any malformed date string. Since `1970-01-01` is always older than the 60-day cutoff, any entry in `seen.json` with a malformed date value will be silently pruned on the next `save_seen` call. If the pipeline writes a bad date string to `seen` (e.g., due to a bug in `pub_date.isoformat()` — unlikely but possible if `pub_date` is not a `date` object), the URL will be re-processed on the next run.

**Fix:** Log a warning for entries being dropped due to unparseable dates:
```python
def _parse_date_str(date_str: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(date_str)
    except Exception:
        logger.warning("Unparseable date in seen-ledger: %r — treating as epoch (will prune)", date_str)
        return datetime.date(1970, 1, 1)
```

---

### WR-06: `OpenAI` client instantiated at module import time — fails if key absent at import

**File:** `pipeline/news/classifier.py:43-46`
**Issue:**
```python
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)
```
This executes at module import time. `scrape_news.py` checks for an empty key and returns exit code 1 **before** importing `classifier` (line 76-83 checks key, then imports at lines 95-110 inside `main()`). So in `scrape_news.py` the guard works. However, any other script or test that imports `pipeline.news.classifier` directly will instantiate `OpenAI(api_key="", ...)`. Depending on the OpenAI SDK version, this may log a warning or silently succeed (deferring the error to the first actual API call). This is not itself a key-leak, but it means test code that imports the classifier without mocking will attempt DNS resolution to `api.deepseek.com` at import time on some SDK versions.

More critically: if `openai` SDK raises `AuthenticationError` at client construction time for an empty key (behavior varies by version), all test imports will fail with an unrelated-looking error.

**Fix:** Wrap client construction in a function or use lazy initialization:
```python
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com",
        )
    return _client
```

---

## Info

### IN-01: `filter_seen` in feeds.py is not used — scrape_news.py reimplements the check inline

**File:** `pipeline/news/feeds.py:196-198` and `pipeline/scrape_news.py:146-149`
**Issue:** `filter_seen(entries, seen)` is defined in `feeds.py` and exported (it appears in the `from pipeline.news.feeds import ...` import list in `scrape_news.py:98-106`), but `scrape_news.py` does not call `filter_seen()`. Instead it manually checks `if url in seen_set: continue` on line 146. The `filter_seen` function operates on a list of dicts with a `'link'` key, while `scrape_news.py` operates on raw feedparser entry objects and uses `canonical_url()` — so they are not equivalent. `filter_seen` is dead code as shipped.

**Fix:** Either use `filter_seen` (after adapting it to work with the canonical URL and the pre-built `seen_set`), or remove it to avoid confusion about which path is authoritative.

---

### IN-02: Magic number `[:500]` on description truncation in classifier.py

**File:** `pipeline/news/classifier.py:93`
**Issue:** `description[:500]` truncates the description silently with no named constant. Combined with the 512 `max_tokens` limit in the API call, a long description could consume most of the token budget before the model produces output, potentially causing truncated JSON responses (handled by the `JSONDecodeError` catch, but wasteful).

**Fix:** Define `_MAX_DESCRIPTION_CHARS: int = 500` as a named constant alongside `CONFIDENCE_THRESHOLD`, and consider whether 512 `max_tokens` is sufficient for the full response (title_es 120 + title_en 120 + summary 2 sentences + JSON overhead ≈ 350-400 tokens; 512 is borderline).

---

### IN-03: `audit_incidents.py` uses non-seeded `random.sample` — non-deterministic output

**File:** `pipeline/scripts/audit_incidents.py:61-62`
**Issue:** `random.sample(incidents, sample_size)` produces different results on each invocation. This is intentional for spot-checking, but means audit output cannot be reproduced for documentation or regression comparison. Minor for a human UAT tool, but worth noting.

**Fix:** Accept an optional `--seed` CLI argument, or document the non-determinism:
```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--seed", type=int, default=None)
args = parser.parse_args()
if args.seed is not None:
    random.seed(args.seed)
```

---

_Reviewed: 2026-06-13T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
