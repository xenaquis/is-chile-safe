# Phase 29 — Baseline Evidence (MAPUX-01) + MAPUX-04 Competitor Click-Through

**Captured**: 2026-07-30, inline in the Fable orchestrator session via BrowserOS MCP.
**Build under test**: real served build — `npm run build` then `npx astro preview --port 4321 --host`.
**Screenshots**: `C:\Users\Carlo\bos-shots\p29\` (paths contain no spaces, per the BrowserOS constraint).

All numbers below were produced by `evaluate_script` against the live DOM, not estimated from a screenshot.

---

## 1. Desktop baseline — 1296 × 678 viewport

Screenshot: `i0-desktop-map.png`

| Measurement | Value |
|---|---|
| `.filters-row` scrollWidth | 1287 px |
| `.filters-row` clientWidth | 780 px |
| **Horizontal overflow (hidden content)** | **507 px** |
| `.ev-chip` ("Noticias recientes" — the news-layer toggle) x-position | **1370 px** |
| `.ev-chip` visible within viewport | **NO** |
| `.leaflet-container` width | 812 px inside a 1296 px viewport |

**Chip order** (left to right): year select → Todos → Vida y convivencia → Propiedad → Robos violentos → Incivilidades → VIF → Drogas → Armas → Homicidios → **Noticias recientes**.

The news-layer toggle is the **last** element of a row that overflows by 507 px. It sits ~590 px past the visible right edge of its scroll container. There is **no scroll affordance** — no edge fade, no chevron, no scrollbar at rest — so nothing signals that content exists to the right.

**This is the discoverability problem, stated exactly**: the qualitative news layer, which is half of the product's core value proposition, is unreachable on a standard desktop viewport unless the user guesses that an unmarked row scrolls horizontally.

Secondary desktop finding: the map occupies 812 px of a 1296 px viewport (63%), with large empty gutters left and right. The map reads as a boxed widget rather than the page's subject.

## 2. Mobile baseline — 375 px iframe emulation (360 px inner width)

Screenshot: `i0-mobile375.png`. BrowserOS has no viewport-resize, so 375 px is emulated with a 375 px-wide iframe, per the phase's BrowserOS constraints.

| Measurement | Value |
|---|---|
| Inner document width | 360 px (375 minus scrollbar) |
| `.filters-row` scrollWidth / clientWidth | 1287 / 296 px |
| **Horizontal overflow** | **991 px** |
| `.ev-chip` x-position | 1151 px (~855 px offscreen) |
| Minimum chip height | 44 px — **touch target OK** |
| Chrome above the map | ~285 px |
| `.legend-mobile` `<details>` open at rest | NO, and it sits below the fold |

Visible chips at rest: `2025`, `Todos`, and a clipped `Vida y convive…`. Nine of eleven controls — including the news toggle — are offscreen with no affordance.

The map viewport at this size is dominated by ocean and Argentina; Chile is a thin sliver. Combined with 285 px of chrome above it, the first mobile impression is mostly chrome and empty sea.

**Passing at baseline**: touch targets are already ≥44 px. That criterion is not the problem; discoverability is.

## 3. MAPUX-04 — live competitor click-through

### police.uk — NOT USED
Screenshot: `ref-policeuk-desktop.png`. The site is behind a Cloudflare "Verificación de seguridad en curso" human-verification challenge. **The challenge was not circumvented.** MAPUX-04 requires "at least one comparable product (police.uk **or** CityProtect)", so the requirement is satisfied by the product below; police.uk is recorded as blocked, not skipped.

### CrimeMapping.com (CityProtect family) — USED
Screenshots: `ref-crimemapping-desktop.png` (loading), `ref-crimemapping-loaded.png` (loaded).

Five transferable findings:

1. **Filters live in a permanent, labeled left rail** — icon + text, stacked vertically: `SUMMARY / WHAT / WHERE / WHEN / REPORT / CHARTS`. Dimensions are grouped by question word rather than flattened into one undifferentiated row. Every filter dimension keeps a visible entry point even when its own panel is closed. **Nothing is ever offscreen.**
2. **The map is full-bleed** — edge to edge, filling all space left over by the rail and top bar. Contrast with our 812/1296 px boxed map.
3. **Current filter state is always legible without opening a panel** — a persistent record-count chip (`0 Records`) and an explicit active range (`Date Range: 7-23-2026 to 7-29-2026 (7 Days)`) sit in the top bar. Our map surfaces no state summary at all.
4. **The empty state is announced across the map** in a banner: "No records found when using the current filter." A filter that yields nothing says so, in place, rather than leaving a blank map.
5. **Search is prominent and wide** (address/landmark/zip) with an explicit submit, occupying the top-left — the same slot our `SearchBox` uses, which is the one part of our shell that already follows the pattern.

**Design consequence for our loop**: the failure in our shell is not chip styling — it is that a single flat, horizontally-scrolling row is being asked to carry four different dimensions (time, crime family, homicide layer, news layer) plus a mode toggle. Every reference product separates dimensions and guarantees each one a persistent, labeled entry point. That, plus a visible state summary, is what iteration 1 must attack.

---

## 4. Folded-in: Phase 28's deferred manual browser pass (N3) — **COMPLETE, ALL PASS**

Phase 28 closed with its manual pass unrun (STATE.md § Phase 28 Outcome, item 2). It was run here, in the same browser session, at effectively zero marginal cost. Target: `/es/noticias/` on the same served build.

| Item | Method | Result |
|---|---|---|
| Filter-bar layout at 375 px | 375 px iframe, measured `scrollWidth - clientWidth` on `#news-filters` and on `documentElement` | **PASS** — 0 px overflow on both; no horizontal scroll |
| Touch targets at 375 px | measured every `#news-filters label` | **PASS** — 28 of 29 labels are 243 × 44 px; the 29th is the caption text for the comuna input, and the input itself is 180 × 44 px |
| Keyboard / focus trap | 32 focusables in the filter bar, **0** with negative tabindex; `grep` for `keydown`/`keyup`/`preventDefault` across `news.astro`, `es/noticias.astro`, `newsFilterLogic.ts` returns **nothing** | **PASS — a trap is impossible by construction.** Native tab order applies because no script intercepts key events. This is stronger evidence than sampling a few Tab presses. |
| `aria-live` announcement | inspected `[aria-live]` nodes | **PASS** — `#news-result-count` carries `aria-live="polite"` and reads "1392 incidentes mostrados" |
| Render with JS disabled | re-loaded the page inside `<iframe sandbox="allow-same-origin">`, which blocks script execution in a real browser | **PASS** — 1392 `article.news-card`, **0** carrying `hidden`, count sentence correct, `#news-empty` hidden, real headline text present |
| No literal `{n}` / `{date}` in indexed HTML (F-32b) | scanned `body.innerText` and every attribute | **PASS** — zero brace tokens in visible text; they appear **only** in `SPAN[data-result-count-template]`, the carrier Phase 28 deliberately ships (F-35) |
| CLS | `PerformanceObserver({type:'layout-shift', buffered:true})` | **PASS** — CLS **0.0000**, **0** layout-shift entries |
| Live filter interaction + URL sync | clicked the "Últimos 7 días" label, then re-read state | **PASS** — 341 of 1392 cards visible, count reads "341 incidentes mostrados", matching the facet count exactly; URL becomes `?window=7d` |

