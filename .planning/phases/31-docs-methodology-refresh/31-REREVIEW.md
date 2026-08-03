---
phase: 31-docs-methodology-refresh
reviewed: 2026-08-03T03:30:00Z
depth: deep
review_type: re-review of fix cycle 1 (a861c75..ba9398c)
files_reviewed: 8
files_reviewed_list:
  - site/src/pages/es/comunas-mas-seguras-chile.astro
  - site/scripts/validate/figure-registry.mjs
  - site/scripts/validate/figure-registry.lib.mjs
  - site/scripts/validate/figure-registry.test.ts
  - site/src/config/i18n.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - data/SOURCES.md
findings:
  critical: 0
  high: 3
  medium: 1
  low: 3
  total: 7
status: issues_found
---

# Phase 31 — Fix Cycle 1 RE-REVIEW

**Verdict:** the six findings are all genuinely closed — CR-01, CR-03, H2 and M1 are correct and provably so.
But the two *guard* fixes (CR-02, H1) each introduced a new build landmine that the whole green suite
cannot see, because both landmines fire only on prose/format the repo does not contain *yet*. This is the
same failure shape as phases 27/28/30: the gate was widened along the axis it was attacked on and
narrowed along another.

Baseline reproduced: `npm run build && npm run validate` → **15/16, freshness sole FAIL** (pre-authorized
F-19). `npx vitest run` → **57 passed / 6 files**. `forbidden-language.mjs` → PASS, 835 pages, 0 terms.

---

## HIGH

### RR-H1: The DOCS-01 sweep bans a generic, factually-correct Spanish phrase — sitewide build landmine

**File:** `site/scripts/validate/figure-registry.mjs:288-296` (`INVERTED_PHRASES_RAW`)

`tasa más baja reportada` / `tasa mas baja reportada` are matched as **bare substrings against every
`.astro` page**, with no `rango … 1 =` context requirement. That phrase is ordinary, correct Spanish for
"lowest reported rate" — the literal subject matter of two pages on this site. The review's own
recommended fix was a *pattern family* anchored on `(rank|rango|…)\s*1\s*=`; the fixer shipped bare
literals instead.

Proof — a correct, editorially-clean sentence added to `rankings.astro` breaks the build:

```
$ node -e "...append '<!-- Esta comuna registra la tasa mas baja reportada de su region segun CEAD. -->'"
$ node scripts/validate/figure-registry.mjs
FAIL [DOCS-01] src/pages/rankings.astro contains the inverted phrase "tasa más baja reportada" (national_rank direction regression)
FAIL [DOCS-01] src/pages/rankings.astro contains the inverted phrase "tasa mas baja reportada" (national_rank direction regression)
FP_EXIT=1
```
(file restored via `git checkout`, validator back to exit 0)

How close the repo already is: `src/pages/es/comunas-mas-seguras-chile.astro:108` is
`<h2>Comunas con Menor Tasa Reportada …</h2>` and `src/pages/es/index.astro:52` is
`// Menor tasa reportada (ascendente)`. One editor writing "las comunas con menor tasa reportada en
Chile" or "…la tasa más baja reportada de la región" red-lines CI with a message accusing them of a
`national_rank direction regression` they did not commit. On the *safest-cities* pages that is the most
natural sentence in the language.

**Fix:** replace the four bare `tasa … baja` literals with a context-anchored regex, e.g.
```js
const INVERTED_PATTERNS = [
  /\b(rank|rango|ranking|posicion)\s*(nacional\s*)?#?\s*1\s*(=|:|es|is)\s*[^.]{0,40}(lowest|menor|mas baja|safest|mas segura)/i,
  /lowest reported rate in Chile/i,
  /menor tasa reportada en Chile/i,
  /lowest reported rate among all non-low-population/i,
];
```
run over `stripAccents(norm(content))`. The four false-negative probes below still pass under this form.

### RR-H2: The DOCS-01 sweep still can't see `src/lib/*.ts` or `src/components/*.astro` — where most of the site's rank-direction prose actually lives

