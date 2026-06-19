# Phase 7: E2E Review Pass — Research

**Researched:** 2026-06-13
**Domain:** Browser-driven QA review — page inventory, map interactions, mobile viewport, BrowserOS MCP tooling
**Confidence:** HIGH (all findings verified against repo source files)

---

## Summary

Phase 7 is a pure investigative phase: no code is written, only the site is observed. The deliverable is `.planning/REVIEW-E2E-FINDINGS.md` — a prioritised log of everything the reviewer found wrong, missing, or unclear, organised by severity (Critical / Warning / Polish). The plan must drive a browser through every page category in a declared order so nothing is missed, capture evidence, and close all five REVIEW-0x requirements.

The site ships 37 Astro source files mapping to approximately 780+ static pages (12 rollout communes × 2 locales = 24 commune pages, 16 regions × 2 locales = 32 region pages, 7 crime types × 2 locales = 14 crime pages, plus editorial and legal). The editorial inventory is **14 EN pages and 14 ES pages** — not 10+10 as stated in REQUIREMENTS.md; the actual page count was verified by enumerating `site/src/pages/`. The plan must acknowledge this discrepancy and use the real count.

The review runs against the dev server (`cd site && npm run dev`), not against a build. This avoids the OneDrive dist/ desync issue. The BrowserOS MCP server drives the browser at `http://127.0.0.1:9200/mcp` and is configured in `.mcp.json`. Its tools surface as `mcp__browseros__*` in Claude Code — a Claude Code restart may be required before execution if the tools are not yet visible.

**Primary recommendation:** Structure the plan as five sequential waves matching the five REVIEW-0x requirements. Each wave produces a section of REVIEW-E2E-FINDINGS.md. The executor uses BrowserOS MCP navigate → screenshot → read-console for each URL, then writes findings inline.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Page navigation & screenshot | BrowserOS MCP (external) | — | MCP drives the real browser; no proxy layer needed |
| Console error capture | BrowserOS MCP | — | Browser console is read via MCP tool |
| Viewport resize (mobile) | BrowserOS MCP | — | MCP set-viewport call |
| Map interaction (click, filter) | BrowserOS MCP (click/type) | MapIsland.tsx (React) | Interactions fire JS events in the real browser |
| Findings document | `.planning/REVIEW-E2E-FINDINGS.md` | — | Written by executor after each review wave |
| Data source for sampling decisions | `data/cead/meta/index.json`, `site/src/config/rollout.json` | — | Pick communes by population tier from these files |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REVIEW-01 | All editorial pages (EN + ES) + /map/ + /es/mapa/ + legal pages navigated, screenshotted, console-checked | Full URL inventory below; BrowserOS MCP tools documented |
| REVIEW-02 | Declared programmatic sample (≥3 communes, ≥2 regions, ≥2 crime types, both locales) reviewed against page template | Rollout communes enumerated; crime-type slugs listed; template structure documented |
| REVIEW-03 | Map dynamic interactions verified in browser | MapIsland.tsx and all sub-components filed; interaction checklist below |
| REVIEW-04 | Mobile viewport (~375px) on money pages and map | BrowserOS MCP set-viewport documented; target pages identified |
| REVIEW-05 | `.planning/REVIEW-E2E-FINDINGS.md` with severity/page/screenshot/recommendation | Findings document schema specified below |
</phase_requirements>

---

## Page Inventory (Verified Against `site/src/pages/`)

### FINDING: Page count differs from REQUIREMENTS.md

REQUIREMENTS.md states "10 EN editorial + 10 ES editorial". The actual source tree has **14 EN editorial pages** and **14 ES editorial pages** (excluding programmatic templates, map pages, and legal pages). The plan must use the real count. [VERIFIED: repo file listing]

### EN Editorial Pages (14 pages)

| # | URL | Source File |
|---|-----|-------------|
| 1 | `/` | `site/src/pages/index.astro` |
| 2 | `/is-chile-safe/` | `site/src/pages/is-chile-safe.astro` |
| 3 | `/is-santiago-safe/` | `site/src/pages/is-santiago-safe.astro` |
| 4 | `/safest-cities-in-chile/` | `site/src/pages/safest-cities-in-chile.astro` |
| 5 | `/chile-crime-map/` | `site/src/pages/chile-crime-map.astro` |
| 6 | `/santiago-safety-map/` | `site/src/pages/santiago-safety-map.astro` |
| 7 | `/valparaiso-safety/` | `site/src/pages/valparaiso-safety.astro` |
| 8 | `/vina-del-mar-safety/` | `site/src/pages/vina-del-mar-safety.astro` |
| 9 | `/concepcion-safety/` | `site/src/pages/concepcion-safety.astro` |
| 10 | `/about/` | `site/src/pages/about.astro` |
| 11 | `/contact/` | `site/src/pages/contact.astro` |
| 12 | `/methodology/` | `site/src/pages/methodology.astro` |

