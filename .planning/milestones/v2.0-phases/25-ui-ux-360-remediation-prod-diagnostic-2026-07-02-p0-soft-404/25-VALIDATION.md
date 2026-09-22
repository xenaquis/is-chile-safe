---
phase: 25
slug: ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-02
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Astro build + 9 custom validators (`site/scripts/validate/all.mjs`); pytest for `pipeline/` |
| **Config file** | `site/package.json` scripts; `pipeline/` pytest discovery |
| **Quick run command** | `cd site && npm run build && npm run validate` (chained — OneDrive requirement) |
| **Full suite command** | `cd site && npm run build && npm run validate && npm run check`; `cd pipeline && python -m pytest -q` |
| **Estimated runtime** | ~120–180 s (build dominates) |

---

## Sampling Rate

- **After every task commit:** grep-level assertion on the touched source file (fast, <1 s)
- **After every plan wave:** `cd site && npm run build && npm run validate` (chained in ONE command — OneDrive desync)
- **Before `/gsd:verify-work`:** Full build+validate+check green; pipeline pytest green; BrowserOS visual pass on preview
- **Max feedback latency:** ~180 s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| P0-1 | TBD | 1 | real 404 | — | no soft-404 index of arbitrary URLs | build-grep | `test -f site/dist/404.html` after chained build | ✅ | ⬜ pending |
| P0-3 | TBD | 1 | favicon | — | N/A | build-grep | `grep -c "rel=\"icon\"" site/dist/index.html` ≥ 1; `ls site/dist/favicon.svg` | ✅ | ⬜ pending |
| P0-2 | TBD | 1 | no tablet overflow | — | N/A | BrowserOS visual | screenshots 375px iframe + ~800px; no horizontal scroll | ✅ | ⬜ pending |
| P1-1 | TBD | 2 | locale numbers | — | N/A | source-grep + visual | `grep -c "es-CL" site/src/components/map/ResultPanel.tsx` = 0; EN panel shows "4,984" | ✅ | ⬜ pending |
| P1-3 | TBD | 2 | map framing/pins/guard | — | unknown ?cut= never fetches | source-grep + visual | grep fitBounds/maxBounds in MapIsland; guard regex on focusCut; purple `.ev-dot` | ✅ | ⬜ pending |
| P1-5 | TBD | 3 | static editorial visuals | — | N/A | build-grep | `grep -c "<table" site/dist/is-santiago-safe/index.html` > 0 (same for is-chile-safe, safest-cities) | ✅ | ⬜ pending |
| P1-6a | TBD | 3 | news semantics | — | N/A | build-grep | `grep -c "<h2" site/dist/news/index.html` > 0; chips present | ✅ | ⬜ pending |
| P1-6b | TBD | 3 | classifier excludes traffic | — | prompt refuses non-crime | pytest | `cd pipeline && python -m pytest -q -k traffic` | ❌ W0 | ⬜ pending |
| P1-2 | TBD | 3 | compare label+URL sync | — | N/A | visual + URL | BrowserOS: select pair → `?a=&b=` in URL; "Composite Crime Index" label + methodology link | ✅ | ⬜ pending |
| P1-4 | TBD | 2 | year badges, no "~" | — | N/A | source-grep + visual | no `~` literal in ResultPanel rate block; year badges render | ✅ | ⬜ pending |
| P2-1 | TBD | 4 | a11y markers/focus/skip | — | N/A | build-grep + visual | `grep "skip-link" site/dist/index.html`; marker title/aria-label present | ✅ | ⬜ pending |
| P2-2 | TBD | 4 | JSON-LD + region links | — | N/A | build-grep | `grep "WebSite" site/dist/index.html`; `grep -c "/region/" site/dist/rankings/index.html` ≥ 16 | ✅ | ⬜ pending |
| P2-3 | TBD | 4 | copy polish | — | never absolute safe/dangerous wording | build-grep | directional label "1 = highest reported" present on region pages; forbidden-language validator green | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pipeline/tests/test_classifier_traffic.py` — traffic-accident exclusion test (may stub LLM: assert prompt contains exclusion rule + filter rejects category)
- [ ] `grep -rn "outline" site/src` sweep — locate the component-scoped `outline:none` override before fixing focus styles

*Everything else: existing infrastructure (build + validators + BrowserOS preview) covers phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tablet 640–1080px no overflow | P0-2 | BrowserOS lacks viewport resize | Full-page screenshot at default width + 375px iframe; check header band integrity |
| Map initial framing | P1-3 | visual judgment | Open /map/ in preview; Chile centered, minimal ocean |
| Legend collapse on mobile | P1-3 | interaction | 375px iframe: legend collapsed by default, expandable |
| Live 404 status code | P0-1 | Cloudflare serves 404.html only in prod | After deploy: `curl -I https://ischilesafe.com/404-test/` → 404 (preview local: astro preview returns 404 for unknown paths with 404.html) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
