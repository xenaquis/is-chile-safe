# Phase 11: Publish All 346 Comunas + Comuna Finder - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning
**Source:** plan-phase inline decisions, grounded in this session's live audit + IA spikes 001–003 (user-confirmed: "publicar las 346")

<domain>
## Phase Boundary

Lift the rollout gate so every comuna with CEAD data has a reachable, indexable page, and add a searchable comuna directory so any of the 346 is findable in ≤2 interactions. This is the **"material perdido" fix**: today only 12/346 comunas have pages; the other 334 exist in data and on the map but their map clicks and ranking rows dead-end (404). The pages, routes, render path, and data already exist — Phase 11 is **un-gating + a directory + linking the tables**, not building comuna pages from scratch.

**In scope:** rollout flip (12→346), comuna directory/finder page (EN+ES), wiring region + crime-type ranking tables to link all comunas, sitemap coverage, thin-content guards, a build validator for coverage.

**Out of scope:** the home redesign + comuna-page hub-and-spoke cross-linking (that's Phase 12), ranking SEO schema/OG (Phase 13), homicide/news. Do NOT redesign the comuna page template here beyond what un-gating requires.
</domain>

<decisions>
## Implementation Decisions

### Rollout (LOCKED)
- Publish **all 346 comunas** with CEAD data in both locales (`/commune/[slug]`, `/es/comuna/[slug]`). The gate is `site/src/config/rollout.json` (`enabled[]`, currently 12) read by `loadRolloutCuts()` in `site/src/lib/data.ts:217` (already supports a `ROLLOUT_ALL` env path). Prefer the cleanest "all 346" mechanism (research/plan to choose: `ROLLOUT_ALL=true` as the committed default vs. expanding `enabled[]` to all 346 vs. making 346 the default and keeping rollout as an optional *subset* flag). Whatever is chosen must make 346 the **committed, build-default** behavior (CI/Cloudflare build emits all pages), not env-dependent on a developer's machine.
- Low-population comunas DO get a page (they're excluded from *rankings* per DATA-04, not from existing).

### Comuna Finder / Directory (LOCKED — design validated in spike 002)
- New directory page in both locales (e.g. `/communes/` + `/es/comunas/`), linked from the primary nav and the home. Reuse the validated spike-002 UX: **accent-insensitive search** + **A–Z view** + **by-region view (16 regions)**; each entry links to the comuna page; level dot + rate shown; low-pop tagged.
- Must be static/indexable HTML (the search filter is progressive enhancement over a server-rendered full list — the 346 links exist in the HTML for crawlers, JS only filters). This is the SEO-safe version of the spike.
- Reference prototype: `.planning/spikes/002-comuna-finder/finder.html` (real-data, validated reachability ≤2 interactions).

### Link the tables (LOCKED)
- Region pages (`region/[slug]`) and crime-type pages (`crime/[family]`) currently show all comunas in ranking tables but only **link** the 12 rolled-out ones and print "Showing N of M — more coming soon." Once 346 are published, link **every** comuna and remove the gating message/partial-row logic (`08-01` rollout-row gating is now obsolete for this purpose).

### SEO / thin-content (LOCKED guards)
- Sitemap (`@astrojs/sitemap`) must include all 346×2 comuna URLs + the new directory pages.
- Each comuna page must keep a **unique** `<title>`/meta/canonical/hreflang and have enough unique content — the existing `proseEngine.ts` already generates per-comuna prose; verify it produces non-trivial unique text for low-traffic comunas too (avoid 668 near-duplicate thin pages). If a comuna genuinely lacks data, it should 404 (not ship an empty page).
- A build validator must assert: comuna pages emitted ≈ 346 per locale, sitemap entry count matches, and **zero internal links point to an ungenerated comuna slug** (the inverse of today's bug).

### Verification (LOCKED)
- Automated: `npm run build` emits ~346×2 comuna pages + directory pages; existing + new validators green (route-count, no-orphan-link, sitemap coverage). Spot-check: click-through from map / region table / directory reaches a real page for a previously-orphaned comuna.
- Manual (light): browse the directory in both locales; confirm a deep-region comuna (e.g. a small southern comuna) is reachable in ≤2 interactions and renders.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Rollout + data
- `site/src/config/rollout.json` — the 12-CUT gate (`enabled[]`).
- `site/src/lib/data.ts` — `loadRolloutCuts()` (~L217, has a `ROLLOUT_ALL` path), `CommuneData`, region resolution.

### Comuna pages (un-gate, don't redesign)
- `site/src/pages/commune/[slug].astro` + `site/src/pages/es/comuna/[slug].astro` — `getStaticPaths()` calls `loadRolloutCuts()`; 404 for non-rollout today.
- `site/src/lib/proseEngine.ts` — per-comuna unique prose (thin-content mitigation).

### Tables to wire
- `site/src/pages/region/[slug].astro` + ES — "Showing N of M" gating (~L215), `CommuneRankingTable.astro` (~L60 links).
- `site/src/pages/crime/[family].astro` + ES — national ranking table (~L222), partial-row gating (~L243).

### Directory prototype + data
- `.planning/spikes/002-comuna-finder/finder.html` — validated finder UX (A–Z + region + accent search).
- `data/cead/meta/index.json` — 346 comunas (cut/name/slug/region_id/population/low_population).

### SEO / validators
- `site/src/layouts/BaseLayout.astro` — title/meta/canonical/hreflang injection.
- `astro.config.*` (@astrojs/sitemap) + `site/scripts/validate/*.mjs` — add a comuna-coverage / no-orphan-link validator.
</canonical_refs>

<specifics>
## Specific Ideas

- Region derived canonically from CUT (`cut//1000` → 1–16) for the directory grouping, mirroring the spike.
- The "Showing N of M — more coming soon" string + partial-row gating from Phase 8 (`08-01`) is now obsolete — remove for comuna links once 346 ship.
- Search must be no-JS-degradable: full 346-link list in HTML, JS only filters/groups.
</specifics>

<deferred>
## Deferred Ideas

- Comuna-page hub-and-spoke cross-linking (map/region/similar/news links + breadcrumb) → **Phase 12**.
- OpenGraph/Twitter + ItemList/BreadcrumbList JSON-LD on directory/rankings → **Phase 13**.
- Per-comuna "recent incidents" populated with real data → **Phase 16**.
</deferred>

---

*Phase: 11-publish-346-comunas-finder*
*Context gathered: 2026-06-15 via plan-phase inline decisions (audit + spike 002 informed, user-confirmed)*
