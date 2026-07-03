---
phase: quick-260703-fjh
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pipeline/news/feeds.py
  - pipeline/scrape_news.py
  - pipeline/tests/fixtures/feed_googlenews_sample.xml
  - pipeline/tests/test_feeds.py
  - pipeline/tests/test_dedup.py
autonomous: true
requirements: [NEWS-01, NEWS-03, NEWS-05]

must_haves:
  truths:
    - "The pipeline fetches Google News RSS queries (1 national + regional) and La Cuarta in addition to the 3 existing feeds"
    - "Incidents sourced via Google News are attributed to the ORIGINAL outlet (from the feed <source> tag), never to 'Google News'"
    - "A Google News redirect URL is stored as the incident link and still lands on the source article"
    - "The same crime story reported by multiple outlets (same commune + date) collapses to a single pin"
    - "The incident data contract (id, cut, lat, lng, title_es, title_en, date, outlet, url, family, slug) is unchanged"
  artifacts:
    - path: "pipeline/news/feeds.py"
      provides: "Extended FEEDS registry (La Cuarta + Google News queries), google_news_url() builder, resolve_outlet() source-tag extractor, Google-News-aware canonical_url()"
      contains: "def resolve_outlet"
    - path: "pipeline/tests/fixtures/feed_googlenews_sample.xml"
      provides: "Google News RSS sample with <source> tags + redirect links + multi-outlet duplicate story"
      contains: "<source"
  key_links:
    - from: "pipeline/scrape_news.py"
      to: "pipeline/news/feeds.py resolve_outlet"
      via: "outlet field assignment in candidate build"
      pattern: "resolve_outlet"
    - from: "pipeline/news/feeds.py FEEDS"
      to: "news.google.com/rss/search"
      via: "google_news_url() entries"
      pattern: "news\\.google\\.com/rss/search"
---

<objective>
Expand the news pipeline's source coverage without changing the incident data contract or touching the frontend.

Add two verified-live source types to the FEEDS registry:
1. **Google News RSS** — one national crime query plus region-targeted queries for underserved regions (≤5 pins today), surfacing regional outlets that have no own RSS.
2. **La Cuarta** — an Arc-platform feed (same shape as the working LaTercera feed), crónica-roja heavy.

The one genuinely new behavior is **source attribution for Google News**: item links are `news.google.com` redirects, so the incident's `outlet` must come from each item's `<source>` tag (the original outlet name) rather than the feed name. Cross-outlet deduplication (same story from N outlets) already exists in `dedup.py` — this plan verifies it under a Google-News multi-outlet scenario and locks it with a test.

Purpose: Reduce Región Metropolitana over-concentration (46% today) and fill the 8 regions with ≤5 pins, using free, courteous RSS.
Output: Extended feed registry + source-aware outlet resolution + fixture-backed tests. No workflow, schema, or frontend changes.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@./CLAUDE.md
@pipeline/news/feeds.py
@pipeline/scrape_news.py
@pipeline/news/dedup.py
@pipeline/tests/test_feeds.py
@pipeline/tests/fixtures/feed_latercera_sample.xml

<interfaces>
<!-- Contracts the executor works against — no codebase exploration needed. -->

From pipeline/news/feeds.py:
```python
FEEDS: dict[str, str]                      # name -> url; simple string map, DO NOT change shape
USER_AGENT: str                            # politeness header, reuse as-is
def canonical_url(entry, feed_name: str) -> str   # per-feed URL selection (BioBio uses .link, else .id)
def fetch_feed(name, url) -> list           # graceful [] on error, sets USER_AGENT — reuse unchanged
def is_crime_item(item: dict) -> bool       # keyword prefilter — reuse unchanged
```

From pipeline/scrape_news.py (the wiring point, ~lines 154-181):
```python
url = canonical_url(entry, feed_name)
...
candidates.append({
    "url": url, "title": title, "description": description,
    "date": pub_date.isoformat(),
    "outlet": feed_name,          # <-- MUST become resolve_outlet(entry, feed_name)
})
```

From pipeline/news/dedup.py (already handles cross-outlet — verify, do NOT change threshold):
```python
def deduplicate(incidents: list[dict]) -> list[dict]
# Phase 1: canonical-URL dedup (strips utm_*). Phase 2: difflib title-similarity
# >= 0.82 within (cut, date) buckets. Multi-outlet same-day same-commune story -> 1 pin.
```

