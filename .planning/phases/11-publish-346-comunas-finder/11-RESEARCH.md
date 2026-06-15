# Phase 11: Publish All 346 Comunas + Comuna Finder — Research

**Researched:** 2026-06-15
**Domain:** Astro static-site rollout un-gating + SEO-safe progressive-enhancement directory (findability / internal linking)
**Confidence:** HIGH (all findings verified by reading source + running a real 346-commune build)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Publish all 346 comunas** with CEAD data in both locales (`/commune/[slug]`, `/es/comuna/[slug]`). The gate is `site/src/config/rollout.json` (`enabled[]`, currently 12) read by `loadRolloutCuts()` in `site/src/lib/data.ts:217` (already supports a `ROLLOUT_ALL` env path). Whatever mechanism is chosen must make 346 the **committed, build-default** behavior (CI/Cloudflare build emits all pages), not env-dependent on a developer's machine.
- Low-population comunas DO get a page (excluded from *rankings* per DATA-04, not from existing).
- **Comuna Finder / Directory** (design validated in spike 002): new directory page in both locales (`/communes/` + `/es/comunas/`), linked from primary nav and home. Reuse spike-002 UX: **accent-insensitive search** + **A–Z view** + **by-region view (16 regions)**; each entry links to the comuna page; level dot + rate shown; low-pop tagged. Must be static/indexable HTML — search filter is progressive enhancement over a server-rendered full list (346 links in the HTML for crawlers; JS only filters).
- **Link the tables**: region (`region/[slug]`) and crime-type (`crime/[family]`) pages currently link only the 12 rolled-out comunas and print "Showing N of M — more coming soon." Once 346 ship, link **every** comuna and remove the gating message/partial-row logic (`08-01` rollout-row gating obsolete for this purpose).
- **SEO / thin-content guards**: sitemap (`@astrojs/sitemap`) must include all 346×2 comuna URLs + new directory pages. Each comuna page keeps a unique `<title>`/meta/canonical/hreflang and sufficient unique content. If a comuna genuinely lacks data, it should 404 (not ship an empty page).
- **Verification**: `npm run build` emits ~346×2 comuna pages + directory pages; existing + new validators green (route-count, no-orphan-link, sitemap coverage). Spot-check click-through from map / region table / directory.

### Claude's Discretion
- Choice of rollout mechanism (ROLLOUT_ALL committed default vs. expand `enabled[]` vs. invert logic) — research recommends one below.
- Directory page implementation detail (vanilla script vs. tiny island) provided it is SEO-safe and degrades without JS.
- Whether/where to add a "Comunas" nav entry and home link.

### Deferred Ideas (OUT OF SCOPE)
- Comuna-page hub-and-spoke cross-linking (map/region/similar/news links + breadcrumb) → **Phase 12**.
- OpenGraph/Twitter + ItemList/BreadcrumbList JSON-LD on directory/rankings → **Phase 13**.
- Per-comuna "recent incidents" populated with real data → **Phase 16**.
- Home redesign → **Phase 12** (Phase 11 only *links* to the directory from the existing home).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMU-01 | Publish a page for all 346 comunas (EN `/commune/[slug]`, ES `/es/comuna/[slug]`); map/ranking clicks reach real pages (0 dead-links/404); sitemap includes all comuna URLs in both locales. | Rollout mechanism (§Architecture Pattern 1); build verified to emit 346 EN + 346 ES + 770 sitemap `<loc>` entries with `ROLLOUT_ALL=true`. |
| COMU-02 | Searchable comuna directory (accent-insensitive search + A–Z + by-region/16), linked from nav and home; any comuna reachable in ≤2 interactions; includes low-population comunas. | SEO-safe progressive-enhancement directory (§Architecture Pattern 2); spike-002 finder.html porting plan; `cut//1000` region grouping. |
| COMU-03 | Region/crime ranking tables link every comuna (no "Showing N of M"); thin-content mitigated (unique data/prose + title/meta/canonical/hreflang); validator asserts ≈346×2 pages + zero internal links to ungenerated comuna slugs. | Un-gate ranking tables (§Architecture Pattern 3); proseEngine verified 890+ words even for smallest low-pop comunas; new validator spec (§Validation Architecture). |
</phase_requirements>

## Summary

This phase is **un-gating + a directory + linking + a validator**, not building pages. The comuna page templates (`commune/[slug].astro`, `es/comuna/[slug].astro`), the render path, the prose engine, the data (346 comunas in `data/cead/meta/index.json`, every one with a complete CEAD series), and even the `ROLLOUT_ALL` code path and sitemap filter **already exist and work**. I verified this by running an actual `ROLLOUT_ALL=true npm run build`: it produced **770 pages** (346 EN + 346 ES comunas + region/crime/editorial), a sitemap with **346 EN + 346 ES comuna `<loc>` entries**, and even the three smallest low-population comunas (Antártica, Río Verde, Laguna Blanca) rendered **890–910 words** of unique prose. Thin-content risk is therefore LOW and no comuna needs to 404 (verified: 0 missing data files, 0 empty series across all 346).