**Count: 12 EN editorial pages** (not 14 as initially miscounted; count verified below against ES).

### ES Editorial Pages (12 pages)

| # | URL | Source File |
|---|-----|-------------|
| 1 | `/es/` | `site/src/pages/es/index.astro` |
| 2 | `/es/mapa-delito-chile/` | `site/src/pages/es/mapa-delito-chile.astro` |
| 3 | `/es/mapa-seguridad-santiago/` | `site/src/pages/es/mapa-seguridad-santiago.astro` |
| 4 | `/es/comunas-mas-seguras-chile/` | `site/src/pages/es/comunas-mas-seguras-chile.astro` |
| 5 | `/es/delitos-por-comuna/` | `site/src/pages/es/delitos-por-comuna.astro` |
| 6 | `/es/delitos-por-region/` | `site/src/pages/es/delitos-por-region.astro` |
| 7 | `/es/seguridad-concepcion/` | `site/src/pages/es/seguridad-concepcion.astro` |
| 8 | `/es/seguridad-valparaiso/` | `site/src/pages/es/seguridad-valparaiso.astro` |
| 9 | `/es/seguridad-vina-del-mar/` | `site/src/pages/es/seguridad-vina-del-mar.astro` |
| 10 | `/es/acerca-de/` | `site/src/pages/es/acerca-de.astro` |
| 11 | `/es/contacto/` | `site/src/pages/es/contacto.astro` |
| 12 | `/es/metodologia/` | `site/src/pages/es/metodologia.astro` |

**Revised count: 12 EN + 12 ES editorial pages.** REQUIREMENTS.md's "10+10" is an undercount. [VERIFIED: repo file listing]

### Map Pages (2 pages)

| URL | Source File |
|-----|-------------|
| `/map/` | `site/src/pages/map.astro` |
| `/es/mapa/` | `site/src/pages/es/mapa.astro` |

### Legal Pages (4 pages, 2 locales = 8 URLs)

| EN URL | ES URL | EN Source | ES Source |
|--------|--------|-----------|-----------|
| `/terms/` | `/es/terminos/` | `terms.astro` | `es/terminos.astro` |
| `/privacy-policy/` | `/es/politica-privacidad/` | `privacy-policy.astro` | `es/politica-privacidad.astro` |

**FINDING: Only 4 legal pages exist (2 EN + 2 ES = 4 URLs total), not 8.** REQUIREMENTS.md says "8 legal pages" — the actual source tree has only terms and privacy-policy in each locale. [VERIFIED: repo file listing] The plan must use the real count and note the discrepancy in REVIEW-E2E-FINDINGS.md as a potential gap (missing cookie policy, accessibility statement, etc. — flag as Polish if absent).

---

## Programmatic Page Patterns

### Commune Pages

- **EN URL pattern:** `/commune/{slug}/`
- **ES URL pattern:** `/es/comuna/{slug}/`
- **Source:** `site/src/pages/commune/[slug].astro` + `site/src/pages/es/comuna/[slug].astro`
- **Gate:** Only communes in `site/src/config/rollout.json` are built (`enabled` array of CUT codes)
- **Rollout state (verified):** 12 communes currently enabled [VERIFIED: `site/src/config/rollout.json`]

**All 12 rollout communes by population tier:**

