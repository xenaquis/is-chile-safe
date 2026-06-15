# Phase 9: UX / Readability / Accessibility Polish - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Two complementary tracks, both about making what already exists **understandable**, not adding new data capabilities:

1. **Map & data comprehension (primary focus this milestone — user-driven):** a non-expert visitor must understand, without prior knowledge: what a "rate per 100k" means, what each crime family includes, how to read the choropleth colours, and how a commune compares to the average. Work lands on the existing map island and ranking tables.
2. **Editorial readability / a11y polish (original review-driven scope):** the UX-01/02, READ-01..03, A11Y-01/02 items surfaced by the Phase 7 E2E review — H1/heading hierarchy on money pages, callout↔prose deduplication, ~720px prose columns, ES/EN parity, sober tone, WCAG-AA contrast, focus states, alt text, map-control aria, and valid `<title>`/meta/canonical/hreflang/JSON-LD.

**Out of scope (→ v1.2):** interactive commune comparators, "safest/least-safe cities" rankings by crime type, A-vs-B comparison pages, new programmatic ranking pages. These are discovery/SEO *features*, not comprehension of the current view. See Deferred Ideas.

**Editorial constraint (site-wide, non-negotiable):** never label a territory "peligroso/seguro" in absolute terms; use relative framing ("incidencia reportada", "X× el promedio", percentil). Always attribute CEAD + year. Avoid thin content.

</domain>

<decisions>
## Implementation Decisions