The last row also **re-confirms F-38's WR-01 fix in the real build**: the URL is `?window=7d`, not the bare `?` the pre-fix code produced.

INP was not measured as a Core Web Vitals field metric (it needs real user interaction sampling); the synthetic filter interaction above completed within one animation frame plus 250 ms of settle time with zero layout shift.

## 5. Incidental defect found while setting up (out of Phase 29 scope — see F-40)

`site/src/layouts/BaseLayout.astro:116-131` runs a browser-language redirect on EN pages that reads the `hreflang="es"` `<link>` and calls `window.location.replace(esLink.href)`. That href is built from `BASE_URL` (line 72-74) and is therefore an **absolute production URL**.

Consequence: on any non-production origin — `localhost` preview, a Cloudflare preview deployment, a staging host — an es-locale browser visiting any EN page is redirected **cross-origin to `https://ischilesafe.com`**. It happened in this session: a tab opened at `http://127.0.0.1:4321/map/` landed on `https://ischilesafe.com/es/mapa/`, silently substituting production for the build under test.

This is a live QA hazard for Phases 29 and 30, whose entire method is driving a local build in a browser. The baseline above was therefore re-measured on `http://127.0.0.1:4321/es/mapa/` (an ES page, where the redirect does not fire) and reproduced the desktop numbers **exactly** (507 px overflow, `.ev-chip` at x=1370), so no baseline figure is contaminated.

Fix is one line — redirect to the same origin by taking only the path off the hreflang href. Handling recorded in F-40.
