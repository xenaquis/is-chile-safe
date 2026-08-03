---
phase: 31-docs-methodology-refresh
reviewed: 2026-08-02T23:15:00Z
depth: deep
files_reviewed: 12
files_reviewed_list:
  - site/src/pages/methodology.astro
  - site/src/pages/es/metodologia.astro
  - site/src/pages/safest-cities-in-chile.astro
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - site/src/config/i18n.ts
  - data/SOURCES.md
  - site/scripts/validate/figure-registry.mjs
  - site/scripts/validate/figure-registry.lib.mjs
  - site/scripts/validate/figure-registry.test.ts
  - site/scripts/validate/coverage.mjs
  - site/scripts/validate/facets.mjs
findings:
  critical: 3
  warning: 3
  info: 5
  total: 11
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-08-02
**Depth:** deep (run + mutate)
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Baseline reproduced exactly as claimed: `npm run build && npm run validate` → **15/16, freshness sole failure** (pre-authorized F-19); `npx vitest run` → **55 passed / 6 files**; `figure-registry.mjs` exit 0 with F15 and F16 both PASS.

Every new gate was broken and restored. All of them are genuinely falsifiable — DOCS-01 negative + positive checks, DOCS-03 tokens, `coverage.mjs` assertion F, `facets.mjs` 23 and 23b, and the four vitest cases. The whitespace normalization is real (a deliberate three-way re-wrap of the corrected EN sentence still exits 0). `extractSection`'s line-anchoring rationale is real and verified: `data/SOURCES.md:313` genuinely contains an inline backtick cross-reference `` `## INE ENUSC SAE — communal VHDV `` that precedes the real heading at line 324 in file order, and a naive `indexOf` would match it. F-67 was honoured — no CLI guard exists; the script executes its whole registry.

**But the phase's headline objective is not met.** Its own stated success criterion — "zero remaining instances of the inverted national_rank claim anywhere in `site/src`" — is false. A fourth instance, in Spanish, is still live in production `dist/`, and the new DOCS-01 guard is structurally incapable of ever catching it. Compounding this, `31-01-SUMMARY.md` asserts the opposite, "verified" by a grep scoped to a phrase that page does not use. This is the same defect class the review brief warned about: the gate measures what it was written to measure.

Tree finished clean: `git status --porcelain` → empty; all mutated `dist/` files restored and the three validators re-run green.

## Critical Issues

### CR-01: The inverted national-rank claim is still live in Spanish on the ES twin SEO page

**File:** `site/src/pages/es/comunas-mas-seguras-chile.astro:162`
**Severity:** CRITICAL

The EN page's footnote was corrected. Its Spanish twin carries the identical inverted claim, untouched:

```
Rango nacional 1 = tasa más baja reportada entre todas las comunas no de baja población de Chile.
```

`pipeline/cead/normalizer.py:111-141` sorts `reverse=True` — rank 1 is the **highest** rate. This is verbatim wrong, and it is shipped:

```
$ grep -o "Rango nacional 1 = [^<]*" dist/es/comunas-mas-seguras-chile/index.html
Rango nacional 1 = tasa más baja reportada entre todas las comunas no de baja población de Chile.
```

The page renders `{c.nationalRank}` in a "Rango nacional" column (line 151) exactly as the EN page does, so an equivalent footnote *does* exist and *is* wrong. Plan 31-01 Task 2 instructed "grep confirms no equivalent footnote exists there — do not add one," and `31-01-SUMMARY.md:82` "proves" it with `grep -c "menor tasa reportada" .../comunas-mas-seguras-chile.astro`. That grep returns 0 because the page says **`tasa más baja reportada`**, not `menor tasa reportada`. The premise was never true.

Net effect: Phase 31 corrected EN and left ES wrong — the exact EN/ES parity divergence Research Pitfall 1 was written to prevent — on the site's credibility-critical territory-comparison page.

