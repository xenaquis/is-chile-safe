---
phase: 21-commune-comparator-a-vs-b-seo
verified: 2026-06-20T00:00:00Z
status: human_needed
score: 6/7 must-haves verified (7th requires human + GSC access)
overrides_applied: 0
human_verification:
  - test: "Interactive comparator island visual/UX verification"
    expected: "Accent-insensitive autocomplete (nunoa → Ñuñoa), 2–3 side-by-side columns with composite index, per-family breakdown with trend arrows, homicide-per-100k row (0 is valid data), Chile avg. column, ES parity, mobile stacking at 375px, no absolute safe/dangerous verdict"
    why_human: "React island renders client-side only — grep cannot verify autocomplete behavior, column layout, mobile stacking, or visual ES parity"
  - test: "GSC URL Inspection on first ~20-pair batch before batch expansion (CMP-07 rollout gate)"
    expected: "At least 3 A-vs-B pages (1 EN, 1 ES) and 2 commune pages show 'URL is on Google' or 'URL can be indexed' — no thin-content exclusion signals before expanding enabled pairs beyond 20"
    why_human: "Requires Google Search Console access for ischilesafe.com — no CLI/API in this repo's workflow"
---

# Phase 21: Commune Comparator A-vs-B SEO — Verification Report

**Phase Goal:** Users can compare 2–3 communes side by side in an interactive island and find bilingual A-vs-B programmatic pages ("Santiago o Providencia?") that deliver substantively differentiated content built on the composite index — without exceeding Cloudflare's file limit or producing thin-content pages Google would deindex.

**Verified:** 2026-06-20
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Users can compare 2–3 communes interactively with composite index, per-family breakdown, trend indicators, homicide row, and avg column | ✓ VERIFIED (auto) | ComparatorIsland.tsx exists (649 lines), Props `{lang, communes, strings}`, accent-insensitive search (NFD/Diacritic line 82-83), homicidios_count at line 524, safeFetch pattern, 8 interaction states; shells at dist/compare/index.html and dist/es/comparar/index.html confirmed |
| 2 | Bilingual A-vs-B programmatic pages exist at /compare/{cutA}-vs-{cutB}/ and /es/comparar/{cutA}-vs-{cutB}/ for the enabled batch | ✓ VERIFIED | 20 EN + 20 ES pages confirmed in dist/; slugs use sorted CUT (cutA < cutB), no inverse duplicates; sample page 10101-vs-10102 has 886 words |
| 3 | Each A-vs-B page carries ≥5 uniqueness blocks and ≥300 non-swappable words (CMP-04) | ✓ VERIFIED | Build-time thin-content throw active (line 38-42 in [pair].astro); 3 sampled pages confirmed: table, trend, national, regional, CEAD — all present; word count 886 (floor: 300) |
| 4 | Total dist file count stays under Cloudflare's 18,000-file limit (CMP-05) | ✓ VERIFIED | avs-b-budget.mjs SAFE_BOUND=18000, [CMP-05] failure message present; dist = 1,258 files; margin = 16,742; registered in all.mjs as validator #14 |
| 5 | Every commune page (346 EN + 346 ES) links to same-region A-vs-B pairs | ✓ VERIFIED | Live dist check: 0 EN commune pages missing href="/compare/"; 0 ES commune pages missing href="/es/comparar/" |
| 6 | hreflang reciprocity and spine validators cover A-vs-B pages (CMP-06) | ✓ VERIFIED | hreflang.mjs: 20 EN == 20 ES compare-page symmetry PASS; spine.mjs: PASS [M] comparator-spoke on all EN and ES commune pages; both exit 0 |
| 7 | Interactive UX verified by human + GSC indexability confirmed before batch expansion (CMP-07) | ? UNCERTAIN — needs human | Programmatic prose checks 10/10 PASS (5 blocks, CEAD attribution, hreflang, no forbidden language). Visual/UX verification and GSC URL Inspection require human operator |

