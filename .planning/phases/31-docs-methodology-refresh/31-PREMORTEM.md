# Phase 31 — PREMORTEM

**Premise:** it is 2026-08-04. Phase 31 failed. This document says exactly why, with evidence, and attaches a paste-ready amendment or an explicit acceptance to each mode.

**Method:** every claim below was verified by reading the real file or executing the real check. Simulations of `forbidden-language.mjs` reproduce its exact algorithm (NFD accent-strip → lowercase → `(?<![a-z0-9])term(?![a-z0-9])`) against the proposed sentences.

**Verdict in one line:** the phase did not fail because it wrote a wrong fact. It failed because **two of the three "corrected" sentences are banned by the site's own CI editorial gate**, and because **Wave 2's guards grep for the literal prose Wave 1 was supposed to write** — so the moment Wave 1 had to reword, the phase's own durability layer went red and the executor's cheapest escape was to loosen the guard.

---

## 1. CRITICAL — The corrected EN and ES methodology sentences trip `forbidden-language.mjs` and fail the build gate

**Evidence.** `site/scripts/validate/forbidden-language.mjs:47` bans `'la mas segura'` and `:57` bans `'the safest'`, matched on accent-stripped visible dist text with a word-boundary lookaround. Plan 31-01 Task 1 prescribes verbatim:

- EN: `"… the commune with the most reported crime, not the safest."`
- ES: `"… la comuna con más delincuencia reportada, no la más segura."`

Running the validator's exact matching logic over those two strings:

```
$ node scratchpad/fl.mjs
HIT EN_meth -> "the safest"
HIT ES_meth -> "la mas segura"
scan complete
```

The `ALLOW_LIST` (`forbidden-language.mjs:66-71`) exempts only CEAD-attributed superlatives (`/according to cead data for \d{4}/i`, `/segun (delitos|incidentes) reportados/i`, …) inside a 100-char forward window. Neither proposed sentence contains any allow-list phrase, so neither is exempted.

Corroboration that this is a known trap and not a theory: `site/src/pages/safest-cities-in-chile.astro:8` carries the comment
`* T-04-11: forbidden-language gate must not catch bare "the safest" / "definitive ranking".`
The page was deliberately authored around this term. Plan 31-01 reintroduces it.

**Blast radius.** `forbidden-language.mjs` is validator #9 in `all.mjs`. `npm run validate` goes red → the phase-close bar in Plan 31-04 Task 3 ("16/16, or 15/16 with only `freshness` excluded") is unreachable. Worse, the plausible executor recovery is to delete the contrastive clause entirely, which restores an unqualified "Rank 1 = highest reported rate" with no directional hint — exactly the ambiguity DOCS-01 exists to remove — or to add a term to `FORBIDDEN_TERMS`' allow-list, which would silently weaken the editorial ban sitewide.

**AMENDMENT (paste-ready).** Replace Plan 31-01 Task 1's two prescribed sentences with these, which were verified clean against the full 23-term ban list:

- `site/src/pages/methodology.astro`, `<strong>Ranking basis:</strong>` item, final clause:
  > `Rank 1 = highest reported rate in Chile for that year (most police-reported incidents per 100,000 inhabitants), not the lowest.`

- `site/src/pages/es/metodologia.astro`, `<strong>Base del ranking:</strong>` item, final clause:
  > `Ranking 1 = mayor tasa reportada en Chile para ese año (más denuncias por 100.000 habitantes), no la menor.`

- `site/src/pages/safest-cities-in-chile.astro`, `<p class="table-note">` final sentence:
  > `The National Rank column (a separate sitewide measure, not this table's own sort order) follows rank 1 = highest reported rate nationwide — most police-reported incidents, not fewest.`

Verification of the amendment (run before committing prose):

```
$ node scratchpad/fl2.mjs
ALL CANDIDATES CLEAN
```

Also add this to Plan 31-01 as a **pre-commit task step**, not a post-hoc verification: *"before writing any new reader-facing sentence, run it through `FORBIDDEN_TERMS` in `site/scripts/validate/forbidden-language.mjs`; the terms `the safest`, `la mas segura`, `most dangerous`, `mas peligrosa` are the ones this phase is most likely to hit."*