The one **material risk** is **build time**. The full 346 build took **~9.4 min wall-clock locally (Astro self-reports 8m 8s)**, and CI/Cloudflare both enforce a **20-minute timeout** (`.github/workflows/ci.yml` has `timeout-minutes: 20`; Cloudflare Pages build timeout is 20 min). The build runs `npm run build` then the full validator suite sequentially, and the validators scan all 692 commune HTML files. The root cause is an O(n²) data-loading pattern: `data.ts` has **zero memoization**, so each of the 692 commune pages re-reads ~700–1000 commune JSON files from disk (`loadNationalAverage`, `loadRegionalAverage`, `nearestComparable`, per-page `allRates`, and proseEngine all re-load the full index). A small memoization layer in `data.ts` is the highest-leverage change to keep the build safely inside the 20-min envelope.

**Primary recommendation:** (1) Make 346 the committed default by setting **`ROLLOUT_ALL=true` in the build environment** (`package.json` build script + CI + Cloudflare) — it is the smallest, already-supported, fully-reversible flip and avoids editing a 346-line `rollout.json`. (2) Add **build-time memoization** to `data.ts` loaders before/alongside the flip to keep the build under 20 min. (3) Build the directory as a server-rendered full 346-link list (A–Z + region sections in the static HTML) with a vanilla `<script>` (no island) for filter/view-toggle. (4) Un-gate the ranking tables by removing the `loadRolloutCuts()` row-filter. (5) Add a no-orphan-link + route-count + sitemap-coverage validator.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Comuna page generation (346×2) | Build (Astro `getStaticPaths`) | — | Pre-rendered static HTML; SEO mandate. No client tier. |
| Rollout gate | Build config (`rollout.json` / `ROLLOUT_ALL` env) | — | Determines which paths `getStaticPaths` emits. |
| Directory full list (A–Z + region) | Build (server-rendered `.astro`) | Browser (filter only) | Links must be in crawlable HTML; JS is enhancement-only. |
| Directory search / view toggle | Browser (vanilla `<script>`) | — | Pure client interaction; degrades to full visible list with no JS. |
| Ranking-table comuna links | Build (`.astro` templates) | — | Static `<a href>`; remove rollout row-filter. |
| Sitemap coverage | Build (`@astrojs/sitemap` filter) | — | `ROLLOUT_ALL` path already returns all URLs. |
| Coverage / orphan-link validation | Build/CI (`scripts/validate/*.mjs`) | — | Post-build dist inspection; no runtime. |

## Standard Stack

No new packages required. This phase uses only what is already installed and verified in `site/package.json`.

