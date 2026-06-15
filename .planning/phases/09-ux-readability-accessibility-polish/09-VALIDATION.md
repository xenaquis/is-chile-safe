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
| UX-01 | 04 (+05 scan) | 2/3 | T-09-08 | Exactly one `<h1>`; scannable H2/H3; purpose clear in ~5s | smoke + manual | `cd site && npm run build` + `grep -c "<h1" site/src/pages/is-santiago-safe.astro` == 1 | ✅ existing infra | ✅ auto (build✓, h1=1) · manual 5s-scan pending |
| UX-02 | 02/03/04 | 2 | T-09-04/06/08 | DataCallout/StatCard = one idea + CEAD source; no callout↔prose stat duplication | smoke + manual | `cd site && npm run build`; manual spot-check (Plan 05 Task 2) on is-santiago-safe / is-chile-safe / safest-cities | ✅ existing infra | ⬜ manual spot-check pending (Task 2) |
| READ-01 | 01 | 1 | T-09-01 | 720px prose column + paragraph rhythm (`.editorial-prose p` margin) | smoke | `cd site && npm run build` + `grep -c ".editorial-prose p" site/src/styles/global.css` ≥ 1 | ✅ existing infra | ✅ green (grep=1, build✓) |
| READ-02 | 04 | 2 | T-09-08 | ES methodology at content parity with EN (6 sections, ≥11,000 bytes) | smoke + manual | `cd site && npm run build` + `wc -c site/src/pages/es/metodologia.astro` ≥ 11000; manual side-by-side depth check (Plan 05) | ✅ existing infra | ✅ auto (14,685 bytes ≥ 11k) · manual depth pending |
| READ-03 | 03/04 (+05 grep) | 2/3 | T-09-06/08 | Sober tone site-wide; no absolute peligroso/seguro/dangerous/safe; CEAD+year attribution | smoke | `grep -rin --include=*.astro "es peligroso\|is dangerous\|muy seguro\|totalmente seguro" site/src/pages/` returns no absolute-verdict line | ✅ existing infra | ✅ green (no absolute verdicts) |
| A11Y-01 | 01/02 (+05 manual) | 1/2/3 | T-09-01/02/04 | Visible :focus-visible rings; alt text; aria on map controls (year `<select>`, crime chips); WCAG-AA contrast | smoke + manual axe | `grep -c ":focus-visible" site/src/styles/global.css` ≥ 1; manual: tab-walk + axe on /map/, /glossary/, /is-santiago-safe/ + map-control aria assertion (Plan 05 Task 2) | ✅ existing infra | ✅ auto (:focus-visible=4) · manual axe/tab-walk pending |
| A11Y-02 | 03 (+05 meta grep) | 2/3 | T-09-06 | Valid `<title>`, meta description, canonical, hreflang on new pages; FAQPage JSON-LD present on a FAQ money page | smoke | build emits `dist/glossary/index.html` + `dist/es/glosario/index.html`; grep built HTML for `<title`,`name="description"`,`rel="canonical"`,`hreflang`; grep `dist/is-santiago-safe/index.html` for `"@type":"FAQPage"` (Plan 05 Task 1) | ✅ existing infra | ✅ green (routes✓, 4 meta signals✓, FAQPage=1) |

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

## Plan 05 Task 1 — Automated Run Record (2026-06-15)

Single chained command (`cd site && npm run build && <dist + source greps>`), OneDrive desync guard honored.

| Assertion | Command excerpt | Result |
|-----------|-----------------|--------|
| Production build | `npm run build` | ✅ exit 0 — 102 page(s) built |
| New routes emitted | `ls dist/glossary/index.html dist/es/glosario/index.html dist/is-santiago-safe/index.html` | ✅ all 3 present |
| Meta signals (glossary) | grep `<title` / `name="description"` / `rel="canonical"` / `hreflang` on `dist/glossary/index.html` | ✅ 1 / 1 / 1 / 1 |
| A11Y-02 FAQPage JSON-LD | `grep -c FAQPage dist/is-santiago-safe/index.html` | ✅ 1 |
| READ-03 tone (absolute verdicts) | `grep -rin "es peligroso\|is dangerous\|muy seguro\|totalmente seguro\|very dangerous\|totally safe" site/src/pages/` | ✅ no matches |
| READ-01 prose rhythm | `grep -c "\.editorial-prose p" src/styles/global.css` | ✅ 1 |
| A11Y-01 focus-visible | `grep -c ":focus-visible" src/styles/global.css` | ✅ 4 |
| UX-01 single H1 | `grep -c "<h1" src/pages/is-santiago-safe.astro` | ✅ 1 |
| READ-02 ES methodology depth | `wc -c src/pages/es/metodologia.astro` | ✅ 14,685 bytes ≥ 11,000 |

Manual-only rows (A11Y-01 tab-walk + axe aria/contrast, UX-02 callout spot-check, UX-01 5s scan, READ-02 side-by-side depth) remain pending the Task 2 human-verify checkpoint.

---

## Plan 05 Task 2 — Browser Verification Record (BrowserOS, localhost:4322, 2026-06-15)

Driven via BrowserOS MCP against the live preview build. ✅ = automated browser assertion confirmed; ⏳ = left for human (inherently visual/subjective/interactive).