**Fix:** replace line 162 with the Spanish equivalent of the EN correction, ban-list-safe (do NOT use `la más segura`):

```astro
      La columna Rango nacional (una medida sitewide distinta, no el orden de esta tabla)
      sigue el criterio rango 1 = mayor tasa reportada a nivel nacional — más delincuencia
      reportada, no menos.
```
Then run `node scripts/validate/forbidden-language.mjs` before commit.

### CR-02: The DOCS-01 regression guard cannot detect CR-01 — wrong file set, wrong phrase set

**File:** `site/scripts/validate/figure-registry.mjs:277-283, 296-300`
**Severity:** CRITICAL

`DOCS01_TARGETS` contains only the three files the executor happened to edit; `INVERTED_PHRASES` contains only the three literal strings that were fixed. `es/comunas-mas-seguras-chile.astro` is absent, and the phrase variant `tasa más baja reportada` is absent. The guard therefore reports six green PASS lines while the live inverted claim sits one directory away:

```
$ node scripts/validate/figure-registry.mjs
PASS [DOCS-01] methodology.astro contains "highest reported rate in Chile"
PASS [DOCS-01] metodologia.astro contains "mayor tasa reportada en Chile"
PASS [DOCS-01] safest-cities-in-chile.astro contains "highest reported rate nationwide"
...
EXIT=0
```

A regression guard scoped to the diff rather than to the claim is a guard that can only ever confirm the fix it was written alongside.

**Fix:** make the negative check a repo-wide scan over `site/src/**/*.{astro,ts,tsx}` for a *pattern family* rather than three literals — e.g. `/(rank|rango|ranking|posición)\s*(nacional\s*)?1\s*=\s*(lowest|menor|más baja|tasa más baja)/i` over `norm(content)` — and add a fourth positive check for the ES twin page once CR-01 is fixed.

### CR-03: `data/SOURCES.md` asserts LLM geolocation; the pipeline does deterministic lookup — and contradicts this phase's own edit to `news.astro`

**File:** `data/SOURCES.md:411-415`
**Severity:** CRITICAL (factual-accuracy requirement 6)

The rewritten Classification block states:

> Items are classified and geolocated by `ibm-granite/granite-4.1-8b` via OpenRouter (`pipeline/news/classifier.py`)

`pipeline/news/classifier.py:26` — "LLM emits commune_name (Spanish name) + region_hint — **NOT a bare CUT code**". Geolocation is performed by `pipeline/news/resolver.py`, whose own docstring reads: *"Deterministic name→(cut, slug) lookup … Anti-hallucination: resolve_cut returns None for any name not in the closed 346-commune set. **No network calls; no LLM; pure dict lookup.**"*

This same phase edited `site/src/pages/news.astro:5-7` to say the *opposite* and correct thing ("classified by the news pipeline's LLM classifier and geolocated by the deterministic commune name->CUT resolver"). SOURCES.md is the F15 source-of-record and now contradicts both the code and the site. `resolver.py` — the single most important anti-hallucination control in the news layer, and the fix that made Phase 16 shippable — is not mentioned anywhere in the rewritten section. Relatedly, the F15 registry description at `site/scripts/validate/figure-registry.mjs` still reads "location from RSS feeds", which was never true.

**Fix:** split the claim —

```markdown
**Classification:** Items are classified (crime family, severity, commune *name*) by
`ibm-granite/granite-4.1-8b` via OpenRouter (`pipeline/news/classifier.py`) …

**Geolocation:** The LLM never emits a CUT. Every LLM-emitted commune name is resolved
through `pipeline/news/resolver.py`, a deterministic dict lookup against the closed
346-commune set from `data/cead/meta/index.json`; unresolvable names yield `None` and the
incident is dropped rather than guessed.
```
and update F15's description to "location from deterministic name→CUT resolution".

## Warnings

### WR-01: `checkF16`'s hardening still passes a 205-character stub that merely mentions "VHDV"

