---
phase: 28-news-visualizer-ui
reviewed: 2026-07-30T10:40:00Z
depth: deep
review_type: re-review (fix-cycle verification, WR-01..WR-05)
files_reviewed: 5
files_reviewed_list:
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - site/src/lib/newsFilterLogic.ts
  - site/src/lib/newsFilterLogic.test.ts
  - site/scripts/validate/facets.mjs
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
verdict: RE-REVIEW PASSED (all five fixes correct; 5 new WARNINGs to record and carry)
---

# Phase 28: Re-Review Report (fix cycle WR-01..WR-05)

**Method:** every claim below was re-derived by execution (mutate → run → observe → restore),
never by reading `28-REVIEW-FIX.md`. Working tree confirmed clean (`git status --short` empty)
after all probes.

## Fix verdicts

| Fix | Correct? | Gated? | Evidence |
|-----|----------|--------|----------|
| WR-01 replaceState | YES | **NO** | code correct; no test/validator covers it (WR2-01) |
| WR-02 hidden-card guard | YES | YES | 5 probes RED; 2 leaks (WR2-02, WR2-03) |
| WR-03 window pinning | YES | YES | 5/5 mutations RED |
| WR-04 comment-stripper | YES | YES | probe RED; new false-positive class (WR2-04) |
| WR-05 nested-paren scan | YES | YES | 2 probes RED; bounded miss remains (WR2-05) |

### WR-01 — correct

`site/src/pages/news.astro:461-474` and `site/src/pages/es/noticias.astro:462-475` are
byte-identical. Traced by construction against `serializeFilterParams`
(`site/src/lib/newsFilterLogic.ts:83-90`), which emits **comma-joined single-keyed** params
(`family=a,b`), so `nextParams.set()` is safe — there is no repeated-key value-loss bug.
Foreign params survive (only the four filter keys are deleted); the empty state yields
`location.pathname` with no trailing `?` because `qs` is falsy; `location.hash` is appended.

### WR-03 — correct and genuinely pinned (5/5 mutations RED)

| Mutation on `newsFilterLogic.ts` | Result |
|---|---|
| `WINDOW_30D_WIDTH_DAYS = 30 → 31` | RED (1 failed / 14 passed) |
| drop `- 1` in the 7d width | RED |
| drop `- 1` in the 30d width | RED |
| `today`: `dateStr === newestDate → >=` | RED |
| `serializeFilterParams` empty → `'x'` | RED |

Baseline 15/15 GREEN, restored.

### WR-02 / WR-04 / WR-05 — validator probes (baseline: `PASS … 21 assertions passed`)

| Probe | Expected | Observed |
|---|---|---|
| `hidden` on an EN `<article class="news-card">` | FAIL | FAIL a12 |
| `hidden` on an ES `.news-card` | FAIL | FAIL a12 (ES covered) |
| `hidden` on a `.news-month-section` | FAIL | FAIL a12 |
| `hidden` as the *last* attribute (`… hidden>`) | FAIL | FAIL a12 |
| `<style>.news-card{display:none}` | FAIL | FAIL a12 |
| scoped `.news-card[data-astro-cid-…]{…display:none}` | FAIL | FAIL a12 |
| existing `#news-empty hidden` node | PASS | PASS (no false fire) |
| `innerHTML` on a line also containing `https://…` | FAIL | FAIL a20 |
| `toLocaleDateString(getLoc(), {month: String("long")})` | FAIL | FAIL a11 |
| `toLocaleDateString("en-US", {month:"long"})` | FAIL | FAIL a11 |

**No new tautology.** Every one of the three new assertion-12 branches was made to fire.
F-24's count of 3 unfailable blocks does not grow.

## Narrative Findings (AI reviewer)

### WR2-01 (WARNING) — the WR-01 fix ships with no gate; Test 12 pins a function the fix never touched

**File:** `site/src/lib/newsFilterLogic.test.ts:129-132`, `site/src/pages/news.astro:461`

