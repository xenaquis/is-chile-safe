# Phase 9: UX / Readability / Accessibility Polish — Research

**Researched:** 2026-06-15
**Domain:** Astro 6 SSR/SSG, React island (Leaflet), WCAG 2.1 AA, WAI-ARIA APG, bilingual i18n, SEO meta/JSON-LD
**Confidence:** HIGH (all findings grounded in actual source files and official specs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** ONE reusable "?" tooltip/info component next to every displayed rate (map Legend, ResultPanel, ranking tables). Short definition + one fixed plain-language sentence per page. Bilingual strings in `i18n.ts`. Static/SSR-friendly — no client-only critical content.
- **D-02:** Two surfaces for crime glossary: (a) per-family tooltip in map/panel/tables; (b) dedicated `/glossary` (EN) + `/glosario` (ES) bilingual pages reusing existing `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES`. Must be real prose (avoid thin content), CEAD-attributed.
- **D-03:** Legend must show real numeric range per colour band (e.g. "0–1,500") AND a qualitative label ("muy bajo → muy alto"), plus "por 100k hab." note. Reuse/extend `Legend.tsx` + `colors.ts`. Must stay legible on mobile.
- **D-04:** Commune standing expressed as multiplier vs average ("1,8× el promedio nacional") + small comparison bar. Neutral framing only. Reuse `loadNationalAverage` / `loadRegionalAverage`. Lives in `ResultPanel.tsx` (and optionally the commune money page).

### Claude's Discretion

- Exact tooltip interaction (hover + tap/focus for touch & keyboard a11y) and component naming.
- Where the once-per-page fixed "rate per 100k" explanation sentence sits.
- Whether the comparison bar also appears on the static commune money page vs only the interactive panel.
- How the original review-driven editorial items (UX/READ/A11Y) are split across plans vs the comprehension track.

### Deferred Ideas (OUT OF SCOPE)

- Interactive commune comparator, A-vs-B comparison pages, "safest communes" editorial, city/commune rankings by crime family. All v1.2.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UX-01 | One H1 per money page; scannable H2/H3; reader grasps page purpose in ~5 seconds | Heading audit findings below; BaseLayout passes `title` prop; headings set per-page |
| UX-02 | DataCallout/StatCard communicate one clear idea + source; callout↔prose redundancy eliminated | DataCallout.astro inspection; redundancy pattern found in review findings |
| READ-01 | Prose columns ~720px max-width with paragraph rhythm; no wall-of-text on editorial pages | EditorialLayout.astro already enforces 720px; gap is per-page paragraph spacing |
| READ-02 | ES/EN content, structure, and tone parity; no missing sections in either locale | F-003 finding (ES methodology half the content); need audit of all editorial pairs |
| READ-03 | Sober editorial tone site-wide; relative framing only; jargon explained | i18n.ts already uses sober strings; need prose review + glossary cross-links |
| A11Y-01 | WCAG AA contrast, visible focus states, alt text, aria on map controls — in sampled pages | Contrast analysis below; focus gap: NO :focus-visible rules exist in global.css |
| A11Y-02 | Valid `<title>`, meta description, canonical, hreflang, JSON-LD (FAQPage) in sampled templates | BaseLayout.astro verified; all present; gap is FAQPage on question-pages that lack it |
</phase_requirements>

---

## Summary

Phase 9 covers two complementary tracks landing on the same codebase. The **comprehension track** (D-01–D-04, user-driven) adds a reusable rate-tooltip component, a bilingual glossary route pair, numeric legend bands, and a multiplier/bar comparison in the map panel — all without new `client:*` directives. The **editorial/a11y track** (UX/READ/A11Y requirements) patches heading hierarchy, callout redundancy, ES content parity, and WCAG compliance gaps.

Code inspection reveals: (1) `EditorialLayout.astro` already enforces the 720px prose column, so READ-01 is a prose-rhythm audit rather than a layout change; (2) `BaseLayout.astro` already emits `<title>`, `<meta name="description">`, `hreflang×3`, and `canonical` — A11Y-02 gaps are about FAQPage JSON-LD coverage on non-FAQ pages and alt-text on inline SVG icons; (3) `global.css` has NO `:focus-visible` rules at all — this is the highest-severity a11y gap to fix; (4) the teal `#0f766e` palette largely passes WCAG AA but the primary-on-bg pair (4.71:1) is dangerously close to the 4.5:1 threshold; (5) `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES` already exist in `[family].astro` and `es/delito/[family].astro` as local constants — hoisting them to `site/src/lib/familyDefs.ts` is a prerequisite for D-02 without any logic rewrite.

**Primary recommendation:** Work in two parallel streams — (A) comprehension components (D-01–D-04, new files), (B) editorial/a11y patches (existing files). They touch disjoint files and can run in parallel plans.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Rate tooltip ("?") — map island | Browser / React island | — | Must exist in JSX to sit next to rate display inside `ResultPanel.tsx` and `Legend.tsx` |
| Rate tooltip ("?") — static tables | SSR / Astro component | — | Must be zero-JS; `<details>` or CSS `:focus-within` disclosure works inside `.astro` files |
| Crime glossary pages | SSR / Astro route | CDN/Static | Build-time pages; no dynamic data; captured in sitemap + hreflang |
| Numeric legend bands | Browser / React island | — | `Legend.tsx` runs client-side only; break thresholds computed from `computeQuantileBreaks` in `colors.ts` |
| Multiplier/comparison bar | Browser / React island (panel) + SSR (commune page) | — | `ResultPanel.tsx` is React; commune money page is Astro + already loads averages at build time |
| Focus styles / WCAG contrast | SSR / global CSS | — | Pure CSS token adjustments in `global.css`; no JS needed |
| Heading hierarchy / prose columns | SSR / per-page Astro | — | H1/H2 set in each `.astro` page; `EditorialLayout` wraps the 720px column |
| JSON-LD FAQPage | SSR / BaseLayout | — | `BaseLayout.astro` already accepts `jsonLd` prop; gap is per-page supply |
| Hamburger keyboard (WR-03) | SSR / Astro component | — | `PageHeader.astro` zero-JS checkbox hack; keyboard gap solvable with CSS `tabindex` on the `<label>` + `button` swap |

---

## Standard Stack

### Core (no new packages required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Astro | 6.4.x (installed) | New glossary pages, Astro tooltip component | Already in project; bilingual route pair mirrors existing pattern |
| React + @astrojs/react | 19.x / 5.x (installed) | React twin of tooltip for map island | Already in project; map island uses `client:only="react"` |
| chroma-js | 3.x (installed) | Compute `computeQuantileBreaks` already uses it | `colors.ts` already imports chroma; legend numeric bands use same breaks |

No new npm packages are needed for this phase. All comprehension and a11y work uses existing dependencies.

### Supporting (already installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @astrojs/sitemap | 3.x (installed) | Glossary pages auto-added to sitemap | sitemap filter in `astro.config.mjs` must pass `/glossary/` and `/es/glosario/` — both are not commune pages so the existing filter includes them by default |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS `<details>` disclosure for tooltip | Headless UI `Popover` (React) | Headless UI requires an additional package and `client:load`; `<details>` is zero-JS and native keyboard-accessible |
| CSS `<details>` disclosure | `title` attribute | `title` attribute is inaccessible on touch and not shown on keyboard focus — does not meet A11Y-01 |
| Hoisting `FAMILY_DEFS` to `lib/familyDefs.ts` | Keeping them per-page and duplicating in glossary | Hoisting eliminates the only source of duplication; single edit point for CEAD attribution strings |

**Installation:** No `npm install` needed for this phase.

---

## Package Legitimacy Audit

No new packages are installed in Phase 9. All work uses existing project dependencies.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Static Astro pages (SSR → HTML)
  │
  ├── EditorialLayout.astro [720px column, already correct]
  │     └── DataCallout.astro, FAQBlock.astro, etc.
  │
  ├── BaseLayout.astro [<title>, meta, hreflang, canonical, JSON-LD slot]
  │
  ├── CommuneRankingTable.astro ─── NEW: rate-tooltip Astro component
  ├── /glossary/ + /es/glosario/ ── NEW: bilingual glossary pages
  │     └── FAMILY_DEFS_EN/ES (hoisted to lib/familyDefs.ts)
  │
  └── global.css ── NEW: :focus-visible rules + token adjustments
        └── (token: --primary-dark or bump to #0c5e57 if needed)

React Island (client:only="react") — map only
  │
  ├── Legend.tsx ─────────── D-03: numeric bands + qualitative labels
  │     └── computeQuantileBreaks() from colors.ts (already exists)
  │
  ├── ResultPanel.tsx ─────── D-01: RateTooltip React twin
  │                           D-04: multiplier + comparison bar
  │     └── loadNationalAverage() / loadRegionalAverage() ← passed as props
  │           (data fetched at panel-open; averages are build-time constants
  │            that must be injected via map island props, not fetched at runtime)
  │
  └── PanelFamilyBars.tsx ── D-02: family glossary tooltip per bar row
```

### Recommended Project Structure

```
site/src/
├── lib/
│   └── familyDefs.ts          # NEW: hoist FAMILY_DEFS_EN + FAMILY_DEFS_ES here
├── components/
│   ├── RateTooltip.astro      # NEW: zero-JS <details> disclosure tooltip (Astro)
│   └── map/
│       ├── RateTooltipReact.tsx  # NEW: React twin (same visual, uses <details>)
│       ├── Legend.tsx            # EDIT: add numeric bands + qualitative labels
│       └── ResultPanel.tsx       # EDIT: add D-01 tooltip + D-04 multiplier/bar
├── pages/
│   ├── glossary.astro         # NEW: /glossary/ (EN)
│   └── es/
│       └── glosario.astro     # NEW: /es/glosario/ (ES)
└── styles/
    └── global.css             # EDIT: :focus-visible, minor token tweak if needed
```

### Pattern 1: Dual-Surface Accessible Tooltip (D-01, D-02) — Recommended Approach

**What:** CSS-only `<details>`/`<summary>` disclosure element styled as a small "?" button. Works identically in Astro `.astro` files and in JSX (React) — no JS runtime required in either context.

**Why `<details>` over a CSS `:hover` tooltip:**
- `<details>` is natively keyboard-operable: Tab to focus `<summary>`, Enter/Space to open, Escape closes in most browsers.
- Touch: tap-to-open (works on iOS Safari and Android Chrome natively).
- Screen reader: `<summary>` is exposed as a button with an expanded/collapsed state; content reads when open.
- Zero JS in the Astro context (pure SSR HTML); in React the same HTML/CSS works without `useState`.

**React usage pattern (for `ResultPanel.tsx`, `Legend.tsx`, `PanelFamilyBars.tsx`):**

```tsx
// Source: MDN Web Docs <details> element + WAI-ARIA APG Disclosure pattern
// site/src/components/map/RateTooltipReact.tsx
interface Props {
  label: string;   // "?" button label (visually hidden content or aria-label)
  tip: string;     // tooltip body text
  lang: 'en' | 'es';
}

export function RateTooltip({ label, tip, lang }: Props) {
  return (
    <span className="rate-tooltip">
      <details className="tooltip-details">
        <summary
          className="tooltip-trigger"
          aria-label={lang === 'es' ? `Más información: ${label}` : `More info: ${label}`}
        >
          <span aria-hidden="true">?</span>
        </summary>
        <div className="tooltip-body" role="tooltip">
          {tip}
        </div>
      </details>
    </span>
  );
}
```

**Astro usage pattern (for `CommuneRankingTable.astro`, glossary pages, static tables):**

```astro
---
// site/src/components/RateTooltip.astro
// Zero JS — pure <details> disclosure
interface Props {
  tip: string;
  lang: 'en' | 'es';
  label?: string;
}
const { tip, lang, label = lang === 'es' ? 'Más información' : 'More info' } = Astro.props;
---
<span class="rate-tooltip">
  <details class="tooltip-details">
    <summary class="tooltip-trigger" aria-label={label}>
      <span aria-hidden="true">?</span>
    </summary>
    <div class="tooltip-body" role="tooltip">{tip}</div>
  </details>
</span>
```

**CSS (add to global.css or scoped):**

```css
.rate-tooltip { display: inline-block; position: relative; }
.tooltip-details { display: inline; }
.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px; height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--primary);
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  list-style: none;           /* hide default <summary> triangle */
  user-select: none;
}
.tooltip-trigger::-webkit-details-marker { display: none; }
.tooltip-trigger:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.tooltip-body {
  display: none;
  position: absolute;
  z-index: 200;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--sm) var(--md);
  font-size: var(--text-label);
  max-width: 240px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  bottom: calc(100% + 4px);
  left: 50%; transform: translateX(-50%);
}
details[open] .tooltip-body { display: block; }
```

**WR-03 note (hamburger keyboard — fits A11Y-01):** The current `PageHeader.astro` hamburger uses `<input type="checkbox" tabindex="-1" aria-hidden="true">` driven by a `<label>`. The `<label>` itself is NOT natively keyboard-focusable (it only forwards clicks to the associated input). The D-09 zero-JS constraint is compatible with a simple fix: replace the `<label>` with a `<button>` that controls the nav via the `aria-expanded` + CSS `:checked` sibling trick — but that still requires JS for keyboard Escape. The pragmatic zero-JS path: keep the checkbox approach but add `tabindex="0"` to the `<label>` so it is keyboard-focusable and accepts Enter to toggle. This is valid HTML — labels respond to Enter key. Escape support requires a small inline `<script>` (11 lines). The planner should decide if that script counts as "zero-JS" under D-09. Recommendation: add `tabindex="0"` on the label (purely CSS, no JS, closes 90% of the keyboard gap) and treat Escape as a nice-to-have that can use a minimal inline script without shipping any framework JS.

### Pattern 2: Numeric Legend Bands (D-03)

`Legend.tsx` currently receives no data — it renders 5 static color swatches with only "Low" / "High" labels. The `computeQuantileBreaks` function in `colors.ts` already computes the break thresholds; `MapIsland` already has the full commune rate array to feed it.

**Extension approach:**

The `breaks` array (4 thresholds for 5 classes) must be passed as a prop from `MapIsland` down to `Legend`:

```tsx
// Legend.tsx — extended signature
interface Props {
  lang: 'en' | 'es';
  breaks?: number[];   // 4 values from computeQuantileBreaks(); undefined = no numeric bands
}

