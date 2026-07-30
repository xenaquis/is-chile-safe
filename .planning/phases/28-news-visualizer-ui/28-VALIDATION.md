---
phase: 28
slug: news-visualizer-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `28-RESEARCH.md` § Validation Architecture, amended by Fable decisions **F-27** (the shipped filter logic must BE the unit-tested module, imported — not a copy-pasted twin) and **F-28** (facet counts use self-exclusion semantics).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (already installed; `site/src/lib/newsFacets.test.ts` is the existing real spec, 20 tests) |
| **Config file** | existing `site/vitest.config.*` — unmodified by this phase |
| **Quick run command** | `cd site && npx vitest run src/lib/newsFilterLogic.test.ts src/lib/newsFacets.test.ts` |
| **Full suite command** | `cd site && npm run build && npm test && npm run validate` |
| **Estimated runtime** | ~25s build + ~5s vitest + ~10s validators ≈ 40s |

**VERIFIED, and binding on every plan:** `npm run validate` does **not** invoke vitest — `package.json` defines `validate` (`node scripts/validate/all.mjs`) and `test` (`vitest run`) as separate scripts. Any gate that runs only `npm run validate` leaves the entire vitest suite unrun. All three must be chained in ONE command, both because of that and because of the OneDrive `dist/` desync rule.

**Exit-code hygiene (directive Operating Lesson 8 / F-22).** No `<automated>` verify block in any Phase 28 plan may route a gate command through `| tail`, `| head`, `; echo`, or `|| echo`. `cmd | tail` reports `tail`'s status, which is always 0. Any plan containing that pattern inside a verify block is rejected at review.

---

## Sampling Rate

