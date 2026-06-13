# Phase 5: RSS News Pipeline - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss (4 grey areas, all accepted with recommended values)

<domain>
## Phase Boundary

The qualitative layer of the platform: a Python pipeline that ingests RSS from confirmed Chilean press feeds, uses DeepSeek v4-flash to classify each crime news item (crime type, commune against the closed 346 canonical list, bilingual headline, summary), deduplicates across sources, and publishes a rolling `data/incidents/current.json` that the Phase-3 map island's `IncidentPinLayer` already consumes. Built on the Phase-1 Python pipeline foundation (`pipeline/shared/`, Pydantic v2 schema gate, atomic write, pytest infra) and the Phase-1 canonical commune catalog.

Requirements: NEWS-01, NEWS-02, NEWS-03, NEWS-04, NEWS-05.

**Out of this phase:**
- The map island / pin rendering — already built in Phase 3 (`IncidentPinLayer.ts`); this phase only PRODUCES the data file it reads.
- GitHub Actions cron scheduling + Cloudflare deploy hook — Phase 6 (this phase makes the pipeline runnable; Phase 6 automates it).
- Editorial pages / AdSense (Phase 4); CEAD quantitative scraper (Phase 1, reused not rebuilt).

</domain>

<decisions>
## Implementation Decisions

### RSS Ingestion & Cost Control
- **D-01:** LLM input = **headline + RSS `<description>`/summary only** — no full-article fetch/scrape (cost + scraping politeness).
- **D-02:** **Keyword pre-filter** (e.g. robo, homicidio, asalto, delito, hurto, balacera, femicidio, narco, portonazo…) applied before classification — clearly non-crime items are skipped without an API call.
- **D-03:** **Seen-URL ledger** (e.g. `data/incidents/seen.json` or pipeline cache) — already-processed article URLs are skipped to avoid re-classifying and to bound API cost.
- **D-04:** Polite fetch: **custom User-Agent, ~10s timeout, tenacity retry**, and **per-feed try/except** so one down/changed feed is skipped + logged without blocking the run (NEWS-01).

### DeepSeek Classification & Geolocation
- **D-05:** Model = **deepseek-v4-flash** (NEWS-02 / CLAUDE.md; never the deprecated `deepseek-chat`/`deepseek-reasoner` IDs). openai SDK with `base_url="https://api.deepseek.com"`, key from `DEEPSEEK_API_KEY` env/secret.
- **D-06:** **Strict JSON output**, Pydantic v2-validated: `{commune_cut, family, title_es, title_en, summary, confidence}`. Temperature 0.0.
- **D-07:** **Closed list of 346 canonical CUT codes embedded in the prompt** (from the Phase-1 catalog). Incident is **rejected** (not committed) if the model returns no exact CUT from the list OR `confidence` is below a threshold (NEWS-02).
- **D-08:** **Pin coordinates are deterministic commune centroids** precomputed once per CUT from the Phase-3 GADM-L3 TopoJSON — the LLM NEVER emits lat/lng (eliminates coordinate hallucination). `lat`/`lng` in the output come from the centroid lookup.
- **D-09:** Crime type maps to the **7 CEAD families** (vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades) for consistency with the choropleth `family` key.

### Dedup, Retention & Store
- **D-10:** **Cross-source dedup is heuristic** (NEWS-03): canonical-URL match + normalized-title similarity within the same commune + date window. No extra LLM call for dedup.
- **D-11:** **Incident `id` = deterministic hash of the source URL** so pins are stable across runs.
- **D-12:** **Retention (NEWS-04):** each run drops incidents older than 30 days from `current.json` and appends them to `archive/YYYY-MM.json` (monthly). `current.json` carries `window_days` and `generated` timestamp.
- **D-13:** **Output path = `data/incidents/current.json`** (the exact Phase-3 contract; synced to `public/data` by the existing `sync-data.mjs` prebuild) + `data/incidents/archive/YYYY-MM.json`.