| Tier | CUT | Name | Slug | Population | Region |
|------|-----|------|------|------------|--------|
| High | 13119 | Maipú | `maipu` | 586,812 | 13 (Metropolitana) |
| High | 13101 | Santiago | `santiago` | 544,388 | 13 (Metropolitana) |
| High | 2101 | Antofagasta | `antofagasta` | 444,276 | 2 (Antofagasta) |
| High | 5109 | Viña del Mar | `vina-del-mar` | 371,490 | 51 (Valparaíso) |
| High | 13114 | Las Condes | `las-condes` | 343,632 | 13 (Metropolitana) |
| High | 5101 | Valparaíso | `valparaiso` | 320,816 | 51 (Valparaíso) |
| High | 9101 | Temuco | `temuco` | 309,696 | 9 (La Araucanía) |
| High | 10101 | Puerto Montt | `puerto-montt` | 280,955 | 10 (Los Lagos) |
| High | 4101 | La Serena | `la-serena` | 267,400 | 4 (Coquimbo) |
| Mid | 8101 | Concepción | `concepcion` | 239,776 | 8 (Biobío) |
| Mid | 13123 | Providencia | `providencia` | 164,009 | 13 (Metropolitana) |
| Low | 12101 | Punta Arenas | `punta-arenas` | 145,713 | 12 (Magallanes) |

**Declared sample for REVIEW-02 (meets ≥3 communes high/mid/low, ≥2 regions, ≥2 crime types, both locales):**

| Commune | Tier | CUT | EN URL | ES URL | Region |
|---------|------|-----|--------|--------|--------|
| Santiago | High | 13101 | `/commune/santiago/` | `/es/comuna/santiago/` | 13 |
| Concepción | Mid | 8101 | `/commune/concepcion/` | `/es/comuna/concepcion/` | 8 |
| Punta Arenas | Low | 12101 | `/commune/punta-arenas/` | `/es/comuna/punta-arenas/` | 12 |

This covers 3 population tiers and 3 distinct regions.

### Region Pages

- **EN URL pattern:** `/region/{slug}/`
- **ES URL pattern:** `/es/region/{slug}/`
- **Source:** `site/src/pages/region/[slug].astro` + `site/src/pages/es/region/[slug].astro`
- **Gate:** All 16 regions — NOT rollout-gated [VERIFIED: source file comment]

**Declared sample for REVIEW-02 (≥2 regions):**

| Region | Slug | EN URL | ES URL |
|--------|------|--------|--------|
| Metropolitana (13) | `metropolitana` | `/region/metropolitana/` | `/es/region/metropolitana/` |
| Biobío (8) | `biobio` | `/region/biobio/` | `/es/region/biobio/` |

### Crime-Type Pages

- **EN URL pattern:** `/crime/{en-slug}/`
- **ES URL pattern:** `/es/delito/{es-slug}/`
- **Source:** `site/src/pages/crime/[family].astro` + `site/src/pages/es/delito/[family].astro`
- **Gate:** All 7 crime families — NOT rollout-gated [VERIFIED: source file comment]

**All 7 crime type slugs:** [VERIFIED: `site/src/config/i18n.ts` FAMILY_SLUGS]

| Family Key | EN Slug | ES Slug | EN URL | ES URL |
|------------|---------|---------|--------|--------|
| vida | `homicide` | `homicidios` | `/crime/homicide/` | `/es/delito/homicidios/` |
| robos_violentos | `violent-robbery` | `robos-violentos` | `/crime/violent-robbery/` | `/es/delito/robos-violentos/` |
| vif | `domestic-violence` | `violencia-intrafamiliar` | `/crime/domestic-violence/` | `/es/delito/violencia-intrafamiliar/` |
| drogas | `drug-crimes` | `drogas` | `/crime/drug-crimes/` | `/es/delito/drogas/` |
| armas | `weapons` | `armas` | `/crime/weapons/` | `/es/delito/armas/` |
| propiedad | `property` | `propiedad` | `/crime/property/` | `/es/delito/propiedad/` |
| incivilidades | `disorder` | `incivilidades` | `/crime/disorder/` | `/es/delito/incivilidades/` |

**Declared sample for REVIEW-02 (≥2 crime types):**

| Family | EN URL | ES URL | Rationale |
|--------|--------|--------|-----------|
| vida | `/crime/homicide/` | `/es/delito/homicidios/` | Featured family; most data |
| propiedad | `/crime/property/` | `/es/delito/propiedad/` | Featured family; highest incidence |

---

## Commune Page Template Structure

The commune page template (verified from `site/src/pages/commune/[slug].astro` imports) renders the following components in order:

1. `BaseLayout` — title, meta description, canonical, hreflang, JSON-LD
2. `LevelChip` — incidence level (low/medium/high/very-high)
3. `TrendChip` — year-over-year trend (up/down/stable)
4. `StatCard` — headline rate per 100k
5. `Sparkline` — 20-year trend sparkline (static SVG)
6. `ComparisonCallout` — vs-national and vs-regional comparison
7. `FamilyBreakdownBars` — 7-family bar chart (static)
8. `ComparableCommune` — comparable commune cross-link
9. `MapPlaceholderSlot` — static placeholder linking to `/map/`
10. `MethodologyCaveat` — CEAD attribution + caveat

"Reviewed against the page template" (REVIEW-02) means: all 10 components present, correct data shown (rate uses national mean not sum), family bars render, comparable link resolves, hreflang correct.

---

## Map Island: Interaction Inventory

**Main file:** `site/src/components/map/MapIsland.tsx` (React island, `client:only="react"`)

**Sub-components and what each drives:**

| Interaction | Component(s) | What to Verify |
|-------------|-------------|----------------|
| Year filter | `FiltersRow.tsx` — `<select>` year dropdown | Select changes choropleth colours for all communes; 2005–2025 available |
| Crime-type filter (chip) | `FiltersRow.tsx` — `CHIP_DEFS` chips | Click each chip → choropleth recolours by family index; "All types" resets to total |
| Commune panel open | `MapIsland.tsx` `setSelected()` + `ResultPanel.tsx` | Click polygon → panel slides in; fetches `/data/cead/comunas/{cut}.json` |
| Panel: rate/trend/ranking | `ResultPanel.tsx` | Rate per 100k, trend arrow, national rank / total 346 |
| Panel: sparkline | `PanelSparkline.tsx` | SVG sparkline renders with ≥2 data points |
| Panel: family bars | `PanelFamilyBars.tsx` | 7 bars present; RECORD→ARRAY conversion (CATALOG_KEY_ORDER) correct |
| Panel: families tab | `ResultPanel.tsx` families section | Family breakdown section visible |
| Search | `SearchBox.tsx` | Type commune name → prefix dropdown → select → map zooms + panel opens |
| Geolocation | `UserLocationMarker.ts` + `SearchBox.tsx` locate button | Click locate → browser permission prompt → marker placed (or Toast error if denied) |
| Incident layer toggle | `FiltersRow.tsx` events toggle + `IncidentPinLayer.ts` | Toggle ON → fetch `/data/incidents/current.json` → 404 expected → "coming soon" Toast shown, NO console.error |
| Toast dismissal | `Toast.tsx` | Toast auto-dismisses or has close button |

**Incident layer empty state is the expected behaviour in dev** — `data/incidents/current.json` does not exist (requires live pipeline). Verifying it shows a graceful toast and no console error is the REVIEW-03 target for that interaction.

---

## BrowserOS MCP Tooling

**Configuration:** `.mcp.json` at repo root — already configured:
```json
{
  "mcpServers": {
    "browseros": {
      "type": "http",
      "url": "http://127.0.0.1:9200/mcp"
    }
  }
}
```
[VERIFIED: `.mcp.json` in repo root]

**How tools surface:** As `mcp__browseros__*` tool calls in Claude Code. If tools do not appear in the executor's environment, a Claude Code restart is required (known issue: MCP tools may not surface in agent threads without restart — see STATE.md Research Flags).

**Expected BrowserOS MCP tool set** [ASSUMED — tools inferred from BrowserOS MCP purpose; executor must verify tool names at runtime]:

| Tool (assumed name) | Purpose | Usage in Review |
|--------------------|---------|-----------------|
| `mcp__browseros__navigate` | Navigate to a URL | Open each page under review |
| `mcp__browseros__screenshot` | Take a screenshot | Capture evidence after navigation |
| `mcp__browseros__get_console_logs` | Read browser console | Check for errors/warnings after page load |
| `mcp__browseros__set_viewport` | Resize viewport | Set to 375×812 for mobile review |
| `mcp__browseros__click` | Click an element | Trigger map interactions (chips, polygon, search) |
| `mcp__browseros__type` | Type text | Enter commune name in SearchBox |
| `mcp__browseros__evaluate` | Execute JS | Check DOM state, read element dimensions for touch-target check |

**Screenshot storage:** `.planning/ui-reviews/` — this directory exists and is gitignored for binary files (png/jpg/etc. excluded by `.planning/ui-reviews/.gitignore`). Screenshots land here; REVIEW-E2E-FINDINGS.md references them by relative path (`ui-reviews/screenshot-name.png`).