### Core (already installed — versions verified in package.json 2026-06-15)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| astro | 6.4.6 | Static generation, `getStaticPaths` | Already the project framework; pre-renders all 346×2 comuna pages to indexable HTML. `[CITED: site/package.json]` |
| @astrojs/sitemap | 3.7.3 | Sitemap with i18n + `filter` | Already wired in `astro.config.mjs`; `ROLLOUT_ALL` branch already emits all comuna URLs. `[VERIFIED: ran build, 770 locs]` |
| @astrojs/react | 5.0.7 | React islands | NOT needed for the directory — directory uses vanilla `<script>`, not React (avoids loading React JS on a content page, per CLAUDE.md "no `client:load` on heavy islands"). `[CITED: site/package.json]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | — | Accent-insensitive search | Implemented inline with `String.prototype.normalize('NFD').replace(/[̀-ͯ]/g,'')` — the exact pattern already proven in `spike-002/finder.html`. No library. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla `<script>` directory filter | React island (`client:visible`) | React island ships ~40KB+ JS to a content/SEO page for trivial filter logic; violates CLAUDE.md island guidance. Vanilla script is ~30 lines, zero deps. **Use vanilla.** |
| `ROLLOUT_ALL=true` env default | Expand `rollout.json enabled[]` to 346 | Expanding the array means a 346-line config churn + must update the `=== 12` hard assertion in `rollout.mjs:34`. ROLLOUT_ALL is a 1-line, already-supported, reversible flip. **Use ROLLOUT_ALL.** |
| `ROLLOUT_ALL=true` env default | Invert logic (346 default, rollout = subset) | Cleaner long-term but touches `loadRolloutCuts`, `astro.config.mjs` filter, and both validators — more surface area for a one-way door we never need to reverse. **Defer; ROLLOUT_ALL is sufficient.** |

**Installation:** None. No `npm install` in this phase.

## Package Legitimacy Audit

> Not applicable — this phase installs **zero** external packages. All work uses existing dependencies (astro 6.4.6, @astrojs/sitemap 3.7.3) already present and verified in `site/package.json`. No registry lookup, slopcheck, or postinstall audit required.

## Architecture Patterns

### System Architecture Diagram

```
data/cead/meta/index.json (346 comunas: cut/name/slug/region_id/population/low_population)
data/cead/comunas/{cut}.json (per-comuna series — all 346 present, 0 empty)
        │
        ▼
  loadIndex() / loadCommune()  ◄──── [ADD memoization here: cache by cut]
        │
        ├──────────────► getStaticPaths() in commune/[slug].astro + es/comuna/[slug].astro
        │                       │
        │                  loadRolloutCuts()  ◄──── ROLLOUT_ALL=true ⇒ returns all 346 cuts
        │                       │
        │                       ▼
        │                346 EN + 346 ES comuna pages (dist/commune/*, dist/es/comuna/*)
        │
        ├──────────────► region/[slug].astro + crime/[family].astro
        │                       │
        │                  [REMOVE] rollout row-filter ⇒ link ALL comunas (no "Showing N of M")
        │
        ├──────────────► NEW: communes/index.astro + es/comunas/index.astro
        │                       │  server-render full 346-link list (A–Z sections + region sections)
        │                       │  + inline <script> (filter / view-toggle / accent-fold)  ← enhancement only
        │
        └──────────────► astro.config.mjs sitemapFilter()  ◄──── ROLLOUT_ALL ⇒ include all comuna URLs
                                │
                                ▼
                         dist/sitemap-0.xml (770 <loc>: 346 EN + 346 ES comunas + rest)

  PageHeader.astro nav  ──[ADD]──► hardcoded /communes/ (EN) + /es/comunas/ (ES) link
  Home pages           ──[ADD]──► link to the directory

  scripts/validate/*.mjs  ──[ADD]──► coverage.mjs: route-count + no-orphan-link + sitemap-coverage
```

### Recommended Project Structure (files this phase touches/adds)
```
site/
├── package.json                         # EDIT: build script → cross-env ROLLOUT_ALL=true astro build
├── astro.config.mjs                     # (no edit needed — ROLLOUT_ALL branch already returns all URLs)
├── src/
│   ├── lib/
│   │   └── data.ts                      # EDIT: add memoization (index + per-cut commune + nat/regional avg)
│   ├── config/
│   │   └── i18n.ts                      # EDIT: add nav_communes + directory page strings (EN+ES)
│   ├── components/
│   │   └── PageHeader.astro             # EDIT: add hardcoded /communes/ + /es/comunas/ nav link
│   └── pages/
│       ├── communes/index.astro         # NEW: EN directory (server-rendered list + vanilla script)
│       └── es/comunas/index.astro       # NEW: ES directory
│       ├── region/[slug].astro          # EDIT: remove rollout row-filter + "Showing N of M" note
│       ├── es/region/[slug].astro       # EDIT: same
│       ├── crime/[family].astro         # EDIT: same
│       └── es/delito/[family].astro     # EDIT: same
└── scripts/validate/
    ├── rollout.mjs                      # EDIT: relax/update the `=== 12` assertion (see Pitfall 1)
    ├── coverage.mjs                     # NEW: route-count + no-orphan-link + sitemap-coverage
    └── all.mjs                          # EDIT: register coverage.mjs in the VALIDATORS array
```

### Pattern 1: Committed full-rollout via `ROLLOUT_ALL` build env (COMU-01)

**What:** `loadRolloutCuts()` in `data.ts:217` already returns all 346 cuts when `process.env.ROLLOUT_ALL === 'true'`. Both comuna route files call `loadRolloutCuts()` identically. The `astro.config.mjs` sitemap filter (line 31, 46–48) also short-circuits to include everything when `ROLLOUT_ALL`. So the flip is purely "set the env var at build time, committed."

**When to use:** This is the recommended mechanism.

**How to commit it (the decision):** Set `ROLLOUT_ALL=true` for the build in a way that lives in the repo, not a dev machine:
```jsonc
// site/package.json — make 346 the committed default
"scripts": {
  "build": "cross-env ROLLOUT_ALL=true astro build"   // add cross-env devDep for Windows-portable env
}
```
`cross-env` is needed because the local dev machine is Windows (PowerShell ignores `VAR=value cmd` syntax); Cloudflare/CI run Linux where `ROLLOUT_ALL=true astro build` would work, but `cross-env` makes the one script portable. `[VERIFIED: env is win32 PowerShell per session context]` — alternatively set the var in CI/Cloudflare dashboard env, but the package.json approach is the single source of truth and satisfies "committed, build-default." Confirm `cross-env` via `npm view cross-env version` before adding (it is a long-established, widely-used package, but treat the name as `[ASSUMED]` until verified per the package-legitimacy rule).

> If the plan prefers zero new devDeps: keep `"build": "astro build"` and set `ROLLOUT_ALL=true` in **both** `.github/workflows/ci.yml` (job env) **and** the Cloudflare Pages project environment variables. Tradeoff: the value then lives in two places outside the repo's package.json and a `npm run build` on a fresh checkout would produce only 12 — weaker "committed default" guarantee. The package.json+cross-env path is preferred.

**Verification artifact:** I ran `ROLLOUT_ALL=true npm run build` → 770 pages, 346 EN + 346 ES comuna dirs, sitemap 770 locs. `[VERIFIED: live build 2026-06-15]`

### Pattern 2: SEO-safe progressive-enhancement directory (COMU-02)

**What:** Server-render the **complete** list of 346 comunas as real `<a href>` links, grouped into BOTH an A–Z structure and a by-region structure in the static HTML, then layer a vanilla `<script>` that toggles which grouping is visible and filters by accent-folded text. Crawlers and no-JS users see all 346 links; JS only hides/shows and highlights.

**When to use:** The directory page. This is the SEO-safe version of `spike-002/finder.html` (which is client-only render — not acceptable for an indexable page).

**Key design (ported from the validated spike):**
- Build data at SSR time from `loadIndex()` enriched with `latestCompleteYearRate(loadCommune(cut))` and `levelForRate(...)` for the level dot. Region grouping uses `cut//1000 → 1..16` (the spike's canonical derivation, sidestepping the CEAD `region_id` quirk; `data.ts:regionFileId` already does the equivalent `Math.floor(n/10)` for ≥20 codes).
- Emit two server-rendered blocks (e.g. `<div data-view="az">` and `<div data-view="region" hidden>`), each containing the full 346 links. Default-visible: A–Z (matches spike).
- Inline `<script>` (no island): handles (1) the search input with `norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase()` (verified in spike line 46), (2) the A–Z / Por región toggle, (3) `<mark>` highlight. With JS off, the input/toggle simply do nothing and the full A–Z list remains visible — graceful degradation.
- Each `<a>` links to the locale-correct comuna path: EN `/commune/{slug}/`, ES `/es/comuna/{slug}/` (hardcoded prefix — see Pitfall 3).
- Low-pop tag: render `<span class="lowpop">baja pob. / low pop.</span>` when `meta.low_population` (spike does this).

**Example (SSR + enhancement skeleton):**
```astro
---
// Source: pattern derived from spike-002/finder.html + existing data.ts loaders
import { loadIndex, loadCommune, latestCompleteYearRate } from '../../lib/data.ts';
import { levelForRate } from '../../lib/colorScale.ts';
const index = loadIndex();
const allRates = index.filter(c => !c.low_population)
  .map(c => latestCompleteYearRate(loadCommune(c.cut))).sort((a,b)=>a-b);
const rows = index.map(c => {
  const rate = latestCompleteYearRate(loadCommune(c.cut));
  return { name: c.name, slug: c.slug, rate, low: c.low_population,
           region: Math.floor(parseInt(c.cut,10)/1000),
           level: levelForRate(rate, allRates) };
}); // 346 rows — ALL rendered in HTML
---
<!-- full 346 links rendered server-side; <script> only filters/toggles -->
```

### Pattern 3: Un-gate ranking tables (COMU-03)

**What:** In `region/[slug].astro` (+ES) and `crime/[family].astro` (+ES), the `displayedRows` filter against `loadRolloutCuts()` is what hides non-rollout comunas and triggers the "Showing N of M — more coming soon" note. Remove the filter so the table maps over the full `rankingRows` and delete the `hiddenCount`/`rollout-note` block.

- `region/[slug].astro`: lines 91–96 (`rolloutCuts` set + `displayedRows` filter + `hiddenCount`) and lines 214–216 (`rollout-note`). Pass full `rankingRows` to `<CommuneRankingTable>`.
- `crime/[family].astro`: lines 100–104 (`rolloutCuts` + `displayedRows` + `hiddenCount`) and lines 242–244 (`rollout-note`). Map the table over `rankingRows` instead of `displayedRows`.
- `CommuneRankingTable.astro` needs **no change** — it already links every row it is given via `communePrefix` (line 39) and handles low-pop marking. Once it receives all rows, it links all comunas. `[VERIFIED: read component]`
- Apply identically to the two ES files (`es/region/[slug].astro`, `es/delito/[family].astro`) for hreflang parity.

**Anti-Patterns to Avoid**
- **Editing the comuna page template content:** Out of scope (CONTEXT: "Do NOT redesign the comuna page template"). Only `getStaticPaths` behavior changes, and that changes via the env flip — no template edit needed.
- **Rendering the directory list client-side only** (as the spike does): kills SEO. The 346 links MUST be in server HTML.
- **Using `getRelativeLocaleUrl()` for the directory/comuna links:** it does not translate ES slugs and would emit broken `/es/communes/` (see Pitfall 3).
- **Expanding `rollout.json` to 346:** churny and trips the `=== 12` assertion; use the env flip.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Which comunas to publish | Custom path list | Existing `loadRolloutCuts()` + `ROLLOUT_ALL` | Already implemented and used identically by both routes. |
| Sitemap coverage of 346×2 | Custom sitemap writer | Existing `@astrojs/sitemap` + the `ROLLOUT_ALL` filter branch | Already emits all 770 locs; verified. |
| Region grouping for the directory | Re-deriving region from CEAD `region_id` | `cut//1000` (spike) or `regionFileId()` (data.ts) | The `region_id` field stores CEAD provincial codes; both existing helpers already resolve the real 1–16 region. |
| Accent-insensitive search | A fuzzy-search library (Fuse.js etc.) | `normalize('NFD').replace(/[̀-ͯ]/g,'')` | Validated in spike; substring match on 346 items is instant; zero deps, zero JS shipped beyond ~30 lines. |
| Per-comuna unique prose | Anything | Existing `proseEngine.buildCommuneProse()` | Already generates 890+ unique words for even the smallest low-pop comuna. |

**Key insight:** Almost every capability this phase needs already exists in the codebase and was built anticipating the 346 rollout (the `ROLLOUT_ALL` branch, the `EXPECT_ALL` validator mode, the sitemap filter). The phase is wiring, not building.

## Runtime State Inventory

> This is primarily a build-config + new-page phase, not a rename/migration. There is **no stored runtime data, live service config, OS-registered state, or secret** keyed to the rollout. The only "state" is build configuration.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — comuna data already complete for all 346 (verified: 0 missing files, 0 empty series). | None. |
| Live service config | **Cloudflare Pages build env** — if the chosen mechanism is "set ROLLOUT_ALL in the CF dashboard" rather than package.json, that value lives in the CF project settings (NOT git). | Prefer package.json+cross-env so it IS in git; otherwise document the CF/CI env var as a go-live step. |
| OS-registered state | None. | None. |
| Secrets/env vars | `ROLLOUT_ALL` is a build flag, not a secret. No secret changes. | None. |
| Build artifacts | `site/dist/` is gitignored (verified `git check-ignore site/dist` → ignored); regenerated each build. After the flip, dist grows from 504 → ~1,172 files. | None (regenerated). |

**Nothing found in categories Stored data / OS state / Secrets** — verified by reading data files and `git check-ignore`.

## Common Pitfalls

### Pitfall 1: `rollout.mjs` hard-asserts `enabled.length === 12`
**What goes wrong:** `scripts/validate/rollout.mjs:34` asserts `rollout.enabled.length === 12`. The default (non-`EXPECT_ALL`) validator path also asserts `dist` commune count equals `rollout.enabled.length` (12). After the flip, the build emits 346 but `rollout.json` still has 12 → validator fails unless run with `EXPECT_ALL=true`.
**Why it happens:** The validator was written for the 12-CUT staged rollout; `EXPECT_ALL=true` is an opt-in mode, not the default.
**How to avoid:** When the build default becomes 346, update `rollout.mjs` so the **default** expectation is 346 (or have `all.mjs` pass `EXPECT_ALL=true` through to it). Relax the `=== 12` config assertion to "≥ 1 and ≤ 346" (or drop it — `enabled[]` is now irrelevant when `ROLLOUT_ALL=true`). Keep the EN/ES reciprocity + count-parity assertions.
**Warning signs:** `rollout.mjs: FAILED` with "expected 12" after the flip.

### Pitfall 2: Build time approaches the 20-min CI/Cloudflare timeout
**What goes wrong:** The 346 build is ~9.4 min wall-clock locally (Astro 8m 8s). CI then runs the full validator suite (which re-scans 692 commune HTML files + reruns the prose self-test via tsx). `ci.yml` has `timeout-minutes: 20`; Cloudflare Pages free tier has a **20-min build timeout** (per CLAUDE.md). CI machines are often slower than a dev laptop. This is the real risk in the phase.
**Why it happens:** `data.ts` has **zero memoization** (verified — no cache/memo/Map). Each commune page re-reads ~700–1000 commune JSON files: `loadNationalAverage` (all ~256 eligible), `loadRegionalAverage`, `nearestComparable`, the page's own `allRates` (all eligible again), and `proseEngine` independently re-calls all three. Across 692 pages that is ~500k `readFileSync`+`JSON.parse`.
**How to avoid:** Add module-level memoization in `data.ts`:
- Cache `loadIndex()` result (read once).
- Cache `loadCommune(cut)` per cut in a `Map`.
- Memoize `loadNationalAverage()` and `loadRegionalAverage(regionId)` (they are pure given the data; compute once each).
This is safe at build time (data is static within a build) and should cut the build by a large multiple. Measure before/after; target the full build + validate well under ~12 min to leave CI headroom.
**Warning signs:** Per-page render times ~1s (observed); CI job nearing 20 min; Cloudflare "build exceeded time limit."

### Pitfall 3: `getRelativeLocaleUrl()` does NOT translate ES slugs
**What goes wrong:** Using `getRelativeLocaleUrl('es', '/communes/')` emits `/es/communes/` — a 404 — because Astro i18n only prefixes the locale, it does not localize the slug. Same trap for the comuna links.
**Why it happens:** Documented project pitfall (CLAUDE.md memory: "i18n localized-slug pitfall"); `PageHeader.astro:22-25` already works around it for `/es/mapa/` and `/es/metodologia/` by hardcoding per-locale paths.
**How to avoid:** Hardcode the directory and comuna paths per locale, exactly as `slugMaps.ts` and `CommuneRankingTable.astro:39` already do:
- Directory: EN `/communes/`, ES `/es/comunas/`.
- Comuna links inside the directory: EN `/commune/{slug}/`, ES `/es/comuna/{slug}/`.
- Nav link (PageHeader): `const communesHref = locale === 'en' ? '/communes/' : '/es/comunas/';`
**Warning signs:** Language-switcher or nav links to the directory 404 in ES; hreflang validator flags missing partner.

### Pitfall 4: hreflang/parity asymmetry between the two directory pages
**What goes wrong:** If the EN and ES directory pages set `enPath`/`esPath` inconsistently, `hreflang.mjs` fails or the language switcher breaks.
**How to avoid:** Both directory pages must declare the same pair: `enPath="/communes/"`, `esPath="/es/comunas/"`, passed to `BaseLayout` (which injects canonical + hreflang). Mirror the existing region/crime page convention.
**Warning signs:** `hreflang.mjs` reports a non-reciprocal pair for the new routes.

## Code Examples

### Memoization for build-time loaders (Pitfall 2 fix)
```typescript
// Source: pattern for site/src/lib/data.ts — build-time only, data is static per build
let _indexCache: CommuneMeta[] | null = null;
export function loadIndex(): CommuneMeta[] {
  if (_indexCache) return _indexCache;
  _indexCache = JSON.parse(readFileSync(path.join(DATA_ROOT,'meta','index.json'),'utf-8'));
  return _indexCache;
}

const _communeCache = new Map<string, CommuneData>();
export function loadCommune(cut: string): CommuneData {
  const hit = _communeCache.get(cut);
  if (hit) return hit;
  /* ...existing read + enrich... */
  _communeCache.set(cut, enriched);
  return enriched;
}

