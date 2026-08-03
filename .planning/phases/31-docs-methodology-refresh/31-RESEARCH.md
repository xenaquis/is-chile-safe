# Phase 31: Docs & Methodology Refresh - Research

**Researched:** 2026-08-02
**Domain:** Documentation-correctness drift audit (prose vs. shipped code), not a technology survey.
**Confidence:** HIGH — every claim below was checked against the live repo tree by direct file read, Grep, or an executed command (`npm run build && npm run validate`, `pytest`). No claim in the Drift Table relies on training data alone.

## Summary

This is an evidence-backed drift audit, not a literature review. I read the EN+ES methodology pages, `data/SOURCES.md`, the news pipeline source (`pipeline/news/feeds.py`, `classifier.py`, `schema.py`), the composite index docs vs. `pipeline/build_composite_index.py`/`normalizer.py`, the map's `MapIsland.tsx`, `mapFilterDefs.ts`, and every validator in `site/scripts/validate/`. I ran the actual build+validate chain and the pytest suite rather than trusting STATE.md's cached numbers.

**Highest-value finding (Q5): the EN and ES methodology pages both contain a factually WRONG claim, not merely a stale one.** Both pages state "Rank 1 = lowest reported rate in Chile" (`site/src/pages/methodology.astro:325`, `site/src/pages/es/metodologia.astro:336`). The code that actually computes `national_rank` sorts by rate **descending** and assigns rank 1 to the **highest** rate (`pipeline/cead/normalizer.py:111-141`, docstring: "highest rate = rank 1"). Every other reader-facing surface (the commune page, `site/src/pages/commune/[slug].astro:100`) correctly documents "rank 1 = highest incidence" in a code comment, and DOCS-01 explicitly names this exact fact as a requirement — the methodology page is the one place on the entire site that gets this backwards, and it is the site's single most important editorial page for framing what "rank" means. This is a direct, provable factual error that would mislead a reader, not a style nit.

**Second-highest finding:** `data/SOURCES.md`'s "News feeds" section (lines 386-411) describes a pipeline that no longer exists. It lists four direct RSS feeds (Emol, BioBioChile, T13, Cooperativa) and "DeepSeek v4-flash" as the classifier. The actual code (`pipeline/news/feeds.py`) fetches exclusively via Google News RSS search queries (`news.google.com/rss/search`) with a decoder module (`gnews_decoder.py`) to resolve the real outlet, and the classifier (`pipeline/news/classifier.py:8,73-79`) defaults to `ibm-granite/granite-4.1-8b` via OpenRouter. SOURCES.md also has zero mention of the R2 full-text research archive (`pipeline/tests/test_archive_r2.py` exists and is a real, tested pipeline component per user memory) or of the `sexuales` news-only family. This is the single largest block of stale prose on the site and DOCS-03's primary target.

**Primary recommendation:** Phase 31 should be scoped as a **targeted correction pass over a short, enumerated list of provably wrong or provably stale claims** (this Drift Table), not a full rewrite of the methodology pages. Most of the composite-index, ENUSC, trend-formula, and "what we don't say" prose is currently accurate and should not be touched — touching working prose only creates new drift risk and anchor-breakage risk for no benefit.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Methodology/sources prose correctness | Static content (Astro `.astro` pages) | — | Pure pre-rendered HTML; no runtime component owns this |
| `national_rank` direction | Python pipeline (`pipeline/cead/normalizer.py`) | Astro consumer pages | Pipeline computes the truth; every doc/page is a consumer that must match it |
| News pipeline provenance (feeds, classifier) | Python pipeline (`pipeline/news/`) | `data/SOURCES.md` (doc consumer) | SOURCES.md must describe what the pipeline actually does, not vice versa |
| Figure-registry validator | Build tooling (`site/scripts/validate/figure-registry.mjs`) | `data/SOURCES.md` | Validator reads SOURCES.md as data; hardening the validator is a build-tooling change, in-phase per DOCS-05 |
| Map legend bands / `AVAILABLE_YEARS` | Browser/Client (`MapIsland.tsx`, `mapFilterDefs.ts`) | — | Pre-existing runtime defects; Phase 31 is DOCS-scoped, so these are candidates for a caveat line or a backlog item, not a code fix (see Q4) |

## User Constraints

No `CONTEXT.md` exists yet for Phase 31 (discuss-phase has not run for this phase at research time). The constraints below are drawn from `.planning/REQUIREMENTS.md` (DOCS-01..06), `.planning/ROADMAP.md` Phase 31 success criteria, `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`, and `CLAUDE.md`'s hard editorial rule. Treat these as locked:

- Never an unqualified absolute "safe/dangerous/seguro/peligroso" verdict about a territory (CI-enforced via `forbidden-language.mjs`).
- `data/` is READ-ONLY for this milestone — no data mutation, ever.
- This is a DOCS phase; DOCS-04 explicitly conditions the clustering-documentation requirement on Phase 26 having returned GO. Phase 26 returned **NO-GO** (see below) — do not build a reader-facing clustering explainer.
- OneDrive gotcha: chain `npm run build && npm run validate` in ONE command; `npm run validate` does NOT run vitest.
- Never put regex `\b` (or other backslash escapes) inside a shell-quoted `node -e` on this Windows/git-bash environment — it silently collapses to a backspace character (F-36). Any new validator logic belongs in a real `.mjs` file.
- Push authorization: the user has authorized `git push` when the phase-close gate is green (per the v2.1 directive) — this is inherited context, not a Phase 31-specific decision.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | EN+ES methodology pages current with composite index, ENUSC layer, `sexuales`, `national_rank` direction | Drift Table rows #1, #2, #7 — the `national_rank` claim is WRONG; composite index and ENUSC prose are OK; `sexuales` is entirely absent from both methodology pages |
| DOCS-02 | Editorial/legal disclaimers present and correct | Drift Table row #8 — "What this site does NOT say" section verified compliant; no changes needed |
| DOCS-03 | `SOURCES.md` current/canonical; ENUSC `[verify edition]` resolved; every outlet + CEAD attributed | Drift Table rows #3, #4, #5, #6 — News feeds section is the largest single drift block; `[verify edition]` is NOT resolvable from repo evidence (see Open Questions Q1) |
| DOCS-04 | Clustering behavior + facet semantics documented for readers, conditioned on Phase 26 GO | Phase 26 returned NO-GO (`.planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md`, STATE.md § Phase 26 Outcome) — the clustering half of DOCS-04 is N/A by its own text; facet semantics (time/region/family filters) ARE reader-relevant since Phase 28 shipped a facet UI with no reader-facing explanation anywhere. See Open Question Q2. |
| DOCS-05 | `figure-registry.mjs` hardened against stub-passing substring matching | Drift Table row #9 — concrete counterexample constructed and verified against the real file (see below) |
| DOCS-06 | EN/ES parity holds; no inbound anchor broken | Anchor inventory below; all currently-linked anchors resolve correctly in both locales as of this research (no drift found on this axis, but the rewrite must preserve them) |

## Drift Table

