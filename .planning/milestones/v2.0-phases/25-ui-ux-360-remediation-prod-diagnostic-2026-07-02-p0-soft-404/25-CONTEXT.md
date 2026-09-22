# Phase 25: UI/UX 360 remediation (prod diagnostic 2026-07-02) - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Execute ALL fixes from `.planning/UI-360-DIAGNOSTIC-260702.md` (2026-07-02 production audit of ischilesafe.com; screenshot evidence in `C:\Users\Carlo\bos-shots\`). **The diagnostic report is the authoritative spec — planner and executors MUST read it in full.** Work follows the report's "Orden sugerido para la fase de mejora":

1. **P0-1 soft-404**: every unknown URL serves the home with status 200 (`canonical=/`, `robots=index,follow`). Check `public/_redirects` / Cloudflare Pages config; remove any `/* /index.html 200` catch-all; create a real `404.html` (Cloudflare Pages serves it with status 404 automatically when no catch-all exists). `/favicon.ico` currently returns 200 `text/html` via the same catch-all.
2. **P0-3 favicon**: none exists. Create favicon (.ico + .svg) + `<link rel="icon">` in the base layout.
3. **P0-2 tablet overflow 640–1080px**: at 772px viewport `scrollWidth=1077` (~305px horizontal scroll). Culprits: `nav.csm-nav` (collapses to hamburger too late), `.header-right`/`.lang-toggle`, and the two home `.lead-table-col` (504px each, no wrap). Fix: collapse nav to hamburger ≤1100px; stack home lead-table columns ≤900px; shorten nav item "Crime type glossary" → "Glossary"/"Glosario".
4. **P1-1 number formatting**: single `formatNumber(value, locale)` helper using `Intl.NumberFormat`, used by ALL islands and static components. Known bugs: MapIsland shows "~4.984" (ES thousands separator) in EN UI; ES page `/es/comuna/nunoa/` "Similar Communes" table shows EN-format "4,991"; `/compare/` rates lack thousands separator ("2871.5") and homicide has 2 decimals vs 1 elsewhere.
5. **P1-3 map**: initial view shows Chile as thin strip on the left (60%+ canvas is Argentina/ocean) — `fitBounds` to continental-Chile bbox + `maxBounds`; legend takes ~40% of map height on 375px — collapsible/compact mobile legend; Index/By-crime pills overlap search input — stack in 2 rows ≤480px; incident pins nearly same orange as "High" choropleth level — distinctive color/shape + legend entry when layer active; pre-fetch guard for unknown `?cut=` (fetch currently fires and 404s).
6. **P1-5 editorial visuals**: `/is-santiago-safe/` (916 words, zero visuals), `/is-chile-safe/`, `/safest-cities-in-chile/` — add top/bottom-10 comuna rate tables and sparklines **generated statically at build time from `public/data` JSON** (must land in the HTML; nothing client-only).
7. **P1-6 news**: 129 items in flat list; card titles are not headings (0 h2/h3 on the whole page); no comuna/crime-type chip per card; no date grouping/pagination. Also harden the Python pipeline classifier filter — traffic accidents (e.g. "Collision leaves at least one dead… in Carahue") published as crime incidents; exclude them.
8. **P1-2 compare**: big number ("39.0 Very High") unlabeled — add "Composite Crime Index" label + link to methodology (also covers editorial-restriction exposure of bare "Very High"); selection not in URL — sync `?a=&b=` via `history.replaceState`; empty state bare — add popular-comparison chips (Santiago vs Las Condes, Providencia vs Ñuñoa…); ALL trends render "→" — verify the island actually receives trend data and not a default.
9. **P1-4 map panel years**: one panel mixes Composite Index (2024), Rate (2025), evolution (2005–2026), and two rank systems (#158 composite vs #169 rate). Group blocks visually by year with a year badge + "?" tooltip explaining why years differ (tooltip pattern already exists); drop the unexplained "~" prefix.
10. **P2 sweep**: ~130 unnamed buttons (Leaflet incident markers) — `aria-label` with incident title (or `aria-hidden` + alternative list); `outline:none` on link focus + no skip-link — global `:focus-visible` + skip-to-main; JSON-LD `WebSite` (+SearchAction) and `Organization` on home; `/rankings/` "By region" must link all 16 regions; region KPI "#13 of 16" needs direction ("1 = highest reported"); "(1 cases)" pluralization EN/ES; region evolution title says "(2005–2025)" but chart includes partial 2026 bar.

**Out of scope** (report's "Lo que está BIEN — no tocar"): commune page architecture, region table, editorial discipline/attribution copy, i18n slugs, commune search autocomplete, news pipeline sources/freshness. P2-4 performance: nothing to do. P2-2 home-title/cannibalization decision: only do the additive JSON-LD + rankings interlinking; do NOT re-target home vs /is-chile-safe/ H1s in this phase (content-strategy decision, defer).

</domain>

<decisions>
## Implementation Decisions

### Sequencing (from the report)
1. P0-1 404 real + P0-3 favicon → 2. P0-2 breakpoints → 3. P1-1 formatNumber → 4. P1-3 map → 5. P1-5 editorial visuals → 6. P1-6 news → 7. P1-2 compare (+P1-4 panel) → 8. P2 polish sweep.
**Each P0 item is its own independent atomic commit, first.**

### Hard constraints (editorial/data/infra — violating any is a blocker)
- NEVER label territories as safe/dangerous in absolute terms; always attribute (CEAD, medio). "Very High" etc. must be tied to the named index.
- rank #1 = MOST reported crime (descending by incidence). Directional labels must say "1 = highest reported".
- Rates in `by_family`/`featured_rates` are ALREADY per-100k — never rescale; large values in small/touristic communes are correct.
- `getRelativeLocaleUrl` does NOT translate ES slugs — hardcode `/es/mapa`, `/es/noticias`, `/es/comuna/...` etc. for nav/cross-links.
- All critical content must be pre-rendered static HTML (SEO) — new editorial visuals must be in the build output, not client-rendered.
- Astro renders `{expr}` literally inside `<script>` — use `set:html` or `data-*` attributes to pass server data to client JS.
- Repo lives in OneDrive: chain build+validate in ONE command or `dist/` vanishes between processes.
- DeepSeek model IDs: only `deepseek-v4-flash`/`deepseek-v4-pro` (never `deepseek-chat`).

### Claude's Discretion
Remaining implementation choices (exact breakpoint values within the specified ranges, favicon glyph design, sparkline SVG generation approach, pagination vs date-grouping for news, chip styling) are at Claude's discretion, guided by the diagnostic report, existing codebase conventions, and brand tokens.

</decisions>

<code_context>
## Existing Code Insights

- Verification method: `npx astro build` then `npx astro preview --port 4321 --host` (no `npm run preview` script), BrowserOS review INLINE in orchestrator (subagents lack browseros tools); screenshots to a no-spaces path (`C:\Users\Carlo\bos-shots\`); mobile emulated via 375px iframe (BrowserOS lacks viewport resize).
- `?cut=` deep-link guard was flagged in v1.2 as pending polish — confirm current state in MapIsland before re-implementing.
- Tooltip "?" pattern already exists on commune/map panels — reuse for P1-4 year explanation.
- `/compare/x-vs-y/` pre-generated pages already exist (Phase 21) — the compare island URL sync should align with those slugs.
- `RankingTableEnhancer` (Phase 24) is the existing pattern for progressive table enhancement.
- `FAMILY_SLUGS.vida.en === 'homicide'` — any byFamily loop must filter `vida` or it emits a duplicate mislabeled homicide link.
- News pipeline: Python, DeepSeek v4-flash classifier, name→CUT resolver; data lands in `public/data/incidents/current.json` (refreshed by cron).

</code_context>

<specifics>
## Specific Ideas

- 404 page: bilingual, links to home/map/rankings, no thin-content indexing risk (it serves with real 404 status so it won't be indexed).
- Favicon: simple mark consistent with site brand (map-pin / Chile silhouette motif), `.svg` primary + `.ico` fallback + `apple-touch-icon` if cheap.
- Popular-comparison chips: Santiago vs Las Condes, Providencia vs Ñuñoa, Viña del Mar vs Valparaíso (or similar high-traffic pairs).
- News classifier: exclude traffic accidents/collisions without criminal component at the prompt/filter level in the Python pipeline; keep closed-list classification at temperature 0.0.

</specifics>

<deferred>
## Deferred Ideas

- P2-2 home vs `/is-chile-safe/` keyword cannibalization re-targeting (content strategy — needs user decision).
- Home `<title>` lengthening (32 chars → add "crime map"/"by commune 2025") — bundle with the cannibalization decision.
- AdSense CLS measurement — only relevant once ads are inserted.

</deferred>
