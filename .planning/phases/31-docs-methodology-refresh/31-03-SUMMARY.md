---
phase: 31-docs-methodology-refresh
plan: 03
subsystem: news-pages-i18n
tags: [i18n, news, facets, docs]
requires: []
provides:
  - news_facet_semantics_note (i18n key pair, EN/ES)
  - "#news-facet-semantics paragraph on /news/ and /es/noticias/"
affects:
  - site/src/config/i18n.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
tech-stack:
  added: []
  patterns:
    - "Static developer-authored i18n string, escaped {expression} interpolation, zero hydration"
key-files:
  created: []
  modified:
    - site/src/config/i18n.ts
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
decisions:
  - "DOCS-04 satisfied via a facet-semantics note, not a clustering explainer (F-61, Phase 26 NO-GO — no shipped clustering feature)"
  - "news.astro header comment corrected (DOCS-01 drift fix): source is now 'Google News RSS search, classified by the news pipeline's LLM classifier and geolocated by the deterministic commune name->CUT resolver' — es/noticias.astro header intentionally left untouched (it made no pipeline claim)"
  - "Reader-facing sentence 'Incidents are extracted from RSS feeds' / 'se extraen de feeds RSS' left as-is per F-63 — still true, not rewritten"
metrics:
  duration: "~20 min"
  completed: "2026-08-02"
---

# Phase 31 Plan 03: Bilingual News Facet-Semantics Note Summary

Added a short bilingual note to `/news/` and `/es/noticias/` explaining facet-count semantics (unfiltered per-option counts, "latest" anchored to newest-incident date not wall-clock, and non-comparability with CEAD per-100k rates) — delivered via a shared i18n key pair and a static `<p id="news-facet-semantics">` element on both pages, with a one-line drift fix to the stale `news.astro` source-attribution comment.

## Tasks Completed

### Task 1: Add the `news_facet_semantics_note` i18n key pair
- Added `news_facet_semantics_note: string;` to the shared `Strings` type interface in `site/src/config/i18n.ts`, in the `news_*` block.
- Added the EN value to `EN_STRINGS` and a genuinely-translated (not pasted) ES value to `ES_STRINGS`, matching the existing single-quoted string style.
- Commit: `abada8a`

### Task 2: Render the note on both news pages
- `site/src/pages/news.astro`: inserted `<p class="facet-semantics-note" id="news-facet-semantics">{t.news_facet_semantics_note}</p>` inside the opening `<section>`, immediately after the `{generated && <p class="freshness">...}` block, before `</section>`.
- `site/src/pages/es/noticias.astro`: identical markup at the identical structural position.
- No new `client:*` directive, no new CSS rule — reused existing typography.
- Also applied the amendment-mandated drift fix: `news.astro`'s file-header comment (line 5) no longer credits "DeepSeek geolocation"; it now reads "incidents sourced from Google News RSS search, classified by the news pipeline's LLM classifier and geolocated by the deterministic commune name->CUT resolver." The ES twin's header was left untouched as instructed (it made no pipeline claim to begin with).
- Commit: `abada8a`

## Verification (commands run, output captured)

```
$ grep -c "news_facet_semantics_note" site/src/config/i18n.ts
3

$ grep -c 'id="news-facet-semantics"' site/src/pages/news.astro
1

$ grep -c 'id="news-facet-semantics"' site/src/pages/es/noticias.astro
1
```

```
$ cd site && npx astro check
...
Result (138 files):
- 4 errors
- 0 warnings
- 43 hints
```
All 4 errors are in `ComparatorPairsLinks.astro:28` (pre-existing, out of scope). Hint count not asserted per plan instruction (moves by design ahead of Plan 31-04).

```
$ cd site && npm run build
...
834 page(s) built in 25.60s
[build] Complete!

$ node scripts/validate/forbidden-language.mjs
forbidden-language: scanning 835 HTML files in dist/
forbidden-language: PASS — 835 pages scanned, 0 forbidden terms found
EXIT:0
```

```
$ grep -c 'id="news-facet-semantics"' dist/news/index.html
1
$ grep -c 'id="news-facet-semantics"' dist/es/noticias/index.html
1
$ grep -Ec 'client:load|client:idle|client:visible|client:only' src/pages/news.astro src/pages/es/noticias.astro
src/pages/news.astro:0
src/pages/es/noticias.astro:0
```

```
$ npm run validate
...
  PASS  structure
  PASS  commune
  PASS  rollout
  PASS  region
  PASS  crime
  PASS  hreflang
  PASS  schema
  PASS  map
  PASS  forbidden-language
  PASS  coverage
  PASS  spine
  PASS  seo
  PASS  figure-registry
  PASS  avs-b-budget
  FAIL  freshness
  PASS  facets
15/16 validators passed
```

`freshness` failed because `data/incidents/current.json` is 3.3 days old (news cron staleness, tracked in project memory `news-cron-billing-outage.md`) — pre-existing, unrelated to this plan's changes, and `data/` is off-limits per this plan's hard rules. All validators relevant to this plan's changes (`forbidden-language`, `facets`, `hreflang`, `seo`, `avs-b-budget`) pass.

## Deviations from Plan

None — plan executed exactly as written, including the frontmatter amendment (stale-header fix folded in as a one-line DOCS-01 drift correction).

## Known Stubs

None.

## Threat Flags

None — no new trust boundary introduced; static developer-authored string via escaped `{expression}` interpolation, per the plan's own threat register (T-31-04, accepted).

## Self-Check: PASSED

- FOUND: site/src/config/i18n.ts (news_facet_semantics_note present 3x)
- FOUND: site/src/pages/news.astro (id="news-facet-semantics" present)
- FOUND: site/src/pages/es/noticias.astro (id="news-facet-semantics" present)
- FOUND: commit abada8a (`git log --oneline --all | grep abada8a`)