**File:** `site/scripts/validate/figure-registry.mjs:284, 298-300`

`PAGES_ROOT = src/pages` and the filter is `.endsWith('.astro')`. That visits **52 files**; `src/` holds
**77** `.astro` files, plus the `.ts` prose generators. The review's stated fix was
`site/src/**/*.{astro,ts,tsx}`; the fixer narrowed it to pages-only.

```
$ node (listAstroFiles(src/pages))
COUNT 52     dirs: . commune communes compare crime crime-ranking es es\comparar es\comuna
             es\comunas es\delito es\ranking-delito es\region region
$ find src -name "*.astro" | wc -l
77
```

The unguarded prose is not hypothetical — `src/lib/comparisonProse.ts:198,209,287,299` emits
`rank 1 = highest reported incidence` / `posición 1 = mayor incidencia reportada` onto **every**
`/compare/[pair]/` page in both locales, and `src/lib/proseEngine.ts:58` carries the same invariant as a
comment. Invert any of those and DOCS-01 reports six green PASS lines — the *exact* structural defect
CR-02 was raised to kill, just relocated one directory.

**Fix:** widen the walk to `src/` with `['.astro', '.ts', '.tsx'].some(ext => e.name.endsWith(ext))`, or
add `src/lib` and `src/components` as extra roots. Confirmed no current file trips it (see RR-C below).

### RR-H3: `checkF16`'s new hidden requirements fail with `Missing tokens: []` — a misdiagnosing build landmine

**Files:** `site/scripts/validate/figure-registry.lib.mjs:69-70`; caller `site/scripts/validate/figure-registry.mjs:226-236`

`checkF16` now returns false unless the body contains the exact literals `sha256` and `136 of 346`.
Neither literal is registered in `FIGURE_REGISTRY.F16.tokens`, and the caller's failure reporter prints
only `figure.tokens`. A legitimate copy-edit therefore produces an error that names the wrong cause:

```
$ (data/SOURCES.md: "136 of 346" -> "136/346")
  FAIL  F16: ENUSC SAE VHDV household victimization rate (experimental, 2024)
         Required tokens: ["## INE ENUSC SAE", "VHDV"]
         Missing tokens:  []                      <-- nothing is missing
         Required tokens: ["ENUSC", "Victimizacion en Hogares", "SAE"]
         Missing tokens:  ["Victimizacion en Hogares"]   <-- permanently unsatisfiable, see RR-L1
figure-registry: FAILED — 1 orphaned figure(s): F16
Add the missing source entries to data/SOURCES.md …
EXIT=1
```
(`data/SOURCES.md` restored byte-identically; `git status --porcelain` clean.)

Breakage matrix (`checkF16` against the real file, each mutation applied alone):

```
a real                        = true
b heading only                = false
c heading + VHDV + 250 filler = false   (H1's target — closed, correct)
d real minus sha256 line      = false   (correct)
e "136 of 346" -> "136/346"   = false   <-- LANDMINE
f "136 of 346" -> "136 de 346"= false   <-- LANDMINE
g "sha256 of" -> "SHA-256 of" = false   <-- LANDMINE
h "136 of\n346" (re-wrap)     = false   <-- LANDMINE (no whitespace norm, unlike DOCS-01)
```

**Verdict on the brittleness question:** not acceptable as shipped. A registry guard may legitimately
pin a *fact* to a document, but it must (1) report the real missing literal and (2) tolerate whitespace,
which the rest of this same validator already does via `norm()`.

**Fix:** move the three substance literals into a named, reported list and normalize whitespace —
```js
const REQUIRED_BODY_SUBSTANCE = ['VHDV', 'sha256', '136 of 346'];
const nbody = body.replace(/\s+/g, ' ');
const missing = REQUIRED_BODY_SUBSTANCE.filter((t) => !nbody.includes(t));
if (missing.length) { console.error(`F16 body missing substance: ${missing.join(', ')}`); return false; }
```
and make `checkF16` return the missing list (or log it) so the caller stops printing `Missing tokens: []`.
Prefer a looser coverage matcher, e.g. `/136\s*(of|de|\/|out of)\s*346/`.

