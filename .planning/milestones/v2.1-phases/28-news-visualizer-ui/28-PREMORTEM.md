---
phase: 28-news-visualizer-ui
type: premortem
author: Opus premortem agent (unattended run, .planning/v2.1-AUTONOMOUS-DIRECTIVE.md)
created: 2026-07-30
premise: "Phase 28 has FAILED. It is now after the fact. Explain why."
---

# Phase 28 — PREMORTEM

> Every claim below marked **VERIFIED** was produced by running the real command against the
> real tree on 2026-07-30 and is quoted verbatim. Nothing here is inferred from prose.

---

## Verdict

**Phase 28 does NOT succeed as planned, and it fails for boring, mechanical reasons before it
ever fails for design reasons.** Three of the five `<automated>` verify blocks across the three
plans *cannot* exit 0 even against a perfectly-implemented Phase 28 — I ran them: Plan 28-01
Task 3's script resolves `site/src/config/i18n.ts` from a cwd that is already `site/` and dies
with `ENOENT`; Plan 28-02's `astro check 2>&1 | grep -c "error" | grep -qE "^[0-4]$"` counts **5**
lines at today's clean baseline, not ≤4; and Plan 28-03 Task 2's `grep -E "^[0-9]+ error"`
matches **zero** lines because `astro check`'s summary line is `- 4 errors`, not `4 error`. This
is Operating Lesson 9 ("a check that cannot pass") shipped three more times, in a plan set whose
own VALIDATION.md contains a section banning exactly this class. On top of that, the phase's
single load-bearing technical bet (F-27: a bare `<script>` `import`s a `.ts` module and the
plan proves it from `dist/`) rests on an evidence claim I verified to be **false** — the
`RankingTableEnhancer` chunk that F-27 and 28-PATTERNS.md cite as proof contains no `import`
at all — and assertion 17 as specified is doubly unable to pass, because Astro's build
**mangles all local identifiers** (so grepping for `parseFilterParams`/`WINDOW_7D_WIDTH_DAYS`
finds nothing) and **inlines** any page script chunk with zero imports under 4096 bytes (so the
`<script src="/_astro/...">` the assertion looks for may never be emitted). Underneath the
tooling problems sits one genuine correctness defect that would ship a wrong fact to users (the
anchor-date label formats a UTC instant with a local-timezone formatter, so Chilean readers see
"Jul 26" while the data anchor is Jul 27), one binding-document contradiction (28-UI-SPEC.md
mandates serializing `facetKeys` and copy-pasting `norm()`; the plans do neither), and a
time-bomb: `freshness.mjs` reads **2.9 days** old right now against a `MAX_AGE_DAYS = 3` limit,
so the "all 16 validators green" phase-close gate will be red within hours and no plan mentions
the F-19 exclusion branch that makes it admissible. With the amendments in the last section the
phase is very achievable — the design is sound and the F-28 semantics are provably consistent.
Without them, Phase 28 closes on laundered or failing gates.

---

## Failure modes

### FM-1 — CRITICAL — Plan 28-03's phase-close gate can never exit 0: `astro check` never prints a line starting with a digit

**Evidence.** Plan 28-03 Task 2 `<automated>`:

```
cd site && npm run build && npm test && npm run validate && npm run check 2>&1 | grep -E "^[0-9]+ error" | grep -qE "^4 error"
```

The real output's summary block is:

```
Result (128 files):
- 4 errors
- 0 warnings
- 38 hints
```

**Verified-by.** `cd site && npx astro check 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -cE "^[0-9]+ error"` → **`0`**.
With zero matching lines, the first `grep` exits 1, the `&&` chain's last command fails, and the
verify block reports FAILURE on a perfect implementation. It is unfixable by any amount of correct
Phase 28 code.

Two compounding facts: the summary says `errors` (plural), and every line is prefixed `- `.
Also note the `Result` line reports `0 warnings` while the body prints 38 `warning ts(6133)`
lines — do not write an assertion that reasons about warnings from the body text.

**Severity.** CRITICAL — this is the phase's terminal gate. An executor hitting it will either
report the phase blocked, or "fix" it by laundering the exit code, which is the exact defect
Operating Lesson 8 says was found four separate times in Phase 27.

**Amendment.** See Amendment 1.

---

### FM-2 — CRITICAL — Plan 28-02's verify block can never exit 0: `grep -c "error"` is 5 at the clean baseline

**Evidence.** Both tasks of Plan 28-02 use:

```
cd site && npx astro check 2>&1 | grep -c "error" | grep -qE "^[0-4]$"
```

**Verified-by.** `npx astro check 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -c "error"` → **`5`**.
The 5 = the 4 per-error diagnostic lines **plus** the `- 4 errors` summary line. `5` does not
match `^[0-4]$`, so the block exits 1 today, before Phase 28 writes a single character. It also
has no discriminating power at all: one new error would give 6, two would give 7 — the check
would be equally red for 0 new errors and for 3.

**Severity.** CRITICAL — it gates both tasks of the plan that does all of the user-visible work.

**Amendment.** See Amendment 1 (single shared replacement command).

---

### FM-3 — CRITICAL — Plan 28-01 Task 3's verify block dies with ENOENT (wrong cwd) and launders its own exit code

**Evidence.** The verify block begins `cd site && node -e "... require('./src/config/i18n.ts') ..." 2>&1 | grep -q "Cannot use import" || true; node -e "const src=fs.readFileSync('site/src/config/i18n.ts', ...)"`.

**Verified-by.** With cwd `site/`:

```
Error: ENOENT: no such file or directory, open
'C:\...\Is Chile Safe\site\site\src\config\i18n.ts'
EXIT=1
```

Three separate defects in one block: (a) the path is `site/src/...` while cwd is already `site/`
(doubled segment); (b) the first `node -e … | grep -q … || true` is dead noise whose `|| true`
is precisely the exit-code laundering 28-VALIDATION.md § "Exit-code hygiene" declares grounds
for rejecting a plan at review — it is in the plan anyway; (c) the block relies on
`src.split('ES_STRINGS')[1]` while `ES_STRINGS` occurs **4 times** in `i18n.ts` (declaration at
:411 plus references at :648-650) — the split is only accidentally safe because the extra
occurrences follow the declaration.

**Severity.** CRITICAL for the plan's own gate; the underlying key-parity intent is fine and is
permanently covered by Plan 28-03 assertion 13 anyway.

**Amendment.** See Amendment 2.

---

### FM-4 — CRITICAL — Assertion 17 (the F-27 bundling proof) cannot pass as specified: identifiers are minified away, and the chunk may be inlined rather than emitted

This is the phase's highest-risk item by the plan's own admission, and it has **two independent**
reasons to fail on a correct implementation.

**(a) The identifiers it greps for do not survive the build.** Plan 28-03 Task 2 says to assert a
chunk "include[s] a distinctive identifier from `newsFilterLogic.ts` (e.g. the literal string
`WINDOW_7D_WIDTH_DAYS` or `parseFilterParams`)". Astro's production build runs esbuild
minification, which mangles every module-scope and local name.

**Verified-by.** The existing bundled page script, `dist/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js`, begins:

```js
(function(){const q=document.getElementById("rte-strings");if(!q)return;
const N=JSON.parse(q.textContent||"{}"),J=q.dataset.locale||"en";
function P(a,c,i){const E=i==="es"?"es-CL":"en-US"; ...
```

Every identifier is a single letter. By contrast, **string literals and property names survive** —
in `dist/communes/index.html` the inlined script reads `const a=e=>e.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase()`, and `grep` for `NFD` / `normalize` / `toLowerCase` all return true.
So the marker must be a **string literal**, never an identifier.

**(b) The `<script type="module" src="/_astro/…">` it cross-references may never be emitted.**
Astro inlines a page script instead of emitting a chunk file under an exactly-known condition.

**Verified-by.** `node_modules/astro/dist/core/build/plugins/plugin-scripts.js:24`:

```js
if (output.type === "chunk" && output.facadeModuleId
    && internals.discoveredScripts.has(output.facadeModuleId)
    && !importedIds.has(output.fileName)
    && output.imports.length === 0 && output.dynamicImports.length === 0
    && shouldInlineAsset(output.code, output.fileName, assetInlineLimit)) { /* inline */ }
```