---

## 2. CRITICAL — Wave 2's regression guards grep the exact prose Wave 1 writes; the guard measures itself

**Evidence.** Plan 31-04 Task 2(a) instructs `figure-registry.mjs` to `fail if methodology.astro is missing "highest reported rate in Chile" or metodologia.astro is missing "mayor tasa reportada en Chile"` — literal substring checks on the exact strings Plan 31-01 Task 1 prescribes.

Three independent ways this goes red or vacuous:

1. **Failure mode 1 forces a reword.** Once the sentence must change (§1), the guard's pinned tokens no longer match unless someone remembers to change them in two plans. Same executor, same wave, no cross-check → the cheapest fix is editing the guard to match whatever was written, which converts the assertion into a tautology.
2. **Line-wrapping breaks the substring.** `site/src/pages/methodology.astro:324` is currently **96 characters** and reads
   `        of which a subset meet the population threshold). Rank 1 = lowest reported rate in Chile`
   with `for that year.` on line 325. `lowest`→`highest` makes it 97 and the appended clause forces a reflow of the whole `<li>`. If the reflow breaks between `in` and `Chile`, `readFileSync(...).includes('highest reported rate in Chile')` is **false** on a file whose prose is perfectly correct. `.astro` prose here is hard-wrapped around 92-96 cols, so this is the default outcome, not the edge case.
3. The ES side has the identical hazard on `es/metodologia.astro:336`.

**AMENDMENT.** Two changes, both required.

(a) In Plan 31-04 Task 2(a), replace the *positive* substring checks with whitespace-insensitive ones so reflow cannot break them:

```js
// Whitespace-insensitive: .astro prose is hard-wrapped, so the phrase may
// straddle a newline. Falsifiable counterexample: revert either sentence to
// "lowest reported rate" -> RED.
const flat = (s) => s.replace(/\s+/g, ' ');
const EN_OK = /rank 1 = highest reported rate in chile/i;
const ES_OK = /ranking 1 = mayor tasa reportada en chile/i;
if (!EN_OK.test(flat(methodologyEn))) fail('DOCS-01: methodology.astro lost the corrected national_rank direction');
if (!ES_OK.test(flat(methodologyEs))) fail('DOCS-01: es/metodologia.astro lost the corrected national_rank direction');
```

Keep the three *negative* checks (`lowest reported rate in Chile`, `menor tasa reportada en Chile`, `lowest reported rate among all non-low-population`) but run them through `flat()` too.

(b) Add a **hard cross-plan pin** to both 31-01 and 31-04, stated identically in each:

> **PINNED TOKENS (do not change in one plan without changing the other).** The regression guard in 31-04 matches, whitespace-insensitively and case-insensitively: `rank 1 = highest reported rate in chile` (EN methodology), `ranking 1 = mayor tasa reportada en chile` (ES methodology), `rank 1 = highest reported rate nationwide` (safest-cities). Any Wave-1 rewording that drops one of these token sequences is a **deviation requiring a matching 31-04 edit in the same commit**, never a guard relaxation.

---

## 3. HIGH — Plan 31-02 edits `data/`, which the run directive declares read-only, and the plans cite decision IDs that do not exist

**Evidence.**

- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:73` — *"**No mutation of `data/`** beyond what the pipeline tests write to fixtures."*
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:156` — *"`data/` es solo lectura"*.
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:79` (F-19) — *"BANNED remediations, each a phase failure: … touching `data/`…"* (scoped to freshness remediation, but the blanket rule at :73/:156 is not so scoped).
- Plan 31-02 `files_modified: [data/SOURCES.md]`, and its own threat model asserts the exemption *inside the plan being judged*: "`data/`'s READ-ONLY constraint applies to scraped/computed data artifacts, not to this hand-maintained attribution document". That reading is almost certainly right on the merits — but a plan cannot grant itself an exemption from the directive.

Separately, the decision IDs are broken:

```
$ grep -c "^| F-" .planning/STATE.md   # highest row present: F-58
```

`F-60`…`F-65` **do not exist** in `.planning/STATE.md § Fable Decisions` (the table ends at F-58). Plans cite them anyway: `31-01-PLAN.md:123` invokes "per F-60" to justify *not* adding an ES safest-cities footnote — but F-60, per the phase brief, is the *ENUSC-edition-year* decision, an entirely different subject. So the one place a plan cites a binding decision by number, it cites the wrong one, and none of the six are recorded anywhere an auditor can read them.

**AMENDMENT.** Before Wave 1 starts, append F-59…F-65 to `.planning/STATE.md § Fable Decisions`, including explicitly:

> `| F-59 | 2026-08-02 | 31 | data/SOURCES.md is a hand-maintained attribution document, NOT a scraped/computed data artifact; editing it is authorized for Phase 31 and does not violate the directive's data/ read-only rule (:73, :156) or F-19's banned-remediation list. No other path under data/ may be touched. | SOURCES.md has no pipeline writer; DOCS-03 cannot be satisfied without editing it. |`

And fix `31-01-PLAN.md:123` to cite the decision that actually says "no forced ES parity where none existed" (F-63 per the phase brief), or to state the rationale inline without an ID.

---

## 4. HIGH — Wave 2's DOCS-03 guard is satisfiable by prose that is still wrong, and Plan 31-02's own acceptance criterion is already vacuous

**Evidence 1 — a pre-satisfied acceptance criterion.** Plan 31-02 Task 1 lists `grep -c "Emol (https" data/SOURCES.md` equals 0 as proof the retired fixed-feed list was removed. Measured on the *unmodified* file:

```
$ grep -c "Emol (https" data/SOURCES.md
0
```

It is already 0 because `data/SOURCES.md:391` reads ``- Emol (`https://www.emol.com/rss/`)`` — a backtick sits between `(` and `https`. The criterion passes whether or not the executor deletes a single line. This is precisely the "green gate that measured what it was written to measure" pattern the phase objective names.

**Evidence 2 — the Wave-2 guard is three token presence checks.** Plan 31-04 Task 2(b): fail unless SOURCES.md contains `news.google.com` *or* `Google News`, contains `granite` case-insensitively, and contains `R2`. Adding one sentence naming all three tokens satisfies it while leaving the retired Emol/BioBio/T13/Cooperativa feed list and the dead `data/news/current.json` citation intact. Nothing checks the *removals*, which are the actual defect.

Current baselines (all confirm the tokens are genuinely absent today, so the positive checks are at least non-vacuous):

```
$ grep -ic granite data/SOURCES.md            -> 0
$ grep -c  "R2" data/SOURCES.md               -> 0
$ grep -c  "data/news/current.json" data/SOURCES.md -> 1
```

**AMENDMENT.**

(a) In Plan 31-02 Task 1, replace the `Emol (https` criterion with one that matches the real bytes:

```
grep -c '^- Emol' data/SOURCES.md            equals 0
grep -c 'biobiochile.cl/feed' data/SOURCES.md equals 0
grep -c 't13.cl/rss.xml' data/SOURCES.md      equals 0
grep -c 'cooperativa.cl/rss' data/SOURCES.md  equals 0
```

(b) In Plan 31-04 Task 2(b), add the two **negative** assertions that carry the actual DOCS-03 signal:

```js
if (sources.includes('data/news/current.json')) fail('DOCS-03: SOURCES.md still cites the dead data/news/current.json path');
if (/^- Emol|biobiochile\.cl\/feed|t13\.cl\/rss\.xml|cooperativa\.cl\/rss/m.test(sources)) fail('DOCS-03: SOURCES.md still lists the retired fixed per-outlet RSS feeds as the ingestion source');
if (!sources.includes('data/incidents/current.json')) fail('DOCS-03: SOURCES.md does not cite the real incidents storage path');
```

---

## 5. HIGH — The `figure-registry.mjs` retitle can silently break F15, which the plans never mention