feedparser maps `<source url="X">Name</source>` to `entry.source`, a FeedParserDict with
keys `title` (the text "Name") and `href` (the url attr). Access defensively:
`getattr(entry, "source", None)` then `.get("title")`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Register Google News + La Cuarta feeds and add source-aware outlet resolution</name>
  <files>pipeline/news/feeds.py, pipeline/scrape_news.py</files>
  <behavior>
    - resolve_outlet(entry, "LaCuarta") returns "LaCuarta" (non-Google feeds pass through the feed name unchanged).
    - resolve_outlet(entry, "GoogleNews-Nacional") returns the text of the item's <source> tag (e.g. "Puranoticia").
    - resolve_outlet(entry, "GoogleNews-Nacional") returns "Google News" as fallback when no <source> tag / empty title is present.
    - canonical_url(entry, "GoogleNews-Nacional") returns the redirect link (entry.link), not the opaque entry.id guid.
    - google_news_url("homicidio chile when:2d") returns a URL beginning "https://news.google.com/rss/search?q=" with the query percent-encoded and "&hl=es-419&gl=CL&ceid=CL:es-419" appended.
    - FEEDS still contains the original 3 keys plus "LaCuarta" plus the GoogleNews-* query keys.
  </behavior>
  <action>
    In pipeline/news/feeds.py:
    (a) Add `google_news_url(query: str) -> str` using `urllib.parse.quote(query, safe="")` to encode the query, formatted as `https://news.google.com/rss/search?q={q}&hl=es-419&gl=CL&ceid=CL:es-419`. Google News expects the standard reserved chars encoded; do not pre-encode spaces yourself — let quote handle it.
    (b) Define a module-level `_GOOGLE_NEWS_QUERIES: dict[str, str]` mapping feed name -> query string. Use one national query and four region-targeted queries aimed at pin-scarce regions per audit findings: "GoogleNews-Nacional" -> `homicidio OR balacera OR portonazo OR "crimen organizado" chile when:2d`; "GoogleNews-Antofagasta" -> `(homicidio OR balacera OR robo OR portonazo) (Antofagasta OR Calama OR Tocopilla) when:3d`; "GoogleNews-Tarapaca" -> `(homicidio OR balacera OR robo) (Iquique OR "Alto Hospicio" OR Tarapaca) when:3d`; "GoogleNews-Coquimbo" -> `(homicidio OR balacera OR robo) ("La Serena" OR Coquimbo OR Ovalle) when:3d`; "GoogleNews-Araucania" -> `(homicidio OR balacera OR robo OR atentado) (Temuco OR Araucania OR Angol) when:3d`. Regional queries use when:3d (wider window for low-volume regions; the seen-ledger + dedup absorb the daily overlap).
    (c) Add "LaCuarta": "https://www.lacuarta.com/arc/outboundfeeds/rss/?outputType=xml" to FEEDS, then splat the Google News entries: `**{name: google_news_url(q) for name, q in _GOOGLE_NEWS_QUERIES.items()}`. Keep FEEDS a flat dict[str, str] — the registry shape must not change (canonical_url/fetch_feed/orchestrator all depend on it).
    (d) Extend `canonical_url`: when `feed_name.startswith("GoogleNews")`, return `getattr(entry, "link", "") or ""` (the redirect URL — it is stable per article and lands on the original source). Leave BioBio and default branches untouched. La Cuarta is Arc-platform like LaTercera and correctly uses the existing default (entry.id) branch — no special case needed.
    (e) Add `resolve_outlet(entry, feed_name: str) -> str`: for non-Google feeds return `feed_name` unchanged (preserves current behavior for BioBio/Cooperativa/LaTercera/LaCuarta). For `feed_name.startswith("GoogleNews")`, read `src = getattr(entry, "source", None)`; extract a title via `src.get("title")` when src is dict-like else `getattr(src, "title", "")`; strip it and return it if truthy, else return the constant "Google News". Do NOT perform any extra HTTP request to resolve the redirect — the stored redirect URL already lands on the source (simplest correct MVP option per audit).

    In pipeline/scrape_news.py:
    (f) Import `resolve_outlet` alongside the existing `from pipeline.news.feeds import (...)` block.
    (g) In the candidate-build dict (~line 175-181), change `"outlet": feed_name` to `"outlet": resolve_outlet(entry, feed_name)`. This is the only change in this file — the D-17 cap, seen-ledger, and dedup call all stay as-is.
    Do NOT modify: the incident schema, merge_and_write, the news cron workflow, or anything under site/. No new dependencies (feedparser/tenacity already present).
  </action>
  <verify>
    <automated>python -m pytest pipeline/tests/test_feeds.py -x -q</automated>
  </verify>
  <done>feeds.py exports google_news_url and resolve_outlet; FEEDS contains LaCuarta + 5 GoogleNews-* keys with news.google.com/rss/search URLs; scrape_news.py sets outlet via resolve_outlet(entry, feed_name); existing test_feeds.py still passes.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Fixture + tests for source attribution, redirect link, and cross-outlet dedup</name>
  <files>pipeline/tests/fixtures/feed_googlenews_sample.xml, pipeline/tests/test_feeds.py, pipeline/tests/test_dedup.py</files>
  <behavior>
    - resolve_outlet extracts "Puranoticia" (or similar) from a Google News item's <source> tag.
    - resolve_outlet falls back to "Google News" for an item with no <source> tag.
    - canonical_url(entry, "GoogleNews-Nacional") returns the news.google.com redirect link, not the guid.
    - deduplicate collapses three near-duplicate incidents of the SAME homicide from three different outlets (same cut + same date, titles varying by outlet phrasing) down to one, while a genuinely distinct incident in the same bucket survives.
  </behavior>
  <action>
    Create pipeline/tests/fixtures/feed_googlenews_sample.xml modeled on feed_latercera_sample.xml but in Google News RSS shape: 3+ <item>s where each has (i) a <link> of the form https://news.google.com/rss/articles/CBMi<opaque>?oc=5, (ii) a <guid isPermaLink="false"> holding the opaque CBMi... id (DIFFERENT from the link), (iii) a <source url="https://<outlet-domain>">Outlet Name</source> child, (iv) a crime <title> and <description> that pass CRIME_KEYWORDS. Include at least: one item from "Puranoticia" (a homicidio), and one item with NO <source> tag (fallback case). Keep it valid RSS 2.0 with a <channel> wrapper.

    In pipeline/tests/test_feeds.py: add a `googlenews_xml` fixture that reads the file (skip if absent, mirroring biobio_xml). Add tests importing `resolve_outlet` and `canonical_url` from pipeline.news.feeds:
    - test_googlenews_outlet_from_source: parse fixture with feedparser, assert resolve_outlet(entry, "GoogleNews-Nacional") equals the <source> title for the Puranoticia item.
    - test_googlenews_outlet_fallback: assert resolve_outlet(entry_without_source, "GoogleNews-Nacional") == "Google News".
    - test_googlenews_canonical_url_is_link: assert canonical_url(entry, "GoogleNews-Nacional") == entry.link and startswith "https://news.google.com/rss/".
    - test_non_google_outlet_passthrough: assert resolve_outlet(any_entry, "LaCuarta") == "LaCuarta".

    In pipeline/tests/test_dedup.py: add test_cross_outlet_google_news_dedup — build three incident dicts for the same homicide (same cut e.g. "02101", same date, family "vida") with outlets "Puranoticia", "ADPrensa", "Canal 9 Biobío" and near-duplicate title_es phrasings (ratio >= 0.82), plus one clearly distinct incident in the same (cut, date) bucket. Assert deduplicate([...]) yields exactly 2 (the merged homicide + the distinct one). Do NOT change dedup.py or its 0.82 threshold — this test only verifies existing behavior covers the Google-News multi-outlet case.
  </action>
  <verify>
    <automated>python -m pytest pipeline/tests/test_feeds.py pipeline/tests/test_dedup.py -x -q</automated>
  </verify>
  <done>New fixture exists; the four feeds tests and the cross-outlet dedup test pass; no change to dedup.py logic.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| external RSS (Google News, La Cuarta) → pipeline | Untrusted third-party feed content (titles, links, source tags) enters the pipeline |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-fjh-01 | Spoofing | Google News `<source>` outlet attribution | accept | Outlet name is taken verbatim from Google's feed; Google is the trusted aggregator. Redirect URL still lands on the real source, so mis-attribution risk is low and self-correcting when a user clicks through. |