and `plugins/util.js:15`: `return Buffer.byteLength(assetContent) < Number(assetsInlineLimit);`
`astro.config.mjs` sets no `build.assetsInlineLimit`, so the Vite default **4096 bytes** applies.

This is not hypothetical — it is already the observed behavior of the closest analog:

| dist page | script shape |
|---|---|
| `dist/communes/index.html` | `<script type="module">` **inline**, 1883 bytes (page-unique script, 0 imports) |
| `dist/commune/algarrobo/index.html` | `<script type="module" src="/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js">` (shared across 346 pages) |

Whether news.astro's script ends up inline or as a file depends on whether Rollup hoists
`newsFilterLogic` into a shared chunk (giving the page entry `imports.length > 0` → never inlined
→ `src=` emitted) or duplicates it into each entry (0 imports → inlined if the minified result is
under 4096 bytes). Both outcomes are plausible and the deciding factor is the final minified byte
count of code Phase 28 has not written yet. **An assertion whose pass/fail depends on crossing a
4096-byte threshold is not a proof of anything.**

**Severity.** CRITICAL — it is the plan's own designated highest-risk item and, per F-27, an
executor that cannot make it pass is instructed to STOP and report, which would halt the phase on
a tooling artifact rather than a real problem.

**Amendment.** See Amendment 3.

---

### FM-5 — HIGH — F-27's cited proof does not prove what it is cited for; the load-bearing assumption is genuinely unproven in this repo

**Evidence.** STATE.md F-27's rationale: *"Astro processes bare (non-`is:inline`) `<script>` tags
through Vite and bundles their imports, and `dist/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.*.js` proves this repo already ships a bundled page script."*
28-PATTERNS.md:131 repeats it, and Plan 28-03's `read_first` calls it "the existing
proof-of-concept this codebase already ships".

**Verified-by.** `RankingTableEnhancer.astro`'s `<script>` block (line 58 onward) contains **zero
`import` statements** — grep for `import` inside the block returns nothing. Its sole `import`
(`{ EN_STRINGS, ES_STRINGS } from '../config/i18n.ts'`, line 38) is in the **frontmatter**, i.e.
server-side. The emitted chunk is a self-contained IIFE with no `import`/`export`. Sweeping every
bare `<script>` in `src/pages`, `src/components`, `src/layouts` (`commune/[slug].astro:434`,
`communes/index.astro:170`, `es/comuna/[slug].astro:437`, `es/comunas/index.astro:170`,
`CookieConsent.astro:41`, `RankingTableEnhancer.astro:58`) finds **no client-side `import`
anywhere in the repo**. The chunk therefore proves Astro *hoists and hashes* a bare script — not
that it *resolves an ES import* from one.

Compounding: 28-RESEARCH.md:326, this phase's own research, states the opposite of F-27 —
*"Astro does NOT provide a supported mechanism for an inline `<script>` (no directive) to `import`
from a `.ts` file without turning it into a bundled client entry point"* — and recommended
duplication. F-27 overrode it citing evidence that does not hold.

My assessment: F-27's *conclusion* is very likely correct (a bare Astro `<script>` is a Vite
client entry and Vite resolves its static imports; that is documented Astro behavior), but the
phase is executing an architectural pattern with **zero precedent in this codebase** on the
strength of a misattributed proof. That is exactly the situation the premortem exists to name.

**Severity.** HIGH — not because the bet is likely wrong, but because the fallback (duplication)
is a Plan-28-02 rewrite discovered at Wave 3, and Plan 28-03 forbids the executor from taking
that decision itself.

**Amendment.** See Amendment 4 (a 60-second Wave-0 spike that settles it before 28-02 is written).

---

### FM-6 — HIGH — The anchor-date label is off by one day for every reader west of UTC, including all of Chile

**Evidence.** Plan 28-02 Task 1, verbatim:

```js
t.news_window_latest.replace('{date}', anchorDate
  ? new Date(anchorDate + 'T00:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  : '—')
```

`new Date('2026-07-27T00:00:00Z')` is a correct UTC instant, but `toLocaleDateString` **without a
`timeZone` option formats in the viewer's local zone**. In `America/Santiago` (UTC−4) that instant
is 2026-07-26 20:00, so the label renders **"Jul 26"** while `#news-facets.anchorDate` says
`2026-07-27` and every `.news-date-outlet` on the newest cards reads `2026-07-27`. Task 2 repeats
the identical construction with `'es-CL'`.

**Verified-by.** `TZ=America/Santiago node -e "console.log(new Date('2026-07-27T00:00:00Z').toLocaleDateString('es-CL',{month:'short',day:'numeric'}))"` → `26 jul`. Real data confirms the
exposure: `current.json` max date is `2026-07-27` (1215 incidents), so the anchor is a real,
currently-rendered value.

This is a **visible factual error about crime-data recency on a safety-information site**, and it
is precisely the class STATE.md's "Four things Phase 28 must handle" item #1 exists to prevent
("Phase 28 must label windows relative to the data"). Note also that no validator catches it:
`facets.mjs` assertion 9's TZ-sensitive-pattern scan (`/toLocaleDateString/`, `/getMonth\(/`,
`/new Date\(\d/`) is hardcoded to `newsFacets.ts` only and never reads the `.astro` pages.

**Severity.** HIGH.

**Amendment.** See Amendment 5.

---

### HIGH — FM-7 — The `{n}` and `{date}` placeholder tokens ship raw in the static HTML, so the JS-disabled and pre-hydration view reads literally "{n} incidents shown"

**Evidence.** 28-UI-SPEC.md's Element Structure renders the result count as
`<span id="news-result-count" role="status" aria-live="polite">{t.news_result_count}</span>` and
the window radios as `{t.news_window_7d}` / `{t.news_window_30d}`. The i18n values are
`"{n} incidents shown"`, `"Last 7 days ({n})"`, `"Last 30 days ({n})"`, `"Latest data: {date}"`.
Plan 28-02 assigns `.replace()` substitution to the **client script** ("updates
`#news-result-count`'s `textContent` from `t.news_result_count` with `{n}` replaced") and says
nothing about substituting server-side.

**Consequence.** The pre-rendered HTML — the only thing Google and a JS-disabled reader ever see —
contains `{n} incidents shown`, `Last 7 days ({n})`, `Last 30 days ({n})`, `Latest data: {date}`.
That is broken-looking copy in the indexed HTML of a page whose entire premise (NEWSUI-02) is
that the static render is complete and correct. 28-VALIDATION.md's manual row even says to
confirm "no filter control is broken-looking" with JS off — this fails that check by construction.

**Verified-by.** The server-side values are available at build time and there is no excuse for
deferring: `facets.byWindow.sevenDay.length` = 297, `.thirtyDay.length` = 1215, `.today.length` = 11,
`incidents.length` = 1215 (all from the live `node scripts/validate/facets.mjs` PASS line:
`window(today=11,7d=297,30d=1215)`).

**Severity.** HIGH.

**Amendment.** See Amendment 6.

---

### HIGH — FM-8 — Plan 28-03 covers only 6 of the 10 Wave-0 validator rows 28-VALIDATION.md marks ❌, so the phase cannot honor its own sign-off checklist

**Evidence.** 28-VALIDATION.md's sign-off requires "Wave 0 covers every ❌ above". Mapping its ❌
validator rows onto Plan 28-03's assertions 11-17:

| VALIDATION.md ❌ row | Covered by |
|---|---|
| NEWSUI-01 — filter controls + counts rendered on BOTH pages | **nothing** |
| NEWSUI-02 — card count == incident count | 12 ✅ |
| NEWSUI-02 — no island / no hydration | 15 ✅ |
| NEWSUI-03 — `#news-comuna-q` present in both dist pages | **nothing** |
| NEWSUI-04 — empty-state node exists, `hidden`, not a heading | 14 ✅ |
| NEWSUI-04 — no new indexable URL; canonical unchanged | **nothing** |
| NEWSUI-05 — no cluster markup | 16 ✅ |
| NEWSUI-06 — no `innerHTML` with data-derived strings (pages + newsFilterLogic.ts) | **nothing** |
| NEWSUI-07 — EN/ES key parity | 13 ✅ |
| (falsifiability table) `anchorDate` correctness | 11 ✅ |
| (F-27) bundling proof | 17 ✅ |

Four required assertions are simply absent. The `innerHTML` one is the most consequential: it is
the only automated guard on NEWSUI-06's security property, in a phase whose threat register
(T-28-07) claims mitigation by discipline alone, on a page whose `family`/`title`/`outlet` values
come from an LLM classifier over scraped press headlines.

**Severity.** HIGH — a gsd-verifier reading VALIDATION.md against the plans will (correctly) fail
the phase for incomplete Wave 0.

**Amendment.** See Amendment 7.

---

### HIGH — FM-9 — Assertion 13's i18n-parity regex is blind to `news_window_7d` and `news_window_30d` — 2 of the 15 keys are silently uncovered

**Evidence.** Plan 28-03 Task 1: *"assert every key matching `/^\s*news_[a-z_]+:/m` in one block
also appears in the other."* `[a-z_]+` excludes digits.

**Verified-by.**
```
node -e "for(const k of ['news_window_7d','news_window_30d','news_filter_heading'])
  console.log(k, /^\s*news_[a-z_]+:/m.test('  '+k+': \"x\",'));"
news_window_7d   false
news_window_30d  false
news_filter_heading true
```
Deleting `news_window_7d` from `ES_STRINGS` would leave assertion 13 **green**. Second defect in
the same sentence: the `m` flag without `g` means a `String.match()` implementation returns a
single match, so the assertion would check exactly one key.

This is Operating Lesson 9 verbatim — a check that reads as coverage and cannot fire for the keys
most likely to be fumbled (the two with digits and the two with `{n}` tokens).

**Severity.** HIGH.

**Amendment.** See Amendment 8.

---

### HIGH — FM-10 — `freshness.mjs` will be RED for the whole of Phase 28, and no plan carries the F-19 branch

**Evidence.** Plan 28-03's `<done>` and success criteria require `npm run validate` (all 16
validators) to exit 0, with no mention of F-19.