- **After every task commit:** `cd site && npx vitest run src/lib/newsFilterLogic.test.ts src/lib/newsFacets.test.ts`
- **After every plan wave:** `cd site && npm run build && npm test && npm run validate` (chained, one command)
- **Before verification:** full suite green — all 16 validators (F-19's freshness exclusion is the only admissible red) + vitest + the Python `pytest` baseline (344 passed / 1 skipped / 1 xfailed) unchanged
- **Max feedback latency:** ~10s per task, ~40s per wave

---

## Per-Task Verification Map

Task IDs are assigned by the planner; this map fixes the requirement→layer→command mapping the planner must honor.

| Requirement | Behavior to prove | Test Type | Automated Command | File Exists |
|---|---|---|---|---|
| NEWSUI-01 | Server-side unfiltered marginal facet counts (unchanged F-20 contract) | unit | `npx vitest run src/lib/newsFacets.test.ts` | ✅ existing |
| NEWSUI-01 | Cross-filtered per-option counts with **F-28 self-exclusion** | unit | `npx vitest run src/lib/newsFilterLogic.test.ts` | ❌ Wave 0 |
| NEWSUI-01 | Filter controls + counts rendered on BOTH pages | build validator | `node scripts/validate/facets.mjs` (new assertion, both locales) | ❌ Wave 0 |
| NEWSUI-02 | Full unfiltered incident superset in static HTML | build validator | `node scripts/validate/facets.mjs` — card count in each dist page equals `current.json` incident count | ❌ Wave 0 |
| NEWSUI-02 | No island / no hydration added | build validator | assert neither dist news page contains `astro-island` | ❌ Wave 0 |
| NEWSUI-03 | Accent-insensitive comuna matching | unit | `npx vitest run src/lib/newsFilterLogic.test.ts` (the `norm()` + match predicate lives in the module) | ❌ Wave 0 |
| NEWSUI-03 | Typeahead wired to the rendered control | build validator | `#news-comuna-q` present in both dist pages | ❌ Wave 0 |
| NEWSUI-04 | Query-param parse/serialize round-trip | unit | `npx vitest run src/lib/newsFilterLogic.test.ts` (pure `parseFilterParams`/`serializeFilterParams`) | ❌ Wave 0 |
| NEWSUI-04 | Empty-state node exists, ships `hidden`, is not a heading | build validator | `facets.mjs` new assertion on both dist pages | ❌ Wave 0 |
| NEWSUI-04 | No new indexable URL; canonical unchanged | build validator | dist file count unchanged ± the 0 new routes; canonical in both news pages still the bare path | ❌ Wave 0 |
| NEWSUI-05 | Faceting-only; no cluster markup shipped | build validator | assert neither page's source nor dist contains a cluster/source-count badge element | ❌ Wave 0 |
| NEWSUI-06 | `#news-facets` payload still escaped at source | build validator | `facets.mjs` assertion 7 (existing, source-level, both locales) — extends automatically to any new field on the same object | ✅ existing |
| NEWSUI-06 | No `innerHTML` with data-derived strings | build validator | source-level assertion over the two pages + `newsFilterLogic.ts` | ❌ Wave 0 |
| NEWSUI-07 | EN/ES parity for all new `news_*` keys | build validator | `facets.mjs` (or a new validator) — every new key present in BOTH `EN_STRINGS` and `ES_STRINGS` | ❌ Wave 0 |
| all | astro check baseline unchanged | CLI | `npm run check` → exactly **4 errors, 0 warnings** (pre-existing, all in `scripts/validate/*.mjs`) | ✅ measured |

*Status column is filled by the executor during the run.*

---

## Wave 0 Requirements

- [ ] `site/src/lib/newsFilterLogic.ts` — the ONE module holding every pure predicate: window-bucket boundary math, `norm()` accent strip, comuna match, param parse/serialize, and the F-28 self-exclusion count routine. **Both pages' inline `<script>` blocks import it (F-27); no copy-pasted twin.**
- [ ] `site/src/lib/newsFilterLogic.test.ts` — vitest spec for that module.
- [ ] `site/scripts/validate/facets.mjs` — extended with the new assertions above (or a new sibling validator registered in `all.mjs`; if a new validator is added, the validator count moves from 16 to 17 and **every** hardcoded "16" must be corrected in the same commit — see F-21, which made a stale count a phase defect).
- [ ] Framework install: none — vitest is already present.

**Falsifiability is mandatory (Operating Lessons 9 + 11).** For every new assertion, the plan must state the counterexample and the executor must demonstrate RED before restoring:

| New assertion | Counterexample that MUST make it exit non-zero |
|---|---|
| `anchorDate` correctness | Move the newest fixture incident's date back one day; the rendered `anchorDate` no longer equals the independently recomputed max → RED |
| card-count == incident-count | Render with one incident dropped → RED. (Match `class="news-card"` on the opening tag, not a bare substring, or the assertion silently counts attribute text.) |
| EN/ES key parity | Delete one `news_*` key from `ES_STRINGS` → RED |
| empty-state node | Remove `hidden` from `#news-empty`, or delete the node → RED |
| no-island | Insert any `client:` directive on either page → RED |
| no cluster markup | Add a source-count badge element → RED |
| 7-day window boundary width | Change the window width from 7 to 6 days in `newsFilterLogic.ts` → RED (Phase 27 shipped a 7-day window whose boundary width was completely unpinned while the 30-day twin was pinned — do not repeat it) |
| F-28 self-exclusion | Switch the count routine to apply the dimension's own filter → RED (a fully-filtered count differs from a self-excluded one whenever ≥2 options in that dimension are non-empty) |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Typeahead + filter interaction end-to-end in a real browser | NEWSUI-01, -03, -04 | No DOM-interaction harness (Playwright / Testing Library) exists in this repo for `.astro`-rendered pages, and introducing one is outside this phase's scope and its zero-new-dependency constraint | `cd site && npm run build && npx astro preview --port 4321 --host`, then exercise both `/news/` and `/es/noticias/`: apply each dimension, confirm counts update per F-28, confirm the URL round-trips on reload, confirm the empty state appears and month headings collapse |
| JS-disabled superset visibility | NEWSUI-02 | Real proof needs a browser with JS off; the validator's card-count assertion covers the static-HTML half | Load `/news/` with JS disabled; every incident remains visible and no filter control is broken-looking |
| No perceptible CLS | NEWSUI-06 | Visual/temporal property | Observe first paint; the `<details>` ships `open` and no JS adds or removes it, so there must be no post-paint reflow |

The interactive halves are automated-adjacent, not automated: the plan must not claim NEWSUI-01/03/04 are fully automated. Their **logic** is unit-tested and their **presence** is validator-gated; only the interaction is manual.

---

## Validation Sign-Off

- [ ] Every task has an `<automated>` verify block or an explicit Wave 0 dependency
- [ ] No `<automated>` block launders an exit code through `| tail`, `| head`, `; echo`, or `|| echo`
- [ ] Sampling continuity: no 3 consecutive tasks without an automated verify
- [ ] Wave 0 covers every ❌ above
- [ ] No watch-mode flags (`vitest run`, never bare `vitest`)
- [ ] Every new assertion has a demonstrated RED counterexample
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
