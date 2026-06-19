# Phase 19: Tech-Debt Sweep - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Seeded from v1.3 swarm review (discuss skipped; review findings ARE the spec)

<domain>
## Phase Boundary

Eliminate accumulated tech debt so the bilingual site has no internal contradictions: methodology math correct, ES prose uses "comuna", all pages have reachable EN/ES counterparts, stale placeholders gone, news newest-first, incident URLs scheme-guarded, structural SEO (robots.txt, hreflang pairs, glossary spine) in place.

Requirements: TD-01..07, BIL-01..04, SEO-01..03 (14 total).
</domain>

<decisions>
## Implementation Decisions (locked — from v1.3-DECISIONS.md + review)

- **COMU-03 (TD-04):** REDIRECT `/crime/homicide/` to its canonical target — do NOT keep two URLs with a note. Determine exact target during planning (likely the vida/life-crimes ranking or a renamed `life-crimes` slug). See `vida-homicide-slug-collision` memory: `FAMILY_SLUGS.vida = {en:'homicide', es:'homicidios'}`.
- **TD-01 (MC-01/07):** The methodology pages currently CLAIM "population-weighted"; `data.ts:13-17,211` computes an UNWEIGHTED mean. The FAQ (is-chile-safe.astro:43) is CORRECT. Fix the methodology EN/ES to match the FAQ + data.ts ("unweighted mean … a typical-commune figure, not a true per-capita average"). Do NOT change `data.ts` — the code is the source of truth.
- **BIL-01 (BP-02):** Replace user-visible "commune"→"comuna" in ES files; do NOT touch JS identifiers (`communeCount`, `loadCommune`). Includes meta descriptions + JSON-LD + RateTooltip labels.
- **TD-05 (CQ-01/02):** Use `new URL()` + protocol whitelist (http/https), mirroring `site/src/components/map/IncidentPinLayer.ts`'s existing safe pattern. Fix BOTH frontend (`news.astro:105`, `es/noticias.astro`) AND pipeline (`pipeline/news/store.py:43` build_incident/canonical_url).
- Legal-safe tone preserved; bilingual EN/ES parity preserved; no new displayed metric (reserved for Phase 18).

### Claude's Discretion
Exact file edits, redirect mechanism (Astro static redirect vs meta-refresh — prefer config/static), and i18n key names for BIL-04 string extraction.
</decisions>

<code_context>
## Existing Code Insights — finding → location (from v1.3-REVIEW-FINDINGS.md)

- **TD-01/MC-01:** `site/src/pages/methodology.astro:191-195`; `es/metodologia.astro:193` (weighted claim) vs `site/src/lib/data.ts:13-17,211` (unweighted). FAQ correct at `is-chile-safe.astro:43`.
- **TD-02:** `site/src/config/i18n.ts` key `map_placeholder_text`; rendered via `site/src/components/MapPlaceholderSlot.astro` — find callers, remove/retire.
- **TD-03/IN-03:** `site/src/pages/news.astro`, `es/noticias.astro` — sort `incidents` by `date` desc before render.
- **TD-04/COMU-03:** `site/src/config/i18n.ts:406` FAMILY_SLUGS.vida; page `site/src/pages/commune/[slug].astro:244-250` / `crime/[family].astro`.
- **TD-05/CQ-01:** `site/src/pages/news.astro:105` (+ ES) fragile `startsWith` URL guard. **CQ-02:** `pipeline/news/store.py:43`.
- **TD-06/DQ:** `data/cead/map-payload-*.json` generator (in `pipeline/`) — add `partial_year` flag.
- **TD-07:** PROJECT.md tech-debt line — `FAMILY_KEYS` order CI assertion, typed `by_family`, dynamic `AVAILABLE_YEARS`, `nyquist_compliant` flags phases 4-6, remove skipif/xfail cruft (`pipeline/tests/`).
- **BIL-01/BP-02:** `site/src/pages/es/seguridad-{concepcion,valparaiso,vina-del-mar}.astro`, `mapa-seguridad-santiago.astro`, RateTooltip — "commune"→"comuna" (≥7 files).
- **BIL-02/BP-01:** `site/src/pages/es/delitos-por-region.astro:31-32` (enPath==esPath==self) — create reciprocal EN `/crimes-by-region/` OR document + fix toggle.
- **BIL-03/BP-03:** `es/seguridad-valparaiso.astro:126` "la adjacent ciudad" → "la ciudad vecina".
- **BIL-04:** hardcoded headings — `commune/[slug].astro:224,232,239` + es; `crime/[family].astro:221-225,252` + es; `crime-ranking/[crime].astro:253-257,284` + es; CookieConsent.astro:17-20. Extract to `i18n.ts`.
- **SEO-01:** `is-santiago-safe.astro:70-71` self-hreflang → pair with `/es/mapa-seguridad-santiago/`.
- **SEO-02:** create `site/public/robots.txt` (Allow + Sitemap: https://ischilesafe.com/sitemap-index.xml).
- **SEO-03:** Glossary into `PageHeader.astro`/`PageFooter.astro` nav (`/glossary/`, `/es/glosario/`); explicit ranking allow rule in `astro.config.mjs:55-85` before catch-all.

## Canonical References
- `.planning/v1.3-REVIEW-FINDINGS.md` (full findings + file:line + adversarial verdicts)
- `.planning/v1.3-DECISIONS.md` (decisions a-d)
- `.planning/REQUIREMENTS.md` (TD/BIL/SEO acceptance)
- Memories: `i18n-localized-slug-pitfall`, `vida-homicide-slug-collision`, `astro-script-no-expr-interpolation`, `onedrive-build-artifacts-desync`, `news-page-build-path-drift`.
</code_context>

<specifics>
## Hard constraints (execution)

- **OneDrive build desync:** ALWAYS chain `cd site && npm run build && npm run validate` in ONE command — dist/ vanishes between processes.
- Legal-safe tone (no absolute "safe/dangerous" / "seguro/peligroso" non-attributed). EN/ES parity. Static-JSON store.
- Verify with the existing validators (12/12) + pipeline pytest after changes.
</specifics>

<deferred>
## Deferred Ideas

- Methodology figure registry + INE/ENUSC/SPD source entries → Phase 20 (MTH/SRC).
- Composite index / new metrics → Phase 18.
</deferred>