**Verified-by.**
```
node scripts/validate/freshness.mjs
PASS freshness: data/incidents/current.json is 2.9 days old (generated: 2026-07-27T14:25:05.303451Z)
```
with `const MAX_AGE_DAYS = 3;` (freshness.mjs:27). At `date -u` = 2026-07-30 12:54 UTC the file is
2.94 days old; it crosses 3.0 days at ~14:25 UTC **today**. `data/` is read-only, `git pull` is a
BANNED remediation, and the local checkout is behind origin.

The F-19 exclusion **is** admissible — I checked condition (b):
`git log -1 --format=%ci origin/master -- data/incidents/current.json` → `2026-07-30 02:02:51 +0000`
(the news cron is alive; this checkout is merely unpulled). But an executor following Plan 28-03
literally sees a red validator on a gate whose success criterion says "exits 0", with no
instruction, and the banned remediations (raise `MAX_AGE_DAYS`, skip the validator, touch `data/`)
are all one edit away and each is a declared phase failure.

**Severity.** HIGH — near-certain to fire, and the wrong response is cheap and tempting.

**Amendment.** See Amendment 9.

---

### HIGH — FM-11 — 28-UI-SPEC.md, a binding contract, mandates two things the plans deliberately do not do

**Evidence.** 28-PATTERNS.md:7 names 28-UI-SPEC.md a "binding source of record" for the
"markup/tokens/i18n keys/query-param contract/hide-show mechanism". Two of its mandates are
contradicted by the plans:

1. **UI-SPEC:167** — *"Phase 28 **must** add `facetKeys` to the `facetsProjection` object in both
   `news.astro`/`es/noticias.astro`"* and recompute cross-filtered counts from it. The plans add
   only `anchorDate` and read counts from per-card `data-*` attributes instead. Plan 28-02's
   threat register even asserts "no new escaping call site was introduced".
2. **UI-SPEC:178** — *"Same `norm()` function, **copy-pasted** (do not import cross-page …)"*.
   F-27 and Plan 28-01 do the exact opposite.

For (2) the resolution is clear: F-27 is a later, explicitly-recorded Fable decision and
28-PATTERNS.md:62 already documents the override. For (1) **the plans are right and the UI-SPEC is
wrong**, and this is worth stating because the numbers are stark: serializing `facetKeys` means
1,215 objects × `{id, family, regionId, yearMonth, window}` into the inline JSON of **both**
pages — order 100 KB of duplicated payload per page, against a requirement (NEWSUI-06) that the
page add "no measurable … regression". The `data-*` approach reuses markup already emitted.

But nothing in the plan set records the override, so a gsd-verifier or code reviewer checking the
implementation against the binding UI-SPEC will flag both as unimplemented mandates.

**Severity.** HIGH (governance/verification, not correctness).

**Amendment.** See Amendment 10.

---

### MEDIUM — FM-12 — Plan 28-02's region-label instruction is unsatisfiable as written, and its ES form will drift

**Evidence.** Plan 28-02 Task 1: *"one checkbox per `facets.byRegion` entry (label
`"{regionName} ({count})"` — region name from `loadIndex()`/an existing region-name lookup already
used elsewhere on this page or `../lib/data`)"*.

