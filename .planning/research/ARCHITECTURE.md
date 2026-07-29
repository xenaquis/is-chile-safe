# Architecture Research — v2.1 (News Intelligence, Map UX & Ops Hardening)

**Domain:** Static-site (Astro/Cloudflare Pages) + Python cron pipeline, adding facets/clustering to an existing news layer and reworking a Leaflet control shell.
**Researched:** 2026-07-29
**Confidence:** HIGH (all claims below verified by reading the actual files cited; no training-data guesses on repo internals)

---

## (a) Where facets get computed

### Options compared

| Option | SSG/indexability | Incremental cost | Validator impact | process.cwd() risk |
|---|---|---|---|---|
| (i) Python pipeline emits derived JSON artifact, committed to `data/` | Preserved — Astro still reads static JSON at build time | Cheap: computed once per cron run in Python, not per Astro page render | New validator needed to check shape/freshness; existing 15 fit this pattern | N/A (Python has no cwd ambiguity) |
| (ii) Astro frontmatter computes facets at build time from `current.json` | Preserved | Recomputed on every `astro build` (cheap: ~hundreds of incidents, pure JS reduce/group) | No new pipeline output to validate; facet logic covered by existing page-level validators (`commune.mjs`, `region.mjs`, `spine.mjs` pattern) | Must follow the exact `process.cwd()` pattern already used in `site/src/pages/news.astro:22` — do NOT use `import.meta.url` |
| (iii) Client-side React island | **Broken** — facet content would be render-only, violating the explicit CLAUDE.md SEO constraint ("nada de contenido crítico render-only en cliente") | N/A | N/A | N/A |

### Recommendation: **(ii) — compute facets in Astro frontmatter at build time**, reading from the same `public/data/incidents/current.json` + `public/data/incidents/archive/*.json` that `news.astro` already reads via `process.cwd()`.

**Why not (i):** the pipeline already treats `current.json`/archive as its unit of truth (`pipeline/news/store.py`), and facet counts are a pure function of that data — computing them in Python and committing a second derived artifact creates a second source of truth that can drift (stale facet JSON vs. fresh `current.json` after a same-day cron run) and adds a commit/diff surface for data that's cheap to derive at build time. Astro already re-runs on every code push (`deploy-on-code.yml`) and every data-changing cron run (`news-pipeline.yml` → deploy hook), so build-time computation is never stale by more than a normal deploy cycle already is.

**Why (ii) is safe:** the exact pitfall this milestone must avoid was already hit and fixed in `site/src/pages/news.astro` (lines 18–22): frontmatter MUST resolve data via `path.resolve(process.cwd(), 'public/data/incidents/current.json')`, never `import.meta.url`, because compiled chunk locations differ per page and previously left EN empty while ES worked. Any new facet-computing module (e.g., `site/src/lib/newsFacets.ts`) must use the same `process.cwd()`-based resolution, and should be a **shared lib function** imported by both `news.astro` and `es/noticias.astro` — not duplicated per-locale — to prevent the bilingual-drift class of bug from recurring.

**New artifact shape** — none committed to the repo; this is an **in-memory build-time derivation**, but for planning clarity here is the shape a `computeNewsFacets()` helper in `site/src/lib/newsFacets.ts` (NEW file) should return, consumed by both news pages:

```ts
interface NewsFacetIndex {
  generated: string;                 // from current.json "generated"
  totalIncidents: number;
  byFamily: Record<string, number>;         // family key -> count (uses FAMILY_LABELS_EN/ES already in site/src/lib/familyDefs.ts)
  byRegion: Record<string, number>;         // region_id -> count, derived via cutToCommune -> region lookup (loadIndex() already gives cut->region via meta/index.json — verify region_id present on CommuneMeta)
  byMonth: Record<string, number>;          // YYYY-MM -> count (news.astro already builds monthGroups Map — refactor into this shared helper)
  windows: { d7: number; d30: number };     // rolling counts, cheap date math against "date" field
}
```

