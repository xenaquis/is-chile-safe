# Phase 27: News Facet Data Model - Research

**Researched:** 2026-07-30
**Domain:** Astro build-time data derivation (TypeScript), zero new frontend JS/dependencies
**Confidence:** HIGH (all core claims verified directly against the checked-out codebase)

## Summary

Phase 27 is a pure build-time data-derivation problem inside an already-proven pattern. `news.astro` and `es/noticias.astro` already read `current.json` via `process.cwd()` and already group incidents by month at build time (`monthGroups`) — this phase generalizes that exact pattern into a shared `site/src/lib/newsFacets.ts` module that both pages import, adds region/family/time-window facets with counts, and stops the two pages from being able to drift (they are currently near-byte-identical copy-pasted files with zero shared facet logic — that is the actual drift risk this phase closes).

Nothing in this phase touches the Python pipeline, `data/`, or CEAD's 7-key `FAMILY_KEYS`. The 8th news-only family `sexuales` is already fully wired end-to-end in `pipeline/news/schema.py` (`VALID_FAMILIES = FAMILY_KEYS | {"sexuales"}`) and in `site/src/lib/familyDefs.ts` (`FAMILY_LABELS_EN/ES` already contain `sexuales`), so Phase 27 only needs to *consume* that existing vocabulary for counts — no new labels need inventing. Region resolution requires no new derivation code at all: `data/cead/meta/index.json` (loaded today via `loadIndex()` in `site/src/lib/data.ts`) already carries a per-commune `region_id` field that was itself computed by the pipeline's CUT-length-aware `region_id_from_cut()` — the facet module should map `incident.cut -> region_id` via that existing index, not reimplement CUT-length math.

The only genuinely new design decision is the time-window semantics (what "today" means in a cron-built static site) and the internal shape of the facet index consumed by Phase 28. Both are addressed below with a recommendation.

**Primary recommendation:** Build `site/src/lib/newsFacets.ts` as a single default-export function `computeNewsFacets(incidents, index, buildTimestamp)` returning one `NewsFacetIndex` object with `{ byFamily, byRegion, byWindow, byMonth }` sub-indexes, each an array of `{ key, count }` (plus label lookups delegated to existing `familyDefs.ts` and `data.ts` region names) — mirroring the existing `loadIndex()`/`loadCommune()` module style (plain exported functions + memoization) rather than a class or multiple small modules, because Phase 28 will need one deterministic snapshot per build, not a stateful service.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read `current.json` + monthly archive | Frontend Server (SSR/SSG, Astro build) | — | Already the pattern in `news.astro`/`noticias.astro`; `process.cwd()`-based, build-time only |
| Compute facet counts (family/region/window/month) | Frontend Server (SSR/SSG) | — | Pure derivation over existing schema fields; no persistence, no new data artifact (FACET-06) |
| CUT → region resolution | Frontend Server (SSR/SSG), via `data/cead/meta/index.json` | Database/Storage (index.json is the source of truth, written by the pipeline) | Region derivation logic itself lives in the pipeline (`region_id_from_cut`, Python); the site tier only *reads* the already-resolved `region_id` — it must never re-derive from CUT length independently, to avoid a second source of truth |
| Facet vocabulary (8 news families incl. `sexuales`) | Frontend Server (SSR/SSG), via `familyDefs.ts` | Pipeline (`pipeline/news/schema.py` VALID_FAMILIES) | Both tiers already independently define the news family superset; Phase 27 must not add a third definition — it consumes `familyDefs.ts` labels and infers the *value* set from data seen (see Pitfall below) |
| Facet UI / filtering interaction | Browser / Client | — | Explicitly Phase 28 scope — NOT Phase 27. Phase 27 ships zero UI, only the data module |
| Query-param state (`?family=&region=&window=`) | Browser / Client | — | Phase 28 scope; Phase 27's module has no knowledge of URLs |

## User Constraints

No CONTEXT.md exists for this phase (autonomous run, `skip_discuss: true` per `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`). The directive itself is the decision source of record; the locked decisions below come from `.planning/REQUIREMENTS.md` "Locked decisions" and the Phase 27 roadmap entry — treat them with identical authority to a CONTEXT.md `## Decisions` section.

### Locked Decisions (from REQUIREMENTS.md / ROADMAP.md — do not reopen)