**Verified-by.** `CommuneMeta` (`src/lib/data.ts:29-36`) is `{cut, name, slug, region_id,
population, low_population}` — **no region name**. `news.astro` has no region-name lookup of any
kind. The only `region_id → name` path is `loadRegion(regionId)` (`data.ts:171`), which needs the
`regionFileId()` normalization and 16 JSON reads. Separately, every ES page renders region names
through `regionNameEs()` (`i18n.ts:666`, "Región de X" / "Región del Maule" / "Región
Metropolitana") — Plan 28-02 Task 2's "three differences only" list does **not** include it, so
`/es/noticias/` would label a checkbox bare `Metropolitana` while the rest of the ES site says
`Región Metropolitana`.

**Severity.** MEDIUM — the executor will improvise, and improvised per-locale label derivation
is exactly the EN/ES drift RR-1 was about.

**Amendment.** See Amendment 11.

---

### MEDIUM — FM-13 — Assertion 12's card-count regex is order-dependent on attributes Plan 28-02 is about to add

**Evidence.** Plan 28-03 prescribes `/<article class="news-card"/g`. Plan 28-02 adds five `data-*`
attributes to that same `<article>`.

**Verified-by.** Today both dist pages give exactly `1215` for `/<article class="news-card"/g` and
`1216` for the bare substring `news-card` (the extra is the inlined `.news-card` CSS rule — which
confirms VALIDATION.md's warning is real). But the count survives only if the executor keeps
`class` as the **first** attribute. `<article data-family="robos" class="news-card">` — a
completely reasonable edit — silently returns 0 and the assertion reports a card/incident mismatch
that does not exist.

**Severity.** MEDIUM — a false RED on correct code, which costs a debugging cycle and tempts a
weakened assertion.

**Amendment.** See Amendment 12.

---

### MEDIUM — FM-14 — Three stale factual claims will send the executor hunting for work that does not exist

Each verified against the tree:

| Claim | Where | Reality (VERIFIED) |
|---|---|---|
| "the pre-existing 4-error baseline **in `scripts/validate/*.mjs`**" | 28-02 `<done>`, 28-03 `<done>` + success criteria, 28-VALIDATION.md:62 | All 4 errors are in **`src/components/ComparatorPairsLinks.astro:28`** (`ts(7031)` implicit-any on `cutA`/`cutB`/`nameA`/`nameB`). `scripts/validate/*.mjs` produces only `ts(6133)` *hints*. Consequence: a real new error introduced in a validator would be waved through as "baseline". |
| "`newsFacets.test.ts` … 20 tests" / "the FULL existing 20-test file" / "20(+)-test suite" | 28-VALIDATION.md:21, 28-01 Task 2 behavior + `<done>` | `newsFacets.test.ts` has **13** `it()` blocks. `npm test` reports `Test Files 2 passed (2) / Tests 20 passed (20)` — the other 7 are in `src/lib/formatNumber.test.ts`. An executor told to make a 20-test file pass will look for 7 missing tests. |
| "`facets.mjs` … proves … every falsifiable claim"; "10 assertions" read as coverage | 28-03 objective | F-24 (STATE.md:203) already recorded that **only 7 of the 10 are load-bearing**: assertion 1's count-sum and assertion 8's three containments are true by construction for every input (20,000-input fuzz), and assertion 4 is unreachable behind assertion 3. Adding 7 more assertions to a validator whose count already overstates coverage by 30% is worth stating out loud. |

**Severity.** MEDIUM.

**Amendment.** See Amendment 13.

---

### MEDIUM — FM-15 — "ES page is byte-identical to EN, only copy differs" is false; the two pages have real structural drift today

**Evidence.** Plan 28-02 Task 2 `read_first`: *"confirmed byte-identical structure to news.astro
pre-Task-1, only copy differs"*, and its `<action>` lists "three differences only".

**Verified-by.** `diff src/pages/news.astro src/pages/es/noticias.astro` shows structural, not just
lexical, divergence:
- the `formattedDate` block sits at **lines 49-63** in the ES file but **83-94** in the EN file
  (different frontmatter ordering);
- the `<style>` block's rule order differs — `.freshness` and `.empty-state` appear at ES:217-227
  but at EN:292-301;
- the EN file has a `slugToCommune` explanatory comment the ES file lacks.

An executor instructed to "mirror Task 1's changes with three differences only" and finding the
insertion anchors in different places will improvise placement. That is how RR-1's single-locale
blind spot recurs — this time as ordering drift rather than a missing check.

**Severity.** MEDIUM.

**Amendment.** See Amendment 14.

---

### MEDIUM — FM-16 — `?region=` acquires a second, incompatible site-wide meaning right before Phases 29/30 rework the map shell

**Evidence.** 28-UI-SPEC.md's query-param table claims `region` as *comma-separated multi-value
region ids* on the news pages. The map already ships a `?cut=` deep link and carries a known
**unclosed `?region=` gap** (MEMORY: "carry-over: home-title cannibalization, 8 astro-check
errors, `?region=` in MapIsland"). Phase 30 is the map control-shell rework, flagged
regression-risk with `IncidentPinLayer.ts` protected.

**Consequence.** After Phase 28 the codebase has two `?region=` contracts — multi-value CSV on
`/news/`, single-value focus on `/map/` — with no recorded decision distinguishing them. Phase 30
closing the map's `?region=` gap will either (a) copy the news CSV parser and give the map
nonsensical multi-region focus, or (b) implement single-value and leave two silently divergent
readers of the same param name. Nothing in Phase 28 documents which.

**Severity.** MEDIUM — no Phase 28 defect, a Phase 30 trap.

**Amendment.** ACCEPTANCE + one documentation line. See Amendment 15.

---

### LOW — FM-17 — F-28's "reduces to F-20's marginals" claim is TRUE; the residual risk is one specific naive implementation

I attempted to construct the divergence the objective asked about and **could not** — F-28 is
consistent. Recorded here so the executor does not go looking for a problem that isn't there:

- With `active = {family:[], region:[], window:'', q:''}`, `cardMatchesFilters` returns true for
  every card in every pass, so `computeFacetCounts(..., 'family', keys)[k]` = count of cards with
  `family === k` = `byFamily[k].count`; same for region; and for `window` the per-key predicate is
  `matchesWindow(card.date, anchorDate, key)`, which reproduces `newsFacets.ts:193-200` exactly.
- I verified the boundary math ports cleanly: `newsFacets.ts:190-191` uses
  `lowerBoundDate(anchorMs, 6)` and `lowerBoundDate(anchorMs, 29)`; Plan 28-01 specifies
  `WINDOW_7D_WIDTH_DAYS - 1` = 6 and `WINDOW_30D_WIDTH_DAYS - 1` = 29. `today` is
  `date === newestDate` in both. Boundaries are `>=` lower bound with no upper bound in both.
  Windows are **cumulative** (today ⊂ 7d ⊂ 30d), matching `byWindow`'s live numbers
  `today=11, 7d=297, 30d=1215`.
- Client-side there is no wall-clock exposure at all, because `anchorDate` comes from the
  build-time `#news-facets` payload. This is the right design.

Two live-data quirks worth a sentence in the code comment, neither a defect:
- `30d` currently equals **1215 = every incident** (`current.json` spans 2026-06-29 → 2026-07-27,
  a 28-day window), so the "Last 30 days (1215)" and "All dates" options are indistinguishable
  today. Cosmetic; do not "fix" it by changing the window math.
- `news_window_latest` ("Latest data: {date}") is the only window option the Copywriting Contract
  gives no `{n}` slot, so the `today` bucket ships without the per-option count NEWSUI-01 asks
  for — while `computeFacetCounts` computes it. Minor spec inconsistency.

**Severity.** LOW.

**Amendment.** ACCEPTANCE — see Accepted risks.

---

### LOW — FM-18 — F-27's "single canonical `norm()` in this codebase" will be false the moment it is written

**Evidence.** Plan 28-01 Task 1 `<action>`: *"`norm()` is the single canonical definition in this
codebase per F-27"*. But `communes/index.astro` (and its ES twin `es/comunas/index.astro`) keep
their own inline copy — Phase 28 touches neither.

**Verified-by.** `dist/communes/index.html`'s inlined module still contains
`const a=e=>e.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase()`. After Phase 28 there will be
**three** `norm()` bodies (newsFilterLogic.ts + 2 directory pages), not one.

**Severity.** LOW — a false comment that misleads a future reader into thinking a refactor
happened. Out of scope to fix properly.

**Amendment.** See Amendment 16 (comment wording only).

---

### LOW — FM-19 — NEWSUI-02 is structurally safe; I found no path by which filtering hides content from Google or a JS-disabled reader

Recorded as a *cleared* concern, with the one thing to keep watching:

- No card starts life `hidden`: hiding happens only in `applyFilters()`, which runs client-side.
- No CSS hides cards pre-JS: the `<style>` blocks contain no `.news-card { display:none }`.
- Nothing is server-side-filtered from a query param — Astro pre-renders and `location.search` is
  read only in the client script.
- `<details open>` ships `open` server-side and JS never removes it (UI-SPEC:213), so the
  disclosure resolves during HTML parse — no CLS by construction.
- `dist/news/index.html` and `dist/es/noticias/index.html` each contain **1215**
  `<article class="news-card">` = `incidents.length` **1215** (VERIFIED). Assertion 12 pins this.
- `#news-empty` ships `hidden` and is explicitly not a heading tag (UI-SPEC:196), so no thin-content
  signal.

**The one live hazard:** `applyFilters()` is called "once synchronously on load" and narrows from
`?`-params. If a URL like `/news/?family=robos` were ever *linked* (a share, a sitemap slip, an
internal link) Google could render it and see a narrowed list. This is fine as long as (a) the
canonical stays the bare path and (b) no internal link ever carries a filter param — which is
exactly why Plan 28-02's "Do not add a 'view all {family}' link anywhere" instruction matters and
should not be dropped. Keep it.

**Severity.** LOW.

---

## Plan amendments required

**Amendment 1 — Replace the `astro check` baseline gate in BOTH Plan 28-02 verify blocks and Plan 28-03 Task 2 (fixes FM-1, FM-2, FM-14 row 1).**

In `28-02-PLAN.md`, Task 1 `<automated>` (line 101) and Task 2 `<automated>` (line 119), replace
the existing line with:

```
cd site && npx astro check > .astro-check.log 2>&1; node -e "const s=require('fs').readFileSync('.astro-check.log','utf8').replace(/\u001b\[[0-9;]*m/g,''); const m=s.match(/^- (\d+) errors?$/m); if(!m) { console.error('FAIL: astro check summary line not found'); process.exit(1); } const n=Number(m[1]); if(n!==4){ console.error('FAIL: astro check reports '+n+' errors, baseline is 4'); process.exit(1); } console.log('astro check at 4-error baseline');"
```

In `28-03-PLAN.md`, Task 2 `<automated>` (line 99), replace with:

```
cd site && npm run build && npm test && npm run validate && npx astro check > .astro-check.log 2>&1; node -e "const s=require('fs').readFileSync('.astro-check.log','utf8').replace(/\u001b\[[0-9;]*m/g,''); const e=s.match(/^- (\d+) errors?$/m), w=s.match(/^- (\d+) warnings?$/m); if(!e||!w){ console.error('FAIL: astro check summary not found'); process.exit(1); } if(Number(e[1])!==4||Number(w[1])!==0){ console.error('FAIL: astro check '+e[1]+' errors / '+w[1]+' warnings, baseline 4/0'); process.exit(1); } console.log('astro check 4/0 baseline confirmed');"
```

Note the `;` before `node -e` is deliberate and is **not** exit-code laundering: `astro check`
exits non-zero whenever errors exist, so it exits 1 at the healthy 4-error baseline; the `node`
step is the actual assertion and its exit code is the block's. Add `site/.astro-check.log` to
`.gitignore` in the same commit.

Also correct the baseline attribution everywhere it appears (28-02 Task 1/2 `<done>`, 28-03
`<done>` + success criteria, 28-VALIDATION.md:62): replace
"pre-existing, all in `scripts/validate/*.mjs`" with
"pre-existing, all 4 in `src/components/ComparatorPairsLinks.astro:28` (ts(7031) implicit-any on
`cutA`/`cutB`/`nameA`/`nameB`) — a new error anywhere else is NOT baseline".

---

**Amendment 2 — Replace Plan 28-01 Task 3's verify block (fixes FM-3).**

`28-01-PLAN.md` line 221, replace the entire `<automated>` content with:

```
cd site && node -e "const fs=require('fs'); const src=fs.readFileSync('src/config/i18n.ts','utf-8'); const keys=['news_filter_heading','news_filter_window_label','news_window_latest','news_window_7d','news_window_30d','news_window_all','news_filter_region_label','news_filter_family_label','news_search_comuna_label','news_search_comuna_placeholder','news_result_count','news_clear_filters','news_empty_heading','news_empty_body','news_cluster_source_count']; const iEn=src.indexOf('export const EN_STRINGS'), iEs=src.indexOf('export const ES_STRINGS'); if(iEn<0||iEs<0||iEs<iEn) throw new Error('could not locate EN_STRINGS/ES_STRINGS declarations'); const iface=src.slice(0,iEn), en=src.slice(iEn,iEs), es=src.slice(iEs); const missing=[]; for(const k of keys){ if(!new RegExp('\\\\b'+k+'\\\\s*:').test(iface)) missing.push('IFACE:'+k); if(!new RegExp('\\\\b'+k+'\\\\s*:').test(en)) missing.push('EN:'+k); if(!new RegExp('\\\\b'+k+'\\\\s*:').test(es)) missing.push('ES:'+k); } if(missing.length){ console.error('MISSING '+missing.join(',')); process.exit(1);} console.log('all 15 keys present in interface + EN + ES');"
```

Changes: path is `src/config/i18n.ts` (cwd is already `site/`); the dead `|| true` sub-command is
deleted; slicing anchors on `export const EN_STRINGS` / `export const ES_STRINGS` (unique, verified
at :207/:411) instead of the bare names that occur 4× each; the `I18nStrings` interface block is
checked too.

---

**Amendment 3 — Rewrite Plan 28-03 assertion 17 to search for a string literal in *either* emission shape (fixes FM-4).**

Add to `28-01-PLAN.md`'s Interfaces block and Task 1 `<action>`:

```typescript
export const FILTER_LOGIC_MARKER = 'newsFilterLogic/v1';
// A string literal (NOT an identifier). Astro's esbuild minification mangles every
// local/module identifier — VERIFIED against dist/_astro/RankingTableEnhancer.*.js,
// where every name is a single letter — but preserves string literals verbatim
// (VERIFIED: "NFD" survives in dist/communes/index.html). facets.mjs assertion 17
// greps the shipped JS for this literal to prove the import was really bundled.
// It MUST be referenced at runtime by both pages' scripts or tree-shaking drops it.
```

In `28-02-PLAN.md` Task 1 and Task 2 `<action>`, add: *"import `FILTER_LOGIC_MARKER` alongside the
predicates and, inside `applyFilters()`'s first run, execute
`document.getElementById('news-filters')?.setAttribute('data-filter-logic', FILTER_LOGIC_MARKER)`
— a real runtime reference so the marker survives tree-shaking, and a browser-inspectable signal
that the module loaded."*

In `28-03-PLAN.md` Task 2 `<action>`, replace the assertion-17 specification with:

> Add assertion 17. For each of the two dist news pages, collect **every** shipped module script
> the page owns, in both emission shapes Astro can produce:
> (a) the bodies of all inline `<script type="module">…</script>` blocks in the page HTML, and
> (b) the contents of every `dist/_astro/*.js` file referenced by a `<script type="module" src="/_astro/…">`
> tag in that page, **plus one level of that chunk's own static `import`/`from "./…js"` specifiers**
> (Rollup may hoist `newsFilterLogic` into a shared chunk).
> Assert that the concatenation of (a)+(b) for that page contains the literal string
> `newsFilterLogic/v1`. Fail with the locale name and the list of script sources searched.
>
> **Both shapes are legitimate and the assertion MUST accept either.** VERIFIED from
> `node_modules/astro/dist/core/build/plugins/plugin-scripts.js:24` + `plugins/util.js:15`: Astro
> inlines a page script iff its chunk has `imports.length === 0 && dynamicImports.length === 0`
> **and** `Buffer.byteLength(code) < assetsInlineLimit` (Vite default **4096**; `astro.config.mjs`
> sets no override). Observed live in this repo: `dist/communes/index.html` ships an **inline**
> 1883-byte `<script type="module">`, while `RankingTableEnhancer`'s chunk (shared by 346 pages)
> ships as `<script type="module" src="/_astro/…">`. Whether Phase 28's script crosses 4096 bytes
> is not knowable in advance, so an assertion that requires the `src=` shape would be a coin flip.
>
> Do **not** grep for `parseFilterParams` or `WINDOW_7D_WIDTH_DAYS`: VERIFIED that esbuild mangles
> every identifier (`dist/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js`
> opens `(function(){const q=document.getElementById("rte-strings")…function P(a,c,i)…`). Only
> string literals survive.
>
> Falsifiable counterexample to demonstrate once: delete the `import` line from `news.astro`'s
> script (leaving the rest), rebuild, confirm assertion 17 fails for the `en` locale with a clear
> message, restore, reconfirm green. Record in the comment whether the build itself failed first.

---

**Amendment 4 — Add a Wave-0 bundling spike to Plan 28-01 so F-27 is settled before 28-02 is written (fixes FM-5).**

Insert as `28-01-PLAN.md` **Task 0** (before Task 1):

> **Task 0 (auto): Prove the F-27 bundling assumption before anything depends on it.**
> Create a throwaway page `site/src/pages/_f27probe.astro` containing only frontmatter `---` and
> a bare `<script>import { FILTER_LOGIC_MARKER } from '../lib/newsFilterLogic'; console.log(FILTER_LOGIC_MARKER);</script>`
> (requires Task 1's module, so run Task 0 immediately after Task 1). Run
> `cd site && npm run build` in ONE command and record, in `28-01-SUMMARY.md`:
> (1) whether the build succeeded; (2) whether `dist/_f9probe`-equivalent HTML carries an inline
> `<script type="module">` or a `src="/_astro/…"` reference; (3) whether the literal
> `newsFilterLogic/v1` appears in the shipped JS; (4) the byte size of the emitted script.
> Then **delete `_f27probe.astro` and rebuild**, confirming `dist/` no longer contains it and
> `node scripts/validate/facets.mjs` still exits 0.
>
> **This is the phase's single load-bearing bet and its cited proof is false.** VERIFIED:
> `RankingTableEnhancer.astro`'s `<script>` block contains **zero** `import` statements (its only
> import, `i18n.ts` at line 38, is frontmatter/server-side), and its emitted chunk is a
> self-contained IIFE with no `import`/`export`. No bare `<script>` anywhere in `src/pages`,
> `src/components`, or `src/layouts` imports a client module. F-27's rationale and
> 28-PATTERNS.md:131 both cite that chunk as proof of import-bundling; it only proves
> hoist-and-hash. 28-RESEARCH.md:326 asserts the opposite conclusion outright.
> If Task 0 shows the import is NOT bundled, STOP and report to the orchestrator — the fallback
> (F-27's stated "duplication with a test-per-copy") is a Plan 28-02 rewrite and that decision is
> the orchestrator's, per F-27. Do not discover this at Wave 3.

Also correct `28-03-PLAN.md` Task 2 `read_first`: replace *"RankingTableEnhancer.astro's bundled
chunk is the existing proof-of-concept this codebase already ships"* with *"RankingTableEnhancer's
chunk shows the file-naming convention and the `src=` emission shape ONLY — its script contains no
`import`, so it does not prove import-bundling; Plan 28-01 Task 0 is the proof"*.

---

**Amendment 5 — Pin the anchor-date formatter to UTC on both pages (fixes FM-6).**

In `28-02-PLAN.md` Task 1 `<action>`, replace the anchor-date sentence with:

> Anchor-date label: `t.news_window_latest.replace('{date}', anchorDate ? new Date(anchorDate + 'T00:00:00Z').toLocaleDateString('en-US', { timeZone: 'UTC', month: 'short', day: 'numeric' }) : '—')`.
> **`timeZone: 'UTC'` is mandatory, not stylistic.** `anchorDate` is a date-only string parsed as a
> UTC midnight instant; without the option, `toLocaleDateString` formats in the *viewer's* zone, so
> in `America/Santiago` (UTC−4) the label renders "Jul 26" for `anchorDate = '2026-07-27'` —
> contradicting `#news-facets.anchorDate` and the newest cards' own `2026-07-27` text, on a page
> whose whole point is data recency (VERIFIED: `TZ=America/Santiago node -e "new Date('2026-07-27T00:00:00Z').toLocaleDateString('es-CL',{month:'short',day:'numeric'})"` → `26 jul`).
> Never reuse `formattedDate` (it formats `generated`, the pipeline timestamp).

Apply the identical change to Task 2 with `'es-CL'`.

Additionally, in `28-03-PLAN.md` Task 1, add to assertion 11: *"and assert that each `.astro` news
page's every `toLocaleDateString(` call site with a `month:` option also passes `timeZone: 'UTC'`
— regex over the page source, both locales. `facets.mjs` assertion 9's TZ scan is hardcoded to
`newsFacets.ts` and will never see these pages."*

---

**Amendment 6 — Substitute `{n}`/`{date}` server-side so the static HTML is correct with JS off (fixes FM-7).**

In `28-02-PLAN.md` Task 1 `<action>`, add:

> **Every `{n}`/`{date}` token must be substituted at build time in the server-rendered markup**;
> the client script re-substitutes on each `applyFilters()`. Otherwise the indexed HTML and the
> JS-disabled view literally read `{n} incidents shown` and `Last 7 days ({n})`, breaking
> NEWSUI-02's "static render is complete and correct" premise and 28-VALIDATION.md's manual
> JS-disabled row ("no filter control is broken-looking"). Server-side initial values (all already
> in scope): `#news-result-count` ← `t.news_result_count.replace('{n}', String(incidents.length))`
> (1215 today); `news_window_7d` ← `.replace('{n}', String(facets.byWindow.sevenDay.length))`
> (297); `news_window_30d` ← `.replace('{n}', String(facets.byWindow.thirtyDay.length))` (1215);
> `news_window_latest` ← the UTC-formatted `anchorDate` per Amendment 5. Assert no literal `{n}`
> or `{date}` survives (Amendment 7, assertion 18).

Mirror in Task 2.

---

**Amendment 7 — Add the four missing Wave-0 assertions to Plan 28-03 (fixes FM-8).**

Extend `28-03-PLAN.md` Task 1 with assertions 18-21, each iterating **both** `DIST_PAGES` entries
(RR-1 pattern) and each with a stated counterexample demonstrated RED once:

- **(18) filter-control presence + no unsubstituted tokens** (covers VALIDATION rows NEWSUI-01
  "controls rendered on BOTH pages" and NEWSUI-03 "`#news-comuna-q` present"): assert each dist
  page contains `id="news-filters"`, `id="news-comuna-q"`, `id="news-result-count"`,
  `id="news-clear-filters"`, one `data-facet="window"|"region"|"family"` fieldset each, at least
  one `input type="checkbox"` inside each of the region and family fieldsets, and that the page's
  visible markup contains **no literal `{n}` and no literal `{date}`**.
  Counterexample: delete the comuna input → RED; leave `{n}` unsubstituted → RED.
- **(19) canonical + route count unchanged** (covers "no new indexable URL"): assert each dist news
  page's `<link rel="canonical">` is exactly `https://ischilesafe.com/news/` /
  `https://ischilesafe.com/es/noticias/` with no query string, and that neither page emits a
  `<link rel="alternate">` or internal `<a href>` containing `?family=`, `?region=`, `?window=`,
  or `?q=`. Counterexample: add a `?family=robos` link → RED.
- **(20) no `innerHTML` with data-derived strings** (covers NEWSUI-06): source-level scan of
  `news.astro`, `es/noticias.astro`, and `newsFilterLogic.ts` for `innerHTML`, `outerHTML`,
  `insertAdjacentHTML`, and `document.write` — assert zero occurrences. `set:html` remains
  permitted **only** on the single `#news-facets` node already guarded by assertion 7 (match it
  explicitly and require exactly one `set:html` per page). Counterexample: replace one
  `textContent =` with `innerHTML =` → RED.
- **(21) no `client:` directive** (hardens assertion 15 at source level, since `astro-island`
  absence is a downstream symptom): assert neither `.astro` source contains `client:load`,
  `client:idle`, `client:visible`, `client:only`, or `client:media`.

Then update `28-03-PLAN.md`'s objective, `must_haves.artifacts.provides`, and success criteria from
"assertions 11-17" / "17 assertions" to **"assertions 11-21" / "21 assertions"**, and tick
28-VALIDATION.md's Wave-0 sign-off box "Wave 0 covers every ❌".

---

**Amendment 8 — Fix assertion 13's regex (fixes FM-9).**

In `28-03-PLAN.md` Task 1 assertion (13), replace `/^\s*news_[a-z_]+:/m` with:

> `/^\s*(news_[a-z0-9_]+)\s*:/gm`, iterated with `matchAll` (**`g` is required** — a bare `m`-flag
> `String.match` returns a single match, so the parity check would cover exactly one key).
> `[a-z0-9_]+` is required too: VERIFIED that `/^\s*news_[a-z_]+:/m` does **not** match
> `news_window_7d` or `news_window_30d`, so 2 of the 15 keys — including both `{n}`-bearing ones —
> would be invisible and deleting `news_window_7d` from `ES_STRINGS` would leave the assertion
> green. Assert set equality in **both** directions (a key in ES but not EN is equally a defect)
> and additionally assert the harvested key count is **≥ 15**, so a regex that silently stops
> matching cannot read as coverage.

---

**Amendment 9 — Carry the F-19 branch explicitly into Plan 28-03 (fixes FM-10).**

In `28-03-PLAN.md` Task 2 `<action>`, append:

> **`freshness.mjs` (validator #15) is expected to be RED for this phase.** VERIFIED 2026-07-30
> 12:54 UTC: `PASS freshness: … is 2.9 days old (generated: 2026-07-27T14:25:05.303451Z)` against
> `MAX_AGE_DAYS = 3` (freshness.mjs:27) — it crosses the limit at ~14:25 UTC on 2026-07-30 and
> stays red for the rest of the phase, because `data/` is read-only and `git pull` is a banned
> remediation. Apply the **F-19 environmental-exclusion branch** verbatim: confirm the failure
> output is exactly the age assertion (not missing-file, not unparseable `generated`), confirm
> `git log -1 --format=%ci origin/master -- data/incidents/current.json` is within 3 days
> (VERIFIED already true: `2026-07-30 02:02:51 +0000` — the cron is alive, this checkout is
> unpulled), then close the phase on a **"15/16 validators, freshness excluded"** basis with a
> STATE.md `## Blockers` entry. **BANNED, each a phase failure:** raising `MAX_AGE_DAYS`,
> editing/skipping/deleting/unregistering the validator, touching `data/`, or running
> `git pull`/`rebase`/`push`. If any OTHER validator is red, that is a real regression.

Amend the same plan's success criterion "Full phase-close gate green: `npm run build && npm test &&
npm run validate`" to read: *"…`npm run validate` green at 16/16, or 15/16 with freshness excluded
strictly under F-19 and recorded in STATE.md § Blockers"*.

---

**Amendment 10 — Record the UI-SPEC overrides as F-29 / F-30 (fixes FM-11).**

Add to `.planning/STATE.md` § Fable Decisions, and reference from `28-02-PLAN.md`'s objective:

- **F-29 — `facetKeys` is NOT serialized into `#news-facets`; per-card `data-*` attributes are the
  client-side count source.** This **overrides 28-UI-SPEC.md:167**, which mandates adding
  `facetKeys` to `facetsProjection`. Rationale: `facetKeys` is 1,215 objects of
  `{id, family, regionId, yearMonth, window}` — order 100 KB of inline JSON **per page, on both
  pages**, duplicating information already present in the markup, against NEWSUI-06's "no
  measurable regression". The `data-family`/`data-region-id`/`data-date`/`data-commune-norm`
  attributes carry the same information at near-zero marginal cost and keep the DOM the single
  source of truth for what is filterable. Consequence: `facetsProjection` gains only `anchorDate`,
  so Plan 28-02's "no new `set:html` site" claim stands and assertion 7 keeps covering the payload.
- **F-30 — `norm()` is imported from `newsFilterLogic.ts`, not copy-pasted.** This **overrides
  28-UI-SPEC.md:178** ("copy-pasted (do not import cross-page)"), consistent with F-27, which is
  the later decision. Already documented at 28-PATTERNS.md:62; recorded here so the UI-SPEC
  contradiction is closed rather than discovered at verification.

Also add `status: superseded-in-part` notes at 28-UI-SPEC.md lines 167 and 178 pointing at F-29 and
F-30, so a verifier reading the binding contract does not flag the plans as non-compliant.

---

**Amendment 11 — Specify the region-label derivation, including the ES form (fixes FM-12).**

In `28-02-PLAN.md` Task 1 `<action>`, replace *"region name from `loadIndex()`/an existing
region-name lookup already used elsewhere on this page or `../lib/data`"* with:

> region names come from `loadRegion(regionFileId(regionId)).name` (`site/src/lib/data.ts:171`),
> built once in the frontmatter as `const regionNames = new Map(facets.byRegion.map(r => [r.regionId, loadRegion(regionFileId(r.regionId)).name]))` — at most 16 lookups.
> **`loadIndex()`/`CommuneMeta` carries no region name** (VERIFIED: `{cut, name, slug, region_id,
> population, low_population}`) and this page has no existing region-name lookup, so there is
> nothing to reuse — do not improvise one from `region_id`.

In `28-02-PLAN.md` Task 2, add a **fourth** difference to its "three differences only" list:

> (4) ES region labels are wrapped in `regionNameEs(name)` (`site/src/config/i18n.ts:666`),
> yielding "Región Metropolitana" / "Región del Maule" / "Región de Valparaíso" — matching every
> other ES page. Without it `/es/noticias/` would label a checkbox bare `Metropolitana` while the
> rest of the ES site says `Región Metropolitana`.

---

**Amendment 12 — Make assertion 12's card regex attribute-order-independent (fixes FM-13).**

In `28-03-PLAN.md` Task 1 assertion (12), replace `/<article class="news-card"/g` with:

> `/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"/g` — order-independent over the attributes
> Plan 28-02 adds to the same tag. VERIFIED today: this and the literal form both return **1215**
> on both dist pages (= `incidents.length`), while the bare substring `news-card` returns **1216**
> (the extra is the inlined `.news-card` CSS rule — confirming VALIDATION.md's warning). The
> literal form silently returns **0** if the executor writes `<article data-family="…"
> class="news-card">`, producing a false RED on correct code.

---

**Amendment 13 — Correct the stale test-count and coverage claims (fixes FM-14 rows 2-3).**

- `28-01-PLAN.md` Task 2: replace "the FULL existing 20-test file" with "the FULL existing
  `newsFacets.test.ts` (**13** `it()` blocks — VERIFIED; the 20 that `npm test` reports are across
  **2** files, the other 7 being `src/lib/formatNumber.test.ts`)". Same in its `<done>`
  ("20(+)-test suite" → "13(+)-test suite") and in `28-VALIDATION.md:21` ("20 tests" → "13 tests;
  `npm test` totals 20 across 2 files").
- `28-03-PLAN.md` objective: append *"Note (F-24, STATE.md:203): `facets.mjs`'s existing 10
  assertions include 3 that are true by construction for every input (assertion 1's count-sum,
  assertion 8's three containments — confirmed by a 20,000-input fuzz) and 1 unreachable behind
  assertion 3. Do not read the assertion count as coverage; every assertion added here must be
  demonstrated RED before it is claimed."*

---

**Amendment 14 — Correct the EN/ES structural-parity claim (fixes FM-15).**

In `28-02-PLAN.md` Task 2 `read_first`, replace *"confirmed byte-identical structure to news.astro
pre-Task-1, only copy differs"* with:

> **NOT byte-identical — VERIFIED structural drift exists today.** The ES file places the
> `formattedDate` block at lines 49-63 where EN has it at 83-94; its `<style>` block orders
> `.freshness`/`.empty-state` at 217-227 where EN has them at 292-301; and it lacks EN's
> `slugToCommune` comment. Locate each insertion point by its **semantic anchor** (the
> `facetsProjection` object literal; the intro `<section>`'s closing tag; the first
> `<section class="news-month-section">`; the `<article class="news-card">` opening tag), never by
> line number. Diff the two files after both tasks and confirm the only remaining differences are
> import depth, locale strings, `FAMILY_LABELS_ES`, `regionNameEs`, the `'es-CL'` formatter, and
> pre-existing comment/order drift — record that diff in `28-02-SUMMARY.md`.

---

**Amendment 15 — Document the `?region=` namespace split for Phases 29/30 (addresses FM-16).**

Add to `28-02-PLAN.md`'s objective and to `.planning/STATE.md` § Phase 28 Outcome (at close):

> **Query-param namespace note for Phases 29/30.** After Phase 28, `?region=` has two distinct
> site-wide meanings: on `/news/` + `/es/noticias/` it is a **comma-separated multi-value** list of
> region ids (`?region=13,5`); on `/map/` + `/es/mapa/` the known-unclosed `?region=` gap is a
> **single-value** focus target alongside the working `?cut=` deep link. Phase 30 (map
> control-shell rework) must implement the map's `?region=` as single-value and must NOT reuse
> `parseFilterParams`, whose CSV semantics are news-specific. `newsFilterLogic.ts` is deliberately
> scoped to the news pages and is not a general query-param library.

---

**Amendment 16 — Soften the "single canonical `norm()`" claim (fixes FM-18).**

In `28-01-PLAN.md` Task 1 `<action>` and the module header it prescribes, replace *"`norm()` is the
single canonical definition in this codebase per F-27"* with:

> `norm()` is the single canonical definition **for the news pages** per F-27 — both news pages
> import it and neither re-declares it. Note that `communes/index.astro` and
> `es/comunas/index.astro` retain their own inline copies (VERIFIED: `dist/communes/index.html`
> still ships `const a=e=>e.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase()`); Phase 28 does not
> touch them, so three bodies exist after this phase. Do not write a comment claiming otherwise —
> consolidating the directory pages is a separate `/gsd:quick` task.

---

## Load-bearing assumptions that are NOT proven

1. **F-27: a bare (non-`is:inline`) Astro `<script>` `import`ing a local `.ts` module is bundled by
   Vite and ships without an island.** *Unproven in this repo.* No bare `<script>` anywhere in
   `src/pages`, `src/components`, or `src/layouts` contains a client-side `import` (VERIFIED across
   all six). The chunk F-27 and 28-PATTERNS.md:131 cite as proof —
   `RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js` — comes from a script
   with **zero** imports and is a self-contained IIFE, so it proves hoist-and-hash only.
   28-RESEARCH.md:326 asserts the opposite conclusion. My judgment: the assumption is probably
   TRUE (documented Astro behavior), but "probably true" is not what a plan should stake three
   waves on. **Amendment 4 makes it a 60-second Wave-0 fact.**
2. **Which emission shape Astro will choose for the news pages' script (inline vs `_astro` chunk).**
   *Genuinely unknowable in advance.* The rule is exact and verified
   (`plugin-scripts.js:24` + `util.js:15`: 0 imports ∧ 0 dynamic imports ∧ bytes < 4096, default
   limit, no override in `astro.config.mjs`), but the inputs — whether Rollup hoists
   `newsFilterLogic` into a shared chunk for the two entries, and the final minified byte count of
   code not yet written — sit on both sides of a threshold. **Amendment 3 makes assertion 17
   shape-agnostic instead of guessing.**
3. **That no `client:`-free bare `<script>` adds an `astro-island` marker.** Strongly supported —
   `dist/communes/index.html` and every commune page carry module scripts with no `astro-island`
   anywhere — but not yet proven *for a script with an import*. Assertion 15 will settle it at
   Wave 3; Amendment 4's Task 0 settles it at Wave 1.
4. **That `newsFilterLogic.ts` living in both the SSR graph (frontmatter `norm()` for
   `data-commune-norm`) and the client graph is harmless.** Almost certainly fine — the module is
   pure with no `node:` imports, unlike `newsFacets.ts` — but it is a new dual-graph usage in this
   repo. Task 0's build settles it.
5. **That the empty-state and result-count nodes cannot be read as thin content.** Reasoned from
   UI-SPEC:196 (not a heading tag, ships `hidden`, canonical unchanged) and it is sound, but there
   is no automated canonical/param-link check until Amendment 7's assertion 19 exists.

---

## Accepted risks

1. **`30d` currently equals "All dates" (both 1215).** `current.json` spans 2026-06-29 → 2026-07-27
   (28 days), so every incident falls inside the 30-day window and the two controls are
   indistinguishable today. *Accepted* — the window math matches `newsFacets.ts` exactly and will
   differentiate as soon as the corpus exceeds 30 days. Do not "fix" it by changing the boundaries;
   that would break the 7d/30d parity with the server-side `byWindow` that assertion 8 pins.
2. **The `today` window option ships without a per-option count.** `news_window_latest` is
   "Latest data: {date}" with no `{n}` slot, while `computeFacetCounts` computes `today` = 11.
   *Accepted* — the anchor date is the more useful signal for that option and the UI-SPEC's
   Copywriting Contract is binding on wording; NEWSUI-01's "per-option counts visible" is satisfied
   by the region, family, 7d, and 30d options.
3. **`?family=`/`?region=` accept arbitrary attacker-supplied values of arbitrary length.**
   *Accepted* (matches Plan 28-01's T-28-02): values are only ever `.includes()`-compared against
   `data-*` attribute strings on 1,215 cards, never interpolated into HTML, so an unrecognized key
   matches zero cards and renders the empty state. No injection surface, bounded compute.
4. **The interactive halves of NEWSUI-01/-03/-04 stay manual.** No DOM-interaction harness exists
   for `.astro` pages and adding one violates the zero-new-dependency constraint. *Accepted* per
   28-VALIDATION.md § Manual-Only Verifications — provided the plans do **not** claim those
   requirements are fully automated, which they currently do not.
5. **Three `norm()` bodies will exist after Phase 28** (newsFilterLogic.ts + the two directory
   pages). *Accepted* — consolidating `communes/index.astro`/`es/comunas/index.astro` is out of
   scope and touching them is gratuitous regression risk. Amendment 16 only stops the code comment
   from claiming otherwise.
6. **The `?region=` semantic split between `/news/` (CSV multi) and `/map/` (single-value focus).**
   *Accepted* rather than renamed: the UI-SPEC's query-param contract is binding and locked to
   `region`, and renaming to `?regions=` would diverge from it for a cross-page consistency the
   user never asked for. Amendment 15 documents the split so Phase 30 cannot trip on it.
7. **F-24's known latent `byMonth` id-fallback edge cases** (id-less incident in both sources
   double-counts; two id-less incidents sharing cut+date collapse; empty archive array still tags
   `source:'both'`). *Accepted, unchanged by Phase 28* — unreachable in live data (VERIFIED: 1,215
   incidents, 0 missing `family`, 0 missing `cut`, 1,215 distinct ids) and Phase 28 adds no new
   `byMonth` consumer beyond the month-section collapse, which reads the DOM, not `byMonth`.

---

## Appendix — commands run, with real output

```
$ cd site && npx astro check              # ANSI-stripped
Result (128 files):
- 4 errors
- 0 warnings
- 38 hints
  → grep -c "error"           = 5      (Plan 28-02's gate requires ^[0-4]$  → CANNOT PASS)
  → grep -cE "^[0-9]+ error"  = 0      (Plan 28-03's gate requires a match  → CANNOT PASS)
  → the 4 errors, VERBATIM, all in ONE file:
      src/components/ComparatorPairsLinks.astro:28 - error ts(7031) 'nameB' implicitly has 'any'
      src/components/ComparatorPairsLinks.astro:28 - error ts(7031) 'nameA' implicitly has 'any'
      src/components/ComparatorPairsLinks.astro:28 - error ts(7031) 'cutB'  implicitly has 'any'
      src/components/ComparatorPairsLinks.astro:28 - error ts(7031) 'cutA'  implicitly has 'any'
    (NOT in scripts/validate/*.mjs, as three documents claim)

$ node scripts/validate/facets.mjs
PASS facets: 1215 incidents, 8 families observed, 346 communes cross-checked,
             3 months in byMonth union, window(today=11,7d=297,30d=1215), TZ-determinism verified
EXIT=0

$ node scripts/validate/freshness.mjs
PASS freshness: data/incidents/current.json is 2.9 days old (generated: 2026-07-27T14:25:05.303451Z)
EXIT=0     # MAX_AGE_DAYS = 3 → flips RED ~14:25 UTC 2026-07-30

$ git log -1 --format=%ci origin/master -- data/incidents/current.json
2026-07-30 02:02:51 +0000        # F-19 condition (b) satisfied: cron alive, checkout unpulled

$ npm test
Test Files  2 passed (2)          # newsFacets.test.ts (13 it()) + formatNumber.test.ts (7)
Tests      20 passed (20)         # NOT "newsFacets.test.ts = 20 tests"

$ node -e "…current.json…"
incidents 1215 · generated 2026-07-27T14:25:05.303451Z
min 2026-06-29 · max 2026-07-27 · no family 0 · no cut 0

$ node -e "card counts in dist"
dist/news/index.html         <article class="news-card": 1215 | substring news-card: 1216 | month-section: 3
dist/es/noticias/index.html  <article class="news-card": 1215 | substring news-card: 1216 | month-section: 3

$ node -e "…i18n parity regex…"
news_window_7d       false     # /^\s*news_[a-z_]+:/m — 2 of 15 keys invisible
news_window_30d      false
news_filter_heading  true

$ node -e "readFileSync('site/src/config/i18n.ts')"      # Plan 28-01 Task 3, verbatim, cwd=site/
Error: ENOENT: … open '…\Is Chile Safe\site\site\src\config\i18n.ts'
EXIT=1

$ grep -o '<script[^>]*>' dist/communes/index.html | sort | uniq -c
      1 <script type="module">                       # INLINE (1883 bytes, 0 imports)
$ grep -o '<script[^>]*Ranking[^>]*>' dist/commune/algarrobo/index.html
  <script type="module" src="/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js">

$ head -c 200 dist/_astro/RankingTableEnhancer.astro_astro_type_script_index_0_lang.BXsR19UC.js
(function(){const q=document.getElementById("rte-strings");if(!q)return;
const N=JSON.parse(q.textContent||"{}"),J=q.dataset.locale||"en";function P(a,c,i){…
  → every identifier mangled; assertion 17's `parseFilterParams` grep can never match
  → and this script contains NO import at all, so it does not prove F-27

$ grep -n "imports.length === 0" node_modules/astro/dist/core/build/plugins/plugin-scripts.js
24: … && output.imports.length === 0 && output.dynamicImports.length === 0
       && shouldInlineAsset(output.code, output.fileName, assetInlineLimit)) { /* inline */ }
$ grep -n "byteLength" node_modules/astro/dist/core/build/plugins/util.js
15: return Buffer.byteLength(assetContent) < Number(assetsInlineLimit);   # Vite default 4096
$ grep -c assetsInlineLimit astro.config.mjs
0                                  # no override → 4096 applies
```