### Explaining the "rate per 100k" metric
- **D-01:** Build ONE reusable "?" tooltip/info component that sits next to every displayed rate (map Legend, commune ResultPanel, and the region/crime/commune ranking tables) carrying the short definition, PLUS one fixed plain-language sentence per page. Consistent, low visual noise, serves every surface. Bilingual strings live in `i18n.ts` (the codebase's existing inline-locale pattern). Static/SSR-friendly — no client-only critical content.

### Crime glossary
- **D-02:** Two delivery surfaces, both reusing the existing `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES` definitions (do NOT rewrite them):
  - Per-family tooltip in the map/panel/tables (immediate in-context help).
  - A dedicated bilingual glossary page (`/glossary` EN + `/glosario` ES) that defines each crime family — captures long-tail SEO ("qué es robo con violencia") and gives a canonical link target. Must be real prose (avoid thin content), CEAD-attributed.

### Choropleth legend
- **D-03:** The legend must show, per colour band, the **real numeric range** (e.g. "0–1,500") AND a qualitative label ("muy bajo → muy alto"), plus a "por 100k hab." note. Reuses/extends `Legend.tsx` and the existing color scale (`colors.ts`). Must stay legible on mobile.

### Comparative context for a commune
- **D-04:** Express a commune's standing as a **multiplier vs the average** ("1,8× el promedio nacional" and/or regional) accompanied by a small **comparison bar** (commune vs average). Neutral framing only — never "safe/dangerous". Reuses `loadNationalAverage` / `loadRegionalAverage` from `data.ts`. Lives primarily in `ResultPanel.tsx` (and optionally the commune page).

### Claude's Discretion
- Exact tooltip interaction (hover + tap/focus for touch & keyboard a11y), component naming, and where the once-per-page fixed sentence sits are left to planning — must satisfy A11Y (keyboard-operable, focus-visible).
- Whether the comparison bar also appears on the static commune money page vs only the interactive panel.
- How the original review-driven editorial items (UX/READ/A11Y) are split across plans vs the comprehension track.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 9" — goal + 5 success criteria (the editorial/a11y track).
- `.planning/REQUIREMENTS.md` — UX-01, UX-02, READ-01, READ-02, READ-03, A11Y-01, A11Y-02 definitions.
- `.planning/phases/07-e2e-review-pass/07-REVIEW-E2E-FINDINGS.md` (if present) — the findings that drove UX/READ/A11Y items; verify exact filename in the Phase 7 dir before planning.

### Reusable code (see code_context)
- `site/src/components/map/Legend.tsx`, `ResultPanel.tsx`, `PanelFamilyBars.tsx`, `colors.ts`
- `site/src/lib/data.ts` — `loadNationalAverage`, `loadRegionalAverage`, `loadCommune`
- `site/src/config/i18n.ts` — bilingual strings + `FAMILY_SLUGS`
- `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES` in `site/src/pages/crime/[family].astro` and `site/src/pages/es/delito/[family].astro` (candidate to hoist into a shared module for the glossary).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Legend.tsx`: existing map legend — extend to show numeric ranges + qualitative labels (D-03).
- `ResultPanel.tsx`: commune detail panel — host for rate tooltip (D-01) + comparison bar/multiplier (D-04). Already locale-aware after Phase 8 (F-007 fix).
- `PanelFamilyBars.tsx`: per-family bars in the panel — natural anchor for family glossary tooltips (D-02).
- `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES`: sober one-sentence CEAD-attributed definitions already written — power both tooltips and the glossary page (D-02). Consider hoisting to a shared `lib/` module so map, tables, and the glossary page share one source.
- `loadNationalAverage` / `loadRegionalAverage` (`data.ts`): feed the comparison multiplier/bar (D-04).
- `MethodologyCaveat.astro`, `DataCallout.astro`, `CommuneRankingTable.astro`: existing data-presentation components touched by the rate-explanation work.
- `i18n.ts`: where every new bilingual string is added (rate definition, legend labels, glossary, comparison copy).

### Established Patterns
- Zero-JS / `client:only="react"` only for the map island; comprehension affordances on static pages (tables, glossary, money pages) must be SSR/CSS, no new `client:*` (CLAUDE.md D-09 lineage; Phase 8 honored this).
- Rollout-gating contract (F-005, Phase 8): any link to a commune page must respect `loadRolloutCuts()`. New glossary/tooltip links must not introduce 404s to non-rollout communes.
- Inline-locale string pattern: locale strings live where the codebase already puts them (`i18n.ts` + per-file inline maps).

### Integration Points
- New `/glossary` + `/glosario` pages join the Astro route set + sitemap + hreflang (mirror existing bilingual page pairs); cross-link from map/tables/money pages.
- The reusable rate-tooltip component is consumed across React (map island) AND Astro (static tables) — plan a form usable in both (e.g. an Astro component + a small React twin, or a CSS-only details/tooltip).

</code_context>

<specifics>
## Specific Ideas

- User's words: the map is "demasiado difícil de leer", "no se entienden tasas", "no se explican los delitos", "debe ser intuitivo".
- Plain-language badges (e.g. percentile phrasing) were considered for comparison; D-04 chose multiplier + bar, but percentile remains an acceptable secondary framing if planning finds room — still neutral, never absolute.

</specifics>

<deferred>
## Deferred Ideas

These are v1.2 features (discovery + SEO), explicitly out of Phase 9 scope. Captured so they are not lost — to be formalized when v1.1 closes and milestone v1.2 opens. Mirrored in `.planning/seeds/SEED-001-v12-discovery-seo.md`.

- **City/commune rankings by crime family** — "which city has the most/least of crime type X" (national, by region, by family). User reiterated this during Phase 9 discussion. → v1.2.
- **Interactive commune comparator** — side-by-side 2–3 communes (rate, rank, trend per family). → v1.2.
- **A-vs-B comparison pages** — programmatic long-tail SEO ("Providencia o Ñuñoa"). → v1.2.
- **"Safest communes" editorial + structured rankings** — top-N pages with prose. → v1.2.
- **Hybrid rollout for rankings** — national rankings show all communes (CEAD data exists) but link only top-N / rollout pages. → v1.2 scoping decision.

### A11y carry-over from Phase 8
- **WR-03 (mobile hamburger keyboard/Escape):** Phase 8 deferred full keyboard operability of the zero-JS hamburger under the D-09 constraint. Candidate to resolve within Phase 9's A11Y-01 track (focus management / keyboard) — planner to decide if it fits.

</deferred>

---

*Phase: 9-UX / Readability / Accessibility Polish*
*Context gathered: 2026-06-15*