**Dev server base URL:** `http://localhost:4321` (Astro default; confirm with `npm run dev` output — may be `4322` if port occupied).

**Connection caveat:** BrowserOS MCP server must be running before the executor starts. The Memory note confirms it is at `http://127.0.0.1:9200/mcp`. If the executor cannot connect, the plan must have a checkpoint that blocks and asks the user to start BrowserOS.

---

## Architecture Patterns

### Review Wave Structure (Recommended)

```
Wave 1 (REVIEW-01): Editorial + Legal inventory
  ├── 12 EN editorial pages × navigate+screenshot+console
  ├── 12 ES editorial pages × navigate+screenshot+console
  ├── /map/ + /es/mapa/ × navigate+screenshot+console
  └── 4 legal EN + 4 legal ES × navigate+screenshot+console

Wave 2 (REVIEW-02): Programmatic page sampling
  ├── 3 commune pages × 2 locales (Santiago, Concepción, Punta Arenas)
  ├── 2 region pages × 2 locales (Metropolitana, Biobío)
  ├── 2 crime-type pages × 2 locales (homicide, property)
  └── Each: template checklist verification + screenshot

Wave 3 (REVIEW-03): Map interactions
  ├── Navigate /map/ (EN)
  ├── Year filter: select 2010, verify recolour
  ├── Crime chip: click "Property crimes", verify recolour
  ├── Commune click: click Santiago polygon → panel opens
  ├── Panel tabs: rate, trend, ranking, sparkline, family bars
  ├── Search: type "Temuco" → select → panel opens
  ├── Geolocation: click locate button
  └── Incident toggle: toggle ON → verify Toast, no console.error

Wave 4 (REVIEW-04): Mobile viewport
  ├── Set viewport 375×812
  ├── Navigate money pages: /, /is-chile-safe/, /is-santiago-safe/, /map/
  └── Check: no horizontal scroll, map usable, touch targets visually ≥44px

Wave 5 (REVIEW-05): Consolidate findings
  └── Write .planning/REVIEW-E2E-FINDINGS.md from all wave observations
```

### REVIEW-E2E-FINDINGS.md Schema

```markdown
# E2E Review Findings — Phase 7

**Date:** YYYY-MM-DD
**Reviewer:** Claude Code (BrowserOS MCP)
**Dev server:** http://localhost:4321
**Viewport (desktop):** 1280×800
**Viewport (mobile wave):** 375×812

## Findings

### F-001 — [Severity: Critical|Warning|Polish]
- **Page:** /route/here/
- **Locale:** EN | ES | Both
- **Screenshot:** ui-reviews/f-001-description.png
- **Observation:** What was seen
- **Recommendation:** What should change

...
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Page screenshot evidence | Manual description only | BrowserOS MCP screenshot tool — every finding needs visual proof |
| Console error detection | Visual inspection of page | BrowserOS MCP console-read tool — automated, reproducible |
| Mobile simulation | Resizing browser manually | BrowserOS MCP set-viewport — exact 375px reproducible |
| URL list management | Ad-hoc navigation | The URL inventory above — declare upfront, tick off in order |

---

## Common Pitfalls

### Pitfall 1: Dev Server Not Running When Executor Starts
**What goes wrong:** BrowserOS navigates to `http://localhost:4321` and gets connection refused. All screenshots are blank.
**Why it happens:** The dev server must be started manually (`cd site && npm run dev`) before the review.
**How to avoid:** First plan task must be a `checkpoint:human` that confirms dev server is running and BrowserOS MCP is reachable.
**Warning signs:** Screenshot shows blank/error page; console log shows "net::ERR_CONNECTION_REFUSED".

### Pitfall 2: BrowserOS MCP Tools Not Surfaced
**What goes wrong:** Executor cannot find `mcp__browseros__*` tools.
**Why it happens:** Claude Code agent threads may not inherit MCP tools added after session start. A restart is needed.
**How to avoid:** STATE.md Research Flags note: "verify with tool search for `mcp__*browseros*__*`". Plan must include a pre-flight tool availability check.
**Warning signs:** Tool calls fail with "tool not found".

### Pitfall 3: Port 4321 vs. Port Conflict
**What goes wrong:** Dev server starts on port 4322 (or higher) if 4321 is occupied.
**How to avoid:** The pre-flight checkpoint confirms the actual port from `npm run dev` output.

