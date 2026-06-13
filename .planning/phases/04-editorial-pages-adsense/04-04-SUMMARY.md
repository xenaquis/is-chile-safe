---
phase: 04-editorial-pages-adsense
plan: "04"
subsystem: editorial-pages-en
tags: [editorial, faq, seo, hreflang, data-callout, json-ld, cead]
dependency_graph:
  requires: [04-01, 04-03]
  provides:
    - site/src/pages/index.astro (extended)
    - site/src/pages/is-chile-safe.astro
    - site/src/pages/is-santiago-safe.astro
    - site/src/pages/valparaiso-safety.astro
    - site/src/pages/vina-del-mar-safety.astro
    - site/src/pages/concepcion-safety.astro
    - site/src/pages/es/delitos-por-comuna.astro (hreflang stub)
    - site/src/pages/es/seguridad-valparaiso.astro (hreflang stub)
    - site/src/pages/es/seguridad-vina-del-mar.astro (hreflang stub)
    - site/src/pages/es/seguridad-concepcion.astro (hreflang stub)
  affects:
    - dist/ (83 pages built)
tech_stack:
  added: []
  patterns:
    - "EditorialLayout used for all EN editorial pages (720px prose + gated AdSlot)"
    - "FAQPage JSON-LD built in page frontmatter, passed via EditorialLayout -> BaseLayout jsonLd prop"
    - "WebPage JSON-LD for non-FAQ city pages (about: CEAD Dataset)"
    - "loadNationalAverage() (MEAN) for national callout — never loadNational().series[].rate_per_100k (SUM)"
    - "loadCommune(cut) + latestCompleteYearRate() for city DataCallouts"
    - "ES stub pages created for hreflang reciprocity; Plan 06 will flesh out full ES content"
key_files:
  created:
    - site/src/pages/is-chile-safe.astro
    - site/src/pages/is-santiago-safe.astro
    - site/src/pages/valparaiso-safety.astro
    - site/src/pages/vina-del-mar-safety.astro
    - site/src/pages/concepcion-safety.astro
    - site/src/pages/es/delitos-por-comuna.astro
    - site/src/pages/es/seguridad-valparaiso.astro
    - site/src/pages/es/seguridad-vina-del-mar.astro
    - site/src/pages/es/seguridad-concepcion.astro
  modified:
    - site/src/pages/index.astro
decisions:
  - "ES stub pages added for hreflang reciprocity (Rule 2): hreflang.mjs validator requires reciprocal pages to exist in dist/; ES editorial content deferred to Plan 06"
  - "is-santiago-safe esPath self-references /is-santiago-safe/ per slug_flag (no ES pair in EDIT-02)"
  - "CUT codes verified against data/cead/meta/index.json: Santiago 13101, Valparaiso 5101, Vina del Mar 5109, Concepcion 8101"
  - "All national callouts use loadNationalAverage() (MEAN of commune rates); SUM from loadNational() never used"
metrics:
  duration: "25m"
  completed: "2026-06-13"
  tasks: 3
  files: 10
---

# Phase 04 Plan 04: EN Editorial Pages (Home + 5 City Pages) Summary

Six EN editorial pages authored with sober CEAD-sourced prose: index.astro extended with national DataCallout + ~900-word editorial; two FAQ pages (is-chile-safe, is-santiago-safe) emitting FAQPage JSON-LD with 6 FAQ items each; three city pages (Valparaíso, Viña del Mar, Concepción) with WebPage JSON-LD and CEAD DataCallouts. Four ES stub pages created to satisfy hreflang reciprocity (Plan 06 will author full ES content).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | EN home extended + is-chile-safe FAQ | 2af79f5 | site/src/pages/index.astro, site/src/pages/is-chile-safe.astro |
| 2 | is-santiago-safe FAQ + valparaiso-safety | b6b3485 | site/src/pages/is-santiago-safe.astro, site/src/pages/valparaiso-safety.astro |
| 3 | vina-del-mar-safety + concepcion-safety + ES stubs | 9af362f | site/src/pages/vina-del-mar-safety.astro, site/src/pages/concepcion-safety.astro, 4x ES stubs |

## Verification Results

- Build: 83 pages, 9/9 validators pass
- forbidden-language: 83 pages scanned, 0 forbidden terms
- hreflang: 83 pages, all reciprocal pairs resolve
- FAQPage JSON-LD present on is-chile-safe and is-santiago-safe
- WebPage JSON-LD (about: CEAD Dataset) present on valparaiso-safety, vina-del-mar-safety, concepcion-safety
- All DataCallouts use loadNationalAverage() (MEAN) and latestCompleteYearRate() — SUM pitfall avoided

## Deviations from Plan

### Auto-added Missing Critical Functionality

**1. [Rule 2 - Missing] ES hreflang stub pages**
- **Found during:** Task 3 verification (hreflang.mjs exit 1)
- **Issue:** hreflang.mjs validator requires reciprocal ES pages to exist in dist/. The four EN editorial pages created in Tasks 1-3 point to ES slugs (/es/delitos-por-comuna/, /es/seguridad-valparaiso/, /es/seguridad-vina-del-mar/, /es/seguridad-concepcion/) that don't exist until Plan 06.
- **Fix:** Created 4 ES stub pages with minimal editorial content (CEAD DataCallouts + brief ES description + links to EN counterpart and commune detail page). These are valid pages — not empty redirects — so hreflang validator passes.
- **Files modified:** es/delitos-por-comuna.astro, es/seguridad-valparaiso.astro, es/seguridad-vina-del-mar.astro, es/seguridad-concepcion.astro
- **Commit:** 9af362f

## Known Stubs

The four ES stub pages (es/delitos-por-comuna, es/seguridad-valparaiso, es/seguridad-vina-del-mar, es/seguridad-concepcion) contain minimal content — DataCallout + a short paragraph — rather than the full 900-1200 word editorial prose planned for those pages. This is intentional: Plan 06 will replace the stubs with full ES editorial content. The stubs are valid pages with real CEAD data; they are not empty redirects.

The is-santiago-safe esPath self-references /is-santiago-safe/ per the slug_flag in the plan (no ES pair in EDIT-02). This is not a stub — it is the specified behavior.

## Threat Flags

No new threat surface beyond the plan's threat model:
- T-04-09: All editorial prose sober — no absolute safety verdicts; forbidden-language gate confirms 0 violations
- T-04-10: loadNationalAverage() (MEAN) confirmed for all national callouts; SUM never used
- T-04-06: FAQPage JSON-LD via BaseLayout set:html (XSS-safe path) — confirmed

## Self-Check: PASSED

- site/src/pages/is-chile-safe.astro: FOUND
- site/src/pages/is-santiago-safe.astro: FOUND
- site/src/pages/valparaiso-safety.astro: FOUND
- site/src/pages/vina-del-mar-safety.astro: FOUND
- site/src/pages/concepcion-safety.astro: FOUND
- site/src/pages/es/delitos-por-comuna.astro: FOUND
- site/src/pages/es/seguridad-valparaiso.astro: FOUND
- site/src/pages/es/seguridad-vina-del-mar.astro: FOUND
- site/src/pages/es/seguridad-concepcion.astro: FOUND
- Commit 2af79f5: FOUND
- Commit b6b3485: FOUND
- Commit 9af362f: FOUND