Test 12 asserts `serializeFilterParams({family:[],region:[],window:'',q:''}) === ''`. That function
is byte-identical before and after `9bbde22` — Test 12 passes on the *pre-fix* tree. The defect
WR-01 reported (`'?' + serializeFilterParams(...)` in the page's inline script producing a bare `?`
and dropping `utm_source`) lives in the `.astro` inline `<script>`, which no vitest spec and no
validator assertion touches. Mutating the page back to `history.replaceState(null,'','?'+serializeFilterParams(active))`
leaves the whole suite and all 21 assertions GREEN.

**Fix (minimal):** add a source-scan assertion alongside the existing `SERIALIZATION_SITES` loop in
`site/scripts/validate/facets.mjs`:

```js
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  const s = readFileSync(pagePath, 'utf-8');
  if (/replaceState\([^)]*['"]\?['"]\s*\+\s*serializeFilterParams/.test(s)) {
    fail(`assertion 22 — ${locale} rebuilds the query from scratch (WR-01 regression)`);
  }
  if (!s.includes("location.pathname + (qs ? '?' + qs : '') + location.hash")) {
    fail(`assertion 22 — ${locale} lost the WR-01 URL-preserving replaceState form`);
  }
}
```

### WR2-02 (WARNING) — the new assertion 12 reproduces the exact defect WR-08 flagged in assertion 14

**File:** `site/scripts/validate/facets.mjs:548-553`

```js
/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"[^>]*\shidden[\s>]/
```

`\shidden[\s>]` is matched against the raw attribute *string*, so a `data-*` **value** containing
the token trips it. **Proven:** inserting `data-note="a hidden b"` on a visible EN news-card makes
the validator exit non-zero with *"ships a .news-card with the hidden attribute (NEWSUI-02
violation)"* — a false accusation. Cards carry `data-commune-norm` (free-form place names) and
`data-family` (LLM-classifier output), so the input is not fully controlled. The prior review
raised this exact class as WR-08; the fix cycle re-introduced it in new code.

**Fix:** require the token to be in attribute-name position, i.e. not inside quotes. Simplest sound
form — strip quoted values first:

```js
const tagsOnly = distHtml.replace(/="[^"]*"/g, '=""');
if (/<article\b[^>]*\bclass=""[^>]*\shidden[\s>]/.test(tagsOnly)) { … }
```

(or match `\shidden(?=[\s>])` against a per-tag attribute list with values stripped).

### WR2-03 (WARNING) — assertion 12's display guard misses inline `style="display:none"` on a card

**File:** `site/scripts/validate/facets.mjs:554-556`

The comment claims to catch "author CSS [that] overrides `display` on the hidden-controlled nodes",
but `/\.news-card[^{}]*\{[^}]*display\s*:/` only inspects stylesheet rules. **Proven:** adding
`style="display:none"` directly to a rendered `<article class="news-card">` leaves the validator at
`PASS … 21 assertions passed`. F-26 binds `hidden` as the *only* show/hide mechanism, so an inline
`style.display` regression — the most likely way a future edit would break it, since
`el.style.display = 'none'` is the reflex alternative to `el.hidden = …` — is ungated in both dist
and source.

**Fix:** add two checks:

```js
if (/<(article|section)\b[^>]*\bclass="[^"]*\bnews-(card|month-section)\b[^"]*"[^>]*\sstyle="[^"]*display\s*:/.test(distHtml)) {
  fail(`assertion 12 — ${locale} sets inline display on a news node (F-26 violation)`);
}
// and source-level, in the SOURCE_SCAN_FILES loop:
if (/\.style\.display\s*=/.test(codeOnly)) {
  fail(`assertion 20 — ${locale} uses style.display; F-26 mandates the hidden attribute`);
}
```

Also note the selector `\.news-card[^{}]*\{` matches prefix-siblings (`.news-card-title`,
`.news-cards-grid`) — it can fire on an unrelated rule. Anchor it: `\.news-card(?![\w-])`.

### WR2-04 (WARNING) — the WR-04 fix trades a false negative for a false positive

**File:** `site/scripts/validate/facets.mjs:830-834`

