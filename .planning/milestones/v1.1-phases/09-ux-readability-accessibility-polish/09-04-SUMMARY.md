---
phase: 09-ux-readability-accessibility-polish
plan: "04"
subsystem: editorial-content
tags: [readability, parity, editorial-audit, i18n]
dependency_graph:
  requires: [09-01]
  provides: [READ-02, READ-03, UX-01, UX-02]
  affects: [es/metodologia, is-santiago-safe, is-chile-safe, safest-cities-in-chile]
tech_stack:
  added: []
  patterns: [editorial-prose-expansion, callout-redundancy-removal]
key_files:
  created: []
  modified:
    - site/src/pages/es/metodologia.astro
    - site/src/pages/is-santiago-safe.astro
decisions:
  - Removed verbatim rate restatement from is-santiago-safe prose (kept % comparison + context)
  - ES methodology now self-contained — removed the EN link stub that was placeholder content
metrics:
  duration: 12m
  completed: "2026-06-15"
  tasks: 2
  files: 2
---

# Phase 09 Plan 04: Editorial Content Parity and Audit Summary

**One-liner:** ES methodology expanded from ~6.9 KB stub to ~13 KB at full content parity with EN across all 6 sections; top editorial pages audited for single-H1, callout redundancy, and sober tone.

## Tasks Completed

| Task | Commit | Files |
|------|--------|-------|
| 1: Expand ES methodology to content parity (READ-02) | 2ddc836 | site/src/pages/es/metodologia.astro |
| 2: Heading + callout-redundancy + tone audit on editorial pages | aa08758 | site/src/pages/is-santiago-safe.astro |

## Task 1: ES Methodology Parity (READ-02 / F-003)

`site/src/pages/es/metodologia.astro` expanded from 52 lines of body prose (stub) to 206 net insertions at full content depth.

All 6 H2 sections now match EN depth:

1. **Fuente de datos: CEAD** — Added Carabineros/PDI breakdown, pipeline/GitHub details, annual-series-only clarification, partial-year exclusion rationale.
2. **Cómo se calcula la tasa** — Added explanation of why CEAD rate is used directly (not recomputed), sum-vs-mean distinction with explicit note on what the national total is vs. our computed mean, low-population exclusion rationale.
3. **Subregistro (cifra negra)** — Expanded from one paragraph to full section with ENUSC reference, per-crime-type patterns (property, VIF, homicidios), and caveat that low rate may reflect underreporting, low prevalence, or both.
4. **Fórmula de tendencia** — Ported ordered list (take year N and N−3, compute %, apply 5% threshold), added 3-year window rationale (pandemic disruption), data-minimum caveat, threshold-choice explanation.
5. **Criterios de comparación** — Converted to bullet list matching EN structure with metric, year, exclusion, ranking basis, and national average definition entries; added note excluding international comparisons.
6. **Lo que este sitio NO dice** — Expanded from 5 terse list items to 5 full prose bullets matching EN content: no absolute verdicts, no victimisation probability, no predictive claims, no neighbourhood ranking, no international comparisons.

Acceptance criteria verified:
- File size: ~13 KB (≥11,000 bytes required; EN is ~13.4 KB — within 15%)
- H1 count: 1
- H2 count: 6
- No "peligroso" or "dangerous": confirmed
- "seguro" only appears in neutral institutional phrases ("Ministerio del Interior y Seguridad Pública") — not absolute framing
- `npm run build` exits 0

## Task 2: Heading + Callout-Redundancy + Tone Audit

### is-santiago-safe.astro

- **UX-01 (H1):** 1 H1. H2 hierarchy correct (6 H2s, no skipped levels). No change needed.
- **UX-02 (callout redundancy):** Two DataCallouts at top of first section show Santiago rate and national average. The immediately following paragraph in "Santiago Commune vs. Greater Santiago" restated both figures verbatim (`{Math.round(rate).toLocaleString('en-US')} per 100,000` and `{Math.round(nationalAvg).toLocaleString('en-US')} per 100,000`). **Fix applied:** removed duplicated raw figures; kept the % comparison (`{Math.abs(vsNationalPct)} % above/below`) and added floating-population context sentence. Each callout still carries CEAD + year attribution.
- **READ-03 (tone):** No absolute "is safe" / "is dangerous" phrasing found. Relative wording throughout. No change needed.

### is-chile-safe.astro

- **UX-01 (H1):** 1 H1. H2 hierarchy correct. No change needed.
- **UX-02 (callout redundancy):** One DataCallout (national average). "What the National Average Tells You" section references it contextually but does not restate the exact figure verbatim in adjacent prose — compliant as-is. No change needed.
- **READ-03 (tone):** No absolute framing. All stats cite CEAD + year. Compliant. No change needed.

### safest-cities-in-chile.astro

- **UX-01 (H1):** 1 H1. H2 hierarchy correct (5 H2s). No change needed.
- **UX-02 (callout redundancy):** One DataCallout (national average). "How to Interpret This Ranking" restates both the top-ranked commune's rate and national mean — but the top-commune rate is not in any DataCallout (the table is the source), and the prose adds the interpretive comparison ("lower reported police-recorded incidents, not necessarily lower actual crime prevalence"). This is contextual commentary, not verbatim callout duplication. Compliant as-is. No change needed.
- **READ-03 (tone):** Already uses careful disclaimers throughout ("not an absolute guarantee of safety", "not a definitive guide", "this ranking does not claim to identify the 'objectively safest' places"). Compliant. No change needed.

## Deviations from Plan

None — plan executed exactly as written. Task 2 found one genuine UX-02 defect on is-santiago-safe (callout-prose stat duplication) and applied a surgical fix; the other two pages were already compliant.

## Known Stubs

None.

## Threat Flags

None — pure authored static content edits; no new endpoints, auth paths, or schema changes.

## Self-Check: PASSED

- `site/src/pages/es/metodologia.astro` — exists and expanded
- `site/src/pages/is-santiago-safe.astro` — exists and patched
- Commits 2ddc836 and aa08758 verified in git log
- Build exits 0
