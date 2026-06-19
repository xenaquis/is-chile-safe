# Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning
**Source:** discuss-phase interactive session, grounded in validated spikes 001 (home framing) + 003 (comuna spokes) + Phase 11 CONTEXT (directory/nav/slugs).

<domain>
## Phase Boundary

Rebuild the home (EN `/` + ES `/es/`) on the **already-approved Hybrid C+B framing** (spike 001) and turn each comuna page into a **hub that spokes out** to the rest of the site (spike 003), with a coherent bilingual navigation spine. The *framing* is LOCKED by the spikes — this phase is **implementation (HOW)**, not re-deciding WHAT.

**In scope:**
- New wide home layout: editorial/SEO-led above the fold + lead rankings (safest + highest incidence) + "busca tu comuna" search hero + national map as first-class CTA + guide cards to existing editorial pages; condensed editorial prose below the fold; single H1; static/indexable; EN/ES parity.
- Comuna page as hub: spoke links to map (centered), regional ranking, similar comunas (same-region/nearest-rate), per-crime-type rankings; breadcrumb upgraded to `Inicio › Comunas › Región › Comuna` in both locales.
- Navigation spine: add **Rankings** to the primary nav pointing to a **new `/rankings/` + `/es/rankings/` index page** that links existing rankings; a common **footer spine**; reciprocal, 404-free internal links enforced by an extended validator.

**Out of scope (deferred — see `<deferred>`):**
- Comuna-page **news spoke** + a **Noticias** nav/spine node → **Phase 16** (geolocation name→CUT must work first).
- OpenGraph/Twitter + ItemList/BreadcrumbList JSON-LD → **Phase 13**.
- Homicide layer/breakdown → Phase 14. Crime-type SEO ranking pages → Phase 15.

**Boundary note:** Deferring the news spoke means IA-02's "geolocated news" link and IA-03's "noticias" spine node are satisfied in Phase 16, not here. Phase 12 delivers the other 4 spokes + breadcrumb + the rest of the spine. Plan/verify acceptance for Phase 12 against that adjusted boundary.
</domain>

<decisions>
## Implementation Decisions

### Home layout (Hybrid C+B)
- **D-01:** Build a **new wide home layout** (e.g. `HomeLayout` / full-width) for the hero + rankings grid + map CTA + guide cards. Keep `EditorialLayout` (720px) for text pages — do NOT shoehorn the hub into the narrow editorial column.
- **D-02:** **Condense the existing long editorial prose** (the ~5 sections "What the Data Shows / How to Read Crime Rates / About CEAD / Limitations") into a shorter block placed **below the Hybrid C+B fold**, preserving SEO/indexable text without a "wall of text". Above the fold = hero + rankings + map + guides.
- **D-03:** Lead rankings above the fold = **two short tables side by side**: comunas with the lowest rate (más seguras) AND highest rate (mayor incidencia), mirroring spike 001-c. Reuse the existing ranking-table component (`CommuneRankingTable.astro`) where practical.
- **D-04:** Guide cards link to **existing editorial pages only** (Is Chile Safe?, Is Santiago Safe?, Safest cities, Chile Crime Map, Methodology). No new editorial content created in this phase.

### "Busca tu comuna" hero
- **D-05:** Hero is a **static box/form** (most prominent interactive element) that on submit routes to the **directory** `/communes/` (EN) / `/es/comunas/` (ES) carrying the query. **Zero JS in the home root**, fully indexable, no duplication of the Phase 11 finder island.
- **D-06:** Even on an exact comuna match, the user **lands on the filtered directory** (then ≤1 click to the ficha). Keeps the ≤2-interaction findability goal without name→slug resolution logic in the home.

### Comuna page spokes (hub)
- **D-07:** "Similar comunas" = **same region, ordered by nearest rate/100k** (reuses `ComparableCommune.astro`; 100% derivable from current data; reinforces the comuna↔region link). NOT national-nearest-rate, NOT geographic adjacency.
- **D-08:** **Map spoke = a link/CTA** to `/map/` (EN) / `/es/mapa/` (ES) with a **focus parameter** (e.g. `?cut=<cut>` or `#<slug>`) so the map opens centered on the comuna. **Do NOT embed Leaflet** in the ficha (respects D-09 / CLAUDE.md: no `client:*` map on the 346 comuna pages). *Research must verify the map island can read the focus param, or add that capability.*
- **D-09:** **Breadcrumb upgraded** to `Inicio › Comunas › Región › Comuna` in both locales, with the new **Comunas** level linking the directory (`/communes/` ÷ `/es/comunas/`). Today's breadcrumb lacks the Comunas level.
- **D-10:** Add **per-crime-type ranking** spoke links from the ficha to the existing `/crime/[family]` / ES `/delito/[family]` pages (no new pages).
- **D-11:** **No news section is built in Phase 12** — deferred whole to Phase 16.

