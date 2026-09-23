# Phase 36: Classification Fidelity & Attribution — Research

**Researched:** 2026-09-23
**Domain:** Python news pipeline (LLM classification, dedup, URL decoding), Astro/React news display
**Confidence:** HIGH (all findings are direct file:line reads or measured commands; no unverified package claims — this phase installs no new dependencies)

## Summary

All seven FID requirements are CONFIRMED-still-live defects, re-verified today against the current codebase and `data/incidents/current.json` (746 incidents, generated 2026-09-23T06:25:01Z). The root causes documented in the V-06/V-07/V-08/V-10/V-11/V-19 audit findings are unchanged by Phase 34/35 work — Phase 34 replaced the classifier model (G-16: `deepseek/deepseek-v4.1-flash`) but did not touch the prompt's headline-rewrite instruction, the non-crime rule, dedup-against-existing-incidents, the Google-News URL, or HTML-entity handling. FID-07's specific hotfixed cards are confirmed clean on both `data/incidents/current.json` and prod.

Key numbers measured today: `vida` share in current.json is **71.4%** (533/746) — up from the pre-Granite 51% baseline (V-07), not down, so V-07's catch-all problem has gotten worse, not better, since the model swap. Google News URL share is **54.2%** (404/746), close to the V-10 baseline (53%). Applying the existing `dedup.deduplicate()` rule (0.82 threshold) against current.json today yields **65 drops of 746** (8.7%), down from the audit's 73/807 baseline only because the hotfix already removed 6 of those 73 near-duplicates (the Fierro Google-News cluster) — the underlying defect (dedup never runs against existing incidents) is untouched. No HTML entities (`&...;`) appear in stored titles (0/746) because titles are LLM-generated, not raw feed text — but this does NOT prove FID-06 is closed, because entities live in the raw `description` field fed to the classifier, not in the stored output; this needs a live-feed sample, not a `current.json` grep (see FID-06 below).