---

## MEDIUM

### RR-M1: `REAL_SECTION_BODY` is a hand-copied duplicate of `data/SOURCES.md` with no drift guard — vitest stays green through exactly the failure H1 introduced

**File:** `site/scripts/validate/figure-registry.test.ts:17-44` (header comment lines 5-9 makes the choice explicit)

Tests 4c/4d are correctly *encoded* (4c really builds `heading + 250 filler + VHDV`; 4d's
`expect(gutted).not.toContain('sha256')` sanity assertion is a good touch). But every fixture is a
verbatim copy of `SOURCES.md:324-349`, deliberately never reading the real file. H1 added two more
literals coupling `checkF16` to that document, so the divergence surface just tripled: rewrite
`136 of 346` in `data/SOURCES.md` and `npx vitest run` stays **57/57 green** while
`npm run validate` goes red — the fixture still contains the old text.

**Fix:** add one test that reads the real `data/SOURCES.md` (read-only, no mutation) and asserts
`checkF16(real) === true`, so the suite fails in the same breath as the validator. Or assert each
`REQUIRED_BODY_SUBSTANCE` literal is present in the real file.

---

## LOW

### RR-L1: F16 token group 2 is permanently unsatisfiable — the group is dead weight
**File:** `site/scripts/validate/figure-registry.mjs` (F16 `tokens[1]`)
Group 2 requires the unaccented `Victimizacion en Hogares`; `data/SOURCES.md:329` writes
`Victimización en Hogares`. `Missing tokens: ["Victimizacion en Hogares"]` appears in every F16 failure
report, always. Pre-existing, but H1 made F16's diagnostics load-bearing. Fix the literal (add the
accent) or delete the group.

### RR-L2: Inverted-phrase matching is accent-insensitive but case-**sensitive**
**File:** `site/scripts/validate/figure-registry.mjs:288-300`
`stripAccents(norm(...))` handles `más`/`mas` in both directions (proved below) but never lowercases.
`Lowest reported rate in Chile` at the start of a sentence, or `RANGO NACIONAL 1 = TASA MAS BAJA` in a
heading, slips through. Add `.toLowerCase()` on both sides.

### RR-L3: EN/ES asymmetry in the corrected footnote
**Files:** `site/src/pages/safest-cities-in-chile.astro:175` vs `site/src/pages/es/comunas-mas-seguras-chile.astro:162`
EN ends `— most reported crime, not safest`; ES ends `es decir, la comuna con más delitos reportados`
and drops the "not safest" clause. Both are correct and both clear `forbidden-language.mjs`; the ES
version is arguably the better one. Prior review's IN-05 recommended removing the bare superlative from
EN — doing so would also make the two symmetric. Cosmetic only.

---

## Verified Clean — with the mutation evidence

**CR-01 — correct, and the page is otherwise untouched.**
`git show a861c75` is a **one-line** diff. The ascending sort (`communeRates.sort((a,b)=>a.rate-b.rate)`,
line 148), the `TOP_N=15` slice, the "menor tasa reportada" list prose (lines 108-114) and the caption are
all unchanged and still correct. The new sentence matches `pipeline/cead/normalizer.py:135-140`
(`sorted(..., reverse=True)`, docstring "highest rate = rank 1") and says the same thing as its EN twin
at `safest-cities-in-chile.astro:174-175`.