This is computed once per page render pass (both EN/ES pages call the same function against the same underlying data — no duplicate file reads needed if hoisted into a shared module, but each `.astro` file's frontmatter runs independently at build time; that's acceptable, it's still O(hundreds) of incidents).

**Open question:** Does `data/cead/meta/index.json` (the source for `loadIndex()` in `site/src/lib/data.ts:151`) carry a `region_id` field per commune entry? This must be verified before Phase 27 — if absent, comuna→region mapping needs a join against `data/cead/meta/catalog.json` or similar. Flag for Phase 27 research, not resolved here.

---

## (b) Does faceting change URL structure?

**Recommendation: query params for facet *state*, no new pre-rendered facet URLs in Phase 27/28.**

Rationale, weighed against the constraints actually in this repo:

- **File budget:** `avs-b-budget.mjs` already enforces a `< 18,000` file budget against the Cloudflare Pages 20,000-file free-tier ceiling (see `site/scripts/validate/all.mjs` #14), and `.planning/PROJECT.md` states the site is already at **792 pages** built with headroom under 18K, but that headroom is a shared budget with the rest of the site's programmatic pages (comunas × crime-type × A-vs-B compare pages). Cartesian faceting (family × region × time-window) would multiply combinatorially — even a modest 8 families × 16 regions × a handful of windows is 100+ new URLs, and many combinations would have 0–2 incidents (thin content), directly violating the "anti-thin-content rule" implied by the existing `figure-registry.mjs` completeness gate and the project's SEO discipline.
- **hreflang/canonical:** every new indexable URL needs a reciprocal ES/EN pair validated by `hreflang.mjs`, plus `EditorialLayout`'s `enPath`/`esPath` props (seen wired in `news.astro:132-133`) — and per the `i18n-localized-slug-pitfall` memory, ES paths must be **hardcoded**, `getRelativeLocaleUrl()` does not translate localized slugs. Facet pages would multiply this hardcoding burden across every combination.
- **Sitemap:** `@astrojs/sitemap` auto-includes every route Astro emits; a combinatorial facet explosion would dilute sitemap signal with low-value pages, working against the explicit SEO goal of ~10 priority editorial pages + comprehensive-but-real comuna/region/crime-type coverage.

Instead:
- `/news/` and `/es/noticias/` stay the single indexable URL per locale (as today), with facet filters expressed as **client-enhanced query params** (`?family=&region=&window=`) that a small vanilla-JS (zero-React, matching the existing "zero-JS/progressive enhancement" pattern used for the hamburger menu per `astro-script-no-expr-interpolation` and `browseros-review-gotchas` memory conventions) reads on load to show/hide pre-rendered sections. **Critical constraint from CLAUDE.md/D-15 style precedent:** the full incident list (all facets, all months) must still be present in the pre-rendered HTML — JS only toggles visibility/filters client-side; Google indexes the unfiltered superset. This mirrors the existing zero-JS-critical-content rule and the pattern already used for `monthGroups` (server-computed, then rendered as static `<section>` blocks in `news.astro:157-186`).
- If SEO analysis later justifies a handful of **high-value, high-volume facet pages** (e.g., a `/news/robos/` per-family archive, analogous to existing crime-type ranking pages), those should be added deliberately and individually — not generated as a full cross-product — and gated by the same thin-content discipline used for `CSEO-01/02` (crime-type SEO pages, v1.2 Phase 15). This is a candidate for a **future phase**, explicitly out of scope for Phase 27/28 unless the roadmapper decides otherwise.
- JSON-LD: the existing single `WebPage` JSON-LD block (`news.astro:119-125`) stays as-is; no `ItemList`-per-facet needed since there's no new indexable URL per facet.

**No sitemap/hreflang/route-count changes required for Phase 27/28** under this recommendation — `coverage.mjs` and `hreflang.mjs` continue validating exactly the same two URLs.

---

## (c) Where clustering lives in the pipeline

### Current stage order (verified in `pipeline/scrape_news.py`)

```
1. feeds.fetch_feed()         — RSS ingest, per outlet (pipeline/news/feeds.py)
2. is_crime_item() filter     — keyword pre-filter (D-02)
3. filter_seen() / seen.json  — skip already-seen URLs (D-03)
4. classifier.classify()      — LLM: family, title_es/en, summary, commune_name, confidence
5. resolver.resolve_cut()     — deterministic name→CUT lookup (anti-hallucination gate, NEWS-01 redesign)
6. centroids.get_centroid()   — lat/lng lookup by CUT
7. store.build_incident()     — assemble IncidentRecord dict
8. dedup.deduplicate()        — cross-source EXACT/NEAR-duplicate collapse (pipeline/news/dedup.py)
9. store.merge_and_write()    — merge into rolling 30-day window + monthly archive, Pydantic-validate, atomic write
```

### How clustering differs from the existing `dedup` step

`pipeline/news/dedup.py` is explicitly **not** semantic clustering — it does two cheap, non-LLM things (per its own docstring, D-10: "Pure stdlib — difflib, re, unicodedata. No rapidfuzz, no LLM"):
1. Canonical-URL collapse (strip UTM params, same URL = same article).
2. `difflib.SequenceMatcher` title-similarity within `(cut, date)` buckets, threshold 0.82 — this only catches **near-identical titles from different feeds re-publishing the same wire story**, bucketed strictly by exact commune + exact date.

Event clustering (Phase 26 spike) is a different, harder problem: grouping articles that describe the **same real-world incident** with materially different titles, possibly different dates (report lag), and articles that individually resolved to the same or adjacent communes — this requires semantic understanding the LLM classifier already has access to, which is why the spike is scoped to reuse "the LLMs we already pay for" rather than building a new similarity metric.

**Stage ordering: clustering extends the pipeline as a new stage AFTER `dedup` and BEFORE/alongside `merge_and_write`**, not a replacement:

```
... 7. store.build_incident()
    8. dedup.deduplicate()                    — EXISTING, unchanged (cheap syntactic pass first)
    9. NEW: clustering.cluster_incidents()    — LLM-assisted grouping on the DEDUPED set
   10. store.merge_and_write()                — EXTENDED to persist cluster fields (see below)
```

Running dedup first is correct and should not change: it's free (stdlib) and shrinks the candidate set before the more expensive LLM clustering pass runs, keeping cost down (mirrors the existing `D-17` cost-control philosophy — `MAX_CLASSIFICATIONS_PER_RUN` cap in `scrape_news.py:144`). Clustering should only ever run against incidents from the **same or adjacent dates** (a rolling window, not the full 30-day store) to bound LLM cost and avoid pathological cross-cluster merges across unrelated time periods — exact window size is a Phase 26 spike parameter, not decided here.

### Persisted cluster representation (proposed, Pydantic v2, back-compat pattern)

Following the established "optional-with-default fields" back-compat convention already used in `pipeline/news/schema.py` (e.g., `slug: str | None = None` on `IncidentRecord`, added post-hoc "for back-compat"):

```python
class IncidentRecord(BaseModel):
    # ... existing fields unchanged ...
    slug: str | None = None
    cluster_id: str | None = None      # NEW, optional-with-default — None = unclustered (GO path only)
    is_primary: bool = False           # NEW, optional-with-default — True for the chosen representative article of its cluster
```

Rather than a separate top-level `clusters: list[...]` structure duplicating article data, prefer attaching `cluster_id`/`is_primary` directly to each `IncidentRecord` — this keeps `IncidentsFile` (`schema.py:126-131`) unchanged in top-level shape (`generated`, `window_days`, `incidents: list[IncidentRecord]`), so:
- **`current.json` consumers stay compatible without changes**: `news.astro`, `es/noticias.astro`, `site/src/components/map/IncidentPinLayer.ts` (which the `news.astro` docstring explicitly says field names must mirror — "Field names match IncidentPinLayer.ts Incident/IncidentsFile exactly (D-15)") all continue to work unmodified because they only read fields they already know about; new optional fields are invisible to them until the consumer code is updated to use them (Phase 28).
- **Archive files** (`data/incidents/archive/YYYY-MM.json`) get the same optional fields for free since `merge_and_write()` in `pipeline/news/store.py` writes both current and archive through the same `IncidentRecord`/`validate_incidents_file()` path (`store.py:176-191` for archive, `194-206` for current) — no separate migration needed.
- A `cluster_id` groups N `IncidentRecord`s; the "chosen primary" is just the record with `is_primary=True` within that `cluster_id` (deterministic tie-break, e.g., earliest `date` or highest classifier `confidence`, to be defined by the Phase 26 spike). Consumers that don't understand clustering simply render every incident individually (today's behavior) — full backward compatibility, no breaking change, and the visualizer (Phase 28) opts in by grouping on `cluster_id` when present.

**NEW module:** `pipeline/news/clustering.py` (mirrors the existing `pipeline/news/dedup.py`, `resolver.py`, `centroids.py` module style — one responsibility per file). **NEW pytest file:** `pipeline/tests/test_clustering.py` (mirrors `test_dedup.py`).

**Schema validator impact:** `VALID_FAMILIES`/`VALID_CUTS`-style field validators in `pipeline/news/schema.py` need one more optional field validator or none at all (since `cluster_id: str | None` and `is_primary: bool = False` need no domain validation beyond type). `record_rejected()` in `scrape_news.py` is unaffected — clustering only touches accepted, already-classified/resolved incidents.

**Gate:** Per PROJECT.md, "Phase 26 gates 27/28. If clustering is NO-GO, the finding is documented and the visualizer ships with faceting only." Concretely: if NO-GO, `clustering.py` is never wired into `scrape_news.py`'s stage order, `cluster_id`/`is_primary` fields are never added to the schema, and Phase 28's UI ships using only the Phase 27 facet index (no clustered-event cards).

---

## (d) Map control shell

### Current structure (`site/src/components/map/MapIsland.tsx`)

- **Leaflet layers** (imperative, ref-held, never re-mounted per the documented `D-12` rule "setStyle in place on filter change — never re-mount L.geoJSON"):
  - `layerRef` — the `L.geoJSON` choropleth layer, mounted once via `mountChoroplethLayer()` (`MapIsland.tsx:211-225`), recolored in place via `applyStyleMap()`.
  - `dotsRef` — low-zoom dot layer (`LowZoomDotLayer.ts`), mounted/unmounted based on `lowZoom` state.
  - `eventsRef` — the **news pin layer**, mounted/unmounted via `fetchAndMountIncidents()` from `IncidentPinLayer.ts`, gated by `showEvents` boolean state (`MapIsland.tsx:359-383`).
  - `userRef` — user-location marker.
- **React state** (`MapIsland.tsx:96-114`): `year`, `crimeFamily`/`crimeFamilyIndex`, `crimeIsHomicide`, `mode` ('composite'|'family'), `showEvents`, `lowZoom`, `selected` (commune cut), `communeIndex`, `breaks`, `partialYear`, `toast`. React owns all UI/filter *state*; Leaflet layers are recolored/toggled imperatively in `useEffect`s reacting to that state — this is the established pattern and should NOT change.
- **Controls UI components** (already extracted, all under `site/src/components/map/`): `MapTopbar.tsx` (search + year/family filters + events toggle + locate button — the props interface at `MapIsland.tsx:418-437` shows `crimeFamily`, `showEvents`, `onEventsToggle`, `onSelect`, `onLocate`, plus a `modeToggle` render-prop for the composite/family switch), `Legend.tsx`, `ZoomControl.tsx`, `ResultPanel.tsx`, `Toast.tsx`.

### Where new controls mount

Phase 30's control-shell rework should be scoped to **`MapTopbar.tsx` and its child controls** — not `MapIsland.tsx`'s Leaflet-layer effects, which the CLAUDE.md-referenced Phase 29→30 gate explicitly protects ("Leaflet logic in `MapIsland` is preserved; the filter panel and the news toggle are redesigned"). New/redesigned controls are additional React UI mounted in the existing topbar/overlay DOM tree (siblings of `MapTopbar`, `Legend`, `ZoomControl`, `ResultPanel` inside the `map-stage` div, `MapIsland.tsx:412-539`), driving the **same existing state setters** (`onFamilyChange`, `onEventsToggle`, `setMode`, `setYear`) — no new Leaflet layer types needed for a filter-shell redesign; if the design calls for a new visual affordance (e.g., grouped filter drawer, mobile bottom-sheet), it's a new `.tsx` component under `site/src/components/map/` composing existing state, not a change to `ChoroplethLayer.ts`/`IncidentPinLayer.ts`/`LowZoomDotLayer.ts`.

### Shared vocabulary between map filters and news-page facets, without coupling

Both surfaces already independently reference the same underlying taxonomy:
- **Crime family**: `site/src/lib/familyDefs.ts` exports `FAMILY_LABELS_EN`/`FAMILY_LABELS_ES` — already imported by both `news.astro` (`familyLabel()` helper, line 66-68) and (presumably) the map's family filter chips. This file is the natural single source of truth for family vocabulary; Phase 27/28 facets and Phase 30 map filters should both import from it, with **no direct code dependency between `/news/` and `/map/`** — they only share the same underlying `familyDefs.ts` + `data/cead/meta/index.json` (comuna→region) constants module, never import each other's components. This preserves the "map filters and news facets share vocabulary without coupling the two pages" requirement structurally.
- **Comuna/region**: `loadIndex()` in `site/src/lib/data.ts` is the CUT→{name,slug} source already used by both `news.astro` (`cutToCommune`/`slugToCommune` maps, lines 48-55) and the map (`communeIndex` state populated from `/data/cead/meta/index.json` fetch, `MapIsland.tsx:172,183`). Same story: shared data source, not shared component.

### `?cut=` deep-link and the known `?region=` gap

`MapIsland.tsx:226-233` implements `?cut=` today: validates a 4-5 digit CUT via regex, then calls `selectCommune(focusCut)` after a 100ms timeout to let Leaflet finish rendering. `.planning/PROJECT.md`'s "Known carry-over debt" list explicitly names `?region=` handling in `MapIsland` as unresolved — there is currently **no equivalent region-level deep-link/filter** parsed from the URL. If Phase 30's design introduces a region facet or a cross-link from `/news/?region=X` into the map, this gap needs to be closed as part of that work (parse `?region=`, filter/zoom accordingly) — flag this explicitly as in-scope risk for Phase 30, not a pre-existing solved problem.

---

## (e) Cron + security posture

### Current workflow surface (verified — all 5 files read in full)

| Workflow | Schedule | Trigger | Secrets consumed | Permissions | Writes |
|---|---|---|---|---|---|
| `news-pipeline.yml` | `0 */6 * * *` (every 6h) | schedule + `workflow_dispatch` | `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `CF_DEPLOY_HOOK_URL` (as `CF_HOOK`) | `contents: write`, `issues: write` | `data/` (commits `[skip ci]`), triggers CF deploy hook if data changed |
| `r2-archive.yml` | `30 5 * * *` (daily) | schedule + `workflow_dispatch` | `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | `contents: read`, `issues: write` | External R2 bucket only (no repo commit) |
| `cead-scraper.yml` | `0 3 1 1,4,7,10 *` (quarterly) | schedule + `workflow_dispatch` | `CF_DEPLOY_HOOK_URL` (as `CF_HOOK`) | `contents: write`, `issues: write` | `data/` (commits `[skip ci]`), triggers CF deploy hook — **but per memory `cead-scraper-quarterly-local`, CEAD 403s the Actions runner IPs, so this cron effectively never succeeds and exists only as an "alert reminder"; the real scrape runs manually on a local machine** |
| `deploy-on-code.yml` | none (event-only) | `push` to `master` on `paths: site/**` or itself | `CF_DEPLOY_HOOK_URL` (as `CF_HOOK`) | `contents: read` | No repo write — fires CF deploy hook only |
| `ci.yml` | none (event-only) | `pull_request` + `workflow_dispatch` | none | `contents: read` (explicit least-privilege comment: "CI only reads; it never commits or deploys") | Nothing — build+validate+pytest+actionlint only |

### Structural inconsistencies / single points of failure identified

1. **CEAD cron is a documented no-op against a known-403 target.** `cead-scraper.yml` runs quarterly on schedule but (per project memory) always fails against CEAD from GitHub-hosted runner IPs; it exists purely so `failure()` fires the GitHub Issue alert as a human reminder to run the scraper locally. This is *intentional* per memory, but it is **not documented in the workflow file itself** — no comment in `cead-scraper.yml` explains why it's expected to fail, unlike `deploy-on-code.yml` which has an extensive header comment explaining its own rationale. This is an inconsistency in self-documentation that Phase 32 should close (add a header comment mirroring the deploy-on-code.yml style, and consider whether `continue-on-error` + a distinct label like `cead-local-required` on the alert issue would be clearer than the generic `pipeline-failure` label shared with real failures).
2. **`CF_DEPLOY_HOOK_URL` is a single point of failure duplicated across three workflows** (`news-pipeline.yml`, `cead-scraper.yml`, `deploy-on-code.yml`), each with its own inline `if: ... && env.CF_HOOK != ''` guard and its own retry policy (`--retry 5 --retry-all-errors` in news-pipeline vs. `--retry 3` in cead-scraper and deploy-on-code — **inconsistent retry counts for the same operation**, worth reconciling in Phase 32). If the deploy hook URL secret is ever rotated and one workflow's copy is missed, that workflow silently stops deploying (empty-string gotcha, see below) while others keep working — no cross-check exists.
3. **Empty-string secrets gotcha is only guarded in some places.** `news-pipeline.yml` and `cead-scraper.yml` both correctly guard with `env.CF_HOOK != ''` before curling (an unset GitHub secret resolves to an empty string, not a missing env var, so `${{ secrets.X }}` always exists but can be `""`). `deploy-on-code.yml` also explicitly checks `if [ -z "$CF_HOOK" ]`. **However, `news-pipeline.yml`'s API key check has no equivalent explicit guard at the workflow-YAML level** — the emptiness check is pushed down into Python (`scrape_news.py:182-190`, `api_key = os.environ.get(_key_env, "").strip(); if not api_key: ... return 0`), which is correct and graceful, but means the *workflow* has no visibility that the run was a no-op due to a missing secret — it will show green even when nothing happened. This is consistent with the "fail gracefully" design goal but is a silent-degradation risk: a rotated/revoked `OPENROUTER_API_KEY` would produce weeks of green CI runs with zero new incidents and no alert, since `return 0` never triggers the `if: failure()` issue-alert step. **Recommend Phase 32 add an explicit "0 candidates classified this run" warning-issue path**, distinct from the hard-failure alert, so a silently-broken key doesn't go unnoticed indefinitely — this directly addresses the `news-cron-billing-outage` memory precedent (an outage was previously invisible for a week).
4. **r2-archive.yml has no deploy-hook interaction at all** (correct — it writes to R2, not the repo) but shares the exact same `issues: write` + generic `pipeline-failure` label alert pattern as the other three crons, meaning a human triaging the issue tracker cannot distinguish "the daily research archive is down" from "the news pipeline that visitors depend on is down" without opening each issue. Phase 33 (security posture) or Phase 32 (cron consistency) should consider distinct labels per workflow (`news-pipeline-failure`, `r2-archive-failure`, `cead-scraper-failure`) for triage clarity.
5. **Permissions are already reasonably scoped** (`ci.yml` explicitly `contents: read` only with a rationale comment; `deploy-on-code.yml` is `contents: read`) but the three data-writing crons all request both `contents: write` AND `issues: write` at the job level — broader than strictly needed if a step-scoped `permissions:` block were used instead (GitHub Actions supports per-job but not native per-step permission narrowing beyond job level, so this is close to best-practice already; Phase 33 should verify no workflow requests `pull-requests: write` or other unused scopes, none found in current files).
6. **`actionlint` runs in `ci.yml` on `pull_request` only**, not on `workflow_dispatch` or on a schedule — a workflow-syntax regression introduced directly on `master` (bypassing PR) would not be caught until the next PR. Given this repo pushes data commits directly to `master` from cron jobs (not via PR), and code changes appear to also land via direct push per `deploy-on-code.yml`'s `push: branches: [master]` trigger, actionlint coverage has a gap for direct-to-master workflow-file edits. Low severity, but a Phase 32/33 candidate.

**No new workflow files are needed for this milestone's data-flow changes** — Phase 27 (facets) is Astro-build-time-only (no new cron), Phase 26/28 (clustering) extends `news-pipeline.yml`'s existing `python pipeline/scrape_news.py` step in place (the new clustering stage runs inside the same script, consuming the same secrets already present — `OPENROUTER_API_KEY`/`DEEPSEEK_API_KEY` — no new secret required unless the spike decides a distinct/cheaper clustering model needs its own key). Phase 32/33 work is entirely about auditing/reconciling the 5 existing files, not adding a 6th.

---

## NEW vs MODIFIED component inventory

| Component | Status | Path | Phase |
|---|---|---|---|
| `newsFacets.ts` shared facet-computation lib | **NEW** | `site/src/lib/newsFacets.ts` | 27 |
| `news.astro` refactor to use shared facet lib + render facet controls | **MODIFIED** | `site/src/pages/news.astro` | 27/28 |
| `es/noticias.astro` refactor to use shared facet lib + render facet controls | **MODIFIED** | `site/src/pages/es/noticias.astro` | 27/28 |
| News facet/filter UI (progressive-enhancement JS, zero-React) | **NEW** | likely `site/src/components/NewsFacetControls.astro` + small `<script>` | 28 |
| `pipeline/news/clustering.py` | **NEW** | `pipeline/news/clustering.py` | 26 (spike) → 28 (wired in) |
| `pipeline/tests/test_clustering.py` | **NEW** | `pipeline/tests/test_clustering.py` | 26/28 |
| `IncidentRecord` schema: `cluster_id`, `is_primary` fields | **MODIFIED** (optional-with-default, back-compat) | `pipeline/news/schema.py` | 28 (gated on 26 GO) |
| `scrape_news.py` stage order: insert clustering after dedup | **MODIFIED** | `pipeline/scrape_news.py` | 28 (gated on 26 GO) |
| `IncidentPinLayer.ts` — optionally render clustered pins | **MODIFIED (optional)** | `site/src/components/map/IncidentPinLayer.ts` | 28/30, only if Phase 26 GO and design calls for cluster-aware map pins |
| Map control-shell components (filter panel, news toggle redesign) | **MODIFIED** | `site/src/components/map/MapTopbar.tsx` + new sibling `.tsx` files under `site/src/components/map/` | 29 (design) → 30 (implement) |
| `MapIsland.tsx` Leaflet-layer effects (`ChoroplethLayer.ts`, `IncidentPinLayer.ts`, `LowZoomDotLayer.ts`) | **UNCHANGED** (explicitly protected by the Phase 29→30 gate) | `site/src/components/map/MapIsland.tsx` and siblings | — |
| `?region=` deep-link support | **NEW** (closing known gap) | `site/src/components/map/MapIsland.tsx` | 30, if design requires it |
| `.github/workflows/*.yml` — comments, retry-count reconciliation, per-workflow issue labels, secret-empty guard for silent-degradation alerting | **MODIFIED** | `.github/workflows/news-pipeline.yml`, `cead-scraper.yml`, `r2-archive.yml`, `deploy-on-code.yml` | 32/33 |
| `ci.yml` actionlint trigger scope | **MODIFIED (optional)** | `.github/workflows/ci.yml` | 32/33 |
| New validator for facet-index shape/consistency (optional) | **NEW (optional)** | `site/scripts/validate/facets.mjs`, registered in `all.mjs` | 27, if the roadmapper wants build-time facet correctness gated like the other 15 validators |

---

## Suggested build order (dependency-respecting)

1. **Phase 26 — clustering spike.** Standalone: builds `pipeline/news/clustering.py` as a script/notebook-style spike against existing `data/incidents/current.json` + archive, no production wiring. Produces a GO/NO-GO decision and (if GO) the chosen clustering prompt/model + a defined `cluster_id`/`is_primary` contract. **Blocks:** the clustering portions of 27/28.
2. **Phase 27 — news faceting data model.** Independent of Phase 26's outcome (facets are pure derivation over existing fields: family, cut/slug→region, date). Build `site/src/lib/newsFacets.ts`, wire into `news.astro`/`es/noticias.astro` frontmatter, verify `region_id` availability in `data/cead/meta/index.json` (open question above) before or during this phase. **Depends on:** nothing new from 26. **Should land before 28** since 28 consumes the facet index.
3. **Phase 28 — news visualizer UI.** Consumes Phase 27's facet lib for filter UI; consumes Phase 26's `cluster_id` schema fields *only if GO* — build the UI defensively so it degrades to ungrouped cards when `cluster_id` is absent (mirrors the existing `slug?: string` optional-field defensive pattern already used in `news.astro`'s incident type, line 25-35). If Phase 26 wired clustering into `scrape_news.py` as part of Phase 28's scope (per PROJECT.md phrasing, wiring appears to happen here, not in 26 itself), that pipeline change should land and run at least one cron cycle before the UI ships, so `current.json` actually contains populated `cluster_id` values to render against.
4. **Phase 29 — map UX audit (BrowserOS design loop).** Independent of 26/27/28 — pure design/screenshot iteration against the *current* map. Produces an accepted design spec. **Blocks:** Phase 30.
5. **Phase 30 — map control-shell rework.** Implements Phase 29's accepted design inside `MapTopbar.tsx` and siblings; Leaflet layer logic untouched. If the design references news facets vocabulary (family/region labels), it should import from the same `familyDefs.ts`/`data.ts` sources Phase 27 already uses — soft dependency on 27 landing first for vocabulary consistency, not a hard blocker.
6. **Phase 31 — docs & methodology refresh.** Should land after 26–30 land (or at least after their scope is finalized) so the methodology page accurately describes clustering (GO/NO-GO outcome) and faceting as shipped.
7. **Phase 32 — cron consistency.** Independent of 26–30's feature work but should audit whatever `news-pipeline.yml` looks like *after* Phase 28's clustering wiring (if any), since that phase may add cost/latency considerations (LLM clustering calls) worth reflecting in the `NEWS_MAX_CLASSIFY`-style cost-control commentary. Sequence after 28.
8. **Phase 33 — security posture.** Can run in parallel with or immediately after 32 (same files, complementary lens — cost/schedule vs. secrets/permissions). Sequence last or alongside 32.

**Critical path:** 26 → (27 parallel) → 28 → 29 → 30, with 31/32/33 as closing phases that depend on 26-30's final shape being known.

---

## Open questions (not resolved by this research — flag for phase-specific research)

1. Does `data/cead/meta/index.json` carry a `region_id`/region-name field per commune, needed for the Phase 27 geography facet? Verify in Phase 27 kickoff.
2. What LLM call pattern will Phase 26's clustering spike use — a single batched prompt over a candidate window, or pairwise/iterative comparison? This determines cost-control parameters analogous to `MAX_CLASSIFICATIONS_PER_RUN` and whether a new env var (e.g., `NEWS_MAX_CLUSTER`) is needed in `scrape_news.py`.
3. Whether Phase 28's clustered-event UI needs a new map pin visual treatment (grouped marker) is a Phase 29/30 design question, not resolved here — `IncidentPinLayer.ts` was read only at the interface level (`fetchAndMountIncidents`), not its internals; a follow-up read is needed before Phase 30 implementation if clustering affects map pins.
4. Exact retry/backoff values and label taxonomy for Phase 32's cron reconciliation are implementation choices for that phase, not architectural decisions — flagged as inconsistencies above but not prescribed.
