---
phase: 20-methodology-sources-hardening
verified: 2026-06-19T02:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
gaps_resolved:
  - truth: "Every inline link to a methodology anchor resolves to an existing id"
    status: fixed
    fix_commit: "anchor ids national-mean / media-nacional added to the F3 <h3> in methodology.astro + es/metodologia.astro; confirmed present in dist/methodology/index.html + dist/es/metodologia/index.html; rebuild 13/13 validators green."
gaps:
  - truth: "Every inline link to a methodology anchor resolves to an existing id"
    status: resolved
    reason: >
      crime/[family].astro:210 and es/delito/[family].astro:201 both render
      live links to /methodology/#national-mean and /es/metodologia/#media-nacional
      respectively. Neither anchor id exists in the methodology pages (confirmed via
      grep of src + built dist). The #trend-formula anchor exists in both locales and
      is fine. Only #national-mean / #media-nacional are dead. This was introduced when
      WR-01 was fixed (review commit ae77535 added the caveat text + deep-link) but the
      corresponding id attribute was never added to the <h3> elements in methodology.astro
      and metodologia.astro.
    artifacts:
      - path: "site/src/pages/crime/[family].astro"
        issue: "href='/methodology/#national-mean' — target id does not exist"
      - path: "site/src/pages/es/delito/[family].astro"
        issue: "href='/es/metodologia/#media-nacional' — target id does not exist"
      - path: "site/src/pages/methodology.astro"
        issue: "h3 'Per-family national mean (F3)' at line 325 has no id attribute"
      - path: "site/src/pages/es/metodologia.astro"
        issue: "h3 'Media nacional por familia (F3)' has no id attribute"
    missing:
      - "Add id=\"national-mean\" to the <h3>Per-family national mean (F3)</h3> in methodology.astro"
      - "Add id=\"media-nacional\" to the equivalent <h3> in metodologia.astro"
---

# Phase 20: Methodology & Sources Hardening — Verification Report

**Phase Goal:** Every quantitative figure displayed on the site maps to a named entry in `data/SOURCES.md` and to an explanation in the methodology (EN + ES at structural parity) — zero orphaned numbers, zero unattributed claims, and a CI check to keep it that way.
**Verified:** 2026-06-19T02:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Build + Validate Evidence

```
npm run build && npm run validate
  13/13 validators passed (structure, commune, rollout, region, crime, hreflang,
  schema, map, forbidden-language, coverage, spine, seo, figure-registry)
  791 pages built — 0 errors.

python -m pytest pipeline -q
  179 passed, 12 warnings in 6.82s
```

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SOURCES.md has first-class INE + ENUSC + SPD-parent entries + editorial-parameters note | VERIFIED | `## INE` (line 203), `## ENUSC` (line 238), `## SPD — institutional authority` (line 264), `## Methodology parameters` (line 284) all present with full content. `[verify edition]` stub retained for ENUSC vintage year per review fix-note WR-02. |
| 2 | Methodology EN+ES explains per-family mean (F3), per-region mean (F4), LevelChip tiers (F6), F2/F5 weighting distinction; 7-H2 parity maintained | VERIFIED | EN h3 at line 325 (F3), 335 (F4), 344 (F6). F2/F5 distinction at methodology.astro:277-280. Both locales have exactly 7 `<h2>` sections — parity confirmed. |
| 3 | Inline ENUSC + INE citation links present pointing at verified ine.gob.cl URLs; all methodology anchors referenced by deep-links exist as ids | FAILED | ENUSC link at methodology.astro:214 → `https://www.ine.gob.cl/estadisticas/sociales/seguridad-publica-y-justicia` (verified URL, WR-02 fix applied). INE link at line 162 → `https://www.ine.gob.cl/...proyecciones-de-poblacion` (verified). BUT: crime-family pages link to `#national-mean` and `#media-nacional` anchors that do not exist in methodology pages — dead anchors. |
| 4 | CI forbidden-language validator gated + green; figure-registry validator passes with zero orphans (F1-F12, F15); F13/F14 excluded | VERIFIED | `forbidden-language: PASS — 793 pages scanned, 0 forbidden terms found`. `figure-registry: PASS — all 13 in-scope figures (F1-F12, F15) have registered sources`. Both are validators #9 and #13 in the 13/13 suite. |
| 5 | drogas scope note inline on FamilyBreakdownBars; #trend-formula anchor exists and is deep-linked; figure registry shows zero orphans | VERIFIED | `FamilyBreakdownBars.astro:93` renders `FAMILY_SCOPE_NOTE['drogas']` — EN: "Note: this is CEAD's Drug Crimes family — criminal offences under Ley 20.000…". `#trend-formula` exists in both methodology pages (methodology.astro:240, metodologia.astro:248). MethodologyCaveat.astro links to `#trend-formula` in both locales. Figure registry 13/13 pass. |