// Qualitative labels per level — add to i18n.ts
// EN: 'Very low' | 'Low' | 'Medium' | 'High' | 'Very high'
// ES: 'Muy baja' | 'Baja' | 'Media' | 'Alta' | 'Muy alta'

// Band label: "0 – 1,200" (format as locale integer)
// If breaks = [1200, 2400, 3600, 4800]:
//   Band 1: 0 – 1,200
//   Band 2: 1,201 – 2,400
//   Band 3: 2,401 – 3,600
//   Band 4: 3,601 – 4,800
//   Band 5: 4,801+
```

The `breaks` are already computed in `MapIsland` for the choropleth layer — they just need to be threaded into `Legend`. No new computation needed.

### Pattern 3: Multiplier + Comparison Bar (D-04)

`ResultPanel.tsx` fetches commune data at open time and already has `rate` and `data.national_rank`. The national and regional averages are **build-time constants** (computed by `loadNationalAverage()` / `loadRegionalAverage()`). They must be injected into the React island at render time as props, not fetched at runtime.

**Data flow:**

```
Astro map.astro (SSR build time)
  → loadNationalAverage()    → nationalAvg: number (build-time prop)
  → loadRegionalAverage()    → per-region map (not needed in panel; use national only)
  → <MapIsland nationalAvg={nationalAvg} />  [client:only="react"]