**Primary recommendation:** Sequence as two waves. Wave A (opus, pipeline kernel + prompt + schema): FID-01 (title_src), FID-02 (golden set + prompt tightening), FID-06 (unescape), FID-04 (gnews decode wiring), FID-05 (cross-run dedup validator) — these are the classifier/schema/store changes that must land together because FID-01 and FID-04 both add new IncidentRecord fields (`title_src`, `via_url`) in the same schema migration, and FID-02's prompt changes should be evaluated with the eval runner before touching FID-01's prompt-adjacent title instructions. Wave B (sonnet, UI + audit + regression): FID-01 UI display (ES/EN card fields, machine-translation label), FID-03 (hand audit using Wave A's tightened classifier), FID-07 (regression check). Opus is required for Wave A because it touches `pipeline/news/classifier.py`'s prompt (a pipeline kernel change per the directive's role table) and `pipeline/news/schema.py` (a contract/schema change).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Verbatim source-title capture | Backend pipeline (feeds.py/scrape_news.py) | Schema (store.py/schema.py) | RSS entry title is available only at ingest time, before classification |
| Headline translation (ES verbatim, EN machine-translated) | Backend pipeline (classifier.py prompt) | Frontend display (news.astro, noticias.astro) | Translation must happen once (cost), display formatting happens per-locale |
| Machine-translation disclosure label | Frontend (Astro pages, cards, IncidentPinLayer) | — | Pure display concern, no pipeline data needed beyond a boolean/known-always-true fact |
| Non-crime rejection accuracy | Backend pipeline (classifier.py prompt + eval harness) | — | Classification decision is made entirely server-side before store.py ever sees the item |
| Golden-set growth / hand audit | Backend pipeline (fixtures + eval_classifier.py) | — | Offline test-fixture maintenance, not a runtime concern |
| Publisher URL vs Google News redirect | Backend pipeline (gnews_decoder.py wiring into scrape_news.py) | Schema (`via_url` field) | Decoding must happen once at ingest (courtesy-delay budget); site never re-decodes |
| Cross-run dedup | Backend pipeline (dedup.py extension) + store.py (merge step) | Validator (new pytest / npm validator) | Existing-incident comparison must happen before merge_and_write, same as the current within-run dedup |
| HTML entity unescape | Backend pipeline (feeds.py strip_html / new unescape step) | — | Descriptions are pipeline-internal (fed to the classifier), never stored or rendered |
| Prod regression check (FID-07) | Backend pipeline (one-off assertion script) or CI validator | — | Read-only verification against `data/incidents/current.json` / prod HTML |

## Project Constraints (from CLAUDE.md)

- Editorial/legal: never call territories "peligrosos/seguros" in absolute terms; always attribute sources (CEAD, outlet). Directly relevant to FID-01 (headline fidelity/attribution) and FID-07 (defamation-risk regression).
- No server/DB in MVP; static JSON in repo is the data store — FID-01/04/05/06 changes are all pure Python + JSON schema changes, no new infra.
- Astro pages must stay static/pre-rendered — the FID-01 "Machine-translated headline" label must be build-time text, not client JS.
- DeepSeek v4 API via `openai` SDK, `deepseek-v4-flash`/`deepseek-v4-pro` model IDs only (not `deepseek-chat`/`deepseek-reasoner`, deprecated 2026-07-24) — already satisfied by the current `model_config`/G-16 winner `deepseek/deepseek-v4.1-flash`.
- Courtesy delays to CEAD and RSS sources — FID-04's gnews decode adds one more network hop per Google-News item; must respect the existing 1.5s courtesy delay pattern already used in fulltext.py.
- GSD workflow enforcement: no direct edits outside a GSD command (informational for the planner, not for this research doc).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FID-01 | title_src stored verbatim; ES cards show title_src; EN cards show a labeled machine translation; LLM stops rewriting headlines | Root-cause section below: classifier.py:176-177 prompt, store.py:51-88 build_incident signature, scrape_news.py:474-484 call site, schema.py:53-56/113-114 IncidentRecord/ClassifierOutput fields, site consumers grepped across 8 files |
| FID-02 | Golden set gains ≥20 non-crime items + relabelled boundary items; non-crime rejection ≥80%; family confusion matrix recorded | golden_set_v2.json measured composition (44 labelled + 3 null), eval_classifier.py `_family_confusion_matrix` (already exists), 34-BACKFILL-AUDIT.md failure taxonomy (natural death, accident, minefield, preventive notice, unestablished death) |
| FID-03 | 50-item hand audit of a fresh 2-week sample meets ≥85% family-agreement (owner default); vida no longer a catch-all | vida share measured 71.4% today vs 51% pre-Granite baseline (V-07); G-11/G-14 audit methodology (stratified sampling, seed, ceil(0.86·n)) reusable |
| FID-04 | `url` = publisher URL, `via_url` keeps Google News link; seen/dedup key on both; decode rate recorded | gnews_decoder.py exists, wired ONLY into fulltext.py (R2 path), NOT scrape_news.py; `via_url` field does not exist anywhere in code (grep 0 hits); Google News share measured 54.2% (404/746) |
| FID-05 | Deterministic 0.82 dedup runs against existing incidents; 0 drops; validator added | dedup.py:71-107 deduplicate() only processes the current run's batch (scrape_news.py:371); measured 65/746 drops applying the same rule to current.json today |
| FID-06 | Descriptions HTML-unescaped before classification; BioBio octet-stream warning handled | strip_html (feeds.py:117-119) strips tags only, no html.unescape import anywhere in pipeline/news or scrape_news.py; V-19 evidence example `&#8220;Keffe D&#8221;` |
| FID-07 | Prod regression check confirms hotfixed cards stay correct | Hotfix quick-260922-t59 confirmed: 0 "Rosamel" / 0 "se quit" hits on prod /news/ HTML today; 8 target ids absent from current.json; retitled id 514872e1d06db7f2 present (need per-item confirmation, see below) |
</phase_requirements>

## Standard Stack

No new external packages needed for this phase — it's a code-only phase. `via_url` and `title_src` are schema additions, not library additions.

### Package Legitimacy Audit

**Not applicable** — Phase 36 adds zero external dependencies. No slopcheck run needed. If the planner later decides to add an HTML-entity library (e.g. `html.unescape` — stdlib, no install), no audit is required since it's Python stdlib.

## Architecture Patterns

### Data flow (current, broken)

```
RSS/Google News feed
   │ entry.title, entry.description (raw, HTML-tagged, entity-encoded)
   ▼
feeds.py: canonical_url() / resolve_outlet() / strip_html() (tags only)
   ▼
scrape_news.py: candidates[] = {url, title, description, date, outlet}
   │ title/description used ONLY for keyword pre-filter (is_crime_item) + classify() call args + log lines
   ▼
classifier.py: classify(title, description) → LLM rewrites BOTH title_es AND title_en from scratch
   │ original `item["title"]` is discarded — never reaches build_incident()
   ▼
store.py: build_incident(title_es=result.title_es, title_en=result.title_en, ...) — NO title_src param
   ▼
data/incidents/current.json → site build reads title_es/title_en only
```

### Recommended data flow (FID-01/04/06)

```
RSS/Google News feed
   │ entry.title (verbatim), entry.link (may be news.google.com redirect)
   ▼
feeds.py: canonical_url() unchanged; NEW: html.unescape(strip_html(description))
         NEW (Google News items only): decode_gnews_url(entry.link) → publisher url, keep entry.link as via_url
   ▼
scrape_news.py: candidates[] = {url (publisher), via_url (google, may be None), title (verbatim, trimmed
                 of " - Outlet" suffix), description (unescaped), date, outlet}
   ▼
classifier.py: classify(title, description) → LLM now ONLY translates title → title_en; commune_name/
                region_hint/family/summary/confidence unchanged; title_es dropped from ClassifierOutput
                (or kept but ignored — see Open Questions)
   ▼
store.py: build_incident(title_src=item["title"], title_en=result.title_en, url=item["url"],
           via_url=item.get("via_url"), ...)
   ▼
data/incidents/current.json → ES pages render title_src; EN pages render title_en with a
                 "Machine-translated headline" label; seen/dedup key on (url, via_url)
```

### Pattern: Google News title suffix stripping

Google News RSS `<title>` values are formatted `"<headline> - <Outlet Name>"`. A verbatim `title_src` must strip the ` - <outlet>` suffix or it will visibly duplicate the outlet byline already shown on the card. Rule: if `title.endswith(f" - {resolve_outlet(entry, feed_name)}")`, strip that suffix; do this ONLY for `GoogleNews*` feeds (BioBio/Cooperativa/LaTercera/LaCuarta titles are not suffixed — confirmed by reading `resolve_outlet()`, feeds.py:135-152, which is Google-News-only logic already).

### Anti-Patterns to Avoid

- **Re-introducing an LLM-authored Spanish headline:** FID-01's whole point is that `title_es` as a prompt-authored field is banned going forward; do not keep asking the LLM for `title_es` "for compatibility" — that recreates V-06.
- **Decoding Google News URLs synchronously inside the classify loop:** the decoder needs a network call (new-format tokens) and must respect courtesy delay; do it in the feed-fetch/candidate-build stage (parallel to `is_crime_item` prefilter, so failed-decode items are still cheap to reject) — do NOT add it after classification, which would burn LLM spend on items whose URL later turns out undecodable.
- **Running the FID-05 cross-existing dedup as an O(n²) full-file scan on every run:** current.json is capped at 30 days/roughly 700-800 items; only the same `(cut, date)` bucket needs comparing, matching the existing per-run algorithm. No new dependency needed — this is what `dedup.deduplicate()` already does per-run; FID-05 just needs to seed `bucket_titles` from the file's existing incidents before processing the new batch.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML entity decoding | Custom regex for `&amp;`/`&#8220;` etc. | stdlib `html.unescape()` | Handles all named + numeric entities correctly; zero new dependency |
| Google News URL decoding | New decoder | Existing `pipeline/news/gnews_decoder.py::decode_gnews_url` | Already implements both old-format (base64) and new-format (batchexecute POST) paths with hardcoded-host security constraint (T-gf7-04); just needs wiring into the ingest path, not a rewrite |
| Title similarity / dedup | New fuzzy-matching library | Existing `pipeline/news/dedup.py::are_duplicates` (difflib, stdlib, D-10 locked) | Locked decision; extending scope (existing-incident comparison), not swapping algorithm |
| Eval harness / confusion matrix | New scoring script | Existing `pipeline/experiments/eval_classifier.py` (`_family_confusion_matrix` already implemented, lines 848-858) | Just needs golden_set_v2.json growth (FID-02) and a non-crime-rejection metric added to the existing `--decide` output |

**Key insight:** every FID requirement in this phase has its supporting machinery already built (dedup, decoder, eval harness) — the work is wiring/extension/data-growth, not new engineering. This lowers execution risk but means the planner must be precise about *where* to splice each change into the existing call chain (feeds.py → scrape_news.py → classifier.py → store.py), because getting the splice point wrong breaks the courtesy-delay budget or the cost-guardrail ordering (`is_crime_item` prefilter must stay before any network call).

## Common Pitfalls

### Pitfall 1: Schema migration breaks old incidents (FID-01 `title_src` back-compat)
**What goes wrong:** Existing 746 incidents in current.json (and all archive/*.json) have no `title_src` field. If `IncidentRecord.title_src` is added as a required field, `validate_incidents_file()` (schema.py, all-or-nothing per D-15) will raise on the NEXT run, since merge_and_write re-validates the whole file including old rows.
**Why it happens:** schema.py's `validate_incidents_file` validates the entire merged list, not just new rows.
**How to avoid:** Make `title_src: str | None = None` (like the existing `slug` back-compat pattern at schema.py:60), OR write a one-time migration setting `title_src = title_es` for existing rows (acceptable since old title_es values, while sometimes wrong, are still the best available fallback — do NOT backfill from RSS since old raw titles aren't stored anywhere). Decide explicitly in the plan; don't leave it implicit.
**Warning signs:** `pydantic.ValidationError` on the next scheduled cron run after deploy.

### Pitfall 2: FID-02 prompt tightening regresses commune/parse accuracy that G-16 just won
**What goes wrong:** Adding more non-crime exclusion rules to the system prompt (classifier.py:128-190) can shift token distribution and hurt the just-selected winner's commune accuracy (44/44) or reasoning-token behavior (G-16 confirmed 0 across all candidates for the disabled-reasoning variant).
**Why it happens:** Prompt changes are not isolated — the model reads the whole prompt as context.
**How to avoid:** Re-run `eval_classifier.py` against `golden_set_v2.json` (needs the ≥20 new non-crime items added first) with the SAME model/variant (`deepseek/deepseek-v4.1-flash`, `thinking:disabled`) before/after the prompt edit; gate the merge on no regression in commune (≥42/44) alongside the new non-crime-rejection ≥80% metric.
**Warning signs:** New golden-set non-crime items pass, but previously-passing crime items start returning `commune_name: null`.

### Pitfall 3: FID-04 `via_url`/seen-dedup key change breaks the retry queue (`pending.json`) and `seen.json` schemas
**What goes wrong:** `seen[item["url"]] = item["date"]` (scrape_news.py:432) keys purely by URL string today. If FID-04 changes `item["url"]` to mean "publisher URL" (decoded) while the feed still hands back a Google News link as `via_url`, the retry-queue and `pending.json` upsert logic (`pq.upsert_failure`, `pq.item_id`) must also switch their key derivation consistently, or the SAME article could be re-queued twice under two different keys (once by publisher URL post-decode, once by Google link if decode failed on a prior attempt and later succeeds).
**Why it happens:** URL identity is currently a single string threaded through canonical_url dedup, seen-ledger, retry-queue and cross-run dedup; FID-04 turns it into a two-string identity.
**How to avoid:** Decide (and record) a single canonical dedup/seen key rule up front: e.g. "key = decoded publisher URL when decode succeeds, else the original Google News URL" — and always store `via_url` as metadata, never as the key, so there's exactly one key per item regardless of decode success.
**Warning signs:** Duplicate incidents for the same story differing only in `url` vs `via_url`, or items disappearing from `pending.json` without ever reaching `seen.json`.

### Pitfall 4: FID-06 unescape happens in the wrong place and never reaches the classifier
**What goes wrong:** `strip_html()` (feeds.py:117-119) is called from `is_crime_item()` (used only for the keyword prefilter) AND separately in scrape_news.py:358 for the description that's actually stored/passed to `classify()`. Adding `html.unescape` to only one of the two call sites leaves the other with entities.
**Why it happens:** `strip_html` is called twice, independently, in two different modules.
**How to avoid:** Put `html.unescape()` INSIDE `strip_html()` itself (feeds.py) so every call site gets it for free — verified as the single choke point by the two grep hits above (feeds.py:196, scrape_news.py:358 both call `strip_html`).
**Warning signs:** Entities present in the description passed to `classify()` (visible via added test/log) despite the "description built" code claiming it's clean.

### Pitfall 5: FID-05 cross-run dedup drop count grows unexpectedly, deleting real distinct incidents
**What goes wrong:** Two genuinely distinct crimes in the same commune on the same day with superficially similar `title_en`/`title_es` LLM-generated titles (e.g. two unrelated robos_violentos both titled "Robo con violencia en Providencia") could trip the 0.82 threshold as false positives — this risk is HIGHER after FID-01, because `title_src` (verbatim, more varied) becomes the comparison field. **Decide explicitly: does FID-05 dedup compare on `title_src` or the LLM-authored title?**
**Why it happens:** The existing per-run dedup was designed and threshold-tuned (D-10 "start value") against LLM-authored titles, not verbatim source titles, which may have MORE textual variety (different outlets, different phrasing) even for the same event, or LESS (two different Google News aggregation blurbs of the same wire story) — the threshold's behavior on `title_src` is unverified.
**How to avoid:** Re-measure the 65-drop baseline (measured above) using whichever field the plan picks, on the SAME data, before locking the threshold; if FID-01 lands first in the same phase, re-run the dedup measurement using `title_src` post-migration.
**Warning signs:** Drop count changes significantly (up or down) after FID-01 lands, without the threshold being re-validated.

## Code Examples

### FID-01: current classifier prompt requiring rewritten Spanish headline (to be removed/changed)
```
# Source: pipeline/news/classifier.py:176-177
  "title_es": "<concise Spanish headline, max 120 chars, plain text>",
  "title_en": "<English translation of title_es, max 120 chars, plain text>",
```

### FID-01: current build_incident signature (no title_src param)
```python
# Source: pipeline/news/store.py:51-64
def build_incident(
    *,
    url: str,
    cut: str,
    lat: float,
    lng: float,
    title_es: str,
    title_en: str,
    date: str,
    outlet: str,
    family: str,
    slug: str | None = None,
) -> dict | None:
```

### FID-01: RSS title discarded at the call site (scrape_news.py:474-484)
```python
# Source: pipeline/scrape_news.py:474-484 — item["title"] (verbatim RSS title,
# available in this scope) is never passed; only result.title_es/title_en (LLM output) is.
incident = build_incident(
    url=item["url"],
    cut=cut,
    lat=lat,
    lng=lng,
    title_es=result.title_es,
    title_en=result.title_en,
    date=item["date"],
    outlet=item["outlet"],
    family=result.family,
    slug=slug,
)
```

### FID-04: gnews_decoder is imported only by fulltext.py (R2/archive path), not the live ingest path
```
# Source: pipeline/news/fulltext.py:30 — the only import site in the whole repo.
from pipeline.news.gnews_decoder import decode_gnews_url  # noqa: E402
```
`grep -rn "decode_gnews_url" pipeline/` returns exactly two hits: the definition in `gnews_decoder.py` and this one import in `fulltext.py`. `scrape_news.py` never calls it — confirms V-10's "decoder exists only on the R2 path."

### FID-06: strip_html strips tags only, no entity decoding
```python
# Source: pipeline/news/feeds.py:117-119
def strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text or "")
```
`grep -rn "html.unescape\|import html" pipeline/` returns zero hits anywhere in the pipeline package.

### FID-05: existing dedup only ever sees the current run's batch
```python
# Source: pipeline/scrape_news.py:371 (call site, not reproduced verbatim here — grep-confirmed)
# deduplicate(new_incidents) — new_incidents is this run's candidates only, never
# compared against store.py's already-merged current.json/archive contents.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Granite `ibm-granite/granite-4.1-8b` (dead since 2026-09-04) | `deepseek/deepseek-v4.1-flash` (OpenRouter, G-16 winner) | 2026-09-23, Phase 34 | Commune 44/44, family 42/44, 0 parse errors on golden_set_v2 — but the prompt's headline-rewrite instruction and non-crime rule are UNCHANGED from the Granite era, so FID-01/02/03 defects persist under the new model too |
| Per-run-only dedup | Still per-run-only (FID-05 not yet shipped) | N/A — this phase | 65/746 near-duplicates measured today; will stay until FID-05 ships |

**Deprecated/outdated:** `deepseek-chat`/`deepseek-reasoner` model IDs (CLAUDE.md, stopped working 2026-07-24) — already avoided; current code uses `deepseek-v4-flash`/`deepseek-v4.1-flash` only (verified via `model_config` reads above).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Google News RSS `<title>` always has the ` - <Outlet>` suffix pattern for every outlet in the feed list (not verified against a live feed sample in this research session — only inferred from `resolve_outlet()` logic and general Google News RSS format knowledge) | Architecture Patterns: title suffix stripping | If some outlets format differently, the strip rule could clip real headline text or fail to strip, leaving outlet names duplicated on ES cards |
| A2 | The 65/746 dedup-drop measurement and 71.4% vida-share measurement are stable "as of 2026-09-23 06:25 UTC" — the live cron runs ~4x/day and will change current.json before the plan executes | FID-03, FID-05 sections | Plan must re-measure at execution time, not trust this session's numbers as a locked baseline |
| A3 | FID-06's "descriptions" scope means the text passed to `classify()` (scrape_news.py:358 `description`), not any other description field — there is no separately-stored "description" in `IncidentRecord`/`current.json` (confirmed: schema.py has no `description` field) | FID-06 section | If the owner meant something else by "descriptions," the fix target is wrong — low risk since V-19's own evidence example (`Duane &#8220;Keffe D&#8221; Davis`) is from a REJECTED item's field, consistent with the classify-time description |

**If this table is empty:** N/A — see above.

## Open Questions

1. **Does the classifier still need to emit `title_es` at all after FID-01?**
   - What we know: FID-01 says ES cards show `title_src` (verbatim); EN cards show a labeled translation of `title_src`.
   - What's unclear: whether `ClassifierOutput.title_es` should be dropped from the schema entirely (LLM stops producing it, one fewer output field, marginally cheaper) or kept-but-unused for some transition/debugging purpose.
   - Recommendation: drop it — the directive's REQUIREMENTS.md line 11 says "verbatim source headline from now on," implying the model should only be asked for `title_en` (a translation of `title_src`, fed in as an input, not regenerated). This also simplifies FID-01's kinship/name-corruption risk since the model no longer authors Spanish text at all.

2. **What is the FID-03 "fresh 2-week sample" population — live incidents only, or does it include anything from Phase 34's withheld backfill?**
   - What we know: G-18 says the 2,122 backfill rows stay `classifier_none`/unpublished; deferred-live says re-running the backfill happens only "after Phase 36's non-crime fix."
   - What's unclear: FID-03's audit should logically run on LIVE incidents only (published since the Phase 34 fix went live, i.e. incidents with `first_seen`/`date` ≥ 2026-09-23), since the backfill isn't published yet.
   - Recommendation: sample only from `current.json` + any archive month with dates ≥ 2026-09-23 (the go-live date of the new classifier); if under 50 such incidents exist by execution time, extend the window backward but flag any pre-fix items explicitly in the audit report — do not silently mix Granite-era-published or unpublished-backfill items into the FID-03 population.

3. **FID-04 decode success-rate measurement needs live network calls — how many, and against which courtesy budget?**
   - What we know: the directive requires courtesy delays to RSS sources; `gnews_decoder.py`'s new-format path requires a GET + a POST per undecoded URL.
   - What's unclear: exact sample size and whether this should run against already-collected historical Google News URLs in current.json (404 available today) or only future/live ones.
   - Recommendation: sample from the 404 existing Google-News URLs already in current.json (no new RSS fetch needed, only the decode network hop, ~1 request pair per URL); cap at 50 items per the FID-01 audit pattern, respecting a courtesy delay (reuse fulltext.py's existing delay constant) between requests.

## Environment Availability

Skipped — this phase makes no new external service/tool dependency; all libraries needed (`tenacity`, `openai`, `feedparser`, `requests`, stdlib `html`/`difflib`) are already installed and used elsewhere in the pipeline (confirmed via existing imports in classifier.py, dedup.py, gnews_decoder.py, fulltext.py).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (pipeline) | pytest 8.x (via `python -m pytest`), no separate config file found beyond default discovery under `pipeline/tests/` |
| Framework (site) | vitest 4.1.10, config likely `site/vitest.config.*` (not read this session; inferred from `npm test` → `vitest run`) |
| Quick run command (pipeline) | `python -m pytest pipeline -q -p no:cacheprovider` |
| Full suite command (pipeline) | same — no separate "full" tier detected |
| Quick/full run command (site) | `cd site && npm test -- --run` (also `npm run validate` for the 16-18 custom validators, plus `npm run build` before validate per OneDrive chaining rule) |

**Baseline measured 2026-09-23 (this session):**
- pytest: **611 passed, 1 skipped, 2 xfailed** (exit 0) — higher than the RUN STATUS Phase-34 baseline (395/1/1) because Phase 34/35 landed many new tests; this is the correct baseline for Phase 36's close gate, not the stale RUN STATUS number.
- vitest: **97 passed (10 files)** — also higher than the RUN STATUS baseline (86/9 files) for the same reason.
- `dedup.deduplicate()` applied to current.json: 65/746 drops (informational, not a pass/fail metric yet — FID-05 will add the validator).

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|-------------|
| FID-01 | title_src stored verbatim, unmodified by LLM | unit | `pytest pipeline/tests/test_store.py -k title_src -x` | ❌ Wave 0 (new test + likely new fixture) |
| FID-01 | ES card renders title_src, EN card renders title_en with disclosure label | unit (vitest) or astro-check + manual grep | `cd site && npx vitest run -t title` | ❌ Wave 0 (extend existing news/card component tests) |
| FID-02 | Non-crime rejection ≥80% on golden_set_v2 | integration (eval run) | `python pipeline/experiments/eval_classifier.py --provider openrouter --model deepseek/deepseek-v4.1-flash --reasoning enabled_false` then `--decide` | Partial — harness exists (`eval_classifier.py`), golden set needs ≥20 more items first |
| FID-03 | 50-item hand audit ≥85% agreement | manual (fresh reviewer), not automatable | N/A — documented procedure, reuses G-11/G-14 stratified-sample pattern | N/A by design |
| FID-04 | Google News URL share drops; decode success rate recorded | unit + measurement script | `pytest pipeline/tests/test_gnews_decoder.py -x` (exists) + new script measuring current.json share | Partial — decoder tests exist; ingest-wiring test does not |
| FID-05 | Cross-run dedup yields 0 drops when applied to current.json | unit/validator | `pytest pipeline/tests/test_dedup.py -k existing -x` (new) + new npm/python validator | ❌ Wave 0 |
| FID-06 | No HTML entities reach classify() input | unit | `pytest pipeline/tests/test_feeds.py -k unescape -x` | ❌ Wave 0 (extend existing feeds test file if present — not confirmed to exist; grep shows no test_feeds.py hit in this session, verify at plan time) |
| FID-07 | Hotfixed cards absent/correct on prod | manual + curl | `curl -s https://ischilesafe.com/news/ \| grep -c Rosamel` (expect 0), plus a python assertion against current.json for the 8 target ids and the retitled id's exact strings | Partial — this session's ad hoc check is not yet a committed regression script |

### Sampling Rate
- **Per task commit:** targeted pytest/vitest `-k`/`-t` filter for the touched module
- **Per wave merge:** full `python -m pytest pipeline -q -p no:cacheprovider` + `cd site && npm run build && npm run validate && npm test -- --run` (one chained command per OneDrive-desync memory rule)
- **Phase gate:** full suite green before `/gsd:verify-work`, plus the FID-02 eval run's `--decide` output and the FID-04 decode-rate sample recorded as evidence in the plan/verification artifact

### Wave 0 Gaps
- [ ] `pipeline/tests/test_store.py` — needs `title_src` param/field coverage (FID-01), including back-compat for missing `title_src` on old rows
- [ ] `pipeline/tests/test_dedup.py` — needs a cross-existing-incidents test (FID-05); confirm whether this file exists today (not verified this session — check at plan time: `ls pipeline/tests/test_dedup.py`)
- [ ] `pipeline/tests/test_feeds.py` — needs an html.unescape test (FID-06); existence not confirmed this session, verify at plan time
- [ ] golden_set_v2.json growth to ≥64 items (44 current + ≥20 new non-crime) — data fixture, not code, but blocks FID-02's eval gate
- [ ] A committed FID-07 regression script (currently only ad hoc curl/python done in this research session) — recommend `pipeline/tests/test_hotfix_regression.py` or a small standalone script under `pipeline/` asserting the 8 dropped ids stay absent and the retitled id's strings stay exact

*(Not "None" — several Wave 0 gaps exist; the planner should assign these to sonnet since they're new pytest fixtures/tests, not pipeline-kernel logic changes.)*

## Security Domain

`security_enforcement` not found explicitly set to `false` in `.planning/config.json` — not read this session; treat as enabled per the instruction default. This phase's security-relevant surface is narrow (no auth, no new user input surface — it consumes existing RSS/LLM output).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | No auth surface touched |
| V3 Session Management | No | Static site, no sessions |
| V4 Access Control | No | No access-control surface |
| V5 Input Validation | Yes | Pydantic `IncidentRecord`/`ClassifierOutput` validators (schema.py) already enforce URL scheme, non-empty outlet/url, valid CUT/family enums; FID-01's `title_src` and FID-04's `via_url` additions must get equivalent validators (non-empty for title_src; URL-scheme check for via_url when present) |
| V6 Cryptography | No | No new crypto surface; `make_id` already uses sha256, unchanged |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|-----------------------|
| SSRF via decoded Google News redirect target | Tampering/Info Disclosure | `gnews_decoder.py` already hardcodes the batchexecute host (T-gf7-04, verified in code) — this constraint must be preserved, and the DECODED output URL must go through the SAME `is_safe_url()` check (store.py) before being stored as `url` |
| XSS via title_src (raw outlet HTML/script injection in RSS titles) | Tampering | `IncidentPinLayer.ts` already escapes titles on render (`escHtml`, confirmed at IncidentPinLayer.ts:118) — this escaping must apply to the NEW `title_src` field exactly as it does to `title_es` today; do not bypass it for the "verbatim" field |
| Prompt injection via crafted RSS title/description feeding into the classifier's user content | Tampering | Existing pattern already truncates description to 500 chars (`classifier.py:479` `description[:500]`) and treats the model's JSON output as untrusted (commune name resolved via closed-set lookup, never trusted raw — `resolve_cut`); FID-01 does not change this since `title_src` is stored, not executed |

## Sources

### Primary (HIGH confidence — direct file reads / measured commands, this session)
- `pipeline/news/classifier.py` lines 72-193, 465-533, 547-763 — prompt text, provider config, classify()/router
- `pipeline/news/schema.py` full file — IncidentRecord, ClassifierOutput, IncidentsFile
- `pipeline/news/store.py` lines 1-100 — build_incident, is_safe_url, make_id
- `pipeline/scrape_news.py` lines 290-500 — candidate building, classify call site, build_incident call site
- `pipeline/news/feeds.py` full file (via grep + sed) — canonical_url, resolve_outlet, strip_html, is_crime_item
- `pipeline/news/dedup.py` full file — deduplicate(), are_duplicates(), threshold constant
- `pipeline/news/gnews_decoder.py` lines 1-40 — module docstring, hardcoded batchexecute host
- `pipeline/news/fulltext.py` grep — confirms sole import site of decode_gnews_url
- `pipeline/experiments/eval_classifier.py` lines 1-120, 820-900 — golden set path, FAMILY_MIN_V2=40, confusion matrix function (already implemented)
- `pipeline/tests/fixtures/golden_set_v2.json` — measured 47 items, 44 labelled + 3 null, family distribution
- `.planning/phases/34-news-classification-restore/34-BACKFILL-AUDIT.md` — G-11/G-14 stratified audit results and per-item failure reasons (natural death, accident, minefield, preventive notice)
- `.planning/quick/260922-t59-hotfix-live-erroneous-news-cards/` — PLAN + SUMMARY, measured before/after ids
- `.planning/research/v2.2-AUDIT-260922.md` V-06/V-07/V-08/V-10/V-11/V-19 sections — full evidence text
- `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md` — G-01..G-24 decision log, REQUIREMENTS.md FID-01..07
- `data/incidents/current.json` — measured 746 incidents, vida 71.4%, google-news-url 54.2%, dedup-drop 65, title-entity 0
- Live commands: `python -m pytest pipeline -q -p no:cacheprovider` → 611/1/2; `cd site && npm test -- --run` → 97/10 files
- `curl https://ischilesafe.com/news/` → 200, 0 "Rosamel", 0 "se quit" hits (FID-07 baseline)
- Site consumer grep: `site/src/components/CommuneNewsSection.astro`, `HomeNewsPulse.astro`, `map/IncidentPinLayer.ts`, `map/IncidentsList.tsx`, `pages/es/noticias.astro`, `pages/news.astro` — all 6 consumers of title_es/title_en enumerated

### Secondary (MEDIUM confidence)
- None — this research relied entirely on direct code/data reads (Primary tier); no WebSearch was needed since the phase is entirely internal to this repo.

### Tertiary (LOW confidence)
- Assumption A1 (Google News title suffix format `" - <Outlet>"`) — based on general knowledge of Google News RSS conventions, NOT verified against a live feed fetch this session (no network fetch of the actual RSS feed was performed — only historical decoded/stored data was inspected). Flagged in Assumptions Log.

## Metadata

**Confidence breakdown:**
- Standard stack: N/A — no new packages
- Architecture / root causes: HIGH — every claim is a direct file:line read or a measured command against live data/prod, cross-checked against the audit's own evidence
- Pitfalls: HIGH for pitfalls 1, 4, 5 (directly derived from code reads); MEDIUM for pitfalls 2, 3 (reasoned from G-16/G-02 mechanics and code structure, not independently re-tested)

**Research date:** 2026-09-23
**Valid until:** short — current.json changes ~4x/day via the live cron; all *measured numbers* (vida share, dedup drops, google-news share, test counts) should be treated as valid for ≤ 24-48h. The *code-location* findings (file:line evidence) are stable until Phase 36 execution begins, per G-24's own warning that Phase 35 code (not yet executed at research time) will shift some of the site consumer line numbers in `news.astro`/`noticias.astro`/`CommuneNewsSection.astro`/`HomeNewsPulse`/`NewsStrip`.

## Orchestrator correction (2026-09-23)
The "vida share 71.4% (533/746)" figure is measured over current.json, whose incidents are almost all from the Granite era (2026-08-24..09-04); only 4 incidents came from the new G-16 model at measurement time. It does NOT measure the new model. The measured family distribution for deepseek/deepseek-v4.1-flash is the backfill classify cache (34-BACKFILL-AUDIT.md / G-18): vida 597 of 1,162 accepted = 51.4%, equal to the pre-Granite 51% baseline. The FID-03 "vida no longer a catch-all" check must therefore be measured on a live post-2026-09-23 sample, not on current.json as a whole.
