---
phase: 25
plan: "07"
subsystem: a11y / keyboard-navigation
tags: [a11y, skip-link, focus-visible, keyboard, WCAG]
dependency_graph:
  requires: [25-01, 25-04]
  provides: [skip-link-on-every-page, focus-visible-restored]
  affects: [BaseLayout, global.css, communes pages, ContactForm]
tech_stack:
  added: []
  patterns: [skip-link hidden until focused, :focus:not(:focus-visible) guard pattern]
key_files:
  created: []
  modified:
    - site/src/layouts/BaseLayout.astro
    - site/src/styles/global.css
    - site/src/pages/communes/index.astro
    - site/src/pages/es/comunas/index.astro
    - site/src/components/ContactForm.astro
decisions:
  - outline:none on .search-input base state (map.css) is harmless — specificity (0,1,0) < *:focus-visible (0,1,1); left as-is
  - skip-link uses lang prop for EN/ES copy, no translation file needed
metrics:
  duration: ~12m
  completed: "2026-07-02"
  tasks: 2
  files: 5
---

# Phase 25 Plan 07: Skip-Link + Focus-Visible Sweep Summary

**One-liner:** Skip-to-main anchor (visually hidden until focused) added to BaseLayout as first body child; unconditional `outline:none` overrides on `.dir-search` and `.form-input` guarded with `:not(:focus-visible)` so keyboard focus outlines are restored.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Skip-to-main link + main landmark id + .skip-link CSS | 5381a2a | BaseLayout.astro, global.css |
| 2 | Remove/guard unconditional outline:none on focusable links | 0ee08ed | communes/index.astro, es/comunas/index.astro, ContactForm.astro |

## What Was Built

**Task 1 — Skip link**
- `<a href="#main-content" class="skip-link">` added as first `<body>` child in `BaseLayout.astro`. Text is `"Skip to main content"` (EN) / `"Ir al contenido principal"` (ES) via `lang` prop.
- `<main class="page-content">` now carries `id="main-content"` as anchor target.
- `.skip-link` CSS block added to `global.css` after the existing `:focus-visible` rule: `position: absolute; top: -40px` hidden off-screen, slides to `top: var(--sm)` on `:focus`. Uses design tokens (`--primary`, `--md`, `--sm`, `--xs`, `--text-label`, `--weight-strong`).

**Task 2 — Focus-visible sweep**

Candidate locations inspected:

| Location | Selector | Assessment | Action |
|----------|----------|------------|--------|
| map.css:327 | `.search-input { outline: none }` | Base state (no `:focus`); specificity (0,1,0) < `*:focus-visible` (0,1,1) — global rule wins on keyboard focus | Left as-is (harmless) |
| communes/index.astro:358 | `.dir-search:focus { outline: none }` | Specificity (0,2,0) > (0,1,1) — DEFEATS focus-visible | Moved `outline:none` to `.dir-search:focus:not(:focus-visible)` |
| es/comunas/index.astro:354 | `.dir-search:focus { outline: none }` | Same as above | Same fix applied |
| ContactForm.astro:116 | `.form-input:focus { outline: none }` | Same pattern | Moved to `.form-input:focus:not(:focus-visible)` |

Global rule at `global.css:175` (`*:focus:not(:focus-visible) { outline: none }`) is **unchanged**.

## Verification

- `npm run build` — 834 pages built, exit 0
- `npm run validate` — 14/14 validators passed
- `grep -q "skip-link" dist/index.html && grep -q 'id="main-content"' dist/index.html` — PASS
- `npm run check` — 8 pre-existing TypeScript errors (ComparatorPairsLinks.astro, RankingTableEnhancer.astro, commune/[slug].astro, es/noticias.astro, es/comuna/[slug].astro); none in files modified by this plan; logged to deferred-items.

## Deviations from Plan

**1. [Out-of-scope pre-existing] `npm run check` exits non-zero (8 TypeScript errors)**
- Found during Task 2 verification
- All 8 errors are in files NOT modified by this plan
- No action taken per deviation scope boundary rule
- Logged here for tracking

## Known Stubs

None.

## Threat Flags

None — a11y-only changes; no new network endpoints or data surfaces introduced.

## Self-Check: PASSED

- `5381a2a` exists: `git log --oneline` confirms feat(25-07) commit
- `0ee08ed` exists: `git log --oneline` confirms fix(25-07) commit
- `dist/index.html` contains `skip-link` and `id="main-content"` (grep verified)
- `.skip-link` rule present in `global.css`
- Build and validate pass clean