MapIsland (React, client-side)
  → <ResultPanel nationalAvg={nationalAvg} ... />

ResultPanel.tsx (new prop: nationalAvg)
  → multiplier = (rate / nationalAvg).toFixed(1)
  → barWidth = Math.min(rate / (nationalAvg * 3), 1) * 100   // cap at 3× for visual
  → neutral framing: "{multiplier}× el promedio nacional" (never "peligroso/seguro")
```

**Comparison bar (CSS only, no chart library):**

```tsx
<div className="comparison-bar-wrapper" aria-hidden="true">
  {/* Average marker at 1/3 of bar width (represents nationalAvg) */}
  <div className="comparison-bar-track">
    <div className="comparison-bar-avg-marker" style={{ left: '33%' }} />
    <div className="comparison-bar-commune"
         style={{ width: `${barWidth}%`, background: `var(--s${level})` }} />
  </div>
</div>
<div className="comparison-bar-label">
  {lang === 'es'
    ? `${multiplier}× el promedio nacional`
    : `${multiplier}× the national average`}
</div>
```

The same multiplier text can also appear on the static commune money page, since `loadNationalAverage()` is already called there for the ComparisonCallout.

### Pattern 4: Bilingual Glossary Pages (D-02)

New routes: `site/src/pages/glossary.astro` (EN `/glossary/`) and `site/src/pages/es/glosario.astro` (ES `/es/glosario/`). They mirror the existing bilingual-page pattern:

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { FAMILY_DEFS_EN, FAMILY_LABELS_EN, FAMILY_ORDER } from '../../lib/familyDefs.ts';

// enPath / esPath cross-reference for hreflang
const enPath = '/glossary/';
const esPath = '/es/glosario/';
---
<BaseLayout lang="en" title="Crime Type Glossary — Chile Safety Map"
  description="Definitions of the 7 crime families used in CEAD police statistics."
  enPath={enPath} esPath={esPath}>
  <article class="editorial-prose">
    <h1>Crime Type Glossary</h1>
    <p>The following definitions describe the 7 crime categories used in CEAD (Centro de Estudios y Análisis del Delito) police statistics, which power all data on this site.</p>
    {FAMILY_ORDER.map(key => (
      <section>
        <h2>{FAMILY_LABELS_EN[key]}</h2>
        <p>{FAMILY_DEFS_EN[key]}</p>
        <p><a href={`/crime/${FAMILY_SLUGS[key].en}/`}>National data for {FAMILY_LABELS_EN[key]}</a></p>
      </section>
    ))}
  </article>
</BaseLayout>
```

