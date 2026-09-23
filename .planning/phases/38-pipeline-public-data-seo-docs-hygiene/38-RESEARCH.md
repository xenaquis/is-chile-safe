# Phase 38: Pipeline, Public-Data, SEO & Docs Hygiene — Research

**Researched:** 2026-09-23
**Domain:** static-site data exposure, SEO cannibalization, pipeline ledger design, CI workflow reliability, docs/memory drift
**Confidence:** HIGH (all findings verified by direct file read, prod curl, or command execution — no Context7/WebSearch needed; this is an internal-repo audit phase)

## Summary

Phase 38 closes 7 low-severity hygiene items (HYG-01..07) left open by the v2.2 audit. All seven are
independently verifiable and independently fixable; none require new libraries or external research —
this is a codebase-forensics phase, not a technology-selection phase. Six of seven are directly
actionable today; HYG-06 (Oct-1 local CEAD scrape) is date-gated and cannot execute until
2026-10-01 — today is 2026-09-23, so it must be deferred-live per the directive's own instruction.

**Primary recommendation:** Decompose into independent single-concern task groups (public-data
exclusion, SEO differentiation, ledger pruning, workflow gate removal, docs sync, CEAD scrape
operator step, GSC operator step) — none share files except `pipeline/scrape_news.py` (HYG-01
consumer check + HYG-03 pruning) and `data/SOURCES.md`/`CLAUDE.md` (HYG-05 touches both).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| seen.json/rejected/ exposure control | Build/Static (site/scripts/sync-data.mjs) | — | Exposure is a copy-step decision, not a runtime one; Astro serves whatever lands in `public/` |
| /map/ vs /chile-crime-map/ differentiation | Frontend Server (SSR/SSG — Astro page frontmatter) | — | Title/H1/meta are set per-page at build time |
| Validator enforcement (SEO diff, dist absence) | Build/Static (site/scripts/validate/*.mjs) | — | Existing validator pattern (seo.mjs) is the established enforcement point |
| Seen-ledger pruning | Backend/Pipeline (pipeline/scrape_news.py, pipeline/news/*) | Database/Storage (data/incidents/seen.json) | Pruning logic lives with the scraper that writes the ledger |
| CEAD workflow continue-on-error removal | CI/CD (.github/workflows/cead-scraper.yml) | — | Pure workflow YAML change |
| Docs/memory sync | Docs (CLAUDE.md, DEPLOYMENT.md, .planning/STATE.md, data/SOURCES.md) | — | No code tier; pure documentation |
| Oct-1 CEAD scrape | Backend/Pipeline (local machine, operator) | Database/Storage (data/cead/) | Runs outside CI per CRON-05; operator-executed |
| GSC sitemap submission | External (Google Search Console, operator) | — | No code in this repo can perform it |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HYG-01 | seen.json/rejected served or 404'd per owner decision, pages/validators unaffected | § 1 below — confirmed 200 + size today, confirmed zero site consumers |
| HYG-02 | /map/ vs /chile-crime-map/ cannibalization resolved + validator-enforced | § 2 below — confirmed near-duplicate titles, confirmed no existing validator coverage |
| HYG-03 | seen-ledger pruned by first_seen, not publication date | § 3 below — confirmed schema has no first_seen field today, 6,976 entries |
| HYG-04 | cead-scraper.yml has no continue-on-error on data-producing steps | § 4 below — 4 offending steps found with line numbers |
| HYG-05 | CLAUDE.md/STATE.md/DEPLOYMENT.md/data/SOURCES.md match repo | § 5 below — concrete version and model-name drift found |
| HYG-06 | Oct-1 local CEAD scrape executed and outcome recorded | § 6 below — date-gated, not yet actionable (today 2026-09-23) |
| HYG-07 | GSC sitemap submitted or formally retired | § 7 below — operator-only, sitemap-index.xml confirmed live |
</phase_requirements>

## 1. HYG-01 — Public ledger exposure (seen.json / rejected/*.json / pending.json)

**Data flow (verified, `site/scripts/sync-data.mjs:42-49`):** the script copies
`data/incidents/` **wholesale** (`cpSync(INCIDENTS_SRC, INCIDENTS_DEST, { recursive: true })`,
no allowlist/denylist) into `site/public/data/incidents/` on every `predev`/`prebuild`. There is
no filtering step anywhere in the copy — everything in `data/incidents/` is served as-is.

**Prod state (curl 2026-09-23):**

| URL | Status | Size |
|-----|--------|------|
| `https://ischilesafe.com/data/incidents/seen.json` | 200 | 2,014,501 bytes (~2.0 MB) |
| `https://ischilesafe.com/data/incidents/rejected/2026-09.json` | 200 | 2,042,890 bytes (~2.0 MB) |
| `https://ischilesafe.com/data/incidents/current.json` | 200 | 544,009 bytes (the intended public payload) |
| `https://ischilesafe.com/data/incidents/pending.json` | 404 | — (file does not currently exist on disk — see below) |

`data/incidents/seen.json` has **6,976 entries** (`python -c "import json;
print(len(json.load(open('data/incidents/seen.json'))))"` → 6976), schema `{url: date_string}`
(no first_seen — relevant to HYG-03 too). `data/incidents/rejected/` has 3 monthly files
(2026-07, 2026-08, 2026-09).

`data/incidents/pending.json` (the retry queue written by `pipeline/news/pending.py`, path
resolved at `pipeline/scrape_news.py:246` as `data_dir / "pending.json"`) does **not exist on
disk right now** (confirmed via `ls data/incidents/*.json` — absent) — it is only written when
the queue is non-empty between runs, so its exposure risk is real but currently dormant. The
directive (G-06) explicitly defers "`pending.json` public exposure" decision text to
`data/SOURCES.md` in this phase, alongside HYG-01.

**Site consumers (grep `site/src`, `site/scripts` for `seen.json`, `rejected`, `pending.json`):
zero matches.** Every page/component that touches `data/incidents/` reads only `current.json`
(`CommuneNewsSection.astro:38`, `HomeNewsPulse.astro:161`, `IncidentPinLayer.ts:85`,
`news.astro:46`, `es/noticias.astro:45`) or `archive/` (`news.astro:169`,
`es/noticias.astro:167`). No validator references these three files either (grep of
`site/scripts/validate/*.mjs` for the same strings: zero matches).

**Implication:** seen.json/rejected are pure incidental exposure — a side effect of the
wholesale-copy design comment ("plain recursive copy … no symlinks"), not an intentional
public API. Removing them from the served tree is a zero-blast-radius change confirmed by
grep, not inference.

**R2 archive keeps them regardless:** per memory `r2-research-archive.md`, the daily R2 cron
already archives the full-text corpus/ledger/corpus-state independently of what `sync-data.mjs`
serves — so excluding these from `public/` does not lose the audit trail.

**Minimal-change design (two options, either satisfies HYG-01):**

- **Option A (exclude from public, recommended default absent an owner override):** in
  `site/scripts/sync-data.mjs`, after the wholesale `cpSync(INCIDENTS_SRC, INCIDENTS_DEST, …)`,
  add `rmSync` calls removing `INCIDENTS_DEST/seen.json`, `INCIDENTS_DEST/rejected`, and
  `INCIDENTS_DEST/pending.json` (if present) post-copy — cheapest correct fix, keeps the
  wholesale-copy simplicity for `current.json`/`archive/` while denylisting the three sensitive
  paths. A companion validator assertion (new check in `site/scripts/validate/`, e.g. extending
  `seo.mjs` or a new `no-internal-data.mjs`) should assert
  `!existsSync(dist/data/incidents/seen.json)` etc. so a future edit to `sync-data.mjs` cannot
  silently reintroduce exposure.
- **Option B (keep served, formalize):** if the owner decides these should stay public
  (e.g. for transparency/audit purposes), no code change is needed — but `data/SOURCES.md`
  should then document `seen.json`/`rejected/` as an intentional public surface (this is the
  G-06-deferred wording decision) so a future reader does not mistake it for an oversight.
- **Cloudflare-native alternative (not recommended over Option A):** a `site/public/_headers`
  rule (`/data/incidents/seen.json` / `/data/incidents/rejected/*` → `X-Robots-Tag: noindex` or
  a 404 override) is possible but redundant with simply not shipping the files — Cloudflare
  Pages `_redirects` can force a 404 status on a path
  (`/data/incidents/seen.json  /404  404`) without removing the file from `dist/`, which is
  strictly worse (bytes still deployed, still fetchable via direct object access on some CDN
  configs) than not copying it at all. Only useful if the owner wants the file to exist in the
  git-tracked `dist/`-adjacent tree for some other automation but never served.

**No existing test/validator breaks under Option A** (confirmed above — zero consumers).

## 2. HYG-02 — /map/ vs /chile-crime-map/ cannibalization

**Directive constraint (binding, from the prompt):** differentiate titles/H1 by intent; **NO
noindex, NO redirect** — this rules out the two most common SEO-cannibalization fixes and
leaves only content differentiation + internal-linking/canonical hygiene (each page already
self-canonicals, confirmed below, which is correct and must be preserved).

**Live prod state (curl 2026-09-23):**

| Page | Title | H1 | Meta description | Canonical |
|------|-------|----|--------------------|-----------|
| `/map/` | "Chile Crime Map — Interactive" | **none in static HTML** (island-rendered, `client:only="react"` — `site/src/pages/map.astro:39`) | "Explore reported crime incidence across Chile's 346 communes. Filter by year and crime type. Data: CEAD." | self (`/map/`) |
| `/chile-crime-map/` | "Chile Crime Map — Interactive Choropleth by Commune" | "Chile Crime Map — Reported Incidence by Commune" (`site/src/pages/chile-crime-map.astro:41`) | "Explore Chile's reported crime incidence across 346 communes with an interactive choropleth map. Filter by crime type and year. Data: CEAD official statistics." | self (`/chile-crime-map/`) |
| `/es/mapa/` | "Mapa de Incidencia en Chile — Interactivo" | none (same island pattern) | "Explora la incidencia delictiva reportada en las 346 comunas de Chile. Filtra por año y tipo de delito. Fuente: CEAD." | self |
| `/es/mapa-delito-chile/` | "Mapa de Delitos en Chile — Coroplético por Comuna — Chile Safety Map" | "Mapa de Delitos en Chile — Incidencia Reportada por Comuna" | "Mapa interactivo de incidencia delictiva reportada por CEAD para las 346 comunas de Chile. Filtra por tipo de delito y año. Datos CEAD 2025." | self |

**Cannibalization evidence:** both EN titles open with the identical 4-word phrase "Chile Crime
Map" and target the identical head query. `/map/` additionally has **zero `<h1>` in static
HTML** — a real on-page-SEO gap independent of cannibalization (an `L.geoJSON` canvas map has
no textual H1 for a crawler; the visually-hidden `data-map-locate-label` span is an aria-label,
not an H1). `data/SOURCES.md`/`CLAUDE.md` legal rule ("never calibrate territories as
dangerous/safe") is respected in both current titles — any rewrite must preserve that.

**Existing validator coverage:** `site/scripts/validate/seo.mjs` samples `commune`, `comuna`,
`region`, `crime`, `crime-ranking`, `rankings`, `is-chile-safe`/`delitos-por-comuna` — **it does
not sample `map.astro` or `chile-crime-map.astro` at all** (confirmed by reading the full
`SAMPLES` array, lines ~152-172). No assertion anywhere compares the two map pages' titles for
difference.

**Recommended differentiation (respecting the no-noindex/no-redirect constraint), by intent:**

- `/map/` = the **utility/tool** page (bare full-viewport map, `client:only`, minimal chrome).
  Its intent is "use the interactive tool" — title should lead with the action/tool framing,
  e.g. "Interactive Crime Map of Chile — Explore by Commune" (EN) / keep the ES equivalent
  parallel. Because it has no static H1 today, add a visible (not visually-hidden) `<h1>` in
  the static shell above/around the island mount point — this is also an independent SEO
  hygiene fix (a page with a Leaflet canvas and zero text is thin content to a crawler), and it
  must read differently from the editorial H1 to avoid duplicating H2/H1 text.
- `/chile-crime-map/` = the **editorial/explainer** page (Template 2, EditorialIntro +
  MapIslandBlock + EditorialBody) — its intent is "read about + explore" and it already carries
  paragraph content and JSON-LD (`WebPage`/`Dataset`). Keep its current title framing
  ("Reported Incidence by Commune") but ensure the wording no longer starts with the identical
  4-word stem as `/map/`'s new title.
- Add both map pages to `seo.mjs`'s `SAMPLES` array and add a new assertion (e.g. `[T] title
  differentiation`) comparing `/map/` vs `/chile-crime-map/` (and the ES equivalents) titles for
  non-identity on the first N characters, so a future regression is caught mechanically.

## 3. HYG-03 — Seen-ledger pruning by first_seen

**Current schema (verified via `data/incidents/seen.json` read + `pipeline/scrape_news.py:320,432`):**
`seen[url] = date` where `date` is the **item's publication date** (`entry.get("date")` /
`item["date"]`), **not** when the scraper first observed the URL. There is **no `first_seen`
field anywhere in `seen.json`** today, and **no pruning logic exists** in `scrape_news.py` —
grep for `prune`/`PRUNE`/`expire` in that file matches only the *pending-queue* expiry function
(`_expire`, line ~303, which handles the retry queue, a different structure from `seen.json`)
and no seen-ledger prune step.

**Measured size:** 6,976 entries, ~2.0 MB served (see § 1). No entries in `seen.json` carry
first_seen — a schema migration is mandatory, not optional, to implement first_seen-based
pruning: **every existing entry's true first-seen time is unrecoverable** (the field was never
recorded), so the migration's only honest choice is to backfill `first_seen = date` (the
publication date, an approximation) for existing rows and start recording real `first_seen` for
new entries going forward — this should be stated explicitly in the plan, not silently assumed.

**Why the bug matters (mechanism, not yet measured against a specific run's raw candidate
count — recommend the planner capture one fresh run's `unseen_candidates`/`keyword_passed`
numbers via `gh run view <latest-news-run-id> --log` at plan time, since these numbers churn
every 6h and would be stale by execution):** because `seen[url]` is keyed by publication date
rather than by observation date, an RSS feed that **re-serves an old-dated item** (a very common
pattern — outlets bump/re-publish or Google News re-surfaces older stories under a fresh feed
entry with the same URL) is looked up correctly by URL (`seen_set = set(seen.keys())`, so
dedup-by-URL already works) — **the actual defect implied by HYG-03's wording is pruning
policy, not dedup correctness**: if/when a size-based or age-based prune is added to bound
`seen.json`'s growth, pruning by the *publication* date would evict entries for genuinely-old
articles that could still be re-served by a feed tomorrow (causing the URL to look "unseen"
again and be reprocessed/re-classified), whereas pruning by `first_seen` (when the scraper
itself last encountered the URL) correctly reflects "how long ago did WE stop seeing this URL
in any feed," which is the right prune signal. Recommend implementing the schema field first
(track `first_seen` per entry, ISO-8601, on first insert) as a strictly additive, backward
compatible change, with pruning logic (e.g. evict entries whose `first_seen` predates a
window, sized generously — the point is boundedness, not aggressiveness) as a follow-on step in
the same phase.

**No current pruning exists at all** — `seen.json` today grows monotonically forever (6,976
entries and climbing since inception); this is itself worth noting as a secondary finding
beyond the literal HYG-03 requirement text, since the file's ~2MB size (before HYG-01 removes
it from `public/`) is a symptom of unbounded growth, not just wrong prune keying.

## 4. HYG-04 — cead-scraper.yml continue-on-error audit

**All `continue-on-error: true` occurrences in `.github/workflows/cead-scraper.yml`
(verified by grep + full read):**

| Line | Step | Data-producing? | Risk of silent failure |
|------|------|------------------|--------------------------|
| 72 | "Build ENUSC victimization snapshot" (`pipeline/snapshots/fetch_enusc_vhdv.py`) | YES — writes VHDV snapshot consumed by enrichment | A failed fetch silently skips, downstream enrichment runs on stale/missing snapshot data with no alert |
| 78 | "Enrich commune JSONs with ENUSC VHDV" (`pipeline/build_enusc_enrichment.py`) | YES — mutates commune JSONs | Silent partial-enrichment; commune data could be committed missing the VHDV layer with no signal |
| 82 | "Build composite index" (`pipeline/build_composite_index.py`) | YES — writes the composite crime index consumed sitewide (rankings, homepage) | Silent failure would commit CEAD data without a refreshed composite index — a real regression that would not alert |
| 86 | "Build map payload" (`pipeline/build_map_payload.py`) | YES — writes the choropleth map's data payload | Silent failure would deploy CEAD numeric updates while the map's visual layer goes stale, with the job still reporting green |

**Contrast:** the one step deliberately **not** guarded, "Run CEAD scraper" (line 68), has an
explicit inline comment explaining why it must NOT have `continue-on-error` (CRON-05: a real
failure must still alert, disambiguated by the issue body text, not by exit code). The four
listed above lack any such justification comment — they appear to be defensive scaffolding
added so a downstream builder's crash doesn't block the CEAD-data commit, but the tradeoff
(silent partial data) was never weighed against the CRON-05 rationale used one step above them.

**test_workflow_guards.py coverage:** grep confirms `pipeline/tests/test_workflow_guards.py`
has assertions about `cead-scraper.yml` (SHA-pin/persist-credentials checks, `H-02` deps
restoration, line ~527/652/676) but **no assertion about `continue-on-error` presence/absence
on these four steps** — HYG-04 needs a **new** test, e.g. asserting the raw YAML text for the
`Build ENUSC…`/`Enrich commune…`/`Build composite index`/`Build map payload` step blocks
contains no `continue-on-error: true` line, mirroring the existing regex-based assertion style
in that file (it already parses workflow YAML as text, not via a YAML lib — follow that
precedent for consistency, confirmed by reading nearby `real_text = (WORKFLOWS_DIR /
"cead-scraper.yml").read_text(...)` at line 676).

**Minimal fix:** delete `continue-on-error: true` from all four steps. Since "Run CEAD scraper"
is already unguarded and is expected to 403 in Actions (CRON-05), the four downstream builder
steps would then also correctly fail (they depend on scraper output) — this is consistent with,
not a regression of, the documented expected-403 behavior: the whole job is a calendar
reminder that is *supposed* to go red on Actions every quarter, so consistently-red is the
correct end state, matching the un-guarded "Run CEAD scraper" step's existing philosophy.

## 5. HYG-05 — Docs/memory drift

**Concrete version drift, CLAUDE.md vs. installed (`pipeline/requirements.txt` +
`pip show openai`):**

| Package | CLAUDE.md states | Actual (pinned/installed) | Drift |
|---------|-------------------|----------------------------|-------|
| requests | 2.32.x | 2.34.2 (`requirements.txt:1`) | minor version behind |
| beautifulsoup4 | 4.14.x | 4.15.0 (`requirements.txt:2`) | minor version behind |
| lxml | 5.x | 6.1.1 (`requirements.txt:3`) | **major version behind** |
| tenacity | 8.x | 9.1.4 (`requirements.txt:5`) | **major version behind** |
| openai | 1.x | 2.53.0 (`requirements.txt:12`, `pip show openai`) | **major version behind** |
| feedparser | 6.0.x | 6.0.14 | matches, no drift |
| Astro | 7.1.x | 7.1.6 (`site/package.json:20`) | matches, no drift |
| @astrojs/react | 6.0.x | ^6.0.2 (`site/package.json:18`) | matches, no drift |
| React | 19.x | ^19.2.8 (`site/package.json:23`) | matches, no drift |

**Classifier model drift, `data/SOURCES.md:417`:** states "Items are classified … by
`ibm-granite/granite-4.1-8b` via OpenRouter … the default model for this milestone … DeepSeek
v4-flash is retained as a selectable fallback provider only." This is **factually wrong today**:
`pipeline/news/classifier.py:124` resolves the default as
`model_config.resolve("NEWS_MODEL", "deepseek-v4-flash")`, and per the Phase-34 gate decision
(G-16, `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md:112`) the actual winning/live model is
`deepseek/deepseek-v4.1-flash`. Granite is confirmed **DEAD since 2026-09-04** (project memory
`granite-default-classifier.md` — OpenRouter delisted the endpoint). This is the single most
consequential drift item: `data/SOURCES.md` is a reader-facing methodology page and currently
describes a dead/wrong model as the live default.

**`.planning/STATE.md` staleness:** the file's own "Last updated" banner (line 18) is stamped
**2026-07-30**, i.e. roughly 8 weeks stale relative to today (2026-09-23) — it predates all of
milestone v2.2 (phases 34-38) and describes v2.1 phase 28/29 status as "Next." The file is 699
lines and its decision log (F-NN entries) continues through 2026-08-05 (phase 33 / end of
v2.1), so it is internally consistent up to that point but carries no v2.2 content at all. Per
the requirement text, `STATE.md` needs to reflect "resolved blockers" — its blockers section
(`## Blockers`, line 193) should be checked/updated to remove anything resolved by phases
29-37 (confirmed resolved externally per `v2.1-autonomous-run` and `v2.2-milestone-news-recovery`
memory entries, but not reflected in STATE.md's own text).

**`DEPLOYMENT.md`:** no drift found in the sampled sections (Deploy Model Overview, workflow
cadence table, CEAD quarterly-scrape runbook) — it already correctly documents CRON-05 (CEAD
403-on-Actions), the byte-identity check procedure for a quarterly scrape (§ "CEAD quarterly
scrape — verified state", used directly by HYG-06 below), and the classifier absence-behavior
section references NREC work generically without naming a stale model. Last-updated banner
reads 2026-08-04 (line 3) — also stale relative to today but its content sampled clean; the
planner should still do a final grep pass for `granite` (none found) and any Phase-34-superseded
provider-absence prose before closing HYG-05, since this research did not read the file in
full (only targeted greps + the operational-notes section).

**Provenance note (per G-06):** the directive explicitly defers "`data/SOURCES.md` wording and
`pending.json` public exposure" to this phase — so the SOURCES.md classifier-name fix is
in-scope docs work, not a `data/` mutation subject to the "`data/` mutation only for
NREC-09/pipeline-runs/HYG-06" restriction (`data/SOURCES.md` is documentation that happens to
live under `data/`, not scraped/generated data — **flagging this distinction explicitly for the
orchestrator/planner to confirm**, since the directive's `data/` mutation-restriction line
(v2.2-AUTONOMOUS-DIRECTIVE.md:77) does not itself carve out `SOURCES.md`, and a literal reading
could be misapplied to block this requirement).

**Memory (`~/.claude/.../memory/MEMORY.md` and linked files):** `granite-default-classifier.md`
is already correctly marked `DEAD since 2026-09-04` with the replacement noted — **not stale**,
no action needed. No other memory entry inspected references an outdated openai/astro version
or a resolved-but-still-flagged blocker; the index itself already labels most entries
RESOLVED/DONE/dated appropriately.

## 6. HYG-06 — Oct-1 local CEAD scrape

**Date gate: NOT YET ACTIONABLE.** Today is 2026-09-23; the directive is explicit — "HYG-06
(local CEAD scrape) only runs on/after 2026-10-01 … If the date has not arrived when Phase 38
is reached, do everything else in the phase, leave HYG-06 open, and add it to the deferred-live
list" (`v2.2-AUTONOMOUS-DIRECTIVE.md:56`).

**Procedure (already fully documented, DEPLOYMENT.md "CEAD quarterly scrape — verified state",
lines ~567-591 — reuse verbatim, do not re-derive):**

1. Run `PYTHONPATH=. python pipeline/scrape_cead.py` locally (never in Actions — 403 per
   CRON-05). Courtesy delay confirmed in code: `time.sleep(2.5)` at `pipeline/scrape_cead.py:305`
   and `:365` (D-03 courtesy delay, 2.5s between requests). At 346 communes with 2 delayed call
   sites in the loop, expect a runtime on the order of tens of minutes (the prior documented
   run on 2026-08-06 completed 346/346, exit 0 — no exact wall-clock time recorded in
   DEPLOYMENT.md; the planner should treat "tens of minutes, single-digit hours worst case" as
   the estimate and let the operator confirm actual timing at execution).
2. **Do not commit on exit 0 alone** — exit 0 is not evidence of new data (DEPLOYMENT.md's own
   stated lesson from the 2026-08-06 run, which came back byte-identical for all 346 communes
   and was correctly reverted, not committed).
3. Diff the crime core specifically — **exclude** `last_updated`, `composite_index`,
   `spd_homicide_rate`, `sii_exposure_index`, `enusc_vhdv` (these are enrichment fields
   `scrape_cead.py` strips and downstream builders re-add, not raw CEAD output) — compare only
   the actual CEAD-sourced crime series.
4. **If unchanged:** revert (do not commit) — committing a no-op scrape would reset the
   heartbeat's quarter-elapsed clock and silence its own Oct-1 alert. Document the byte-identity
   outcome in STATE.md/deferred-live list exactly as the 2026-08-06 precedent did.
5. **If changed:** commit `data/` (CEAD + composite/enrichment rebuild), push, then
   **dispatch `deploy-manual.yml`** (`workflow_dispatch`) — a data-only push matches no `paths`
   filter and Cloudflare auto-build is off (H-05 closed by this exact workflow), so nothing else
   will rebuild production for a quarterly CEAD push.
6. Either outcome: re-evaluate the quarterly-cadence assumption if data comes back unchanged a
   second consecutive quarter in a row (DEPLOYMENT.md's own "Open question this raises" —
   worth restating in the phase's docs update if the Oct-1 scrape is also byte-identical).

**Recommendation for the plan:** ship HYG-06 as an explicit `checkpoint:human-verify` /
operator-gated task with the above 6-step runbook attached, scheduled for on/after 2026-10-01,
and add it to the deferred-live list now (per directive instruction) since today's date makes
it non-executable in this phase pass.

## 7. HYG-07 — GSC sitemap submission

**Confirmed operator-only** — the directive (`v2.2-AUTONOMOUS-DIRECTIVE.md:71,128`) and
`REQUIREMENTS.md:61` both explicitly assign this to the operator; no code/CLI path in this repo
can authenticate to Google Search Console.

**What's mechanically ready today (curl-verified):**

| URL | Status |
|-----|--------|
| `https://ischilesafe.com/sitemap-index.xml` | 200 |
| `https://ischilesafe.com/sitemap.xml` | 404 (expected — `@astrojs/sitemap` emits an index file, not a flat `sitemap.xml`, per CLAUDE.md's i18n section) |

The sitemap the operator should submit in GSC is `https://ischilesafe.com/sitemap-index.xml`
(confirmed live, 200). Recommended plan action: a short operator-facing instruction block (URL
to submit, expected GSC property, and a note that this closes the item "carried over from
22-03") — no code task needed. If the owner declines to do this manually, the alternative is to
formally retire the requirement (mark it explicitly out-of-scope in ROADMAP/REQUIREMENTS rather
than leaving it silently pending) — either resolution satisfies HYG-07's "done or formally
retired" wording.

## Test Baseline (measured 2026-09-23)

- **pytest:** `python -m pytest pipeline -q -p no:cacheprovider` → **611 passed, 1 skipped, 2
  xfailed** in 84.03s, exit 0. (Note: this is well above the directive's 2026-09-22 "Baseline"
  line of "395 passed / 1 skipped / 1 xfailed" — that baseline predates phases 34-37's test
  additions; 611 is the correct current-tree number to cite when writing this phase's plan, not
  395.)
- **vitest:** `site/package.json` `"test": "vitest run"`, `"vitest": "^4.1.10"`. 10
  `*.test.*` files found under `site/` (not run in this pass — read-only research; the planner
  should capture a fresh count at plan time since Phase 36 will touch pipeline/news code,
  which does not affect vitest count, but a frontend-adjacent HYG-02 change might add a new
  spec).
- **Workflow lint / CI:** not re-run in this research pass (no changes made); `ci.yml`
  runs `frontend` (build+validate), `pipeline` (pytest), `lint-workflows`
  (`.github/scripts/lint-workflows.sh`) — HYG-04's workflow YAML edit must pass
  `lint-workflows.sh` locally before push (master-push is not CI-linted, per
  DEPLOYMENT.md's own documented gap).

## Common Pitfalls

### Pitfall 1: Treating `pending.json`'s current 404 as "already fixed"
**What goes wrong:** Concluding HYG-01 is a no-op for `pending.json` because it 404s today.
**Why it happens:** The file only exists when the retry queue is non-empty between runs —
today's 404 is absence-of-file, not an exclusion rule.
**How to avoid:** The sync-data.mjs exclusion (§ 1) must explicitly exclude `pending.json` by
name (not rely on its current absence), so a future run with a non-empty queue doesn't
regress this silently.
**Warning signs:** A validator asserting "pending.json 404s" that passes vacuously today and
would also pass if the file were simply never excluded — write the validator against a
synthetic populated `dist/` fixture, or assert the sync script's denylist directly, not just
prod's current empty state.

### Pitfall 2: Fixing HYG-02 by adding noindex or a redirect
**What goes wrong:** The most common cannibalization fix (redirect the weaker page, or noindex
one) is explicitly banned by the governing directive for this pair of pages.
**Why it happens:** It's the default SEO playbook and easy to reach for.
**How to avoid:** Only title/H1/meta-description differentiation by intent is in scope; both
pages keep serving, both keep self-canonicalizing, both stay indexable.

### Pitfall 3: Implementing HYG-03 pruning without a schema migration plan
**What goes wrong:** Writing prune-by-first_seen logic against a `seen.json` where no entry has
`first_seen` crashes or silently treats every entry as brand-new (worst case: prunes nothing,
or prunes everything, depending on the default/fallback chosen).
**How to avoid:** Explicit migration step: backfill `first_seen = date` for all 6,976 existing
entries in one pass, then switch the write path (`seen[url] = ...`) to a `{date, first_seen}`
object schema going forward, before any prune logic runs against it.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | HYG-06 runtime estimate ("tens of minutes, single-digit hours worst case") is inferred from the 2.5s per-call delay × 346 communes × ~2 call sites, not measured directly (DEPLOYMENT.md does not record the 2026-08-06 run's wall-clock time) | § 6 | Low — informational only, operator will observe actual runtime live |
| A2 | `data/SOURCES.md` counts as in-scope "docs" for HYG-05 rather than restricted `data/` mutation | § 5 | Medium — if wrong, the classifier-name fix (the most reader-visible drift item) would need explicit owner sign-off before editing; flagged for orchestrator decision as instructed |

**If this table is empty:** N/A — two items above need confirmation.

## Open Questions

1. **Does the owner want seen.json/rejected/ served at all (HYG-01 Option A vs B)?**
   - What we know: zero site consumers, R2 already archives them independently, directive
     frames it as "the owner decides."
   - What's unclear: whether there's an external/reader-facing transparency reason to keep them
     public that isn't visible from the code.
   - Recommendation: default to Option A (exclude) unless the owner states a reason to keep
     them public; it's the reversible, lower-risk choice (adding back is one line; removing
     after being indexed/linked externally is harder).

2. **Should HYG-04's fix also add a positive-signal alert for the four builder steps** (so a
   quarter where the scraper itself succeeds — post-2026-10-01 — but a builder script breaks is
   distinguishable from CRON-05's expected 403)?
   - What we know: removing `continue-on-error` makes the whole job fail loudly, which is
     directionally correct per HYG-04's literal text.
   - What's unclear: whether the existing failure-alert issue body (worded around the 403 case)
     needs updated wording to not mislead a reader when the failure is actually a downstream
     builder bug after a successful local scrape.
   - Recommendation: planner should read the existing issue-body text (`cead-scraper.yml:130-137`)
     and decide whether it needs a builder-failure branch, or whether the existing
     "otherwise a real regression" catch-all sentence is sufficient — this is a judgment call,
     not a blocking gap.

## Sources

### Primary (HIGH confidence — direct file reads / command execution this session)
- `site/scripts/sync-data.mjs` — full read, copy-rule mechanics
- `pipeline/scrape_news.py` (lines 76-140, 242-340) — seen/pending ledger read/write paths
- `pipeline/news/classifier.py` (lines 12-139) — live default model resolution
- `data/SOURCES.md` (lines 405-430) — classifier documentation drift
- `.github/workflows/cead-scraper.yml` — full read, continue-on-error audit
- `pipeline/tests/test_workflow_guards.py` (targeted greps, lines ~512-676) — existing coverage
- `DEPLOYMENT.md` (lines 1-30, 237-271, 567-591) — CEAD runbook, workflow cadence table
- `.planning/STATE.md` (line 18 banner, structure scan to line 699) — staleness confirmation
- `CLAUDE.md` (Technology Stack section) — version claims
- `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 38 sections) — requirement text and constraints
- `site/src/pages/map.astro`, `site/src/pages/chile-crime-map.astro` — full read, title/H1/meta source
- `site/scripts/validate/seo.mjs` — full read, existing SEO validator coverage
- `data/incidents/seen.json` — measured via Python (6,976 entries, schema)
- Live prod curls (2026-09-23): `/map/`, `/chile-crime-map/`, `/es/mapa/`, `/es/mapa-delito-chile/`, `/data/incidents/{seen,pending,current}.json`, `/data/incidents/rejected/2026-09.json`, `/sitemap-index.xml`, `/sitemap.xml`
- `pytest pipeline -q` execution this session — 611/1/2 result
- `pip show openai`, `pipeline/requirements.txt`, `site/package.json` — version cross-check
- `~/.claude/.../memory/MEMORY.md` + `granite-default-classifier.md` — memory staleness check
- `gh run list --workflow=news-pipeline.yml` — confirmed 5 recent successful runs (2026-09-23)

### Secondary / Tertiary
None used — this phase required no external documentation lookup.

## Metadata

**Confidence breakdown:**
- HYG-01/02/03/04: HIGH — every claim backed by a file:line read or a live curl/command this session
- HYG-05: HIGH for the concrete version/model-name drift (directly diffed against installed versions); MEDIUM for the STATE.md "which blockers are resolved" sub-task (requires cross-referencing multiple memory files at plan time, not exhaustively done here)
- HYG-06: HIGH on the procedure (fully documented precedent exists); N/A on execution (date-gated, correctly deferred)
- HYG-07: HIGH — operator-only status confirmed by directive text and live sitemap curl

**Research date:** 2026-09-23
**Valid until:** ~7 days for the prod curl snapshots and pytest count (fast-moving — daily
news cron + in-flight v2.2 phases churn these numbers); ~30 days for the structural findings
(file locations, workflow YAML, validator coverage, schema absence of first_seen).
