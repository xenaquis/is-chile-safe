# Phase 15: Crime-Type SEO Ranking Pages - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Source:** plan-phase session decisions (no discuss-phase; decisions captured live during planning)

<domain>
## Phase Boundary

Programmatic bilingual "las N comunas con más {delito}" / "communes with the most {crime}" ranking pages that capture long-tail SEO, are static/indexable, correctly internally linked to comuna/region pages, with reciprocal hreflang, sitemap entries, single keyword H1, unique title/meta/canonical, and `ItemList` JSON-LD. Sober editorial tone preserved (reported-incidence framing, CEAD cited).

Builds on Phase 13 (SEO schema patterns) and Phase 14 (homicide data). Reuses the existing `crime/[family].astro` template pattern — copy, don't invent.

</domain>

<decisions>
## Implementation Decisions (LOCKED this session)

### Scope — which ranking pages ship
- Ship ranking pages for the crime categories that have HONEST data in the dataset now: **homicidios** (from `featured_rates.homicidios[latestCompleteYear]`) plus the **7 pre-aggregated families** available in `series[].by_family`: `vida`, `robos_violentos`, `vif`, `drogas`, `armas`, `propiedad`, `incivilidades`.
- **Deferred (data not available at required granularity):** standalone **hurtos** (only inside `propiedad`), **secuestros** (empty in all 346 comunas; CEAD gives no valid subgroup id), **manejo en estado de ebriedad** (only inside `incivilidades`). These need a Python/CEAD pipeline expansion — out of scope for Phase 15, candidate for a follow-up phase.

### Framing — honesty over catchiness
- Each page is titled by **what the data actually measures** (honest broad label, e.g. "delitos de drogas", "robos violentos"), NOT a narrower catchy label the data doesn't support.
- Each page includes a **methodology note** listing exactly which delitos the CEAD family aggregate includes, citing CEAD as source, with reported-incidence framing.
- Must pass `forbidden-language.mjs` and the `buildItemList` `assertSafeName` editorial guard (no "safe/dangerous/safest/most dangerous" in ItemList name).

### URL namespace
- New EN namespace: `/crime-ranking/[crime]/` (avoids collision with existing `/crime/[family]/` overview pages — `/crime/homicide/` already taken by the Life Crimes family overview).
- ES namespace: `/es/ranking-delito/[crime]/` (hardcoded ES slug — getRelativeLocaleUrl does NOT translate slugs; see i18n-localized-slug-pitfall).

### Aggregation point
- Compute rankings at **build time** in Astro `getStaticPaths`, exactly as existing `crime/[family].astro` does. No new Python pipeline step for the in-scope categories.
- Homicidios is the special case: read `featured_rates.homicidios`, NOT `by_family` (using the wrong field returns 0 for all comunas).

### Claude's Discretion
- Value of N (how many comunas per ranking) — pick a sensible default consistent with existing ranking/SEO pages.
- Exact methodology copy wording (in `site/src/lib/familyDefs.ts` entries, bilingual).
- Internal-link row target resolution via existing comuna/region URL helpers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### SEO ranking page pattern (reuse)
- `site/src/pages/crime/[family].astro` + `site/src/pages/es/delito/[family].astro` — exact template: getStaticPaths, buildItemList, buildBreadcrumb, BaseLayout props, loadIndex/loadCommune
- `site/src/lib/jsonld.ts` — `buildItemList` (with `assertSafeName` editorial guard), JSON-LD injection
- `site/src/lib/familyDefs.ts` — crime family definitions + methodology copy (add new entries here)

### Data
- `data/cead/comunas/13101.json` (sample shape), `data/cead/meta/catalog.json`, `pipeline/cead/catalog.py` (`FAMILIA_IDS`) — confirms 7 family keys + `featured_rates.homicidios` / empty `secuestros`

### Validators (must pass)
- `site/scripts/seo.mjs` — extend SAMPLES with first-subdir heuristic for `/crime-ranking/` prefix
- `site/scripts/forbidden-language.mjs` — FORBIDDEN_TERMS the page bodies must avoid

### Research
- `.planning/phases/15-crime-type-seo-ranking-pages/15-RESEARCH.md` — full data mapping + slug proposals + validator verification

</canonical_refs>

<deferred>
## Deferred Ideas

- Standalone **hurtos**, **secuestros**, **manejo en estado de ebriedad** ranking pages — require CEAD/pipeline subgroup-fetch expansion. Candidate follow-up phase.

</deferred>

---

*Phase: 15-crime-type-seo-ranking-pages*
*Context captured: 2026-06-16 during plan-phase session*
