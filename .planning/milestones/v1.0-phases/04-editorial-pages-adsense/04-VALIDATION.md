---
phase: 4
slug: editorial-pages-adsense
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 04-RESEARCH.md "## Validation Architecture".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node.js custom `dist/` scanners (`scripts/validate/*.mjs`) — no Jest/Vitest/pytest for frontend |
| **Config file** | none — validators run via `node scripts/validate/all.mjs` |
| **Quick run command** | `node scripts/validate/forbidden-language.mjs` (visible-text scan only — fast) |
| **Full suite command** | `npm run build && node scripts/validate/all.mjs` (chained — OneDrive desync guard) |
| **Estimated runtime** | ~30–60s full (build dominates); quick validator ~1–2s |

---

## Sampling Rate

- **After every task commit:** Run `node scripts/validate/forbidden-language.mjs`
- **After every plan wave:** Run `npm run build && node scripts/validate/all.mjs` (all 9 validators)
- **Before `/gsd:verify-work`:** Full suite green + human spot-check of 3 editorial pages (prose quality, data accuracy)
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-?-? | forbidden-lang | 1 | EDIT-05 | — | Build fails non-zero naming page+term on prohibited language; passes on qualifying phrases | unit | `node scripts/validate/forbidden-language.mjs` | ❌ W0 | ⬜ pending |
| 4-?-? | adslot | 2 | MON-01 | T-AdSense | AdSlot placeholder present, NO `<ins class="adsbygoogle">`, NO `pagead2.googlesyndication` when ADSENSE_ENABLED=false | smoke | `grep -r "adsbygoogle\|pagead2.googlesyndication" dist/` (must be empty) | ❌ W0 | ⬜ pending |
| 4-?-? | editorial-en | 2 | EDIT-01 | — | 10 EN editorial pages render with title/canonical/hreflang | smoke | `node scripts/validate/forbidden-language.mjs` + `node scripts/validate/hreflang.mjs` + structure.mjs | ✅/❌ | ⬜ pending |
| 4-?-? | editorial-es | 3 | EDIT-02 | — | 10 ES editorial pages render; reciprocal hreflang | smoke | `node scripts/validate/hreflang.mjs` | ✅ | ⬜ pending |
| 4-?-? | methodology | 3 | EDIT-03 | — | Methodology page has required H2 sections (CEAD sources, rate calc, subregistro, comparison) | manual | Human inspection of `dist/methodology/index.html` | n/a | ⬜ pending |
| 4-?-? | legal | 3 | EDIT-04 | V8 | privacy/terms/about/contact exist + linked from footer | smoke | `structure.mjs` REQUIRED_FILES + `hreflang.mjs` | ❌ W0 | ⬜ pending |
| 4-?-? | adslot-exclusion | 3 | MON-01 | — | No AdSlot on legal/map pages | smoke | `grep "ad-slot" dist/privacy-policy/index.html` (empty) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Plan/Task IDs finalized by planner.*

---

## Wave 0 Requirements

- [ ] `site/scripts/validate/forbidden-language.mjs` — primary new validator for EDIT-05 (NFD accent-insensitive, `<script>`/`<style>` stripping, `(?<![a-z0-9])...(?![a-z0-9])` boundary, extensible term list, qualifying-phrase allow-list). Build FIRST (Wave 1) before editorial content.
- [ ] `structure.mjs` additions — assert legal page files exist (Wave 3) + all 10 EN editorial slugs exist in `dist/` (Wave 2 completion).
- [ ] Register `forbidden-language.mjs` as validator #9 in `all.mjs` (update "8 validators" header comment).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Methodology page substantive content (CEAD sources, rate-per-100k calc, subregistro/cifra negra caveat, comparison criteria, trend formula) | EDIT-03 | Topic-aware prose quality not feasible to assert automatically | Open `dist/methodology/index.html`, confirm each required H2 section present and accurate |
| Editorial prose authority + data-callout accuracy (3-page spot-check) | EDIT-01/02 | Editorial sobriety + sourced-claim accuracy are judgement calls | Spot-check 3 hero pages: rate/ranking/trend callouts match `data/cead/`, sober language |
| Cookie consent gates AdSense personalization load | MON-01/D-11 | Requires browser interaction (consent accept/reject → script load) | Manual: load page, reject → no pagead script; accept → script loads (only when ADSENSE_ENABLED=true) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (forbidden-language.mjs, structure.mjs additions)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
