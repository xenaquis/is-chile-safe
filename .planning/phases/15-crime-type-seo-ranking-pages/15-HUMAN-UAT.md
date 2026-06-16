---
status: partial
phase: 15-crime-type-seo-ranking-pages
source: [15-VERIFICATION.md]
started: 2026-06-16T16:11:59Z
updated: 2026-06-16T16:11:59Z
---

## Current Test

[awaiting human testing]

## Tests

### UAT-15-01 — Locale switcher cross-navigation
- **status:** pending
- **What to check:** On a crime-ranking page, click the language switcher and confirm it lands on the *reciprocal* localized page, not a 404.
  - EN `/crime-ranking/homicide/` → switcher → `/es/ranking-delito/homicidios/`
  - ES `/es/ranking-delito/homicidios/` → switcher → `/crime-ranking/homicide/`
  - Repeat for one family page (e.g. `/crime-ranking/drug-crimes/` ↔ `/es/ranking-delito/drogas/`).
- **Why human:** hreflang/canonical tags are verified present in the built HTML programmatically, but actual in-browser click behavior of the switcher needs a real browser. (Watch for the i18n localized-slug pitfall — ES slugs must be hardcoded, not derived.)

### UAT-15-02 — Editorial accuracy of methodology notes
- **status:** pending
- **What to check:** Read the per-page methodology note on each of the 8 crime-ranking pages (EN + ES) and confirm the prose is factually correct: the CEAD delitos named in each family aggregate are accurate, the "denuncias not convictions" framing is honest, and the homicide page correctly references CEAD subgroup 101.
- **Why human:** CEAD attribution and "denuncias" framing are confirmed present programmatically; factual correctness of the editorial wording requires human judgment.

## Resolved

### CR-01 — Duplicate mislabeled homicide-ranking spoke (RESOLVED)
- Fixed in commit `30c7b7d`; confirmed gone in built HTML (EN + ES). Was: every commune page rendered a second "homicide ranking" link to `/crime/homicide/` (Life-Crimes family). Now filtered.

## Tech Debt (non-blocking)

### CR-02 — Mixed-year ranking display
- Per-commune rate read at its own `latestCompleteYear` while the table heading advertises the national-max `latestYear`. Pre-existing in `/crime/[family].astro`, propagated to the new ranking pages. Does not break SEO indexability or CSEO requirements. Candidate for a future data-fidelity pass.