### Orchestration, Validation & Audit
- **D-14:** **Module layout:** `pipeline/news/` (feeds/RSS client, classifier, dedup, store) + `pipeline/scrape_news.py` orchestrator, mirroring `pipeline/scrape_cead.py`; reuse `pipeline/shared/atomic_write.py` and the Pydantic v2 schema pattern.
- **D-15:** **Validation gate:** a Pydantic v2 incident schema enforces every published incident has a valid CUT, a valid family, outlet, source URL, date (NEWS-05 attribution), and centroid lat/lng. Atomic write; the batch is rejected / last-good preserved on schema violation. Output must exactly match the `IncidentsFile`/`Incident` TS interface in `IncidentPinLayer.ts`.
- **D-16:** **50-incident manual audit (success criterion #5):** a `pipeline/scripts/audit_incidents.py` dumps 50 random published incidents (title, outlet, source URL, assigned commune) for human spot-check — this is the phase's human-UAT gate before the pipeline is "production-ready".
- **D-17:** **API cost guardrail:** dedup + keyword pre-filter + seen-ledger minimize calls; a per-run classification cap bounds cost. `DEEPSEEK_API_KEY` read from env (dotenv in dev, repo secret in CI).

### Claude's Discretion
- Exact keyword pre-filter list and confidence threshold value (tune during research/planning).
- Exact RSS feed endpoint URLs (confirm live during research — see NEWS-01 sources; STATE flags some outlet URLs unconfirmed).
- Centroid computation method (polygon centroid vs label-point) from the TopoJSON.
- Title-similarity algorithm/threshold for dedup.
- Whether the seen-ledger lives in `data/` (committed) or `pipeline/cache/` (gitignored).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — NEWS-01..05 (confirmed feeds, closed-list classification, dedup, 30-day retention, attribution).
- `site/src/components/map/IncidentPinLayer.ts` — **the LOCKED output contract**: `IncidentsFile`/`Incident` TS interfaces (`generated`, `window_days`, `incidents[]` with id/cut/lat/lng/title_es/title_en/date/outlet/url/family). The pipeline output MUST match this exactly.
- `pipeline/scrape_cead.py` + `pipeline/cead/` — orchestrator + client/catalog/parser/normalizer patterns to mirror.
- `pipeline/shared/atomic_write.py`, `pipeline/shared/schema.py` — reuse atomic write + Pydantic v2 schema gate.
- `pipeline/cead/catalog.py` — the canonical 346-commune CUT list for the closed-list prompt.
- `pipeline/tests/conftest.py` — pytest fixtures/infra to extend.
- Phase-3 GADM-L3 TopoJSON (346-commune boundaries, ~87KB) — source for per-CUT centroid lat/lng.
- `CLAUDE.md` — DeepSeek model IDs (v4-flash; never deepseek-chat), openai SDK + base_url pattern, feedparser, tenacity, python-dotenv; scraping courtesy; source attribution editorial rule.
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — Pydantic v2-only, temp 0.0 closed-list anti-hallucination decision, atomic-write/last-good-preserved pattern.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/shared/atomic_write.py` — atomic JSON write with last-good preservation (reuse for current.json + archives).
- `pipeline/shared/schema.py` — Pydantic v2 schema-gate pattern (extend with an Incident model).
- `pipeline/cead/catalog.py` — canonical 346-commune catalog (source of the closed CUT list).
- `pipeline/cead/client.py` — HTTP client w/ tenacity retry + courtesy delays (pattern for the RSS fetcher).
- `pipeline/scrape_cead.py` — orchestrator skeleton to mirror for `scrape_news.py`.
- `pipeline/tests/` — pytest infra + fixtures (`conftest.py`) to extend with feed/classifier fixtures.

### Established Patterns
- Pydantic v2 exclusively (no v1 `@validator`/`parse_obj`).
- Validation gate rejects on count/key/range violations; last-good JSON preserved.
- DeepSeek via openai SDK (`base_url`), tenacity backoff, python-dotenv in dev / repo secret in CI.

### Integration Points
- Output `data/incidents/current.json` is consumed by Phase-3 `IncidentPinLayer` (already shipped) and synced to `public/data` by `site/scripts/sync-data.mjs`.
- Phase 6 will schedule `scrape_news.py` via GitHub Actions cron (every 4–6h) + Cloudflare deploy hook on data change.

</code_context>

<specifics>
## Specific Ideas

- Output schema is non-negotiable — it must deserialize into the `Incident` TS interface already written in Phase 3 (bilingual `title_es`/`title_en`, `cut`, `family`, centroid `lat`/`lng`, `outlet`, `url`, `date`).
- Anti-hallucination is the central risk (CLAUDE.md pitfall): closed 346-CUT list at temp 0.0, reject-on-no-match, deterministic centroids, and the 50-incident manual audit gate are the layered mitigations.
- Editorial/legal rule: every incident cites + links its source outlet with date (NEWS-05); never editorialize beyond the source.

</specifics>

<deferred>
## Deferred Ideas

- GitHub Actions cron scheduling + Cloudflare deploy hook for the news pipeline — Phase 6.
- Additional/secondary feeds beyond the 3 confirmed (T13, 24Horas, Meganoticias, SoyChile) — only if the 3 confirmed feeds underperform; STATE flags their URLs unconfirmed.
- Incident detail pages / per-incident SEO pages — not in scope (v2).

</deferred>

---

*Phase: 5 - RSS News Pipeline*
*Context gathered: 2026-06-13 (autonomous smart-discuss)*
