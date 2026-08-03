---
phase: 31-docs-methodology-refresh
verified: 2026-08-02T23:45:00Z
status: passed
score: 5/5 success criteria verified after inline fix 89a52a7 (initial pass was 3/5)
verifier: Claude Opus 5 (gsd-verifier, goal-backward, FORCE stance)
diff_under_review: d8db0ab..HEAD (20 commits)
re_verification:
  commit: 89a52a7
  verified: 2026-08-03T03:50:00Z
  previous_status: failed
  previous_score: 3/5
  gaps_closed:
    - "SC1 / DOCS-01 — fifth inverted national_rank claim (is-santiago-safe.astro:53)"
    - "SC4 / DOCS-04 — facet-semantics note claimed unfiltered counts vs F-28 self-exclusion"
  gaps_remaining: []
  regressions: []
  warnings:
    - "INVERTED_PATTERNS[2] over-matches a NEGATED/co-occurrence sentence (synthetic L6); no instance exists in the 117-file corpus and it fails loud, not silent"
    - "The corrected is-santiago-safe sentence clears the pattern's [^.]{0,40} window by only 3 characters — a future reword could redden the build against correct prose"
resolved_gaps:  # RECORD of the initial verification's findings — both now CLOSED by 89a52a7
  - truth: "SC1 / DOCS-01 — no reader-facing national_rank claim contradicts the code"
    status: closed_by_89a52a7
    reason: "A FIFTH inverted rank-direction claim survives, in shipped HTML, in both the visible FAQ and the FAQPage JSON-LD. The new DOCS-01 sweep guard cannot see it because the guard requires a literal `1 =` definition token and this sentence uses the `closer to 1` phrasing instead."
    artifacts:
      - path: "site/src/pages/is-santiago-safe.astro:53"
        issue: "\"A lower national rank (closer to 1) indicates a lower reported rate.\" — pipeline/cead/normalizer.py:136-141 sorts rate_per_100k DESCENDING, so a lower rank number means a HIGHER reported rate. The sentence asserts the exact inverse. Present twice in site/dist/is-santiago-safe/index.html (rendered FAQBlock + schema.org FAQPage mainEntity)."
    missing:
      - "Correct the sentence, e.g. 'A lower national rank (closer to 1) indicates a HIGHER reported rate.'"
      - "Extend INVERTED_PATTERNS in site/scripts/validate/figure-registry.mjs to catch rank-direction assertions phrased without `1 =` (e.g. /closer to 1|cercano a 1/ combined with an inverted direction word)."
  - truth: "SC4 / DOCS-04 — the facet-semantics note's claims match the shipped facet behaviour"
    status: closed_by_89a52a7
    reason: "The note's first sentence describes behaviour the code does not implement."
    artifacts:
      - path: "site/src/config/i18n.ts:380 (EN) and :614 (ES)"
        issue: "EN: 'Filters show unfiltered per-option counts.' / ES: 'Los filtros muestran conteos por opción sin filtrar.' The shipped behaviour (F-28) is SELF-EXCLUSION, not unfiltered: computeFacetCounts (site/src/lib/newsFilterLogic.ts:193-219) calls cardMatchesFilters(card, active, newestDate, dimension), which applies EVERY OTHER active filter dimension and only ignores the option's own dimension. With region=13 selected, family counts are region-13-scoped, not corpus-wide. newsFilterLogic.test.ts Test 9 is literally named 'F-28 self-exclusion' and asserts this."
    missing:
      - "Reword both locale strings to describe self-exclusion, e.g. 'Each filter option's count shows how many incidents it would add given the other filters you have active.'"
      - "Optionally add a facets.mjs assertion pinning the note's wording against the self-exclusion contract."
---

# Phase 31: Docs & Methodology Refresh — Verification Report

**Phase Goal:** Every EN/ES methodology, source-registry, and disclaimer page accurately reflects what the shipped code actually computes today — so no reader-facing claim is stale or contradicted by the running system.
**Status (initial pass, 2026-08-02):** FAILED (2 gaps; both are content-accuracy defects, both narrow and cheap to close)
**Status (final, after 89a52a7):** PASSED — see `## Re-verification (post-89a52a7)` at the bottom of this file. Everything between here and that section is the ORIGINAL report, kept verbatim as the record of what was found.

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Methodology pages describe composite index, ENUSC layer, news-only `sexuales`, and `national_rank` direction with zero prose-vs-computation drift | ✗ **FAIL** | Methodology pages themselves are CORRECT (see below), but a fifth inverted claim survives sitewide in `is-santiago-safe.astro:53` and ships in `dist/`. See GAP-1. |
| 2 | Editorial/legal disclaimers present and correct on every affected page | ✓ PASS | `forbidden-language.mjs`: 835 pages scanned, 0 forbidden terms. `safest-cities-in-chile.astro:105` "does not claim to identify the 'objectively safest' places" intact; methodology "what this site does not claim" intact; all new sentences keep "reported"/"reportad*" framing. |
| 3 | `data/SOURCES.md` current and canonical; ENUSC `[verify edition]` resolved (per amended text, explicit no-claim allowed); CEAD + press outlets attributed | ✓ PASS | See DOCS-03 below — every News-section claim verified line-by-line against `pipeline/news/`. |
| 4 | Phase 26 NO-GO → documentation states so; every facet's semantics documented bilingually | ✗ **FAIL** | NO-GO branch is correct (zero clustering explainer in 835 dist pages). But the shipped note misdescribes facet-count semantics in BOTH locales. See GAP-2. |
| 5 | `figure-registry.mjs` hardened against stub sections; suite + pytest green; EN/ES parity; no broken inbound anchor | ✓ PASS | Mutation re-proved independently; anchors present in built HTML; suite green. |

