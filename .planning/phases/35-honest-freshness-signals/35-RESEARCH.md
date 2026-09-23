# Phase 35: Honest Freshness Signals — Research

**Researched:** 2026-09-23
**Domain:** Astro build-time data rendering (news/methodology pages), Python pipeline write-path (store.py), GitHub Actions deploy gating
**Confidence:** HIGH (all claims measured against repo HEAD `8095928`, prod `https://ischilesafe.com`, and `data/incidents/current.json` as of 2026-09-23T03:37:54Z)

## Summary

All five FRESH requirements are additive display/gating fixes on top of infrastructure that
already exists (G-05's `last_new_incident_at` field and `freshness.mjs` validator, shipped in
Phase 34-03). Phase 35 does not need to invent a freshness model — it needs to (1) surface the
existing evidence on the served pages (FRESH-01, FRESH-05), (2) stop padding the histogram with
dead days before the data actually starts (FRESH-02), (3) caveat stale commune sections
(FRESH-03), and (4) stop the pipeline from committing/deploying on true no-op runs (FRESH-04).
Every one of these is measurably broken right now: prod's `/news/` shows no "Latest incident"
line at all, the histogram draws 18 empty bars before 2026-08-24, all 112 communes with news
already show a >7-day-old caveat trigger, and 11 of the last 14 auto-commits to `current.json`
changed nothing but the `generated` timestamp yet still fired a Cloudflare deploy.

**Primary recommendation:** Reuse `freshness.mjs`'s exact evidence rule (`last_new_incident_at`
preferred, else `max(date)+1day`) as the single source of truth for every "Latest incident" /
stale-notice computation across news.astro, es/noticias.astro, CommuneNewsSection.astro, and the
methodology pages — implemented as one new pure TS helper (mirroring `newsDayFacets.ts`'s
pattern) so validator and page logic can never drift, then fix store.py's `generated` field so a
true no-op run is byte-identical and the Actions `git diff --staged --quiet` gate naturally skips
the deploy.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Freshness evidence computation (last_new_incident_at / max(date)) | Frontend Server (Astro build) | Database/Storage (current.json) | Must be computed identically at build time (page render) and in CI (freshness.mjs validator) — both read the same static JSON, no runtime server exists |
| Day-histogram coverage clipping | Frontend Server (Astro build, `newsDayFacets.ts`) | — | Pure function, already isolated; only its window math changes |
| Commune-page staleness caveat | Frontend Server (Astro build, `CommuneNewsSection.astro`) | — | Static HTML per commune, computed once at build from the same current.json |
| No-op run / deploy suppression | Backend (Python pipeline `store.py`) + CI (`news-pipeline.yml`) | — | The commit-diff gate lives in the workflow; the byte-identity precondition lives in `store.py`'s write path |
| CEAD `last_updated` / partial-year cutoff display | Frontend Server (Astro build, methodology + commune pages) | Database/Storage (`data/cead/national.json`, `data/cead/*/*.json`) | Static data already carries `last_updated`; only the display layer is missing |

## Package Legitimacy Audit

Not applicable — Phase 35 adds no new dependencies (all work is in existing `site/src/lib`,
`site/src/pages`, `site/scripts/validate`, and `pipeline/news/store.py`; no npm/pip installs).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRESH-01 | `/news/` and `/es/noticias/` show "Latest incident: <max date>" from data, plus a bilingual >48h stale notice, validated with the Sep-4-frozen fixture | § FRESH-01 below: exact insertion points, evidence-source recommendation, fixture mechanism already proven by `freshness.test.ts` |
| FRESH-02 | Day histogram draws no bars for days outside `current.json`'s coverage window | § FRESH-02: `computeDayBuckets` measured producing 18 empty days before real data starts; minimal clip fix identified |
| FRESH-03 | Commune "Recent incidents" section caveats when newest item >7 days old, both locales | § FRESH-03: exact heading strings, measured 112/112 communes would trigger today |
| FRESH-04 | No-op pipeline run leaves `current.json` byte-identical, fires no deploy; deploys ≤ runs that changed the incident set over 7 days | § FRESH-04: `store.py:233` root cause pinpointed line-exact; measured 11/14 recent auto-commits were no-ops that still deployed |
| FRESH-05 | Methodology + commune pages show "CEAD data as of `<last_updated>`" and partial-year cutoff label, both locales, validated | § FRESH-05: `last_updated` field located (`data/cead/national.json:"last_updated"`, format `YYYY-MM-DD`, currently `2026-06-16`), consumers found, gap identified |
</phase_requirements>

## FRESH-01: "Latest incident" stamp + stale notice on /news/ and /es/noticias/

**Current state (measured):**
- `site/src/pages/news.astro:48-84` reads `raw.generated` from `public/data/incidents/current.json`
  and renders it as `<time datetime={generated}>Updated {formattedDate}</time>` at line 240-244.
  This is the **build/write timestamp**, not incident freshness — `generated` is rewritten every
  pipeline run regardless of whether any incident changed (`pipeline/news/store.py:233`,
  confirmed live: `data/incidents/current.json` `generated` = `2026-09-23T03:37:54.191098Z` while
  the newest incident date is `2026-09-04`, a 19-day gap).
