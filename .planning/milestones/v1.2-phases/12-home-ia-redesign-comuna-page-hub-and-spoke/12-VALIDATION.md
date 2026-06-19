---
phase: 12
slug: home-ia-redesign-comuna-page-hub-and-spoke
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-15
updated: 2026-06-15
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node.js validator scripts (`site/scripts/validate/*.mjs`) + Astro build + `astro check` |
| **Config file** | `site/scripts/validate/all.mjs` (orchestrates the suite) |
| **Quick run command** | `cd site && npm run check` (types) or `node scripts/validate/<one>.mjs` |
| **Full suite command** | `cd site && npm run build && npm run validate` (chained — OneDrive dist/ desync gotcha) |
| **Estimated runtime** | build ~3–6 min (346×2) + validators ~30–60s |

---

## Sampling Rate

- **After every task commit:** `cd site && npm run check` (fast) and/or the task's own `<automated>` build/validator command.
- **After every plan wave:** `cd site && npm run build && npm run validate` (full suite, chained in one command).
- **Before `/gsd:verify-work`:** Full suite green + the 12-06 human map-focus smoke check.
- **Max feedback latency:** ~60s for validators; build is the long pole.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | IA-02 | — | N/A (pure data helper) | type/build | `cd site && npm run check` | ✅ | ⬜ pending |
| 12-01-02 | 01 | 1 | IA-03 | — | N/A (i18n strings) | type | `cd site && npm run check` | ✅ | ⬜ pending |
| 12-01-03 | 01 | 1 | IA-02/03 | T-12-01 | ?q= → input.value only, never innerHTML | build/source | `cd site && npm run build` + grep URLSearchParams in dist | ✅ | ⬜ pending |
| 12-02-01 | 02 | 1 | IA-02 | T-12-02 | ?cut= opaque string → Map lookup only | type/build | `cd site && npm run check && npm run build` | ✅ | ⬜ pending |
| 12-03-01 | 03 | 2 | IA-01 | — | N/A | type | `cd site && npm run check` | ✅ | ⬜ pending |
| 12-03-02 | 03 | 2 | IA-01 | T-12-03 | home never echoes ?q= (no JS) | build/structure | `npm run build && node scripts/validate/structure.mjs` | ✅ | ⬜ pending |
| 12-03-03 | 03 | 2 | IA-01 | — | hreflang reciprocity | build/hreflang | `npm run build && node scripts/validate/hreflang.mjs` | ✅ | ⬜ pending |
| 12-04-01 | 04 | 2 | IA-02 | — | N/A | build | `cd site && npm run build` | ✅ | ⬜ pending |
| 12-04-02 | 04 | 2 | IA-02 | T-12-04 | static build-time hrefs only | build/commune | `npm run build && node scripts/validate/commune.mjs` | ✅ | ⬜ pending |
| 12-04-03 | 04 | 2 | IA-02 | T-12-04 | ES slugs hardcoded; hreflang | build/commune/hreflang | `npm run build && node scripts/validate/commune.mjs && node scripts/validate/hreflang.mjs` | ✅ | ⬜ pending |
| 12-05-01 | 05 | 2 | IA-03 | T-12-05 | static hrefs | build | `cd site && npm run build` (grep nav href) | ✅ | ⬜ pending |
| 12-05-02 | 05 | 2 | IA-03 | T-12-05 | static hrefs | build | `cd site && npm run build` (grep footer-spine) | ✅ | ⬜ pending |
| 12-05-03 | 05 | 2 | IA-03 | — | hreflang reciprocity | build/hreflang | `npm run build && node scripts/validate/hreflang.mjs` | ✅ | ⬜ pending |
| 12-06-01 | 06 | 3 | IA-01/02/03 | T-12-06 | reads dist/ only | build/spine | `npm run build && node scripts/validate/spine.mjs` | ❌ Wave 0 new (spine.mjs) | ⬜ pending |
| 12-06-02 | 06 | 3 | IA-01/02/03 | — | full suite | build/all | `cd site && npm run build && npm run validate` | ✅ | ⬜ pending |
| 12-06-03 | 06 | 3 | IA-02 | — | map focus param | manual/e2e | `npm run dev` + visit /map/?cut=13101 | manual only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `site/scripts/validate/spine.mjs` — NEW validator (assertions F–L: map-spoke targets, /rankings/ in dist + sitemap, breadcrumb reciprocity, map-spoke present on ficha, home single-H1, rankings nav site-wide). Authored in plan 12-06.
- [ ] No test framework install needed — Node validators + Astro build are the existing infrastructure.
- [ ] `nearestComparables(cut, n)` + `?q=` finder read + `?cut=` map read are themselves Wave-1 prerequisites (plans 12-01/12-02) that downstream pages depend on.

*Existing infrastructure (Astro build + 10 validators) covers most assertions; spine.mjs fills the new cross-link gap.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `/map/?cut=<cut>` flies to + selects the commune | IA-02 / D-08 | Leaflet flyToBounds + highlight are client runtime behaviors not observable in static dist HTML | `cd site && npm run dev`, visit `/map/?cut=13101` → Santiago focused; `/map/` unchanged; `/map/?cut=zzz` no crash |
| Hybrid C+B above-the-fold reads correctly | IA-01 | Visual layout fidelity vs spike 001-c | Visit `/` and `/es/`; confirm search hero + two lead tables + map CTA + guide cards above fold, condensed prose below |
| Ficha hub spokes navigate correctly | IA-02 | Click-through behavior | Visit `/commune/santiago/`; click map-spoke → focused map; confirm similar-comunas + crime-type + breadcrumb |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies — YES (15/15 mapped; 1 spine.mjs Wave-0 new)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify — YES
- [ ] Wave 0 covers all MISSING references — YES (spine.mjs is the only MISSING; authored in 12-06)
- [ ] No watch-mode flags — YES
- [ ] Feedback latency < 60s for validators — YES
- [ ] `nyquist_compliant: true` set in frontmatter — YES

**Approval:** pending