## DOCS-01..06

| Req | Status | Evidence |
|-----|--------|----------|
| DOCS-01 | ✗ **INCOMPLETE** | 4 of 5 inverted claims fixed and correct; the 5th (GAP-1) ships. |
| DOCS-02 | ✓ SATISFIED | `forbidden-language.mjs` green; spirit-check of every sentence added this phase passed (all use reported-incidence framing, attribute CEAD, and make no absolute verdict). Note `.planning/REQUIREMENTS.md:177` still lists DOCS-02 as **Pending** — a bookkeeping inconsistency, not a code defect. |
| DOCS-03 | ✓ SATISFIED | Verified against source, not SUMMARY. |
| DOCS-04 | ✗ **INCOMPLETE** | Note ships bilingually on both pages, gated by facets 23/23b; NO-GO branch clean; but one factual claim is wrong (GAP-2). |
| DOCS-05 | ✓ SATISFIED | Independently mutation-re-proved. |
| DOCS-06 | ✓ SATISFIED | 6/6 inbound anchors resolve in built HTML. |

---

## 1. `national_rank` direction — independent sweep

**Ground truth re-established from code:** `pipeline/cead/normalizer.py:136-141` — `sorted(..., key=_latest_rate, reverse=True)`, `for rank, i in enumerate(..., start=1)`. **Rank 1 = HIGHEST reported rate.** Docstring agrees ("highest rate = rank 1").

