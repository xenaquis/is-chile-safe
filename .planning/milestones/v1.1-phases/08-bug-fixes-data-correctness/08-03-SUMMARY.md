---
phase: 08-bug-fixes-data-correctness
plan: "03"
subsystem: frontend/header
tags: [mobile-nav, hamburger, css-only, i18n, a11y, F-009]
dependency_graph:
  requires: []
  provides: [mobile-nav-hamburger, nav_menu_open-i18n-string]
  affects: [site/src/components/PageHeader.astro, site/src/config/i18n.ts]
tech_stack:
  added: []
  patterns: [css-checkbox-checked-sibling-nav, zero-client-directive-D09]
key_files:
  created: []
  modified:
    - site/src/config/i18n.ts
    - site/src/components/PageHeader.astro
decisions:
  - Zero-JS checkbox pattern chosen per D-09 (no client:* directives in PageHeader)
  - nav_menu_open string added to I18nStrings interface and both EN/ES dictionaries
  - aria-label uses trusted dictionary literal; no set:html needed (Astro auto-escapes)
  - Desktop breakpoint 640px matches codebase standard; dropdown positioned absolute at top:var(--3xl) (64px header height)
metrics:
  duration: "12m"
  completed: "2026-06-15"
  tasks: 2
  files: 2
---

# Phase 08 Plan 03: Mobile Nav Hamburger (F-009) Summary

**One-liner:** CSS-only hamburger toggle (hidden checkbox + :checked sibling selector) exposes Home/Map/Methodology nav at mobile width (<640px) with zero JavaScript and full i18n support.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add nav_menu_open i18n string (EN + ES) | 3a1f67c | site/src/config/i18n.ts |
| 2 | Zero-JS hamburger mobile nav in PageHeader (F-009) | def0269 | site/src/components/PageHeader.astro |

## What Was Built

**Task 1 — i18n string:**
- Added `nav_menu_open: string` to `I18nStrings` interface (after `nav_methodology`)
- `EN_STRINGS.nav_menu_open = 'Open navigation menu'`
- `ES_STRINGS.nav_menu_open = 'Abrir menú de navegación'`

**Task 2 — Hamburger nav:**
- Inserted `<input type="checkbox" id="nav-toggle" class="nav-toggle-input" aria-hidden="true" />` between wordmark and `<nav class="csm-nav">`
- Inserted `<label for="nav-toggle" class="nav-toggle-btn" aria-label={t.nav_menu_open}>` with three `<span class="burger-bar"></span>` elements
- Added CSS: `.nav-toggle-input { display: none }`, `.nav-toggle-btn` shown as 24×18px flex column below 640px, hidden at `@media (min-width: 640px)`
- `.nav-toggle-input:checked ~ .csm-nav` rule: absolute dropdown below header (top: var(--3xl)), background: var(--card), border-bottom, z-index: 99
- `@media (min-width: 640px)` override resets nav to `position:static; flex-direction:row; border-bottom:none; padding:0`
- Zero `client:*` directives — D-09 honored
- Build passes; `nav-toggle-btn` present in `dist/index.html`

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

No new threat surface beyond what was modeled in the plan's threat register (T-08-04, T-08-05). The `aria-label={t.nav_menu_open}` interpolates a static dictionary literal; Astro auto-escapes attribute values. No JS, no user/network input introduced.

## Self-Check: PASSED

- site/src/config/i18n.ts: verified nav_menu_open in interface, EN_STRINGS, ES_STRINGS
- site/src/components/PageHeader.astro: verified nav-toggle-input, nav-toggle-btn, burger-bar, t.nav_menu_open, :checked sibling rule, 640px breakpoint, zero client: directives
- dist/index.html: verified nav-toggle-btn present in built output
- Commits: 3a1f67c (i18n), def0269 (hamburger)
