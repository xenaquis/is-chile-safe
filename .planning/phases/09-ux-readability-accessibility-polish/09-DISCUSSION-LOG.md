# Phase 9: UX / Readability / Accessibility Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 9-ux-readability-accessibility-polish
**Areas discussed:** Explaining "rate per 100k", Crime glossary, Choropleth legend, Comparative context

---

## Explaining "rate per 100k"

| Option | Description | Selected |
|--------|-------------|----------|
| Reusable "?" tooltip + fixed sentence | Reusable info tooltip next to every rate (legend, panel, tables) + one fixed sentence per page | ✓ |
| Legend + methodology page only | Explanation in map legend + link to a methodology page | |
| Inline contextual sentence per table/panel | Visible prose in each table/panel, no tooltip | |

**User's choice:** Reusable "?" tooltip + fixed sentence (D-01)
**Notes:** Consistent, low visual noise, serves all surfaces. Bilingual via i18n.ts.

---

## Crime glossary

| Option | Description | Selected |
|--------|-------------|----------|
| Tooltips + dedicated bilingual /glossary page | Per-family tooltip (reuse FAMILY_DEFS) + dedicated EN/ES glossary page (SEO) | ✓ |
| Inline tooltips only | Definitions on hover/tap, no new page | |
| Glossary page only | Dedicated page, no in-map tooltips | |

**User's choice:** Tooltips + dedicated bilingual glossary page (D-02)
**Notes:** Reuse existing FAMILY_DEFS_EN/ES (do not rewrite). Glossary page must be real prose (avoid thin content), CEAD-attributed.

---

## Choropleth legend

| Option | Description | Selected |
|--------|-------------|----------|
| Numeric ranges + qualitative labels | Each band shows real range (e.g. "0–1,500") + "muy bajo → muy alto" + "por 100k" note | ✓ |
| Qualitative labels only | "muy bajo → muy alto" without numbers | |
| Numeric ranges only | Numbers without qualitative labels | |

**User's choice:** Numeric ranges + qualitative labels (D-03)
**Notes:** Extends Legend.tsx + colors.ts. Must stay legible on mobile.

---

## Comparative context

| Option | Description | Selected |
|--------|-------------|----------|
| Multiplier vs average + bar | "1,8× el promedio nacional/regional" + visual comparison bar | ✓ |
| Percentile among communes | "lower than 70% of communes with data" | |
| Both (multiplier + percentile) | Show both readings | |

**User's choice:** Multiplier vs average + bar (D-04)
**Notes:** Neutral framing only (no absolute safe/dangerous). Reuses loadNationalAverage/loadRegionalAverage. Percentile remains an acceptable secondary framing if planning finds room.

---

## Claude's Discretion

- Exact tooltip interaction (hover + tap/focus for touch & keyboard a11y), component naming, fixed-sentence placement.
- Whether the comparison bar also appears on the static commune money page vs only the interactive panel.
- How original review-driven editorial items (UX/READ/A11Y) split across plans vs the comprehension track.

## Deferred Ideas

- City/commune **rankings by crime family** (most/least by type) — user reiterated mid-discussion → v1.2.
- Interactive commune **comparator**, **A-vs-B** pages, **"safest communes"** rankings, hybrid rollout for rankings → v1.2 (SEED-001).
- WR-03 mobile hamburger keyboard/Escape — a11y carry-over from Phase 8; candidate for Phase 9 A11Y-01 track.