**Patterns I used** (my own, run over all of `site/src`, all extensions, not just the phase's diff):

1. `(rank|ranking|position)[^.]{0,120}(lowest|safest|least|lower reported|safer)` — EN, rank noun then inverted direction, same sentence.
2. `(lowest|safest|least)[^.]{0,120}(rank(ed|ing)? ?#?1|rank 1|first)` — EN, reverse word order.
3. `(posici[oó]n|rango|ranking|puesto|lugar)[^.]{0,120}(m[aá]s segur|menor|m[ií]nim|baja incidencia|m[aá]s baja)` — ES.
4. `(m[aá]s segur|menor incidencia|m[aá]s baja)[^.]{0,120}(posici[oó]n|rango|ranking|puesto|#1|n[uú]mero 1)` — ES reverse.
5. `closer to 1|cercano a 1|m[aá]s cerca de 1` — the phrasing that carries a rank-direction assertion **without** a `1 =` token. **This is the pattern the phase's own guard lacks, and it is the one that found the surviving defect.**
6. Direct read of every `national_rank` / `nationalRank` / rank-label site in `.astro`, `.ts`, `.tsx`, plus `i18n.ts`.

**Result: 4 fixed, 1 surviving.**

Correct after the fix (each read in full, EN vs ES compared for semantic equivalence):

- `methodology.astro:337` — "Rank 1 = highest reported rate in Chile for that year — rank 1 identifies the commune with the most reported crime, not the one with the least." ✓
- `es/metodologia.astro:350` — "Ranking 1 = mayor tasa reportada en Chile para ese año — identifica la comuna con más delincuencia reportada, no la que registra menos." ✓ semantically identical.
- `safest-cities-in-chile.astro:174` — "The National Rank column (a separate sitewide measure, not this table's own sort order) follows rank 1 = highest reported rate nationwide — most reported crime, not safest." ✓
- `es/comunas-mas-seguras-chile.astro:162` — "La columna Rango nacional es una medida a nivel de sitio, distinta del orden de esta tabla: rango 1 = mayor tasa reportada a nivel nacional, es decir, la comuna con más delitos reportados." ✓ equivalent (ES drops the explicit "not safest" contrast clause but states the direction unambiguously — acceptable, not a parity defect).

Confirmed **correct and not collateral damage** (already right, untouched):
`comparisonProse.ts:198,287` ("rank 1 = highest reported incidence" / "posición 1 = mayor incidencia reportada"), `comparisonProse.ts:193` (`rank >= bot10 → 'lowest-incidence decile'` — correct), `proseEngine.ts:58-77` (rankTier doc + thresholds).

### GAP-1 (BLOCKER) — the fifth instance

`site/src/pages/is-santiago-safe.astro:53`, FAQ answer to "Which parts of Santiago have lower reported crime rates?":

> "A lower national rank (closer to 1) indicates a lower reported rate."

This is the exact inversion the phase exists to eliminate. It is reader-facing twice over — rendered by `<FAQBlock items={faqItems}>` (line 231) and serialized into the `FAQPage` JSON-LD `mainEntity` (line 76). `grep -c` against `site/dist/is-santiago-safe/index.html` returns **2**. It predates the phase (commit `b6b3485`, Phase 04) and has no ES twin. Two review rounds plus a sitewide guard missed it because the guard's `INVERTED_PATTERNS[0]` requires a literal `1\s*=` and this sentence uses `(closer to 1)` instead.

The phase goal is explicitly sitewide ("no reader-facing claim is stale or contradicted by the running system") and the phase itself chose a sitewide guard over a diff-scoped one — so this is in scope, not a pre-existing-defect excuse.

## 2. Collateral damage

`git diff --stat d8db0ab..HEAD` touches only 6 files under `site/src`. **Zero** changes to `chile-crime-map.astro`, `rankings.astro`, `is-chile-safe.astro`, `is-santiago-safe.astro`. Within the two ranking pages: `safest-cities-in-chile.astro:54` ascending sort and `:125` "ascending order — lowest reported first" prose intact; `es/comunas-mas-seguras-chile.astro` heading and list prose intact (only line 159 changed). **PASS — no collateral damage.**

## 3. DOCS-03 — SOURCES.md News section vs the pipeline

Every claim checked against source:

| SOURCES.md claim | Code | Verdict |
|---|---|---|
| Google News RSS search, `google_news_url()` | `feeds.py:25-32` → `news.google.com/rss/search?q=...&ceid=CL:es-419` | ✓ |
| `_GOOGLE_NEWS_QUERIES` named registry | `feeds.py:39` | ✓ |
| Direct feeds BioBioChile, Cooperativa, LaTercera, LaCuarta | `feeds.py:66-69` (exactly those four) | ✓ |
| Emol / T13 removed | absent from `feeds.py` | ✓ correct de-attribution |
| `gnews_decoder.py` resolves redirect → real article URL | `decode_gnews_url()` :191 | ✓ |
| Outlet from RSS `<source>`, fallback literal "Google News" | `resolve_outlet()` :141 | ✓ |
| **Classification** by `ibm-granite/granite-4.1-8b` via OpenRouter; DeepSeek selectable fallback | `classifier.py:58,73-79` (`NEWS_PROVIDER` default `openrouter`), `:60-65` deepseek branch | ✓ |
| **Geolocation** is separate, deterministic, LLM never emits a CUT | `classifier.py:26-27,154-155,192` ("LLM emits commune_name … NOT a bare CUT"); `resolver.py:4,22` dict from `data/cead/meta/index.json`, no network/LLM; `resolve_cut()` returns `None` off-set → incident dropped | ✓ **The earlier draft's error (LLM credited with geolocation) is genuinely corrected, and the anti-hallucination control is named correctly.** |
| R2 archive internal, not reader-displayed | `pipeline/tests/test_archive_r2.py` | ✓ |

**ENUSC vintage (F-60):** `data/SOURCES.md:307` now reads "Resolved: intentionally generic — no specific ENUSC edition year is claimed", with the rationale. Verified against the pages: `methodology.astro:213-227` / `es/metodologia.astro:216-232` cite the ENUSC programme via a bare `ine.gob.cl` link with **no year** on any of the three underreporting bullets. The separate dated section survives unchanged: `methodology.astro:253` "Household Victimization Indicator (ENUSC 2024 SAE)" / `es/metodologia.astro:262`. **No year was invented; the dated SAE VHDV text was not collaterally genericised.** ✓

## 4. DOCS-04 — facet-semantics note

Ships as `<p class="facet-semantics-note" id="news-facet-semantics">` on both `news.astro:198` and `es/noticias.astro:196`, from shared i18n keys, with a CSS rule.

- **Window anchor claim: TRUE.** `news.astro:145,157-165` derives the label from `facets.anchorDate` (newest incident date), formatted with `timeZone: 'UTC'`; the client re-reads `parsed.anchorDate` (:344-347). Not wall-clock. ✓
- **Quoted UI label: TRUE.** The note quotes "Latest data" / "Últimos datos"; `i18n.ts:367` = `'Latest data: {date}'`, `:601` = `'Últimos datos: {date}'`. The H2 fix is real. ✓
- **Non-comparability to CEAD per-100k: TRUE** and consistent with SOURCES.md "Measure semantics". ✓
- **Clustering: correctly absent.** Zero matches for `same-event|clustering|agrupamiento` across all 835 dist HTML files. The orphan i18n key `news_cluster_source_count` ('{n} sources') exists but is referenced by no component — dead string, not a reader-facing explainer. (INFO-level: worth deleting.) ✓
- **GAP-2 (BLOCKER): the per-option-count claim is FALSE.** See frontmatter. The note says counts are *unfiltered*; the code implements F-28 *self-exclusion*. This is exactly the class of defect the phase was chartered to eliminate — prose contradicted by the running system — introduced by the phase itself.

## 5. DOCS-05 — figure-registry hardening, re-proved by my own mutation

Run directly against `figure-registry.lib.mjs`, not via the project's own test:

| Fixture | Result | Reason emitted |
|---|---|---|
| heading-only stub | `ok: false` | "section body is 0 chars (<= 200) — the section looks like a stub, not a populated registry entry" |
| heading + `VHDV` + 250 chars filler | `ok: false` | "section body carries only 1 provenance marker(s) [VHDV] — at least 3 of [sha256, ine.gob.cl, VHDV, SAE, Publisher, Measure semantics] are required" |
| real `data/SOURCES.md` | `ok: true` | "6 provenance markers, body 1487 chars" |

**The stub hole is genuinely closed**, and the failure message names a real cause (body length / marker shortfall) rather than `Missing tokens: []`. ✓

## 6. DOCS-06 — anchors in the BUILT tree

| Anchor | EN `dist/methodology/index.html` | ES `dist/es/metodologia/index.html` |
|---|---|---|
| `#trend-formula` | present | present |
| `#comparison-criteria` | present | present |
| `#national-mean` | present | n/a |
| `#media-nacional` | n/a | present |

All **6** inbound links found in `site/src` (`methodology/#trend-formula`, `#comparison-criteria`, `#national-mean`; `metodologia/#trend-formula`, `#comparison-criteria`, `#media-nacional`) resolve to an existing id in the built page. **No anchor broken.** ✓

EN/ES parity of the new content: `sexuales` section added to both (ids `sexuales-family` / `familia-sexuales`, neither is an inbound-link target); facet note in both; rank correction in both twins. ✓

## 7. Are the new gates real? — each broken, each went red

| Gate | Mutation applied | Result |
|---|---|---|
| DOCS-01 sweep | appended `national rank 1 = lowest reported rate` to `rankings.astro` | **RED**, exit 1, names the file. Restored. |
| DOCS-01 sweep breadth | — | reports "swept **117** source files under site/src" (RR-H2 fix real: `.ts`/`.tsx` now covered, so `comparisonProse.ts` is guarded). |
| DOCS-03 | `granite`/`Granite` → `XXX` in `data/SOURCES.md` | **RED**, exit 1. Restored, `git status` clean. |
| `coverage.mjs` assertion F | `id="national-mean"` → `id="zzz"` in dist | **RED** — "EN methodology page missing id=\"national-mean\"". Restored. |
| `facets.mjs` assertion 23 | removed `id="news-facet-semantics"` from EN dist | **RED**, names the page. Restored. |
| `facets.mjs` assertion 23b | copied EN note text over the ES note in dist | **RED** — "byte-identical after whitespace normalization". Restored. |
| `checkF16` chain + vitest 4a–4f | see §5 | **RED on both stub shapes, green on the real file.** |

**All seven gates are falsifiable and fire.** This is a genuinely stronger gate surface than the phase started with.

**The one gate that does not do what its name implies** is the DOCS-01 sweep: it gates the *`1 =` phrasing* of the rank-direction claim, not the *claim*. GAP-1 is the live proof.

### Test 4d's reversed expectation — legitimate de-brittling, not a weakened gate

**Verdict: legitimate de-brittling.** The pre-cycle-2 contract required the literals `sha256` AND `136 of 346`; reformatting to `136/346` or `136 de 346` would have reddened the build against a correct registry entry, reporting only `Missing tokens: []`. That is the mirror-image failure mode (a gate that cannot pass against correct work), and it is the failure mode this repo has repeatedly shipped. Crucially, 4d does **not** stand alone: 4a (token-free filler), 4b, 4c (heading + VHDV + padding) and especially **4e** (200+ chars of plausible prose with a single marker → still `false`) pin the other side, and I re-proved 4c and 4e's shapes independently rather than trusting the suite. The stub-detection contract survives the reversal intact.

Residual, worth recording: `sha256` is no longer individually mandatory, so a registry entry could silently lose its checksum while keeping 3 of 6 markers. That is a narrower loss than the landmine it removed, but it is a real loss.

### Is `figure-registry.mjs` the right home for sitewide prose guards?

**No — it is a design smell, and worth recording for a future phase.** A file whose stated job is "every displayed figure has a registered source in `data/SOURCES.md`" now also owns a 117-file regex sweep of `site/src` for national-rank prose direction. The two concerns share nothing but a process exit code, and the next person hunting a DOCS-01 failure has no reason to look there.

That said, **F-64's reasoning is sound and the outcome is acceptable for now.** F-21 established that "16 validators" is hardcoded across `all.mjs`'s header, `STATE.md`, and the autonomous directive, and that a stale count is a phase defect — so a 17th validator buys a documentation cascade for no additional guarantee. The right future move is a rename/split (`content-claims.mjs` absorbing the DOCS-01/03 blocks) at a moment when a count edit is already being made, not an extra file now. Recorded as debt, not a gap.

## 8. Coverage honesty

`all.mjs` `VALIDATORS` array contains **exactly 16** entries (`structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo, figure-registry, avs-b-budget, freshness, facets`); its header says "run all 16 validation scripts". **No stale validator count.** ✓

INFO-level doc drift (not a gap): `.planning/STATE.md:32` records the 31-04 close as "vitest 55" and `31-REREVIEW.md:312` as "57"; the shipped tree runs **59**. Both are point-in-time records superseded by cycle 2's added tests, but the STATE.md line is the phase's own close figure and is now understated.

## 9. Gate state as executed by me (not as claimed)

| Gate | Expected | Observed |
|---|---|---|
| `npm run build && npm run validate` (one command, per OneDrive rule) | 15/16, freshness sole failure | ✅ **15/16 — `freshness` the ONLY red** ("3.3 days old"), pre-authorized F-19/F-65, not remediated |
| `facets.mjs` | 24 assertions | ✅ "24 assertions passed" (1412 incidents, 8 families) |
| `npm test` (vitest) | 59 | ✅ **59 passed / 6 files** |
| `python -m pytest -q` | 344 / 1 skipped / 1 xfailed | ✅ **344 passed, 1 skipped, 1 xfailed** (Phase 26 `xfail(strict=True)` quarantine — untouched) |
| `forbidden-language.mjs` | green | ✅ 835 pages, 0 forbidden terms |
| `git status --porcelain` | only the 2 untracked review files | ✅ exactly those two; every mutation restored |

---

## Verdict

**FAILED — 3/5 success criteria.** The phase did the hard part well: the ground truth was re-derived from the normalizer rather than assumed, four inverted claims were corrected in both locales with matching semantics, `data/SOURCES.md`'s News section is now accurate down to the function name, the ENUSC vintage was resolved honestly rather than fabricated, the F16 stub hole is genuinely closed (I re-proved it by mutation), all six inbound anchors survive into `dist/`, and all seven new gates fire when broken. Cycle 2's de-brittling was correct.

But the phase's promise is that **no reader-facing claim contradicts the running system**, and two claims still do:

1. **GAP-1** — the fifth inverted rank sentence, live in `dist/is-santiago-safe/index.html` twice. The sitewide guard was the phase's answer to "two agents swept and still missed one"; it has the same blind spot, one phrasing over.
2. **GAP-2** — the facet note the phase itself wrote asserts unfiltered counts where the code implements self-exclusion. A documentation phase shipping a fresh prose-vs-computation contradiction is the defect class it was chartered to remove.

Both are one-sentence fixes plus one regex extension. Neither is architectural. Recommend a short gap-closure cycle rather than a re-plan.

---

_Verified: 2026-08-02 — every claim above established by executing commands against the shipped tree; no SUMMARY.md assertion was accepted as evidence._
_Verifier: Claude Opus 5 (gsd-verifier)_

---

# Re-verification (post-89a52a7)

**Re-verified:** 2026-08-03 · **Commit under review:** `89a52a7` (3 files, +14/−3) · **Verifier:** Claude Opus 5 (gsd-verifier, FORCE stance, independent re-derivation)
**Result: PASSED — 5/5 success criteria.** Both gaps closed in source AND in `dist/`, in both locales. No regression introduced. No sixth inverted claim found. Two non-blocking WARNINGs recorded.

Nothing below was accepted from the fix commit message; every line is a command result against the shipped tree.

## R1. GAP-1 — closed

`site/src/pages/is-santiago-safe.astro:53` now reads:

> "A national rank closer to 1 indicates a **higher** reported rate, not a lower one — rank 1 is the commune with the most reported crime."

| Check | Result |
|---|---|
| Old sentence in source | absent |
| Old sentence anywhere in `dist/` (`grep -rl "indicates a lower reported rate" site/dist`) | **0 files** |
| New sentence in `dist/is-santiago-safe/index.html` | **2** occurrences — rendered FAQ prose + FAQPage JSON-LD `mainEntity`, i.e. both reader-facing surfaces the defect occupied |
| Factual check vs `pipeline/cead/normalizer.py:111-141` | `sorted(eligible_indices, key=_latest_rate, reverse=True)` then `enumerate(..., start=1)`; docstring "Rank by rate_per_100k descending (highest rate = rank 1)". **Rank 1 = highest reported rate. The sentence is now correct**, and it explicitly negates the old claim ("not a lower one") rather than merely deleting it. |
| `forbidden-language.mjs` — letter | **PASS, 835 pages, 0 forbidden terms** |
| `forbidden-language.mjs` — spirit | Keeps "reported" framing throughout, makes no absolute safety verdict, and the answer attributes CEAD in its first sentence. No superlative safety claim. Clean. |

INFO (not a gap): "the commune with the **most reported crime**" is a count-flavoured phrasing for what is a per-100k *rate*. It is the phrasing already approved and shipped on `methodology.astro:337`, so it is consistent sitewide; noted only so a future editor tightens both together, not one.

## R2. GAP-2 — closed, and the new wording is TRUE of the code

New EN (`i18n.ts:380`) / ES (`:614`):

> EN — "Each filter's per-option counts reflect the other filters you have applied, but not that filter's own selection — so you can always see what widening a selection would return."
> ES — "Los conteos de cada filtro reflejan los demás filtros que hayas aplicado, pero no la selección propia de ese filtro, de modo que siempre puedas ver qué aparecería al ampliar una selección."

Checked against the code, not against the commit message:

- `newsFilterLogic.ts:161-183` `cardMatchesFilters(card, active, newestDate, excludeDimension)` — each of `family`, `region`, `window` is applied **only when it is not the excluded dimension**; `q` is applied unconditionally.
- `newsFilterLogic.ts:193-219` `computeFacetCounts` calls it with `dimension` as `excludeDimension`, then tallies per key.
- Therefore a facet's counts **do** reflect every other active filter and **do not** reflect its own selection. The new sentence states exactly that. The old "unfiltered" claim is gone from source and from `dist/` in both locales (`grep -rl` returns 0 files for both the EN and the ES old string).
- The `q` search box is not a facet and has no per-option count, so its unconditional application does not contradict the note.
- New wording present in built HTML: `dist/news/index.html` 1×, `dist/es/noticias/index.html` 1×.

**EN/ES say the same thing, remain non-identical, and 23b can still fire — proven by mutation:** copied the EN note text (558 chars) over the ES note (644 chars) in `dist/es/noticias/index.html` and re-ran `facets.mjs`:

```
FAIL facets: assertion 23b — EN and ES facet-semantics notes are byte-identical
after whitespace normalization (untranslated ES string, i18n VALUE-parity regression)
```

Restored by rebuild; `facets.mjs` back to **24 assertions passed**.

## R3. Did the fix introduce anything? — the new regex, tested in both directions

The added guard is `INVERTED_PATTERNS[2]`:

```
/(closer to 1|cercano a 1|mas cerca de 1|lower (national )?rank)[^.]{0,80}(lower|menor|mas baja|mas bajo)[^.]{0,40}(reported|reportada|rate|tasa|incidence|incidencia)/i
```

It runs over the same 117-file sweep (`.astro`/`.ts`/`.tsx` under `site/src`) — confirmed: `[DOCS-01] swept 117 source files`, exit 0 on the shipped tree.

**(a) Does it still catch all FIVE inverted claims?** Each re-introduced one at a time into its own page, `figure-registry.mjs` run, file restored:

| # | Sentence re-introduced | Into | Exit | Names the file? |
|---|---|---|---|---|
| 1 | `Rank 1 = lowest reported rate in Chile for that year.` | `methodology.astro` | **1** | yes |
| 2 | `Ranking 1 = menor tasa reportada en Chile...` | `es/metodologia.astro` | **1** | yes |
| 3 | `National rank 1 = lowest reported rate among all non-low-population communes...` | `safest-cities-in-chile.astro` | **1** | yes (2 patterns fire) |
| 4 | `Rango nacional 1 = tasa mas baja reportada...` | `es/comunas-mas-seguras-chile.astro` | **1** | yes |
| 5 | `A lower national rank (closer to 1) indicates a lower reported rate.` | `is-santiago-safe.astro` | **1** | yes — matched by the NEW pattern |

All five. The new pattern additionally fires on prose variants the original never took: `Un rango cercano a 1 indica una menor tasa reportada.` and `A lower rank means a lower reported incidence.` — so it does generalise past the one sentence it was written for.

**(b) Does it false-positive on legitimate pages?** No instance in the corpus (117 files, exit 0). Five realistic legitimate sentences injected one at a time into the five named pages, each followed by a validator run and a restore:

| # | Sentence | Page | Result |
|---|---|---|---|
| L1 | "Several communes report a lower reported rate than the national average, and their national rank reflects that." | `is-chile-safe.astro` | GREEN |
| L2 | "Vitacura shows a lower reported rate of theft than the Santiago average." | `is-santiago-safe.astro` | GREEN |
| L3 | "Communes near the bottom of the national rank list have a lower reported incidence." | `safest-cities-in-chile.astro` | GREEN |
| L4 | "Sorting ascending puts the lower reported rates first; the national rank column is unaffected." | `rankings.astro` | GREEN |
| L5 | "Estas comunas presentan una menor tasa reportada que el promedio nacional." | `es/comunas-mas-seguras-chile.astro` | GREEN |

**WARNING-1 (not a blocker).** The pattern matches **co-occurrence, not assertion**. A synthetic sentence that merely mentions both concepts without equating them reddens the build:

> L6 into `rankings.astro`: "A lower national rank is shown next to each commune, and a lower reported rate is shown in the adjacent column." → **exit 1**, `FAIL [DOCS-01] ... prose-form rank-direction claim`.

So does a *negated* correct sentence ("Communes with a lower national rank number are **not** necessarily those with a lower reported rate"). This is the same trap F-63/RR-H1 was written to avoid, one shape over. Not a blocker because (i) no such sentence exists anywhere in the 117-file corpus, (ii) it fails **loud** — the failure mode is a build that stops on correct prose, not wrong content shipping silently, and (iii) the wrong "fix" (weakening the guard) is now recorded here as the wrong move. Debt alongside F-73.

**WARNING-2 (not a blocker).** The corrected `is-santiago-safe` sentence clears the pattern's `[^.]{0,40}` tail window by **3 characters** (`lower` → `reported` is 43 apart; the limit is 40). Any reword that shortens "one — rank 1 is the commune with the most" by four characters turns the *correct* sentence into a build failure. Fragile by construction; noted so the next editor of that FAQ answer knows the guard is watching that exact clause spacing.

## R4. Independent sweep for a SIXTH inverted claim — none found

Treated "clean" as a hypothesis. Twelve patterns over **118** files (`site/src`, `.astro`/`.ts`/`.tsx`/`.js`/`.mjs`/`.json`/`.md`, whitespace-normalized and accent-stripped), plus four patterns over all **835** built HTML pages in `dist/`. Patterns recorded verbatim so the coverage is auditable:

| # | Shape | Pattern |
|---|---|---|
| P1 | rank noun → inverted direction (EN) | `(national[_ ]?rank\|rank(ing)?\|position)[^.]{0,120}\b(lowest\|safest\|least\|lower reported\|safer\|fewest)\b` |
| P2 | inverted direction → rank 1 (EN) | `\b(lowest\|safest\|least\|fewest\|lower)\b[^.]{0,120}(rank(ed\|ing)?\s*#?\s*1\|rank 1\|number one\|top of the ranking\|first)` |
| P3 | rank noun → inverted (ES) | `(rango\|ranking\|posicion\|puesto\|lugar)[^.]{0,120}(mas segur\|menor\|minim\|mas baja\|mas bajo\|baja incidencia)` |
| P4 | inverted → rank (ES) | `(mas segur\|menor incidencia\|menor tasa\|mas baja)[^.]{0,120}(rango\|ranking\|posicion\|puesto\|#1\|numero 1)` |
| P5 | "closer to 1" family | `(closer to (number )?1\|cercano a 1\|mas cerca de 1\|approaching 1\|proximo a 1)` |
| P6 | "lower rank means/indicates" | `(lower\|menor\|mas bajo\|mas baja) (national )?(rank\|rango\|ranking\|posicion)[^.]{0,60}(means\|indicates\|implica\|significa\|equivale\|refleja\|=)` |
| P7 | "cuanto más bajo / mientras menor" | `(cuanto mas baj\|cuanto menor\|mientras menor\|mientras mas baj\|entre mas baj)` |
| P8 | symbolic `rank 1 =` / `rank 1:` | `(rank\|rango\|ranking\|posicion\|puesto)\s*#?\s*1\s*[:=]` |
| P9 | "the lower the rank, the safer" | `(the (higher\|lower) the (rank\|number))[^.]{0,80}(safer\|safest\|lower\|higher\|menor\|mayor)` |
| P10 | rank + safety adjective adjacency | `(rank\|rango\|ranking\|posicion)[^.]{0,60}(seguridad\|segura\|seguro\|safe\|safety)` |
| P11 | comparative "better/worse rank" | `(better\|mejor\|peor\|worse) (rank\|rango\|ranking\|posicion\|puesto)` |
| P12 | rank 1 explicit best/worst | `(rank\|rango\|ranking\|puesto)\s*#?\s*1[^.]{0,60}(best\|mejor\|worst\|peor\|safest\|mas segura)` |

**Every P8 hit read in full — all eleven `1 =` sites state the direction CORRECTLY:** `comparisonProse.ts:198,209` (`rank 1 = highest reported incidence`, incl. the regional variant), `:287,299` (`posición 1 = mayor incidencia reportada`), `compare/[pair].astro:232,246`, `es/comparar/[pair].astro:230,244`, `commune/[slug].astro:100` and `es/comuna/[slug].astro:102` (code comments: "DESCENDING (rank 1 = highest incidence)"), `methodology.astro:337`, `es/metodologia.astro:350`, `safest-cities-in-chile.astro:175`, `es/comunas-mas-seguras-chile.astro:162`.

**P7, P9, P11 and P12 returned zero hits sitewide.** P5's only hit is the corrected Santiago sentence. P1/P2/P3/P4/P10 hits were all read and are legitimate low-rate prose, page titles, or the correct "not safest" contrast clauses.

**i18n strings audited directly** (the surface no page-level grep covers): `rank_sublabel` EN `'CEAD {year} · #{rank} of {total} · 1 = most reported incidence'` / ES `'… 1 = mayor incidencia reportada'` — correct and mutually consistent; `rank_pct_value` EN `'More reported crime than {pct}%'` / ES `'Más delitos reportados que el {pct}%'` — correct; `ci_rank_national/regional`, `th_rank`, `national_rank_label`, `regional_rank_label` carry no direction claim. **`proseEngine.ts:58-61`** `rank 1 = HIGHEST reported incidence … rank total = LOWEST` — correct; its `bottom10` templates (`:136,148,160,290`) state low incidence and quote the rank number without asserting a direction, which is consistent, not inverted.

**`dist/` (835 pages)** scanned for the symbolic inverted form, the `closer to 1` prose form, the "lower rank means" form and the "cuanto más bajo" form: **zero hits except the corrected Santiago sentence.**

**Conclusion: no sixth instance.** Stated with the F-70 caveat that a grep returning 0 is evidence about the grep — which is why the patterns are recorded above, why they are shape-based rather than phrasing-based, why each of the eleven `1 =` sites was read rather than counted, and why i18n and `dist/` were swept separately from `src/pages`.

## R5. Full gate, executed by me

| Gate | Expected | Observed |
|---|---|---|
| `npx astro check` | 4 errors / 0 warnings, all `ComparatorPairsLinks.astro:28` | **4 errors / 0 warnings / 43 hints**; all four are `ts(7031)` implicit-any on `ComparatorPairsLinks.astro:28` (`cutA`, `cutB`, `nameA`, `nameB`) — baseline, untouched |
| `npx vitest run` | 59 | **59 passed / 6 files** |
| `npm run build && npm run validate` (one command, OneDrive rule) | 15/16, `freshness` sole failure | **15/16 — `freshness` the ONLY red** ("3.3 days old"), pre-authorized F-19/F-65 |
| `facets.mjs` | 24 assertions | 24 assertions passed (1412 incidents, 8 families) |
| `figure-registry.mjs` standalone | green, 117-file sweep | exit 0, "swept 117 source files under site/src" |
| `forbidden-language.mjs` | 835 pages / 0 terms | **835 pages scanned, 0 forbidden terms** |
| `python -m pytest -q` | 344 / 1 skipped / 1 xfailed | **344 passed, 1 skipped, 1 xfailed** (Phase 26 quarantine intact) |

## R6. Could the fix have disturbed SC2 / SC3 / SC5 / DOCS-03 / 05 / 06?

`git show 89a52a7` (full diff read, not the stat line) touches exactly three files: `site/scripts/validate/figure-registry.mjs` (+11, **all inside the `INVERTED_PATTERNS` array** — no change to `checkF16`, the lib module, the DOCS-03 block, or the sweep root), `site/src/config/i18n.ts` (two string values), `site/src/pages/is-santiago-safe.astro` (one string).

- **DOCS-03 / SC3** — `data/SOURCES.md` not in the diff; `figure-registry`'s DOCS-03 assertions still PASS (Google News / Granite / R2). Untouched.
- **DOCS-05 / SC5** — `checkF16` and `figure-registry.lib.mjs` not in the diff; vitest 59/59 including the stub-detection specs. Untouched.
- **DOCS-06** — no anchor in the diff; re-checked in the **freshly built** tree: `#trend-formula`, `#comparison-criteria`, `#national-mean` present in `dist/methodology/index.html`; `#trend-formula`, `#comparison-criteria`, `#media-nacional` present in `dist/es/metodologia/index.html`. All 6 resolve.
- **DOCS-02 / SC2** — the only new reader-facing prose is the two i18n strings and the Santiago sentence; `forbidden-language.mjs` green on 835 pages and each sentence read for spirit (reported-framing, no absolute verdict).

## R7. Working-tree state

`git status --porcelain` at close:

```
 M .planning/STATE.md
?? .planning/phases/31-docs-methodology-refresh/31-REREVIEW.md
?? .planning/phases/31-docs-methodology-refresh/31-REVIEW.md
?? .planning/phases/31-docs-methodology-refresh/31-VERIFICATION.md
```

Every mutation I applied (5 inverted re-introductions, 6 legitimate injections, the 23b `dist` overwrite) was restored — verified file-by-file; `dist/` was fully rebuilt after the 23b mutation.

`.planning/STATE.md` is **not my mutation**: `git diff --stat` shows **5 insertions, 0 deletions**, and the added lines are the orchestrator's own decision records **F-70…F-74**, written after `89a52a7` and landing in the working tree via OneDrive sync. Left in place deliberately — reverting would destroy the orchestrator's uncommitted work. It should be committed together with this verification.

## Verdict

**PASSED — 5/5 success criteria.** SC1 and SC4 are now genuinely satisfied: the fifth inverted claim is gone from source and from both of its `dist/` surfaces and the replacement is factually correct against `normalizer.py`; the facet note now describes F-28 self-exclusion, which is what `cardMatchesFilters` / `computeFacetCounts` actually implement, in both locales, still non-identical and still gated by a 23b assertion I re-proved can fire. The new guard catches all five historical instances plus prose variants they never took, and stays quiet on five realistic legitimate sentences injected into the five pages most likely to trip it. An independent twelve-pattern sweep of 118 source files plus 835 built pages, with every `1 =` site read in full, found no sixth instance. The full gate matches the expected close state exactly, with `freshness` the sole pre-authorized red.

Two warnings are recorded rather than fixed: the new pattern matches co-occurrence rather than assertion (so a negated or merely-adjacent correct sentence would redden the build), and the corrected Santiago sentence clears the pattern's window by three characters. Both fail loud rather than ship silently, and neither has a live instance — they are debt for the F-73 split, not gaps.

---

_Re-verified: 2026-08-03 — every claim above established by executing commands against the shipped tree; no SUMMARY.md or commit-message assertion was accepted as evidence._
_Verifier: Claude Opus 5 (gsd-verifier)_
