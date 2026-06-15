---
phase: 11
slug: publish-346-comunas-finder
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 11 — Validation Strategy

> Per-phase validation contract. This phase is Astro routing/data/SEO — validation is structural-validator + build-assertion based, plus one light manual reachability check.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Repo structural validators (`site/scripts/validate/*.mjs`) + the Astro build itself (page emission). No unit-test runner for static pages. |
| **Config file** | none — standalone Node validators run in CI after build |
| **Quick run command** | `cd site && node scripts/validate/rollout.mjs` (and the new `coverage.mjs`) |
| **Full suite command** | `cd site && npm run build` (emits all pages + runs prebuild sync) then `node scripts/validate/*.mjs` |
| **Estimated runtime** | build ~9–10 min with memoization fix (was ~9.4 min); validators seconds |

## Sampling Rate

- **After every task commit:** run the relevant validator (`rollout.mjs` / `coverage.mjs`) or a scoped `astro build` check.
- **After the rollout flip + table un-gate:** full `npm run build` green + coverage validator.
- **Before `/gsd:verify-work`:** full build green, all validators pass, manual directory reachability check in both locales.
- **Max feedback latency:** validators ~seconds; full build ~10 min (the gating cost — memoization keeps it under the 20-min CI limit).

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-0x | 0x | 0 | COMU-01 | perf/build | `cd site && npm run build` completes < 20 min (memoization) | ❌ new (data.ts memo) | ⬜ pending |
| 11-0x | 0x | 1 | COMU-01 | structural | build emits ~346 `/commune/*` + ~346 `/es/comuna/*` pages | ✅ extend rollout.mjs (`=== 12` → 346 / EXPECT_ALL) | ⬜ pending |
| 11-0x | 0x | 1 | COMU-03 | structural | region + crime ranking tables link every comuna; no "Showing N of M" gating string in dist | ✅ new coverage.mjs | ⬜ pending |
| 11-0x | 0x | 2 | COMU-02 | structural | `/communes/` + `/es/comunas/` emitted; full 346-link list in server HTML (crawlable); nav + home link present | ✅ new coverage.mjs | ⬜ pending |
| 11-0x | 0x | 3 | COMU-01/03 | structural | sitemap includes 346×2 comuna URLs + directory; ZERO internal links to ungenerated comuna slugs | ✅ new coverage.mjs | ⬜ pending |
| 11-0x | 0x | 2 | COMU-02 | a11y/no-JS | directory search/filter degrades gracefully (full list visible without JS) | ⚠ manual + grep | ⬜ pending |

*Task IDs finalize when PLAN.md numbers are assigned.*

## Wave 0 Requirements

- [ ] `site/src/lib/data.ts` — add build-time memoization (index + per-comuna/region loads) so 692 comuna pages don't re-read ~700–1000 JSON files each. **Highest-leverage task; without it the build risks the 20-min CI timeout.**
- [ ] `site/scripts/validate/coverage.mjs` (new) — assert comuna page count ≈ 346/locale, sitemap coverage, and zero internal links to ungenerated comuna slugs (inverse of today's orphan bug).
- [ ] Update `rollout.mjs` `=== 12` assertion to the all-346 / EXPECT_ALL expectation.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Any comuna reachable ≤2 interactions | COMU-02 | Reachability is a UX judgment | In both locales, open `/communes/` (and `/es/comunas/`), search a deep small comuna + browse a region, click through to its page — confirm ≤2 interactions and the page renders |
| Map/ranking click no longer dead-ends | COMU-01 | Cross-surface flow | Click a previously-orphaned comuna polygon on the map and a non-rollout row in a region table — both reach a real page, no 404 |

## Validation Sign-Off

- [ ] Build completes under the 20-min CI limit (memoization in place)
- [ ] rollout/coverage validators assert 346/locale + sitemap + zero orphan links
- [ ] Wave 0 (memoization + coverage validator) lands before the rollout flip
- [ ] No watch-mode flags
- [ ] `nyquist_compliant: true` set after Wave 0 assertions exist

**Approval:** pending