**Score:** 4/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/SOURCES.md` | INE + ENUSC + SPD-parent + editorial params | VERIFIED | All 4 sections present with substantive content |
| `site/scripts/validate/figure-registry.mjs` | 13th validator, zero-orphan gate | VERIFIED | Passes 13/13 validation suite |
| `site/src/pages/methodology.astro` | F3/F4/F6 sub-sections, 7 H2, ENUSC link | VERIFIED | All present; dead anchor gap is in linking FROM crime pages TO this file |
| `site/src/pages/es/metodologia.astro` | ES parity of above | VERIFIED | 7 H2 confirmed, inline links present |
| `site/src/pages/crime/[family].astro` | Inline F3 caveat + deep-link | PARTIAL | Caveat text present; link target (#national-mean) does not exist |
| `site/src/pages/es/delito/[family].astro` | ES inline F3 caveat + deep-link | PARTIAL | Caveat text present; link target (#media-nacional) does not exist |
| `site/src/components/FamilyBreakdownBars.astro` | drogas scope note inline | VERIFIED | Renders FAMILY_SCOPE_NOTE['drogas'] in both EN+ES |
| `pipeline/tests/test_ine_population_spotcheck.py` | INE population spot-check | VERIFIED | 179 pytest tests pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `crime/[family].astro` | `methodology.astro` | `href="/methodology/#national-mean"` | NOT_WIRED | Anchor id missing from target |
| `es/delito/[family].astro` | `metodologia.astro` | `href="/es/metodologia/#media-nacional"` | NOT_WIRED | Anchor id missing from target |
| `methodology.astro` underreporting section | ENUSC landing | `href="https://www.ine.gob.cl/estadisticas/sociales/seguridad-publica-y-justicia"` | WIRED | Verified URL present |
| `methodology.astro` rate section | INE projection page | `href="https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion"` | WIRED | Verified URL present |
| `MethodologyCaveat.astro` | `#trend-formula` | `href="/methodology/#trend-formula"` | WIRED | id="trend-formula" exists in both locale pages |
| `FamilyBreakdownBars.astro` | `FAMILY_SCOPE_NOTE_EN/ES` | import from familyDefs.ts | WIRED | Drogas note renders inline |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 13/13 validators pass | `npm run build && npm run validate` | All 13 PASS, 791 pages | PASS |
| Pipeline pytest | `python -m pytest pipeline -q` | 179 passed | PASS |
| figure-registry zero orphans | validator #13 in suite | F1-F12 + F15 all registered | PASS |
| forbidden-language gate | validator #9 in suite | 793 pages scanned, 0 found | PASS |
| #trend-formula anchor exists | grep methodology.astro | line 240 + es line 248 | PASS |
| #national-mean anchor exists | grep methodology.astro | not found | FAIL |
| #media-nacional anchor exists | grep metodologia.astro | not found | FAIL |

### Requirements Coverage

| Requirement | Plans | Status | Evidence |
|-------------|-------|--------|----------|
| MTH-01 (per-family/per-region mean explanation) | 20-02 | SATISFIED | F3 at methodology:325, F4 at :335, both locales |
| MTH-02 (LevelChip tier explanation) | 20-02 | SATISFIED | F6 sub-section at methodology:344, both locales |
| MTH-03 (drogas scope note + #trend-formula anchor) | 20-02 | SATISFIED | FamilyBreakdownBars renders note; #trend-formula anchor exists |
| MTH-04 (inline citation links + structural parity assertion) | 20-03 | PARTIAL | ENUSC + INE inline links present; 7-H2 parity confirmed; #national-mean/#media-nacional dead anchors are a gap |
| SRC-01 (INE first-class entry) | 20-01 | SATISFIED | `## INE — population denominator` in SOURCES.md with supply-chain caveat |
| SRC-02 (ENUSC first-class entry + inline links) | 20-01, 20-03 | PARTIAL | ENUSC section present; inline link points to verified URL; `[verify edition]` stub retained |
| SRC-03 (SPD-parent first-class entry) | 20-01 | SATISFIED | `## SPD — institutional authority` present |
| SRC-04 (editorial-parameters note) | 20-01 | SATISFIED | `## Methodology parameters` section with trend window/threshold/<10k rule/unweighted distinction |
| SRC-05 (CI INE spot-check) | 20-04 | SATISFIED | pytest 179 passed; test_ine_population_spotcheck.py confirmed |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `data/SOURCES.md` | 254 | `[verify edition]` stub for ENUSC vintage year | Info | Intentionally retained per review WR-02 fix-note; not a live broken link |

No `TBD`, `FIXME`, `XXX` markers found in phase-modified files.

### Human Verification Required

None. All gaps are verifiable programmatically. The dead-anchor issue is confirmed by grep.

### Gaps Summary

**One gap blocks Success Criterion 3** (SC-3: inline caveats present and anchors referenced by links actually exist).

When WR-01 was fixed (adding the inline "unweighted commune mean — see methodology" caveat to crime-family hero stats), the implementation added links to `#national-mean` (EN) and `#media-nacional` (ES). However, the corresponding `id` attributes were never added to the `<h3>` elements in `methodology.astro` and `metodologia.astro`. Both anchors are dead in the built output.

**Fix is minimal (2 lines):**
- `methodology.astro` line 325: change `<h3>Per-family national mean (F3)</h3>` to `<h3 id="national-mean">Per-family national mean (F3)</h3>`
- `metodologia.astro`: add `id="media-nacional"` to the equivalent ES `<h3>`

All other Success Criteria are met: SOURCES.md has all required entries, methodology explains F3/F4/F6/F2/F5 distinction, drogas scope note renders, #trend-formula anchor works, CI validators 13/13 pass, pytest 179/179 passes, figure registry shows zero orphans.

---

_Verified: 2026-06-19T02:30:00Z_
_Verifier: Claude (gsd-verifier)_
