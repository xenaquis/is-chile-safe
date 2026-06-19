---
phase: 09-ux-readability-accessibility-polish
verified: 2026-06-15T18:35:00Z
status: passed
score: 7/7 requirements verified
overrides_applied: 0
note: >
  Produced retroactively during the v1.1 milestone close to fill the artifact
  gap flagged by v1.1-MILESTONE-AUDIT.md. Phase 9 coverage was already
  substantively evidenced by 09-05-SUMMARY.md + 09-VALIDATION.md; this report
  formalizes it and records the closure of the two audit-flagged partials
  (READ-02 / F-006 and A11Y-01 / WR-03) by commit d9593a3.
human_verification:
  - test: "Tab-walk /map/, /glossary/, /is-santiago-safe/ in a real browser at desktop and <640px"
    expected: "Visible teal focus ring on every interactive control; on mobile, Tab reaches the hamburger and Space opens the nav (WR-03 fix)"
    why_human: "Rendered :focus-visible outlines and keyboard interaction are only observable in a live browser; CSS rules and the focusable checkbox are code-verified, the visible-outline confirmation is human"
  - test: "Open a commune panel (map polygon or search select) on /map/"
    expected: "Rate '?' tooltip opens via keyboard; multiplier + comparison bar render with neutral framing"
    why_human: "Client-island render requires an open panel; styles/components are built but the interactive render is human-observable only"
---

# Phase 9: UX / Readability / Accessibility Polish — Verification Report

**Phase Goal:** Money pages are easy to scan and pleasant to read in both languages; editorial tone is sober throughout; key a11y and SEO meta signals are present in sampled pages.
**Verified:** 2026-06-15T18:35:00Z
**Status:** passed
**Re-verification:** Yes — formal report produced at v1.1 close; incorporates the F-006 + WR-03 gap-closure (commit d9593a3) that resolved the two audit-flagged partials.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every money page has exactly one H1; scannable H2/H3 hierarchy | VERIFIED | `grep -c "<h1" src/pages/is-santiago-safe.astro` == 1; build emits all pages with single-H1 templates (09-VALIDATION Task 1) |
| 2 | DataCallout/StatCard each communicate one idea + CEAD source; callout↔prose redundancy removed | VERIFIED (browser) | 09-VALIDATION Task 2: is-santiago-safe / is-chile-safe clean; safest-cities single editorially-justified reuse flagged, not a defect |
| 3 | Editorial prose ~720px column with paragraph rhythm | VERIFIED | `grep -c ".editorial-prose p" src/styles/global.css` ≥ 1; `.editorial-prose` max-width applied |
| 4 | EN/ES editorial parity; no absolute "peligroso/seguro" phrasing site-wide | VERIFIED | ES methodology 14,685 bytes (≥11k parity); tone grep returns no absolute verdicts; forbidden-language validator PASS (772 pages, 0 terms) |
| 5 | Sampled pages: WCAG-AA contrast, visible focus, alt/aria on map controls, valid title/meta/canonical/hreflang/JSON-LD | VERIFIED | axe-core 4.10 on /map/ → 0 contrast violations; map year `<select>` + 13 buttons all named (0 unnamed); glossary meta 1/1/1/1; FAQPage JSON-LD present on is-santiago-safe |

**Score:** 5/5 truths verified (build + grep + live BrowserOS axe/aria session; residual visual focus-ring + panel-tooltip checks are human, consistent with this being a manual-verify phase).

