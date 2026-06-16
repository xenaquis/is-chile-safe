---
phase: 15
slug: crime-type-seo-ranking-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-16
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
| 15-01-01 | 01 | 1 | CSEO-01 | — | N/A | build | `cd site && npm run build` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | CSEO-02 | — | N/A | validate | `cd site && npm run validate` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Extend `site/scripts/validate/seo.mjs` SAMPLES with a first-subdir heuristic for the `/crime-ranking/` path prefix so ItemList + canonical + OG assertions fire on the new pages
- [ ] Confirm `site/scripts/validate/forbidden-language.mjs` covers the new page bodies (methodology copy)

*Detailed per-task automated commands are finalized by the planner per plan.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reciprocal hreflang resolves in browser | CSEO-01 | Cross-locale link correctness needs a rendered page | Load `/crime-ranking/homicide/`, confirm `<link rel="alternate" hreflang="es">` points to `/es/ranking-delito/...` and vice versa |
| Sober tone / methodology reads accurately | CSEO-02 | Editorial judgment | Read each ranking page; confirm methodology note lists included delitos + cites CEAD + reported-incidence framing |

*Automated guards (forbidden-language.mjs, buildItemList assertSafeName) cover hard violations; the above are judgment checks.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