- Prod measured (`curl -s https://ischilesafe.com/news/`, 2026-09-23): page shows
  `Updated September 23, 2026` and contains **no** "Latest incident" text and no
  `last_new_incident_at` anywhere in the HTML — FRESH-01 is fully unimplemented today.
- `data/incidents/current.json` currently has `last_new_incident_at: null` (key absent from the
  JSON — Python `.get()` returns `None`; the key is genuinely omitted per `store.py:239-241`,
  since no live run has yet bumped it post-Phase-34-classifier-restore). `es/noticias.astro`
  mirrors `news.astro`'s data-loading pattern (same `dataPath` resolution via `process.cwd()`,
  per the memory hazard "News page build path drift" — confirmed both files independently resolve
  `public/data/incidents/current.json`, so both need the same fix applied twice, not shared via a
  single conditional render).
- `site/scripts/validate/freshness.mjs` (Validator #15, already in `all.mjs`'s `VALIDATORS` array,
  `site/scripts/validate/all.mjs:39-55`) already implements the exact evidence rule needed:
  `last_new_incident_at` preferred, else `max(incident.date) + 1 day` (`freshness.mjs:83-105`),
  48h threshold (`freshness.mjs:36`), with a 24h future-clock allowance
  (`freshness.mjs:113-119`). This validator checks **data health**, not the **page's rendered
  text** — it does not currently assert anything about what `/news/` displays.

**Recommendation — which "newest incident" definition:** Use `last_new_incident_at` when present
(it reflects true classification liveness, immune to backfills per G-07(a)), falling back to
`max(incident.date)` (not `+1 day` — that offset exists in `freshness.mjs` only to give the
48h-age check slack for same-day publishing lag; a page-display value should show the literal
data date, not an inflated one). **Reason to diverge from freshness.mjs's `+1 day` offset**: the
validator's fallback exists to avoid false-failing on legitimately fresh data classified the same
calendar day; the page's job is to state a fact ("newest incident dated X"), not to pass a
threshold check, so no offset belongs in the displayed value. Do apply the identical 48h staleness
threshold for the caveat-render decision, reusing the SAME comparison logic as `freshness.mjs` so
the two can never disagree (extract a shared pure function, see below) — but display the raw date,
not the offset date.