**Evidence.** `figure-registry.mjs:185-190` — the figure immediately preceding F16 passes on the whole-file token group `['RSS', 'news']`, with the note *"News layer attribution: … SOURCES.md must reference RSS/news."* Plan 31-02 retitles the section from `## News feeds — qualitative incident layer (RSS)` to `## News feeds — qualitative incident layer (Google News RSS)`, which happens to preserve `RSS`. But the rewrite instruction is a free-form "replace the entire section", and nothing in Plan 31-02's acceptance criteria asserts `RSS` survives. If an executor writes "Google News search feeds" instead, validator #13 goes red for a reason no criterion in either plan predicts, and the diagnosis cost lands on the phase-close gate.

**AMENDMENT.** Add to Plan 31-02 Task 1's acceptance criteria:

```
grep -c "RSS" data/SOURCES.md >= 1   # F15's token group ['RSS','news'] must keep matching
```

and to the Task 1 action text: *"the literal token `RSS` must remain somewhere in this section — `figure-registry.mjs`'s F15 entry depends on it."*

---

## 6. MEDIUM — The corrected claim IS factually right; the ES translation IS equivalent. Verified, accept.

**Evidence.** `pipeline/cead/normalizer.py:111-141`:

```
- Rank by rate_per_100k descending (highest rate = rank 1)
eligible_sorted = sorted(eligible_indices, key=lambda i: _latest_rate(records[i], year), reverse=True)
for rank, i in enumerate(eligible_sorted, start=1): records[i]["national_rank"] = rank
```

Rank 1 = highest rate. The plans' direction is correct, and matches the three places already correct in the codebase (`site/src/pages/commune/[slug].astro:100`, `site/src/pages/es/comuna/[slug].astro:102`, `site/src/lib/proseEngine.ts:58`, `site/src/pages/compare/[pair].astro:232,246`, `site/src/lib/comparisonProse.ts:198,209`). The ES clause `mayor tasa reportada` is the exact semantic twin of `highest reported rate`. **No inverted-fix risk. Accept.**

**One real ambiguity worth noting, not a blocker.** The EN methodology sentence says "Rank 1 = highest reported rate **in Chile**"; the safest-cities footnote says "**nationwide**". Both refer to the same national scale, but a reader moving between pages sees two phrasings. Accept — a synonym is not a factual divergence, and F-63 forbids churning correct prose elsewhere to homogenize it.

---

## 7. MEDIUM — A fourth surface uses lowest/highest language and must NOT be "fixed"

**Evidence.** `grep -rn "lowest reported rate\|rank 1\|Rank 1" site/src` returns exactly **three** inverted instances (`methodology.astro:324`, `es/metodologia.astro:336`, `safest-cities-in-chile.astro:174`) — the plans' inventory is complete. But it also returns:

- `site/src/pages/chile-crime-map.astro:89` — *"(lowest reported rate) to the deepest red-brown (highest reported rate)"*. This describes the **choropleth colour scale**, not `national_rank`. It is correct.
- `site/src/pages/safest-cities-in-chile.astro:54-55` — *"Sort by rate ascending (lowest reported incidence first)"*. A source comment describing the page's own sort. Correct.

Both contain the trigger strings a careless "zero remaining instances" sweep would target. Plan 31-01's `<verification>` block says *"`grep -rn "lowest reported rate"` … returns zero matches"* but scopes it to the three files — good. Plan 31-01's `<success_criteria>` says *"Zero remaining instances of the inverted national_rank claim anywhere in `site/src`"* — unscoped, and an executor who greps `site/src` broadly will find `chile-crime-map.astro:89` and be tempted.

**AMENDMENT.** Add to Plan 31-01, under `<context>`:

> **DO NOT TOUCH (correct today, protected by F-63):** `site/src/pages/chile-crime-map.astro:89` (colour-scale prose, "lowest reported rate → highest reported rate" describes the choropleth ramp, not rank) and `site/src/pages/safest-cities-in-chile.astro:54-55` (source comment describing this page's own ascending sort). A repo-wide grep for "lowest reported rate" will surface both. Leave them byte-identical.

---

## 8. MEDIUM — The F16 hardening's only real discriminator is the 200-char threshold, and the heading alone already satisfies token group 1

**Evidence.** Measured section lengths in `data/SOURCES.md` (heading line through the byte before the next `## `):

| Section | chars |
|---|---|
| `## CEAD — displayed incidence rates` | 3095 |
| `## Composite Crime Index — methodology` | 2675 |
| `## SPD — homicide reference snapshot` | 2081 |
| `## INE ENUSC SAE — communal VHDV victimization (experimental)` | **1585** |
| `## SII — exposure proxy reference snapshot` | 1548 |
| `## INE — population denominator` | 1465 |
| `## Fiscalía — secuestro reference snapshot` | 1232 |
| `## News feeds — qualitative incident layer (RSS)` | 1099 |
| `## Methodology parameters (editorial decisions)` | 1075 |
| `## chilemapas — map geometry` | 1072 |
| `## ENUSC — underreporting / cifra negra` | 964 |
| `## SPD — institutional authority` | 760 |
| `## Cross-source notes` | **676** ← shortest real section |

**Threshold verdict: safe.** 200 vs. the shortest real section at 676 is a 3.4× margin, and vs. the only section the check actually applies to (1585) it is 7.9×. No legitimate section is at risk. Plan 31-04 is right on this point.

**But the hole is only half-closed.** `figure-registry.mjs:193-196` token group 1 is `['## INE ENUSC SAE', 'VHDV']`, and the real heading line is `## INE ENUSC SAE — communal VHDV victimization (experimental)` — **61 characters that contain both tokens by themselves**. After hardening, the length guard is the *sole* discriminator: a stub section consisting of the heading plus 150 characters of any filler still returns PASS. The mutation test (Test 1) uses a zero-body fixture, so it goes green on a fix that leaves a 201-char bypass wide open.

Can it be defeated from outside the section? No — `extractSection` bounds the search, and group 2 (`['ENUSC','Victimizacion en Hogares','SAE']`) is also evaluated against the bounded text only. That part of the design is sound.

**AMENDMENT.** In Plan 31-04 Task 1, change `checkF16`'s token groups so the heading cannot self-satisfy, and add a fourth test:

```js
export function checkF16(content) {
  const section = extractSection(content, '## INE ENUSC SAE');
  if (!section || section.length <= 200) return false;
  // Drop the heading line: the heading alone contains "## INE ENUSC SAE" and
  // "VHDV", so matching against it proves nothing about the section's body.
  const body = section.slice(section.indexOf('\n') + 1);
  if (body.trim().length <= 200) return false;
  const GROUPS = [['VHDV', 'SAE'], ['Victimizacion en Hogares', 'SAE']];
  return GROUPS.some((g) => g.every((tok) => body.includes(tok)));
}
```

> **Test 4 (add):** a fixture whose `## INE ENUSC SAE — communal VHDV victimization (experimental)` heading is followed by 300 characters of filler containing neither `SAE` nor `Victimizacion en Hogares` in the body must make `checkF16(fixture)` return **false**. This is the case the 200-char guard alone does not catch.

Then re-confirm `checkF16(readFileSync('data/SOURCES.md'))` is still `true` — the real body at lines 319-343 contains both `VHDV` and `SAE` well past the heading.

---

## 9. MEDIUM — DOCS-06's anchor gate omits a linked ES anchor

**Evidence.** `site/src/components/MethodologyCaveat.astro:21`:

```js
const trendHref = locale === 'en' ? '/methodology/#trend-formula' : '/es/metodologia/#trend-formula';
```

`#trend-formula` is a **live link target in both locales**, and `site/src/pages/es/metodologia.astro:262` defines `<h2 id="trend-formula">`. Plan 31-04's assertion F checks `dist/es/metodologia/index.html` for only `id="comparison-criteria"` and `id="media-nacional"` — it does not check `id="trend-formula"` on the ES page. A DOCS-06 gate that omits an actively-linked anchor leaves the exact hole it was written to close.

Full verified inventory of linked methodology anchors:

| Anchor | Defined at | Linked from |
|---|---|---|
| `#trend-formula` (EN) | `methodology.astro:254` | `MethodologyCaveat.astro:21` |
| `#trend-formula` (ES) | `es/metodologia.astro:262` | `MethodologyCaveat.astro:21` ← **missed by the plan** |
| `#comparison-criteria` (EN) | `methodology.astro:301` | `crime-ranking/[crime].astro:244` |
| `#comparison-criteria` (ES) | `es/metodologia.astro:310` | `es/ranking-delito/[crime].astro:250` |
| `#national-mean` (EN) | `methodology.astro:339` | `crime/[family].astro:210` |
| `#media-nacional` (ES) | `es/metodologia.astro:351` | `es/delito/[family].astro:201` |

**Do the phase's edits endanger any of these?** No. Plan 31-01 Task 1 edits an `<li>` *inside* the `#comparison-criteria` section without touching the `<h2>`, and Task 2 inserts a new `<h2 id="sexuales-family">` / `<h2 id="familia-sexuales">` between the cifra-negra and `#enusc-vhdv` sections — above `#national-mean`/`#media-nacional` in document order but not renaming them. Anchor risk is genuinely low; the gap is in the *gate*, not the edit.

**AMENDMENT.** Plan 31-04 Task 2, assertion F: assert **six** ids, not five — add `id="trend-formula"` to the `dist/es/metodologia/index.html` check. Update the plan's `<interfaces>` anchor inventory line accordingly (it currently states `#trend-formula (methodology.astro)` singular, which is what caused the omission).

---

## 10. MEDIUM — i18n parity IS gated (good), but the ES *value* is not; a copied English string ships silently

**Evidence.** Probe 6's assumption is correct and better than the plan claims. `site/scripts/validate/facets.mjs:593-634` is assertion 13, "EN/ES i18n key parity for all `news_*` keys", harvesting `/^\s*(news_[a-z0-9_]+)\s*:/gm` from both `EN_STRINGS` and `ES_STRINGS` blocks and failing on either direction of asymmetry. `news_facet_semantics_note` matches the `news_*` prefix, so an EN-only addition **does** go RED. Plan 31-03's implicit assumption holds.

**What is not gated:** assertion 13 checks key *existence*, never value content. `news_facet_semantics_note: '<the English text>'` pasted into `ES_STRINGS` passes every gate in the repo — assertion 13 (key present), assertion 23 as specified in Plan 31-04 (`.trim().length > 0`, deliberately no wording match), `astro check`, and `forbidden-language`. The ES news page would ship an English paragraph and the phase would close 16/16.

Note also the `enNewsKeys.size < 15` floor at `facets.mjs:619-623`: after this phase there are 16 `news_*` keys, so the floor stays satisfied but no longer tracks reality. Harmless; leave it (F-63).

**AMENDMENT.** In Plan 31-04 Task 2, extend assertion 23 with a cheap non-identity check that costs nothing and closes the copy-paste hole:

```js
// assertion 23b — the ES note must not be the EN string verbatim (silent
// untranslated-copy guard). Falsifiable counterexample: paste the EN value
// into ES_STRINGS -> RED.
const enNote = /news_facet_semantics_note:\s*'([\s\S]*?)',\n/.exec(enBlock)?.[1];
const esNote = /news_facet_semantics_note:\s*'([\s\S]*?)',\n/.exec(esBlock)?.[1];
if (!enNote || !esNote) fail('assertion 23b — could not read news_facet_semantics_note from both string tables');
else if (enNote.trim() === esNote.trim()) fail('assertion 23b — ES news_facet_semantics_note is a verbatim copy of the EN string (untranslated)');
```

The same hole exists for the `sexuales` sections in Plan 31-01 (the ES section is prose, not an i18n key, so assertion 13 does not cover it at all) — see §12.

---

## 11. MEDIUM — Answering probe 1 plainly: what goes RED if the executor writes the OPPOSITE sentence?

Per edit, with the plans as written (before the amendments above):

| Prose edit | What goes RED on the inverted/wrong version? |
|---|---|
| EN methodology "Rank 1 = …" | Plan 31-04's new figure-registry check — **only after Wave 2 lands, and only if its literal token survives (§2)**. During Wave 1: **nothing.** |
| ES methodology "Ranking 1 = …" | Same. During Wave 1: **nothing.** |
| safest-cities footnote | Same. During Wave 1: **nothing.** |
| New `sexuales` sections (EN + ES) | **Nothing, ever.** Plan 31-04 adds no assertion for them. The only checks are Plan 31-01's own `grep -c 'id="sexuales-family"'` — presence of an id, not correctness of a word of its content. An ES section stating the opposite (that `sexuales` *is* merged into CEAD statistics) ships green. |
| `data/SOURCES.md` News-section rewrite | Three token-presence checks (§4) — satisfiable by an otherwise-wrong section. |
| Facet-semantics note (EN + ES) | Assertion 23 checks non-empty inner text only. A note saying "Latest is anchored to today's calendar date" — the exact inverse of `newsFacets.ts`'s contract — ships green. |

**This is the phase's structural weakness and it cannot be fully engineered away** — there is no test for "is this sentence true". Accept for the `sexuales` and facet-note bodies (§13's amendment adds the cheapest partial guard), but the amendments in §2 and §4 are non-negotiable because they cover the claim that is *provably* falsifiable against `normalizer.py`.

