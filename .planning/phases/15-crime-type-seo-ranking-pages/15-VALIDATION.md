---
phase: 15
slug: crime-type-seo-ranking-pages
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-16
validated: 2026-06-16
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | astro build + node validators under `site/scripts/validate/` (run via `npm run validate` → `all.mjs`, 13 validators incl. seo + forbidden-language + map) |
| **Config file** | site/package.json scripts |
| **Quick run command** | `cd site && npm run build` (= `cross-env ROLLOUT_ALL=true astro build`; chained — see OneDrive desync note) |
| **Full suite command** | `cd site && npm run build && npm run validate` |
| **Estimated runtime** | ~60-120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run build` (repo lives in OneDrive — keep build+validate chained so dist/ doesn't desync across separate processes)
- **After every plan wave:** Run full suite (`npm run build && npm run validate`)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | CSEO-02 | T-15-01 | editorial-guard via seo.mjs sampling | node assertion | `cd site && node -e "<seo.mjs crime-ranking/ranking-delito + firstCrimeRanking* guard check>"` | ✅ | ✅ green |
| 15-01-02 | 01 | 1 | CSEO-02 | T-15-01 | forbidden-language clean methodology copy | tsc + node import | `cd site && npx tsc --noEmit && node --input-type=module -e "<RANKING_METHODOLOGY_EN/ES 8-key + CEAD-cite check>"` | ✅ | ✅ green |
| 15-02-01 | 02 | 2 | CSEO-01, CSEO-02 | T-15-03, T-15-04 | assertSafeName + non-uniform homicide rates | build + node | `cd site && npm run build && node -e "<homicide EN page + ItemList + single-H1 + property page check>"` | ✅ | ✅ green |
| 15-02-02 | 02 | 2 | CSEO-01, CSEO-02 | T-15-03, T-15-04 | assertSafeName + ES comuna links | build + node | `cd site && npm run build && node -e "<ES homicidios page + ItemList + 1×H1 + /es/comuna/ + robos-violentos check>"` | ✅ | ✅ green |
| 15-02-03 | 02 | 2 | CSEO-01 | T-15-03, T-15-05 | reciprocal-link + full 13-validator gate | build + validate + node | `cd site && npm run build && npm run validate && node -e "<EN+ES comuna homicide-ranking spoke check>"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Extend `site/scripts/validate/seo.mjs` SAMPLES with a first-subdir heuristic for the `/crime-ranking/` path prefix so ItemList + canonical + OG assertions fire on the new pages — *landed in 15-01-01 (commit 20f08ef); 6 crime-ranking/firstCrimeRanking refs present, guarded so pre-Phase-15 builds skip*
- [x] Confirm `site/scripts/validate/forbidden-language.mjs` covers the new page bodies (methodology copy) — *forbidden-language.mjs scans all dist/ HTML in the 15-02-03 full-suite gate; PASS on rendered methodology + H1 prose*

*Detailed per-task automated commands are finalized by the planner per plan.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reciprocal hreflang resolves in browser | CSEO-01 | Cross-locale link correctness needs a rendered page | Load `/crime-ranking/homicide/`, confirm `<link rel="alternate" hreflang="es">` points to `/es/ranking-delito/homicidios/` and vice versa |
| Sober tone / methodology reads accurately | CSEO-02 | Editorial judgment | Read each ranking page; confirm methodology note lists included delitos + cites CEAD + reported-incidence framing |

*Automated guards (forbidden-language.mjs, buildItemList assertSafeName) cover hard violations; the above are judgment checks. hreflang.mjs already asserts reciprocity structurally; the manual check confirms it resolves in a real browser.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-06-16 — all 5 tasks COVERED by automated verify; 0 gaps; 2 documented manual judgment checks.

---

## Validation Audit 2026-06-16

| Metric | Count |
|--------|-------|
| Tasks audited | 5 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Reconciliation note:** The pre-execution draft listed only the 2 Wave-0 tasks (15-01-01/02) as `pending`/`red`. This audit reconciled the map against both executed SUMMARYs — added Plan 02's 3 tasks, marked all 5 green (validator suite reports 12/12 PASS; 790 pages built), checked the Wave 0 boxes (seo.mjs sampling + forbidden-language coverage both landed), and set `nyquist_compliant: true`. No test files generated — the requirement guards (build + 13-validator suite) already exist and run green; this phase's "tests" are the validators, not a separate spec framework.
