---
status: reviewed
phase: 04-editorial-pages-adsense
baseline: 04-UI-SPEC.md
audited: 2026-06-13
overall_score: 19/24
screenshots: none (code-only audit — no dev server)
pillars:
  copywriting: 3/4
  visuals: 3/4
  color: 3/4
  typography: 4/4
  spacing: 4/4
  experience_design: 2/4
---

# Phase 4 — UI Audit Review

Retroactive 6-pillar audit of implemented Phase-4 frontend against the approved `04-UI-SPEC.md`. Code-only (no browser). Phase-4 inherits the Phase-2 design system (D-16) — inherited-token reuse is correct, not a finding.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | CTAs + CEAD attribution compliant; `esPath` self-ref on `/is-santiago-safe/` (intended for unpaired slug); footer-legal link weight 400 vs spec 700 |
| 2. Visuals | 3/4 | 720px prose column, DataCallout border, FAQ dividers all correct; map breakout CSS unverified without browser |
| 3. Color | 3/4 | ContactForm hover hardcoded `#0d6460` instead of token; Reject button missing hover state |
| 4. Typography | 4/4 | Exactly 4 sizes / 2 weights per spec; all roles correct |
| 5. Spacing | 4/4 | Tokens consistent; CLS reserved dims correct; no arbitrary values |
| 6. Experience Design | 2/4 | CookieConsent does not forward consent signal to the ad runtime (Phase-6 activation concern — see note) |

**Overall: 19/24** (advisory — non-blocking)

## Findings Applied (this phase)

- **Footer legal links weight** — `PageFooter.astro .footer-legal a` was `--weight-body` (400); spec requires Label style 700. → set to `--weight-strong`.
- **ContactForm hover token** — `.form-submit:hover` used literal `#0d6460`; replaced with `color-mix(in srgb, var(--primary) 90%, black)` to stay token-derived.
- **CookieConsent Reject hover** — added the spec'd `background: rgba(255,255,255,0.1)` hover state for visual affordance.

## Findings Deferred to Phase 6 (AdSense activation)

- **Consent signal not forwarded to ad runtime** — UI-SPEC specifies `googletag.pubads().setPrivacySettings()` (Google Ad Manager API), but the built loader uses `adsbygoogle` (AdSense). The correct mechanism for AdSense is Google **Consent Mode** (`gtag('consent', ...)`) / non-personalized-ads flag, wired when `ADSENSE_ENABLED` is flipped on in Phase 6. Only executes when ads go live (flag is OFF in Phase 4). Captured as a Phase-6 task — do not wire the wrong (GAM) API now.

## Findings Left As-Is (intended by design)

- **`esPath` self-reference on `/is-santiago-safe/`** — planned behavior for the slug with no EDIT-02 ES pair (slug_flag); passes the project's `hreflang.mjs` validator. Revisit only if an ES Santiago page is added.
- **mailto contact** — locked decision D-14 (static MVP, no backend); email-harvest tradeoff documented in source.

## Registry Safety

No shadcn / no third-party registries (`shadcn_initialized: false`). Not applicable.
