---
phase: 9
slug: ux-readability-accessibility-polish
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-15
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> This is a CSS / Astro / React source-edit + manual-verify phase. There is NO
> JS unit-test runner in `site/` — the deterministic signal is a clean Astro
> production build plus targeted `grep` assertions on source and built HTML;
> the inherently visual / keyboard a11y items are covered by one consolidated
> human-verify checkpoint (Plan 05 Task 2).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Astro production build (`npm run build`) + `grep` source/HTML assertions + manual axe / keyboard browser checkpoint |
| **Config file** | `site/astro.config.mjs` (build), `site/package.json` (scripts); no JS unit-test config exists |
| **Quick run command** | `cd "C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe" && cd site && npm run build` |
| **Full suite command** | `cd "C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe" && cd site && npm run build && ls dist/glossary/index.html dist/es/glosario/index.html` (then manual axe + tab-key walk via `npm run preview`) |
| **Estimated runtime** | ~30–60 seconds (build); manual checkpoint adds a few minutes |

> **OneDrive desync guard (memory: onedrive-build-artifacts-desync):** the repo
> lives inside OneDrive; `dist/` can vanish between separate processes. ALWAYS
> chain the build and any `dist/` check into ONE command (the `&&` chains above).

---

## Sampling Rate

- **After every task commit:** Run the quick run command (`npm run build`).
- **After every plan wave:** Run the full suite command (build + dist route check).
- **Before `/gsd:verify-work`:** Full suite must be green and the Plan 05 human-verify checkpoint approved.
- **Max feedback latency:** ~60 seconds (single build).

---

## Per-Task Verification Map

Per-requirement rows for all 7 phase requirements (mirrors 09-RESEARCH
§"Phase Requirements → Test Map"). Threat refs from each plan's `<threat_model>`.

| Req ID | Plan | Wave | Threat Ref | Expected Behavior | Test Type | Automated Command | File Exists | Status |
|--------|------|------|------------|-------------------|-----------|-------------------|-------------|--------|
| UX-01 | 04 (+05 scan) | 2/3 | T-09-08 | Exactly one `<h1>`; scannable H2/H3; purpose clear in ~5s | smoke + manual | `cd site && npm run build` + `grep -c "<h1" site/src/pages/is-santiago-safe.astro` == 1 | ✅ existing infra | ⬜ pending |
| UX-02 | 02/03/04 | 2 | T-09-04/06/08 | DataCallout/StatCard = one idea + CEAD source; no callout↔prose stat duplication | smoke + manual | `cd site && npm run build`; manual spot-check (Plan 05 Task 2) on is-santiago-safe / is-chile-safe / safest-cities | ✅ existing infra | ⬜ pending |
| READ-01 | 01 | 1 | T-09-01 | 720px prose column + paragraph rhythm (`.editorial-prose p` margin) | smoke | `cd site && npm run build` + `grep -c ".editorial-prose p" site/src/styles/global.css` ≥ 1 | ✅ existing infra | ⬜ pending |
| READ-02 | 04 | 2 | T-09-08 | ES methodology at content parity with EN (6 sections, ≥11,000 bytes) | smoke + manual | `cd site && npm run build` + `wc -c site/src/pages/es/metodologia.astro` ≥ 11000; manual side-by-side depth check (Plan 05) | ✅ existing infra | ⬜ pending |
| READ-03 | 03/04 (+05 grep) | 2/3 | T-09-06/08 | Sober tone site-wide; no absolute peligroso/seguro/dangerous/safe; CEAD+year attribution | smoke | `grep -rin --include=*.astro "es peligroso\|is dangerous\|muy seguro\|totalmente seguro" site/src/pages/` returns no absolute-verdict line | ✅ existing infra | ⬜ pending |
| A11Y-01 | 01/02 (+05 manual) | 1/2/3 | T-09-01/02/04 | Visible :focus-visible rings; alt text; aria on map controls (year `<select>`, crime chips); WCAG-AA contrast | smoke + manual axe | `grep -c ":focus-visible" site/src/styles/global.css` ≥ 1; manual: tab-walk + axe on /map/, /glossary/, /is-santiago-safe/ + map-control aria assertion (Plan 05 Task 2) | ✅ existing infra | ⬜ pending |
| A11Y-02 | 03 (+05 meta grep) | 2/3 | T-09-06 | Valid `<title>`, meta description, canonical, hreflang on new pages; FAQPage JSON-LD present on a FAQ money page | smoke | build emits `dist/glossary/index.html` + `dist/es/glosario/index.html`; grep built HTML for `<title`,`name="description"`,`rel="canonical"`,`hreflang`; grep `dist/is-santiago-safe/index.html` for `"@type":"FAQPage"` (Plan 05 Task 1) | ✅ existing infra | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Status rows flip to ✅ during execution (automated rows at each plan commit; manual rows at Plan 05 Task 2 checkpoint).*

