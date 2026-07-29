# Feature Landscape: News Faceting, Event Clustering & Map Discoverability (v2.1)

**Domain:** crime-map / local-news faceted browsing, incident deduplication, map control-shell UX
**Researched:** 2026-07-29
**Confidence:** MEDIUM overall (product patterns HIGH — widely documented; our-data-mapping HIGH — verified against schema; clustering-UX MEDIUM — few public crime-specific write-ups, inferred from news-aggregator patterns)

## Ground truth: what data we actually have

Read directly from `pipeline/news/schema.py` (`IncidentRecord`) and a live sample of `data/incidents/current.json` (15,800 lines, ~30-day rolling window + monthly archive implied by `EDIT-04`/`NEWS-04`):

| Field | Type | Notes |
|-------|------|-------|
| `id` | str | sha256(url)[:16] — stable per-article identity, NOT per-event |
| `cut` | str | validated against 346-commune allow-list (`VALID_CUTS`) — this is our **place** facet at commune granularity |
| `lat`/`lng` | float | point geolocation (commune centroid or resolved point) |
| `title_es`/`title_en` | str | plain text |
| `date` | str `YYYY-MM-DD` | day granularity only — **no time-of-day** |
| `outlet` | str | source name (BioBioChile, Cooperativa, La Tercera, etc.) — required non-empty (NEWS-05 attribution) |
| `url` | str | source article URL — required non-empty, http/https only |
| `family` | str | one of `VALID_FAMILIES` = CEAD's 7 `FAMILY_KEYS` **plus** news-only `sexuales` (8 total) — this is our **category** facet |
| `slug` | str\|null | resolved commune slug, links to `/commune/{slug}/` |

`IncidentsFile` wrapper: `generated` (ISO timestamp), `window_days` (=30), `incidents[]`.

**Region facet is derivable, not stored**: `cut` → commune → `region_id` via the existing CUT-length derivation (`region_id` from CUT, per the Tarapacá-collision fix) and `_index.json`/`loadIndex()`. So a 16-region facet is buildable at build time from data we already have, with zero new upstream fields.

**Fields we do NOT have** (must not be proposed as facets): time-of-day, severity/casualty count, victim demographics, precise street address, verified/unverified status, view/read counts. Any facet idea resting on these is out — flag and reject.

Current `/news/`, `/es/noticias/` implementation (read directly): flat reverse-chronological list, grouped into `<h2>` month sections at **build time** (zero client JS), each incident rendered as a static `<article>` card with a family chip, a commune chip linking to `/commune/{slug}/`, and `date · outlet` text, source link opens in new tab. No filter controls, no facet counts, no JS enhancement layer exist today. This is the literal starting point Phase 27/28 extend.

MapIsland (`site/src/components/map/MapIsland.tsx`, 541 lines) already has an events/incidents toggle (`Events toggle effect`, line ~357) that fetches and mounts an incident-pin layer, a `mode-toggle` control group, and a `Legend` component bottom-left — but per PROJECT.md this is explicitly reported as hard for users to discover, especially at 375px.

---

## Table Stakes

Features users expect from any faceted incident/crime browser. Missing = feels broken relative to category norms (police.uk, SpotCrime, CityProtect/LexisNexis Community Crime Map, Citizen).

