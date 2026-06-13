---
phase: 04-editorial-pages-adsense
plan: "02"
subsystem: monetization-scaffold
tags: [adsense, cookie-consent, footer, i18n, env-gate]
dependency_graph:
  requires: [04-01]
  provides: [AdSlot.astro, CookieConsent.astro, BaseLayout-AdSense-loader, i18n-footer-strings, PageFooter-legal-links]
  affects: [site/src/layouts/BaseLayout.astro, site/src/components/PageFooter.astro]
tech_stack:
  added: []
  patterns:
    - "Exact string compare env gate: import.meta.env.ADSENSE_ENABLED === 'true' (Pitfall 4)"
    - "Single async AdSense loader in BaseLayout head — not per-component (D-12)"
    - "CookieConsent: vanilla <script> localStorage gate; no client:* directive"
    - "Footer second nav row below existing flex row — do not alter first row"
key_files:
  created:
    - site/src/components/AdSlot.astro
    - site/src/components/CookieConsent.astro
  modified:
    - site/src/layouts/BaseLayout.astro
    - site/src/config/i18n.ts
    - site/src/components/PageFooter.astro
decisions:
  - "ADSENSE_ENABLED (no PUBLIC_ prefix) is build-time-only; PUBLIC_ADSENSE_PUBLISHER_ID is client-accessible per Astro convention"
  - "CookieConsent is NOT injected in BaseLayout — EditorialLayout (Plan 03) injects it only when enabled"
  - "AdSlot height literals 90px/50px are intentional exceptions to CSS token rule (CLS-critical per UI-SPEC)"
metrics:
  duration: "18m"
  completed: "2026-06-13"
  tasks: 3
  files: 5
---

# Phase 04 Plan 02: AdSense Subsystem + Footer Legal Links Summary

AdSense monetization scaffold (MON-01) fully env-gated OFF with CLS-safe placeholder slots, cookie consent banner, gated BaseLayout loader, i18n footer/cookie strings, and four legal page links in footer per locale (EDIT-04).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | AdSlot.astro — CLS-safe env-gated slot | 40c5bd8 | site/src/components/AdSlot.astro |
| 2 | CookieConsent.astro + BaseLayout gated loader | 5f890df | site/src/components/CookieConsent.astro, site/src/layouts/BaseLayout.astro |
| 3 | i18n.ts extension + PageFooter legal links | 0c24618 | site/src/config/i18n.ts, site/src/components/PageFooter.astro |

## Verification Results

- Build: 74 pages, 9/9 validators pass
- AdSense gate: zero `pagead2.googlesyndication` / `adsbygoogle` occurrences in 74 pages with ADSENSE_ENABLED unset
- Footer legal links: EN `/privacy-policy/` `/terms/` `/about/` `/contact/` confirmed in dist/index.html
- Footer legal links: ES `/es/politica-privacidad/` `/es/terminos/` `/es/acerca-de/` `/es/contacto/` confirmed in dist/es/index.html
- forbidden-language validator: 0 forbidden terms in new footer/cookie copy (sober editorial tone)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

- AdSlot `data-ad-slot` attribute uses placeholder string literals `CONTENT_SLOT_ID` / `BOTTOM_SLOT_ID` — intentional Phase 4 stubs. Real AdSense slot IDs are assigned in Phase 6 when AdSense account is approved and `ADSENSE_ENABLED=true` is set.
- CookieConsent component exists but is not injected on any page yet — EditorialLayout (Plan 03) handles injection conditioned on ADSENSE_ENABLED. Phase 4 default: consent banner does not appear.

## Threat Flags

No new threat surface beyond what the plan's threat model covers (T-04-03, T-04-04, T-04-05 all documented and dispositioned).

## Self-Check: PASSED

- site/src/components/AdSlot.astro: FOUND
- site/src/components/CookieConsent.astro: FOUND
- site/src/layouts/BaseLayout.astro (modified): FOUND
- site/src/config/i18n.ts (modified): FOUND
- site/src/components/PageFooter.astro (modified): FOUND
- Commit 40c5bd8: FOUND
- Commit 5f890df: FOUND
- Commit 0c24618: FOUND