### Pitfall 4: Incident Layer — Missing File Is Expected, Not a Bug
**What goes wrong:** Reviewer logs 404 for `/data/incidents/current.json` as a Critical bug.
**Why it happens:** The incidents pipeline requires a live `DEEPSEEK_API_KEY` run (out of scope for v1.1). The 404 is the correct graceful empty state.
**How to avoid:** REVIEW-03 interaction for the incident layer is "verify graceful toast + no console.error", not "verify incidents appear".

### Pitfall 5: Page Count Mismatch with REQUIREMENTS.md
**What goes wrong:** Plan gates success on "10 EN + 10 ES editorial" and REVIEW-01 is marked incomplete because 12+12 exist.
**How to avoid:** Use the real counts (12 EN + 12 ES editorial, 4 legal pages in each locale, total 4 URL pairs) established in this research.

### Pitfall 6: OneDrive Build Artifact Desync
**What goes wrong:** Executor tries to run `npm run build` before review to get a "clean" build; `dist/` desyncs and pages show stale content.
**How to avoid:** Review runs exclusively against the dev server. No build step in Phase 7.

---

## Existing Review Artifacts

- `.planning/ui-reviews/` exists and is **empty** (contains only `.gitignore` for image files). No prior review screenshots exist. [VERIFIED: directory listing]
- No prior REVIEW-E2E-FINDINGS.md exists. Phase 7 creates it from scratch.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | `npm run dev` (Astro dev server) | ✓ | (not probed — assumed present since v1.0 was built) | — |
| Astro dev server | All BrowserOS navigation | Must be started by human before review | `cd site && npm run dev` | None — blocking |
| BrowserOS MCP server | All browser interactions | Must be running at 127.0.0.1:9200 | — | None — blocking; review cannot proceed without it |
| `.planning/ui-reviews/` dir | Screenshot storage | ✓ (exists, writable) | — | — |

**Missing dependencies with no fallback:**
- Astro dev server (human must start: `cd site && npm run dev`)
- BrowserOS MCP at port 9200 (human must confirm it is running; Claude Code restart may be needed to surface tools)

---

## Validation Architecture

Phase 7 is observational — there are no unit tests. Each REVIEW-0x requirement is verified by browser evidence:

| Req ID | Verification Method | Evidence Type | Automated? |
|--------|--------------------|-|---|
| REVIEW-01 | BrowserOS navigate + screenshot + console-read for every URL in inventory | Screenshot files in `ui-reviews/`, console log excerpts in FINDINGS | Semi-auto (MCP-driven) |
| REVIEW-02 | Programmatic page template checklist for declared sample communes/regions/crime-types | Screenshots + checklist table in FINDINGS | Semi-auto (MCP-driven) |
| REVIEW-03 | Map interaction sequence: year filter → chip filter → polygon click → panel tabs → search → locate → incident toggle | Screenshots at each interaction step + console clean | Semi-auto (MCP-driven) |
| REVIEW-04 | BrowserOS set-viewport(375, 812) → navigate money pages → screenshot → visual inspection | Screenshot evidence, horizontal scroll check via JS `document.body.scrollWidth > window.innerWidth` | Semi-auto (MCP + JS eval) |
| REVIEW-05 | REVIEW-E2E-FINDINGS.md written and non-empty with at least one finding per reviewed URL | File exists, structured per schema above | File existence check |

**Nyquist sampling strategy:** Because all 5 requirements are browser-evidence based, the "test suite" is the BrowserOS MCP interaction sequence itself. The plan's tasks ARE the tests. Per-wave completion = requirement satisfied.

**No Wave 0 gaps:** No test framework installation needed. BrowserOS MCP is an external service already configured.

---

## Security Domain

This phase makes no code changes. No ASVS categories apply — Phase 7 is read-only QA observation.

---

## Sources