- Facet URL strategy: **query params only** (`?family=&region=&window=`) on the existing `/news/` + `/es/noticias/`. Never new indexable facet URLs.
- Facet computation: **Astro build time**, in a shared `site/src/lib/newsFacets.ts`, reading data via `process.cwd()`.
- `data/` is **read-only** this milestone — no new derived JSON committed, no facet artifact under `site/**`.
- CEAD's `FAMILY_KEYS` **stays at 7** — `sexuales` is news-only, never added to the CEAD family list.
- No new shipped frontend JS, no new dependency (facet computation uses only Node built-ins + existing `site/src/lib` modules).
- `region_id` on `data/cead/meta/index.json` is pre-verified present — do not re-research its existence, only confirm the read path.

### Claude's Discretion (research-informed recommendations below)

- Exact shape/module boundary of `newsFacets.ts` (single export vs. per-facet exports) — Phase 28 is the only consumer, so optimize for its needs; see "Don't Hand-Roll" / Architecture sections.
- "Today" semantics for the day-granularity time window — see Common Pitfalls, Pitfall 1.
- Whether facet counts span `current.json` only or `current.json + archive` — see Open Questions.
- Whether to add an optional `facets.mjs` validator to the suite — assessed below; recommendation is **yes, add a minimal one**.

### Deferred Ideas (OUT OF SCOPE for Phase 27 — do not implement)

- Any filter/typeahead/query-param UI, empty-state rendering, clustered-event cards — all Phase 28 (NEWSUI-01..07).
- Pre-rendered facet URLs (region × family × time) — explicitly rejected project-wide (thin content, file-budget risk).
- Heat-map/density, severity score, "breaking" badges — rejected project-wide, unrelated to faceting anyway.
- Map control-shell changes, `?region=` deep link on the map — Phase 30 (MAPSH-04), not Phase 27. The map's `?region=` deep link and this phase's news facet `?region=` query param are two independent pieces of state on two different pages; do not conflate them or attempt to share implementation.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FACET-01 | Shared `newsFacets.ts` computed at build time from `current.json` + archive, read via `process.cwd()`, consumed identically by both locale pages | Confirmed exact current per-page duplication in `news.astro`/`noticias.astro` (identical `dataPath`, `monthGroups`, `getCommuneInfo`, `safeUrl` logic) — this is the precise drift this phase must eliminate. Existing `process.cwd()` pattern documented and quoted below. |
| FACET-02 | Day-granularity presets (today/7d/30d) + monthly archive access; sparse days rolled up | See Pitfall 1 (build-timestamp vs newest-incident "today") and recommendation. Monthly archive schema confirmed (`data/incidents/archive/YYYY-MM.json`, same `IncidentRecord`-shaped list, e.g. 84 incidents in `2026-06.json`). |
| FACET-03 | CUT→region via established CUT-length derivation; verified against `index.json` | Confirmed: derivation lives in `pipeline/scrape_cead.py:region_id_from_cut()` (Python, pipeline-only) and its *output* is what `data/cead/meta/index.json` stores per commune (`region_id`, 1-16, verified present in all 346 entries). Site-side code must read `region_id` from the index, never re-derive from CUT length independently — see Don't Hand-Roll. |
| FACET-04 | All 8 news families incl. `sexuales`; CEAD `FAMILY_KEYS` stays at 7 | Confirmed: `pipeline/shared/schema.py` `FAMILY_KEYS` = 7 CEAD families (unchanged). `pipeline/news/schema.py` `VALID_FAMILIES = set(FAMILY_KEYS) | {"sexuales"}` = 8. `site/src/lib/familyDefs.ts` `FAMILY_LABELS_EN/ES` already has entries for all 7 CEAD keys plus `homicidios` and `sexuales` (9 total keys in the label maps; the facet module must use only the 8 values actually present in incident records, not the full label-map superset — see Pitfall 2). |
| FACET-05 | Per-option counts computed at build time, available to UI (e.g. "Robo (14)") | Directly analogous to the existing `monthGroups` `Map<string, incidents[]>` pattern already in both pages; counts are `.length` of each grouped array. |
| FACET-06 | No facet artifact under `site/**`, no new derived JSON committed, `@astrojs/check` clean, validator suite + budget green, no new indexable URLs | Confirmed current `@astrojs/check` baseline is 4 pre-existing errors in `ComparatorPairsLinks.astro` (unrelated component) — NOT 8 as STATE.md's stale carry-over note states; see Pitfall 5. Facet module introduces zero new `.astro` pages, so page-count budget (`avs-b-budget.mjs`, `<18,000` files) is untouched by construction. |
| FACET-07 | Existing validator suite + page-count budget stay green | Validator suite is `site/scripts/validate/all.mjs` running 15 scripts in sequence (not `site/scripts/validators/` — that path does not exist). Confirmed exact list and file locations below. |

