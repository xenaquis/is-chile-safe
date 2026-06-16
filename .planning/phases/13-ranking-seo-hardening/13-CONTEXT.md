# Phase 13: Ranking SEO Hardening - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Add the SEO/structured-data signals an earlier audit found missing — **purely additive, no content changes**. Two deliverables:
1. **OpenGraph + Twitter Card meta** injected **site-wide via `BaseLayout.astro`** (og:title/description/image/url/type + Twitter card), locale-correct.
2. **`ItemList` JSON-LD** on ranking tables (rank position + comuna link + rate) and **`BreadcrumbList` JSON-LD** wherever a visual breadcrumb renders; both validate (offline) against schema.org shape, with a build check asserting presence on sampled templates.

**In scope:** OG/Twitter meta in BaseLayout; ItemList JSON-LD across all ranking tables; BreadcrumbList JSON-LD on pages with a visual breadcrumb (comuna/region/crime-type); a new build validator; static per-page-type OG images.

**Out of scope (deferred):** dynamically generated per-page OG card images (satori/@vercel-og) → future enhancement; any copy/content/layout change to the pages themselves; new ranking pages or data (those are Phases 14/15); AdSense consent mode (separate concern).

**Boundary note:** This phase consumes the visual breadcrumbs shipped in Phase 12 and the single `jsonLd` slot already present in BaseLayout. It changes head meta + structured data only — never the rendered body content. Editorial rule still applies: structured data must never imply a territory is absolutely "safe/dangerous".
</domain>

<decisions>
## Implementation Decisions