| T-fjh-02 | Tampering/Injection | feed title/description → DeepSeek classifier → stored title_es/title_en | mitigate | Classifier rewrites titles into a constrained schema; store validates via pydantic (validate_incidents_file). No raw feed HTML reaches storage — strip_html already applied. |
| T-fjh-03 | Elevation/SSRF | redirect + article URLs stored as incident.url | mitigate | store.is_safe_url() already rejects any non-http(s) scheme before write; Google redirect URLs are https. No extra HTTP hop is made to resolve redirects (avoids SSRF surface entirely). |
| T-fjh-04 | Denial of Service | 5 extra Google News fetches per daily cron run | accept | Each query = 1 bounded HTTP fetch (socket timeout 30s already set); when:2d/3d windows cap item volume; MAX_CLASSIFICATIONS_PER_RUN (200) bounds DeepSeek cost; seen-ledger drains backlog across daily runs. |
| T-fjh-SC | Tampering | package installs | mitigate | No new packages — feedparser/tenacity/openai already present. Package legitimacy gate N/A. |
</threat_model>

<verification>
- `python -m pytest pipeline/tests/test_feeds.py pipeline/tests/test_dedup.py -x -q` passes.
- Full regression (recommended): `python -m pytest pipeline/tests -q` stays green (179 historically).
- OPTIONAL live smoke (must NOT commit data): set a temp output dir so real data/incidents is untouched, e.g. Bash: `NEWS_DATA_DIR=$(mktemp -d) python pipeline/scrape_news.py`. With no DEEPSEEK_API_KEY it exits 0 cleanly (graceful skip); with a key it writes only to the temp dir. Confirm logs show the new feeds fetched and outlets resolved to real outlet names, then discard the temp dir. Do not stage or commit any data/ change from a smoke run.
</verification>

<success_criteria>
- FEEDS registry contains the original 3 feeds + LaCuarta + 5 Google News query feeds, all as flat name→url strings.
- Google-News-sourced incidents carry the original outlet name (from `<source>`), with the redirect URL as the link.
- Cross-outlet duplicate stories (same commune + date) collapse to one pin, proven by test.
- Incident data contract, dedup threshold, news cron workflow, and site/ are all unchanged.
- Test suite green.
</success_criteria>

<output>
Create `.planning/quick/260703-fjh-expand-news-sources-add-google-news-rss-/260703-fjh-SUMMARY.md` when done.
</output>