---

## 12. LOW/MEDIUM — Requirement DOCS-04's reader-facing note has no factual gate, and one clause is inverse-shaped

**Evidence.** Plan 31-03's ES string prescribes *"«Más reciente» está anclado a la fecha del incidente más nuevo registrado, no a la fecha calendario de hoy"* and the EN twin. This matches the `newsFacets.ts` F-20 contract. But per §11 the only gate is non-emptiness, and the sentence is one negation away from stating the opposite of the shipped behaviour — the single highest-risk sentence in the phase for a silent inversion, because it is the one a reader can least easily check.

**AMENDMENT (cheap, non-brittle).** Plan 31-04 assertion 23: in addition to non-empty text, require the note to contain the anchoring *concept* in each locale without pinning full prose:

```js
const EN_MARKERS = [/anchored/i, /newest incident/i, /not comparable/i];
const ES_MARKERS = [/anclad/i,   /incidente más nuevo/i, /no son comparables/i];
```

Three low-cardinality markers per locale. They survive rewording (§2's lesson) but a wholesale inversion or a dropped clause goes RED.

---

## 13. LOW — Stale doc surface the plans forgot: `news.astro`'s file header still credits DeepSeek

**Evidence.**

```
$ grep -rni "deepseek" site/src
site/src/pages/news.astro:5: * Bilingual news surface for incidents sourced from RSS feeds + DeepSeek geolocation.
```

This is the same falsehood DOCS-03 fixes in `data/SOURCES.md` (default classifier is `ibm-granite/granite-4.1-8b` via OpenRouter per `pipeline/news/classifier.py:8,73-79`), one file away from a page Plan 31-03 already opens. It is a source comment, not reader-facing, so it ships no wrong claim to production — but leaving it means the next reader of `news.astro` learns the retired architecture from the file they are editing.

**AMENDMENT.** Add to Plan 31-03 Task 2 (it already has `news.astro` open):

> Also update `site/src/pages/news.astro:5` from `sourced from RSS feeds + DeepSeek geolocation` to `sourced from Google News RSS search + Granite-4.1-8b classification (see data/SOURCES.md)`. This is a file-header comment, not reader-facing prose; it is the only remaining `DeepSeek` reference under `site/src` (`grep -rni deepseek site/src` -> 1 hit).

Add the acceptance criterion `grep -rci deepseek site/src` equals `0`.

---

## 14. LOW — Surfaces checked and found clean (recorded so nobody re-litigates them)

- **`glossary.astro` / `es/glosario.astro` / `about.astro` / `es/acerca-de.astro` / `rankings.astro`** — `grep -rni "national rank|ranking nacional"` over all six returns **zero matches**. No fourth reader-facing instance of the rank claim exists. The plans' three-instance inventory is complete.
- **JSON-LD / sitemap** — no rank-direction prose in either; nothing to fix.
- **`README.md`** — no `national_rank` or DeepSeek prose surfaced by the sweep.
- **The `checkF16` CLI-execution guard** (Plan 31-04 Task 1, `process.argv[1] === fileURLToPath(import.meta.url)`) — I expected this to be a Windows-path-separator trap that turns validator #13 into a silent no-op. **Measured: it is not.** On Node 22.21.1 on this machine, `process.argv[1]` and `fileURLToPath(import.meta.url)` are strictly equal for (a) an absolute-path invocation (how `all.mjs:66` spawns it: `spawnSync(process.execPath, [path.join(__dirname, script)])`), and (b) a relative-path invocation from `site/` (`node scripts/validate/figure-registry.mjs`, the plan's own acceptance command). Both printed `strict equal: true`. **The plan's guard is safe as specified — do not "improve" it into a normalizing variant.**
- **vitest discovery** — `site/` has no `vitest.config.*`; `package.json:14` is `"test": "vitest run"`, so vitest's default include (`**/*.{test,spec}.?(c|m)[jt]s?(x)`, excluding `node_modules`/`dist`) picks up `site/scripts/validate/figure-registry.test.ts`. The new tests will actually run.

---

## 15. LOW — Plan 31-04's mutation-test fixture invents a heading that does not exist

**Evidence.** Plan 31-04 Task 1, Test 1 fixture heading: `"## INE ENUSC SAE — communal VHDV household victimization rate (experimental, 2024)"`. The real heading at `data/SOURCES.md:318` is `## INE ENUSC SAE — communal VHDV victimization (experimental)`. The fixture also writes `2024`, which sits uncomfortably next to the phase's "never write an ENUSC edition year" constraint even though the SAE dataset is legitimately dated.

**Amendment or accept:** **accept the divergence in principle** — a fixture need not mirror production byte-for-byte, and `extractSection` matches on the `## INE ENUSC SAE` prefix, which both share. But **amend the year**: drop `, 2024` from the fixture heading so no year is written anywhere this phase touches. One-word change, removes any argument about the constraint.

---

## 16. Summary of required amendments (execution order)

| # | Severity | Change | Plan(s) |
|---|---|---|---|
| 1 | CRITICAL | Replace all three corrected sentences with the ban-list-clean versions in §1 | 31-01 |
| 2 | CRITICAL | Whitespace-insensitive regex guards + pinned cross-plan tokens | 31-01 + 31-04 |
| 3 | HIGH | Record F-59…F-65 in STATE.md before Wave 1; authorize `data/SOURCES.md`; fix the F-60 miscitation | STATE.md, 31-01 |
| 4 | HIGH | Fix the vacuous `Emol (https` criterion; add negative DOCS-03 assertions | 31-02, 31-04 |
| 5 | HIGH | Pin `RSS` survival in the SOURCES.md rewrite (F15 dependency) | 31-02 |
| 6 | MEDIUM | Add the DO-NOT-TOUCH list (`chile-crime-map.astro:89`, `safest-cities:54-55`) | 31-01 |
| 7 | MEDIUM | Strip the heading line before F16 token matching; add Test 4 | 31-04 |
| 8 | MEDIUM | Assertion F must check six anchors, incl. ES `#trend-formula` | 31-04 |
| 9 | MEDIUM | Assertion 23b: ES note ≠ EN note verbatim | 31-04 |
| 10 | LOW-MED | Assertion 23 concept markers for the facet note | 31-04 |
| 11 | LOW | Fix `news.astro:5` DeepSeek comment | 31-03 |
| 12 | LOW | Drop `, 2024` from the Test-1 fixture heading | 31-04 |

Accepted without amendment: §6 (the fix is factually correct and the ES twin is equivalent), §11's structural point that prose truth is untestable for the `sexuales` sections, §14's verified non-issues, §15's fixture/production heading divergence.