**Thin-content avoidance:** Each family section must have 2–3 sentences: definition + what CEAD records + a link to the family page. The existing `FAMILY_DEFS_EN/ES` strings are 1 sentence each — the page template must add context (what data counts, which subgroups CEAD includes) to reach substantive content. The planner should specify a minimum of 80–120 words per family entry.

**Sitemap:** `@astrojs/sitemap` automatically includes `/glossary/` and `/es/glosario/` because the sitemap filter's final `return true` catches all non-commune pages.

**Rollout compliance:** Glossary pages contain no commune links — rollout gating is not applicable. However, the within-glossary "National data for X" links go to `/crime/{slug}/` pages (already fully built, all 7 families, not rollout-gated per D-26), so no 404 risk.

### Anti-Patterns to Avoid

- **Passing `loadNationalAverage()` calls into the React island at runtime:** `loadNationalAverage()` uses Node `fs.readFileSync` — it is build-time only. Must compute once in the Astro page and pass as a prop.
- **Using `title` attribute for tooltips:** not announced by screen readers on mobile/touch; fails WCAG 1.3.1.
- **Creating a new `client:load` component for the tooltip:** violates D-09; the `<details>` element achieves the same UX with zero JS.
- **Hard-coding "peligroso" / "seguro" in glossary prose:** violates the editorial constraint. Always use "incidencia reportada" framing.
- **Linking glossary entries to non-rollout commune pages:** would introduce 404s. Only link to crime-type pages (`/crime/*`) or region pages (`/region/*`), never to commune pages (`/commune/*`) unless the slug is in rollout.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accessible tooltip | Custom `useState` + `useRef` popover logic in React | `<details>/<summary>` HTML element | Native keyboard focus, Escape, touch support; zero JS; WCAG 4.1.2 compliant |
| Colour-contrast checking | Manual RGB math | DevTools Accessibility panel + `wcag-contrast` npm CLI in verification step | Human error in manual calculation; tool gives exact ratios |
| Quantile legend breaks | Re-implementing `computeQuantileBreaks` | `colors.ts` `computeQuantileBreaks()` (already exists) | Duplicate logic risks divergence from the actual choropleth rendering |
| Bilingual string storage | New translation files / i18n library | `i18n.ts` `EN_STRINGS` / `ES_STRINGS` pattern (existing) | All new strings go in the same place — consistent with every prior phase |
| Chart/bar for comparison | D3 or recharts | Pure CSS `width %` bar (see Pattern 3) | No new dependency; sufficient for a single-axis proportional bar |

**Key insight:** This is a polish phase — every capability needed already exists as a library, helper, or pattern in the codebase. No new dependencies are warranted.

---

## Common Pitfalls

### Pitfall 1: Passing `loadNationalAverage()` to the React island at runtime

**What goes wrong:** Developer calls `loadNationalAverage()` inside the React component; it tries `fs.readFileSync` in the browser and throws.
**Why it happens:** `data.ts` uses Node `fs` — it is documented "build-time only" but the island's SSR boundary can be confused.
**How to avoid:** Call `loadNationalAverage()` in the Astro page's frontmatter (`map.astro`), then pass the result as a numeric prop to `<MapIsland nationalAvg={avg} />`. Document this explicitly in the plan.
**Warning signs:** `ReferenceError: fs is not defined` in the browser console.

### Pitfall 2: Breaking `<details>` tooltip positioning inside the map panel

**What goes wrong:** The `<details>` tooltip body uses `position: absolute` and overflows the `result-panel` if `overflow: hidden` is set on an ancestor.
**Why it happens:** Leaflet's panel container or the scrollable panel may clip absolutely-positioned children.
**How to avoid:** Set `overflow: visible` on the panel's stat-card and mini-stats-row containers, or use `position: fixed` for the tooltip body (with JS to calculate position — then D-09 applies). Simplest: verify in the browser that the tooltip opens without clipping; if it clips, use `z-index` + `overflow: visible` on the `.stat-card` wrapper.
**Warning signs:** Tooltip appears clipped or invisible when opened inside the panel.

### Pitfall 3: Thin glossary content triggering Google thin-content penalty

**What goes wrong:** Each glossary entry is only one sentence (the existing `FAMILY_DEFS_*` strings), making the page thin and at risk of deindexing.
**Why it happens:** The `FAMILY_DEFS_*` strings are excellent for tooltips but insufficient for a standalone page.
**How to avoid:** Each entry must have at minimum: (1) the definition sentence, (2) what specific CEAD subgroup IDs or categories it covers, (3) a note on under-reporting patterns for this category, (4) a link to the crime-type page. Target 80–120 words per entry, ~600+ words total page.
**Warning signs:** Google Search Console reports the page as "thin content" or "Excluded: content issues."

### Pitfall 4: `:focus-visible` gap remains after applying only global rules