**File:** `site/scripts/validate/figure-registry.lib.mjs:52-71`
**Severity:** HIGH

`checkF16` builds `whole = heading + body` where `heading` is the short constant `'## INE ENUSC SAE'`. That constant already satisfies group 1's first token and group 2's `ENUSC`/`SAE`. So group 1 collapses to a single requirement: the string `VHDV` appearing anywhere in a >200-char body. Probe (`site/scripts/validate/_probe.mjs`, deleted after use):

```
A padded-stub-with-VHDV (len 205) => true      <-- HOLE
B padded-stub-no-tokens (len 270) => false
C heading+150                     => false
D 201 filler no VHDV              => false
E real data/SOURCES.md            => true  seclen 1562
G gutted real section             => false
```

Test 4a in `figure-registry.test.ts:79-84` uses `'x'.repeat(250)` — filler that deliberately contains none of the tokens — so it proves the token check, not the stub case. The plan's stated must-have ("can no longer report PASS against a stub section") holds only for token-free stubs; a stub that copies the heading's own word `VHDV` into its filler still passes. The margin is large (real body 1562 chars vs. floor 200), so the floor can be raised cheaply.

**Fix:** raise the floor to `<= 600` (still below the file's shortest real section, 676) and strip the heading from the token test as well, adding a group-1 variant that requires `VHDV` to appear in `body`, not in `whole`.

### WR-02: The Spanish facet note quotes a UI control label that does not exist

**File:** `site/src/config/i18n.ts:614`
**Severity:** HIGH (EN/ES parity + factual accuracy)

The ES note tells readers: `"Más reciente" está anclado a la fecha del incidente más nuevo…`. The actual radio label rendered at `site/src/pages/es/noticias.astro` comes from `i18n.ts:601`, `news_window_latest: 'Últimos datos: {date}'`. There is no control labelled "Más reciente" anywhere on the page — a Spanish reader looking for the thing the note explains will not find it. (EN is only marginally better: the note says `"Latest"`, the control says `Latest data: {date}`.)

Assertions 23 and 23b cannot catch this: 23 requires only non-empty text, 23b requires only that EN≠ES.

**Fix:** quote the real labels — ES `"Últimos datos"`, EN `"Latest data"` — or reference the control positionally ("el filtro de período más reciente").

### WR-03: `facet-semantics-note` is a dead class — the new paragraph ships unstyled

**File:** `site/src/pages/news.astro:198`, `site/src/pages/es/noticias.astro:196`
**Severity:** MEDIUM

```
$ grep -rn "facet-semantics-note" site/src/ | wc -l
2
$ grep -rn "facet-semantics-note" site/dist/_astro/*.css
(no output)
```

Both occurrences are the class *usage*; no rule defines it in either page's `<style>` block, in `src/styles/`, or in the emitted CSS. Every comparable note on these pages (`.table-note`, `.filter-count`) has a rule. The result is a four-sentence, full-body-size paragraph rendered directly beneath the H1/updated-timestamp on the highest-traffic news surface, in both locales.

**Fix:** add to both pages' `<style>` blocks a rule matching the existing `.table-note` treatment (smaller font-size, muted colour, constrained max-width).

## Info

### IN-01: `figure-registry.mjs` prints its global PASS banner before the checks that can still fail

**File:** `site/scripts/validate/figure-registry.mjs:255-257` vs `258-361`
Under the mutation probe the script emitted `figure-registry: PASS — all 16 in-scope figures …` and then `figure-registry: FAILED — 2 DOCS-01/DOCS-03 content check(s) failed` in the same run (exit 1, correctly). Confusing in CI logs. Move the figures banner below all checks, or scope its wording to figures only.

### IN-02: A single figure orphan suppresses all DOCS-01/DOCS-03 diagnostics

**File:** `site/scripts/validate/figure-registry.mjs:246-253`
The `orphans.length > 0 → process.exit(1)` block runs before the new content checks, so an unrelated orphan hides every DOCS finding until it is fixed, forcing serial debugging. Exit status is still correct. Accumulate into one failure list and exit once at the end.

### IN-03: `extractSection` truncates at any `## ` line, including inside a fenced code block

**File:** `site/scripts/validate/figure-registry.lib.mjs:38-40`
`rest.search(/\n## /)` is not fence-aware. `data/SOURCES.md` has no such content today, so this is latent, not live. Note it, or skip fenced regions.

### IN-04: `31-01-SUMMARY.md` records a verified-false claim

**File:** `.planning/phases/31-docs-methodology-refresh/31-01-SUMMARY.md:27,49,82`
"no equivalent national-rank footnote exists there, so no parity gap to close", evidenced by a grep for a phrase the page does not use. See CR-01. Correct the record when CR-01 is fixed; the failure mode (proving absence with a literal borrowed from the *other* page) is worth adding to STATE.md's pitfalls.

### IN-05: Editorial spirit — "not safest" on the safest-cities note

**File:** `site/src/pages/safest-cities-in-chile.astro:175`
`forbidden-language.mjs` exits 0 and the sentence *denies* a verdict rather than issuing one, so it does not violate the hard rule. It is nonetheless the one place in the new prose that puts a bare superlative safety word next to a commune table. `— most reported crime, not the least` reads identically and removes the ambiguity entirely.

## Verified Clean (no finding)

- **Corrected claims match `normalizer.py`, both locales.** EN `methodology.astro:337-339` and ES `es/metodologia.astro:350-351` both now say rank 1 = highest/mayor, and are semantically equivalent to each other.
- **No collateral damage.** `git diff d8db0ab..HEAD --stat` shows `chile-crime-map.astro`, `rankings.astro`, `is-chile-safe.astro`, `is-santiago-safe.astro`, `es/comunas-mas-seguras-chile.astro`, `compare/[pair].astro`, `comparisonProse.ts` all untouched. All of their low-rate prose re-read and confirmed correct, including `comparisonProse.ts:198,287` (`rank 1 = highest reported incidence` / `posición 1 = mayor incidencia`) and both `tierDesc` helpers.
- **All new gates falsifiable** (mutated → non-zero exit → restored): DOCS-01 negative `MUTATED_EXIT=1`; three-way re-wrap `REWRAP_EXIT=0` (normalization works); `coverage.mjs` assertion F → `FAIL [F] anchor-presence: EN methodology page missing id="trend-formula"`, exit 1; facets 23 (note deleted from ES dist) → exit 1; facets 23b (EN inner text copied into ES dist) → `FAIL facets: assertion 23b — … byte-identical`, exit 1.
- **No coverage loss.** No CLI guard in `figure-registry.mjs` (F-67 honoured); full 16-figure registry executes; F15 and F16 both PASS on the real file; `all.mjs` registers exactly 16 validators; no document's "16 validators" figure went stale.
- **Anchors intact in built HTML.** `dist/methodology/index.html`: `trend-formula`, `comparison-criteria`, `national-mean`, `sexuales-family` each ×1. `dist/es/metodologia/index.html`: `trend-formula`, `comparison-criteria`, `media-nacional`, `familia-sexuales` each ×1.
- **`sexuales` explainer parity.** Present in both locales, semantically equivalent, and factually correct against `pipeline/shared/schema.py:20-22` (7 CEAD `FAMILY_KEYS` + news-only `sexuales`); `facets.mjs` observes exactly 8 families.
- **SOURCES.md News section, everything except CR-03.** Google News RSS search URL (`feeds.py:32`), `_GOOGLE_NEWS_QUERIES` with `GoogleNews-Nacional`/`GoogleNews-Antofagasta` (`feeds.py:40,43`), `gnews_decoder.py` redirect resolution, direct feeds BioBioChile/Cooperativa/LaTercera/LaCuarta (`feeds.py:66-69` — stale Emol/T13 correctly removed), `resolve_outlet()` fallback to the literal `"Google News"` (`feeds.py:152,159`), Granite default via `NEWS_PROVIDER=openrouter` with DeepSeek as fallback (`classifier.py:58-79`), R2 bucket `ischilesafe`, storage path corrected to `data/incidents/current.json`.
- **ENUSC vintage (F-60).** No edition year written for the underreporting bullets (`SOURCES.md:307-314`); the separate dated SAE VHDV section retains "Reference year 2024; first published 2026-01-21".
- **Facet-note substance** (apart from WR-02) matches `newsFacets.ts:8-17,180-195`: counts are unfiltered per-option totals; the window anchor is the newest incident's date via UTC string arithmetic.
- **`extractSection` line-anchoring** is necessary and correct: the inline cross-ref at `SOURCES.md:313` precedes the real heading; regex is a simple escaped `^`-anchored literal — no backtracking or escaping defect, and it lives in a real `.mjs`, never in a shell-quoted `node -e`.

## Environment / Restoration

```
$ git status --porcelain
(empty)
```
`data/` was never written. Mutations were made only to `site/src/pages/methodology.astro` (restored from backup) and to two `dist/` HTML files (restored from backup); the scratch `_probe.mjs` was deleted. `facets.mjs`, `coverage.mjs`, `forbidden-language.mjs` all re-run at exit 0 after restoration.

---

## Fix cycle 1

_Fixed: 2026-08-02_
_Fixer: Claude (gsd-code-fixer)_

All 3 CRITICALs, both HIGHs, and M1 were fixed and committed atomically. Every fix was proven RED-then-GREEN with real command output before commit.

### CR-01: inverted claim on ES safest-cities twin

**Changed:** `site/src/pages/es/comunas-mas-seguras-chile.astro:162` — replaced the inverted footnote sentence with the corrected, ban-list-safe sentence supplied in the review (`La columna Rango nacional es una medida a nivel de sitio, distinta del orden de esta tabla: rango 1 = mayor tasa reportada a nivel nacional, es decir, la comuna con más delitos reportados.`). Rest of the page untouched.

**RED:** production `dist/es/comunas-mas-seguras-chile/index.html` (pre-fix) contained `Rango nacional 1 = tasa más baja reportada entre todas las comunas no de baja población de Chile.` — verbatim inverted claim, verified by the reviewer's own grep.

**GREEN:** `grep -o "mayor tasa reportada a nivel nacional" dist/es/comunas-mas-seguras-chile/index.html` → `mayor tasa reportada a nivel nacional` (post-build, present); `node scripts/validate/forbidden-language.mjs` → `PASS — 835 pages scanned, 0 forbidden terms found`.

**Commit:** `a861c75`

### CR-02: DOCS-01 guard rewritten as a repo-wide sweep

**Changed:** `site/scripts/validate/figure-registry.mjs` — replaced the hardcoded `DOCS01_TARGETS` (3 files) / `INVERTED_PHRASES` (3 literals) with a recursive walk of every `.astro` file under `site/src/pages/`, matched against an accent-stripped (`NFD` + combining-mark strip) and whitespace-normalized phrase family covering all EN/ES inverted variants (including `tasa más baja reportada` / `tasa mas baja reportada` / both `Rango nacional 1 = tasa ...` forms). Added a 4th positive check asserting `mayor tasa reportada a nivel nacional` in the ES safest-cities twin. Also corrected the stale F15 description ("location from RSS feeds" → "location from deterministic name→CUT resolution").

**RED:** with the corrected CR-01 sentence reverted back to the inverted phrase, `node scripts/validate/figure-registry.mjs` exited 1 and printed:
```
FAIL [DOCS-01] src/pages/es/comunas-mas-seguras-chile.astro contains the inverted phrase "tasa más baja reportada" (national_rank direction regression)
FAIL [DOCS-01] src/pages/es/comunas-mas-seguras-chile.astro contains the inverted phrase "tasa mas baja reportada" (national_rank direction regression)
FAIL [DOCS-01] src/pages/es/comunas-mas-seguras-chile.astro contains the inverted phrase "Rango nacional 1 = tasa más baja" (national_rank direction regression)
FAIL [DOCS-01] src/pages/es/comunas-mas-seguras-chile.astro contains the inverted phrase "Rango nacional 1 = tasa mas baja" (national_rank direction regression)
FAIL [DOCS-01] es/comunas-mas-seguras-chile.astro is missing the corrected phrase "mayor tasa reportada a nivel nacional"
figure-registry: FAILED — 5 DOCS-01/DOCS-03 content check(s) failed
```
(exit code confirmed 1 via a separate `echo REAL_EXIT=$?` run — the sweep names the exact regressed file, closing the gap CR-02 identified.)

**GREEN:** with CR-01's fix restored, `node scripts/validate/figure-registry.mjs` → all 16 figures PASS, all 4 DOCS-01 positive checks PASS, all 3 DOCS-03 checks PASS, exit 0.

**Commit:** `be72ac9`

### CR-03: SOURCES.md geolocation misattribution

**Changed:** `data/SOURCES.md:415-419` — split the single "Classification" paragraph (which claimed the LLM "classified and geolocated") into two entries: **Classification** (LLM classifies family/severity and proposes a commune *name*) and **Geolocation** (deterministic `pipeline/news/resolver.py` name→CUT dict lookup against the closed 346-commune set; unresolvable names are dropped, not guessed — the anti-hallucination control). Also updated `site/scripts/validate/figure-registry.mjs` F15 description to match. `data/SOURCES.md` was the only file touched under `data/` (F-66 honoured).

**Verification:** read `pipeline/news/resolver.py` (docstring: "No network calls; no LLM; pure dict lookup") and `pipeline/news/classifier.py` (docstring: "LLM emits commune_name ... NOT a bare CUT code") to confirm every word written is true of the code, and cross-checked against `site/src/pages/news.astro:5-7` which already said the correct thing — the two now agree.

**GREEN:** `node scripts/validate/figure-registry.mjs` → `PASS F15: News incidents (count, date, location from deterministic name→CUT resolution)`, `PASS [DOCS-03] data/SOURCES.md contains granite (case-insensitive)`, exit 0.

**Commit:** `46fdc0e`

### H1: checkF16 hardened against padded-stub-with-VHDV

**Changed:** `site/scripts/validate/figure-registry.lib.mjs` — `checkF16` now additionally requires the section BODY (heading excluded) to contain `VHDV`, `sha256`, AND `136 of 346` before the existing token-group check runs. `site/scripts/validate/figure-registry.test.ts` — replaced nothing from test 4a (kept as-is, it still probes the pure token-free case) and added test 4c (the exact padded-stub-with-VHDV case that used to pass) and test 4d (real section minus the sha256 line).

**RED (via `_probe.mjs`, deleted after use), all four required cases, output pasted verbatim:**
```
(c) heading + VHDV + 200 chars filler (CURRENT BUG target): true   <-- the hole
(a) real SOURCES.md: true
(b) heading only: false
(d) real section minus sha256 line: true   <-- also a hole (undetected before fix)
```

**GREEN, same four cases after the fix:**
```
(c) heading + VHDV + 200 chars filler (CURRENT BUG target): false
(a) real SOURCES.md: true
(b) heading only: false
(d) real section minus sha256 line: false
```

**Vitest:** `npx vitest run scripts/validate/figure-registry.test.ts` → `Test Files 1 passed (1)`, `Tests 6 passed (6)` (4 original + 2 new: 4c, 4d).

**Commit:** `6a62620`

### H2: ES facet note quotes real UI label

**Changed:** `site/src/config/i18n.ts` — both `news_facet_semantics_note` (EN, line 380) and its ES twin (line 614) corrected to quote `"Latest data"` / `"Últimos datos"` respectively (matching the real rendered control `news_window_latest: 'Latest data: {date}'` / `'Últimos datos: {date}'`), replacing the nonexistent `"Latest"` / `"Más reciente"`. EN and ES remain semantically equivalent but not byte-identical (required by assertion 23b).

**Verification:** read `site/src/pages/news.astro` / `es/noticias.astro` (both render `{t.news_window_latest}` as the control label) and `i18n.ts:367,601` to confirm the exact rendered strings before writing the note. Tier-1 re-read confirms both notes now contain the correct quoted label and the substitution is symmetric across locales.

**Commit:** `b895f7f`

### M1: facet-semantics-note CSS rule added

**Changed:** `site/src/pages/news.astro` and `site/src/pages/es/noticias.astro` — added a `.facet-semantics-note` rule to each page's `<style>` block (`font-size: var(--text-label); color: var(--muted); max-width: 65ch; margin: 0 0 var(--md)`), matching the existing `.table-note` treatment used elsewhere in the site.

**RED (pre-fix, from the original review):** `grep -rn "facet-semantics-note" site/dist/_astro/*.css` → no output; the class had two usages and zero rules.

**GREEN (post-fix, post-build):**
```
$ grep -o "facet-semantics-note[^;]*{[^}]*}" dist/news/index.html
facet-semantics-note[data-astro-cid-5kj6t6lp]{font-size:var(--text-label);color:var(--muted);max-width:65ch;margin:0 0 var(--md)}
$ grep -o "facet-semantics-note[^;]*{[^}]*}" dist/es/noticias/index.html
facet-semantics-note[data-astro-cid-xsumocn5]{font-size:var(--text-label);color:var(--muted);max-width:65ch;margin:0 0 var(--md)}
```
(Astro inlines scoped CSS directly into the page HTML rather than a shared external stylesheet, which is why the original review's `dist/_astro/*.css` grep found nothing even before this fix — the rule is confirmed present in the actual served HTML for both locales.)

**Commit:** `ba9398c`

### Full-instrument re-run (not just the touched lines)

```
$ cd site && npm run build && npm run validate
834 page(s) built in 23.94s
...
  PASS  structure / commune / rollout / region / crime / hreflang / schema / map /
        forbidden-language / coverage / spine / seo / figure-registry / avs-b-budget / facets
  FAIL  freshness  (data/incidents/current.json is 3.3 days old — pre-authorized F-19, sole failure, not remediated, data/incidents/ untouched)
15/16 validators passed

$ cd site && npm test
Test Files  6 passed (6)
Tests  57 passed (57)

$ python -m pytest pipeline/tests -q
344 passed, 1 skipped, 1 xfailed in 45.13s

$ npx astro check
Result (139 files):
- 4 errors   (all in src/components/ComparatorPairsLinks.astro:28, pre-existing, ts(7031) implicit-any — not touched by this fix cycle)
- 0 warnings
- 43 hints

$ node scripts/validate/forbidden-language.mjs
forbidden-language: scanning 835 HTML files in dist/
forbidden-language: PASS — 835 pages scanned, 0 forbidden terms found
```

All gates match or exceed the required bars: 15/16 with freshness the sole (pre-authorized) failure, 57 ≥ 55 vitest tests with zero failures, 344 passed / 1 skipped / 1 xfailed pytest, exactly 4 astro-check errors all in `ComparatorPairsLinks.astro:28`.

### Summary

- Findings in scope: 6 (CR-01, CR-02, CR-03, H1/WR-01, H2/WR-02, M1/WR-03)
- Fixed: 6
- Skipped: 0
- Commits: `a861c75`, `be72ac9`, `46fdc0e`, `6a62620`, `b895f7f`, `ba9398c`
- `git status --porcelain` (repo root, excluding this REVIEW.md edit): clean — no partial/uncommitted source changes remain.

---

_Reviewed: 2026-08-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
_Fix cycle 1: 2026-08-02_
_Fixer: Claude (gsd-code-fixer)_
