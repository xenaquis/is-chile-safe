---
phase: 31-docs-methodology-refresh
plan: 02
subsystem: docs
tags: [sources-registry, news-pipeline, methodology, attribution]
requires: []
provides:
  - "data/SOURCES.md News feeds section describing the live Google News RSS pipeline"
  - "data/SOURCES.md ENUSC underreporting vintage marker resolved (intentionally generic)"
affects:
  - "site/scripts/validate/figure-registry.mjs (F15 token dependency, read-only consumer)"
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified:
    - data/SOURCES.md
decisions:
  - "Resolved ENUSC underreporting Vintage marker as 'intentionally generic — no specific ENUSC edition year is claimed' per F-60, never writing a year for the underreporting survey itself."
  - "Cross-reference to the distinct SAE VHDV section rephrased to avoid the literal substring 'ENUSC 20' so the section-scoped falsifiable check (awk-extracted section, grep -c \"ENUSC 20\" == 0) passes without weakening the cross-reference."
metrics:
  duration: "~15m"
  completed: "2026-08-02"
---

# Phase 31 Plan 02: SOURCES.md News Feeds & ENUSC Vintage Refresh Summary

Rewrote `data/SOURCES.md`'s News feeds section to describe the live Google News RSS
search pipeline (query registry + gnews_decoder + Granite-4.1-8b/OpenRouter classifier
+ internal R2 research archive + corrected `data/incidents/current.json` path) in place
of the retired fixed-outlet-feed/DeepSeek architecture, and resolved the standing
ENUSC `[verify edition]` marker as explicitly and honestly generic with no edition
year ever written.

## Task 1: News feeds section rewrite

Replaced the entire "## News feeds — qualitative incident layer (RSS)" section
(previously describing 4 fixed-outlet RSS feeds processed by DeepSeek v4-flash,
stored at the non-existent `data/news/current.json`) with a rewritten "## News feeds
— qualitative incident layer (Google News RSS)" section containing five new
sub-points, verified against source code before writing:

- **Ingestion mechanism:** Google News RSS search via `google_news_url()` against
  `https://news.google.com/rss/search`, driven by `_GOOGLE_NEWS_QUERIES` registry
  (`pipeline/news/feeds.py`); `gnews_decoder.py` resolves redirect URLs to the real
  outlet. Also notes the small set of direct-outlet feeds still ingested
  (BioBioChile, Cooperativa, LaTercera, LaCuarta — confirmed against
  `pipeline/news/feeds.py`'s `FEEDS` dict).
- **Outlet attribution:** `resolve_outlet()` (the actual function name in
  `pipeline/news/feeds.py`, not `_extract_outlet_from_item()` as named in the
  research doc — corrected against source) reads the RSS `<source>` tag, falling
  back to "Google News".
- **Classification:** `ibm-granite/granite-4.1-8b` via OpenRouter
  (`pipeline/news/classifier.py`) as default, DeepSeek v4-flash as selectable
  fallback (`NEWS_PROVIDER=deepseek`).
- **Full-text research archive (internal, not reader-displayed):** R2 bucket
  `ischilesafe`, daily cron, full text + APA + provenance ledger
  (`pipeline/tests/test_archive_r2.py`), explicitly not reader-facing.
- **Storage:** corrected to `data/incidents/current.json` + `data/incidents/archive/`
  (confirmed these exist on disk; `data/news/` does not exist).

Kept Attribution requirement, Measure semantics (updated wording), Vintage, and
Licence points.

## Task 2: ENUSC vintage marker resolution

Replaced the `**Vintage:** Cite the exact ENUSC edition year used for the on-page
claims. [verify edition]` line under "## ENUSC — underreporting / cifra negra" with
an explicit "intentionally generic — no specific ENUSC edition year is claimed"
resolution, per decision F-60. No year is written as the edition of the underreporting
survey anywhere in the replacement. The separate, dated "## INE ENUSC SAE — communal
VHDV victimization" section (2024 VHDV snapshot) was left completely untouched.

The cross-reference to that distinct section was phrased as "the dated SAE VHDV
snapshot in the section below (`## INE ENUSC SAE — communal VHDV victimization`)"
rather than "the ENUSC 2024 SAE VHDV snapshot below" (the plan's literal suggested
wording) because the latter phrase contains the substring "ENUSC 20", which would
have failed the section-scoped falsifiable acceptance check
(`awk`-extracted `## ENUSC — underreporting` section, `grep -c "ENUSC 20"` must equal
0). This preserves the cross-reference's intent (pointing readers to the distinct,
dated dataset) without writing a year adjacent to "ENUSC" inside the underreporting
section.

## Verification

All acceptance criteria run and confirmed:

```
news.google.com: 1
granite (case-insensitive): 1
R2: 1
ischilesafe: 2
data/news/current.json: 0
data/incidents/current.json: 1
www.emol.com/rss: 0
biobiochile.cl/feed: 0
t13.cl/rss.xml: 0
cooperativa.cl/rss: 0
DeepSeek v4-flash: 0
RSS: 5
news: 7
[verify edition]: 0
intentionally generic: 1
```

Section-scoped ENUSC year check (awk-extracted `## ENUSC — underreporting` section
only, not whole-file):
```
ENUSC 20 count: 0
intentionally generic count (in-section): 1
```

Falsifiability check: same extraction with "ENUSC 2024" inserted into the Vintage
line on a scratch copy returned `ENUSC 20 count: 1` (proving the check can go red),
then the scratch copy was discarded without writing back to `data/SOURCES.md`.

`cd site && node scripts/validate/figure-registry.mjs` exit code 0, all 16 figures
(F1-F16) PASS, including F15 (News incidents) and F16 (ENUSC SAE VHDV).

No files under `site/scripts/validate/` were touched. No other file under `data/`
was touched (pre-existing unrelated staged changes to
`site/src/pages/methodology.astro` and `site/src/pages/es/metodologia.astro` were
left untouched and unstaged by this plan). No push performed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Correction] Function name corrected from research doc**
- **Found during:** Task 1
- **Issue:** 31-RESEARCH.md and the plan's task description referenced
  `_extract_outlet_from_item()`; the actual function in `pipeline/news/feeds.py` is
  named `resolve_outlet()`.
- **Fix:** Used the verified function name `resolve_outlet()` in the written prose.
- **Files modified:** data/SOURCES.md
- **Commit:** 764114c

**2. [Rule 1 - Bug] Cross-reference wording adjusted to satisfy falsifiable check**
- **Found during:** Task 2
- **Issue:** The plan's literal suggested phrase "the ENUSC 2024 SAE VHDV snapshot
  below" would have failed the amended, falsifiable section-scoped acceptance check
  (`grep -c "ENUSC 20"` == 0 within the extracted section), since it contains the
  literal substring "ENUSC 20".
- **Fix:** Rephrased to "the dated SAE VHDV snapshot in the section below (`##
  INE ENUSC SAE — communal VHDV victimization`)" — same cross-reference intent,
  no year adjacent to "ENUSC" within the underreporting section.
- **Files modified:** data/SOURCES.md
- **Commit:** 764114c

## Self-Check: PASSED

- FOUND: data/SOURCES.md contains "news.google.com" (grep confirmed above)
- FOUND: data/SOURCES.md contains "intentionally generic" exactly once
- FOUND: commit 764114c exists in git log
- FOUND: figure-registry.mjs exits 0 with all 16 figures PASS