**What goes wrong:** Developer adds `:focus-visible` to `a` and `button` in `global.css` but misses the `<summary>` element (used by the new tooltip), the `.lang-btn` span, and the `.nav-toggle-btn` label.
**Why it happens:** Custom-styled elements that suppress native focus rings without replacing them.
**How to avoid:** Apply a blanket rule first (`*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`) and then override only where needed. Test by tabbing through every interactive element in the page.
**Warning signs:** Tabbing through the page with keyboard shows no visible focus indicator on some elements.

### Pitfall 5: Glossary links creating rollout 404s

**What goes wrong:** A glossary entry links to `/commune/{slug}/` for an example commune that is not in rollout.
**Why it happens:** Developer adds "e.g. Santiago recorded 9,309…" with an `<a href="/commune/santiago/">` — Santiago IS in rollout so it works in dev, but other example communes used in prose may not be.
**How to avoid:** Only link commune names if their slug is confirmed in `rollout.json`; otherwise name-drop without linking. Crime-type pages (`/crime/*`) and region pages (`/region/*`) are safe to link always.

### Pitfall 6: `--primary` on `--bg` contrast at 4.71:1 — barely passing

**What goes wrong:** A future designer tightens `--bg` toward pure white (or lightens `--primary`) and the primary-on-bg pairing drops below 4.5:1.
**Why it happens:** The current 4.71:1 ratio has only a 5% margin above the threshold.
**How to avoid:** Document the exact ratio in a CSS comment: `/* #0f766e on #f5f8f8 = 4.71:1 (AA min 4.5:1) — do not lighten primary or darken bg */`. If any Phase 9 change touches these tokens, re-verify with the DevTools accessibility checker.

### Pitfall 7: Hamburger `<label>` not keyboard-focusable (WR-03)

**What goes wrong:** `<label for="nav-toggle">` with `tabindex="-1"` on the checkbox — the label is not reachable by Tab key because `<label>` elements are not natively focusable.
**Why it happens:** The zero-JS checkbox pattern is widely used but the label needs `tabindex="0"` to be keyboard-reachable.
**How to avoid:** Add `tabindex="0"` to the `<label class="nav-toggle-btn">` element. Labels activate their associated control on Enter key press (HTML spec), so this is sufficient for toggle-open without JS. For Escape-to-close, a 10-line inline `<script>` is the minimum and is consistent with D-09 (no framework JS is being added).

---

## WCAG Contrast Analysis

All calculations use relative luminance per WCAG 2.1 §1.4.3.

| Foreground | Background | Ratio | Standard | Status |
|-----------|-----------|-------|----------|--------|
| `#0f766e` (--primary) | `#f5f8f8` (--bg) | **4.71:1** | AA normal (4.5:1) | PASSES — barely |
| `#0f766e` (--primary) | `#ffffff` (--card) | **5.01:1** | AA normal (4.5:1) | PASSES |
| `#ffffff` | `#0f766e` (--primary, lang-btn.active) | **5.01:1** | AA normal (4.5:1) | PASSES |
| `#5d6c6d` (--muted) | `#f5f8f8` (--bg) | **4.72:1** | AA normal (4.5:1) | PASSES — barely |
| `#5d6c6d` (--muted) | `#ffffff` (--card) | **5.02:1** | AA normal (4.5:1) | PASSES |
| `#1c2a2b` (--ink) | `#f5f8f8` (--bg) | **~16:1** | AA | PASSES (comfortable) |
| `#0f766e` (--primary) at 28px/700 | `#ffffff` (--card, callout-value) | **5.01:1** | AA large (3:1) | PASSES easily |
| `#dbeef0` (--s1, choropleth fill) | no text overlay | N/A | no text | N/A |
| `#9fd0cd` (--s2, choropleth fill) | no text overlay | N/A | no text | N/A |

**Key finding:** NO colour token changes are strictly required for WCAG AA compliance. The two "barely passing" pairings (primary-on-bg at 4.71:1 and muted-on-bg at 4.72:1) have sufficient margin. A11Y-01 work is **focus states** (entirely missing) and **alt text / aria labels**, not colour changes.

**Focus state gap (critical):** `global.css` has zero `:focus-visible` rules. The browser default focus ring (a thin blue outline) may be suppressed by the CSS reset (`margin: 0; padding: 0`). The reset does NOT suppress focus rings, but the site has no intentional focus styling. Required fix:

```css
/* Add to global.css — WCAG 2.1 SC 2.4.7 (AA) */
*:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Suppress the outline on mouse-click (cosmetic) — focus-visible handles this */
*:focus:not(:focus-visible) {
  outline: none;
}
```

---

## Code Examples

### Add i18n strings for Phase 9 features

```typescript
// Source: site/src/config/i18n.ts — extend I18nStrings interface and both locale objects

// In I18nStrings interface — add:
rate_tooltip_title: string;      // "Rate per 100,000 inhabitants"
rate_tooltip_body: string;       // explanation sentence
glossary_link: string;           // "Crime type glossary"
comparison_national: string;     // "{multiplier}× the national average"
legend_qual_1: string;           // "Very low"
legend_qual_2: string;           // "Low"
legend_qual_3: string;           // "Medium"
legend_qual_4: string;           // "High"
legend_qual_5: string;           // "Very high"
legend_per_100k_note: string;    // "Reported rate per 100,000 inhabitants"

// EN values:
rate_tooltip_title: 'Rate per 100,000 inhabitants',
rate_tooltip_body: 'This figure counts police-reported incidents for every 100,000 people living in the area, allowing fair comparison between places of very different population sizes. Source: CEAD official police statistics.',
glossary_link: 'Crime type glossary',
comparison_national: '{multiplier}× the national average',
legend_qual_1: 'Very low',
legend_qual_2: 'Low',
legend_qual_3: 'Medium',
legend_qual_4: 'High',
legend_qual_5: 'Very high',
legend_per_100k_note: 'Reported rate per 100,000 inhabitants',

// ES values:
rate_tooltip_title: 'Tasa por 100.000 habitantes',
rate_tooltip_body: 'Esta cifra cuenta los incidentes reportados a la policía por cada 100.000 personas residentes en la zona, permitiendo comparar lugares de tamaños muy distintos en igualdad de condiciones. Fuente: estadísticas policiales oficiales CEAD.',
glossary_link: 'Glosario de tipos de delito',
comparison_national: '{multiplier}× el promedio nacional',
legend_qual_1: 'Muy baja',
legend_qual_2: 'Baja',
legend_qual_3: 'Media',
legend_qual_4: 'Alta',
legend_qual_5: 'Muy alta',
legend_per_100k_note: 'Tasa reportada por 100.000 habitantes',
```

