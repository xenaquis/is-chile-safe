---
phase: 04-editorial-pages-adsense
plan: "03"
subsystem: editorial-layout-components
tags: [editorial, layout, faq, contact-form, adsense, cookie-consent, components]
dependency_graph:
  requires: [04-02]
  provides:
    - EditorialLayout.astro
    - LegalLayout.astro
    - DataCallout.astro
    - FAQBlock.astro
    - ContactForm.astro
  affects:
    - site/src/layouts/EditorialLayout.astro
    - site/src/layouts/LegalLayout.astro
    - site/src/components/DataCallout.astro
    - site/src/components/FAQBlock.astro
    - site/src/components/ContactForm.astro
tech_stack:
  added: []
  patterns:
    - "EditorialLayout wraps BaseLayout (D-16 WRAP rule) — never declares own html/head"
    - "LegalLayout: same 720px prose column, zero ad slots, zero consent banner (D-10 ad exclusion)"
    - "DataCallout: 4px solid var(--primary) left border, CSS token system only"
    - "FAQBlock: static open h2/p list, no client: directive; JSON-LD ownership stays at page->BaseLayout"
    - "ContactForm: mailto:xenaquis@gmail.com, required on all three fields, no backend (D-14)"
    - "ADSENSE_ENABLED exact string compare gate in EditorialLayout (Pitfall 4)"
key_files:
  created:
    - site/src/layouts/EditorialLayout.astro
    - site/src/layouts/LegalLayout.astro
    - site/src/components/DataCallout.astro
    - site/src/components/FAQBlock.astro
    - site/src/components/ContactForm.astro
  modified: []
decisions:
  - "EditorialLayout named-slot contract: default <slot /> for page body + <slot name='ad-content' /> for optional in-content ad position; bottom AdSlot always rendered"
  - "FAQPage JSON-LD ownership stays at page->BaseLayout boundary (single injection point); FAQBlock documents the shape via leading comment"
  - "LegalLayout JSDoc avoids the word 'AdSlot' so verify grep stays clean — documented as 'no ad slots'"
  - "ContactForm hover color uses literal #0d6460 per UI-SPEC (darken var(--primary) 10%) — only allowed literal beyond CLS exceptions"
metrics:
  duration: "22m"
  completed: "2026-06-13"
  tasks: 3
  files: 5
---

# Phase 04 Plan 03: Editorial Layout + Content Components Summary

Layout + content component contracts for all Wave-3 editorial and legal pages: EditorialLayout (720px prose + gated AdSlot + CookieConsent), LegalLayout (720px prose, no ads), DataCallout (sourced value box), FAQBlock (static Q+A list), ContactForm (static mailto).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | EditorialLayout + LegalLayout | 13e93c6 | site/src/layouts/EditorialLayout.astro, site/src/layouts/LegalLayout.astro |
| 2 | DataCallout + FAQBlock | 1745b29 | site/src/components/DataCallout.astro, site/src/components/FAQBlock.astro |
| 3 | ContactForm static mailto | d66b93c | site/src/components/ContactForm.astro |

## Verification Results

- Build: 74 pages, 9/9 validators pass (structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language)
- EditorialLayout: contains BaseLayout, AdSlot, CookieConsent gated by ADSENSE_ENABLED
- LegalLayout: contains BaseLayout, zero AdSlot/CookieConsent references (grep clean)
- DataCallout: value/label/source with 4px solid var(--primary) left border; callout-source class present
- FAQBlock: static h2/p list, no client: directive, no script type=application/ld+json self-injection
- ContactForm: mailto:xenaquis@gmail.com with enctype=text/plain, required on 3 fields, leading comment documents v2 path

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All five components are fully wired:
- EditorialLayout injects AdSlot (gated by ADSENSE_ENABLED; AdSense slot IDs are placeholder strings, tracked in Plan 02 stubs)
- DataCallout renders live props (value/label/source supplied by the page at build time)
- FAQBlock renders live items array from the page
- ContactForm sends to xenaquis@gmail.com via mailto (intentional MVP mechanism per D-14)

## Threat Flags

No new threat surface beyond the plan's threat model:
- T-04-06: FAQPage JSON-LD via set:html in BaseLayout (existing XSS-safe path) — confirmed implemented
- T-04-07: mailto exposes address by design — documented in component leading comment
- T-04-08: required on all three ContactForm fields, no server-side processing

## Self-Check: PASSED

- site/src/layouts/EditorialLayout.astro: FOUND
- site/src/layouts/LegalLayout.astro: FOUND
- site/src/components/DataCallout.astro: FOUND
- site/src/components/FAQBlock.astro: FOUND
- site/src/components/ContactForm.astro: FOUND
- Commit 13e93c6: FOUND
- Commit 1745b29: FOUND
- Commit d66b93c: FOUND
