---
phase: 13
slug: ranking-seo-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | In-repo ESM dist-reading validators (`node scripts/validate/*.mjs`) — NOT a unit-test framework |
| **Config file** | none — plain Node ESM scripts |
| **Quick run command** | `cd site && npm run build && node scripts/validate/seo.mjs` (build+validate chained — OneDrive desync guard) |
| **Full suite command** | `cd site && npm run build && node scripts/validate/all.mjs` |
| **Estimated runtime** | ~60-90 seconds (dominated by Astro build) |

---

## Sampling Rate

- **After every task commit:** Run `cd site && npm run build && node scripts/validate/seo.mjs`
- **After every plan wave:** Run `cd site && npm run build && node scripts/validate/all.mjs`
- **Before `/gsd:verify-work`:** Full suite must be green (existing validators + new `seo.mjs`)
- **Max feedback latency:** ~90 seconds

> **OneDrive desync guard:** repo lives inside OneDrive — always chain `npm run build && node scripts/validate/...` in ONE command; `dist/` can vanish between separate processes.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-* | 01 | 1 | RSEO-01 | — | OG/Twitter meta present + locale-correct on sampled pages | dist assertion | `node scripts/validate/seo.mjs` | ❌ W0 (new `seo.mjs`) | ⬜ pending |
| 13-02-* | 02 | 2 | RSEO-02 | — | ItemList shape (position+url+name) on ranking templates | dist assertion | `node scripts/validate/seo.mjs` | ❌ W0 | ⬜ pending |
| 13-02-* | 02 | 2 | RSEO-02 | — | BreadcrumbList shape (position+name+item) on breadcrumb templates | dist assertion | `node scripts/validate/seo.mjs` | ❌ W0 | ⬜ pending |
| 13-03-* | 03 | 2 | RSEO-02 | — | All ld+json blocks JSON.parse cleanly (XSS escaping intact) | dist assertion | `node scripts/validate/seo.mjs` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `site/scripts/validate/seo.mjs` — new validator covering RSEO-01 + RSEO-02 (mirror `spine.mjs` dist-reading ESM pattern)
- [ ] Register `'seo.mjs'` in `site/scripts/validate/all.mjs` VALIDATORS array
- [ ] `site/public/og/*.png` — per-type 1200×630 OG images (placeholder PNGs) must exist before build so `og:image` resolves

*The new `seo.mjs` validator IS the phase's primary test infrastructure — it must exist before any RSEO behavior can be asserted.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| JSON-LD validates against live Google Rich Results / schema.org validator | RSEO-02 | Network call — excluded from ~$0 offline build; offline shape check covers required fields | (optional, post-deploy) Paste a sampled rendered page URL into Google Rich Results Test; confirm ItemList + BreadcrumbList detected with no errors |
| OG/Twitter card visual preview | RSEO-01 | Renders only on external scrapers (Facebook/Twitter/Slack) | (optional, post-deploy) Paste a page URL into a card debugger; confirm 1200×630 image + title/description render |

*Offline `seo.mjs` covers all gating behaviors; manual checks are post-deploy confirmations only.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify (`node scripts/validate/seo.mjs`) or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (`seo.mjs`, `all.mjs` registration, `public/og/`)
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
