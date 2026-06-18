# Phase 16: News Activation + Geolocation Redesign + Model A/B - Context

**Gathered:** 2026-06-18 (discuss artifact pre-staged for autonomous run)
**Status:** Ready to plan. Runs AFTER Phase 17 (source registry + methodology
must be authoritative first — D-ORDER).
**Milestone:** v1.2 (final phase — "activar noticias")
**Requirements:** NEWS-01, NEWS-02, NEWS-03, NEWS-04

> ## Run context (autonomous)
> - **API keys WILL be available** (`DEEPSEEK_API_KEY`, `MINIMAX_API_KEY` in the
>   gitignored repo `.env`). The pipeline live-run (NEWS-03) and the DeepSeek-vs-
>   MiniMax A/B (NEWS-02) are IN SCOPE for this run. The pipeline already exits 0
>   gracefully if a key is absent (commit b2ad8f8) — if keys are missing at run
>   time, do the no-key parts (frontend NEWS-04 + geolocation redesign code +
>   golden set) and leave the live run/A-B as a checkpoint.
> - Use **BrowserOS** to verify the news page + incident pins + incident→source
>   and incident→comuna links render correctly in a real browser (EN+ES).

<domain>
## Phase Boundary

Turn the built-but-dark news layer on: fix geolocation accuracy, pick the LLM
provider on evidence, run the pipeline for real, and surface incidents linked
across the site with clickable sources.

## What already exists (verify, don't rebuild)
- `pipeline/news/` — feeds, classifier, dedup, store, centroids, schema +
  `pipeline/scrape_news.py` orchestrator. Centroid geolocation from CUT is the
  anti-hallucination design — KEEP it; only the CUT *selection* is broken.
- `site/src/components/map/IncidentsList.tsx` — already renders a clickable
  **"Fuente: {outlet}"** link (`rel="noopener noreferrer"`, no
  dangerouslySetInnerHTML). Extend it (add comuna link), don't replace.
- `site/src/components/map/IncidentPinLayer.ts` — map incident pin layer.
- Incident schema: `{id, title_es, title_en, date, outlet, url}` — extend with
  the resolved comuna (cut + slug) for the comuna link.
- There is **no dedicated news page** and **no incident→comuna link** yet.

## Known findings (Wave-0-equivalent smoke test, 2026-06-15)
- **Geolocation design is the bottleneck, not the vendor.** Both DeepSeek and
  MiniMax classify the crime *family* well but pick the **wrong comuna CUT
  ~60–70%** of the time, because `pipeline/news/classifier.py` hands the model
  346 **bare CUT codes with no names** → it recalls "Las Condes=13114" from
  memory and fails.
- Confidence is uncalibrated (0.9–1.0 while wrong) → the 0.6 threshold won't
  filter bad cases on its own.
- **MiniMax that works:** model `MiniMax-Text-01` @ `https://api.minimaxi.chat/v1`
  (international host). Does NOT support `response_format={"type":"json_object"}`
  (400) — parse JSON from content. `deepseek-v4-flash` gave 3/10 empty/truncated
  JSON (prod retry rescues some).
- No labelled golden set exists yet (only 1 fixture).

## In Scope
1. **NEWS-01 — Geolocation redesign:** LLM emits the comuna **NAME** (+ region
   hint), resolved by a **deterministic name→CUT lookup** (mirror the geometry
   re-key `srcCodeToCut`; accent-insensitive, like the comuna finder). Keep
   centroid-from-CUT for coordinates. Measure accuracy vs the golden set; beat
   the bare-CUT baseline.
2. **NEWS-02 — Golden set + A/B:** build a labelled golden set (30–50 real
   incidents with ground-truth comuna + family) + a scoring script; provider is
   env-configurable; A/B DeepSeek vs MiniMax on comuna accuracy, family
   accuracy, latency, cost, output reliability; document the winner + wire as
   default.
3. **NEWS-03 — Live run:** run the pipeline for real (keys available) →
   `data/incidents/current.json`; map pins + comuna "recent incidents" render
   real, correctly-geolocated incidents, no console errors.
4. **NEWS-04 — Surfacing + linking:** each incident links to its source ↗ AND
   to its comuna page; a dedicated bilingual news page (EN `/news/`, ES
   `/es/noticias/`); a freshness indicator ("updated …"); every incident cites
   and links its press source (editorial policy).

## Out of Scope
- Composite crime index / metric redesign (Phase 17 / future Phase 18).
- Go-live infra cutover (DEPLOYMENT.md; human gate).
</domain>

<decisions>
## Decisions (locked with user 2026-06-18)
- **Keys available** → run live pipeline + A/B in this autonomous run.
- **Geolocation:** name-emit + deterministic name→CUT (do NOT just switch
  models — that won't fix it). Keep centroid-from-CUT for coordinates.
- **Reuse**, don't rebuild: extend `IncidentsList.tsx` (add comuna link) and the
  existing pipeline modules; keep the anti-hallucination centroid design.
- **Depends on Phase 17** (source registry + methodology) and Phase 11 (comuna
  pages exist to link incidents to).
- **Verify with BrowserOS** (EN+ES news page, pins, both link types).
- Editorial/legal: every incident cites + links its press source; sober tone;
  attribute the medium.
</decisions>

<approach>
## Proposed wave structure
- **Wave 1 — Geolocation redesign (NEWS-01):** classifier emits comuna name +
  region hint; deterministic name→CUT resolver (accent-insensitive, 346-list);
  RED tests on known headlines.
- **Wave 2 — Golden set + A/B harness (NEWS-02):** label 30–50 incidents;
  scoring script (comuna/family accuracy, latency, cost, reliability);
  env-configurable provider; run A/B (keys); document + default the winner.
- **Wave 3 — Live run (NEWS-03):** execute pipeline → `current.json`; sync to
  `site/public`; verify pins + recent-incidents render.
- **Wave 4 — Surfacing (NEWS-04):** extend incident schema with comuna cut+slug;
  incident→comuna link in `IncidentsList`; bilingual news page (EN/ES);
  freshness indicator; sitemap + nav/footer spine entry.
- **Wave 5 — Verify + gate:** chained build+validate (OneDrive desync);
  BrowserOS visual check (EN+ES); `16-VERIFICATION.md`.

## Cross-cutting risks
1. **Comuna hallucination** (highest) — closed-list name→CUT + golden-set
   measurement is the mitigation; never let the model emit a raw CUT.
2. **Uncalibrated confidence** — don't rely on the 0.6 threshold alone;
   the name→CUT resolver is the real guard.
3. **API cost/rate limits** during A/B — bounded golden set (30–50), cache.
4. **OneDrive build desync** — chain build+validate in one command.
5. **Legal tone** — incidents must cite+link source; reuse forbidden-language
   gate where prose is generated.
</approach>