### Hoist FAMILY_DEFS to shared lib module

```typescript
// NEW: site/src/lib/familyDefs.ts
// Hoisted from site/src/pages/crime/[family].astro and es/delito/[family].astro
// Source: existing constants in those files — copy verbatim, do not rewrite

export const FAMILY_LABELS_EN: Record<string, string> = {
  vida:            'Life Crimes',
  robos_violentos: 'Violent Robbery',
  vif:             'Domestic Violence',
  drogas:          'Drug Crimes',
  armas:           'Weapons Offences',
  propiedad:       'Property Crimes',
  incivilidades:   'Disorder',
};

export const FAMILY_LABELS_ES: Record<string, string> = { /* existing ES labels */ };

export const FAMILY_DEFS_EN: Record<string, string> = { /* existing EN defs */ };
export const FAMILY_DEFS_ES: Record<string, string> = { /* existing ES defs */ };

// Display order for glossary (matching PanelFamilyBars FAMILY_ORDER)
export const FAMILY_ORDER = [
  'vida', 'propiedad', 'robos_violentos', 'incivilidades', 'vif', 'drogas', 'armas'
] as const;
```

After hoisting, update the two `[family].astro` pages to import from `../../lib/familyDefs.ts` instead of defining locally.

### Extended Legend.tsx (D-03)

```tsx
// site/src/components/map/Legend.tsx — extended (key diff only)
// Source: existing Legend.tsx + Pattern 2 above

interface Props {
  lang: 'en' | 'es';
  breaks?: number[];  // [b1, b2, b3, b4] from computeQuantileBreaks in MapIsland
}

const QUAL_LABELS = {
  en: ['Very low', 'Low', 'Medium', 'High', 'Very high'],
  es: ['Muy baja', 'Baja', 'Media', 'Alta', 'Muy alta'],
};

export function Legend({ lang, breaks }: Props) {
  const labels = QUAL_LABELS[lang];

  function bandLabel(i: number): string {
    if (!breaks) return labels[i] ?? '';
    const lo = i === 0 ? 0 : (breaks[i - 1] ?? 0) + 1;
    const hi = breaks[i] ?? null;
    const fmt = (n: number) => Math.round(n).toLocaleString(lang === 'es' ? 'es-CL' : 'en-US');
    return hi !== null ? `${fmt(lo)} – ${fmt(hi)}` : `${fmt(lo)}+`;
  }

  return (
    <div className="legend">
      <div className="legend-title">
        {lang === 'es' ? 'Incidencia reportada' : 'Reported incidence'}
        {/* D-01: rate tooltip */}
        <RateTooltip lang={lang} label="rate" tip={/* from i18n */''} />
      </div>
      <div className="legend-bands">
        {INCIDENCE_COLORS.map((c, i) => (
          <div key={i} className="legend-band">
            <span className="legend-swatch" style={{ background: c }} aria-hidden="true" />
            <span className="legend-band-label">
              <span className="legend-qual">{labels[i]}</span>
              {breaks && <span className="legend-range">{bandLabel(i)}</span>}
            </span>
          </div>
        ))}
      </div>
      <div className="legend-unit">
        {lang === 'es' ? 'por 100.000 hab.' : 'per 100,000 inhab.'}
      </div>
    </div>
  );
}
```

### MapIsland prop threading for nationalAvg and breaks

```astro
---
// site/src/pages/map.astro (SSR frontmatter — build time)
import { loadNationalAverage } from '../lib/data.ts';
const nationalAvg = loadNationalAverage();   // computed once at build time
---
<!-- Pass as prop to React island; breaks are computed inside MapIsland from commune rates -->
<MapIsland lang="en" nationalAvg={nationalAvg} client:only="react" />
```

---

## Bilingual Glossary Page Wiring

### Route pair mirrors existing bilingual pattern

| Page | URL | enPath | esPath |
|------|-----|--------|--------|
| `site/src/pages/glossary.astro` | `/glossary/` | `/glossary/` | `/es/glosario/` |
| `site/src/pages/es/glosario.astro` | `/es/glosario/` | `/glossary/` | `/es/glosario/` |

### Sitemap (automatic)

The `sitemapFilter` in `astro.config.mjs` returns `true` for all non-commune pages via the final `return true` branch. `/glossary/` and `/es/glosario/` match no commune or region pattern, so they pass through automatically. No filter change needed.

### hreflang (automatic via BaseLayout)

`BaseLayout.astro` already emits:
```html
<link rel="alternate" hreflang="en" href="https://ischilesafe.com{enPath}" />
<link rel="alternate" hreflang="es" href="https://ischilesafe.com{esPath}" />
<link rel="alternate" hreflang="x-default" href="https://ischilesafe.com{enPath}" />
```
The glossary pages pass `enPath="/glossary/"` and `esPath="/es/glosario/"` — reciprocal hreflang is automatic.

### Cross-links from existing pages

- `CommuneRankingTable.astro` and crime-type pages: add a "See [glossary link]" footnote.
- `PanelFamilyBars.tsx`: each family label can link to the glossary anchor `#vida`, `#propiedad`, etc. (anchor navigation, zero JS).
- `MethodologyCaveat.astro`: add glossary cross-link in the existing caveat text.