---

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| UX-01 | Single H1, scannable hierarchy, ~5s purpose clarity | VERIFIED | h1=1 grep; build clean; 5s-scan is subjective human (low risk) |
| UX-02 | One-idea callouts + CEAD source; redundancy removed; legend/multiplier neutral framing | VERIFIED | Browser Task 2: legend 5 bands EN/ES, multiplier bar present, redundancy audited |
| READ-01 | 720px prose column + rhythm | VERIFIED | global.css `.editorial-prose p` rule confirmed |
| READ-02 | ES methodology parity **+ grammatical ES region naming** | VERIFIED | ES methodology 14,685 B; **F-006 closed (commit d9593a3)** — `regionNameEs()` now renders "Región Metropolitana" / "Región del Biobío" / "Región de Tarapacá" on region pages and across the ES prose engine; 0 "Región de Metropolitana" in dist |
| READ-03 | Sober tone site-wide; CEAD+year attribution | VERIFIED | Tone grep clean; forbidden-language validator PASS |
| A11Y-01 | Focus rings, alt/aria, **keyboard-operable nav**, WCAG-AA | VERIFIED | axe contrast PASS; map controls named; **WR-03 closed (commit d9593a3)** — hamburger checkbox is sr-only-but-focusable with the accessible name + focus ring; keyboard can open the mobile nav |
| A11Y-02 | Valid title/meta/canonical/hreflang + FAQPage JSON-LD | VERIFIED | Glossary meta signals present; FAQPage JSON-LD on is-santiago-safe |

All 7 Phase-9 requirements verified. No orphaned requirements.

---

### Audit-Flagged Partials — Closure

| Audit finding | Was | Now | Evidence |
|---------------|-----|-----|----------|
| READ-02 / F-006 — "Región de Metropolitana" ungrammatical | partial | CLOSED | `regionNameEs()` helper (i18n.ts); ES region page h1/title/meta/JSON-LD + ES prose engine use it; dist verified (Metropolitana/Biobío/Maule/Tarapacá all grammatical); commit d9593a3 |
| A11Y-01 / WR-03 — mobile hamburger keyboard-inoperable | partial | CLOSED | PageHeader.astro checkbox now sr-only-but-focusable carrying the accessible name; label decorative; `:focus-visible` ring on burger; commit d9593a3 |

Build after closure: clean; **10/10 validators pass** (structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage).

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Production build clean (ROLLOUT_ALL) | `npm run build` | exit 0, all pages built | PASS |
| ES region grammar correct in dist | `grep "de Metropolitana" dist/es/region/metropolitana/index.html` | 0 (h1 = "Región Metropolitana") | PASS |
| "del" regions correct | `grep "Región del Biobío" dist/es/region/biobio/index.html` | present | PASS |
| ES prose grammar (RM comuna) | `grep -c "Región Metropolitana" dist/es/comuna/buin/index.html` | 4 (0 "región de Metropolitana") | PASS |
| Hamburger keyboard path | source: checkbox focusable + aria-label, no `display:none`/`tabindex=-1` | confirmed | PASS |
| Full validator suite | `npm run validate` | 10/10 PASS | PASS |

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None in Phase-9 scope | — | — | — |

Pre-existing out-of-scope item (from Phase 03/04, not a Phase-9 regression): axe `aria-prohibited-attr` on the hidden `data-map-locate-label` span across 6 map pages — recommended future cleanup, logged in 09-VALIDATION and v1.1 tech-debt.

---

### Human Verification Required (residual, low-risk)

1. **Focus-ring Tab-walk** — confirm visible teal outline on all interactive controls across /map/, /glossary/, /is-santiago-safe/ at desktop and <640px; confirm Tab reaches the hamburger and Space opens the mobile nav (WR-03).
2. **Commune-panel interactive render** — open a panel; confirm rate "?" tooltip keyboard operation and multiplier/comparison-bar render with neutral framing.

These are inherently visual/interactive confirmations of code that is verified and built; they were the standing manual rows for this manual-verify phase, not missing implementation.

---

### Gaps Summary

No implementation gaps. All 7 requirements have code/build/browser evidence. The two audit-flagged partials (READ-02/F-006, A11Y-01/WR-03) are closed by commit d9593a3 with dist + validator confirmation. Remaining items are low-risk human visual checks.

---

_Verified: 2026-06-15T18:35:00Z_
_Verifier: Claude (gsd-verifier, retroactive at v1.1 close)_