**CR-02 — four false-negative probes, one at a time, each names its own file.**
```
M1 methodology.astro   'highest reported rate in Chile' -> 'lowest...'   EXIT=1, names src/pages/methodology.astro
M2 es/metodologia      'mayor tasa reportada en Chile'  -> 'menor...'    EXIT=1, names src/pages/es/metodologia.astro
M3 safest-cities       -> 'lowest reported rate among all non-low-population communes'  EXIT=1, names the file
M4 es/comunas (ACCENT) -> 'Rango nacional 1 = tasa más baja reportada'   EXIT=1, 4 phrase hits + positive-check FAIL
M5 es/comunas (PLAIN)  -> 'Rango nacional 1 = tasa mas baja reportada'   EXIT=1, identical output to M4
CLEAN_EXIT=0 after restore
```
Accent-stripping works **in both directions** (M4 and M5 produce byte-identical FAIL sets). The recursive
walk is real: 52 files across 13 directories including `es/`, `commune/`, `crime/`, `compare/`,
`es/comparar/`, `region/`. `readdirSync(..., {recursive:true})` + `e.parentPath ?? e.path` is correct on
Node v22.21.1 (and the `?? e.path` fallback covers Node 20.x). The guard reads **SOURCE**, not `dist/` —
which is why RR-H2 matters: a claim injected via a component or an i18n string is invisible to it.

**CR-03 — every sentence in the rewritten News section is true of the code.**
- "classified (crime family, severity) and a commune *name* is proposed" ✓ `classifier.py:26`
- "The LLM never emits a CUT code" ✓ `classifier.py:26`, and `scrape_news.py:312` is the only production
  call site
- "deterministic name→(cut, slug) dict lookup built from `data/cead/meta/index.json` — no network calls,
  no LLM" ✓ `resolver.py:1-10, 34-56`
- "closed 346-commune set" ✓ `len(json.load(index.json)) == 346`
- "returns `None` for any name outside the set (or an unresolved ambiguity), and the incident is dropped
  rather than guessed" ✓ `resolver.py:88-90, 105-116` **and** the caller actually drops:
  `scrape_news.py:313-321` (`rejection_stage = "commune_null" | "resolver_fail"` → `continue`).
Not "differently wrong" — it is exactly right, and now agrees with `news.astro:5-7`.
`git show 46fdc0e` touches only F15's **description** string; `F15.tokens` and every other registry field
are byte-identical. F15 still PASSes.

**H1 — the four required cases re-proved independently** (matrix above, rows a-d): real file `true`,
heading-only `false`, heading+VHDV+filler `false`, sha256-deleted `false`. Vitest 4c/4d genuinely encode
those cases rather than describing them. (Brittleness caveat: RR-H3/RR-M1.)

**H2 — the quoted label is the one the UI actually renders.**
Trace: `i18n.ts:367 news_window_latest: 'Latest data: {date}'` → `news.astro:165 windowLatestText` →
`news.astro:209 <span class="filter-opt-label">{windowLatestText}</span>`; ES path identical via
`i18n.ts:601` / `es/noticias.astro:163,~207`. Built HTML confirms:
```
dist/news/index.html          -> Latest data: Jul 30
dist/es/noticias/index.html   -> Últimos datos: 30 jul
```
This is not the previous mistake repeated. **Assertion 23b is still falsifiable** — copying the EN inner
text over the ES one in `dist/es/noticias/index.html` gives:
```
FAIL facets: assertion 23b — EN and ES facet-semantics notes are byte-identical after whitespace normalization …
EXIT_23b=1     (restored -> 0)
```

**M1 — the rule really applies, in both locales, and collides with nothing.**
```
dist/news/index.html:       class="facet-semantics-note" id="news-facet-semantics" data-astro-cid-5kj6t6lp>
                            facet-semantics-note[data-astro-cid-5kj6t6lp]{font-size:var(--text-label);color:var(--muted);max-width:65ch;margin:0 0 var(--md)}
dist/es/noticias/index.html:class="facet-semantics-note" id="news-facet-semantics" data-astro-cid-xsumocn5>
                            facet-semantics-note[data-astro-cid-xsumocn5]{…same…}
```
The scoped `data-astro-cid` on the rule matches the one on the element in each page (they differ per
page, as expected). Exactly 2 occurrences per file (rule + element) — no duplicate/overriding
`.facet-semantics-note` anywhere. All three custom properties resolve:
`--muted:#5d6c6d` (styles:16), `--md:16px` (:41), `--text-label:14px` (:51).