| # | Doc file:line | Current claim (quoted) | What the code actually does (file:line evidence) | Verdict | DOCS-req | Fix sketch |
|---|---|---|---|---|---|---|
| 1 | `site/src/pages/methodology.astro:322-325` | "the *national rank* shown on commune pages is computed across all non-low-population communes... Rank 1 = lowest reported rate in Chile for that year." | `pipeline/cead/normalizer.py:111-141` — `compute_ranks()` docstring: "Rank by rate_per_100k descending (highest rate = rank 1)"; `eligible_sorted = sorted(..., reverse=True)`; `records[i]["national_rank"] = rank` starting at 1 for the highest-rate commune. Also confirmed correct on the actual commune page: `site/src/pages/commune/[slug].astro:100` — code comment "national_rank/regional_rank are DESCENDING (rank 1 = highest incidence)". | **WRONG** (factually false, not stale) | DOCS-01 | Change "Rank 1 = lowest reported rate" to "Rank 1 = highest reported rate (most reported crime, not safest)" and add the same explicit non-safety-verdict qualifier used elsewhere on the page. |
| 2 | `site/src/pages/es/metodologia.astro:333-336` | "Ranking 1 = menor tasa reportada en Chile para ese año." (same claim, Spanish) | Same evidence as #1 — `compute_ranks()` is locale-agnostic; both pages describe the same field. | **WRONG** | DOCS-01, DOCS-06 (parity) | Same fix, translated; must land in the same commit as #1 to preserve EN/ES parity. |
| 3 | `data/SOURCES.md:386-411` ("News feeds — qualitative incident layer (RSS)") | Lists feeds as `Emol (https://www.emol.com/rss/)`, `BioBioChile`, `T13`, `Cooperativa`; "classified and geolocated by DeepSeek v4-flash (`pipeline/news/`)". | `pipeline/news/feeds.py:22-65` — `google_news_url()` builds `https://news.google.com/rss/search?q=...`; `_GOOGLE_NEWS_QUERIES` dict of named Google News search queries (e.g. `GoogleNews-Nacional`); `pipeline/news/gnews_decoder.py` exists solely to decode `news.google.com` redirect URLs back to the real outlet. `pipeline/news/classifier.py:8,73-79` — default model is `ibm-granite/granite-4.1-8b` via OpenRouter (`base_url` implied by `OPENROUTER_API_KEY`); DeepSeek is present only as an alternate/fallback path, not the default. | **STALE** (whole section describes a retired architecture) | DOCS-03 | Rewrite the section: source = Google News RSS search (query registry, not fixed outlet feeds) with `gnews_decoder.py` resolving the true outlet per item for attribution; default classifier = Granite 4.1 8B via OpenRouter; DeepSeek retained as fallback. Add a line naming the R2 full-text research archive as a separate, non-displayed corpus (row #4). |
| 4 | `data/SOURCES.md` (entire file) | No section exists for the R2 research archive. | `pipeline/tests/test_archive_r2.py` (666+ lines of tests: `test_rejected_article_and_jsonl_uploaded`, `test_fetch_priority_incidents_before_rejected`, etc.) proves a live, tested R2-backed archival pipeline exists (full-text corpus, APA citations, ledger, corpus-state — per project memory `r2-research-archive.md`, daily cron, bucket `ischilesafe`). | **MISSING** | DOCS-03 | Add a short "R2 Research Archive" sub-entry under News feeds: internal-only, not reader-displayed, daily cron, full-text + APA + provenance ledger; note it is a research/audit corpus, not a site-facing data source (no reader-facing claim needed, but a SOURCES.md line for transparency/completeness is in scope). |
| 5 | `data/SOURCES.md:293-308` (ENUSC — underreporting / cifra negra) | "Vintage: Cite the exact ENUSC edition year used for the on-page claims. **[verify edition]**" | No code path in `pipeline/` or `site/src` ties a specific ENUSC survey-edition year to the three qualitative underreporting bullet points in `methodology.astro:212-231` — those bullets cite ENUSC generically with a link to the landing page, never a specific year. Grep of `pipeline/` for an ENUSC underreporting ingest (distinct from the SAE VHDV ingest, which IS dated 2024) returned nothing. | **Unresolved — NOT repo-resolvable** | DOCS-03 | See Open Question Q1: this needs an external check (INE/SPD ENUSC national report), not a code read. Recommend citing the **2024 ENUSC national report** (INE's most recent annual edition as of this milestone) IF a human confirms it is the edition the reporting-rate figures in the current prose are drawn from — this cannot be verified from the repo and must not be silently guessed into the page. |
| 6 | `pipeline/shared/schema.py:20-37` vs. `site/src/pages/methodology.astro`/`es/metodologia.astro` | Methodology pages never mention the `sexuales` family at all. | `pipeline/shared/schema.py:20-22` — `VALID_FAMILIES: set[str] = set(FAMILY_KEYS) | {"sexuales"}` with the comment "NEWS-ONLY extension: 'sexuales' is not a CEAD quantitative family (no scraped rate)." `FAMILY_KEYS` (7 keys) is the CEAD-quantitative contract and is explicitly never extended (confirmed unchanged per user memory `sexuales-news-only-family.md`). | **MISSING** | DOCS-01 | Add one short paragraph to the methodology pages (or the news/facet-adjacent prose, see Q2) explaining: the news layer classifies 8 families including `sexuales`, which has no CEAD quantitative counterpart and therefore no per-100k rate — it exists only as a qualitative news-classification label. |
| 7 | `site/src/pages/methodology.astro` (whole page) vs. Phase 26-30 shipped work | No mention anywhere of the clustering NO-GO verdict, the facet UI, or the map redesign. | `.planning/phases/26-event-clustering-spike/26-SPIKE-REPORT.md` + STATE.md § Phase 26 Outcome: NO-GO, `precision=0.667`, no schema change shipped. `site/src/lib/newsFacets.ts` + `newsFilterLogic.ts` (Phase 27/28, shipped) — a facet UI exists on `/news/` and `/es/noticias/` with zero reader-facing methodology note about what a facet count means or how "today"/"7d"/"30d" windows are anchored. | **MISSING** (facets); clustering documentation is explicitly NOT required (DOCS-04 conditions it on GO) | DOCS-04 | See Open Question Q2 — recommend a short facet-semantics note (what "today" is anchored to, that counts are unfiltered marginals on the news page itself), and explicitly NOT a clustering section, with a one-line internal note (commit message or STATE.md, not reader-facing) recording that DOCS-04's clustering half is N/A per NO-GO. |
| 8 | `site/src/pages/methodology.astro:444-484` ("What this site does NOT say") | Absolute-verdict, probability, predictive-claim, neighbourhood-ranking, and cross-country disclaimers. | Verified against `site/scripts/validate/forbidden-language.mjs` (runs in the live validate suite, PASSED in the run below) and against actual page prose — no contradicting language found anywhere in a grep of rendered pages for "safest"/"most dangerous" without a "reported" qualifier. | **OK** | DOCS-02 | No change needed. Do not touch this section — it is correct and the forbidden-language validator actively guards it. |
| 9 | `site/scripts/validate/figure-registry.mjs:212-216` | Validator logic: `figure.tokens.some((group) => group.every((token) => sourcesContent.includes(token)))` — a plain whole-file substring `.includes()` check, with no requirement that the tokens appear within the actual section they are meant to prove exists. | Read in full (253 lines). Confirmed the entire figure-registry passes purely on file-wide substring presence, not proximity to a heading, not minimum section length, not any structural check. | **Confirmed defect** (this IS the "green against a stub" hole DOCS-05 names) | DOCS-05 | See Q3 below for a concrete, falsifiable hardening proposal. |
| 10 | `site/src/lib/mapFilterDefs.ts:45-50` (pre-existing, not reader prose, but Phase 31 was told to document it) | `AVAILABLE_YEARS` = `Array.from({length: currentYear-2005+1}, ...)` — derives from `new Date().getFullYear()`, currently 2026. | `find site/public/data/cead -iname "map-payload-2026.json"` returns nothing — only 2020-2025 payloads exist on disk. Selecting year 2026 in the map's year filter would hit `safeFetch` returning null and show the "data not available" toast (`MapIsland.tsx:274-280`), not a crash, but it is a real UX/data gap the STATE.md Phase 30 Outcome explicitly flagged for Phase 31 to document. | **Confirmed pre-existing defect** (code, not doc drift) | none (DOCS phase doesn't own this) | See Q4 — recommend a reader-facing caveat is NOT the right instrument here (a config-driven UI year list shouldn't need reader prose); recommend a STATE.md/backlog line instead, out of Phase 31's DOCS scope. |
| 11 | `site/src/components/map/MapIsland.tsx:200-203, 289-293` | Legend numeric bands: `setBreaks(computeQuantileBreaks(payload.comunas.map(c => c.rate).filter(r => r > 0), 5))` — called identically at initial load (line 201) and on year change (line 291). | The `.rate` field used is the commune's **overall** rate (not `by_family[index]` or the composite `ci` score), and this same `computeQuantileBreaks` call is used regardless of `mode` ('composite' vs 'family') or `crimeFamilyIndex`/`crimeIsHomicide` — confirmed by reading the surrounding `useEffect` block: the style-map function branches on mode/family (lines 300-308) but `setBreaks` never receives a family-scoped or composite-scoped rate array. | **Confirmed pre-existing defect** (code, not doc drift) | none (DOCS phase doesn't own this) | See Q4 — recommend documenting as a known limitation (backlog item), not a reader-facing caveat, since it is a legend-accuracy bug, not an editorial framing question. |
| 12 | `data/SOURCES.md` News feeds section | No attribution entry names Google News as an intermediary aggregator (only original outlets are implied). | `pipeline/news/feeds.py:145-159` — `_extract_outlet_from_item()`: "For Google News feeds, extract the outlet from the item's `<source>` tag, falling back to the constant 'Google News' if absent or empty." This means some published incidents may cite "Google News" as the outlet, not a named Chilean press outlet, when the underlying `<source>` tag is empty. | **MISSING** (attribution nuance not documented) | DOCS-03 | Add a line to SOURCES.md's News section noting that outlet attribution is extracted per-item from the Google News RSS `<source>` tag, with "Google News" as an honest fallback label when the tag is empty — so DOCS-03's "every press outlet correctly attributed" claim is verifiably true of the mechanism, not just the common case. |

## Anchor Inventory (DOCS-06)

Every in-page anchor fragment on the methodology pages that is linked to from elsewhere in the repo, gathered by `grep -rn "/methodology/#\|/es/metodologia/#"` plus a check of each target `id=` against the page it targets:

| Anchor | Defined at | Linked from |
|---|---|---|
| `#trend-formula` | `methodology.astro:254` (EN) | `site/src/components/MethodologyCaveat.astro:21` (both locales via `locale === 'en' ? ... : ...`) |
| `#comparison-criteria` | `methodology.astro:301` (EN), `metodologia.astro:310` (ES, `id="comparison-criteria"` — note: NOT translated to a Spanish id) | `site/src/pages/crime-ranking/[crime].astro:244`, `site/src/pages/es/ranking-delito/[crime].astro:250` |
| `#national-mean` | `methodology.astro:339` (EN) | `site/src/pages/crime/[family].astro:210` |
| `#media-nacional` | `metodologia.astro:351` (ES — this one WAS translated) | `site/src/pages/es/delito/[family].astro:201` |
| `#enusc-vhdv` | `methodology.astro:240` | No inbound `#enusc-vhdv` link found in a repo-wide grep — currently unlinked from elsewhere, but do not remove the `id` (external readers or future links may target it). |
| `#composite-index` | `methodology.astro:378` | No inbound anchor link found — same treatment as above. |

**Verified all four actively-linked anchors resolve correctly today** (both locales built and validated green in the run below, `hreflang.mjs` and `spine.mjs` passed). Any Phase 31 rewrite that renumbers, renames, or removes these four `id`s without updating every listed inbound link breaks a live cross-link — this is the concrete list DOCS-06 needs. Note the EN/ES id-naming inconsistency (`#comparison-criteria` shared verbatim vs. `#national-mean`/`#media-nacional` diverging) is pre-existing and not itself a defect, but any new anchor added during this phase should follow the ES-translated-id pattern (`#media-nacional`) for new prose, matching the majority convention, or explicitly document why not.

## EN/ES Parity Mechanics (for context, not a DOCS-06 finding)

- No dedicated automated "i18n string parity" validator exists in `site/scripts/validate/`; parity is enforced structurally by `hreflang.mjs` (canonical + reciprocal hreflang pairs) and `spine.mjs` (IA cross-link reciprocity), plus manual convention — every `.astro` EN page has a hand-written ES twin with the same H2 order (see the `methodology.astro` file header comment listing "Required H2 sections IN ORDER").
- ES slugs are hardcoded throughout (`/es/metodologia/`, `/es/glosario/`, `/es/acerca-de/`) — confirmed via the grep above; none use `getRelativeLocaleUrl()` for these routes, consistent with the documented pitfall (`i18n-localized-slug-pitfall.md`) that this helper does not translate ES slugs.
- `facets.mjs` (validator #16) is the closest thing to an i18n-parity check for the new Phase 27/28 surfaces — its description names "family/region containment... i18n parity" as one of its assertion groups (confirmed passing in the live run below).

## Validators Path Correction

**`site/scripts/validators/` does NOT exist.** The real, live path is `site/scripts/validate/` (confirmed: `find`/`ls` returned nothing for `validators/`, 16 files for `validate/`). Any reference elsewhere in the repo's own docs or in prior phase notes to `scripts/validators/figure-registry.mjs` is itself a path-naming drift that should be corrected wherever it appears in reader-adjacent docs (it does not appear in the two methodology pages or SOURCES.md, so it is out of this phase's Drift Table, but the planner should use `site/scripts/validate/figure-registry.mjs` as the one true path).

**Full validator surface (`site/scripts/validate/all.mjs`, 16 registered + 1 non-registered):**

| # | Validator | Touches docs/prose? |
|---|---|---|
| 1 | `structure.mjs` | No |
| 2 | `commune.mjs` | No |
| 3 | `rollout.mjs` | No |
| 4 | `region.mjs` | No |
| 5 | `crime.mjs` | No |
| 6 | `hreflang.mjs` | Yes — canonical + reciprocal hreflang per page, including methodology pages |
| 7 | `schema.mjs` | No |
| 8 | `map.mjs` | No |
| 9 | `forbidden-language.mjs` | **Yes — directly guards DOCS-02's editorial constraint** over all rendered dist/ text |
| 10 | `coverage.mjs` | Partial — no-orphan-link check would catch a broken anchor turned into a broken full URL, but does not check in-page `#fragment` validity |
| 11 | `spine.mjs` | Yes — IA cross-link reciprocity, includes methodology cross-links |
| 12 | `seo.mjs` | Partial — OG/Twitter/JSON-LD shape, not prose content |
| 13 | `figure-registry.mjs` | **Yes — the DOCS-05 target** |
| 14 | `avs-b-budget.mjs` | No |
| 15 | `freshness.mjs` | No (data staleness, not docs) |
| 16 | `facets.mjs` | Yes — i18n parity assertion group for the news facet UI |
| — | `phase30-gate.mjs` | Not registered in `all.mjs` (deliberately, per F-21) — a standalone Phase 30 close script, irrelevant to Phase 31 |

No dedicated "anchor validity" or "in-page fragment resolves" check exists anywhere in this list — `coverage.mjs`'s "no-orphan-link" check is the closest relative but is described as route-level, not fragment-level. This is a real gap for DOCS-06's requirement; see Validation Architecture below for a proposed check.

## Don't Hand-Roll

Not applicable in the traditional sense — this phase touches static prose and one existing validator, not new library-backed functionality. The one relevant guardrail: **do not hand-roll a new "prose freshness" mechanism** (e.g., a script that diffs page text against pipeline source comments) — that is a disproportionate solution for a six-item, human-curated Drift Table. Direct manual correction of the enumerated rows is the right-sized fix.

## Common Pitfalls

### Pitfall 1: Fixing the `national_rank` claim in only one locale
**What goes wrong:** EN and ES methodology pages currently carry the identical wrong claim (rows #1/#2). A fix that updates only `methodology.astro` breaks parity and would make the ES page the sole remaining wrong one.
**Why it happens:** The two files are hand-maintained twins with no shared source of truth for this sentence.
**How to avoid:** Land both edits in the same commit; grep both files for "lowest reported rate"/"menor tasa reportada" before closing the phase to confirm zero remaining instances.
**Warning signs:** `hreflang.mjs`/`spine.mjs` will not catch a prose-only asymmetry — they check link reciprocity, not sentence-level parity.

### Pitfall 2: Guessing the ENUSC edition year to close DOCS-03's `[verify edition]` marker
**What goes wrong:** No code path ties a specific ENUSC survey year to the underreporting bullets. Writing in a plausible year (e.g. "ENUSC 2024") without a human confirming that IS the edition the reporting-rate figures are drawn from would replace a marked gap with an unmarked, unverifiable factual claim — worse than the current honest `[verify edition]` flag on an editorial/legal-adjacent page.
**Why it happens:** The SAE VHDV dataset IS confirmed 2024 (a different, code-verifiable fact), and it is tempting to reuse that year for the unrelated underreporting citation.
**How to avoid:** Either (a) get explicit human confirmation of the underreporting-statistics ENUSC edition before writing a year, or (b) rephrase the citation to not claim a specific year at all (cite ENUSC generically, as the current prose already mostly does) and remove the internal-only `[verify edition]` marker as "resolved: intentionally generic," which is itself a legitimate, falsifiable resolution.

### Pitfall 3: Hardening `figure-registry.mjs` into a check that can never pass
**What goes wrong:** Per Operating Lesson 9 (Phase 27 close, `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:111`), an assertion that requires the exact token substrings to appear directly under their own heading, if implemented naively (e.g. via a brittle line-count-since-heading rule), could break on any legitimate future SOURCES.md reformatting (e.g. moving a token to a table cell one line later).
**How to avoid:** Bound the section by heading-to-next-heading (or heading-to-EOF), not by a fixed line/word count — see the concrete design in Q3 below.

### Pitfall 4: Touching prose that is already correct
**What goes wrong:** The composite index formula, ENUSC SAE section, trend formula, and "what this site does NOT say" sections (rows not in the Drift Table, or row #8 marked OK) are accurate today. A broad "refresh everything" pass risks introducing new drift or breaking a currently-correct anchor for no reason.
**How to avoid:** Scope the phase strictly to the enumerated Drift Table rows. Any edit outside that list needs its own file:line evidence entry first.

## Code Examples

### The `national_rank` producer (ground truth for row #1/#2)
```python
# Source: pipeline/cead/normalizer.py:111-141
def compute_ranks(records: list[dict], year: int) -> list[dict]:
    """
    Assign national_rank and regional_rank to every commune.

    Rules (D-12):
    - Eligible communes: low_population=False AND series is non-empty
    - Rank by rate_per_100k descending (highest rate = rank 1)
    ...
    """
    eligible_sorted = sorted(
        eligible_indices,
        key=lambda i: _latest_rate(records[i], year),
        reverse=True,
    )
    for rank, i in enumerate(eligible_sorted, start=1):
        records[i]["national_rank"] = rank
```

### The correct reader-facing framing already in production (commune page)
```typescript
// Source: site/src/pages/commune/[slug].astro:100
// national_rank/regional_rank are DESCENDING (rank 1 = highest incidence).
```

### The Google News query registry the methodology/sources prose does not reflect
```python
# Source: pipeline/news/feeds.py:22-32
def google_news_url(query: str) -> str:
    """Build a Google News RSS search URL for the given query string."""
    q = urllib.parse.quote(query, safe="")
    return f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=CL&ceid=CL:es-419"
```

### `figure-registry.mjs`'s exploitable check (row #9 / Q3)
```javascript
// Source: site/scripts/validate/figure-registry.mjs:212-216
const passed = figure.tokens.some((group) =>
  group.every((token) => sourcesContent.includes(token))
);
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommending "ENUSC 2024" as a plausible (but NOT repo-verifiable) edition for the underreporting citation, IF the user chooses to name a year rather than stay generic | Drift Table row #5, Pitfall 2 | Low if flagged clearly (it is, both here and in the table) — this is explicitly presented as a human-verification item, not a fact to write into the page unconfirmed. |
| A2 | That "Google News" as a fallback outlet label (row #12) is rare in practice (most `<source>` tags are populated) | Drift Table row #12 | Low — this is a documentation-completeness point (document the mechanism), not a claim about frequency; no reader-facing number is asserted. |

No other claim in this research is asFcSUMED-only: the `national_rank` direction, the Google News/Granite pipeline shape, the `sexuales` family boundary, the figure-registry substring-matching behavior, the map legend/`AVAILABLE_YEARS` defects, the validator path (`validate/` not `validators/`), the anchor inventory, and the live validate/pytest run results were all confirmed by direct file read or command execution in this session.

## Open Questions

1. **Is the ENUSC edition resolvable from repo evidence alone?**
   **No.** Grep of `pipeline/` and `site/src` found no ingestion code, snapshot, or config tying a specific ENUSC survey year to the three underreporting bullets in `methodology.astro:212-231`. The only dated ENUSC artifact in the repo is the unrelated 2024 SAE VHDV victimization snapshot (`data/SOURCES.md:318-343`), which is a distinct dataset (household violent-crime victimization estimate) from the national underreporting/reporting-rate survey the methodology page's cifra-negra bullets implicitly cite. **Recommendation:** either get explicit human confirmation of the correct edition year before writing one, or rephrase the citation as intentionally generic (cite the ENUSC program, not a specific year) and mark the `[verify edition]` item "resolved: intentionally generic" in SOURCES.md with a one-line rationale.

2. **Should Phase 31 document the Phase 26 clustering NO-GO on a reader-facing page, or is it internal-only?**
   DOCS-04's own text conditions the clustering-documentation requirement on Phase 26 returning GO ("required if Phase 26 returned GO"). Phase 26 returned NO-GO. The honest reading of DOCS-04 is that **the clustering half is not required** — there is no shipped clustering feature for a reader to encounter, so a "how clustering works" reader page would describe a feature that does not exist. **However**, the facet UI (time/region/family filtering on `/news/`) DID ship in Phase 28 and has zero reader-facing explanation anywhere — a first-time visitor sees filter counts and window presets with no context for what "today" is anchored to (the newest incident's date, not wall-clock, per `newsFacets.ts`'s documented contract) or that family counts are unfiltered marginals on that surface. **Recommendation: write a short facet-semantics note (2-4 sentences), and explicitly do NOT write a clustering section.** Record the NO-GO status as an internal note only (a commit message or a one-line SOURCES.md/STATE.md cross-reference, not new reader-facing prose) — a reader-facing "we tried grouping duplicate articles and it didn't work" explainer serves no reader need and risks reading as an admission of low data quality where none exists.

3. **What is the minimal, falsifiable hardening for `figure-registry.mjs`?**
   **The exploitable hole, proven with a real counterexample:** F16's token groups are `['## INE ENUSC SAE', 'VHDV']` or `['ENUSC', 'Victimizacion en Hogares', 'SAE']`. The actual heading text is `## INE ENUSC SAE — communal VHDV household victimization rate (experimental, 2024)` (`data/SOURCES.md:318`) — note "VHDV" already appears IN the heading itself. **A section reduced to just this heading line, with every other line of body content (URL, sha256, coverage figures, provenance) deleted, would still report F16 PASS today**, because `.includes()` only checks whole-file substring presence, never proximity to the heading or minimum section length. This is the literal "green against a stub" hole DOCS-05 names.
   **Correct input that must still pass:** the current, fully-populated `## INE ENUSC SAE` section (heading + provenance + coverage figures + sha256), unchanged.
   **Sketch of the fix:** bound each figure's search scope to the text between its anchor heading and the next `## ` heading (or EOF), and additionally require the bounded section to exceed a minimum non-trivial length (e.g. > 200 characters, chosen well below any real populated section but above a bare heading line) OR require at least N distinct required tokens to each appear (not just the heading-embedded ones) within that bounded scope. Concretely: `const sectionText = extractSection(sourcesContent, '## INE ENUSC SAE'); const passed = tokens.every(t => sectionText.includes(t)) && sectionText.length > 200;` — a stub-heading-only section is provably < 200 characters and fails on length even if it happens to contain every literal token; the real section is 26 lines / ~900+ characters and passes both checks.

4. **Where do the two pre-existing map defects (legend bands, `AVAILABLE_YEARS` 2026) belong?**
   Phase 31's `REQUIREMENTS.md` scope is DOCS-01..06 — none of the six requirements mention map code changes, and MAPSH-01..07 (Phase 30, already CLOSED) was the map's dedicated code-change phase with its own protected-file rules (`ChoroplethLayer.ts`/`IncidentPinLayer.ts`/`LowZoomDotLayer.ts` untouched, no declarative react-leaflet). Reopening map code in a DOCS phase would be scope creep against a phase the roadmap explicitly gates as documentation-only. **Recommendation: record both as a backlog/STATE.md item, not a reader-facing caveat and not a code fix.** A reader-facing caveat is the wrong instrument for either: the legend-band defect is a legend-accuracy bug (the legend visually implies per-family/per-index granularity it doesn't have) that a disclaimer sentence cannot honestly fix without either being ignored by readers or looking alarmist next to an otherwise-working map; and the `AVAILABLE_YEARS` gap already degrades gracefully (a toast, not a crash — `MapIsland.tsx:274-280`) and self-resolves once a 2026 payload exists, making a permanent doc caveat about a temporary, self-resolving state actively become the next round of stale prose.

5. **Is there any prose currently on the site that is FACTUALLY WRONG (not merely stale)?**
   **Yes — flagged loudly, this is the phase's highest-value finding.** Drift Table row #1/#2: both EN and ES methodology pages state "Rank 1 = lowest reported rate," while the code that computes `national_rank` assigns rank 1 to the **highest** rate. This is not an omission or a staleness issue — it is an inverted, falsifiable, currently-live claim on the site's primary editorial/credibility page, directly contradicting the correct framing already present elsewhere in the codebase (`commune/[slug].astro:100`) and contradicting the exact fact DOCS-01 names by name ("the directional meaning of `national_rank`"). Every other candidate defect in this research (map legend, `AVAILABLE_YEARS`, SOURCES.md staleness) is either a pre-existing code bug outside DOCS scope or an honest staleness gap — this is the one item that is simply incorrect and must be fixed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Node built-in test runner via standalone `.mjs` scripts (no jest/vitest for validators); vitest for TS/TSX unit tests; pytest for the Python pipeline |
| Config file | `site/scripts/validate/all.mjs` (validator orchestration, not a config file per se — no separate config) |
| Quick run command | `cd site && node scripts/validate/figure-registry.mjs` (offline, no build needed) |
| Full suite command | `cd site && npm run build && npm run validate` (chained — OneDrive gotcha) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DOCS-01 | `national_rank` direction claim matches `normalizer.py` | unit (new) | `node -e` string-match check (real `.mjs` file, not inline regex) reading both `methodology.astro` and `metodologia.astro` for the absence of "lowest reported rate"/"menor tasa reportada" and presence of "highest reported"/"más reportada" near the ranking-basis section | ❌ Wave 0 — new small check, or fold into `figure-registry.mjs`'s scope as a companion assertion |
| DOCS-02 | Forbidden-language / disclaimer presence | automated (existing) | `node scripts/validate/forbidden-language.mjs` | ✅ exists, PASSED in the run below |
| DOCS-03 | SOURCES.md News section names Google News + Granite + R2 archive | unit (new) | string-presence check against `data/SOURCES.md` for tokens `"news.google.com"` or `"Google News"`, `"granite"`/`"Granite"`, and an R2/archive marker | ❌ Wave 0 |
| DOCS-04 | Facet-semantics note exists on news pages (not clustering) | integration (existing infra) | extend `facets.mjs` (validator #16) with one more assertion checking for the presence of a facet-explainer string in the rendered `/news/` and `/es/noticias/` dist HTML | ❌ Wave 0 — extend existing file, don't create a new validator |
| DOCS-05 | `figure-registry.mjs` rejects a stub section | unit (new) | a mutation test: temporarily replace the `## INE ENUSC SAE` section body with only its heading in a test fixture (or an in-memory string, not `data/SOURCES.md` itself since it's read-only-adjacent) and assert `figure-registry`'s (hardened) logic returns non-zero | ❌ Wave 0 — this is the counterexample from Q3, must be encoded as an actual test, not just prose |
| DOCS-06 | No inbound anchor broken | existing (`hreflang.mjs`, `spine.mjs`) + new | the four actively-linked anchors (`#trend-formula`, `#comparison-criteria`, `#national-mean`, `#media-nacional`) should be asserted present in the built HTML post-rewrite — no such fragment-level check exists today (see gap noted above) | ❌ Wave 0 — a small addition, e.g. to `coverage.mjs` or a dedicated few-line check |

### Sampling Rate
- **Per task commit:** `cd site && node scripts/validate/figure-registry.mjs` (fast, offline) plus a targeted grep for the specific Drift Table row being fixed.
- **Per wave merge:** `cd site && npm run build && npm run validate` (full 16-validator chain).
- **Phase gate:** Full suite green (16/16, modulo the pre-existing local `freshness` staleness noted below) + `python -m pytest pipeline/tests -q` green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] A new or extended validator assertion for the `national_rank` direction claim (DOCS-01) — smallest correct home is likely a new assertion appended to `figure-registry.mjs` or a tiny new sibling script, NOT a new 17th entry in `all.mjs`'s hardcoded list without updating that list and its header comment (which enumerates "16" by name).
- [ ] A new assertion (or new tiny script) for DOCS-03's SOURCES.md content check.
- [ ] One new assertion appended to `facets.mjs` for DOCS-04's facet-semantics-note-exists check.
- [ ] A genuine mutation test for DOCS-05's hardened `figure-registry.mjs` (the stub-section counterexample must be encoded, not just described in a plan).
- [ ] A small anchor-presence check for DOCS-06 — no existing validator does fragment-level (`#id`) verification; `coverage.mjs` is the closest existing home if extending rather than adding a new file is preferred.

## Security Domain

Not applicable — `workflow.nyquist_validation` security-domain guidance targets phases introducing new input-handling code paths, auth, or cryptography. Phase 31 is a static-prose and validator-string-matching change with no new user input surface, no new dependency, and no data-mutation path. No ASVS category applies.

## Current State: `npm run validate` (executed, not assumed)

Ran `cd site && npm run build && npm run validate` in one chained command as required. Result: **15/16 validators passed**; the sole failure is `freshness`:

```
FAIL freshness: data/incidents/current.json is 3.3 days old (generated: 2026-07-30T19:20:47.950917Z)
Maximum allowed age is 3 days. The news cron is probably down.
```

This matches the exact, pre-declared F-19 environmental-exclusion pattern documented in `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` §"F-19 freshness environmental-exclusion branch": the failure is precisely the age assertion (not a missing-file or unparseable-`generated` failure), and this is almost certainly local-checkout staleness (the same class of issue recorded repeatedly at prior phase closes), not a real regression. **The planner should NOT attempt to fix this** — per the hard rule, banned remediations include raising `MAX_AGE_DAYS`, editing/skipping the validator, touching `data/`, or running `git pull`/`rebase`/`push` mid-phase. Confirm via `git log -1 --format=%ci origin/master -- data/incidents/current.json` before invoking the F-19 branch at phase close, per the directive's own precondition (b).

`facets.mjs` (validator #16) passed cleanly: "1412 incidents, 8 families observed, 346 communes cross-checked, 3 months in byMonth union... 22 assertions passed" — confirming the 8-family (7 CEAD + `sexuales`) contract holds in the live build.

`python -m pytest pipeline/tests -q` (executed): **344 passed, 1 skipped, 1 xfailed** — matches the STATE.md baseline exactly; no drift in the pipeline test suite.

## Sources

### Primary (HIGH confidence — direct file read or executed command in this session)
- `site/src/pages/methodology.astro` (full read, 541 lines)
- `site/src/pages/es/metodologia.astro` (targeted read of comparison-criteria section, lines 307-356)
- `data/SOURCES.md` (full read, 424 lines)
- `pipeline/cead/normalizer.py:105-165` (`compute_ranks`)
- `pipeline/news/feeds.py:1-65` (Google News query registry)
- `pipeline/news/classifier.py:1-215` (Granite/OpenRouter default)
- `pipeline/news/schema.py`, `pipeline/shared/schema.py:20-37` (`FAMILY_KEYS`/`VALID_FAMILIES`/`sexuales`)
- `site/scripts/validate/figure-registry.mjs` (full read, 253 lines)
- `site/scripts/validate/all.mjs` (full read, 113 lines)
- `site/src/components/map/MapIsland.tsx:180-309`
- `site/src/lib/mapFilterDefs.ts:40-51`
- `site/src/lib/newsFacets.ts:1-40` (module contract header, F-20/F-28)
- Grep across `site/src` for `/methodology/#`, `/es/metodologia/#` (anchor inventory)
- `find` for `site/public/data/cead/map-payload-2026.json` (absent, confirmed)
- Executed: `cd site && npm run build && npm run validate` (15/16, freshness fails locally as expected)
- Executed: `python -m pytest pipeline/tests -q` (344 passed / 1 skipped / 1 xfailed)
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`, `CLAUDE.md` (full reads)

### Secondary (MEDIUM confidence)
- User memory files (`sexuales-news-only-family.md`, `r2-research-archive.md`, `granite-default-classifier.md`, `national-rank-direction.md`) — used as corroborating context, all independently reverified against source code in this session rather than trusted as-is.

### Tertiary (LOW confidence)
- None — every claim in the Drift Table has a direct file:line or command-execution citation.

## Metadata

**Confidence breakdown:**
- Drift Table: HIGH — every row backed by a direct file read or grep, cross-checked against the code that produces the actual behavior.
- Validation Architecture: MEDIUM-HIGH — the proposed checks are sketched precisely enough to plan from, but exact assertion wording is a planner/executor decision.
- Open Questions: HIGH confidence in the "cannot resolve from repo" verdicts (Q1), and in the recommendations (Q2-Q5) — these are reasoned recommendations, correctly flagged as such, not verified external facts.

**Research date:** 2026-08-02
**Valid until:** Should be treated as valid only until the next code change to `pipeline/cead/normalizer.py`, `pipeline/news/feeds.py`/`classifier.py`, `data/SOURCES.md`, or the map/facet files cited above — this is a point-in-time drift snapshot, not a stable technology recommendation. Re-verify before use if more than ~7 days old given this milestone's active development pace.

## RESEARCH COMPLETE

**Phase:** 31 - Docs & Methodology Refresh
**Confidence:** HIGH

### Key Findings
- Both EN and ES methodology pages contain a **factually wrong** claim about `national_rank` direction ("Rank 1 = lowest reported rate") that directly contradicts the code (`normalizer.py`: highest rate = rank 1) and contradicts DOCS-01's own named requirement — this is the phase's highest-priority, highest-confidence fix.
- `data/SOURCES.md`'s News feeds section describes a retired architecture (direct RSS from 4 named outlets + DeepSeek) when the live pipeline uses Google News RSS search queries + a Granite-4.1-8B/OpenRouter default classifier, with no mention of the R2 research archive or the `sexuales` news-only family.
- The ENUSC `[verify edition]` marker is **not resolvable from repo evidence** — no code ties a specific survey year to the underreporting prose; this needs a human decision (name a year with explicit confirmation, or go intentionally generic).
- Phase 26 returned **NO-GO** — DOCS-04's clustering-documentation clause is N/A by its own conditional text; the facet UI (which DID ship) has no reader-facing semantics note and should get a short one instead.
- `figure-registry.mjs`'s whole-file `.includes()` substring check is provably exploitable (a stub `## INE ENUSC SAE` heading-only section would still pass F16 today) — a concrete, falsifiable hardening (section-bounded token search + minimum section length) is sketched in Q3.
- Two pre-existing map defects (legend bands never vary by family; `AVAILABLE_YEARS` offers 2026 with no payload) are confirmed real but are out of this DOCS-scoped phase's remit — recommend a backlog/STATE.md note, not a reader-facing caveat or a code fix.
- `npm run validate` currently runs 15/16 (freshness fails on local staleness only, matching the pre-declared F-19 exclusion pattern exactly); pytest is 344/1/1, unchanged from the STATE.md baseline.

### File Created
`.planning/phases/31-docs-methodology-refresh/31-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Drift Table (factual claims) | HIGH | Every row verified by direct file read against the producing code, not inference |
| Validator hardening design (Q3) | HIGH | Constructed and reasoned against the actual 253-line file with a real counterexample |
| ENUSC edition resolution (Q1) | HIGH confidence in "unresolvable," zero confidence in any specific year — correctly flagged as needing human input |

### Open Questions
- Human confirmation needed: the correct ENUSC edition year for the underreporting citation (or a decision to go intentionally generic).
- Planner decision needed: exact home for the five new validator assertions (extend existing files vs. new sibling scripts) — recommended to extend existing files (`figure-registry.mjs`, `facets.mjs`) rather than add new entries to `all.mjs`'s hardcoded 16-item list, to avoid an F-21-style validator-count cascade.

### Ready for Planning
Research complete. Planner can now create PLAN.md files against the Drift Table above.