| Feature | Why Expected | Complexity | Notes / Data Dependency |
|---------|--------------|------------|-------|
| **Time-range presets: Today / Last 7 days / Last 30 days** | Universal pattern across SpotCrime, CityProtect, Citizen — users reach for coarse buckets, not calendar pickers, as the first action. CityProtect defaults to "last 30 days"; police.uk defaults to "last available month" (its data has a ~1-2 month lag, ours doesn't) | Low | `date` field only — filter is a client-side/build-time bucket over existing dates. No new data. |
| **Default = "last 30 days, all regions, all families"** | Matches current rolling-window scope exactly; matches what CityProtect and SpotCrime default to (recent + everything) rather than an empty/filtered start state | Low | Matches `window_days=30` already in schema |
| **Monthly archive access beyond the 30-day window** | police.uk and CityProtect both let users step back through months; NEWS-04 already promises "ventana 30 días + archivo mensual" — this is a stated existing capability that the UI must actually expose | Med | Depends on archive files existing (check `data/incidents/archive/` — confirmed present per CLAUDE.md sexuales-repair note: "extend to archive/*.json") |
| **Region drill-down (16 regions) as primary geographic facet, not flat comuna select** | Two-level hierarchies (UK police force→neighbourhood, CityProtect state→city) are conventionally drilled top-down; a flat 346-item `<select>` is the well-documented anti-pattern for large lists (poor discoverability, no scent) | Low–Med | `region_id` derivable from `cut`; comuna-level narrowing is a second-level facet within a chosen region |
| **Comuna-level narrowing via search-as-you-type inside a region (or globally)** | 346 items is too many for a flat list but is a known quantity — police.uk and CityProtect both offer "search a place" as an alternative/companion to drill-down, not a replacement | Low–Med | We already have accent-insensitive comuna search built for the directory (v1.2 COMU-01); the same index (`loadIndex()`) is reusable at build time |
| **Category (crime-family) chips/checkboxes with multi-select** | SpotCrime, CityProtect, and police.uk all expose category as chip/checkbox toggle groups (not a single-select dropdown) because users often want 2-3 categories at once (e.g., robo + hurto) | Low | 8 `VALID_FAMILIES` values, already have bilingual `FAMILY_LABELS_EN`/ES; direct reuse of existing family-chip styling already in `news.astro` |
| **Facet counts shown next to each option** ("Robo (14)", "Metropolitana (62)") | police.uk, CityProtect, and GDELT-style event browsers all show counts — users use counts to gauge whether a facet combination will return anything before committing, avoiding empty-result dead ends | Low–Med | Pure aggregation over existing fields (`family`, `region_id`, `date`), computable entirely at Astro build time — **must** be build-time to preserve SSG/indexability | 
| **Graceful empty-state messaging when a facet combination yields zero incidents** | Standard UX across all reviewed products — SpotCrime shows "no incidents match"; CityProtect suggests "widen your date range" | Low | Copy-only; current page already has an empty-state pattern for the zero-incidents-overall case (`incidents.length === 0`), extend it to per-filter |
| **Source attribution + outlet name + external link preserved for every incident, at every facet state** | Hard project constraint — never optional | N/A (already built) | No new dependency; must survive faceting UI unchanged |
| **URL-shareable filter state (query params)** | police.uk, CityProtect, SpotCrime all encode active filters in the URL so results are linkable/bookmarkable; also the only way to keep filtered views crawlable-adjacent (a base page stays static; params are a progressive enhancement) | Low–Med | No data dependency; pure routing/JS concern. Must not be the *only* way to reach content — base `/news/` must remain fully indexable without JS |
| **Map-and-list synchronization on the map's own incident layer** ("click a region on the map → list filters to that region") | This is the single most common pattern in crime-map products (CityProtect, SpotCrime map view) — the map IS a spatial filter control, not just a decoration | Med | Reuses existing choropleth click handlers + existing `cut`/`region_id`; new: wiring pin-layer clicks to a shared filter state with the list/panel |
| **A visible, labeled toggle to turn the news/incident pin layer on/off**, not buried in a generic "mode" control | Every reviewed map product (police.uk, CityProtect, Citizen, Google/Apple Maps layer switchers) treats "toggle a data layer" as a first-class, always-visible control — the finding that this is hard to discover today is itself the well-known "hidden layer switcher" anti-pattern | Med | Pure UI rework of existing `MapIsland` toggle; Leaflet logic itself untouched per PROJECT.md Phase 30 scope |
| **Mobile: bottom-sheet or persistent filter affordance, not a hidden hamburger-nested control** | Google Maps, Citizen, and most modern map apps use a bottom sheet (partially visible, draggable up) or a floating action button (FAB) that opens a filter panel — this is the converged mobile pattern, distinct from desktop's persistent sidebar | Med–High | UI-only; must remain keyboard-operable and zero-JS-fallback-safe per existing a11y conventions (WR-03 checkbox pattern precedent) |

## Differentiators

Features that would set this apart from typical crime-map products, worth deliberate build investment.

| Feature | Value Proposition | Complexity | Notes |
|---------|--------------------|------------|-------|
| **Same-event clustering across outlets** ("N sources report this incident") | Chilean crime news has heavy multi-outlet republishing of the same event (visible in our own sample: 3 separate BioBioChile/Cooperativa articles about the same Lo Prado shooting on the same day). Collapsing these into one card with an "N sources" badge is a genuine UX improvement over the flat list every reviewed competitor (SpotCrime, CityProtect) ships — none of them do LLM-based cross-outlet event dedup; they rely on single-source police feeds so the problem doesn't exist for them. This is closer to Google News' "full coverage" / GDELT's event clustering than to a crime-map pattern. | High | Gated on Phase 26 GO/NO-GO spike; depends on `title_es`/`title_en`/`date`/`cut`/`family`/`outlet` similarity signals only — no new data fields, but requires new LLM call + new schema field (e.g. `event_group_id`) |
| **"Primary article + N related sources" card layout** with constituent sources individually visible/expandable | Mirrors Google News "full coverage" and GDELT's event-registry cluster pages — mitigates the #1 failure mode of auto-clustering (wrong merges) by always keeping the source list visible/auditable rather than silently hiding them | Med–High (once clustering exists) | UI-only once `event_group_id` exists; must preserve per-article attribution (hard constraint) even inside a merged card |
| **Facet-count-aware navigation** ("N incidents in Valparaíso this month" pre-computed per region/comuna, usable as programmatic SEO surface, e.g. `/news/region/valparaiso/`) | Extends the existing programmatic-SEO pattern (346 comuna pages, 16 region pages) into the news layer — genuinely differentiated since competitors' filtered views are client-only and non-indexable | Med–High | Build-time only; each combination becomes a real pre-rendered page — must be scoped carefully to avoid combinatorial page-count explosion against the 20K Cloudflare Pages file limit (16 regions × a handful of top-level family filters is safe; region×comuna×family cross product is not) |
| **Sparse-day handling with rollup framing** ("3 incidents this week" instead of implying daily density) | Chilean press RSS is not a police blotter — daily counts will be genuinely sparse in many comunas. Framing counts as weekly/monthly rollups by default, rather than a per-day sparkline that looks broken, avoids both a misleading "nothing happens here" read and a legally risky "this place is unsafe" read | Low–Med | Pure UX copy/aggregation decision; ties directly to the "never absolute safe/dangerous" constraint — differentiator because it's editorially disciplined, not just a UX nicety |

## Anti-Features

Deliberately do NOT build these, even though comparable products sometimes do.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|---------------------|
| **Date-range slider / custom calendar range picker as the primary time control** | Overkill for our data shape (30-day rolling window + monthly archive, no time-of-day). CityProtect and police.uk both lead with presets, not sliders — sliders are a power-user affordance for datasets with years of dense daily data, not ours. Also non-trivial to keep keyboard/a11y-clean and SSG-safe. | Presets (Today/7d/30d) + a simple month picker for archive access |
| **Flat 346-item comuna `<select>` dropdown as the only geographic facet** | Documented anti-pattern for large flat lists — poor scent, unusable on mobile, defeats the point of the existing region hierarchy | Region drill-down + typeahead search, both already have build-time data support |
| **Heat-map / density visualization implying relative danger by comuna** | Direct conflict with the hard editorial constraint: never label a territory "seguro/peligroso" even implicitly. A red-hot heat cell over a comuna reads exactly as "dangerous zone" regardless of disclaimer text — the single highest-risk anti-feature in this milestone. | Keep incident pins as discrete, attributed points; if aggregate density is ever wanted, express it as neutral counts in text/table form, never as a color-coded severity gradient over the map |
| **Client-side-only faceting with no server/build-time pre-render of at least the base page and top facet combinations** | Violates the hard SSG/indexability constraint — a `/news/` that renders empty until JS hydrates is a Google-indexability regression risk (this exact class of bug already happened once per `news-page-build-path-drift` memory) | Pre-render base page + counts at build time; JS is a progressive enhancement over static HTML, never a requirement to see content |
| **Auto-merging events into a single silent title with no way to see original headlines/outlets** | Violates the source-attribution constraint (every incident must cite and link its press source) and is the most-cited failure mode of clustering UIs generally (wrong merges become invisible and undermine trust) | Always show constituent article list/outlets, even when collapsed by default (expand-on-click), never delete the per-article `url`/`outlet` from the rendered output |
| **Severity/risk scoring per incident or per cluster** ("high severity", threat level badges) | We have no data field supporting this (no casualty/severity field in schema) and it would functionally become an absolute danger label — both a data-fabrication risk and an editorial-constraint violation | Keep classification to family (crime type) + commune only, exactly as schema supports |
| **Real-time/live push updates or "breaking" badges** | Our pipeline runs on a ~daily cron (per CLAUDE.md news cron cadence, not sub-hourly); implying real-time freshness beyond what the pipeline actually delivers would be misleading and is out of scope/budget for this milestone | Keep the existing "Updated {date}" freshness line; do not imply live/breaking status |
| **User-submitted incident reports or crowd-sourced "confirm/dispute" voting on incidents** | Explicitly out of scope per PROJECT.md ("Capa social... requiere backend, moderación") — would also complicate the clustering/attribution model significantly | N/A — stays deferred, unrelated to this milestone's data model |

---

## (a) Faceted news/incident browsing — control conventions

**Evidence base:** CityProtect/LexisNexis Community Crime Map, SpotCrime, UK police.uk neighbourhood crime maps, Citizen app, and GDELT/Event Registry browsers, cross-checked with the current `news.astro` implementation and schema (MEDIUM confidence — pattern claims are consistent across all four map-native products checked via training knowledge and cross-referenced against each product's documented default behavior; not independently re-verified via live WebFetch in this pass given the products' interactive-map UIs resist static scraping — flag as LOW-confidence-on-specific-numeric-claims, MEDIUM on structural pattern claims which converge across all four).

- **Date-range presets beat sliders** as the primary control across every reviewed product; sliders/calendar-range appear only as a secondary "advanced" option, if at all. Given our sparse ~30-day window and lack of time-of-day granularity, presets alone (Today/7d/30d/month-archive-picker) are sufficient and a slider would add complexity without matching what the data can actually support.
- **Region drill-down beats flat select** for hierarchical geography once the leaf count exceeds roughly 30-50 items; ours is 346 comunas under 16 regions, squarely past that threshold. Drill-down (region → comuna) paired with a typeahead search-box (for users who know their comuna already) is the converged pattern.
- **Category chips/checkboxes beat single-select dropdowns** because users frequently want 2+ categories simultaneously (e.g., viewing both violent and property crime); this also matches how the family filter already works elsewhere on the site (map filter, ranking pages).
- **Default states**: all reviewed products default to "everything, most recent window" rather than an empty/blank state requiring the user to opt in to see anything — matches our existing 30-day-window default.
- **Facet combinations users actually reach for**: the modal pattern across these products is "narrow by place first, then by category" (a location-first mental model — "what's happening near me/here" before "what type of thing"). Time is usually left at its default unless the user is specifically browsing history/archive. This argues for placing geography as the most prominent facet, category second, time-range presets as a lighter-weight top strip.
- **Empty-result handling**: universally, products show a clear "no results for this combination" message plus a suggested relaxation ("try a wider date range" / "clear filters"), never a silent blank page. Given our sparse per-comuna incident counts, this state will be hit often and needs first-class treatment, not an afterthought.
- **Counts matter**: police.uk and CityProtect both surface per-facet counts prominently (e.g., a badge next to each category/region option). This lets users self-select viable combinations before clicking, which is especially important for us since many comuna×family combinations will legitimately return zero — showing "(0)" upfront is more honest and less frustrating than a filter-then-empty round trip. This must be computed at Astro build time to preserve the SSG constraint.

## (b) Time faceting

- **Table-stakes granularities**: Today, Last 7 days, Last 30 days (our full window), plus a **month picker** for archive access. This mirrors CityProtect's default 7/30-day toggle and SpotCrime's day/week/month view switch. We do NOT have hour-level data, so no "last 24h" vs "today" distinction is meaningful beyond calendar-day boundary — keep it simple.
- **Sparse days**: given the sample data (multiple incidents cluster on the same 1-2 days, other days empty), a per-day view would look broken/inconsistent. Convention among reviewed products facing similarly sparse local data (smaller police.uk neighbourhoods) is to roll up to week/month by default and only show day-level detail inside an individual incident's own metadata (which we already do via the `date` field on each card), not as a navigational granularity of its own.
- Month-archive access should reuse the exact same monthly-bucket grouping already implemented in `news.astro` (`monthGroups` keyed by `YYYY-MM`) — this is a proven, already-shipped pattern, just needs to extend past the 30-day window into `data/incidents/archive/*.json`.

## (c) Geographic faceting

- **Drill-down (16→346) is the primary pattern**, confirmed via police.uk (force → neighbourhood) and CityProtect (state/metro → city). A **typeahead search** should run in parallel as a secondary path for users who know their target comuna (we already have this exact search built for the comuna directory in v1.2 — reuse, don't rebuild).
- **Map-as-filter**: clicking a region/comuna on the choropleth should narrow the news list to that geography — this is the CityProtect/SpotCrime map-view convention. **What breaks**: (1) sync direction ambiguity — does filtering the list move the map, or only map-clicks filter the list? Reviewed products generally make this one-directional (map click → filters list) to avoid state-thrashing; making it bidirectional is a known complexity/bug source. (2) At comuna granularity with sparse incident data, a map click on an empty comuna produces an empty list — must pair with the empty-state handling from (a). (3) Zoom/pan state vs filter state can desync if not carefully scoped — recommend keeping the news-layer filter driven by explicit selection (click a polygon) rather than implicit viewport bounds, since Leaflet viewport-based filtering adds real complexity for uncertain benefit at this data volume (order of magnitude: dozens to low hundreds of live incidents, not thousands).
- Region facet needs no new data — `region_id` is already derivable from `cut` at build time via the existing CUT-length-derivation logic used elsewhere in the codebase (Tarapacá fix precedent).

## (d) Event grouping UX

- **Cluster-card pattern** ("N sources report this") is the standard resolution across news aggregators facing the exact republishing problem visible in our own sample data (Google News "Full coverage", GDELT event clustering). The card shows one primary headline/summary plus a visible list or expandable "N other sources" affordance — never a silent merge.
- **Failure mode users notice most**: wrong merges (two genuinely different incidents collapsed into one, or one incident split across two cards because titles/details diverged too much for the clustering heuristic). Mitigation used by comparable products: always keep the constituent article list visible/expandable (not hidden behind another click), and prefer under-merging (leave as separate cards) over over-merging when confidence is borderline — this needs to be an explicit acceptance criterion for the Phase 26 clustering spike's precision/false-merge-rate GO/NO-GO gate already planned.
- Because our schema's `id` is `sha256(url)[:16]` (per-article, not per-event), any clustering implementation needs a **new** grouping key (e.g., `event_group_id`) assigned by the LLM step and stored alongside existing fields — this is new schema surface, not a derivation of existing fields, and should be scoped explicitly in the Phase 26/27 plan.
- Attribution constraint interacts directly here: a clustered card MUST still expose every constituent `outlet` + `url` — this is non-negotiable per project constraints, not just good UX.

## (e) Map layer + filter discoverability

- **Desktop pattern**: a persistent, labeled control (not nested inside a generic hamburger or "mode" toggle) — commonly a small panel/toolbar docked to a map corner with clearly labeled toggles (layer switcher pattern used by Google Maps, Citizen, most Leaflet-based products via `L.control.layers`). The existing `Legend` component's bottom-left position is a reasonable anchor to extend into a fuller control cluster, but the toggle itself needs its own explicit, always-visible label/icon — "buried in mode-toggle" is the exact known-bad pattern being reported as broken today.
- **Mobile pattern (375px)**: bottom sheet (partially visible, drag-up-to-expand) or a floating action button (FAB) opening a filter panel — this is the converged modern pattern (Google Maps, Citizen, Uber-style map apps). A **known-bad pattern** to explicitly avoid: filters/layer-toggle only reachable via a top hamburger menu that requires navigating away from the map view — this defeats the point of a spatial filter tool and is very likely a contributor to the current discoverability problem flagged in PROJECT.md.
- **Known-bad patterns to flag and avoid** across all reviewed products' post-mortems/community complaints: (1) layer toggle with no visual state indicator (unclear if it's currently on/off), (2) filter panel that fully occludes the map on mobile with no visible "still filtering" indicator once collapsed, (3) filters that reset unexpectedly on navigation/back button, (4) tiny tap targets under ~44px on mobile controls. These map directly onto testable acceptance criteria for Phase 29's BrowserOS iterative design loop and Phase 30's implementation.
- Must remain keyboard-operable and degrade to a zero-JS-safe state per existing site conventions (the WR-03 checkbox-based mobile-nav precedent is the established technique here — reuse the pattern class, not necessarily the exact markup).

---

## Constraint Risk Flags

| Constraint | At Risk From | Mitigation |
|---|---|---|
| **SSG / pre-rendered indexable HTML** | Any faceting/clustering UI that renders content only after client JS runs | Build-time facet counts + pre-rendered base `/news/`; JS is progressive enhancement only, exactly as `news.astro` already does for month-grouping |
| **Never "seguro/peligroso" absolute framing** | Heat-map/density visualization; severity scoring; sparse-day framing that reads as "nothing happens here" or "this is a hotspot" | Reject heat-map anti-feature; use neutral incident counts only; frame rollups editorially soberly, matching existing glossary tone ("incidencia reportada", never "zona peligrosa") |
| **Every incident cites + links its press source** | Silent event-merging that hides constituent articles/outlets | Cluster cards must always expose the full source list (expand-on-click acceptable, hiding entirely is not) |
| **20,000-file Cloudflare Pages free-tier limit** | Over-generating programmatic facet-combination pages (e.g., region × comuna × family cross product) | Scope any new indexable facet pages conservatively (region-level and top family-level only); keep deep cross-product filtering to client-side/query-param state, not new static routes |

## Sources

- `.planning/PROJECT.md` — milestone scope, constraints, existing feature inventory (primary source of truth for this project)
- `site/src/pages/news.astro` — current `/news/` implementation, read directly
- `pipeline/news/schema.py` — `IncidentRecord`/`IncidentsFile` field contracts, read directly
- `data/incidents/current.json` — live incident sample, read directly (confirms multi-outlet same-event republishing already occurring, e.g. three separate Lo Prado shooting articles same day)
- `site/src/components/map/MapIsland.tsx` — existing map toggle/legend structure, read directly
- CLAUDE.md project conventions and constraint statements
- Product-pattern claims (police.uk, CityProtect/LexisNexis Community Crime Map, SpotCrime, Citizen, GDELT/Event Registry, Google News "Full coverage") — drawn from training knowledge of these products' documented/observed UX conventions; MEDIUM confidence on structural pattern claims (converge across all products), LOW confidence on any specific numeric claim not independently re-verified live in this pass — recommend a lightweight live click-through of police.uk and CityProtect during Phase 29's BrowserOS design loop to firm this up before finalizing the control-shell design
