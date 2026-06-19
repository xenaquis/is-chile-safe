---
phase: 20-methodology-sources-hardening
reviewed: 2026-06-19T12:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - data/SOURCES.md
  - site/scripts/validate/figure-registry.mjs
  - pipeline/tests/test_ine_population_spotcheck.py
  - site/src/pages/methodology.astro
  - site/src/pages/es/metodologia.astro
  - site/src/pages/crime/[family].astro
  - site/src/pages/es/delito/[family].astro
  - site/src/components/FamilyBreakdownBars.astro
  - site/src/components/MethodologyCaveat.astro
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: clean
---

# Phase 20: Code Review Report

**Reviewed:** 2026-06-19
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 20 delivers the methodology and sources hardening contract. The core deliverables
are solid: SOURCES.md now has all required first-class entries (INE, ENUSC, SPD, editorial
parameters), both methodology pages have 7 H2 sections in exact parity, the ENUSC citation
is inline-linked in both locales, the F2/F5 weighting distinction is explained, the LevelChip
F6 sub-section is present, F3/F4 regional/family mean sub-sections are present, the
`#trend-formula` anchor exists in both locales, and the FamilyBreakdownBars drogas scope note
renders in both locales. The INE spot-check values were cross-verified against the committed
JSON — all 7 match exactly.

Three warnings and three info items were found. None are blockers. The most significant is
a missing inline "unweighted mean" label next to the F3 hero figure on crime-ranking pages
(the number appears without its caveat, violating the spec requirement — it depends entirely
on a user following the MethodologyCaveat link to discover the explanation).

---

## Warnings

### WR-01: F3 hero figure displayed without inline "unweighted" caveat on crime-ranking pages

**File:** `site/src/pages/crime/[family].astro:210`
**Also:** `site/src/pages/es/delito/[family].astro:201`

**Issue:** The spec (v1.3-METHODOLOGY-SPEC.md Part 1, F3; Part 3 H2-6) requires the
per-family national mean hero figure to carry an inline caveat noting it is the
"unweighted commune mean". The rendered output is:

```
National mean: 1,234 per 100k (2025)
```

There is no qualifier — no "unweighted", no "typical-commune", no asterisk. The
`RANKING_METHODOLOGY_EN/ES` extended notes in `familyDefs.ts` do explain the scope in
detail, but those strings appear in the hero definition text, not adjacent to the number.
A user reading the hero stat without the `familyDef` text present would see a bare number
labeled only "National mean" with no indication it is unweighted. The MethodologyCaveat
component at the bottom of the page links to `/methodology/` but does not anchor to the
specific F3 explanation.

The MC-02 finding from the spec ("displayed with no caveat, not in methodology") was
partially addressed by adding the methodology sub-section (F3 now explained), but the
inline caveat AT the display point was not added.

**Fix:** Append the qualifier in the hero stat span, for example:

```astro
<span class="hero-stat">
  National mean: {Math.round(familyNationalMean).toLocaleString('en-US')} per 100k ({latestYear})
  <span class="hero-stat-note">(unweighted commune mean)</span>
</span>
```

ES equivalent:

```astro
<span class="hero-stat">
  Media nacional: {Math.round(familyNationalMean).toLocaleString('es-CL')} por 100k ({latestYear})
  <span class="hero-stat-note">(media simple comunal)</span>
</span>
```

---

### WR-02: ENUSC citation uses `[verify URL]` for the ENUSC edition year — the inline link points to an unverified URL

**File:** `data/SOURCES.md:255`
**Also:** `site/src/pages/methodology.astro:214`, `site/src/pages/es/metodologia.astro:216`

**Issue:** SOURCES.md states `[verify edition]` for the ENUSC vintage, and the
`[verify URL]` comment on `https://www.ine.gob.cl/enusc` acknowledges the canonical URL
is unconfirmed. Both methodology pages already expose the ENUSC link as a live
`<a href="https://www.ine.gob.cl/enusc">` pointing to that unverified URL. If the URL
is wrong (the CONTEXT notes it may actually be `https://www.seguridadpublica.gov.cl`),
users clicking the citation hit a dead or incorrect page, which is an editorial
credibility failure for the core underreporting claims.

The spec itself marks this `[verify URL]` and classifies it as acceptable, but the link
is already live in both published pages — not just in SOURCES.md. An unverified live link
in a methodology page is a higher-severity issue than the same stub in SOURCES.md.

**Fix:** Either verify and confirm `https://www.ine.gob.cl/enusc` before deployment (preferred),
or temporarily render the ENUSC name without a live hyperlink (text only + SOURCES.md
reference) until the canonical URL is confirmed. Do not ship a live link to an unverified
official government URL.

---

### WR-03: figure-registry validator's token matching is purely substring-based — cannot detect section removal or stub replacement

**File:** `site/scripts/validate/figure-registry.mjs:192-211`

**Issue:** The zero-orphan check validates that certain substrings (e.g. `"## ENUSC"`,
`"## Methodology parameters"`, `"Trend window"`) appear in `data/SOURCES.md`. This is
meaningful for detecting a file that has never had these sections added. However, the check
is trivially bypassable and provides no guarantee of section depth:

1. A future commit could add `## ENUSC` as a one-line stub with empty content and the
   check would pass.
2. Tokens like `['## CEAD', '## INE']` for F1 prove both heading strings exist, but do
   not verify the INE section contains any actual population-denominator provenance (it
   could be an empty heading).
3. For F15, the tokens are `['RSS', 'news']` — these are so generic they would match any
   incidental mention anywhere in the file, including the CEAD section's `## Cross-source notes`.

The result is a CI check that will turn green on a heavily degraded SOURCES.md as long as
the heading strings survive.

**Fix:** Extend at least the most critical figures (F11 ENUSC, F7 trend params) to assert
that the section body also contains a key distinguishing substring. For example:

```js
// F11: require ENUSC URL or "cifra negra" to appear in the section
['## ENUSC', 'Encuesta Nacional Urbana'],

// F7: require both parameter values to appear (not just the heading)
['## Methodology parameters', 'Trend window', 'Trend threshold', '5 %'],

// F15: require the specific feed list marker, not just 'news'
['News feeds', 'RSS'],
```

This does not fully solve the empty-stub problem but makes the check substantially harder
to pass accidentally.

---

## Info

### IN-01: SOURCES.md `[verify URL]` stub for INE official landing — the live methodology page already links it

**File:** `data/SOURCES.md:209`
**Also:** `site/src/pages/methodology.astro:163`, `site/src/pages/es/metodologia.astro:160`

**Issue:** `data/SOURCES.md` marks the INE official landing as `[verify URL]`, yet
both methodology pages already render it as a live hyperlink:
`https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion`.
If the SOURCES.md mark-up was accurate (URL unverified), then the live link in the
methodology pages should also carry that uncertainty. In practice the INE URL pattern is
well-documented and this URL is structurally plausible, but the inconsistency between the
SOURCES stub status and the deployed live link should be resolved.

**Fix:** Either confirm the URL (recommended — this INE landing page is stable) and remove
the `[verify URL]` tag from SOURCES.md, or add a comment in the methodology page source
noting the URL needs verification.

---

### IN-02: Spot-check hardcoded values are self-certified from the mirror, not from the official INE PDF

**File:** `pipeline/tests/test_ine_population_spotcheck.py:21-25`

**Issue:** The docstring acknowledges the values were "sourced from
bastianolea/censo_proyecciones_poblacion mirror, cross-checked against the committed JSON
at Phase 20 commit." This means the test verifies that the JSON has not changed since the
Phase 20 snapshot — it does NOT independently confirm the values match the official INE
publication. If the mirror had already drifted before the Phase 20 snapshot, the hardcoded
expected values would encode the drift, and the test would perpetually pass while producing
wrong denominators.

This is a fundamental limitation of a self-certification approach. It is noted in the
docstring but should be more prominently flagged.

**Fix:** Add a comment block at the top of `OFFICIAL_INE_2024` explicitly stating that
these values have NOT been independently verified against the official INE PDF or portal
download, and noting the specific commit at which they were pinned. Separately, a future
work item should document verifying at least 2-3 values against the actual INE portal download.

---

### IN-03: `LevelChip 1–5` methodology sub-section says "346 eligible communes" — number is hardcoded in prose

**File:** `site/src/pages/methodology.astro:348`
**Also:** `site/src/pages/es/metodologia.astro:360`

**Issue:** The LevelChip explanation reads: "the 346 eligible communes are divided into
five approximately equal tiers." The number 346 is the total number of communes, not the
number of non-low-population eligible communes used for level calculation. Some communes
are excluded by the <10k threshold, so the actual eligible pool is smaller than 346. This
is a factual inaccuracy in the published methodology text.

The ES page repeats: "las 346 comunas elegibles se dividen en cinco grupos".

**Fix:** Replace the hardcoded count with accurate wording that does not claim 346 are all
eligible:

EN: "...eligible communes (those with 10,000 or more inhabitants) are divided into five
approximately equal tiers..."

ES: "...las comunas elegibles (aquellas con 10.000 o más habitantes) se dividen en cinco
grupos aproximadamente iguales..."

This avoids the off-by-N error and is future-proof across build years as the eligible pool
may shift slightly.

---

---

## Fix Notes (2026-06-19)

- **WR-01** fixed: inline "(unweighted commune mean — see methodology)" caveat added to hero stat in `crime/[family].astro` and `es/delito/[family].astro`. Commit ae77535.
- **WR-02 + IN-01** fixed: `[verify URL]` removed from SOURCES.md for both INE projections and ENUSC entries; live links in `methodology.astro` and `es/metodologia.astro` updated to verified URLs. `[verify edition]` for ENUSC vintage year retained. Commit 9a6b218.
- **IN-03** fixed: "346 eligible communes" reworded to "eligible communes (those with 10,000 or more inhabitants)" in both locale methodology pages. Commit 13f0b44.
- **WR-03** deferred: figure-registry substring matching hardening is acceptable for v1.3. Logged as tech-debt for v1.4 hardening pass.

_Reviewed: 2026-06-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
