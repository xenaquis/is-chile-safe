---
phase: 20-methodology-sources-hardening
plan: "01"
subsystem: documentation
tags: [sources, methodology, provenance, ine, enusc, spd, editorial-parameters]
dependency_graph:
  requires: []
  provides: [SRC-01, SRC-02, SRC-03, SRC-04]
  affects: [data/SOURCES.md, plan-20-02, plan-20-03, plan-20-04]
tech_stack:
  added: []
  patterns: []
key_files:
  modified:
    - data/SOURCES.md
decisions:
  - "All unconfirmed URLs carry [verify URL] markers — never fabricated (threat T-20-01 mitigated)"
  - "INE supply-chain caveat documents bastianolea mirror risk + P20 CI mitigation"
  - "Methodology parameters documented as editorial decisions, not external standards"
metrics:
  duration: "~10 minutes"
  completed: 2026-06-19
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 20 Plan 01: SOURCES.md Expansion (SRC-01..04) Summary

Expanded `data/SOURCES.md` with four new registry entries covering INE population denominator, ENUSC underreporting survey, SPD institutional authority, and labeled editorial parameters — establishing the "no orphan number" backbone for plans 20-02 and 20-03.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Author INE + ENUSC first-class classes (SRC-01, SRC-02) | 9e6b1dc | data/SOURCES.md |
| 2 | Add SPD-parent class, CEAD taxonomy provenance, editorial-parameters (SRC-03, SRC-04) | 9e6b1dc | data/SOURCES.md |

## What Was Done

**Task 1 — INE + ENUSC:**
- Added `## INE — population denominator (per-100k + <10k rule)` with official landing URL (marked `[verify URL]`), measure semantics (denominator + <10k gate), Censo 2017 vintage, `fetch_ine_population.py` fetch provenance, and a SUPPLY-CHAIN CAVEAT documenting the bastianolea community mirror and P20 CI mitigation.
- Added `## ENUSC — underreporting / cifra negra` with publisher (SPD/INE co-executed), household victimization semantics, `[verify URL]` markers for both INE and SPD portals, used-by reference to methodology.astro lines, and licence.

**Task 2 — SPD-parent + editorial parameters:**
- Added `## SPD — institutional authority (parent of CEAD + taxonomy)` with portal URL, role description as CEAD parent and taxonomy owner, and taxonomy provenance referencing `ajax_2.php seleccion=9`.
- Added `### Taxonomy provenance` subsection under the existing `## CEAD` class, citing the catalog endpoint and cross-referencing the new SPD section.
- Added institutional note under the existing `## SPD — homicide reference snapshot` linking to the new SPD-parent entry (SC-07).
- Added `## Methodology parameters (editorial decisions)` covering the 5% trend threshold, 3-year window, <10k exclusion (retained + flagged, not silently dropped), and the UNWEIGHTED national aggregate mean distinction.

## Deviations from Plan

None — plan executed exactly as written. Both tasks merged into one atomic commit because all changes were in a single file with no intermediate verification state.

## Threat Flags

No new threat surface. Existing threats T-20-01 (invented URLs) and T-20-02 (INE mirror supply chain) are mitigated as specified: all unconfirmed URLs carry `[verify URL]`; supply-chain caveat documented with CI mitigation cross-reference.

## Known Stubs

Per plan design, the following remain intentionally unresolved and require downstream action:

- `[verify URL]` on the INE landing page — requires manual confirmation against live endpoint before publish.
- `[verify URL]` on the ENUSC landing page — also requires confirming whether INE or seguridadpublica.gov.cl is canonical.
- `[verify edition]` on the ENUSC vintage — the exact survey edition year used for on-page claims must be identified.

These stubs are intentional (editorial guardrail: no fabricated URLs) and are tracked for plan 20-03 (methodology page wiring).

## Self-Check: PASSED

- `data/SOURCES.md` exists and contains `## INE`, `## ENUSC`, `## SPD — institutional authority`, `## Methodology parameters`, `bastianolea`, `seleccion=9`, `UNWEIGHTED`.
- Commit 9e6b1dc verified in git log.
- SII / Fiscalia / SPD-VHC stubs remain unchanged (reference snapshots, not promoted).
