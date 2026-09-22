---
phase: 28-news-visualizer-ui
fixed_at: 2026-07-30T10:41:30Z
review_path: .planning/phases/28-news-visualizer-ui/28-REVIEW-2.md
iteration: 2
findings_in_scope: 5
fixed: 5
skipped: 0
tests_passed: true
test_command: "npx astro check (4/0 baseline) && npm run build && npm test && npm run validate && python -m pytest -q"
status: all_fixed
---

# Phase 28: Code Review Fix Report (cycle 2 of 2)

**Fixed at:** 2026-07-30T10:41:30Z
**Source review:** .planning/phases/28-news-visualizer-ui/28-REVIEW-2.md (plus carried WR-06 from 28-REVIEW.md)
**Iteration:** 2

**Summary:**
- Findings in scope: 5 (WR-06, WR2-01, WR2-02, WR2-03, WR2-04)
- Fixed: 5
- Skipped: 0
- Test gate: PASSED

## Test Gate

- PASSED — `npx astro check` confirmed the 4/0 baseline (unchanged), `npm run build` succeeded (834 pages),
  `npm test` (vitest) reported 37/37 passing across 3 files, `npm run validate` reported 15/16 validators
  passing with only the pre-declared `freshness` environmental exclusion red (current.json is 3.0 days old,
  cron alive on `origin/master` per non-negotiable rule #10 — not a regression), and
  `python -m pytest -q` reported 344 passed, 1 skipped, 1 xfailed.

## Fixed Issues

### WR-06: comuna query never trimmed, zeroing matches on trailing/leading whitespace

**Files modified:** `site/src/lib/newsFilterLogic.ts`, `site/src/lib/newsFilterLogic.test.ts`
**Commit:** b62dec1
**Applied fix:** Added `.trim()` as the first step inside the shared `norm()` function (the single
canonical normalizer used both server-side for `data-commune-norm` and client-side for the comuna
filter), so "santiago " and "santiago" now normalize identically. Verified no caller depends on
preserved surrounding whitespace before making the change. Added Test 16 pinning the behavior, then
mutation-tested it: removed `.trim()`, ran `npm test`, observed Test 16 RED
(`expected '  santiago  ' to be 'santiago'`, 1 failed / 36 passed), restored, reconfirmed 37/37 green.

### WR2-02: assertion 12's hidden-attribute check matched inside data-* attribute VALUES

**File:** `site/scripts/validate/facets.mjs:548` (now ~561-572)
**Commit:** 44dc007
**Applied fix:** Replaced the raw-string regex `\shidden[\s>]` (which fires on `data-note="a hidden b"`
regardless of whether it's an attribute name or value substring) with a per-tag scan: for every
captured `<article ...>` / `<section ...>` opening tag that carries the `news-card` / `news-month-section`
class, strip every `="..."` attribute-value body first, then test for a bare `hidden` token in
attribute-name position. Demonstrated RED both directions against a real build (dist/news/index.html):
(a) injecting a real `hidden` attribute on a visible EN card FAILS assertion 12 (`ships a .news-card
with the hidden attribute`); (b) injecting `data-note="a hidden b"` on a visible card leaves the
validator at `PASS ... 21/22 assertions passed` (no false fire). Restored dist/ from backup and
re-confirmed clean.

### WR2-03: assertion 12's display guard missed inline `style="display:none"` on a card

**File:** `site/scripts/validate/facets.mjs:554` (now ~573-586)
**Commit:** 4f8569b
**Applied fix:** Added a per-tag check alongside the existing stylesheet-only display guard: for every
`<article>` / `<section>` opening tag carrying the `news-card` / `news-month-section` class, test its
own `style="..."` attribute value for a `display` declaration. Demonstrated RED against a real build:
injecting `style="display:none"` on a visible EN card FAILS assertion 12 (`sets inline
style="display:..." on a news node (F-26 violation)`). Restored dist/ from backup, reconfirmed
21/21-then-22 assertions PASS.

### WR2-04: WR-04's comment stripper traded a false negative for a false positive

**File:** `site/scripts/validate/facets.mjs:830-834` (now ~857-870)
**Commit:** 172c898
**Applied fix:** Replaced the whole-line-only comment filter with: (1) keep filtering out lines that
are entirely `/*` or `*` block-comment continuation lines, then (2) strip a trailing `// ...` from
every remaining line via `line.replace(/(^|[^:'"\`\\])\/\/(?!\/).*$/, '$1')`, which skips a `//`
immediately preceded by `:` (a URL scheme) so a `https://` literal is never mistaken for a comment
start. Demonstrated all three required directions against `src/pages/news.astro`, each RED then
restored: (a) `el.innerHTML = 'https://ischilesafe.com/news/';` with no comment still FAILS assertion 20
(WR-04 case does not regress); (b) appending `// never use innerHTML here` as a trailing comment on an
existing code line does NOT fail (PASS, 22/22); (c) a real `el.innerHTML = x;` with no URL/comment
still FAILS assertion 20.

### WR2-01: the WR-01 replaceState fix shipped with no source-level gate

**File:** `site/scripts/validate/facets.mjs` (new assertion 22, end of file)
**Commit:** 059e566
**Applied fix:** Added assertion 22, mirroring the existing `SERIALIZATION_SITES` source-scan pattern
used by assertion 7: fails if either `news.astro` / `es/noticias.astro` contains
`replaceState(..., '?' + serializeFilterParams` (the pre-WR-01 regression form), or no longer contains
the URL-preserving `location.pathname + (qs ? '?' + qs : '') + location.hash` form. Bumped the final
"N assertions passed" counter from 21 to 22. Demonstrated RED: reverted `news.astro`'s `replaceState`
call to `history.replaceState(null, '', '?' + serializeFilterParams(active));`, ran the validator,
observed `FAIL facets: assertion 22 — EN rebuilds the query from scratch with '?' + serializeFilterParams
(WR-01 regression)`. Restored the file, reconfirmed `PASS facets: ... 22 assertions passed`.

## Accepted, Not Fixed (per orchestrator instruction)

- **WR2-05** — assertion 11's 400-char tail window is still theoretically escapable by an extremely
  long `toLocaleDateString` options object. Explicitly marked out-of-scope for this cycle by the
  orchestrator; left as-is.

---

_Fixed: 2026-07-30_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