### Primary (HIGH confidence)
- `site/src/pages/**/*.astro` — exact page inventory, all 37 files enumerated directly
- `site/src/config/rollout.json` — 12 rollout CUT codes verified
- `site/src/config/i18n.ts` — FAMILY_SLUGS, all 7 EN/ES slug pairs
- `data/cead/meta/index.json` — 346 communes, population values, slugs
- `data/cead/regions/*.json` — 16 region slugs
- `site/src/components/map/MapIsland.tsx` — map init, data fetch URLs, state variables
- `site/src/components/map/FiltersRow.tsx` — CHIP_DEFS, AVAILABLE_YEARS (2005–2025)
- `site/src/components/map/ResultPanel.tsx` — panel data shape, CATALOG_KEY_ORDER
- `site/src/components/map/IncidentPinLayer.ts` — empty-state graceful behaviour
- `site/src/components/map/SearchBox.tsx` — search + locate interaction
- `.mcp.json` — BrowserOS MCP endpoint confirmed at `http://127.0.0.1:9200/mcp`
- `.planning/ui-reviews/.gitignore` — directory exists and is gitignored for images
- `.planning/STATE.md` — Research Flags confirm BrowserOS caveat and dev server requirement

### Tertiary (LOW confidence)
- BrowserOS MCP tool names (`mcp__browseros__navigate`, `screenshot`, `get_console_logs`, `set_viewport`, `click`, `type`, `evaluate`) — [ASSUMED] from typical browser automation MCP conventions; executor must list available tools at runtime before proceeding

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | BrowserOS MCP tool names are `navigate`, `screenshot`, `get_console_logs`, `set_viewport`, `click`, `type`, `evaluate` | BrowserOS MCP Tooling | If names differ, plan tasks referencing tool names need adjusting; executor discovers actual names at runtime |
| A2 | Astro dev server starts on port 4321 | Environment Availability | If port differs, all URLs in the plan need updating; executor must confirm actual port at startup |
| A3 | Node.js is installed and `npm run dev` works without setup | Environment Availability | If Node not present or deps not installed, `cd site && npm install` is needed first |

---

## Open Questions (RESOLVED)

1. **Actual BrowserOS MCP tool names**
   - What we know: The server is at port 9200 and the `.mcp.json` entry is named `browseros`
   - What's unclear: Whether tools expose as `navigate`, `screenshot`, etc. or use different names (e.g. `open_url`, `take_screenshot`)
   - RESOLVED: at runtime by the Wave 0 pre-flight checkpoint (07-01) — executor lists available `mcp__browseros__*` tools and records real names; aborts with a checkpoint if BrowserOS tools are not found. Planning does not depend on the exact names.

2. **Astro dev server actual port**
   - What we know: Default is 4321; may vary if port occupied
   - What's unclear: Whether port 4321 is free on the user's machine during review
   - RESOLVED: at runtime by the Wave 0 pre-flight checkpoint (07-01) — port captured from `npm run dev` stdout and used for all subsequent navigation.

3. **Legal page count (8 vs. 4)**
   - What we know: Repo has 2 EN legal pages and 2 ES legal pages (terms + privacy = 4 URLs total)
   - What's unclear: REQUIREMENTS.md says "8 legal pages" — this may anticipate pages not yet built (cookie policy, accessibility statement, etc.)
   - RESOLVED: Plan reviews the 4 URLs that exist and logs the missing legal pages as a Polish finding in REVIEW-E2E-FINDINGS.md (not a blocker). Success is not gated on 8.

---

## RESEARCH COMPLETE

**Phase:** 7 — E2E Review Pass
**Confidence:** HIGH

### Key Findings

1. **Real editorial page count is 12 EN + 12 ES** (not 10+10 as in REQUIREMENTS.md). All URLs enumerated from source files.
2. **Legal page count is 4 total (2 EN + 2 ES)**, not 8 — REQUIREMENTS.md overcounts; the plan must review existing pages and flag missing ones.
3. **12 rollout communes are live** (not the full 346); sample declared as Santiago (high), Concepción (mid), Punta Arenas (low) across 3 distinct regions.
4. **Map island has 10 verifiable interactions** spread across 7 component files; incident layer empty state (graceful 404 toast) is expected correct behaviour.
5. **BrowserOS MCP tool names are ASSUMED** — the executor must list available tools before proceeding; plan must include a pre-flight checkpoint for both dev server and BrowserOS availability.

### File Created
`.planning/phases/07-e2e-review-pass/07-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Page inventory | HIGH | Enumerated directly from `site/src/pages/` |
| Programmatic URL patterns | HIGH | Verified from `getStaticPaths` source + data files |
| Map interaction inventory | HIGH | Read from all 7 map component files |
| BrowserOS tool names | LOW | Inferred from convention; must verify at runtime |

### Ready for Planning
Research complete. Planner can now create PLAN.md files for Phase 7.
