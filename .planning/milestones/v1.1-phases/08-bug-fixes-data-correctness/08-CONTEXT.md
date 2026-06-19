# Phase 8: Bug Fixes & Data Correctness - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve the defects surfaced by the Phase 7 E2E review (`.planning/REVIEW-E2E-FINDINGS.md`) so the site is correct and clean before go-live. The review found **0 Critical, 4 Warning, 5 Polish**. This phase owns:
broken internal links (F-005), the two i18n leaks (F-001, F-007), the missing mobile nav path (F-009), AdSlot CLS/placeholder cleanup (BUGFIX-04), and re-verification that console is clean + rate methodology is correct (BUGFIX-01/03).

**In scope:** fix the 3 Warnings selected below (F-001, F-007, F-009) + F-005 link strategy + AdSlot placeholder + verify console/data/hreflang.
**Out of scope (→ Phase 9):** all 5 Polish findings (content parity, grammar, toast, thin pages, new legal pages) and any new capability. No new pages, no rollout expansion.
</domain>

<decisions>
## Implementation Decisions

### F-005 — Broken commune links in region/crime rankings (BUGFIX-02, highest impact)
- **D-01:** **Gate the linked set to rollout slugs.** In ALL region (`/region/*`, `/es/region/*`) and crime (`/crime/*`, `/es/delito/*`) ranking tables, only list communes that have a built rollout page. Non-rollout communes are removed from the displayed ranking rows entirely (not rendered as dead `<a>`, not as plain text). Result: shorter but 404-free, consistent lists.
- **D-02:** Use the existing `loadRolloutCuts()` (`site/src/lib/data.ts`) as the single source of truth for "which communes have a page." Do NOT hardcode the 12 slugs — derive from `rollout.json` so the lists auto-expand when rollout grows (and `ROLLOUT_ALL=true` naturally shows all).
- **D-03 (Claude discretion / planner note):** A national/regional rank like "#11 of 346" is computed across all 346 and MUST stay accurate — only the *displayed table rows* are gated, not the rank denominator. Planner should consider a short "showing N rollout communes — more coming" affordance so a gated RM table (≈4 of 52) doesn't read as data loss; keep it minimal (this is a bug-fix phase, not UX).

### Finding split — which Warnings Phase 8 fixes (BUGFIX-05)
- **D-04:** **Fix in Phase 8:** F-001 (ES H1 "Commune" → "Comuna"), F-007 (map panel close-button `aria-label` "Cerrar" → locale-aware Close/Cerrar, 3 occurrences in `ResultPanel.tsx`), F-009 (add mobile nav path to Home/Map/Methodology — hamburger or persistent mobile "Map" entry).
- **D-05:** **Defer to Phase 9 (with written justification in BUGFIX-05 closeout):** all 5 Polish findings — F-002 (cookie/accessibility legal pages → new pages + go-live gate, not a bug), F-003 (ES methodology parity → READ-02), F-004 (thin contact → content), F-006 ("Región de Metropolitana" grammar → READ), F-008 (incident "coming soon" toast → UX-01/UX). Each gets a one-line deferral reason when closing BUGFIX-05.

### AdSlot CLS / disabled placeholder (BUGFIX-04)
- **D-06:** AdSlot already reserves height (90px desktop / 50px mobile) and renders no `adsbygoogle` when `ADSENSE_ENABLED !== 'true'` — **no real CLS exists**. The only change: with AdSense OFF, render the reserved space as **blank** (remove the dashed-border `.ad-placeholder` box) while keeping the reserved height. Clean/finished look pre-AdSense, still zero CLS.
- **D-07:** Keep the env-gating contract intact (exact string compare `=== 'true'`, no `adsbygoogle` in DOM when off) — this is verified, not redesigned.

### Re-verification method (BUGFIX-05)
- **D-08:** **Build + grep + spot-check**, no BrowserOS dependency. Verify via: `npm run build`, existing validators, grep for the corrected strings (e.g. no "Commune" in ES H1, no `aria-label="Cerrar"` on EN path), and fetch/exist-check of previously-404 commune URLs to confirm rankings no longer link to them. **Chain build + validate in one command** (OneDrive build-artifact desync — dist/ vanishes between separate processes).
- **D-09:** F-009 (mobile nav) and F-007 (panel) involve render/interaction; verify the markup/CSS path is correct (hamburger toggle present, links reachable, `display:none` removed at mobile breakpoint) via build + DOM/CSS inspection rather than a BrowserOS re-run. A BrowserOS spot-check is optional, not required, and if done must run inline (not in gsd-executor) with a no-spaces screenshot path.

