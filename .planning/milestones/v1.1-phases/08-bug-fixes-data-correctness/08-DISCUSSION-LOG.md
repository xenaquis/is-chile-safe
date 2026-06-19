# Phase 8: Bug Fixes & Data Correctness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 8-Bug Fixes & Data Correctness
**Areas discussed:** F-005 link strategy, Phase 8/9 finding split, AdSlot OFF placeholder, Re-verification method

---

## F-005 — Broken commune links (region/crime rankings)

| Option | Description | Selected |
|--------|-------------|----------|
| Texto plano (no-rollout) | Non-rollout communes render as plain text (no `<a>`). Zero 404, keeps 12 pages, loses future internal linking. | |
| Construir 346 ligeras | Generate lightweight pages for all 346 communes (ROLLOUT_ALL exists). Max SEO but heavy output + thin-content risk. | |
| Gate a slugs rollout | Linked set limited to the rollout slugs in all rankings — only communes with a page are listed. Shorter but consistent, no 404. | ✓ |

**User's choice:** Gate a slugs rollout
**Notes:** Derive the gate from `loadRolloutCuts()` (rollout.json), not a hardcoded list, so lists auto-expand. Keep the "#N of 346" rank denominator accurate — only displayed rows are gated.

---

## Finding split — Phase 8 vs Phase 9

| Option | Description | Selected |
|--------|-------------|----------|
| F-001 H1 'Commune' ES | One-word ES H1 fix, high SEO value. | ✓ |
| F-007 aria 'Cerrar' EN | Map panel close-button aria-label i18n leak (ResultPanel.tsx ×3). | ✓ |
| F-009 nav móvil | Mobile header has no path to the Map (core product). | ✓ |
| Polish a Phase 9 | Defer the 5 Polish findings (F-002/003/004/006/008) with written justification. | ✓ |

**User's choice:** Fix F-001, F-007, F-009 in Phase 8; defer all 5 Polish to Phase 9.
**Notes:** BUGFIX-05 closeout must record a one-line deferral reason per Polish finding. F-002 (new legal pages) is a go-live gate, not a bug.

---

## AdSlot OFF — reserved-space appearance

| Option | Description | Selected |
|--------|-------------|----------|
| Espacio en blanco | Remove dashed placeholder box; reserve height invisibly. Clean pre-AdSense look, no CLS. | ✓ |
| Mantener placeholder punteado | Keep visible dashed box (current). Useful in dev, looks unfinished in prod. | |
| Solo verificar, no tocar | AdSlot already meets criterion; verify only. | |

**User's choice:** Espacio en blanco
**Notes:** Height reservation and exact-string env-gating stay intact; only the visible dashed box is removed.

---

## Re-verification method

| Option | Description | Selected |
|--------|-------------|----------|
| Build + grep + spot-check | npm build + validators + grep corrected strings + fetch previously-404 URLs. Fast, no BrowserOS, chainable. | ✓ |
| Re-correr BrowserOS E2E | Re-navigate affected pages with BrowserOS inline. Faithful but slow/fragile. | |
| Híbrido | Build+grep for most; BrowserOS only for F-009/F-007. | |

**User's choice:** Build + grep + spot-check
**Notes:** Chain build + validate in one command (OneDrive dist/ desync). BrowserOS spot-check of F-009/F-007 is optional, not required; if done, run inline with a no-spaces screenshot path.

---

## Claude's Discretion

- Where localized UI strings live (locale dict vs inline) for F-001/F-007 — follow existing i18n pattern.
- Exact mobile-nav UX (hamburger drawer vs inline collapse) for F-009 — lightest pattern consistent with the header; requirement is only reachability of Home/Map/Methodology.

## Deferred Ideas

- F-002 cookie/accessibility legal pages → Phase 9 / go-live gate (new pages).
- F-003 ES methodology parity → Phase 9 (READ-02).
- F-004 thin contact pages → Phase 9.
- F-006 ES region display-name grammar → Phase 9 (READ).
- F-008 incident "coming soon" toast → Phase 9 (UX-01).
- Rollout expansion (more commune pages) → out of scope; F-005 solved by gating.
