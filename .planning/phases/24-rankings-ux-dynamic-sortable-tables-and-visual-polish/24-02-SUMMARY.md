---
phase: 24-rankings-ux-dynamic-sortable-tables-and-visual-polish
plan: 02
status: complete-with-gap
date: 2026-06-20
---

# 24-02 SUMMARY — BrowserOS E2E Visual Review

BrowserOS in-detail E2E review of all ranking surfaces, run INLINE by the orchestrator
(gsd-executor lacks BrowserOS). Verified against the 24-UI-SPEC.md Sortability Visual
Contract + BrowserOS E2E Review Contract. Build served via `astro preview` at
http://localhost:4321 (note: repo has no `npm run preview` script — used `npx astro preview`).

Method: DOM assertions via `evaluate_script` (sort buttons, `aria-sort`, arrow glyph +
computed color, year `<select>`, row order, `overflow-x`) + screenshots. This is more
robust than eyeballing — every contract row was checked programmatically on the real
rendered page.

## Surface × Contract Matrix

| Surface | Wired? | Default dir | Arrow on load | Teal #0f766e | Year select | Click re-sorts | Verdict |
|---|---|---|---|---|---|---|---|
| `/crime-ranking/homicide/` (EN) | ✅ 346 rows | ▼ desc | ✅ | ✅ rgb(15,118,110) | ✅ | ✅ | **PASS** |
| `/es/ranking-delito/homicidios/` (ES) | ✅ 346 rows | ▼ desc | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `/safest-cities-in-chile/` (EN) | ✅ 12 rows | ▲ asc | ✅ | ✅ rgb(15,118,110) | ✅ | ✅ asc→desc flips 3,223→9,748 | **PASS** |
| `/es/comunas-mas-seguras-chile/` (ES) | ✅ 12 rows | ▲ asc | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `/` home (EN) | ⚠️ flag only, **0 `data-rates`** | — | ❌ none | — | ❌ | ❌ | **GAP** |
| `/es/` home (ES) | ⚠️ flag only, **0 `data-rates`** | — | ❌ none | — | ❌ | ❌ | **GAP** |

`/communes/` correctly excluded (A–Z directory, no rate column).

## Functional / accessibility checks (desktop)
- **Click-to-sort:** PASS — safest-cities EN rate header toggled ascending (3,223 / 3,512 / 3,984) → descending (9,748 / 9,359 / 9,309). Correct re-order.
- **Focus ring:** PASS — focusing a `.rte-sort-btn` yields a solid teal outline (`rgb(15,118,110)`, ~2px, offset 2px) per `:focus-visible` rule.
- **Number locale:** PASS — EN `3,223` (comma) vs ES `3.223` (period) rendered correctly.

## Mobile (375px)
- **Method:** BrowserOS has no viewport-resize primitive; used a 375px iframe + structural assertions. Cross-origin (file://→localhost) blocked iframe introspection, so verified structurally.
- **Arrow on load:** PASS by construction — the enhancer runs on DOMContentLoaded independent of viewport width; the same DOM that shows ▲/▼ at 1280px shows it at 375px.
- **Horizontal overflow:** PASS — `.ranking-table-wrapper` / `.table-wrapper` computed `overflow-x: auto` on both safest-cities EN+ES; a 4-column table exceeds 375px → horizontal scroll. No layout break observed in the 375px frame.

## Screenshots
- `C:/tmp/p24-review/safest-cities-en-desktop.png` — ▲ teal, year select, ascending
- `C:/tmp/p24-review/crime-ranking-en-desktop.png` — (capture timed out on 346-row page; DOM-verified ▼ desc instead)
- `C:/tmp/p24-review/home-en-desktop-GAP.png` — home previews, no sort affordance
- `C:/tmp/p24-review/safest-cities-en-mobile-375.png` — 375px frame, clean layout

## GAP-24A — Home ranking previews not interactively sortable (EN + ES)

**Observed:** `/` and `/es/` each render two `CommuneRankingTable` previews ("Lowest Reported
Rate" / "Highest Reported Rate", ~top-N). They carry `data-ranking-table` but their rows have
**no `data-rates`**, so `RankingTableEnhancer` hits its `hasRatesData` guard
(`RankingTableEnhancer.astro:87-88`) and silently skips them. Result: no arrow, no year
selector, no click-to-sort on home.

**Expected per phase goal:** the goal text explicitly lists "landing/home `index.astro` EN+ES"
as a surface to wire. The researcher + planner both assumed home was "already wired" — it is
only *half*-wired (component flag present, per-row data absent).

**Design tension (why this isn't a clean bug):** home previews are **pre-sorted top-N teasers**
(Lowest / Highest), each with an explicit "See full ranking →" / "Browse all communes →" link
to the now-fully-sortable full pages. Making a fixed 10-row "lowest" subset interactively
sortable/year-switchable is semantically awkward (sorting a "lowest" teaser to descending shows
"highest-of-the-lowest"; switching year rewrites cells for a commune set chosen by a different
year's ranking). This is a plausible reason the teasers were left static by design.

**Resolution options (scope decision — see orchestrator):**
- A) Wire home: enrich `lowestRows`/`highestRows` with `ratesByYear` in `index.astro` (EN) + ES home (mirror the safest-cities pattern). Fully meets the literal goal. ~1 small gap-closure plan.
- B) Accept as-is: treat home previews as intentional static teasers; the full sortable UX is one click away. Optionally drop the vestigial `data-ranking-table` flag on the preview tables to remove the implied-but-absent affordance.

## Verdict
4/6 surfaces PASS the full sortable contract (the two genuinely-new wirings + both crime-ranking).
2/6 (home EN+ES) carry GAP-24A — a scope decision, not a regression. No regressions on previously-working surfaces. The headline new value (safest-cities EN+ES now sortable, descending default + asc override, teal affordance on load) is delivered and verified.