---

## SEO / Meta Validation (A11Y-02)

### Current state (from BaseLayout.astro inspection)

| Signal | Implementation | Status |
|--------|---------------|--------|
| `<title>` | `{title}` prop in BaseLayout | Present on all pages |
| `<meta name="description">` | `{description}` prop | Present on all pages |
| `canonical` | `{BASE_URL}{canonicalPath}` (locale-aware) | Present on all pages |
| `hreflang en/es/x-default` | BaseLayout hard-wired from `enPath`/`esPath` | Present on all pages |
| JSON-LD FAQPage | `jsonLd` prop → `<script type="application/ld+json">` | Present on FAQ editorial pages; **absent on region/commune templates** |

### Gap: FAQPage JSON-LD on question-format money pages

`/is-santiago-safe/`, `/is-chile-safe/`, and their Spanish counterparts supply `jsonLd` with `FAQPage` type — confirmed in the `is-santiago-safe.astro` source. The **region pages** (`[slug].astro`) and **commune pages** (`[slug].astro`) have ranking tables but no FAQ block; they use a `Dataset` schema, which is appropriate. No gap here.

**Actual A11Y-02 gaps to address:**
1. **Alt text on inline SVGs:** The `official-check` SVG in `ResultPanel.tsx` has `aria-hidden="true"` (correct). The PinGlyph SVG in `PageHeader.astro` has `aria-hidden="true"` (correct — the link already has `aria-label="Chile Safety Map home"`). The `TrendChip.astro` and `LevelChip.astro` components need review — check for decorative icons without `aria-hidden`.
2. **Map control aria labels:** The `MapIsland` filters row (year `<select>`, crime-type chip `<button>` elements) — confirm `aria-label` or `<label>` associations. From Phase 8 fixes, these were addressed. Planner should add a verification step.
3. **Focus states:** As noted — entirely missing from `global.css`. This is the primary A11Y-01 fix.

---

## Editorial / Readability Gaps (UX-01, UX-02, READ-01, READ-02, READ-03)

### READ-01: 720px prose column

`EditorialLayout.astro` already sets `max-width: 720px` on `.editorial-prose`. The gap is per-page paragraph rhythm:
- No `margin-bottom` on `<p>` elements in `global.css` (`margin: 0` from the CSS reset).
- Required fix: add `p + p { margin-top: var(--md); }` or `p { margin-bottom: var(--md); }` globally, or scope to `.editorial-prose p`.
- Verify the commune/region/crime programmatic pages that use `BaseLayout` (not `EditorialLayout`) have their own prose containers — they use `<main class="page-content">` (max-width 860px). The wider container is intentional for data tables; prose sections within those pages need their own max-width scoping.

### READ-02: ES/EN parity

Confirmed F-003 finding: ES methodology is 4,174 chars vs EN 8,849 chars — roughly half. This is the one confirmed structural parity gap. Other editorial page pairs were verified as equivalent in the review (REVIEW-01 table). The plan must include updating `/es/metodologia/` to match the EN content structure.

### READ-03: Tone audit

`i18n.ts` strings are already sober. The risk area is the free-form prose in editorial `.astro` pages. The planner should specify a tone audit pass on at least the 6 highest-traffic editorial pages (is-chile-safe, is-santiago-safe, safest-cities, chile-crime-map, mapa-delito-chile, mapa-seguridad-santiago) verifying:
- No use of "peligroso", "seguro", "dangerous", "safe" in absolute terms.
- Every stat has a CEAD + year attribution.
- Relative framing present where comparisons appear (already true in code-generated FAQs).

### UX-01: Heading hierarchy

From REVIEW-01: all 30 sampled pages rendered with a single `<h1>` (confirmed). The H1 content issue (F-001 — "Commune" in Spanish H1) was fixed in Phase 8. The Phase 9 task is a pass to verify H2/H3 scannability in the top editorial pages — not a structural fix, but a content-quality pass.

### UX-02: DataCallout redundancy

`DataCallout.astro` shows `value` + `label` + `source`. The review noted no specific callout-redundancy finding, but the requirement asks to eliminate callout-to-prose redundancy where the same statistic appears twice. The plan should include a pass over the top 3 editorial pages (is-santiago-safe, is-chile-safe, safest-cities) to remove any stat that is stated both in a DataCallout and word-for-word in the adjacent paragraph.

---

## Runtime State Inventory

This is a polish/UX/CSS phase with no renames. No runtime state changes needed. No data migration.

**Stored data:** None — JSON files in `data/cead/` are read-only in this phase.
**Live service config:** None — no n8n, no external service config.
**OS-registered state:** None.
**Secrets/env vars:** None — no new keys introduced.
**Build artifacts:** `dist/` is rebuilt on every `npm run build`; no stale artifacts from this phase's changes.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `title` attribute for tooltips | `<details>/<summary>` disclosure | WCAG 2.1 (2018) | `title` fails on touch; `<details>` is accessible on all input modalities |
| Custom focus ring removal (`:focus { outline: none }`) | `:focus-visible` (hide on mouse, show on keyboard) | CSS Level 4 / 2021 browser support | Allows hiding the ring on mouse without hiding it from keyboard users |
| Separate JS tooltip libraries | HTML-native `<details>` | 2020+ | No JS bundle cost; better a11y defaults |

**Deprecated/outdated:**
- `:focus { outline: none; }` anywhere: replace with `:focus:not(:focus-visible) { outline: none; }` to preserve keyboard navigation.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `loadNationalAverage()` is not already passed as a prop to MapIsland — it is only used in Astro SSR pages currently | Pattern 3, Code Examples | If MapIsland already receives this prop, the threading step is unnecessary; low risk (additive change) |
| A2 | `<label>` with `tabindex="0"` activates its associated checkbox via Enter key in all major browsers | Pitfall 7, Pattern anti-hamburger | If certain browsers don't trigger the checkbox from Enter on a focused `<label>`, the keyboard toggle won't work; low risk (well-established HTML behavior) |
| A3 | The `sitemapFilter` in `astro.config.mjs` includes `/glossary/` by default via its final `return true` | Bilingual Glossary Wiring | If a future change to the filter narrows it, the glossary could be excluded; easy to verify by checking the build output sitemap |