### Claude's Discretion
- Where localized UI strings live (locale dictionary vs inline) for F-001/F-007 fixes — follow existing i18n pattern in the codebase.
- Exact mobile-nav UX (hamburger drawer vs inline collapse) for F-009 — pick the lightest pattern consistent with the existing header; the requirement is only that Home/Map/Methodology are reachable on mobile.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Findings & requirements (read first)
- `.planning/REVIEW-E2E-FINDINGS.md` — the source of truth for every finding (F-001..F-009), severity, page, observation, and recommendation. Defines what "resolved" means per finding.
- `.planning/REQUIREMENTS.md` §BUGFIX-01..05 — the phase requirements.
- `.planning/ROADMAP.md` §"Phase 8" — the 5 success criteria (console clean, links resolve + hreflang, rates via `loadNationalAverage`, AdSlot no-CLS, all Critical/Warning resolved-or-deferred).

### Code touched by this phase
- `site/src/lib/data.ts` — `loadRolloutCuts()` (rollout gating source of truth for D-01/D-02), `loadNationalAverage` / `loadRegionalAverage` (rate methodology to verify for BUGFIX-03).
- `site/src/pages/region/[slug].astro` + `site/src/pages/es/region/[slug].astro` — region ranking tables (F-005 gating).
- `site/src/pages/crime/[family].astro` + `site/src/pages/es/delito/[family].astro` — crime ranking tables (F-005 gating).
- `site/src/components/map/ResultPanel.tsx` — close-button `aria-label="Cerrar"` ×3 (F-007).
- `site/src/components/AdSlot.astro` — reserved-height placeholder; remove dashed `.ad-placeholder` visible box (D-06).
- ES commune-index page rendering the F-001 H1 ("Commune") — locate the template producing `/es/delitos-por-comuna/` H1.
- Global header component — mobile nav (F-009).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `loadRolloutCuts()` in `site/src/lib/data.ts` — returns enabled CUT codes from `src/config/rollout.json`; honors `ROLLOUT_ALL=true`. Reuse directly to gate F-005 ranking rows; do not duplicate the slug list.
- AdSlot already env-gates and reserves height correctly — BUGFIX-04 is a small cosmetic delta + verification, not a rebuild.

### Established Patterns
- Region pages are intentionally NOT rollout-gated for *building* (all 16 regions built — D-26). The gate in D-01 applies to the *linked commune set inside the ranking*, not to which region pages exist.
- AdSlot uses exact string compare on `ADSENSE_ENABLED` (Pitfall 4) — preserve.
- Repo lives inside OneDrive: chain build + validate in one command or `dist/` desyncs between processes (see project memory).

### Integration Points
- F-005 fix lives in the 4 ranking templates (region ×2 locales, crime ×2 locales) — same gating logic applied consistently.
- F-001/F-007 are i18n string fixes; route through the existing locale-string mechanism so EN/ES both stay correct.

</code_context>

<specifics>
## Specific Ideas

- F-001: ES H1 must read "Comuna" (title/slug already correct — only the visible `<h1>` is wrong).
- F-007: EN → "Close", ES → "Cerrar" on the panel close button (`aria-label` + visible "×" stays).
- F-009: the **Map** is the core product — the non-negotiable is a reachable mobile path to `/map/`.
- BUGFIX-03 is largely a verification: the review already confirmed rate-vs-raw sanity PASS (national mean 5,808/100k; Santiago 9,309 #11/346). Spot-check ≥3 communes against `data/cead/` and confirm `loadNationalAverage` (mean, not sum) is the path used.

</specifics>

<deferred>
## Deferred Ideas

- **F-002** — cookie/consent policy + accessibility statement legal pages → Phase 9 / AdSense go-live gate (new pages, not a bug fix).
- **F-003** — ES methodology content parity with EN → Phase 9 (READ-02).
- **F-004** — thin contact pages (add contact method + response expectation) → Phase 9.
- **F-006** — ES region display name ("Región Metropolitana", "Región del Biobío" vs blanket "Región de {name}") → Phase 9 (READ).
- **F-008** — incident empty-state "coming soon" toast confirm/fix → Phase 9 (UX-01).
- Rollout expansion (building more commune pages) — explicitly out of scope; F-005 is solved by gating, not by expanding rollout.

</deferred>

---

*Phase: 8-Bug Fixes & Data Correctness*
*Context gathered: 2026-06-15*