---

## Wave 0 Requirements

**Existing infrastructure covers all phase requirements (no Wave 0 test files).**

This is a CSS / Astro / React + manual-verify phase. No JS unit-test runner is
installed in `site/`, and none is warranted: the deterministic signal is the
Astro production build (type-checks i18n locale objects against `I18nStrings`,
emits all routes, fails on template errors) plus `grep` assertions on source and
built HTML. There are no `MISSING` automated references and therefore no Wave 0
test scaffolding gaps.

- [x] No new test files required — Astro build + grep is the automated layer.
- [x] No framework install needed — `npm run build` already runs in CI.
- [x] OneDrive build+check chained in one command (dist desync guard).

---

## Manual-Only Verifications

These behaviors are inherently visual / keyboard / browser-rendered and cannot
be asserted by a build or grep. All are gated behind Plan 05 Task 2 (one
consolidated blocking human-verify checkpoint).

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visible focus rings on every interactive element | A11Y-01 | Rendered outline only observable in a browser via Tab | Tab through `/map/`; confirm teal outline on search, year select, crime chips, legend, panel close, "?" trigger |
| Map-control aria (year `<select>`, crime-type chips) | A11Y-01 | aria-label / `<label>` association is a runtime-accessibility-tree fact | In `/map/` inspect the year select + crime chips; confirm each has an `aria-label` or associated `<label>` (axe surfaces missing names) |
| Tooltip keyboard + touch operation, no clipping | A11Y-01 / D-01 | `<details>` open/close + clipping only verifiable interactively | Tab to a "?" trigger, Enter/Space opens, Escape/Enter closes; confirm CEAD cited and not clipped (panel + ranking table) |
| WCAG-AA contrast (axe scan) | A11Y-01 | Computed contrast across rendered DOM | Run axe on `/map/`, `/glossary/`, `/is-santiago-safe/`; #0f766e on #f5f8f8 = 4.71:1 must still pass; no new violations |
| Legend numeric bands render + update on year change | D-03 (UX-02) | Client-island render observable only in browser | `/map/`: 5 bands each with numeric range + qualitative label + per-100k note; change year → ranges update; `/es/mapa/` shows ES labels |
| Multiplier + comparison bar neutral framing | D-04 (UX-02) | Island render + wording check | Santiago panel: "X× the national average" + bar; never safe/dangerous |
| FAQPage JSON-LD present on a FAQ money page | A11Y-02 | Built HTML assertion (automatable) + visual confirm | `grep "\"@type\":\"FAQPage\"" dist/is-santiago-safe/index.html` ≥ 1 (Plan 05 Task 1 automates; checkpoint confirms) |
| Callout↔prose redundancy removed (3 editorial pages) | UX-02 | Semantic duplication judgement, not greppable | Spot-check is-santiago-safe / is-chile-safe / safest-cities: no statistic stated both in a DataCallout and verbatim in adjacent prose |
| ES/EN methodology depth parity | READ-02 | Editorial-quality judgement beyond byte count | Open `/methodology/` and `/es/metodologia/` side by side; confirm comparable depth per section |
| 5-second page-purpose scan | UX-01 | Subjective scannability | Glance at `/is-santiago-safe/`; purpose clear within ~5s (one H1, scannable H2s) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are documented manual-only with no Wave 0 gaps
- [x] Sampling continuity: every plan ends in an `npm run build` automated gate; no 3 consecutive tasks without an automated signal
- [x] Wave 0 covers all MISSING references — none exist (existing infra covers all requirements)
- [x] No watch-mode flags (single-shot `npm run build`)
- [ ] Feedback latency < 60s — confirmed at execution (build timing)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-15 (contract established pre-execution; Plan 05 re-confirms manual rows at closeout)