**All color contrast ratios** are calculated from first principles using the WCAG 2.1 relative luminance formula — not verified with an external tool in this session. The planner should add a verification step using browser DevTools or an `axe` scan. [ASSUMED confidence level for exact ratios]

---

## Environment Availability

Step 2.6: SKIPPED for most items — this phase is CSS/Astro/React source edits only, no new CLIs or services.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build | ✓ | (project already building) | — |
| npm | Package management | ✓ | (project already running) | — |
| Astro dev server | Manual visual verification | ✓ | `cd site && npm run dev` | — |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (pipeline tests) + manual browser verification (UI changes) |
| Config file | `pytest.ini` or `pyproject.toml` (existing) |
| Quick run command | `cd "C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe" && cd site && npm run build` |
| Full suite command | `npm run build && npm run preview` (then manual tab-key walk) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| UX-01 | Single H1, scannable H2/H3 | smoke | `npm run build` (Astro throws on duplicate H1 only if validator added) | Manual re-read in browser after build |
| UX-02 | No callout-prose redundancy | manual | — | Visual scan of top 3 editorial pages |
| READ-01 | 720px column, paragraph rhythm | smoke | `npm run build` → preview | Visual check; `EditorialLayout` already enforces max-width |
| READ-02 | ES/EN parity on methodology | manual | — | Character-count comparison after update |
| READ-03 | No absolute tone ("peligroso/seguro") | smoke | `grep -ri "peligroso\|seguro\|dangerous\|safe" site/src/pages/` | String search after prose edits |
| A11Y-01 | Focus states visible; WCAG AA contrast; alt text | smoke | `axe` browser extension (manual) OR build + axe-core scan | Primary automated signal: no build error; secondary: axe scan |
| A11Y-02 | title/meta/canonical/hreflang/JSON-LD present | smoke | `npm run build` + spot-check built HTML with `grep` | `BaseLayout.astro` unchanged — already verified in Phase 7 |

### Wave 0 Gaps

- No new test files required. This phase's validation is build-success + manual browser tabbing + axe scan.
- The planner should add a verification step: `cd site && npm run build` (chain with build to avoid OneDrive desync — see memory note `onedrive-build-artifacts-desync`).
- Recommend a `grep` assertion for forbidden tone words as part of the phase closeout (READ-03).

---

## Security Domain

This phase makes no changes to authentication, session management, or data handling. It adds:
- Static HTML pages (glossary) — no user input, no XSS vectors.
- CSS changes — no security surface.
- `<details>` element — native HTML, no JS injection surface.

| ASVS Category | Applies | Control |
|---------------|---------|---------|
| V5 Input Validation | No | No new user input fields |
| V6 Cryptography | No | No new secrets |
| Other | No | Pure CSS/HTML/static page additions |

The existing `JSON.stringify().replace(/<\//g, '<\\/')` XSS escape in `BaseLayout.astro` already covers the JSON-LD slot — no change needed for glossary pages (they supply no JSON-LD in the initial scope, or plain `WebPage` schema if added).

---

## Sources

### Primary (HIGH confidence)

- `site/src/components/map/Legend.tsx` — current implementation, inspected directly
- `site/src/components/map/colors.ts` — `computeQuantileBreaks`, `INCIDENCE_COLORS`, inspected directly
- `site/src/components/map/ResultPanel.tsx` — current panel, all props, inspected directly
- `site/src/components/map/PanelFamilyBars.tsx` — family display order, FAMILY_LABELS, inspected directly
- `site/src/config/i18n.ts` — EN_STRINGS, ES_STRINGS, FAMILY_SLUGS, full interface, inspected directly
- `site/src/lib/data.ts` — `loadNationalAverage`, `loadRegionalAverage`, `loadRolloutCuts`, inspected directly
- `site/src/layouts/BaseLayout.astro` — hreflang, canonical, JSON-LD slot, inspected directly
- `site/src/layouts/EditorialLayout.astro` — 720px prose column, confirmed present
- `site/src/styles/global.css` — full token set, NO `:focus-visible` rules confirmed absent
- `site/src/components/PageHeader.astro` — hamburger implementation, `tabindex="-1"` on checkbox confirmed
- `site/src/components/DataCallout.astro` — component structure, inspected directly
- `site/src/pages/crime/[family].astro` — `FAMILY_DEFS_EN` source location confirmed
- `.planning/REVIEW-E2E-FINDINGS.md` — F-001 through F-009 findings; Phase 7 evidence
- `site/astro.config.mjs` — sitemap filter logic, i18n config, confirmed
- WCAG 2.1 SC 1.4.3 relative luminance formula [ASSUMED — standard formula applied to hex values above]
- WAI-ARIA APG Disclosure (Show/Hide) pattern — [ASSUMED: standard `<details>/<summary>` is the recommended native implementation]

### Secondary (MEDIUM confidence)

- MDN Web Docs — `<details>/<summary>` keyboard behavior (Enter to open, native accessibility) [ASSUMED based on training knowledge, well-established]

### Tertiary (LOW confidence)

- WCAG AA contrast ratio calculations performed manually in this session — [ASSUMED: recommend re-verification with browser DevTools Accessibility panel]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all from codebase inspection
- Architecture: HIGH — grounded in actual file structure and existing patterns
- WCAG contrast values: MEDIUM — manual calculation, recommend tool verification
- Pitfalls: HIGH — derived from actual code inspection + Phase 7/8 findings

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 (stable stack; Astro 6 / React 19 unlikely to break in 30 days)
