---
phase: 08-bug-fixes-data-correctness
plan: "04"
subsystem: frontend/ads
tags: [bugfix, adsense, cls, cosmetic]
dependency_graph:
  requires: []
  provides: [BUGFIX-04]
  affects: [AdSlot.astro]
tech_stack:
  added: []
  patterns: [env-gated CSS-only change]
key_files:
  created: []
  modified:
    - site/src/components/AdSlot.astro
decisions:
  - "CSS-only removal of dashed border — no logic, no env-gate, no markup changes"
metrics:
  duration: 5m
  completed: "2026-06-15"
  tasks_completed: 1
  files_changed: 1
---

# Phase 08 Plan 04: AdSlot Dashed-Border Removal (BUGFIX-04) Summary

**One-liner:** CSS-only removal of dashed-border placeholder from AdSlot, preserving 90px/50px height reservation and exact-compare env gate.

## Tasks

| # | Name | Commit | Status |
|---|------|--------|--------|
| 1 | Remove dashed-border placeholder, keep reserved height + env gate | 3fda7fc | done |

## What Was Done

Removed two CSS declarations from the `.ad-placeholder` rule in `site/src/components/AdSlot.astro`:
- `border: 2px dashed var(--line);`
- `border-radius: var(--radius);`

The placeholder div now renders as a blank space (background color only) instead of a dashed rectangle. All structural and functional invariants were preserved unchanged:
- `const enabled = import.meta.env.ADSENSE_ENABLED === 'true';` (exact string compare)
- `enabled && publisherId` guard around `<ins class="adsbygoogle">`
- `.ad-slot--content` / `.ad-slot--bottom` height reservations: 90px desktop, 50px mobile

Verification confirmed zero `adsbygoogle` elements in built `dist/index.html` with AdSense OFF, and `npm run build` succeeded in 31s.

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes. The T-08-06 threat (third-party script injection via env gate) remains fully mitigated — the change is CSS-only and the `=== 'true'` gate is untouched.

## Self-Check: PASSED

- `site/src/components/AdSlot.astro` modified: confirmed (git diff shows 2 deletions)
- Commit 3fda7fc: confirmed (`git log --oneline -1`)
- Build output verified: BUGFIX-04 OK message from node verification script
