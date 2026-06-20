# Phase 21: Commune Comparator + A-vs-B SEO - Context

**Gathered:** 2026-06-20
**Status:** Ready for planning
**Mode:** Pre-seeded for autonomous run (decisions locked from ROADMAP success criteria + STATE risks; verify against live commune data during planning)

<domain>
## Phase Boundary

Users can compare 2–3 communes side by side in an interactive island, and find bilingual A-vs-B programmatic pages ("Santiago o Providencia?") that deliver substantively differentiated content built on the Phase 18 composite index — WITHOUT exceeding Cloudflare's free-tier file limit or producing thin-content pages Google would deindex.

**Requirements:** CMP-01, CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07
**Depends on:** Phase 18 (DONE) — consumes `data/cead/comparator_table.json` + the `composite_index` field on commune JSON. Both present in repo.
</domain>

<decisions>
## Implementation Decisions (LOCKED from ROADMAP success criteria + STATE risk register)

### Comparator island (CMP-01)
- Routes: `/compare/` (EN) + `/es/comparar/` (ES). Hardcode the ES slug for nav/cross-links (do NOT rely on getRelativeLocaleUrl for localized slugs — see memory [[i18n-localized-slug-pitfall]]).
- Compare 2–3 communes; **accent-insensitive autocomplete** across all 346 communes.
- Side-by-side panel shows: composite-index headline, per-family breakdown, trend indicator, and a "compare to national/regional average" column.
- **Pre-rendered static HTML shell** that is Google-indexable — the island hydrates on top of server-rendered content (`client:only`/`client:visible`; NEVER render-only critical content). Reuse the existing map-island hydration pattern; zero new heavy deps.

### A-vs-B programmatic pages (CMP-02, CMP-03, CMP-04)
- **DO NOT generate the full cartesian product.** 346×346 ≈ 59,685 pairs × 2 locales = 119,370 pages — blows the Cloudflare 20k file limit. Use a **curated priority-pair allowlist** (~3,400 pairs → ~6,800 bilingual pages).
- **Compute the exact priority-pair count from real commune data BEFORE writing getStaticPaths** (STATE-flagged sub-problem #1). Selection heuristic: same-region neighbors, capital-vs-neighbor, high-search-intent pairs.
- Slugs: **CUT-code, alphabetical order**, one canonical page per pair (e.g. `/compare/13110-vs-13119/`) — NO A-vs-B / B-vs-A duplication. Reciprocal EN/ES hreflang on every pair.
- **Thin-content guard (STATE-flagged sub-problem #2):** each pair page needs ≥5 uniqueness blocks (index-difference statement, per-family rate table, trend narrative, national rank, regional context) totaling **≥300 words of non-swappable prose**. `buildComparisonProse()` must generate substantively different text per pair from real trend/index data — NOT a swappable template. Enforce with a **build-time thin-content assertion**.

### Build-size + linking + validators (CMP-03, CMP-05)
- **Build-time assertion: total files < 18,000** (safely under Cloudflare free-tier 20,000).
- Every commune page links to **3–5 relevant A-vs-B pairs** involving that commune.
- Extend the hreflang-reciprocity validator to cover A-vs-B pages. All validators must exit 0 (`npm run validate` → 13/13+).

### Rollout discipline (CMP-06, CMP-07)
- Acceptance-check a random sample of **≥10 A-vs-B pairs** for prose quality before any deploy.
- Publish the **first batch ~20 pairs**, verify GSC URL Inspection, THEN expand to subsequent batches.

### Editorial / data invariants (project-wide — non-negotiable)
- Never an absolute "safe/dangerous / seguro/peligroso" verdict; always attribute CEAD. Forbidden-language validator must stay green.
- CEAD rates are already per-100k — never rescale (see memory [[crime-rates-already-per-100k]]).
- EN/ES parity on every surface; static pre-render for SEO; ~$0 infra (no new paid services).

### Claude's Discretion
Component structure, prose-engine internals, autocomplete implementation, and priority-pair heuristic specifics are at Claude's discretion — but must satisfy the locked guardrails above and be grounded in real commune data (verify counts during research/planning, do not assume).
</decisions>

<code_context>
## Existing Code Insights
- Phase 18 outputs to consume: `data/cead/comparator_table.json` (+ mirrored to `site/public/data/cead/`) and `composite_index` on each commune JSON.
- Reuse the existing React island hydration pattern from the Leaflet map island for the comparator island.
- Reuse `CommuneRankingTable` / `RankingTableEnhancer` patterns and brand tokens (teal `#0f766e`, 5-level incidence scale) for the per-family breakdown table inside the comparator.
- Validators live in `site/scripts/validate/`; extend the hreflang validator there.
- i18n strings in `site/src/config/i18n.ts`.
</code_context>

<specifics>
## Specific Ideas
- This phase is research-flagged: the FIRST planning task must compute the priority-pair allowlist size from real data and confirm `existing ~792 pages + A-vs-B < 18,000` before committing to getStaticPaths.
- Reference: STATE.md risk register entries tagged [Phase 21]; ROADMAP Phase 21 success criteria (5 items).
</specifics>

<deferred>
## Deferred Ideas
- AdSense / Consent Mode v2 — out of v2.0 scope.
- Expanding beyond the first ~20-pair batch happens only after GSC URL-Inspection verification (CMP-07).
</deferred>