`.filter((line) => !/^\s*(\/\/|\/\*|\*)/.test(line))` drops only *whole-line* comments. A trailing
comment on a code line is now scanned as code. **Proven:** adding `let z = 1; // never use innerHTML here`
to `news.astro` fails assertion 20 with *"contains forbidden DOM sink /innerHTML/"* — a
false positive on a doc comment, which is precisely the class the original stripper existed to
prevent (the removed comment says so verbatim). Both pages already carry
`// … T-12-01: value assignment only, never innerHTML` — today as whole-line comments, so the build
is green; converting one to a trailing comment silently reddens CI.

**Fix:** strip trailing comments but skip `//` preceded by `:` (URL scheme) or inside a string:

```js
.map((line) => line.replace(/(^|[^:'"`\\])\/\/(?!\/).*$/, '$1'))
```

Or keep the whole-line filter and add an explicit allow: `if (/^\s*[^'"]*\/\/[^'"]*$/.test(line))`.
Either way, restore the doc-comment tolerance without restoring the URL truncation.

### WR2-05 (WARNING) — assertion 11's 400-char window is a strictly-better but still-unsound bound

**File:** `site/scripts/validate/facets.mjs:513`

**Proven:** a `toLocaleDateString("en-US", { … ~500 chars of padding … month: "long" })` call with
no `timeZone` leaves the validator at `PASS`. The `[^)]*` silent-escape is gone, but the failure
mode is unchanged in kind — the scan does not fail, it stops looking. Complementary risk (not
proven, but structural): the window can also reach *forward* into an unrelated `month:` after a
legitimate no-month call and fire spuriously.

**Fix:** balance the parens instead of guessing a length — walk forward from `m.index` counting
`(`/`)` (skipping quoted spans) and slice the exact argument region; then the check is sound in
both directions. If that is judged too heavy, at minimum assert the tail contained a closing `)`
within 400 chars and `fail()` if it did not, so an over-long call is loud rather than silent.

## Also-checked (clean)

- **EN/ES parity:** diffed both pages in full. Only legitimate deltas — import depth
  (`../lib` vs `../../lib`), `EN_STRINGS`/`ES_STRINGS`, `FAMILY_LABELS_EN`/`_ES`, locale tag
  (`en-US`/`es-CL`), commune-URL prefix (`/commune/` vs `/es/comuna/`), CSS-block ordering, and
  translated prose/comments. The WR-01 block is byte-identical across the two files.
- **F-26:** no `style.display` in shipped code (gap is in the *gate*, see WR2-03, not the code).
- **F-27/F-30:** single imported `newsFilterLogic` module; no copy-pasted twin introduced.
- **F-29:** no `facetKeys` serialization added.
- **F-32:** every `toLocaleDateString` in both pages carries `timeZone: 'UTC'`; exactly one
  `data-result-count-template` `{n}` carrier per page.
- **NEWSUI-06:** no `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` in shipped code.
- **No new tautology or unreachable assertion branch** among assertions 11-21 (all new branches
  demonstrated failable above).
- `freshness` validator red — pre-declared F-19 environmental exclusion, **not a finding**.

## Info / still-open carry from `28-REVIEW.md`

### IN-01 (INFO) — WR-06 is the one carried item that genuinely matters

`site/src/lib/newsFilterLogic.ts:171-173` — `norm(active.q)` still untrimmed. User-visible on a live
typeahead: `"santiago "` matches zero communes. Not a fix-cycle regression, but the highest-value
remaining defect; recommend fixing before Phase 28 closes.

### IN-02 (INFO) — WR-07 (`'{n} incidents shown'` at n=1) and WR-08 (assertion 14 substring `hidden`) confirmed still open

`site/src/config/i18n.ts:365,589` unchanged; `facets.mjs` assertion 14 unchanged. WR-08 is now
doubly relevant given WR2-02 — fix both `hidden` matchers in one commit.

### IN-03 (INFO) — IN-01..IN-06 from the prior review all confirmed still open

Verified `FILTER_LOGIC_MARKER` is in fact *used* on both pages (`news.astro:328,338`), so prior
IN-01 ("unused frontmatter import") is **incorrect as written** — the import is live. The other
five (dead `news_cluster_source_count` key, unreachable `return false` at
`newsFilterLogic.ts:136`, stale validator header, `public/data` vs repo `data/`, assertion 17
brittleness) stand; all are record-and-carry.

---

_Reviewed: 2026-07-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep (execution-verified re-review)_
