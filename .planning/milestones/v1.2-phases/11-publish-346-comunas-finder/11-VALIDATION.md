---
phase: 11
slug: publish-346-comunas-finder
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-15
validated: 2026-06-15
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
| 11-01 | 01 | 0 | COMU-01 | perf/build | `cd site && npm run build` completes < 20 min (memoization) — ~90s actual | ✅ data.ts caches (`_indexCache`/`_communeCache`/`_natAvg`/`_regAvg`) | ✅ COVERED |
| 11-01 | 01 | 1 | COMU-01 | structural | build emits 346 `/commune/*` + 346 `/es/comuna/*` pages | ✅ rollout.mjs (expectedCount = index.json length; `=== 12` removed) | ✅ COVERED |
| 11-01/04 | 01/04 | 1 | COMU-03 | structural | ranking tables link every comuna; ZERO "Showing N of M" / "Mostrando N de M" gating string in dist | ✅ coverage.mjs [B] no-orphan-link + [E] no-gating-string | ✅ COVERED |
| 11-03/04 | 03/04 | 2 | COMU-02 | structural | `/communes/` + `/es/comunas/` emitted; full 346-link list in server HTML (crawlable); nav + home link present | ✅ coverage.mjs [D] directory-completeness | ✅ COVERED |
| 11-04 | 04 | 3 | COMU-01/03 | structural | sitemap includes 346×2 comuna URLs + directory; ZERO internal links to ungenerated comuna slugs | ✅ coverage.mjs [A] route-count + [B] no-orphan-link + [C] sitemap-coverage | ✅ COVERED |
| 11-03 | 03 | 2 | COMU-02 | a11y/no-JS | directory full list visible without JS (server-rendered links) | ✅ coverage.mjs [D] (346 SSR hrefs) + manual no-JS spot-check | ✅ COVERED |

*All assertions live in `site/scripts/validate/{rollout,coverage}.mjs`, wired into `all.mjs`; full suite 10/10 PASS (11-04-SUMMARY).*

## Wave 0 Requirements

- [x] `site/src/lib/data.ts` — build-time memoization (`_indexCache`/`_communeCache`/`_natAvg`/`_regAvg`) landed; build ~90s, well under the 20-min CI timeout.
- [x] `site/scripts/validate/coverage.mjs` — asserts comuna page count = 346/locale [A], sitemap coverage [C], zero orphan links [B], directory completeness [D], and zero gating strings [E]. Wired into all.mjs.
- [x] `rollout.mjs` `=== 12` assertion removed — expectedCount now derived from index.json length (346).

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Any comuna reachable ≤2 interactions | COMU-02 | Reachability is a UX judgment | In both locales, open `/communes/` (and `/es/comunas/`), search a deep small comuna + browse a region, click through to its page — confirm ≤2 interactions and the page renders |
| Map/ranking click no longer dead-ends | COMU-01 | Cross-surface flow | Click a previously-orphaned comuna polygon on the map and a non-rollout row in a region table — both reach a real page, no 404 |

## Validation Sign-Off

- [x] Build completes under the 20-min CI limit (memoization in place; ~90s actual)
- [x] rollout/coverage validators assert 346/locale + sitemap + zero orphan links + zero gating strings
- [x] Wave 0 (memoization + coverage validator) landed before the rollout flip
- [x] No watch-mode flags
- [x] `nyquist_compliant: true` set after Wave 0 assertions exist

**Approval:** validated 2026-06-15

## Validation Audit 2026-06-15

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

Gap: COMU-03 sub-assertion "no `Showing N of M` / `Mostrando N de M` gating string in dist" was manual-only. Resolved by adding assertion `[E] no-gating-string` to `coverage.mjs` (scans all 772 dist HTML files; 0 occurrences; exits 1 on regression). Coverage validator now PASS [A]–[E]; full suite 10/10.