### Navigation spine
- **D-12:** Add **"Rankings"** to the primary nav → a **new static index page** `/rankings/` + `/es/rankings/` that lists/links the available rankings (más seguras, mayor incidencia, por tipo de delito, por región). This is a small index over existing pages — **no new ranking data**. (Scope addition consciously accepted to satisfy IA-03's "ranking" spine node + nav coherence.)
- **D-13:** Add a **common footer spine** (map / directory / regions / key editorial) for cheap global interconnection, AND **extend the Phase 11 `no-orphan-link` validator** to assert reciprocity + zero 404 across the new cross-links.
- **D-14:** **Do NOT** add a "Noticias" nav/spine entry now — deferred to Phase 16 with the news spoke.

### Claude's Discretion
- Exact focus-param syntax for the map link (`?cut=` vs `#slug`) — choose what the existing map island supports with least change.
- Exact `/rankings/` page composition and the footer's link set — keep minimal, reuse existing pages, create no new content/data.
- Whether to reuse vs lightly extend `CommuneRankingTable.astro` and `ComparableCommune.astro`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Locked framing (validated spikes — read FIRST)
- `.planning/spikes/001-home-hub-framing/README.md` — Hybrid C+B decision (approved 2026-06-15): editorial/SEO above fold + busca-comuna hero + map as first-class CTA.
- `.planning/spikes/001-home-hub-framing/001-c-ranking-led.html` — reference structure for the ranking-led above-the-fold (two lead tables, inline search, region tiles).
- `.planning/spikes/003-comuna-page-spokes/README.md` — hub-and-spoke ficha: map / regional ranking / similar comunas / crime-type rankings / news + breadcrumb spine.
- `.planning/spikes/003-comuna-page-spokes/comuna-page.html` — reference ficha layout (spokes + "#26 de 52 en su región" regional-rank device).

### Prior decisions carried forward
- `.planning/phases/11-publish-346-comunas-finder/11-CONTEXT.md` — directory `/communes/` `/es/comunas/`, finder UX, **ES slugs hardcoded** (getRelativeLocaleUrl does NOT translate ES slugs), region derived from CUT (`cut//1000`), no-orphan-link validator.

### Home (rebuild target)
- `site/src/pages/index.astro` + `site/src/pages/es/index.astro` — current narrow editorial home (the prose to condense lives here).
- `site/src/layouts/EditorialLayout.astro` (keep for text pages) + `site/src/layouts/BaseLayout.astro` (title/meta/canonical/hreflang).

### Comuna page (hub target) + reusable spoke components
- `site/src/pages/commune/[slug].astro` + `site/src/pages/es/comuna/[slug].astro` — existing breadcrumb (~L124), `MapPlaceholderSlot`, sections; region slug resolved via `loadRegion(regionFileId(region_id)).slug`.
- `site/src/components/ComparableCommune.astro` — "similar comunas" spoke (D-07).
- `site/src/components/MapPlaceholderSlot.astro` — current map placeholder on the ficha (becomes the map-spoke link, D-08).

### Nav / spine / i18n
- `site/src/components/PageHeader.astro` — primary nav; **per-locale hardcoded slugs** pattern (`mapHref`, `communesHref`) — add `Rankings` here the same way.
- `site/src/config/i18n.ts` — `EN_STRINGS` / `ES_STRINGS` nav labels (add `nav_rankings`).
- Map memory: `i18n-localized-slug-pitfall` — hardcode `/es/rankings/`, `/es/mapa/`, `/es/comunas/` etc.; never rely on `getRelativeLocaleUrl` for ES slugs.

### Validators / SEO
- `site/scripts/validate/*.mjs` — extend the Phase 11 `no-orphan-link` / coverage validator for spine reciprocity + 404-free new cross-links (D-13).
- `astro.config.*` (@astrojs/sitemap) — add `/rankings/` (+ES) to sitemap coverage.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CommuneRankingTable.astro` — reuse for the home's two lead-ranking tables (D-03) and likely the `/rankings/` index.
- `ComparableCommune.astro` — already implements the similar-comunas spoke (D-07).
- Phase 11 finder/directory (`/communes/`) — the hero routes into it; no need to re-implement search (D-05).
- `PageHeader.astro` per-locale hardcoded-slug pattern — copy it to add the Rankings nav entry safely.

### Established Patterns
- Static-first / zero `client:*` outside the map island (D-09 / CLAUDE.md). Hero + ficha stay JS-free; map stays a link, not an embed (D-05, D-08).
- ES localized slugs are hardcoded per-locale, not derived — applies to every new link added this phase.
- Build validators gate coverage/links (Phase 10–11 precedent) — extend, don't invent a new gate style (D-13).

### Integration Points
- Map island focus param: the ficha map-spoke link depends on `/map/` accepting a comuna focus (`?cut=`/`#slug`) — verify/extend the map island (D-08).
- Region pages `region/[slug]` ↔ comuna pages: reciprocity of the new cross-links is what the extended validator must assert.
</code_context>

<specifics>
## Specific Ideas

- The regional-rank device from spike 003 ("#26 de 52 en su región") is the engagement + internal-link hook that justifies the comuna↔region reciprocal link — keep it on the ficha.
- Two-table lead rankings (más seguras + mayor incidencia) come straight from spike 001-c's above-the-fold.
- Never label territories absolutely "safe/dangerous"; rankings are framed as reported-incidence (CEAD-attributed) per CLAUDE.md editorial rule.
</specifics>

<deferred>
## Deferred Ideas

- **Comuna-page news spoke** (geolocated incidents linking to source ↗ AND back to the comuna) → **Phase 16** — requires the name→CUT geolocation fix to land the right comuna first.
- **"Noticias" nav/spine node** → **Phase 16** (ships with the news spoke + dedicated news page).
- **OpenGraph/Twitter cards + ItemList/BreadcrumbList JSON-LD** on home/rankings/comuna → **Phase 13** (this phase emits the visual breadcrumb; the JSON-LD comes in 13).

None of the above to be implemented in Phase 12 — discussion otherwise stayed within phase scope.
</deferred>

---

*Phase: 12-home-ia-redesign-comuna-page-hub-and-spoke*
*Context gathered: 2026-06-15*