## Standard Stack

### Core

No new libraries. This phase uses only:

| Tool | Version | Purpose | Why Standard (for this repo) |
|------|---------|---------|-------------------------------|
| Node.js `fs`/`path` built-ins | (Node 20/22 LTS, per repo `.nvmrc`) | Read `current.json` + archive JSON files | Exact pattern already used in `news.astro`, `noticias.astro`, and every `site/src/lib/*.ts` module — `readFileSync` + `path.resolve(process.cwd(), ...)` |
| TypeScript (Astro's built-in) | Astro 6.4.x toolchain | Type the facet index shape | Every other `site/src/lib/*.ts` module (`data.ts`, `familyDefs.ts`) exports typed interfaces; `newsFacets.ts` must follow the same convention for `@astrojs/check` to catch shape drift |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain TS module with exported pure functions | A class `NewsFacetIndex` with instance methods | Rejected — no other `site/src/lib` module uses a class; would be the only OOP module in a functional-style codebase, adding unnecessary review friction for zero benefit (facet computation runs exactly once per build) |
| Reading `data/incidents/archive/*.json` via `readdirSync` glob | A hardcoded list of month filenames | Rejected — new archive files land automatically every month via cron; a hardcoded list would silently miss new months. Use `readdirSync` + filter on `/^\d{4}-\d{2}\.json$/`. |

**Installation:** None — zero new dependencies, per the locked "New dependencies" decision (`rapidfuzz` + `zizmor` are the *only* new deps for the whole v2.1 milestone, both unrelated to Phase 27).

**Version verification:** N/A — no packages to verify.

## Package Legitimacy Audit

**Not applicable.** Phase 27 introduces zero new npm/pip packages. `package.json`/`requirements.txt` are unchanged by this phase. Skipping the slopcheck/registry-verification protocol accordingly.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │  data/incidents/current.json (1,215 recs)│
                    │  data/incidents/archive/YYYY-MM.json     │
                    │  data/cead/meta/index.json (346 CUTs,    │
                    │    region_id pre-resolved per commune)   │
                    └───────────────┬───────────────────────────┘
                                    │ readFileSync via process.cwd()
                                    │ (build time only — Astro SSG)
                                    ▼
                    ┌─────────────────────────────────────────┐
                    │  site/src/lib/newsFacets.ts (NEW)        │
                    │  computeNewsFacets(incidents, index, now) │
                    │    -> byFamily:  [{key,label_en,label_es,│
                    │                    count}]                │
                    │    -> byRegion:  [{regionId,name,count}]  │
                    │    -> byWindow:  {today,7d,30d} counts    │
                    │    -> byMonth:   [{yearMonth,count}] (arch)│
                    └───────────────┬───────────────────────────┘
                                    │ imported identically by both pages
                    ┌───────────────┴───────────────┐
                    ▼                                ▼
        site/src/pages/news.astro         site/src/pages/es/noticias.astro
        (EN, existing monthGroups          (ES, existing monthGroups
         logic REPLACED by shared           logic REPLACED by shared
         facet computation for counts;      facet computation for counts;
         card rendering unchanged)          card rendering unchanged)
                    │                                │
                    ▼                                ▼
              Static pre-rendered HTML (no client JS added this phase —
              Phase 28 adds the query-param filter UI on top of this data)
```

### Recommended Project Structure

```
site/src/lib/
├── newsFacets.ts        # NEW — this phase's deliverable
├── data.ts               # existing — loadIndex(), region name/slug lookups (reused, not modified)
├── familyDefs.ts         # existing — FAMILY_LABELS_EN/ES (reused, not modified)
site/src/pages/
├── news.astro            # MODIFIED — imports newsFacets.ts instead of inlining monthGroups/family logic
├── es/noticias.astro     # MODIFIED — same import, eliminating the current copy-paste drift
site/scripts/validate/
├── facets.mjs            # NEW (optional, recommended) — asserts facet counts sum correctly, no CEAD FAMILY_KEYS mutation
├── all.mjs               # MODIFIED — registers facets.mjs as validator #16 if added
```

### Pattern 1: Build-time facet computation mirroring `monthGroups`

**What:** A single function that takes the already-loaded incident array (both pages already do this loading step) and returns pre-counted facet buckets, exactly like the existing inline `monthGroups` `Map` build in both pages today.

**When to use:** Any time a static site needs "faceted browsing" without new URLs — compute all facet states at build time, ship the superset, let the client (Phase 28) toggle visibility via CSS/JS over a `data-family`/`data-region`/`data-date` attribute per card, no new HTML fetch.

**Example (verified current pattern from `site/src/pages/news.astro:98-104`):**
```typescript
// Source: site/src/pages/news.astro (existing, to be generalized into newsFacets.ts)
const monthGroups = new Map<string, typeof incidents>();
for (const incident of incidents) {
  const yearMonth = incident.date.slice(0, 7);
  if (!monthGroups.has(yearMonth)) monthGroups.set(yearMonth, []);
  monthGroups.get(yearMonth)!.push(incident);
}
```
This exact reduce-into-Map shape should be reused (not reinvented) for `byFamily` and `byRegion` in `newsFacets.ts`, keyed by `incident.family` and `region_id` respectively instead of `yearMonth`.

### Pattern 2: CUT→region resolution reusing `loadIndex()`

**What:** Build a `cut -> region_id` map once from the already-loaded `CommuneMeta[]` (exact same approach both pages already use for `cutToCommune`).

**Example (verified current pattern, `site/src/pages/news.astro:48-51`, generalize the same way):**
```typescript
// Source: site/src/pages/news.astro (existing pattern to replicate for region_id)
const _index = loadIndex(); // from site/src/lib/data.ts — reads data/cead/meta/index.json
const cutToRegion = new Map<string, string>(
  _index.map((c) => [c.cut, c.region_id])
);
```
`CommuneMeta.region_id` is already typed in `site/src/lib/data.ts:29-36` — no new type needed, no re-derivation from CUT length in the frontend.

### Anti-Patterns to Avoid

- **Re-deriving region from CUT length in TypeScript:** The derivation (`cut.length === 5 ? cut.slice(0,2) : cut.slice(0,1)`) lives in `pipeline/scrape_cead.py:region_id_from_cut()` and its output is already baked into `index.json`. Re-implementing this in `newsFacets.ts` creates a second source of truth that can silently drift from the pipeline's logic (e.g. if a future CUT edge case is patched in Python only). Read `region_id` from `loadIndex()` instead.
- **Hardcoding the 8-family list as a literal array in `newsFacets.ts`:** `familyDefs.ts` does not export a canonical "news families" array (`FAMILY_ORDER` there is CEAD's 7, not the news 8). Do not hand-write `['vida','robos_violentos',...,'sexuales']` in the new module — derive the family key set from **data actually observed** in `incidents` (`new Set(incidents.map(i => i.family))`) so a future 9th family requires zero code change to the facet counter, only a label-map entry. See Pitfall 2.
- **Writing a facet output file to `public/data/` or anywhere under `site/`:** FACET-06 explicitly forbids this. All facet computation must happen in-memory during the Astro build, consumed directly by the `.astro` frontmatter — never serialized to disk.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| CUT → region mapping | A new `regionIdFromCut(cut: string)` TS function | `loadIndex()` from `site/src/lib/data.ts`, keyed lookup on `region_id` | Second source of truth risk (see Anti-Pattern above); the pipeline's Python function is the single authoritative derivation, already baked into `index.json` |
| Region display name/slug | Hardcoded region-name literal map | `loadRegion(regionFileId(regionId)).name` / `.slug`, already exported from `data.ts` | Already exists, already used by every commune/region page; duplicating it invites the exact bilingual-label drift this milestone is trying to close |
| Family EN/ES labels | New label object in `newsFacets.ts` | `FAMILY_LABELS_EN` / `FAMILY_LABELS_ES` from `familyDefs.ts` | Already contains `sexuales` (added in quick-260727-j6z) — reuse guarantees the facet UI never shows a label CEAD/news pages don't already show |
| Recursive month-file listing | Manual filename construction from date math | `readdirSync(archiveDir).filter(f => /^\d{4}-\d{2}\.json$/.test(f))` | Handles gaps (a month with zero incidents/no cron run that month = no file) without assuming a contiguous sequence |

**Key insight:** Every piece of vocabulary and derivation this phase needs (region names, family labels, region_id resolution) already exists in the codebase from prior phases. The entire risk surface of Phase 27 is in *not* re-deriving/duplicating that vocabulary, not in computing anything genuinely new.

## Common Pitfalls

### Pitfall 1: "Today" is ambiguous in a cron-built static site

**What goes wrong:** If "today" means `new Date()` evaluated at build time, a build triggered at 2am for yesterday's news cron run will show 0 "today" incidents even though fresh data landed at 6am the same calendar day pre-deploy, or (worse) a *stale* build (deploy hook not fired, matching the documented `prod-deploy-hook-secret-gap` / cron billing-lapse history in this project) will show a "today" window that is actually several days old with no visual indication of staleness.

**Why it happens:** Static builds bake in a wall-clock timestamp that can diverge from the data's actual freshness. This project has already lost a full week of freshness silently once (`news-cron-billing-outage` memory).

**How to avoid:** Anchor "today" to the **newest incident's date** (`Math.max` over `incidents.map(i => i.date)`), not `new Date()` at build time. Recommendation:
- `windowToday` = incidents where `date === newestIncidentDate`
- `window7d` = incidents where `date >= newestIncidentDate - 7 days`
- `window30d` = incidents where `date >= newestIncidentDate - 30 days` (this equals the full `current.json` set today, since `window_days: 30` is the pipeline's own retention window — confirmed in the file's top-level field)
This makes "today" mean "the most recent day we have data for" — deterministic given fixed input, immune to build-vs-deploy timing skew, and consistent with the existing `freshness.mjs` validator's philosophy (which already treats `generated` staleness as the signal to alert on, separately, at the validator level — not by silently reinterpreting "today").
**Warning signs:** If a future implementation uses `new Date().toISOString().slice(0,10)` anywhere in `newsFacets.ts`, that is the anti-pattern — flag it in code review.

### Pitfall 2: `familyDefs.ts` label-map keys are a superset, not the news family list

**What goes wrong:** `FAMILY_LABELS_EN`/`FAMILY_LABELS_ES` in `familyDefs.ts` contain 9 keys (`vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades, homicidios, sexuales`) — but `homicidios` is a CEAD *subgroup* (101, inside `vida`), never a value of `IncidentRecord.family` in news data. If `newsFacets.ts` iterates `Object.keys(FAMILY_LABELS_EN)` to build the family facet, it will emit a spurious "Homicide (0)" facet option that never has any incidents, confusing FACET-05's promised per-option counts.

**Why it happens:** The label map was built for both CEAD ranking pages (which do show a separate homicide category) and news pages, but the two domains have different valid-value sets.

**How to avoid:** Derive the *set* of family keys from what is actually present in the loaded incidents (`new Set(incidents.map(i => i.family))`), and use `FAMILY_LABELS_EN[key]` only for **display**, never for enumeration.

**Warning signs:** A facet option rendering with count `(0)` for every build — that is diagnostic of iterating the label map instead of the data.

### Pitfall 3: `cut` field type inconsistency (string vs number)

**What goes wrong:** Both existing pages already defensively handle this: `incident.cut` may arrive as either a string or a number in `current.json` (`getCommuneInfo` does `String(incident.cut)` before map lookup). `newsFacets.ts` must apply the same coercion when building the `cut -> region_id` lookup, or region facet counts will silently undercount for any incident whose `cut` came through as a number.

**How to avoid:** Always `String(incident.cut)` before any Map `.get()`/`.has()` call, exactly as the existing pages do.

### Pitfall 4: `existsSync` fallback must be preserved, not weakened

**What goes wrong:** Both pages currently degrade gracefully (`existsSync(dataPath)` guard, empty `incidents = []` fallback) so a missing `current.json` doesn't crash the build. If `newsFacets.ts` is written assuming `current.json` always exists and always parses, and `news.astro`/`noticias.astro` are refactored to call it before the `existsSync` guard, a missing file starts crashing the whole site build instead of rendering the existing "no incidents available" empty state.

**How to avoid:** `computeNewsFacets()` should accept `incidents: IncidentRecord[]` (already-parsed, already-guarded) as a parameter rather than doing its own file I/O for `current.json` — let each page keep its own `existsSync`/try-catch exactly as today, then hand the resulting array (possibly empty) to the facet function. The facet function itself CAN own the archive-file reading (since archive files are a new read this phase introduces) but should apply the identical `existsSync`-per-file / try-catch-per-file discipline.

### Pitfall 5: Stale "8 astro-check errors" baseline in STATE.md

**What goes wrong:** STATE.md's UI-360-diagnostic carry-over note says "8 astro-check errors" — if the Phase 27 plan writes a verification step asserting "no new errors beyond the known 8," and the actual current count is 4 (verified live in this research session: all 4 are `ts(7031)` implicit-any errors in `ComparatorPairsLinks.astro`, unrelated to news/facets), a plan could either falsely fail (if it expects exactly 8) or mask a real regression (if it's lenient about "up to 8").

**How to avoid:** The Phase 27 plan's `@astrojs/check` verification step should assert **the delta introduced by this phase is zero new errors relative to a pre-phase baseline re-measured at kickoff (4 errors, all in `ComparatorPairsLinks.astro`)**, not against the stale "8" figure in old docs.

**Warning signs:** Any verification script hardcoding the literal number 8.

## Code Examples

### Reading the monthly archive directory (new pattern for this phase)

```typescript
// Pattern to add in newsFacets.ts — no existing precedent in this repo reads
// the archive directory yet (both pages only read current.json today).
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import path from 'node:path';

function loadArchiveMonths(archiveDir: string): Array<{ yearMonth: string; incidents: IncidentLike[] }> {
  if (!existsSync(archiveDir)) return [];
  const files = readdirSync(archiveDir).filter((f) => /^\d{4}-\d{2}\.json$/.test(f));
  const result: Array<{ yearMonth: string; incidents: IncidentLike[] }> = [];
  for (const file of files) {
    try {
      const raw = JSON.parse(readFileSync(path.join(archiveDir, file), 'utf-8'));
      result.push({ yearMonth: file.replace('.json', ''), incidents: raw.incidents ?? [] });
    } catch {
      // Malformed archive month — skip, don't crash the build (Pitfall 4 discipline)
    }
  }
  return result;
}
```

### Family facet counting (data-driven, not label-map-driven — closes Pitfall 2)

```typescript
// Source: derived from the verified 8-value VALID_FAMILIES set in
// pipeline/news/schema.py, but the *implementation* reads it from data, not
// from a hardcoded list — see "Don't Hand-Roll" and Pitfall 2.
function computeFamilyFacet(incidents: IncidentLike[]): Array<{ key: string; count: number }> {
  const counts = new Map<string, number>();
  for (const inc of incidents) {
    if (!inc.family) continue;
    counts.set(inc.family, (counts.get(inc.family) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count); // descending, matches ranking-page convention elsewhere in the repo
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-------------------|---------------|--------|
| `news.astro`/`noticias.astro` each inline their own `monthGroups`, `cutToCommune`, `familyLabel` logic | Shared `newsFacets.ts` module imported by both | This phase (27) | Eliminates the exact bilingual-drift risk pattern that has bitten this project before (`news-page-build-path-drift` memory — EN page rendered empty while ES worked, due to a build-path difference between the two near-duplicate files) |

**Deprecated/outdated:** Nothing in this phase deprecates prior work — it is additive/refactor-only over existing, working pages.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | `computeNewsFacets` as a single default export (vs. per-facet named exports) is the right module shape for Phase 28's consumption pattern | Standard Stack / Architecture | Low — Phase 28 hasn't been planned yet; if its needs differ, this is a cheap refactor of an unreleased internal module, not a public API |
| A2 | "Today" should anchor to newest-incident-date rather than build wall-clock | Common Pitfalls, Pitfall 1 | Medium — this is a genuine design choice with no single "correct" answer; if the planner/user prefers wall-clock "today" (matching literal calendar semantics over "freshest data" semantics), FACET-02's "sparse days rolled up" requirement still holds either way, but the exact set of incidents in the "today" bucket would differ. Flagging as ASSUMED because it's an editorial/UX judgment call, not a verified fact. |
| A3 | Adding a `facets.mjs` validator (#16) is worth the effort for Phase 27 specifically (vs. deferring validation entirely to Phase 28 once there's UI to check against) | Validation Architecture | Low — even a minimal facet-count-sanity validator (sum of family-facet counts == total incident count) catches a real class of bug (double-counting, off-by-one in date-window boundaries) cheaply; if skipped, that bug class is only caught by manual eyeballing until Phase 28 ships |

**If this table is empty:** N/A — table is populated; both A2 and A3 need the planner/user to make an explicit call rather than treating this research as settling them.

## Open Questions

1. **Should facet counts span `current.json` only, or `current.json` + full archive?**
   - What we know: `current.json` holds the rolling 30-day window (`window_days: 30`, 1,215 incidents as of this research). The archive holds prior months (`2026-04.json`: exists; `2026-06.json`: 84 incidents) as flat monthly snapshots with the same incident shape.
   - What's unclear: FACET-02 says "time facets expose day-granularity presets (today/7d/30d) **plus monthly-archive access**" — this reads as two separate facet dimensions (a recency window over `current.json`, and a separate archive browse-by-month capability), not one merged pool. But FACET-04/05 (family/region counts) don't specify whether those counts are scoped to `current.json` only or to `current.json` + all loaded archive months.
   - Recommendation: Scope family/region facet **counts** to `current.json` only (matches "recent incidents" framing on both pages' `<h1>`/intro copy, and keeps counts stable/comprehensible as "last 30 days"). Treat the archive strictly as its own `byMonth` facet dimension (a list of past months with their own incident counts, browsable independently) — this matches FACET-02's phrasing exactly ("today/7d/30d... **plus** monthly-archive access", not "today/7d/30d/archive combined into one pool"). The planner should confirm this interpretation explicitly since it affects Phase 28's UI structure (two independent facet groups vs. one unified timeline).

2. **Exact tie-break / sort order for the `byRegion` and `byMonth` facet arrays.**
   - What we know: `byFamily` has an obvious precedent (descending by count, matching every ranking table in this codebase).
   - What's unclear: whether regions should sort by count (busiest region first) or by the canonical 1-16 region-ID order (matching how region pages/`/rankings/` already list "16 linked regions" per the Phase 25 P2-2 fix).
   - Recommendation: Sort `byRegion` by canonical region-ID order (1-16), not by count — this matches the existing `/rankings/` convention (region list ordered 1-16, not by magnitude) and avoids a facet UI where region order visually jumps between builds as counts shift. `byMonth` should sort newest-first, matching the existing `monthGroups` convention already live on both pages.

## Environment Availability

Skipped — this phase has no external tool/service dependencies beyond the already-installed Node.js/Astro toolchain (verified working: `npx astro check` ran successfully in this research session).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Custom Node.js validator scripts (`site/scripts/validate/*.mjs`), run via `node scripts/validate/all.mjs`; no Jest/Vitest for the frontend. Python side uses pytest (`pipeline/tests/`), unaffected by this phase. |
| Config file | None — each validator is a standalone `.mjs` script; `all.mjs` is the aggregator/registry |
| Quick run command | `node site/scripts/validate/freshness.mjs` (or any single validator by filename) for a fast targeted check |
| Full suite command | `cd site && npm run build && npm run validate` (MUST be chained in one command — OneDrive `dist/` desync gotcha) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|---------------|
| FACET-01 | Both `news.astro` and `es/noticias.astro` import and render from the exact same `newsFacets.ts` output (no drift) | build-time assertion / manual diff | `cd site && npm run build && npm run validate` (existing `structure.mjs`/`commune.mjs` pattern can be extended, or covered by new `facets.mjs`) | ❌ Wave 0 — needs new `facets.mjs` or an assertion added to an existing validator |
| FACET-02 | Day-granularity windows exist and sparse days roll up (no empty per-day slots rendered) | validator (HTML absence check) or unit-style assertion in `facets.mjs` | `node site/scripts/validate/facets.mjs` (new) | ❌ Wave 0 |
| FACET-03 | CUT→region resolution matches `index.json` region_id for every incident's CUT | validator assertion (loop all incidents, assert `region_id` lookup succeeds and is in `1..16`) | `node site/scripts/validate/facets.mjs` (new) | ❌ Wave 0 |
| FACET-04 | All family facet values found in data are ⊆ the 8-value `VALID_FAMILIES` set; CEAD `FAMILY_KEYS` (7) unchanged | validator assertion + `pytest` regression already exists on the pipeline side for `FAMILY_KEYS` length (unaffected by this phase, but worth a negative-check: `git diff pipeline/shared/schema.py` is empty) | `node site/scripts/validate/facets.mjs` (new); `git diff --stat pipeline/shared/schema.py` (manual, zero-diff expected) | ❌ Wave 0 for the new assertion; pipeline side already covered by existing pytest suite |
| FACET-05 | Per-option counts sum correctly (no double count / undercount) | validator assertion: `sum(byFamily counts) === total incidents with non-null family` | `node site/scripts/validate/facets.mjs` (new) | ❌ Wave 0 |
| FACET-06 | No facet artifact under `site/**`; no new derived JSON committed | `git status --porcelain` check (manual/CI, not a validator per se) — or a validator that asserts no new files exist under `site/public/data/` beyond the synced CEAD/news mirrors | `git status --porcelain site/` (manual verification step in the plan) | ❌ N/A — procedural check, not a script |
| FACET-07 | `@astrojs/check` clean on new code; full validator suite + budget green; no new indexable URLs | `npx astro check` (delta vs 4-error baseline) + `npm run validate` (15/15, soon 16/16) + `avs-b-budget.mjs` (page count unchanged since no new `.astro` pages) | `cd site && npm run build && npm run validate && npx astro check` | ✅ All exist today; this phase adds zero new pages so `avs-b-budget.mjs`'s page count assertion should be numerically identical pre/post |

### Sampling Rate

- **Per task commit:** Run the single new/modified validator (`facets.mjs` once it exists) plus `npx astro check` for a fast signal.
- **Per wave merge:** Full `cd site && npm run build && npm run validate` (chained, OneDrive-safe).
- **Phase gate:** Full suite green (16/16 validators if `facets.mjs` is added, else 15/15) before `/gsd:verify-work`; `@astrojs/check` delta = 0 new errors vs the 4-error `ComparatorPairsLinks.astro` baseline; pytest suite unaffected (this phase touches zero Python) — re-run once anyway to confirm the 344/1/1(xfail) baseline is undisturbed.

### Wave 0 Gaps

- [ ] `site/scripts/validate/facets.mjs` — new validator covering FACET-01/02/03/04/05 sanity assertions (recommended addition per success criterion 5's mention of an optional facets validator)
- [ ] Register `facets.mjs` in `site/scripts/validate/all.mjs`'s `VALIDATORS` array (becomes #16) and update its header comment listing 1-15 → 1-16
- [ ] No pytest gaps — this phase is 100% TypeScript/Astro, zero Python changes

*Testability note: this phase is frontend-only (TypeScript/Astro build-time code). There is nothing here for pytest to cover — the pipeline (`pipeline/news/*.py`) is completely untouched by Phase 27. All verification is either (a) the custom Node validator suite, (b) `@astrojs/check` for type safety, or (c) a manual `git diff`/`git status` procedural check for the "read-only `data/`, no new artifacts" constraints (FACET-06), which are not really unit-testable claims — they are repo-hygiene assertions best verified by the executor/reviewer inspecting `git status` before commit.*

## Sources

### Primary (HIGH confidence — verified directly in this session)

- `site/src/pages/news.astro` — full file read, quoted verbatim above
- `site/src/pages/es/noticias.astro` — full file read, confirms exact structural parity/drift risk with EN page
- `site/src/lib/data.ts` — full file read; `CommuneMeta.region_id`, `loadIndex()`, `regionFileId()`, `loadRegion()` all confirmed
- `site/src/lib/familyDefs.ts` — full file read; confirmed `FAMILY_ORDER` (7, CEAD-only) vs `FAMILY_LABELS_EN/ES` (9 keys, includes `sexuales` and `homicidios`)
- `pipeline/news/schema.py` — full file read; `VALID_FAMILIES = set(FAMILY_KEYS) | {"sexuales"}` confirmed
- `pipeline/shared/schema.py` — grepped; `FAMILY_KEYS` (7 CEAD-only families) confirmed unchanged/untouched
- `pipeline/scrape_cead.py:49-60` — `region_id_from_cut()` function read in full, confirms CUT-length-aware derivation, Python/pipeline-only
- `data/cead/meta/index.json` — parsed live: 346 entries, `region_id` present on every entry, values span `1`-`16`
- `data/incidents/current.json` — parsed live: `generated`/`window_days`/`incidents` keys confirmed, 1,215 incidents, sample record schema confirmed (`id, cut, lat, lng, title_es, title_en, date, outlet, url, family, slug`)
- `data/incidents/archive/2026-06.json` — parsed live: same shape, 84 incidents, confirms monthly archive schema
- `site/scripts/validate/all.mjs` — full file read; confirmed exact validator list (15 scripts) and location `site/scripts/validate/` (not `site/scripts/validators/`)
- `site/scripts/validate/avs-b-budget.mjs` — partial read; confirms `<18,000` file-count budget mechanism
- `site/scripts/validate/freshness.mjs` — full file read; confirms 3-day staleness gate pattern and module style convention
- `npx astro check` (live run in this session) — confirmed current baseline: 4 errors, all `ts(7031)` implicit-any in `ComparatorPairsLinks.astro`, unrelated to news/facets (corrects STATE.md's stale "8 errors" figure)
- `site/src/config/i18n.ts` — partial read; confirms `I18nStrings` interface convention for future Phase 28 i18n key additions (informational only, not this phase's direct concern)
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` — read in full for locked decisions, Phase 26 outcome, pre-verified facts

### Secondary (MEDIUM confidence)

None required — every claim in this research was directly verified against the checked-out repository in this session.

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies, entire stack already in place and verified
- Architecture: HIGH — pattern is a direct generalization of code read in full this session
- Pitfalls: HIGH for pitfalls 2-5 (each grounded in a specific verified code fact); MEDIUM for pitfall 1 (the "today" semantics recommendation is a defensible design choice, not a fact — flagged as Assumption A2)

**Research date:** 2026-07-30
**Valid until:** 30 days (stable internal codebase, no external API/library version drift risk since no new dependencies are introduced)