### OpenGraph / Twitter meta (RSEO-01)
- **D-01:** Inject OG (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:locale`) + Twitter Card meta **site-wide in `BaseLayout.astro` `<head>`** — the same single inject point that already handles hreflang/canonical. No per-page frontmatter duplication.
- **D-02:** **Reuse existing text** — `og:title` = the page `<title>`, `og:description` = the page meta description (both already passed per-locale into BaseLayout). DRY, no double-maintenance, inherits the existing non-absolute phrasing.
- **D-03:** **og:image = static images per page TYPE** (home, comuna, region, ranking, editorial), stored under `site/public/og/`, referenced as absolute `https://ischilesafe.com/og/<type>.<ext>`. BaseLayout selects the image from a page-type signal (a new optional prop, e.g. `ogType`/`pageType`), with a site-wide default fallback. **Twitter card = `summary_large_image`** (the large preview the per-type images enable). NOT a single site-wide image; NOT per-page generated cards (deferred).
- **D-04:** `og:url` = the lang-correct canonical already computed in BaseLayout (`enPath`/`esPath`). Emit `og:locale` per `lang` + an `og:locale:alternate`. `og:type` defaults to `website`, `article` for editorial pages (exact mapping = Claude's discretion).

### ItemList JSON-LD (RSEO-02)
- **D-05:** **Full coverage** — emit `ItemList` JSON-LD on every ranking table: regional ranking (region pages + the ficha's regional context), `/crime/[family]` + `/es/delito/[family]`, the home's two lead tables (lowest/highest), the `/rankings/` index, and the ficha "similar comunas" table.
- **D-06:** ListItems carry `position` + `url` (the comuna page) + `name`; include the **rate** where the table shows an absolute reported rate (regional, crime-type, home lead). For the semantically weaker tables: `/rankings/` index = ItemList of links (`position`+`url`+`name`, no rate); **"similar comunas" position reflects the displayed proximity order, NOT a safety ranking** — represent honestly, never as a rate-rank. Structured data must never imply absolute safe/dangerous.

### BreadcrumbList JSON-LD (RSEO-02)
- **D-07:** Emit `BreadcrumbList` JSON-LD **only where a visual breadcrumb renders** — comuna, region, and crime-type pages (per SC2). Home and `/rankings/` have no visual breadcrumb → no BreadcrumbList there. Mirror the exact visual hierarchy + per-locale labels (the Phase-12 comuna breadcrumb is `Inicio › Comunas › Región › Comuna`).

### JSON-LD emission mechanism
- **D-08:** A single page can need BOTH `BreadcrumbList` + `ItemList` (e.g. region/crime-type pages). BaseLayout's `jsonLd` prop currently accepts ONE object — **extend it to accept `object | object[]`** (emit one `<script type="application/ld+json">` per object) **or** a schema.org `@graph`; pick whichever is cleanest + schema-valid (Claude's discretion / confirm in research). **Preserve the existing XSS-safe `JSON.stringify(...).replace(/<\//g,'<\\/')` handling.**

### Validation (RSEO-01 / RSEO-02)
- **D-09:** **Sampled validator** — a new build-time validator (mirror Phase-12 `spine.mjs` ESM pattern, reads `dist/`) asserts OG/Twitter meta + JSON-LD presence on **one representative page per template type** (home, comuna, region, crime, ranking, editorial) × both locales. Register it in `site/scripts/validate/all.mjs`. Not all 774 pages — templates are the only source of variation.
- **D-10:** "Validate against schema.org" = **offline shape check** (no network, keeps ~$0 build): parse each JSON-LD block and assert `@context`/`@type` + required fields — `ItemList`: `itemListElement[].position` + `url`; `BreadcrumbList`: `itemListElement[].position` + `name` + `item`.

### Claude's Discretion
- Exact `og:type` mapping per template; `og:locale` value form (`en_US`/`es_CL` vs `en`/`es`); per-type OG image filenames + dimensions (1200×630 standard) and the default-fallback image; `jsonLd` as array-of-scripts vs `@graph`; which exact URLs are picked as each "template type" for the sampled validator.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope + requirements
- `.planning/ROADMAP.md` § "Phase 13: Ranking SEO Hardening" — goal + success criteria (OG/Twitter site-wide; ItemList + BreadcrumbList validated).
- `.planning/REQUIREMENTS.md` — RSEO-01 (OG/Twitter via base layout, per-locale) + RSEO-02 (ItemList on ranking tables, BreadcrumbList where breadcrumb visible, schema.org validation, sampled build check).

### Inject point + structured-data hook
- `site/src/layouts/BaseLayout.astro` — head meta (title/description/hreflang/canonical/PWA) + the existing single `jsonLd?: object` slot injected XSS-safely via `JSON.stringify(...).replace(/<\//g,'<\\/')`. OG/Twitter + JSON-LD multiplicity land here.

### Ranking tables → ItemList source
- `site/src/components/CommuneRankingTable.astro` — the shared ranking table used by home lead tables, `/rankings/`, the ficha "similar comunas", and (regional/crime) rankings. One component is the natural ItemList emission point.

### Breadcrumbs → BreadcrumbList source (shipped Phase 12)
- `.planning/phases/12-home-ia-redesign-comuna-page-hub-and-spoke/12-CONTEXT.md` — D-09 visual breadcrumb `Inicio › Comunas › Región › Comuna`.
- `site/src/pages/commune/[slug].astro` + `site/src/pages/es/comuna/[slug].astro` — comuna breadcrumb (4-level).
- Region pages (`site/src/pages/region/[slug].astro` + ES) and crime-type pages (`site/src/pages/crime/[family].astro` + `site/src/pages/es/delito/[family].astro`) — other visual breadcrumbs.

### Validator pattern + i18n
- `site/scripts/validate/spine.mjs` + `site/scripts/validate/all.mjs` — Phase-12 validator pattern to mirror + register the new SEO validator.
- `site/src/config/i18n.ts` — per-locale strings (any new social/SEO strings, og:locale values).
- Project memory `i18n-localized-slug-pitfall` — ES slugs hardcoded per-locale; `og:url`/canonical/image URLs must use the locale-correct hardcoded paths, never `getRelativeLocaleUrl` for ES slugs.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`BaseLayout.astro`** — already the single SEO inject point (hreflang/canonical/PWA + `jsonLd` slot). Adding OG/Twitter here covers every page at once (RSEO-01). The XSS-safe JSON-LD injector already exists — extend it for multiple blocks.
- **`CommuneRankingTable.astro`** — one shared component behind all ranking tables; emitting ItemList here (or alongside it) covers home/rankings/region/crime/similar in one place (RSEO-02 / D-05).
- **`spine.mjs`** — Phase-12 dist-reading validator establishes the exact ESM pattern (`let failures=0`, recursive HTML scan, `process.exit(1)`) for the new sampled SEO validator (D-09).

### Established Patterns
- **Centralized SEO injection** — hreflang/canonical are already central in BaseLayout; OG/Twitter follow the same rule (never per-page frontmatter).
- **XSS-safe JSON-LD** — `JSON.stringify(obj).replace(/<\//g,'<\\/')` via `set:html`; preserve when going to multiple blocks / `@graph`.
- **ES localized slugs hardcoded per-locale** — `og:url`, `og:image` absolute URLs, and BreadcrumbList `item` URLs must be locale-correct hardcoded paths.
- **Editorial rule** — never label territories absolutely safe/dangerous; ItemList/BreadcrumbList must inherit the existing CEAD-attributed, reported-incidence framing.

### Integration Points
- BaseLayout props: add a page-type / og-image signal + widen `jsonLd` to `object | object[]` (or `@graph`).
- Ranking tables emit/accept ItemList; breadcrumb-bearing templates emit BreadcrumbList; the new validator hooks into `all.mjs`.
- Static OG images live in `site/public/og/` (served at `/og/...`).
</code_context>

<specifics>
## Specific Ideas

- OG images are **per page TYPE**, not per page and not one-for-all — a curated handful (home / comuna / region / ranking / editorial), enabling `summary_large_image`.
- ItemList coverage is **total** but **honest**: weaker-semantic tables (`/rankings/` index, "similar comunas") use ItemList for position+link only and must not present proximity/index order as a safety ranking.
- Validation is **sampled per template type** with an **offline** schema.org shape check — no network calls, consistent with the ~$0 build constraint.
</specifics>

<deferred>
## Deferred Ideas

- **Dynamically generated per-page OG card images** (satori / @vercel-og with comuna name + rate) → future enhancement; static per-type images ship now.
- Any change to page copy/content/layout to "improve SEO" → out of scope; this phase is additive meta/structured-data only.

### Reviewed Todos (not folded)
- `adsense-consent-mode-phase6.md` — weak keyword match ("phase") only; it's about AdSense consent mode, unrelated to OG/JSON-LD SEO. Not folded; remains its own AdSense concern.
</deferred>

---

*Phase: 13-ranking-seo-hardening*
*Context gathered: 2026-06-15*
