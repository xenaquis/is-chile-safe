# Phase 14: Homicide as a First-Class Category - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-16
**Phase:** 14-homicide-as-a-first-class-category
**Areas discussed:** Data scope, Filter UX, Choropleth scaling, Zero/low-case framing, Data depth, Counts fetch

---

## Data scope (missing homicide data)

Scout finding surfaced before discussion: `featured_rates.homicidios = {}` in all
346 comuna files; `scrape_cead.py:448` hardcodes empty — CEAD subgroup-101 scrape
never implemented.

| Option | Description | Selected |
|--------|-------------|----------|
| Scrape it in this phase | Implement CEAD subgroup-101 fetch, populate data, then build UI | ✓ |
| Split: data first, then UI | Treat scrape as a prerequisite plan/wave feeding the UI | |
| UI now, stub data | Build UI against schema, ship with empty states | |

**User's choice:** Scrape it in this phase.
**Notes:** Data acquisition is in scope; two-stage within the phase (data → UI).

---

## Filter UX

| Option | Description | Selected |
|--------|-------------|----------|
| 8th chip in the row | Add homicide chip alongside the 7 family chips, featured-dot | ✓ |
| Distinct/grouped treatment | Visually nest under/adjacent to 'vida' as a subgroup | |
| Let research/planner decide | Capture intent, let planner place it | |

**User's choice:** 8th chip in the row.
**Notes:** Peer chip placement; planner should still label it honestly as a vida subgroup.

---

## Choropleth scaling

| Option | Description | Selected |
|--------|-------------|----------|
| Independent scale for homicide | Own quantile/bucket breakpoints + own legend | ✓ |
| Reuse existing buckets | Keep shared 5-bucket scale | |
| Let research decide | Capture concern, research recommends method | |

**User's choice:** Independent scale for homicide.
**Notes:** Magnitude mismatch (single digits vs hundreds /100k); research to pick bucketing method.

---

## Zero/low-case framing

| Option | Description | Selected |
|--------|-------------|----------|
| Show rate + absolute count + year | Per-100k + raw count + CEAD year | ✓ |
| Rate only, with 0/N-A states | Per-100k like other stats, explicit 0 states | |
| Let planner decide framing | Capture concern, planner chooses | |

**User's choice:** Show rate + absolute count + year.
**Notes:** Honest framing for rare events; explicit non-alarmist 0 state; editorial rule honored.

---

## Data depth (history + model placement)

| Option | Description | Selected |
|--------|-------------|----------|
| Full series, like families | 2005–2025 rate+count in series + featured_rates | ✓ |
| Latest complete year only | Most recent year only, payload + featured_rates | |
| Let research recommend | Capture both as acceptable | |

**User's choice:** Full series, like families.
**Notes:** Enables trend arrow + panel + Phase 15 SEO pages without a second scrape.

---

## Counts fetch (second CEAD measure)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — fetch both measures | rate (medida=2) + count (medida=1) per query | ✓ |
| Only if cheap; else rate-only | Prefer both, fall back if heavy | |
| Let research decide | Capture want for counts, research confirms | |

**User's choice:** Yes — fetch both measures.
**Notes:** ~doubles homicide-subgroup requests; keep polite with existing inter-batch delays. Research must confirm the live subgroup-101 selector param.

---

## Claude's Discretion

- Bucketing algorithm for the independent homicide scale (research-recommended).
- Whether the 8th chip reuses the `featured` flag or a new `CHIP_DEFS` field.
- Panel layout/placement of the homicide figure in `ResultPanel.tsx`.
- Whether homicide rides as a separate payload field vs the `by_family` array
  (leaning separate field to preserve the family-index contract).

## Deferred Ideas

- `secuestros` subgroup as a first-class category (subgroup ID still unconfirmed).
- Homicide crime-type SEO ranking pages → Phase 15 (CSEO-01/02).