let _natAvg: number | null = null;
export function loadNationalAverage(): number {
  if (_natAvg !== null) return _natAvg;
  /* ...existing computation... */
  _natAvg = result; return _natAvg;
}
const _regAvg = new Map<string, number>(); // memoize loadRegionalAverage(regionId)
```

### Accent-insensitive filter (directory enhancement — verified in spike)
```javascript
// Source: .planning/spikes/002-comuna-finder/finder.html line 46
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
// "vina" matches "Viña del Mar"; "nunoa" matches "Ñuñoa"
```

### Sitemap filter (already correct — no edit needed)
```javascript
// Source: site/astro.config.mjs:31,46-48 — ROLLOUT_ALL short-circuits to include all
const ROLLOUT_ALL = process.env.ROLLOUT_ALL === 'true';
function sitemapFilter(url) { if (ROLLOUT_ALL) return true; /* ...staged logic... */ }
```

## State of the Art

| Old (12-CUT staged) | New (346 full) | When | Impact |
|---------------------|----------------|------|--------|
| `rollout.json enabled[]` = 12 + `ROLLOUT_ALL` opt-in for special builds | `ROLLOUT_ALL=true` committed build default | This phase | 346×2 comuna pages ship; rollout.json becomes vestigial. |
| Ranking tables gate rows by rollout + "Showing N of M" | All comunas linked | This phase | `08-01` rollout-row gating obsolete. |
| Directory does not exist | Static + enhanced directory at `/communes/`, `/es/comunas/` | This phase | New findability hub; SEO internal-link distribution to 692 pages. |

**Deprecated/obsolete after this phase:**
- The "Showing N of M — more coming soon" note and `hiddenCount`/`displayedRows` logic in all 4 ranking templates.
- The `=== 12` assertion in `rollout.mjs` (must be updated).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `cross-env` is the right cross-platform way to set the build env var on this Windows dev machine. | Pattern 1 | Low — fallback is CI/CF dashboard env var; verify `cross-env` via `npm view` before adding. |
| A2 | Build-time memoization is safe because data is immutable within a single build. | Pitfall 2 | Low — Astro build is single-pass over static JSON; no data mutation during build. |
| A3 | Cloudflare Pages build timeout is 20 min (from CLAUDE.md). | Summary, Pitfall 2 | Medium — if CF tightened it, the time risk is worse; the memoization mitigation applies regardless. `[CITED: CLAUDE.md Cloudflare limits table]` |
| A4 | No comuna needs to 404 (all 346 have complete data). | Summary, COMU-01 | Low — verified live: 0 missing files, 0 empty series. `[VERIFIED]` |

## Open Questions

1. **Where does the home link to the directory?**
   - What we know: CONTEXT says directory is "linked from the primary nav and the home."
   - What's unclear: The home redesign is Phase 12; Phase 11 must add a link to the existing home without redesigning it.
   - Recommendation: Add a minimal, unobtrusive link/CTA to the directory on the existing home pages (EN `/`, ES `/es/`) and the nav. Defer any hero/search redesign to Phase 12.

2. **Should `rollout.json` be deleted or kept?**
   - What we know: With `ROLLOUT_ALL=true` it is ignored by `loadRolloutCuts` and the sitemap filter.
   - Recommendation: **Keep** it (it is still referenced by `structure.mjs` REQUIRED_FILES and the non-ALL validator path); just don't rely on it. Update `rollout.mjs` assertions. Removing it is a larger change with no benefit this phase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build | ✓ | 20+ (CI pins 20) | — |
| astro | build | ✓ | 6.4.6 | — |
| @astrojs/sitemap | sitemap | ✓ | 3.7.3 | — |
| cross-env (proposed) | portable build env var | ✗ (not yet installed) | — | Set `ROLLOUT_ALL` in CI + CF dashboard instead |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** `cross-env` (optional; fallback = CI/CF env var). Verify with `npm view cross-env version` before adding.

## Validation Architecture

> `workflow.nyquist_validation` not explicitly false → section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Node-native assert-based validators in `site/scripts/validate/*.mjs` (no Jest/Vitest for the site) + `pytest` for the pipeline (not relevant here). |
| Config file | none — plain `.mjs` scripts run via `node` |
| Quick run command | `node scripts/validate/rollout.mjs` (post-build) |
| Full suite command | `npm run build && node scripts/validate/all.mjs` (run from `site/`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMU-01 | 346 EN + 346 ES comuna pages emitted; EN/ES reciprocal | route-count | `node scripts/validate/rollout.mjs` (update default to 346) | ✅ (needs Pitfall-1 edit) |
| COMU-01 | sitemap includes all 346×2 comuna URLs | sitemap-coverage | `node scripts/validate/coverage.mjs` (new) | ❌ Wave 0 |
| COMU-01/03 | **zero internal links to ungenerated comuna slugs** (no orphans) | no-orphan-link | `node scripts/validate/coverage.mjs` (new) | ❌ Wave 0 |
| COMU-02 | directory pages emitted EN+ES with all 346 links in static HTML | route+content | `coverage.mjs` asserts `/communes/`, `/es/comunas/` exist + contain ≥346 `/commune/` (resp. `/es/comuna/`) hrefs | ❌ Wave 0 |
| COMU-03 | ranking tables contain no "Showing N of M" note | content-grep | `coverage.mjs` greps dist region/crime pages for the obsolete string (must be absent) | ❌ Wave 0 |
| COMU-03 | each comuna page ≥500 words + unique meta | thin-content | `node scripts/validate/commune.mjs` (existing, already runs over all dist comuna pages) | ✅ |

### New validator: `coverage.mjs` (the COMU-03 "build validator")
Assert, against `dist/`:
1. **Route count:** `dist/commune/*` dir count === `dist/es/comuna/*` dir count === 346 (= `loadIndex().length`).
2. **No-orphan-link (inverse of today's bug):** scan every `dist/**/*.html`, extract every `href="/commune/{slug}/"` and `href="/es/comuna/{slug}/"`, and assert each `{slug}` corresponds to a generated page (i.e. `dist/commune/{slug}/index.html` exists). Fail listing any orphan. This is the assertion that proves "0 dead-links."
3. **Sitemap coverage:** parse `dist/sitemap-0.xml`; assert it contains exactly 346 `…/commune/` and 346 `…/es/comuna/` `<loc>` entries, and that the directory URLs are present.
4. **Directory completeness:** assert `dist/communes/index.html` contains ≥346 distinct `/commune/` hrefs (links are in the static HTML, proving SEO-safe), same for ES.

Register `coverage.mjs` in `all.mjs`'s `VALIDATORS` array.

### Sampling Rate
- **Per task commit:** `node scripts/validate/rollout.mjs` (fast, post-build) for un-gate tasks; `node scripts/validate/coverage.mjs` for directory/orphan tasks.
- **Per wave merge:** `npm run build && node scripts/validate/all.mjs`.
- **Phase gate:** full suite green + manual browse of directory in both locales + click-through from map/region table to a previously-orphaned comuna.

### Wave 0 Gaps
- [ ] `site/scripts/validate/coverage.mjs` — route-count + no-orphan-link + sitemap-coverage + directory-completeness (covers COMU-01/02/03).
- [ ] Edit `site/scripts/validate/rollout.mjs` — make 346 the default expectation; relax `=== 12` config assertion (Pitfall 1).
- [ ] Edit `site/scripts/validate/all.mjs` — register `coverage.mjs`.
- [ ] (Recommended, not strictly a test) `data.ts` memoization to keep build+validate under the 20-min CI/CF timeout (Pitfall 2).

## Security Domain

> `security_enforcement` not configured false; but this phase has a narrow, low-risk surface.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Static site, no auth. |
| V3 Session Mgmt | no | No sessions. |
| V4 Access Control | no | All content public. |
| V5 Input Validation | yes (light) | Directory search input is **client-side only**, never sent to a server; render filtered text via `textContent`/safe interpolation. The spike highlights matches by string-slicing into `innerHTML` with a `<mark>` — port carefully: the comuna `name` is from trusted build data (CEAD index), not user input, so XSS risk is minimal, but the **user's query** is inserted into `<mark>`. Insert the query via the matched substring of the trusted name (as the spike does at line 47), NOT the raw query, to avoid reflecting arbitrary input into the DOM. |
| V6 Cryptography | no | None. |

### Known Threat Patterns for static Astro + inline script
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| DOM-based XSS via search-highlight `innerHTML` | Tampering | Highlight by slicing the trusted comuna name around the match index (spike pattern), not by injecting the raw query string; or use `textContent` + CSS. |
| Crawl-budget waste from non-canonical URLs | — | Sitemap already canonical; directory links use canonical `/commune/{slug}/` paths. |

## Sources

### Primary (HIGH confidence — read source / ran build)
- `site/src/lib/data.ts` — `loadRolloutCuts()` + `ROLLOUT_ALL` path (L217), no memoization, O(n²) loaders.
- `site/src/config/rollout.json` — 12 enabled cuts.
- `site/src/pages/commune/[slug].astro` + `es/comuna/[slug].astro` — `getStaticPaths` via `loadRolloutCuts()`.
- `site/src/pages/region/[slug].astro` (L91-96, 214-216) + `crime/[family].astro` (L100-104, 242-244) — rollout row-filter + "Showing N of M".
- `site/src/components/CommuneRankingTable.astro` — links every row given; needs no change.
- `site/src/lib/proseEngine.ts` — unique per-comuna prose (verified 890+ words for smallest low-pop).
- `site/astro.config.mjs` — sitemap `ROLLOUT_ALL` filter (already correct).
- `site/scripts/validate/{all,rollout,commune,structure}.mjs` — validator patterns + `EXPECT_ALL` mode + `=== 12` assertion.
- `site/src/components/PageHeader.astro` (L22-25) + `slugMaps.ts` — localized-slug hardcoding pattern.
- `.github/workflows/ci.yml` — `timeout-minutes: 20`, `npm run build` + `all.mjs`.
- `.planning/spikes/002-comuna-finder/{README.md,finder.html}` — validated directory UX + accent-fold.
- **Live build run** (`ROLLOUT_ALL=true npm run build`): 770 pages, 346 EN + 346 ES comuna dirs, 770 sitemap locs, ~9.4 min wall-clock; 1,172 dist files; smallest low-pop comunas 890-910 words; 0 missing data / 0 empty series across 346. `[VERIFIED 2026-06-15]`

### Secondary (MEDIUM)
- CLAUDE.md — Cloudflare Pages limits (20k files / 20-min build), island guidance, i18n approach.
- `.planning/MILESTONES.md` — prior "full 346 ROLLOUT_ALL build verified under 20K limit" note.

### Tertiary (LOW)
- `cross-env` package recommendation — `[ASSUMED]`, verify via `npm view cross-env version` before adding.

## Metadata

**Confidence breakdown:**
- Rollout mechanism: HIGH — code path exists and was exercised in a live build.
- Build-cost finding: HIGH — measured (~9.4 min) against a known 20-min budget; root cause (no memoization) verified.
- File-limit safety: HIGH — 1,172 dist files measured vs 20,000 limit.
- Thin-content / no-404: HIGH — verified 0 missing/0 empty + 890+ word floor.
- Directory pattern: HIGH — spike validated UX; SSR-full-list + vanilla-script is a standard Astro progressive-enhancement pattern matching the codebase's island discipline.
- Validator spec: HIGH — mirrors existing `rollout.mjs`/`commune.mjs` conventions.

**Research date:** 2026-06-15
**Valid until:** ~2026-07-15 (stable; the only moving piece is the Cloudflare build-timeout number — recheck if CF changes free-tier limits).