| Manual check | Req | Result |
|--------------|-----|--------|
| Map-control aria names | A11Y-01 | ✅ year `<select>` = "Filter by year" / "Filtrar por año"; 13 buttons, **0 unnamed** (chips have text, zoom/locate have aria-label) |
| WCAG-AA contrast (axe-core 4.10, wcag2a/2aa) on `/map/` | A11Y-01 | ✅ **no color-contrast violations** |
| Legend numeric+qualitative bands | D-03 | ✅ EN: 5 bands (Very low→Very high, 0–4,464 … 7,121+) + "per 100,000 inhabitants"; ES: Muy baja→Muy alta + "por 100.000 habitantes" |
| Rate "?" tooltip (zero-JS) on ranking table | D-01 | ✅ `/region/metropolitana/` rate header has `<details>` "?" explaining rate-per-100k + "Crime type glossary" cross-link → /glossary/ |
| Bilingual glossary depth + language round-trip | A11Y-02 / READ-02 | ✅ EN 1017 words / ES 1167 words, 7 family anchors, CEAD-attributed, 7 `/crime/*` (`/es/delito/*`) links; switcher round-trips /glossary/ ↔ /es/glosario/ |
| Meta signals on new pages | A11Y-02 | ✅ glossary title/description/canonical/hreflang all present (Task 1) |
| Callout↔prose redundancy | UX-02 | ✅ is-santiago-safe (only repeat is in self-contained FAQ answers, 8 sections from callout) · ✅ is-chile-safe (no non-FAQ repeat) · ⚠️ safest-cities: 5,808 reused in a comparison sentence ("compared with the national mean of 5,808") in a separate "How to Interpret" section — editorially justified, flagged for human eye |
| Visible :focus-visible rings (Tab walk) | A11Y-01 | ⏳ CSS present (4 `:focus-visible` rules); visible-outline confirmation needs human Tab walk |
| Panel rate "?" tooltip keyboard operation | D-01 | ⏳ requires opening a commune panel (map-polygon/search select) — human interactive check |
| Multiplier + comparison bar in commune panel | D-04 | ⏳ map.css comparison-bar styles loaded; render needs an open panel — human interactive check |
| ES/EN methodology depth parity (visual) | READ-02 | ⏳ byte parity ✅ (14,685 ≥ 11k); side-by-side editorial-depth glance is human |
| 5-second page-purpose scan | UX-01 | ⏳ subjective — human |

**Pre-existing finding (out of Phase 9 scope, not a regression):** axe flags `aria-prohibited-attr` (serious) on `<span aria-label="Show my location" data-map-locate-label>` — an empty visually-hidden locate-label span with no role. Originates from Phase 03 (591702b) + Phase 04 (3d65129) across 6 map pages; the locate *button* already carries the correct aria-label. Recommend a future cleanup (drop the redundant aria-label or give the span `role="text"`), but it does not block Phase 9.

---

## Plan 05 Task 2 — Human Checkpoint Outcome + Gap-Closure (2026-06-15)

User reviewed the live preview and **did not approve as-is** — reported 5 issues. Triaged into Phase-9 scope vs new work:

**Fixed now (Phase-9 gap-closure):**
- **#1 "¿Qué es incivilidades?"** — opaque CEAD family terms had no inline explanation on the map filter chips. Added a per-chip `title` definition sourced from `familyDefs` (commit `fa44ab3`). Verified: ES "Incivilidades" chip now shows the full CEAD definition on hover; all 7 families covered. *(D-02/READ comprehension)*
- **#5 internal-links audit** — crawled 48 internal links across Phase-9 + ES pages; found one broken target `/es/map/` emitted by the shared header nav (`getRelativeLocaleUrl('/map')` doesn't translate the ES slug). Fixed to localized `/es/mapa/` (commit `590b009`). Re-audit: **0 broken links**. Footer ES slugs were already correct.

**Deferred to new roadmap phases (out of Phase-9 polish scope — confirmed with user):**
- **#2 Map geometry** — `communes.topo.json` is only 88KB for 346 communes (heavily simplified → blocky polygons). User wants real boundaries (high resolution, accepting larger file). → new phase.
- **#3 Homicide as its own category** — `homicidios` data exists per commune but is folded inside "vida"; no dedicated map filter/layer. → new phase.
- **#4 SEO rankings by crime type** ("las N comunas con más homicidios") — depends on #3 data exposure; needs programmatic ranking templates + internal linking. → new phase.

**Residual interactive a11y items (low risk, not reported as defects by user during live review):** visible focus-ring Tab-walk, panel "?" tooltip keyboard operation, and multiplier-bar render require an open commune panel; CSS/components are present and built, contrast passed axe. Recommend a final Tab-walk at convenience.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are documented manual-only with no Wave 0 gaps
- [x] Sampling continuity: every plan ends in an `npm run build` automated gate; no 3 consecutive tasks without an automated signal
- [x] Wave 0 covers all MISSING references — none exist (existing infra covers all requirements)
- [x] No watch-mode flags (single-shot `npm run build`)
- [x] Feedback latency < 60s — confirmed at execution (build ~32–55s, single shot)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-15 (contract established pre-execution; Plan 05 re-confirms manual rows at closeout)