**Wave 1 not regressed.** All four corrected claims present
(`methodology.astro:337`, `es/metodologia.astro:350`, `safest-cities-in-chile.astro:175`,
`es/comunas-mas-seguras-chile.astro:162`); zero inverted phrases live; `sexuales` explainer present in
both locales (`methodology.astro:240,244` / `es/metodologia.astro:248,252`); all six anchors present
exactly once each in built HTML (EN `trend-formula`/`comparison-criteria`/`national-mean`/
`sexuales-family`; ES `trend-formula`/`comparison-criteria`/`media-nacional`/`familia-sexuales`).

**No validator was weakened.** `git diff 662e49b..HEAD` touches only `figure-registry.mjs`,
`figure-registry.lib.mjs`, `figure-registry.test.ts` under `scripts/validate/` — `coverage.mjs` and
`facets.mjs` are untouched by the fix cycle (their `d8db0ab..HEAD` deltas are Wave 1's additive
assertions F and 23/23b). Every fix-cycle change to `figure-registry` **adds** a requirement; none
removes one. `all.mjs` registers exactly **16** validators. `facets.mjs` still reports 24 assertions.

**Editorial compliance.** `forbidden-language.mjs` → PASS, 835 pages, 0 terms. The two sentences added
this cycle (`es/comunas-mas-seguras-chile.astro:162`, `data/SOURCES.md` Geolocation block) issue no
absolute safety verdict about any territory and sit inside CEAD-attributed notes.

**No fifth inverted claim.** Patterns run over all of `site/src/` (not just pages — `.astro`, `.ts`,
`.tsx`, `.json` all included), reported here so the coverage is auditable:
```
P1 (rank|rango|ranking|posici[oó]n)[^.\n]{0,40}\b1\b[^.\n]{0,60}(lowest|least|menor|m[aá]s baja|mas baja|safest|m[aá]s segura|seguro)   -> 0 hits
P2 (lowest|menor|m[aá]s baja|safest|m[aá]s segura)[^.\n]{0,60}(rank|rango|posici[oó]n)[^.\n]{0,20}\b1\b                                 -> 0 hits
P3 lowest reported rate|menor tasa reportada|tasa m[aá]s baja reportada                                                                 -> 6 hits, ALL legitimate:
     chile-crime-map.astro:89 (colour-scale legend), es/comunas-mas-seguras-chile.astro:108 (H2),
     es/index.astro:52 + index.astro:52 (code comments), index.astro:110 (H2), index.astro:140 (link text)
P4 #?1[^.\n]{0,15}(=|es|is|means|significa)[^.\n]{0,25}(safest|m[aá]s segura|lowest|menor)                                               -> 0 hits
```
All four rank-direction statements found (`comparisonProse.ts:198,209,287,299`) state rank 1 = highest —
correct — plus `proseEngine.ts:58`'s invariant comment.

---

## Restoration

Every mutation was reverted. Files touched and restored: `src/pages/methodology.astro`,
`src/pages/es/metodologia.astro`, `src/pages/safest-cities-in-chile.astro`,
`src/pages/es/comunas-mas-seguras-chile.astro`, `src/pages/rankings.astro`,
`dist/es/noticias/index.html`, and `data/SOURCES.md` (one in-place mutation + byte-identical restore for
the RR-H3 diagnostic evidence — no other write to `data/`). Two scratch probes
(`scripts/validate/_rrprobe.mjs`, `_rr2.mjs`) were deleted after use.

```
$ git status --porcelain
?? .planning/phases/31-docs-methodology-refresh/31-REVIEW.md
```
Clean apart from the expected dirty `31-REVIEW.md`. Post-restore re-runs: `figure-registry.mjs` exit 0,
`facets.mjs` exit 0, `forbidden-language.mjs` exit 0, vitest 57/57.

---

_Re-reviewed: 2026-08-03_
_Reviewer: Claude (gsd-code-reviewer, independent re-review)_
_Depth: deep (mutate)_
