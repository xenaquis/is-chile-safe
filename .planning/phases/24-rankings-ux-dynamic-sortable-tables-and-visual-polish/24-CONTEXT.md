# Phase 24: Rankings UX — dynamic sortable tables and visual polish - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Make the ranking pages — the project's most important SEO products — feel like first-class, sortable data tables. Wire dynamic high→low sorting (the existing `RankingTableEnhancer` island) into every ranking surface that currently lacks it (landing/home `index.astro` EN+ES, `/crime/[family]/` family pages EN+ES, `/communes/` directory, `/safest-cities-in-chile/` + ES), default sort to descending, make sortability visually obvious, and apply visual/UX polish using existing brand tokens (teal #0f766e, 5-level incidence scale). Includes a BrowserOS in-detail E2E visual review (EN+ES, desktop + mobile).

**Depends on:** Phase 18 (composite-index data, already shipped). Independent of Phase 22 launch ops.

</domain>

<decisions>
## Implementation Decisions

### Locked by UI-SPEC (24-UI-SPEC.md — approved 2026-06-19, 6/6 dimensions PASS)
The design contract is the authoritative source for all visual/interaction decisions. Key locked points:
- Reuse existing `global.css` tokens (8-pt spacing, 4 type sizes, 2 weights, teal `#0f766e` accent reserved for sort arrows / focus rings / commune links only).
- Default sort: descending; sort arrow (▼) in teal as on-load focal point; `aria-sort` + `aria-label` on every header button.
- **Real gap is narrower than the goal states** — home + crime-family pages already have `RankingTableEnhancer` wired. True gaps:
  1. `/safest-cities-in-chile/` — raw `<table>`, missing `data-ranking-table` + per-row `data-rates` JSON.
  2. `/es/comunas-mas-seguras-chile/` — same gap.
  3. Both need a per-page `data-default-sort-dir="asc"` override (editorial intent = lowest-first, conflicts with the descending default).
  - `/communes/` directory is an A-Z alphabetical list with no rate column → no sort wiring applies.
- Copy: 2 new caption strings (EN+ES, "click headers to sort"); the rest pre-exist in `i18n.ts`.
- Registry: vanilla JS only, zero new dependencies.

### Claude's Discretion
All remaining implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use the UI-SPEC, ROADMAP phase goal, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

- `site/src/components/RankingTableEnhancer.astro` — existing sort behavior + data-attribute API (`data-ranking-table`, per-row `data-rates`, `data-default-sort-dir`).
- `site/src/components/CommuneRankingTable.astro` — table markup pattern with existing data-attributes (reference for wiring the missing surfaces).
- `site/src/pages/safest-cities-in-chile.astro` (+ ES counterpart) — confirmed missing `data-ranking-table` + `data-rates`; primary targets for this phase.
- `site/src/styles/global.css` — all design tokens (spacing, typography, color, border-radius).
- `site/src/i18n.ts` — caption strings (2 new EN+ES needed).
- Additional codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

- Phase closes with a BrowserOS in-detail E2E visual review across EN+ES, desktop + mobile (375px), per the phase goal — run inline (gsd-executor lacks BrowserOS).
- Do not over-scope: surfaces already wired (home, crime-family) need only visual-polish verification, not re-wiring.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