**Build-time implementation:** Add a pure helper — e.g. `site/src/lib/newsFreshness.ts` — exporting
`computeFreshnessEvidence(payload)` and `isStale(evidenceMs, nowMs, thresholdHours=48)`, ported from
`freshness.mjs:83-105` and `113-136` (same UTC/string arithmetic discipline used across this
codebase — no local-time `Date` construction, per this file's `newsDayFacets.ts` precedent).
`news.astro` / `es/noticias.astro` then call it at build time (line ~64, right after `raw` is
parsed) instead of only reading `raw.generated`, and render:
- ES/EN "Latest incident: `<date>`" line near the existing `.freshness` paragraph (do not remove
  the `Updated <date>` build stamp — it remains useful, just relabel/keep both, since the
  Assumptions Log below flags that the exact microcopy/wording is not locked by CONTEXT.md).
- A conditional bilingual stale-notice block, rendered only when `isStale(...)` is true, following
  the same `{condition && (<p>…</p>)}` Astro pattern already used at line 240-244 and 310 for the
  histogram (zero client JS, matches CLAUDE.md "nada de contenido crítico render-only en cliente").

**Validator + fixture mechanism (already proven, reuse it):** `freshness.test.ts`
(`site/scripts/validate/freshness.test.ts:1-13`) demonstrates the established fixture pattern for
this exact evidence rule: `mkdtempSync` a tmp dir, write a synthetic `current.json`, `spawnSync`
the script with env-var injection (`FRESHNESS_CURRENT_JSON`, `FRESHNESS_NOW`) — never mutate real
`data/`, never touch the wall clock. For FRESH-01 there are two distinct testing needs:
1. **The extracted `computeFreshnessEvidence`/`isStale` helper** — pure functions, test directly
   with plain vitest `describe/it`, no subprocess needed (same style as
   `site/scripts/validate/facets.mjs`'s sibling logic, which `newsDayFacets.ts` already tests this
   way per its own module header).
2. **The rendered page** (does the stale notice actually appear in HTML) — there is **no existing
   fixture mechanism that swaps `current.json` before an Astro build**; `news.astro` resolves the
   path unconditionally via `process.cwd()`. Options: (a) a validator over `dist/news/index.html`
   after a real build with a temporarily-swapped fixture file (risk: OneDrive build-desync memory
   hazard, must chain build+validate in one command); (b) rely on the pure-helper unit tests plus
   a `scripts/validate/` assertion that greps built HTML for the presence of the freshness markup
   when `last_new_incident_at`/incidents are present, without needing to control the input data
   (assert structural presence, e.g. a `<p class="freshness-stale">` node exists in the DOM when
   `freshness.mjs` itself reports FAIL on the same live `current.json` — i.e., cross-check the two
   independently-computed signals rather than fixture-swapping the build input). Recommend (b) as
   the primary validator (no fixture-swap risk) plus (1) unit tests for the pure logic; if the
   planner wants a true Sep-4-frozen-fixture build assertion, it must budget an extra `astro build`
   invocation with `FRESHNESS_CURRENT_JSON`-style path override added to `news.astro`/`noticias.astro`
   (a new env-injection point mirroring `freshness.mjs`'s own pattern) — this is a **structural
   change to the page**, not just glue, and should be called out explicitly as its own task if
   chosen.

**Implications for the plan:** Two near-identical page edits (EN + ES, memory hazard: i18n
localized-slug pitfall does not apply here since this is content not routing, but the "duplicated
verbatim, must edit both" pattern from `news.astro`'s own comments at line 727-729 applies
directly — the CSS family palette is already duplicated 3x across `news.astro`,
`es/noticias.astro`, `CommuneNewsSection.astro`; expect the same duplication burden for this
change). One new lib file with unit tests. One validator addition (structural cross-check against
`freshness.mjs`'s own verdict). Zero new client JS.

## FRESH-02: Day histogram draws dead zero-days before real coverage

**Current state (measured):** `computeDayBuckets` (`site/src/lib/newsDayFacets.ts:63-95`) is
**already anchored to `facets.anchorDate`** (the newest incident's date), not build wall-clock —
this part is correct and was clearly a deliberate fix already (module header explicitly warns
against wall-clock anchoring). The defect is the **fixed `DAY_WINDOW_WIDTH = 30`**
(`newsDayFacets.ts:33`): the window is always `[anchor - 29, anchor]` regardless of where the
data actually starts.

Measured on prod (`curl https://ischilesafe.com/news/`, 2026-09-23) and independently on
`data/incidents/current.json`: `anchorDate = 2026-09-04` (max incident date), earliest incident
date = `2026-08-24`. Window = `2026-08-06` .. `2026-09-04` (30 days). Prod HTML confirms exactly
30 `data-day` bars from `2026-08-06` to `2026-09-04`. Real coverage only starts `2026-08-24`, so
**18 of 30 bars (60%) are contractual zero-padding with no data behind them at all** — not a gap
in an otherwise-continuous feed, but dead space before the dataset's own start. This is precisely
V-05's complaint: bars for days "outside coverage."

**Minimal fix:** Clip the lower bound of the window to `max(lowerBoundDate(anchorMs, width-1),
earliestIncidentDate)` — i.e., compute the earliest date present in `dates` and never emit bars
before it, while still emitting real zero-count days that fall *within* the actual coverage span
(a genuine reporting gap, e.g. if the feed goes quiet for 3 days mid-month, must still show as
zero bars — that is real information per the module's own "dense series" contract at
`newsDayFacets.ts:11-14`, which FRESH-02 does not touch). Concretely: compute
`const earliest = dates.length ? dates.reduce((a,b) => a < b ? a : b) : null;` and use
`const lower = earliest && earliest > windowLower ? earliest : windowLower;` in
`computeDayBuckets`. Also consider capping the window width when the actual coverage span is
narrower than 30 days rather than always requesting 30 slots — same effect, expressed as
`width = min(DAY_WINDOW_WIDTH, (anchor - earliest) + 1)`, which is the cleaner one-line change and
avoids introducing a second lower-bound variable.

**Existing vitest coverage:** No `.test.ts` file exists for `newsDayFacets.ts` currently (grep
confirms only `figure-registry.test.ts` and `freshness.test.ts` exist under
`site/scripts/validate/`, plus 178 total `*.test.ts` files repo-wide, but none matching
`newsDayFacets`). This is a **coverage gap for Wave 0**: `computeDayBuckets`/`peakBucket` are pure
and trivially unit-testable (no fixture-swap needed, unlike FRESH-01's page-level assertion) — a
new `site/src/lib/newsDayFacets.test.ts` should be added as part of this phase regardless of
which fix lands, covering: (a) window narrower than 30 days when coverage is narrower, (b) a
genuine internal gap still zero-pads, (c) `anchorDate = null` still returns `[]`.

**Implications for the plan:** Single-file, single-function change plus new test file. No
Astro/rendering change needed since `news.astro`/`noticias.astro` already just map over whatever
`computeDayBuckets` returns (`news.astro:310-336`).

## FRESH-03: Commune "Recent incidents" caveat when newest item >7 days old

**Current state (measured):** `CommuneNewsSection.astro` (`site/src/components/CommuneNewsSection.astro`)
renders a static heading with no date-conditional logic at all:
- EN: `t.commune_news_heading = 'Recent Incidents in the News'`
  (`site/src/config/i18n.ts:485`)
- ES: `t.commune_news_heading = 'Incidentes Recientes en la Prensa'`
  (`site/src/config/i18n.ts:730`)
- A caveat string already exists but is generic, not date-conditional: EN
  `'Automatically classified from press coverage; not official statistics. Sources are always
  cited.'` (`i18n.ts:488`), ES equivalent at `i18n.ts:733`.
- The newest item's date **is** available at build time: `items[0].date` after the existing
  `.sort((a, b) => b.date.localeCompare(a.date))` call inside `loadIncidentsByCut()`
  (`CommuneNewsSection.astro:49-51`), and `latestYear` (line 114) already derives from
  `items[0]!.date`. This means the age check is a one-line addition using data already in scope —
  no new I/O.

**Measured impact today:** Computing `now(2026-09-23) - max(date per commune)` over all 112
communes that currently have any news incident: **112/112 (100%)** are already >7 days stale
(max incident date across the whole dataset is `2026-09-04`, 19 days old). This is expected given
the classifier outage (Phase 34's subject) — it also means FRESH-03's caveat, once shipped, will
be visible everywhere until Phase 34's live classification catches up, which is by design (honest
signal) but worth flagging to the planner/premortem so it isn't mistaken for a bug at review time.

**Recommendation:** Add a `staleHeading`/`staleCaveat` pair of strings to `i18n.ts` (both
locales), and in `CommuneNewsSection.astro` compute `const isStale = items.length > 0 &&
(refNow - Date.parse(items[0].date + 'T00:00:00Z')) / 86400000 > 7;` — reuse the same "now"
source recommended for FRESH-01 (ideally a single shared `buildNow` concept, though this component
has no access to `facets.anchorDate` since it's a per-commune slice with no facets computation;
using literal build wall-clock here is acceptable and arguably *more* honest for this specific
component, since the question being answered is "how old is this to a reader visiting today," not
"how does this compare to the newest incident anywhere" — flag this as a discretion point, not a
locked decision, since CONTEXT.md was not read in this research pass and may already have an
opinion). Render the caveat/heading swap conditionally, same `{isStale && (...)}` pattern already
used elsewhere in this file for `{items.length > 0 && (...)}` (line 133).

**Implications for the plan:** Single component + i18n string additions, both locales. Given
100% of communes trigger this today, a hand-checked screenshot/HTML diff of at least 2-3 commune
pages (one high-volume, one low-volume) is a reasonable verification step, not a full 346-page
audit.

## FRESH-04: No-op pipeline run must not rewrite current.json or fire a deploy

**Root cause, pinpointed:** `pipeline/news/store.py:232-236`:
```python
payload = {
    "generated": ref_now.isoformat().replace("+00:00", "Z"),
    "window_days": window_days,
    "incidents": current_incidents,
}
```
`generated` is **unconditionally set to the current run's wall-clock timestamp**, every run, with
no comparison to the previous payload's `generated` value or content. `atomic_write_json` then
always writes a file that differs from the previous one by at least this one field, even when
`current_incidents` is byte-for-byte identical in content (same ids, same fields, same order —
`_merge_by_id` at `store.py:119-127` preserves `existing` order and only appends genuinely new
ids, so a 0-new-incident run produces an identical `incidents` array).

**Measured proof (git log on `data/incidents/current.json`, last 15 auto-commits, excluding the
one manual hotfix `45c2650`):**

| Commit | Date (UTC) | Lines containing `"id"` added in diff | Interpretation |
|---|---|---|---|
| f5761ea | 09-23 03:37 | 0 | no-op, generated-only rewrite |
| 3a0d94e | 09-23 03:36 | 0 | no-op |
| e4774b0 | 09-23 03:05 | 57 | real (backfill classify write) |
| 7c32fd7 | 09-22 20:49 | 0 | no-op |
| e52a6b0 | 09-22 16:11 | 0 | no-op |
| 041afe4 | 09-22 10:53 | 0 | no-op |
| 6576275 | 09-22 03:05 | 78 | real |
| cff4e48 | 09-21 21:39 | 0 | no-op |
| 9d29494 | 09-21 17:47 | 0 | no-op |
| cb5620d | 09-21 11:52 | 0 | no-op |
| c754a15 | 09-21 03:05 | 68 | real |
| c09d88c | 09-20 20:15 | 0 | no-op |
| 2a9606f | 09-20 15:21 | 0 | no-op |
| 64d265c | 09-20 10:32 | 0 | no-op |

**11 of these 14 commits (79%) added zero incident lines** — i.e., every field in `incidents`
was unchanged, only `generated` differed — yet each one passed `git diff --staged --quiet` (false,
i.e. "changed") in `.github/workflows/news-pipeline.yml`'s "Commit data if changed" step
(`news-pipeline.yml:79-90`) purely because of the `generated` timestamp diff, triggering
`git commit` + `push-with-rebase.sh` + the unconditional "Trigger Cloudflare Pages deploy" step
(`news-pipeline.yml:107-110`, gated only on `steps.commit.outputs.changed == 'true'`, which was
true for all of these). This matches G-16 (the classifier is currently outage-recovering, live
runs since the fix landed have mostly seen genuinely 0 new items) and confirms FRESH-04's premise
precisely — **the effective no-op deploy rate over this measured window is ~79%**, not the "≤ runs
that changed the incident set" the requirement demands.

**What must be byte-identical vs. what legitimately changes:** Define "no-op" as: same set of
incident ids in `current_incidents` (content-equal, not merely same length — a
publish/unpublish/correction would change fields on an existing id and should still count as a
real change) AND no ids aged into/out of the archive this run (archive writes are a separate
`atomic_write_json` call per month, `store.py:226`, with the same "always writes even if
unchanged" defect — the archive dir also needs the same treatment, or a no-op run's `git add
data/` will still pick up an archive rewrite). Minimal precise rule: **only bump `generated` when
`current_incidents` (post-partition) differs from what was previously on disk**, and skip writing
the archive file for a month when its merged content is unchanged from what's already there.

**Proposed minimal change (store.py):**
1. Before writing `payload`, compare `current_incidents` against `existing_payload.get("incidents",
   [])` (or, simpler and cheaper: compare against the pre-partition `existing` list plus new
   ids — but the correct comparison is against what's about to be written, i.e. the previous
   `current.json`'s `incidents` array, not `existing` which already includes items about to age
   out). If identical (same ids, same field values, same order — or order-insensitive by id-set
   plus per-id field equality, since `_merge_by_id` is stable so order should already match),
   **reuse `previous_payload.get("generated")` instead of `ref_now`**, and skip the write
   entirely if `previous_payload == payload` byte-for-byte (or just build `payload` with the old
   `generated` and let `atomic_write_json`'s own content do the comparison — but `atomic_write_json`
   is not shown to already dedupe; check its implementation before assuming — not read in this
   research pass, flagged as an open question below).
2. Apply the same "unchanged → don't rewrite" logic to each `archive/YYYY-MM.json` write at
   `store.py:207-226` (currently every run re-writes `generated` on every touched archive month's
   file even when `by_month[month_key]` is empty for that iteration — actually `by_month` is only
   populated for months with items in `aged_out`, so this only fires when something genuinely aged
   out, which is a real event; the archive path's `generated` timestamp overwrite is less
   important than `current.json`'s but should be checked against the same rule for consistency).
3. This makes `git diff --staged --quiet` correctly report "unchanged" for a true no-op run,
   which naturally makes `changed=false`, which naturally skips both the commit and the deploy —
   **no change needed to `news-pipeline.yml` itself**, the existing conditional
   (`if: steps.commit.outputs.changed == 'true'`) already does the right thing once the input is
   fixed. This is the cleanest fix surface: one Python file, no workflow YAML changes.

**Interplay with G-05 `last_new_incident_at` and heartbeat:** No conflict — `last_new_incident_at`
is already correctly gated on `new_in_window_count > 0` (`store.py:237-241`), independent of
`generated`. Once `generated` stops rewriting on no-ops, `last_new_incident_at` remains the
correct "is the pipeline actually alive" signal and `generated` becomes purely "when did the
file's content last actually change" — the two fields become properly orthogonal, which is an
improvement (currently `generated` is misleading operators into thinking the pipeline just ran
successfully with new data, when it may have run and found nothing).

**Open question (flag for planner):** `atomic_write_json`'s implementation
(`pipeline/shared/atomic_write.py`) was not read in this research pass — verify whether it already
short-circuits on identical content (in which case the fix is purely "don't put `ref_now` in the
payload unconditionally") or always writes (in which case the fix also needs an explicit
"payload == previous → skip write" guard in `store.py` before calling it).

## FRESH-05: CEAD "data as of" + partial-year cutoff on methodology/commune pages

**Current state (measured):**
- `data/cead/national.json` has a top-level `"last_updated": "2026-06-16"` field (format:
  ISO date, no time component). `pipeline/scrape_cead.py` writes this same key at three call
  sites (`scrape_cead.py:461`, `570`, `584`, all `run_date.isoformat()`) — i.e. every CEAD output
  file (national, presumably per-region and per-commune, and the `meta/` files) carries its own
  `last_updated`. `data/cead/meta/index.json` and `catalog.json` do not appear to carry
  `last_updated` themselves (only `national.json` was inspected directly; per-commune/per-region
  files were not individually opened in this pass — same field name is very likely present given
  the three call sites write it into every payload shape scrape_cead.py produces, but this is
  `[ASSUMED]` for files other than `national.json`, confirm in planning).
- **This field is currently NOT surfaced on any page.** `grep` across `site/src/` found
  `last_updated` referenced only in `site/src/lib/data.ts:65` (an optional field on the
  `CommuneData` TypeScript interface) and `site/src/components/map/ResultPanel.tsx:77` (same
  interface, map-popup component) — i.e. it flows into the map island's result panel type but was
  not confirmed to actually render in the DOM in this pass (interface presence ≠ display; not
  independently verified — flag for planner to check `ResultPanel.tsx`'s JSX). It is **not**
  referenced anywhere in `methodology.astro`, `es/metodologia.astro`, or
  `CommuneNewsSection.astro`/commune page templates.
  Given CLAUDE.md's "CEAD es fuente única cuanti" and "atribuir fuentes" constraints, and given
  the memory hazard that CEAD is scraped quarterly/locally (not live), this gap is a genuine
  attribution/honesty miss: a reader of `/methodology/` or any commune page currently has no way
  to know the CEAD statistics are dated 2026-06-16, over three months stale as of this research
  date.
- **Partial-year cutoff:** `methodology.astro:19,95,327` already documents the concept in prose —
  "the current calendar year is excluded as partial" (line 327) — this is a *methodology text*
  explanation, not a dynamic per-page label driven by data. FRESH-05 as worded ("label the
  partial-year cutoff... with a validator") likely means: make this fact assertable/validatable,
  and possibly surface it more concretely (e.g. "data covers through `<last full year>`" using the
  actual max year present in the series, not just static prose). The existing prose is accurate
  and does not need rewriting — FRESH-05's work is adding the `<last_updated>` stamp and,
  optionally, tightening the partial-year statement to be data-driven rather than purely narrative
  (recommend keeping the narrative, adding a validator that cross-checks the narrative's claimed
  cutoff year against the actual max complete year in `national.json`'s `series`, so a future data
  refresh can't silently invalidate the prose).

**Consumers to update:** `site/src/pages/methodology.astro`, `site/src/pages/es/metodologia.astro`,
and commune page templates (need to identify the commune page — not opened in this pass; likely
`site/src/pages/commune/[slug].astro` or similar dynamic route given `CommuneNewsSection.astro`'s
comment about "the ~340×2 page build" — confirm exact path in planning, `[ASSUMED]`).

**Existing validators that could host the assertion:** `site/scripts/validate/coverage.mjs` and
`site/scripts/validate/schema.mjs` are the closest existing validators by name (not opened in this
pass — their exact assertions are unknown, `[ASSUMED]` that they check data completeness rather
than page display; confirm before assuming either can be extended rather than needing a new
`cead-freshness.mjs`). Given `freshness.mjs`'s precedent (a small, single-purpose validator per
concern, registered in `all.mjs`'s `VALIDATORS` array), the cleanest path is a new validator
(e.g. `cead-staleness.mjs`) that greps built HTML (or, cheaper, checks the source data directly
plus a build-time-rendered marker) for the "CEAD data as of" string in both locales, mirroring
`hreflang.mjs`/`forbidden-language.mjs`'s pattern of scanning `dist/` output — none of these three
validators' internals were read in this pass; their existence and naming convention is the load-
bearing fact here, not their implementation detail.

**Implications for the plan:** This is the least-scoped requirement of the five — it needs (a) one
new i18n string pair, (b) edits to methodology.astro + es/metodologia.astro (straightforward), (c)
an edit to the commune page template (path needs confirming in planning, not this research pass),
and (d) possibly a new validator or an extension of an existing one (coverage.mjs/schema.mjs need
to be opened before the plan commits to "extend" vs. "new file").

## Test/Validator Baseline

- **Validators registered in `all.mjs`:** 16 (`site/scripts/validate/all.mjs:39-55`), confirmed
  by direct read — matches the directive's "validators 16". `freshness.mjs` is validator #15 per
  its own file header comment, currently reads real `data/incidents/current.json` on every CI
  run — given the newest incident is 19 days old (`2026-09-04`) and the 48h threshold, **this
  validator is presently FAILing in CI**, consistent with the directive's note ("freshness
  currently FAIL until live recovery") and Phase 34's still-open classifier-restore work.
- **Vitest test files:** 178 `*.test.ts` files found repo-wide (`find site -name "*.test.ts" | wc
  -l`); this count was not cross-checked against the directive's "vitest 97" figure, which more
  likely refers to individual `it()`/test-case count, not file count, from an earlier baseline
  snapshot — a sampled `it(` grep across just the two `scripts/validate/*.test.ts` files found 20
  cases (8 + 12) alone, so 97 as a *file* count would be implausible; treat "97" and "611/1/2" as
  the directive's own prior measurement (RUN STATUS block states pytest 395/1/1 as of 2026-09-22,
  vitest 86/86 as of the same date — these are the last **directive-recorded** numbers, not
  independently re-measured in this research pass per the instruction not to rerun the build
  unless needed). **Recommend the planner re-run the full baseline in the chained
  build+validate+vitest command at plan/execute time**, since Phase 34 work (34-01..34-05) has
  landed test files since 2026-09-22 and the directive's own numbers are already stated as
  pre-34 baseline, not current.
- **Pytest:** not re-run in this pass (would require a full `pytest` invocation; deferred to
  planning/execution per the "don't rerun unless needed" instruction and because the directive's
  own numbers are already known to be stale post-34-01..34-05).

## Editorial Constraints (confirmed applicable to Phase 35)

- **No absolute safe/dangerous wording:** `site/scripts/validate/forbidden-language.mjs` already
  scans built output (per `CommuneNewsSection.astro`'s own comment at line 76-79 referencing it as
  the authoritative scanner). None of the FRESH-01..05 additions introduce any safety-verdict
  language — all new copy is purely about data recency ("Latest incident: X", "data as of Y"),
  which is safely outside this validator's scope, but the planner should still run it post-change
  since it scans the whole built site, not just diffed files.
- **Attribution (CEAD / outlet):** FRESH-05 is itself an attribution improvement (surfacing CEAD's
  `last_updated`); FRESH-01/03's incident-level attribution (outlet, source link) is unchanged by
  this phase — no new incident rendering paths are added, only freshness metadata around existing
  ones.
- **Bilingual parity:** Every FRESH requirement is explicitly bilingual (EN+ES). The existing
  `hreflang.mjs` validator (registered in `all.mjs`) checks route-level hreflang pairing, not
  string-parity content — confirm in planning whether any validator actually asserts "every EN
  string added has an ES counterpart" or whether this is presently only enforced by convention
  (the `i18n.ts` file's parallel `EN_STRINGS`/`ES_STRINGS` object structure is the de facto
  mechanism — a missing ES key would be a TypeScript compile error if both interfaces are strict,
  which `@astrojs/check` in CI would catch; not independently verified in this pass).

## Risks / Open Questions

1. **FRESH-01 "now" source ambiguity.** Should the page's own staleness check use Astro build
   wall-clock (when the site was built/deployed) or `facets.anchorDate` (data-relative)? Using
   build wall-clock is more honest to an actual site visitor ("as of right now, this is stale")
   but means every rebuild without new data will change the displayed age; using anchor-relative
   would be static until real data changes but doesn't tell a visitor "how old is this to me right
   now." Recommend build wall-clock (same choice `freshness.mjs` makes) for the reader-facing
   copy — flag as a discretion point for discuss-phase/planner, not locked by this research.
2. **`atomic_write_json`'s existing dedupe behavior is unverified** (see FRESH-04 open question)
   — planner must open `pipeline/shared/atomic_write.py` before finalizing the store.py fix scope.
3. **Exact commune-page file path for FRESH-05** was not resolved in this pass — must be
   identified in planning (likely `site/src/pages/commune/[slug].astro` given the
   `~340×2 page build` comment in `CommuneNewsSection.astro`, but not opened/confirmed).
4. **`data/cead/meta/*.json`'s own `last_updated` presence** is assumed, not directly verified —
   only `national.json` was inspected; per-commune/region CEAD files should be spot-checked in
   planning.
5. **`coverage.mjs`/`schema.mjs` internals unread** — planner should open both before deciding
   whether FRESH-05's validator extends one of them or needs a new file.
6. **FRESH-04's exact archive-file rewrite behavior** needs the same "does this month's content
   actually differ" check as `current.json`, or `git add data/` will still pick up archive noise
   on months where nothing new aged out but the file was still touched — verify empirically
   whether `by_month` (which only populates from non-empty `aged_out` groups) can ever fire with
   unchanged merged content (it can, when the same ids simply re-merge on every run without new
   aged-out items — actually `by_month` only iterates `aged_out`, which is non-empty only when
   something crossed the 30-day cutoff this run, a genuine time-driven event, not a duplicate-run
   artifact — so archive rewrites are naturally rarer and lower-priority than the `current.json`
   fix, but the "unchanged → don't rewrite generated" rule should still apply there for
   consistency, since two runs on the same day could each see the same item age out if the cutoff
   math is date-only not run-count-gated — needs a concrete test case in planning).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `data/cead/meta/*.json` and per-commune/region CEAD files also carry `last_updated` (only `national.json` was directly inspected) | FRESH-05 | Plan might assume a field is universally available when it's only on the national aggregate; would need a fallback or per-file check |
| A2 | Commune page template path (not opened) is a single dynamic route under `site/src/pages/commune/` | FRESH-05 | Wrong file targeted in plan; low risk, easily found by `Glob` at plan time |
| A3 | `atomic_write_json` always writes regardless of content equality (not verified — inferred from absence of any dedupe comment in `store.py`) | FRESH-04 | If it already dedupes, the required fix is smaller (just don't recompute `generated` unconditionally) than if it doesn't (also need an explicit skip-write guard) |
| A4 | `coverage.mjs`/`schema.mjs` validators do not already assert anything about CEAD `last_updated` display (not opened) | FRESH-05 | Plan might create a duplicate validator, or miss an easy extension point |
| A5 | Build wall-clock (not `facets.anchorDate`) is the right "now" reference for FRESH-01/03's staleness display | FRESH-01, FRESH-03 | If discuss-phase/CONTEXT.md already has an opinion, this reasoning should defer to it |

## Recommended Plan Decomposition

**Wave 0 (test infra additions, no behavior change):**
- `site/src/lib/newsDayFacets.test.ts` — new, covers FRESH-02's fix pre/post
- `site/src/lib/newsFreshness.test.ts` — new, covers the extracted evidence/staleness helper for FRESH-01/03

**Wave 1 (pure logic changes, independently testable, no Astro/page wiring):**
- `site/src/lib/newsDayFacets.ts` — FRESH-02 clip-to-coverage fix
- `site/src/lib/newsFreshness.ts` (new) — extracted evidence + staleness helper shared by FRESH-01 and FRESH-03, ported from `freshness.mjs:83-136`
- `pipeline/news/store.py` — FRESH-04 no-op-write guard (after resolving Open Question 2 re: `atomic_write_json`)
- `pipeline/tests/test_store.py` (or wherever store.py's existing tests live — not located in this pass, confirm in planning) — no-op-run regression test

**Wave 2 (page wiring, both locales each):**
- `site/src/pages/news.astro` + `site/src/pages/es/noticias.astro` — FRESH-01 (Latest incident line + stale notice)
- `site/src/components/CommuneNewsSection.astro` — FRESH-03 (stale caveat heading)
- `site/src/pages/methodology.astro` + `site/src/pages/es/metodologia.astro` + commune page template (path TBD) — FRESH-05 ("CEAD data as of" stamp)
- `site/src/config/i18n.ts` — new string pairs for all of the above (Latest incident label, stale-notice copy, stale-caveat heading/body, CEAD-as-of label)

**Wave 3 (validators + close):**
- New/extended validator(s) for FRESH-01 (structural cross-check against `freshness.mjs`'s
  independent verdict), FRESH-05 (CEAD-as-of presence + partial-year cutoff cross-check)
- Full chained `build + npm run validate + vitest` (OneDrive hazard — one command) plus `pytest`
  re-baseline
- `forbidden-language.mjs` and `hreflang.mjs` full-site re-run (they scan the whole `dist/`, not
  just diffed files)

This ordering lets FRESH-02 and FRESH-04 ship as isolated, low-risk, high-confidence fixes even
if FRESH-01/03/05's exact copy/UX needs a discuss-phase pass first — they have no dependency on
locked microcopy decisions.

## Sources

### Primary (HIGH confidence — direct file reads, this session, repo HEAD `8095928`)
- `site/src/pages/news.astro` (full read)
- `site/src/lib/newsDayFacets.ts` (full read)
- `site/src/lib/newsFacets.ts:1-100` (partial read, header + anchorDate contract)
- `pipeline/news/store.py` (full read)
- `site/src/components/CommuneNewsSection.astro` (full read)
- `site/scripts/validate/freshness.mjs` (full read)
- `site/scripts/validate/freshness.test.ts:1-60` (partial read)
- `site/scripts/validate/all.mjs:33-60` (partial read, VALIDATORS array)
- `.github/workflows/news-pipeline.yml` (full read)
- `site/src/config/i18n.ts` (grep for commune_news_* keys)
- `data/cead/national.json` (parsed, `last_updated` field confirmed)
- `site/src/lib/data.ts`, `site/src/components/map/ResultPanel.tsx` (grep for `last_updated`)
- `pipeline/scrape_cead.py` (grep for `last_updated` write sites)
- `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md`, `.planning/REQUIREMENTS.md` (grep for FRESH-*)

### Measured (this session, treated as HIGH confidence — direct tool execution)
- `curl -s https://ischilesafe.com/news/` (prod HTML: confirmed "Updated September 23, 2026", 30
  `data-day` bars spanning 2026-08-06..2026-09-04, no "Latest incident" text present)
- `python3` over `data/incidents/current.json` (742 incidents, dates 2026-08-24..2026-09-04,
  `generated=2026-09-23T03:37:54.191098Z`, `last_new_incident_at` absent)
- `python3` over `data/incidents/current.json` grouped by commune (112 communes with news, 112
  currently >7 days stale)
- `git log` + `git show` diffs over `data/incidents/current.json`'s last 14 auto-commits (11/14
  added zero incident lines, i.e. no-op runs that still committed + would have deployed)
- `find site -name "*.test.ts" | wc -l` → 178

### Not independently re-verified (carried from the governing directive, flagged as such)
- Directive's own pytest/vitest baseline numbers (395/1/1 pytest, 86/86 vitest, as of 2026-09-22
  per RUN STATUS) — pre-dates Phase 34-01..34-05, planner should re-measure

## Metadata

**Confidence breakdown:**
- FRESH-01, FRESH-02, FRESH-04: HIGH — root cause pinpointed to exact file:line, measured live on
  prod/data, existing infrastructure (freshness.mjs, newsDayFacets.ts, store.py) fully read
- FRESH-03: HIGH on defect/impact measurement, MEDIUM on "now" source recommendation (flagged as
  discretion, not locked)
- FRESH-05: MEDIUM — core gap (last_updated unsurfaced) confirmed, but exact consumer file paths
  and per-file field presence partially assumed (A1, A2)
- Test/validator baseline: MEDIUM — validator count (16) directly confirmed; vitest/pytest case
  counts not re-measured, directive's own numbers flagged stale

**Research date:** 2026-09-23
**Valid until:** Short — this research is tied to the live `current.json` state (742 incidents,
max date 2026-09-04) which will change as soon as Phase 34's classifier-restore produces new live
runs. The *code-location* findings (file:line references) remain valid until Phase 34/35 code
changes land; the *measured numbers* (79% no-op rate, 112/112 stale communes, 18/30 dead histogram
bars) will shift the moment live classification resumes — re-measure before execution if more
than ~48h elapse between this research and Phase 35 execution.