**Score:** 6/7 truths verified (7th needs human action)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/generate-pairs.mjs` | Pair-allowlist generator | ✓ VERIFIED | Exists; generates 5,031 pairs, 20 enabled, all cutA < cutB |
| `data/comparator-pairs.json` | 5,031 sorted-CUT pair objects | ✓ VERIFIED | 5031 pairs confirmed by Node assertion; 20 enabled; no unsorted pairs |
| `site/src/lib/comparisonProse.ts` | buildComparisonProse() engine | ✓ VERIFIED | 404 lines; exports buildComparisonProse + buildMetaDescription; D-05 forbidden-language comment present |
| `site/scripts/validate/avs-b-budget.mjs` | File budget + pair symmetry assertion | ✓ VERIFIED | SAFE_BOUND=18000, [CMP-05] message, exits 0 on current dist (1258 files) |
| `site/src/config/i18n.ts` | 15 comparator i18n keys (EN+ES) | ✓ VERIFIED | nav_compare and cmp_page_h1 confirmed in EN_STRINGS (line 356-357) and ES_STRINGS (line 544-545); interface extended |
| `site/src/islands/ComparatorIsland.tsx` | Client:only React comparator island | ✓ VERIFIED | 649 lines; default export with lang/communes/strings props; no EN_STRINGS import at module level |
| `site/src/pages/compare/index.astro` | EN comparator landing shell | ✓ VERIFIED | Contains #comparator-root (line 54-55), client:only="react" mount, esPath="/es/comparar/" hardcoded |
| `site/src/pages/es/comparar/index.astro` | ES comparator landing shell | ✓ VERIFIED | ES mirror confirmed in build (dist/es/comparar/index.html exists with comparator-root) |
| `site/src/components/PageHeader.astro` | Compare nav link (EN+ES) | ✓ VERIFIED | compareHref logic at line 32; /es/comparar/ present |
| `site/src/pages/compare/[pair].astro` | EN A-vs-B getStaticPaths + thin-content gate | ✓ VERIFIED | Reads comparator-pairs.json, filters enabled, calls buildComparisonProse, throws on <300 words |
| `site/src/pages/es/comparar/[pair].astro` | ES A-vs-B mirror | ✓ VERIFIED | 20 ES pages in dist/es/comparar/ confirmed; symmetric with EN |
| `site/src/components/ComparatorPairsLinks.astro` | 3–5 same-region pair links | ✓ VERIFIED | Exists; injected in commune/[slug].astro and es/comuna/[slug].astro; 0 commune pages missing the link |
| `site/scripts/validate/all.mjs` | avs-b-budget registered in validator suite | ✓ VERIFIED | avs-b-budget.mjs at line 51 of all.mjs; header comment entry #14 at line 18 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| scripts/generate-pairs.mjs | data/cead/meta/index.json | readFileSync at repo-root | ✓ WIRED | Pattern confirmed; generates 5031 pairs |
| site/src/lib/comparisonProse.ts | site/src/lib/data.ts | import CommuneData/loadNationalAverage | ✓ WIRED | 404-line module; data imports at top |
| site/src/pages/compare/index.astro | ComparatorIsland.tsx | client:only="react" mount | ✓ WIRED | Confirmed at lines 11+55 of compare/index.astro |
| ComparatorIsland.tsx | /data/cead/comunas/{cut}.json | safeFetch on selection | ✓ WIRED | safeFetch pattern present; comunas/ path referenced |
| site/src/pages/compare/[pair].astro | data/comparator-pairs.json | readFileSync + filter(p.enabled) | ✓ WIRED | Lines 30+37; comparator-pairs referenced |
| site/src/pages/compare/[pair].astro | comparisonProse.ts | buildComparisonProse + thin-content throw | ✓ WIRED | Import at line 24; thin-content gate at lines 38-42 |
| commune/[slug].astro | ComparatorPairsLinks.astro | render with 3–5 same-region pairs | ✓ WIRED | Import at line 24 and render at line 332 |
| site/scripts/validate/all.mjs | avs-b-budget.mjs | VALIDATORS array entry | ✓ WIRED | 'avs-b-budget.mjs' at line 51 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CMP-01 | 21-02 | 2–3 commune comparator island with composite index, per-family, trend, avg column | ✓ SATISFIED | ComparatorIsland.tsx 649 lines; all columns present in source |
| CMP-02 | 21-02 | Accent-insensitive autocomplete; pre-rendered static indexable shell | ✓ SATISFIED | NFD/Diacritic normalize at line 82-83; shells at dist/compare/index.html + dist/es/comparar/index.html with h1+lead |
| CMP-03 | 21-01, 21-03 | A-vs-B pages from curated allowlist; CUT-code slugs; alphabetical ordering; one canonical page per pair | ✓ SATISFIED | 5031 pairs all cutA<cutB; 20 EN + 20 ES pages built; no inverse duplicates |
| CMP-04 | 21-01, 21-03 | ≥5 uniqueness blocks + ≥300 non-swappable words; build-time assertion | ✓ SATISFIED | Thin-content throw in [pair].astro; 886 words sample; 5 blocks confirmed in 3 sampled pages |
| CMP-05 | 21-01, 21-04 | Total page count < 18,000 asserted at build time | ✓ SATISFIED | avs-b-budget.mjs SAFE_BOUND=18000; dist=1258; registered in all.mjs |
| CMP-06 | 21-03 | hreflang + spine validators extended; commune pages link to 3–5 pairs | ✓ SATISFIED | hreflang.mjs: 20 EN==20 ES PASS; spine.mjs PASS [M] 0 misses on all 346×2 commune pages |
| CMP-07 | 21-04 | Prose quality acceptance ≥10 pairs; staged batches ~20 pairs; GSC verified before expansion | ? NEEDS HUMAN | Automated: 10/10 programmatic PASS; Visual read + GSC URL Inspection require human operator |

**Note:** REQUIREMENTS.md traceability table still marks CMP-06 and CMP-07 as "Pending" (lines 90-91). CMP-06 is fully implemented and verified in the build. CMP-07's automated portion is complete; its human-verification portion is correctly deferred. The REQUIREMENTS.md traceability table should be updated to reflect CMP-06 as Complete.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX markers in phase-modified files | — | — |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| comparator-pairs.json: 5031 pairs, 20 enabled, all sorted | `node -e` assertion | 5031 pairs, 20 enabled, no unsorted pairs | ✓ PASS |
| A-vs-B pages: 20 EN + 20 ES, ≥300 words sample | dist scan + word count | 20+20, 886 words sample | ✓ PASS |
| All 346 commune pages carry /compare/ cross-link | dist scan | 0 EN misses, 0 ES misses | ✓ PASS |
| hreflang.mjs exits 0 with compare symmetry | `node scripts/validate/hreflang.mjs` | PASS — 20 EN == 20 ES; 835 pages checked | ✓ PASS |
| spine.mjs exits 0 with PASS [M] | `node scripts/validate/spine.mjs` | PASS [M] all EN + ES commune pages | ✓ PASS |
| avs-b-budget.mjs: dist < 18000 | registered in all.mjs (#14) | 1258 files, margin 16742 | ✓ PASS |
| Total validator suite 14/14 | 14/14 per build facts | 14/14 passed | ✓ PASS |

---

### Human Verification Required

### 1. Interactive Comparator Island — Visual/UX

**Test:** Run `cd site && npx astro preview --port 4321 --host`. Visit http://localhost:4321/compare/ and:
1. View-source — confirm h1, lead paragraph, MethodologyCaveat, and noscript render before JS
2. Type "nunoa" (no tilde) — confirm "Ñuñoa" appears in autocomplete dropdown (accent-insensitive)
3. Select 2–3 communes — confirm side-by-side columns show composite index score, per-family breakdown with trend arrows (↑↓→), a distinct "Homicide (per 100k, {year})" sub-row, and a "Chile avg." column
4. Select a commune with 0 homicides — confirm 0.00 renders (not "no data")
5. Visit http://localhost:4321/es/comparar/ — confirm ES copy parity: "Comparar Comunas", "Prom. Chile", "Homicidios"
6. Open at 375px width — confirm columns stack vertically, no horizontal scroll
7. Confirm no absolute "safe/dangerous/seguro/peligroso" verdict anywhere

**Expected:** All 8 steps pass without visual/UX defects.
**Why human:** React island renders client-side only — DOM/layout/autocomplete behavior cannot be verified by grep or static HTML inspection.

---

### 2. GSC URL Inspection — Indexability Gate (CMP-07 Staged Rollout)

**Test:** After deploy of the current ~20-pair batch via master push → Cloudflare deploy hook:
1. Open Google Search Console for ischilesafe.com
2. Run URL Inspection on: `https://ischilesafe.com/compare/10101-vs-10102/` (EN), `https://ischilesafe.com/es/comparar/10101-vs-10103/` (ES), and `https://ischilesafe.com/commune/puerto-montt/` (commune with new compare links)
3. Confirm each shows "URL is on Google" or "URL can be indexed" — no "Excluded — Duplicate" or thin-content signals

**Expected:** All inspected URLs indexable; no thin-content exclusion.
**Why human:** Requires Google Search Console access for ischilesafe.com — no CLI/API in this repo's workflow. Must be completed before expanding enabled pairs beyond 20 in data/comparator-pairs.json.

---

### Gaps Summary

No technical gaps. All automated must-haves pass. The only open items are the two human verification checkpoints above, both correctly identified in the plan as `checkpoint:human-verify` tasks requiring a human operator.

**Minor note:** REQUIREMENTS.md traceability rows for CMP-06 (line 90) and CMP-07 (line 91) remain marked "Pending" despite CMP-06 being fully implemented and verified. This is a doc-drift issue, not a code gap — update REQUIREMENTS.md to mark CMP-06 as Complete.

---

_Verified: 2026-06-20_
_Verifier: Claude (gsd-verifier)_
