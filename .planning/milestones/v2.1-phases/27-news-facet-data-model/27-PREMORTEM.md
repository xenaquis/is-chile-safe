---
phase: 27-news-facet-data-model
type: premortem
model: opus
created: 2026-07-30
status: amendments-pending
---

# Phase 27 — Premortem

> Premise: **Phase 27 has failed.** Below are the concrete, evidence-grounded ways it happened.

---

## Verdict — most likely single cause of failure

**Phase 27 stalls the unattended run on a validator that has nothing to do with faceting: `freshness.mjs` goes red at `2026-07-30T14:25:05Z`, roughly eight hours from the moment this premortem was written.** `data/incidents/current.json` was generated `2026-07-27T14:25:05.303451Z`; `freshness.mjs` hard-fails at `MAX_AGE_DAYS = 3` (`site/scripts/validate/freshness.mjs:27,80-91`); a live run right now prints `PASS freshness: ... is 2.6 days old`. Phase 27's close gate (27-02 Task 2) requires *all* validators green, the directive forbids `git push` and mutation of `data/`, and the only real fix — running the news cron — is outside this phase and outside the run's permissions. So the phase will do all its work correctly, then fail its own closing assertion for an unrelated reason, and the executor's most likely reactions are all bad: weaken `MAX_AGE_DAYS`, regenerate `current.json` (mutating read-only `data/`), or halt the run. Secondary and nearly as likely: the plan asks the executor to assert an arithmetically impossible test case (27-01 Task 1, Test 4 — see FM-2), which forces either a silently-dropped test or a corrupted 30-day window definition.

---

## Failure modes

### FM-1 — `freshness.mjs` turns the phase-close gate red today, for reasons Phase 27 cannot fix

**Severity: CRITICAL**

**Evidence.**
```
$ node site/scripts/validate/freshness.mjs
PASS freshness: data/incidents/current.json is 2.6 days old (generated: 2026-07-27T14:25:05.303451Z)
$ node -e "..." → fails after 2026-07-30T14:25:05.303Z    (now: 2026-07-30T05:46:43Z)
```
- `site/scripts/validate/freshness.mjs:27` — `const MAX_AGE_DAYS = 3;`
- `site/scripts/validate/freshness.mjs:80-91` — `if (ageDays > MAX_AGE_DAYS) { ... process.exit(1) }`
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:77` — "Every phase leaves the frontend validators **and** the pytest suite green before being marked complete."
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` hard rules — no `git push`; "No mutation of `data/`"; no `workflow_dispatch` triggers. The news cron is remote and cannot be triggered.
- Memory `news-cron-billing-outage`: the cron has silently died before, for a full week.

**How it would go undetected / go wrong.** It will *not* go undetected — it will be loud. The danger is the executor's remediation. A Sonnet executor facing "16/16 required, freshness FAILS" has three cheap outs, and all three are damaging: (a) bump `MAX_AGE_DAYS` to 7 — silently disables the project's only cron-death alarm, the exact regression Phase 32/33 exists to prevent (STATE.md § Critical Pitfalls, "[Phase 32/33] Cron billing-lapse … already happened once"); (b) re-run the news pipeline to refresh `current.json` — mutates read-only `data/` and burns LLM budget unattended; (c) declare the phase blocked — stalls a run whose facet work is actually complete. Note also that `all.mjs` does **not** abort on first failure (`site/scripts/validate/all.mjs:71-77`) but does `process.exit(1)` at the end, so the summary will read `15/16` with `facets` green and `freshness` red — maximally confusing for an agent whose success criterion is the literal string "16/16".

**AMENDMENT.** Add to `27-02-PLAN.md` Task 2, before the gate command, as an explicit pre-declared branch (do not leave this to executor judgement):

> **Pre-declared freshness branch (F-NN candidate).** `data/incidents/current.json` was generated `2026-07-27T14:25:05Z`. `freshness.mjs` fails once age > 3 days, i.e. after `2026-07-30T14:25:05Z`. This is a **cron-liveness signal about production, not a Phase 27 regression** — Phase 27 touches zero data files.
> - Run the gate as `cd site && npm run build && npm run validate` and capture the full summary block.
> - **If the only failing validator is `freshness`**: the phase closes GREEN on a `15/16 (freshness excluded)` basis. Record it verbatim in `27-02-SUMMARY.md` and add a `## Blockers` entry in `.planning/STATE.md`: *"news cron stale since 2026-07-27T14:25Z; `freshness.mjs` red from 2026-07-30T14:25Z onward; owner action = re-run news cron on return (add to deferred-live list). Phase 27+ close gates read as N-1/N until then."* Also append it to the directive's deferred-live list.
> - **You MUST NOT**: change `MAX_AGE_DAYS`, edit/regenerate any file under `data/`, add a skip/env-guard to `freshness.mjs`, or remove it from `VALIDATORS`. Any of these is an immediate stop-and-record.
> - If **any validator other than `freshness`** fails, that IS a Phase 27 regression — fix it.

Also amend the same phrasing into `27-VALIDATION.md` ("Before `/gsd:verify-work`") and into `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` § Hard safety rules, since phases 28–33 inherit the identical problem and will each rediscover it.

---

### FM-2 — 27-01 Task 1 Test 4 asserts something arithmetically false; making it pass corrupts the 30-day window

**Severity: HIGH**

**Evidence.** `27-01-PLAN.md`, Task 1 `<behavior>` Test 4:
> "Given incidents dated `2026-07-28`, `2026-07-25`, `2026-06-01`, and newest date `2026-07-28`: … `byWindow.thirtyDay` contains all three if within 30 days of `2026-07-28` (**assert the `2026-06-01` incident IS included**)"

```
$ node -e "console.log((new Date('2026-07-28')-new Date('2026-06-01'))/86400000)"
57
```
57 days. The same task's `<action>` says `thirtyDay = within 29 days after today`. The fixture is 57 days out. The assertion is unsatisfiable under the plan's own definition.

**How it would go undetected.** The plan explicitly permits the test to be "folded into `facets.mjs`" if no runner exists, and `facets.mjs` runs against real data where the fixture never appears. So the contradiction resolves itself by evaporating: the executor writes a throwaway script, hits the failure, and either (a) widens `thirtyDay` until it passes — silently making "30 days" mean "unbounded", which then silently makes `byWindow.thirtyDay === incidents` for all time and quietly satisfies the "equals the full `current.json` set today" line in Planning Decision 1 for the *wrong* reason; or (b) drops the case as "environmental". Neither leaves a trace. The acceptance criterion ("paste its console output") is satisfiable by pasting output from whichever version passed.

**AMENDMENT.** Replace Test 4 verbatim in `27-01-PLAN.md` with a fixture that actually exercises the boundary:

> - Test 4: Given incidents dated `2026-07-28`, `2026-07-25`, `2026-06-29`, `2026-06-28` and a wall-clock date far from all of them: `newestDate` resolves to `2026-07-28`; `byWindow.today` = the `2026-07-28` incident only (1); `byWindow.sevenDay` = the `2026-07-28` + `2026-07-25` incidents (2); `byWindow.thirtyDay` = the `2026-07-28`, `2026-07-25`, `2026-06-29` incidents (3) and **excludes** `2026-06-28` (day 30 exclusive of the anchor per the "within 29 days" rule). Assert `byWindow.thirtyDay.length === 3`, i.e. the window is a real boundary, not a pass-through of `incidents`.
> - Test 4b (anti-pass-through guard): assert `byWindow.thirtyDay.length < incidents.length` for this fixture. This case must remain in whatever durable test artifact ships — if it is folded into `facets.mjs`, `facets.mjs` must construct this synthetic array in-memory rather than relying on real data (real `current.json` spans `2026-06-29..2026-07-27` = 28 days, so it can never falsify a broken 30-day window).

Evidence the real data cannot catch it:
```
$ node -e "...current.json..." → minDate 2026-06-29  maxDate 2026-07-27   (n=1215)
```
28 days of span — every incident falls inside any window ≥ 28 days. `thirtyDay` returning the whole array is indistinguishable from correct against production data.

---

### FM-3 — Plan 02's verify command is `npx astro build`, which skips `prebuild` *and* `ROLLOUT_ALL=true`

**Severity: HIGH**

**Evidence.** `site/package.json`:
```json
"prebuild": "node ../scripts/generate-pairs.mjs && node scripts/sync-data.mjs",
"build": "cross-env ROLLOUT_ALL=true astro build",
```
`27-02-PLAN.md` Task 1 `<verify><automated>`: `cd "...\site" && npx astro build 2>&1 | tail -20`, and its acceptance criterion: `cd site && npx astro build` completes with exit 0.

`npx astro build` invokes the Astro binary directly. It does **not** run the npm `prebuild` lifecycle hook and does **not** set `ROLLOUT_ALL`.

**Consequences, all silent:**
1. **`sync-data.mjs` never runs**, so `site/public/data/` is whatever a previous build left there. It is gitignored (`site/.gitignore:3` → `public/data/`, confirmed via `git check-ignore -v site/public/data/incidents/current.json`). On a fresh clone or in CI, `site/public/data/incidents/current.json` does not exist → `existsSync(dataPath)` at `site/src/pages/news.astro:37` is false → `incidents = []` → the page renders the single `.empty-state` paragraph (`news.astro:152-155`) and **the build still exits 0**. This exact class of bug has already shipped in this repo once — memory `news-page-build-path-drift`, and the comment at `news.astro:19-21` is the scar tissue. The Task-1 acceptance criterion "non-empty body content" is satisfied by the empty-state paragraph.
2. **`archiveDir` reads stale/absent data.** `newsFacets.ts` is specified to read `public/data/incidents/archive` — the synced copy. Without `prebuild`, `byMonth` silently reflects whatever is stale on disk, or is `[]`.
3. **`ROLLOUT_ALL` unset produces a partial `dist/`** (a reduced commune set). Combined with the OneDrive gotcha, if anyone runs `npm run validate` against that `dist/`, `rollout.mjs`/`region.mjs`/`avs-b-budget.mjs` fail for reasons entirely unrelated to Phase 27 — a second false-red stall vector on top of FM-1.

**How it would go undetected.** The developer machine has a warm `site/public/data/` (`ls` confirms `current.json` present, 856,437 bytes, same mtime as the repo-root copy) so the local run looks fine. The failure only manifests in CI/fresh-clone — i.e. on the Cloudflare build that actually serves users. And "the news page went empty" is exactly the regression this repo has silently shipped before.

**AMENDMENT.** In `27-02-PLAN.md` Task 1:
- Replace both occurrences of `npx astro build` with `npm run build` (which runs `prebuild` → `sync-data.mjs` and sets `ROLLOUT_ALL=true`).
- Strengthen the acceptance criterion from "non-empty body content" to a falsifiable count, chained in one command (OneDrive):
  ```
  cd site && npm run build && node -e "const {readFileSync}=require('fs');for(const p of ['dist/news/index.html','dist/es/noticias/index.html']){const h=readFileSync(p,'utf8');const n=(h.match(/class=\"news-card\"/g)||[]).length;console.log(p,'cards:',n);if(n<1000)throw new Error('news cards regressed: '+p+' '+n);if(h.includes('empty-state'))throw new Error('empty-state rendered: '+p);}"
  ```
  (`current.json` currently holds 1,215 incidents, all with a `cut`; a floor of 1000 cards per locale catches both the empty-state regression and the "monthGroups deleted" regression in FM-4.)
- Add a `<read_first>` note: *"`npx astro build` is forbidden in this phase — it bypasses the `prebuild` sync that populates the gitignored `site/public/data/` that `news.astro:22` depends on, and bypasses `ROLLOUT_ALL=true`."*

---

### FM-4 — The hollow-deliverable path: `facets` computed, never rendered, and no assertion anywhere notices

**Severity: HIGH**

**Evidence.** `site/src/pages/news.astro:157` — `Array.from(monthGroups.entries()).map(...)` is the *entire* rendered incident body (lines 157-186). `27-02-PLAN.md` Task 1 tells the executor to "replace the inline `monthGroups` Map-building loop … with a single call", then immediately hedges: "if `monthGroups` was only used to group the CURRENT incidents by month for card display purposes … preserve that specific per-page grouping behavior by deriving it from `incidents` directly (unchanged), and use `facets` purely for the NEW family/region/window/month facet data". Reading the code: `monthGroups` **is** only used for card display. So the correct reading is "change nothing about rendering, add an unused `const facets`".

**How it would go undetected.** Perfectly. `astro check` treats an unused `const` in `.astro` frontmatter as a hint at worst (the 4 real errors are all `ts(7031)` in `ComparatorPairsLinks.astro`, confirmed by running it — nothing in `news.astro`). `facets.mjs` is specified as deliberately independent of the module (re-implemented plain-JS assertions against raw JSON), so it cannot detect that no page consumes `computeNewsFacets`. Both `key_links` patterns (`computeNewsFacets\(`) match. Both `must_haves.artifacts.contains` (`computeNewsFacets`) match. `grep -c "computeNewsFacets"` returns ≥1. FACET-05 ("counts … **available to the UI**") and ROADMAP criterion 1 ("both pages **consume** the exact same module") are satisfied only lexically. The phase closes green having shipped a dead variable.

Note this is *also* the safest outcome — Phase 28 owns the UI, and FACET-06 forbids new artifacts. The problem is not that nothing renders; it is that nothing **proves** the module produces correct values for the real dataset, so Phase 28 inherits an unvalidated dependency.

**AMENDMENT.** Do not force UI (that is Phase 28 scope and would violate the fence). Instead make the unused-ness impossible and the values observable:
1. In `27-02-PLAN.md` Task 1, require both pages to emit the facet index as a single non-indexable, non-visible, machine-checkable node in the rendered HTML — zero visual change, zero new URLs, zero client JS, no file under `site/public/**` (FACET-06 intact):
   ```astro
   <script type="application/json" id="news-facets" set:html={JSON.stringify(facets)} />
   ```
   Use `<script type="application/json">` (inert; not executed, not JSON-LD, not indexed as content) and pass values via `set:html` — Astro renders `{expr}` literally inside `<script>` (memory `astro-script-no-expr-interpolation`), so plain interpolation would silently emit the literal string `{JSON.stringify(facets)}`. Serialize a **counts-only** projection (`byFamily`, `byRegion`, `byMonth`, and `byWindow` reduced to `{today,sevenDay,thirtyDay}` **lengths**) — never the full incident arrays, which would add ~800KB to each page.
2. Add to `facets.mjs` (or a new task in 27-01) a `dist/`-reading assertion — this is the check that closes FACET-01 and FACET-05 for real:
   > Parse `#news-facets` out of both `dist/news/index.html` and `dist/es/noticias/index.html`; assert both parse as JSON, are **deeply equal to each other** (that is the actual no-per-locale-drift test — an identical-looking source line is not evidence), and that `byFamily` sums to the count of incidents with a non-empty `family`.
3. Add a guard to `27-02-PLAN.md` Task 1 acceptance: `grep -c "monthGroups" site/src/pages/news.astro` must still be ≥ 3 and the card-count floor from FM-3 must hold — i.e. the literal-deletion reading of the instruction is mechanically blocked.
4. Rewrite the ambiguous instruction to remove the hedge entirely:
   > "Do **not** modify the `monthGroups` block or any rendering. Leave lines 96-104 and 152-187 of `news.astro` byte-identical (and the ES equivalents). Add only: the two imports, the `archiveDir` const, the `computeNewsFacets(...)` call, and the inert `#news-facets` JSON node."

---

### FM-5 — `vitest ^4.1.9` IS installed; the plan says it is not, and there is no way to run it

**Severity: MEDIUM**

**Evidence.**
- `site/package.json` `devDependencies`: `"vitest": "^4.1.9"`.
- `site/package.json` `scripts`: **no `test` script.**
- `site/src/lib/formatNumber.test.ts` exists and is tracked (`git ls-files 'site/**/*.test.ts'` → one hit).
- No `vitest.config.*` / `vite.config.*` in `site/` (`ls` → No such file).
- `27-VALIDATION.md` Test Infrastructure table: "**No Jest/Vitest configured in `site/`**".
- `27-01-PLAN.md` Task 1 `<action>`: "Add a `.test.ts`/`.spec.ts` file **if the repo has a frontend test runner configured (check `site/package.json` `scripts`/`devDependencies` first)**".

**How it would go undetected.** The executor is instructed to check `devDependencies` — where it will find `vitest`. It concludes a runner exists, writes `site/src/lib/newsFacets.test.ts`, and… nothing ever runs it. It is not in `all.mjs`, there is no `npm test`, and `astro check`'s `include` (`src/**/*.ts`) will type-check it but never execute it. `formatNumber.test.ts` is the proof this already happened once: a test file that has been dead in the tree. The 6 behavior cases would then be "delivered" as a file nobody executes — the purest form of hollow deliverable, and it would read as *stronger* coverage than folding them into `facets.mjs`.

**AMENDMENT.** Two options; take (a).
- **(a) Correct the fact and pick one path explicitly.** Fix `27-VALIDATION.md` to read: *"`vitest ^4.1.9` is present in `site/devDependencies` but there is no `test` script, no vitest config, and the one existing spec (`src/lib/formatNumber.test.ts`) is never executed by any command in this repo."* Then in `27-01-PLAN.md` Task 1, replace the whole conditional with a decision: *"Add `\"test\": \"vitest run\"` to `site/package.json` scripts (one line, zero new dependencies — vitest is already installed), create `site/src/lib/newsFacets.test.ts` with the 6 behavior cases, and append `npm test` to the phase-close gate chain in Plan 02 Task 2. Confirm `formatNumber.test.ts` also passes under it; if it does not, that is a pre-existing red — record it in STATE.md Blockers, do not modify `formatNumber.ts`."* This turns a dead file into the phase's real regression net and is the only way FM-2's boundary cases stay durable.
- **(b) If (a) is rejected as scope creep**, then forbid `.test.ts` outright: *"Do NOT create a `.test.ts` file — nothing executes them in this repo. Write the 6 cases as in-memory synthetic-fixture assertions inside `facets.mjs` itself, guarded behind a `SELFTEST` section that runs unconditionally on every `npm run validate`."*

---

### FM-6 — `byMonth` double-counts June 2026 and omits July 2026: the archive dimension is structurally wrong for Phase 28

**Severity: MEDIUM**

**Evidence.**
```
$ ls data/incidents/archive → 2026-04.json  2026-06.json
$ node -e "..." → 2026-04: {generated,window_days,incidents} incidents:1
                  2026-06: {generated,window_days,incidents} incidents:84
$ node -e "current.json" → minDate 2026-06-29  maxDate 2026-07-27  (n=1215)
```
- Archive holds only **2026-04** and **2026-06**. No `2026-05`, no `2026-07`.
- `current.json` spans `2026-06-29 .. 2026-07-27`, i.e. it **overlaps** the `2026-06` archive month and is the **only** source for July 2026.
- `27-01-PLAN.md` Planning Decision 2: "The archive is a **separate `byMonth` dimension** … never merged into the `current.json`-scoped counts."
- Archive files are objects with an `incidents` array, not bare arrays — the plan never states how to derive `count`.

**How it would go wrong / go undetected.** `byMonth` = `[{2026-06, 84}, {2026-04, 1}]`. A Phase 28 "browse by month" UI built on this: offers **April 2026 (1)** — a one-item thin page; offers **June 2026 (84)** whose items partially duplicate incidents already in the current window; and offers **no July 2026 at all**, despite July being where 1,204 of the 1,215 current incidents live. A user clicking "June 2026" sees a set that overlaps but does not equal what the unfiltered list shows for June. Nothing in the plan detects this: `facets.mjs` is scoped to `current.json` + `index.json` only, and there is no assertion relating `byMonth` to `byWindow`. It surfaces as a Phase 28 UI bug attributed to Phase 28.

**AMENDMENT.** In `27-01-PLAN.md`:
1. Specify the count derivation unambiguously: *"each archive file is `{generated, window_days, incidents: [...]}`; `count = (parsed.incidents ?? []).length`. A file that parses but lacks an `incidents` array counts 0 and is still listed."*
2. Add a third field so the overlap is explicit rather than latent, and Phase 28 cannot get it wrong by accident:
   ```ts
   interface MonthBucket { yearMonth: string; count: number; source: 'archive' | 'current' | 'both' }
   ```
   Build `byMonth` as the **union** of archive months and the months observed in `incidents`, tagging each: archive-only → `'archive'`, current-only → `'current'` (this makes `2026-07` appear), present in both → `'both'` with `count` = archive count **and** an added `currentCount: number`. Phase 28 then has the information it needs to avoid showing a month twice.
3. Add a `facets.mjs` assertion: *"every `yearMonth` observed in `current.json` incident dates appears in `byMonth`"* — that single check would have caught the missing July.
4. **ACCEPTED sub-risk**: the April-2026 single-incident month remains a thin facet option. Tolerable — Phase 27 ships no UI and STATE.md's "[Phase 27/28] Facet/URL explosion" pitfall already forbids new indexable URLs. Signal that would reveal it: Phase 28's zero/near-zero-result empty-state requirement (NEWSUI-04) must cover `count < 5` months, not just `count === 0`. Note this in the Phase 28 handoff.

---

### FM-7 — Pre/post-filter count semantics are undefined, and Phase 28 needs post-filter counts

**Severity: MEDIUM**

**Evidence.** `27-01-PLAN.md` exports `computeNewsFacets(incidents, index, archiveDir?) → { byFamily, byRegion, byWindow, byMonth }` — four **independent** marginal tallies over the same fixed input. There is no parameter for an active-filter state.
- FACET-05 / ROADMAP 27 criterion 4: counts like `"Robo (14)"`.
- ROADMAP Phase 28 criterion 1: *"filter the news list by time window, region, and crime family **with per-option counts visible**"* — a facet UI showing region counts while a family filter is active needs counts conditioned on the family filter. That is a *cross-tabulation*, which four marginals cannot produce.

**How it would go undetected.** Phase 27 closes green (all four marginals are correct in isolation and `facets.mjs` verifies them). Phase 28 then discovers on day one that it must either recompute facets client-side from the full incident array (which conflicts with the zero-JS-for-content requirement and re-introduces the exact per-locale drift FACET-01 exists to eliminate) or render counts that don't change when other filters are applied (a visibly broken facet UI). Cost lands on Phase 28, attributed to Phase 28.

**AMENDMENT.** Cheapest fix that keeps Phase 27's scope and adds no artifact: have `computeNewsFacets` additionally return a compact per-incident facet-key projection that Phase 28 can cross-tabulate from, plus record the decision so Phase 28 isn't surprised.
1. Extend the return type: `facetKeys: Array<{ id: string; family: string | null; regionId: string | null; yearMonth: string; window: 'today' | '7d' | '30d' | 'older' }>` — one small record per incident, derived by the same code that builds the marginals (so they cannot drift). This is what a filter UI actually needs and it is ~40 bytes/incident.
2. Add to `27-01-PLAN.md` Planning Decisions: *"7. **Counts are unconditioned marginals.** `byFamily`/`byRegion`/`byMonth`/`byWindow` are computed over the full `incidents` array with no active-filter conditioning. Phase 28 MUST derive conditioned (post-filter) counts by cross-tabulating `facetKeys`, never by recomputing facets from raw incidents."*
3. **Region id type is locked as `string`** — `data/cead/meta/index.json` stores `region_id` as a string (verified: `{"cut":"10101","region_id":"10"}`, `typeof === 'string'`, values `'1'..'16'`). Add an explicit note: *"`regionId` is a `string` throughout the facet API. Sort ascending by `Number(regionId)` — a string sort yields `1,10,11,...,2,3` (demonstrated: `[...new Set(index.map(c=>c.region_id))].sort()` → `['1','10','11','12','13','14','15','16','2','3',...]`). Never coerce `regionId` to a number in the output shape; Phase 28's query params are strings."*

---

### FM-8 — Plan fixtures use a family key that does not exist (`robos`), and one that does exist is easy to drop (`sexuales`)

**Severity: MEDIUM**

**Evidence.**
- `27-01-PLAN.md` Task 1 Test 2: *"Given 3 incidents with families `robos`, `robos`, `vif`"*.
- `.planning/REQUIREMENTS.md:56` FACET-05 example: *"Robo (14)"*.
- Real families in `current.json`:
  ```
  { vida: 613, drogas: 78, propiedad: 109, armas: 32, robos_violentos: 283,
    incivilidades: 53, sexuales: 28, vif: 19 }   (n=1215, all 8 present)
  ```
  There is no `robos` family. The real key is `robos_violentos`.
- `pipeline/news/schema.py:22` — `VALID_FAMILIES = set(FAMILY_KEYS) | {"sexuales"}`; `pipeline/shared/schema.py:22` — `FAMILY_KEYS` (7).
- `site/src/lib/familyDefs.ts:18-28` — `FAMILY_LABELS_EN` has **9** keys: the 7 CEAD families + `sexuales` + the phantom `homicidios`.

**How it would go wrong.** Two ways. (a) The executor, told to hardcode "the 8 values … sourced from `pipeline/news/schema.py`" as a literal in `facets.mjs`, must expand `FAMILY_KEYS` by hand. `FAMILY_KEYS` is not visible in the quoted snippet, `FAMILY_ORDER` in `familyDefs.ts` looks like the same list, and the plan's own fixture says `robos`. A literal of `['vida','propiedad','robos','incivilidades','vif','drogas','armas','sexuales']` passes review-by-eye and makes the validator reject all 283 real `robos_violentos` incidents — or, worse, an executor who "fixes" the resulting FAIL by widening the literal ends up with a 9-value set including `homicidios`, quietly re-opening the leak the `sexuales` memory exists to prevent. (b) Because `familyDefs.ts` label lookups fall back to a capitalized key (`news.astro:66-68`), a wrong key never throws — it renders as `Robos_violentos`.

**AMENDMENT.** In `27-01-PLAN.md` Task 2, replace "hardcode the 8 values" with a derivation that cannot be mistyped:
> Build the 8-value set **by reading the Python source**, not by hand-transcription:
> ```js
> // VALID_FAMILIES = FAMILY_KEYS (7, pipeline/shared/schema.py) + the news-only 'sexuales'.
> // Parsed from source so this validator fails loudly if CEAD's 7 keys ever change,
> // instead of drifting silently. Memory: sexuales news-only family — FAMILY_KEYS stays 7.
> const py = readFileSync(path.join(REPO_ROOT,'pipeline','shared','schema.py'),'utf-8');
> const block = py.match(/FAMILY_KEYS:\s*list\[str\]\s*=\s*\[([\s\S]*?)\]/);
> if (!block) { console.error('FAIL facets: could not parse FAMILY_KEYS from pipeline/shared/schema.py'); process.exit(1); }
> const CEAD_FAMILY_KEYS = [...block[1].matchAll(/["']([a-z_]+)["']/g)].map(m => m[1]);
> if (CEAD_FAMILY_KEYS.length !== 7) { console.error(`FAIL facets: FAMILY_KEYS is ${CEAD_FAMILY_KEYS.length}, expected 7 (CEAD contract) — see memory 'sexuales news-only family'`); process.exit(1); }
> const VALID_FAMILIES = new Set([...CEAD_FAMILY_KEYS, 'sexuales']);
> ```
> This makes FACET-04's "CEAD's `FAMILY_KEYS` remains unmodified at 7" a **live automated assertion** rather than the manual `git diff --stat` check `27-VALIDATION.md` currently lists — and it structurally cannot admit `homicidios`.
>
> Add two more assertions: (5) `'homicidios'` does not appear among observed families in `current.json`; (6) `'sexuales'` **is** present (28 incidents today) — a validator that would still pass if the news-only 8th family silently vanished from the pipeline is not guarding FACET-04.

Also fix Test 2's fixture in Task 1 to use `robos_violentos`, and add a note to `.planning/REQUIREMENTS.md:56` that the illustrative `"Robo (14)"` label is not a real family key (`robos_violentos` / "Violent Robbery" is).

---

### FM-9 — Timezone: `formatMonth` uses local-midnight `new Date(y, m-1, 1)` while facets compare `YYYY-MM` strings; and `newestDate` depends on incident-local dates

**Severity: LOW-MEDIUM**

**Evidence.**
- `site/src/pages/news.astro:77-78` — `const d = new Date(y, m - 1, 1); return d.toLocaleDateString('en-US', {year:'numeric', month:'long'});` — **local** midnight, then locale-formatted. On a build machine in UTC (GitHub Actions / Cloudflare) this is fine; the risk is any consumer that instead parses `'2026-07'` via `new Date('2026-07')` (UTC midnight) and formats it in a negative-offset zone (Chile is UTC-4/-3) → renders "June 2026".
- Incident `date` is a bare `YYYY-MM-DD` string (`node -e` → `sample date 2026-07-01`), with no time and no zone. `generated` is a UTC instant (`2026-07-27T14:25:05.303451Z`).
- `27-01-PLAN.md` Task 1 `<action>`: *"`byWindow` via `newestDate = max(incidents.map(i => i.date))` then filter by day-diff from that anchor (today = same date string …)"*.

**How it would go undetected.** The plan's own Planning Decision 1 already dodges the worst version of this by anchoring to the newest *incident* date instead of `new Date()` — that is genuinely the right call and it removes the wall-clock off-by-one entirely. The residual risk is narrow: if the executor implements the day-diff by constructing `Date` objects (`new Date(a) - new Date(b)`) mixed with any local-time construction, or by comparing `incident.date` against a `Date`-derived value, an off-by-one appears only in non-UTC zones and only at window boundaries. `byWindow.today` currently holds **11** incidents (`2026-07-27`) versus 38-66 on adjacent days — an off-by-one shifts "today" to a 38-item day and looks entirely plausible.

**AMENDMENT.** Add to `27-01-PLAN.md` Task 1 `<action>`:
> **All window arithmetic is string-and-UTC only.** Compare `YYYY-MM-DD` strings lexicographically for equality (`today`), and compute the two lower bounds once with `Date.UTC` — never `new Date(y, m, d)` (local) and never `new Date(str)` on anything but a `YYYY-MM-DD` literal (which V8 parses as UTC midnight):
> ```ts
> const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
> const lower = (days: number) => new Date(anchorMs - days * 86400000).toISOString().slice(0, 10);
> const min7 = lower(6), min30 = lower(29);
> // today: i.date === newestDate ; sevenDay: i.date >= min7 ; thirtyDay: i.date >= min30
> ```
> No `toLocaleDateString`, no `getMonth()`, no local-time `Date` construction anywhere in `newsFacets.ts`. `yearMonth` is `i.date.slice(0,7)` — never derived from a `Date` object.
>
> Add a `facets.mjs` determinism assertion: run the window computation twice with `process.env.TZ` set to `'UTC'` and `'America/Santiago'` and assert identical bucket sizes. (`spawnSync` with a modified `env`, or set `process.env.TZ` before the first `Date` use.) This is a ~10-line check that permanently closes the class.

**Also**: `byWindow` returns full `IncidentLike[]` arrays. Per FM-4's amendment, only their lengths may be serialized into the page. Add to Planning Decision 4: *"`byWindow` arrays are for build-time consumption only; never serialize them — three arrays over 1,215 incidents would add ~2.4MB to each page and blow the map/page-weight budgets."*

---

### FM-10 — The "16/16" renumbering is broader than `all.mjs`, and the directive's own handoff prompt will contradict it

**Severity: MEDIUM** (extends plan-checker H3 into what it actually breaks)

**Evidence.**
- `site/scripts/validate/all.mjs:2` — "run all **12** validation scripts in sequence" (already wrong: the array has 15 entries, lines 39-55, enumerated 1-15 in the doc-comment).
- `all.mjs:117` — `console.log(\`  ${passed.length}/${results.length} validators passed\`)`. The summary line is **computed**, so it will read `16/16` automatically. No change needed there — good.
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md:16` (RUN STATUS), `:77` (hard rules), `:104` (operating lesson 6) — all say `15/15`.
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` § Session continuation, the **verbatim paste-after-`/clear` handoff prompt**: *"cada fase termina con la suite pytest y **los 15 validadores** en verde"*.
- `.planning/STATE.md:18`, `:81` — `15/15`.
- `27-01-PLAN.md` Planning Decision 6 asserts *"No other document in this repo hardcodes '15 validators'"* — false, per the six hits above.

**How it would go wrong.** `27-02-PLAN.md` Task 2 only updates STATE.md. The directive keeps saying 15. A future session pastes the handoff prompt, is told 15 validators, sees 16, and either "fixes" the count by removing a validator or logs a phantom discrepancy. Because operating lesson 6 explicitly frames the number as the authoritative baseline ("correct these in STATE.md if they drift"), a diligent agent may treat 16 as the drift.

**AMENDMENT.** In `27-02-PLAN.md` Task 2, extend the file list and the action:
> `files_modified` += `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`.
> Update every `15/15` / "15 validadores" / "15 validators" occurrence to `16/16` in: `.planning/STATE.md` (lines ~18, ~81), `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` (RUN STATUS table row, § Hard safety rules, § Operating lessons item 6, **and the verbatim Spanish handoff prompt in § Session continuation**). Verify with `grep -rn "15/15\|15 validadores\|15 validators" .planning/` returning zero hits afterward.
> Also fix the stale `all.mjs:2` header: "run all **16** validation scripts in sequence".
> If FM-1's freshness branch is taken, phrase the baseline as **"16 validators (15 green + `freshness` red pending cron re-run — see Blockers)"** rather than a bare number, so the next session isn't told to expect a green it cannot get.

---

### FM-11 — `facets.mjs` lands inside `astro check`'s `include` glob, so the "exactly 4 errors" gate is coupled to the new validator's typing

**Severity: LOW-MEDIUM**

**Evidence.**
- `site/tsconfig.json`: `"include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.astro", "scripts/**/*.mjs"]` — validator scripts **are** type-checked.
- Proof it processes them:
  ```
  scripts/validate/region.mjs:53:10 - warning ts(6133): 'hasLowPopCommune' is declared but its value is never read.
  scripts/validate/seo.mjs:40:10  - warning ts(6133): ...
  ```
- Baseline confirmed by execution: `Result (125 files): - 4 errors - 0 warnings - 36 hints`, and all four are:
  ```
  src/components/ComparatorPairsLinks.astro:28:{19,25,31,38} - error ts(7031): Binding element '...' implicitly has an 'any' type.
  ```
  So the plan's "4 errors, all in `ComparatorPairsLinks.astro`" claim is **correct** — good. (Note the STATE memory `ui-360-diagnostic-pending` carries "8 astro-check errors"; that figure is stale, now 4.)

**How it would go wrong.** `27-02-PLAN.md` Task 2 requires "exactly 4 errors". A new `facets.mjs` that trips a real TS diagnostic — e.g. indexing a plain object with a `string` key, `JSON.parse(...)` results flowing into a typed position, `err.message` on an `unknown` catch binding — pushes the count to 5+ and fails a gate that has nothing to do with facet correctness, adding a third false-red stall vector alongside FM-1 and FM-3.

**AMENDMENT.** Add to `27-01-PLAN.md` Task 2 acceptance criteria:
> `site/tsconfig.json` includes `scripts/**/*.mjs`, so `facets.mjs` **is** type-checked by `astro check`. Verify with the chained command `cd site && npx astro check 2>&1 | tail -5` that the error count is still exactly 4, all in `ComparatorPairsLinks.astro`. If `facets.mjs` introduces an error, fix the typing in `facets.mjs` (add JSDoc `@param`/`@type` annotations, use `catch (err) { String(err) }`) — **do not** add `// @ts-nocheck`, do not touch `tsconfig.json`, and do not "fix" the 4 pre-existing `ComparatorPairsLinks.astro` errors (out of scope; that is a v2.0 carry-over).

Also change `27-02-PLAN.md` Task 2's phrasing from "confirm the error count is exactly 4" to "exactly 4, all `ts(7031)` in `src/components/ComparatorPairsLinks.astro:28`" so a coincidental 4-error total from different files cannot pass.

---

### FM-12 — The `git status --porcelain` FACET-06 check is specified as "human/executor-reviewed", i.e. as nothing

**Severity: LOW**

**Evidence.** `27-VALIDATION.md` § Manual-Only Verifications: *"`git status --porcelain` is the correct tool but its output must be human/executor-reviewed against the expected `files_modified` list, not pattern-matched blindly."* No human is present — the directive states "The user is away."

Meanwhile `site/public/data/` (where a stray artifact would most plausibly land) is gitignored (`site/.gitignore:3`), so `git status` **cannot** see a facet artifact written there. The one check named for FACET-06 is blind to the one location FACET-06 is about.

**How it would go undetected.** Entirely. `git status` stays clean whether or not `site/public/data/facets.json` was written.

**AMENDMENT.** Replace the manual entry in `27-VALIDATION.md` with a scripted assertion, and add it to `facets.mjs`:
> ```js
> // FACET-06: no facet artifact anywhere under site/** — including the gitignored
> // site/public/data/ tree, which `git status --porcelain` cannot see.
> const strays = [];
> const walk = (d) => { for (const e of readdirSync(d, {withFileTypes:true})) {
>   const p = path.join(d, e.name);
>   if (e.isDirectory()) { if (!/^(node_modules|\.astro|dist)$/.test(e.name)) walk(p); }
>   else if (/facet/i.test(e.name)) strays.push(path.relative(SITE_ROOT, p));
> }};
> walk(path.join(SITE_ROOT, 'public'));
> // plus: assert no *.json under site/src/**
> if (strays.length) { console.error(`FAIL facets: facet artifact(s) under site/**: ${strays.join(', ')}`); process.exit(1); }
> ```
> Keep the `git status --porcelain` step too, but state its actual limit: *"catches tracked-file surprises only; the gitignored `site/public/data/` tree is covered by the `facets.mjs` walk above."*

---

### FM-13 — 27-01 Task 2's failure-path demonstration involves copying and corrupting incident data next to a read-only `data/` tree

**Severity: LOW** — **ACCEPTED with a hardening amendment**

**Evidence.** `27-01-PLAN.md` Task 2 acceptance: *"Deliberately corrupting one incident's `cut` … (in a throwaway test copy of `current.json`, not the real file) and pointing the validator at it causes exit code 1 … (revert the throwaway file after this check; never leave `data/` mutated)."*

`current.json` is 856,437 bytes and lives in a OneDrive-synced tree. The directive's hard rule is "No mutation of `data/`". An executor that copies, edits, and restores in-place — or writes the throwaway *into* `data/incidents/` — risks a torn OneDrive write on production data (operating lesson 4 names torn writes as real in this repo).

**Disposition: ACCEPTED** — proving the assertion fires is worth more than the residual risk, and 27-01's plan-checker finding H1 (a verify that can never fail) makes a demonstrated failure path essential. But harden the mechanics:

**AMENDMENT.** Rewrite the demonstration so nothing is ever written near `data/`:
> Make `facets.mjs` accept an optional override path (`process.argv[2] || process.env.FACETS_CURRENT_JSON`, defaulting to `data/incidents/current.json`). Demonstrate the failure entirely in the OS temp dir, in one chained command:
> ```
> node -e "const {readFileSync,writeFileSync}=require('fs'),os=require('os'),p=require('path');const j=JSON.parse(readFileSync('data/incidents/current.json','utf8'));j.incidents[0].cut='99999';const t=p.join(os.tmpdir(),'facets-negative.json');writeFileSync(t,JSON.stringify(j));console.log(t)" > /tmp/negpath.txt && node site/scripts/validate/facets.mjs "$(cat /tmp/negpath.txt)"; echo "EXPECT_EXIT_1:$?"
> ```
> **Never** create, copy, move, or edit any file under `data/` — not even a `.bak`. Assert `git status --porcelain data/` is empty immediately afterward.
> Also add a second negative case: an incident whose `family` is `'homicidios'` must FAIL (proves the FM-8 containment assertion fires, not just the region one).
> And fix the H1 no-op verify: the `<automated>` block must be `node site/scripts/validate/facets.mjs && echo GREEN` (`&&`, so a non-zero exit propagates) — never `...; echo "EXIT:$?"`, which always exits 0.

---

### FM-14 — Plan 02 Task 2 will edit the wrong ROADMAP entry: Phase 27's `**Plans**: TBD` no longer exists

**Severity: MEDIUM**

**Evidence.** `27-02-PLAN.md` Task 2 `<action>`: *"Update `.planning/ROADMAP.md`'s Phase 27 entry: **replace `**Plans**: TBD` with `**Plans**: 2 plans`** and add the plan checklist"*.

But the ROADMAP already has it:
```
### Phase 27: News Facet Data Model
...
**Plans**: 2 plans
Plans:
**Wave 1**
- [ ] 27-01-PLAN.md — newsFacets.ts ... registered as #16
**Wave 2**
- [ ] 27-02-PLAN.md — Wire news.astro + es/noticias.astro ...
```
And `grep -n 'Plans\*\*: TBD' .planning/ROADMAP.md` → lines **343, 360, 378, 394, 409, 425** — six hits, none of them Phase 27. Line 343 is **Phase 28's**.

**How it would go wrong.** A Sonnet executor told to "replace `**Plans**: TBD`" greps, finds the first hit (Phase 28, line 343), and rewrites **Phase 28's** roadmap entry to claim Phase 27's two plans. That is a hard-to-detect corruption of the next phase's planning input, discovered only when Phase 28 starts planning from a wrong entry — and the run is unattended.

**AMENDMENT.** Rewrite `27-02-PLAN.md` Task 2's ROADMAP instruction:
> `.planning/ROADMAP.md`'s Phase 27 entry **already** reads `**Plans**: 2 plans` with both plans listed under Wave 1 / Wave 2 — do not add or replace it. **There are six `**Plans**: TBD` lines in ROADMAP.md (343, 360, 378, 394, 409, 425) and none belong to Phase 27; line 343 is Phase 28's. Do not touch any of them.** The only ROADMAP edits in this task are: tick the two plan checkboxes `- [ ]` → `- [x]` inside the `### Phase 27` section, and update the Phase 27 row of the Progress Table to `2/2 | Complete | 2026-07-30`. Verify with `sed -n '/### Phase 27/,/### Phase 28/p' .planning/ROADMAP.md` that only lines within that range changed, and `git diff .planning/ROADMAP.md` touches no line above the `### Phase 27` heading except the Progress Table row.

---

### FM-15 — FACET-03 / ROADMAP criterion 3 demand a CUT-length derivation; Plan 01 forbids one — the verifier will read this as unmet

**Severity: MEDIUM**

**Evidence.**
- `.planning/REQUIREMENTS.md:54` FACET-03: *"Geography facets resolve each incident's `cut` to its region **via the established CUT-length derivation**"* (annotated: use `index.json`'s `region_id` as the authoritative **cross-check**).
- ROADMAP Phase 27 success criterion 3: *"resolve every incident's `cut` to one of the 16 regions **via the established CUT-length derivation**, and this derivation is verified correct against `data/cead/meta/index.json`"*.
- `27-01-PLAN.md` `must_haves.truths`: *"Region facet resolves via the existing `region_id` already present in `data/cead/meta/index.json` — **no CUT-length re-derivation in TypeScript**"*.

The plan's choice is the technically better one (memory `tarapaca-region-id-collision` documents that hand-derivation caused an 11-vs-14 collision, resolved by deriving from CUT length; using the already-correct `region_id` avoids re-implementing that logic a third time in a third language). But it is a **direct textual contradiction** of two locked artifacts.

**How it would go wrong.** The Opus `gsd-verifier` (step 6 of the per-phase protocol) checks the ROADMAP success criteria literally. Criterion 3 says "via the established CUT-length derivation"; the code contains no such derivation. Expect a `PARTIAL`/`FAIL` on criterion 3 and a fix cycle that re-adds a redundant derivation — or worse, replaces the correct lookup with a hand-rolled one.

**AMENDMENT.** Reconcile the wording *before* execution, and make the cross-check real rather than rhetorical:
1. In `27-01-PLAN.md` Planning Decisions, add: *"**Decision 8 (resolves a REQUIREMENTS/ROADMAP wording conflict).** FACET-03 and ROADMAP criterion 3 say 'via the established CUT-length derivation'. We resolve `region_id` by direct lookup in `data/cead/meta/index.json` instead — it is authoritative, already correct for all 346 communes, and avoids a third re-implementation of the logic that caused the Tarapacá 11-vs-14 collision (memory `tarapaca-region-id-collision`). The requirement's spirit — a verified-correct CUT→region mapping — is satisfied and **strengthened** by asserting the two agree."*
2. Make the agreement an assertion in `facets.mjs`, so criterion 3's "verified correct against `index.json`" is literally executed:
   > For every entry in `index.json`, compute `derived = cut.length === 4 ? cut.slice(0,1) : cut.slice(0,2)` and assert `derived === entry.region_id` for all 346, and that the resulting set is exactly `{'1'..'16'}` (16 distinct values). FAIL with the offending CUT otherwise. (Verified reachable: `index.json` is a 346-entry array; `region_id` values are the strings `'1'..'16'`.)
3. Add a note to `.planning/REQUIREMENTS.md:54` recording the resolution so the verifier reads the amended intent.

---

### FM-16 — `newsFacets.ts` uses `process.cwd()` while `data.ts` warns against it; both are right, and the plan doesn't say why

**Severity: LOW** — **ACCEPTED**

**Evidence.**
- `site/src/lib/data.ts:2-10` header: *"NEVER use `process.cwd()` or `import.meta.glob` — both are CWD-dependent or bundler-dependent"* — then `data.ts:24-26` does exactly that: `path.resolve(process.cwd(), '..', 'data', 'cead')`, with a superseding comment.
- `site/src/pages/news.astro:19-22`: *"`import.meta.url` is unreliable at build time — compiled chunk locations differ per page, which previously made EN resolve to a missing path and render empty (bilingual drift)"* → uses `process.cwd()`.
- `27-01-PLAN.md` correctly specifies `process.cwd()`-relative for `newsFacets.ts` and `__dirname`-relative for `facets.mjs`.

**Disposition: ACCEPTED.** The plan gets both right. The residual risk is only that an executor who reads `data.ts`'s stale opening warning "corrects" `newsFacets.ts` to `import.meta.url` — which is precisely the bug memory `news-page-build-path-drift` records (EN news page rendered empty while ES worked). The FM-3 card-count floor assertion would catch it on the next build, and the FM-4 dist-equality check would catch the EN/ES asymmetry specifically. **Signal that would reveal it:** an EN/ES card-count divergence in `dist/`. Add one line to `27-01-PLAN.md` Task 1 `<read_first>`: *"`data.ts`'s opening 'NEVER use `process.cwd()`' comment is superseded by the comment at `data.ts:24-26` — `process.cwd()` is the correct, deliberate choice for build-time reads in this repo. Do not 'fix' it to `import.meta.url`; that is the exact cause of the `news-page-build-path-drift` bug."*

---

## What the plan-checker missed

Only genuinely new findings, in severity order:

1. **FM-1 — `freshness.mjs` fails within ~8 hours of planning, and the phase-close gate has no branch for it.** Demonstrated: `PASS ... 2.6 days old`, `MAX_AGE_DAYS = 3`, fails after `2026-07-30T14:25:05Z`. This is the single most likely cause of Phase 27 failing, and it is entirely outside the faceting work. It also affects every subsequent phase 28–33.
2. **FM-2 — 27-01 Task 1 Test 4 is arithmetically impossible** (`2026-06-01` is 57 days before `2026-07-28`, asserted to be inside a 30-day window). The plan's escape hatch ("fold into `facets.mjs`") makes the contradiction vanish without trace, and real data cannot falsify a broken 30-day window because `current.json` only spans 28 days.
3. **FM-3 — `npx astro build` in Plan 02's verify skips `prebuild`/`sync-data.mjs` and `ROLLOUT_ALL=true`.** `site/public/data/` is gitignored; on a fresh clone the news page renders the empty state and the build still exits 0 — the exact bug class already shipped once here.
4. **FM-14 — Phase 27's `**Plans**: TBD` no longer exists in ROADMAP.md.** The six remaining `TBD` lines belong to phases 28+; line 343 is Phase 28's. The instruction as written points a grepping executor at the wrong phase's entry.
5. **FM-5 — `vitest ^4.1.9` IS installed** (27-VALIDATION.md says it isn't), with no `test` script and one already-dead spec (`formatNumber.test.ts`). The plan's "check devDependencies first" instruction leads the executor straight into producing a second never-executed test file.
6. **FM-6 — the archive is `{2026-04, 2026-06}` only:** `byMonth` overlaps `current.json` for June, omits July entirely (where 1,204 of 1,215 incidents live), and the plan never defines how to count an archive file (they are objects, not arrays).
7. **FM-10 — the "15/15" figure appears six times outside `all.mjs`**, including in the directive's verbatim paste-after-`/clear` handoff prompt. Planning Decision 6's claim that no other document hardcodes it is false. (`all.mjs`'s summary line is *computed*, so it needs no change — the plan-checker's concern there was misplaced; the real exposure is the directive.)
8. **FM-11 — `site/tsconfig.json` includes `scripts/**/*.mjs`**, so the new `facets.mjs` is type-checked and can break the "exactly 4 errors" gate. (Baseline confirmed by execution: 4 × `ts(7031)` in `ComparatorPairsLinks.astro:28` — the plan's claim is correct, but the coupling is undocumented. The STATE memory's "8 astro-check errors" is stale.)
9. **FM-15 — FACET-03 and ROADMAP criterion 3 mandate a "CUT-length derivation" that Plan 01 explicitly forbids.** The Opus verifier reads criteria literally; this will read as unmet and invite a harmful fix cycle.
10. **FM-8 — the plan's own fixture family `robos` does not exist** (real key: `robos_violentos`, 283 incidents), and FACET-05's `"Robo (14)"` example is likewise fictional. Combined with hand-transcribing an 8-value literal from a `FAMILY_KEYS` the plan never shows, this is a live path to either rejecting 283 real incidents or widening the set to admit `homicidios`.
11. **FM-12 — the one check named for FACET-06 (`git status --porcelain`) is structurally blind to `site/public/data/`**, which is gitignored — the very place a stray facet artifact would land.
12. **FM-7 — four independent marginals cannot produce the conditioned counts Phase 28's facet UI requires**; region id string-vs-number and the `byWindow` array-serialization weight trap are the same handoff.

---

## Amendment digest

Apply in order. Each is self-contained.

1. **[FM-1, CRITICAL]** `27-02-PLAN.md` Task 2: insert the pre-declared freshness branch (close green on `15/16 (freshness excluded)`; record a STATE.md Blocker + deferred-live item; explicitly forbid editing `MAX_AGE_DAYS`, `data/`, or the `VALIDATORS` array). Mirror the same wording into `27-VALIDATION.md` and `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` § Hard safety rules.
2. **[FM-2, HIGH]** `27-01-PLAN.md` Task 1: replace Test 4 with the `2026-07-28 / 2026-07-25 / 2026-06-29 / 2026-06-28` boundary fixture (expect 1 / 2 / 3, `2026-06-28` excluded) and add Test 4b (`thirtyDay.length < incidents.length`). Require synthetic in-memory fixtures if folded into `facets.mjs`.
3. **[FM-3, HIGH]** `27-02-PLAN.md` Task 1: replace `npx astro build` with `npm run build` everywhere; add the chained card-count-floor assertion (`≥1000` cards per locale, no `empty-state`); add a `<read_first>` note banning `npx astro build` in this phase.
4. **[FM-4, HIGH]** `27-02-PLAN.md` Task 1: delete the hedged monthGroups instruction; replace with "leave `news.astro` lines 96-104 and 152-187 byte-identical; add only imports + `archiveDir` + the `computeNewsFacets` call + an inert `<script type="application/json" id="news-facets" set:html={...}>` carrying a counts-only projection". Add a `dist/`-parsing assertion to `facets.mjs`: both locales' `#news-facets` parse and are deeply equal. Add `grep -c "monthGroups" ≥ 3` to acceptance.
5. **[FM-5, MEDIUM]** `27-VALIDATION.md`: correct "No Jest/Vitest configured" → vitest 4.1.9 present, no `test` script, one dead spec. `27-01-PLAN.md` Task 1: replace the conditional with "add `\"test\": \"vitest run\"`, create `newsFacets.test.ts` with the 6 cases, append `npm test` to Plan 02's gate chain" (fallback: forbid `.test.ts` and put the cases in a `facets.mjs` SELFTEST section).
6. **[FM-6, MEDIUM]** `27-01-PLAN.md`: define `count = (parsed.incidents ?? []).length`; make `byMonth` the union of archive months and months observed in `incidents`, each tagged `source: 'archive' | 'current' | 'both'` (+ `currentCount`); add the `facets.mjs` assertion that every month in `current.json` appears in `byMonth`. Flag `count < 5` months to Phase 28's empty-state requirement.
7. **[FM-7, MEDIUM]** `27-01-PLAN.md`: add `facetKeys: Array<{id, family, regionId, yearMonth, window}>` to `NewsFacetIndex`; add Planning Decision 7 (counts are unconditioned marginals; Phase 28 cross-tabulates `facetKeys`); lock `regionId` as a `string` sorted by `Number(regionId)` with the string-sort counterexample inline.
8. **[FM-8, MEDIUM]** `27-01-PLAN.md` Task 2: derive `VALID_FAMILIES` by regex-parsing `FAMILY_KEYS` out of `pipeline/shared/schema.py` and hard-failing if it is not 7; add assertions that `homicidios` is absent and `sexuales` is present. Fix Test 2's fixture to `robos_violentos`; annotate `REQUIREMENTS.md:56` that `"Robo (14)"` is illustrative only.
9. **[FM-9, LOW-MED]** `27-01-PLAN.md` Task 1: mandate string/UTC-only window arithmetic (`Date.UTC`/`Date.parse(d+'T00:00:00Z')`, no local `Date` construction, no `toLocaleDateString`, `yearMonth = date.slice(0,7)`); add a `TZ=UTC` vs `TZ=America/Santiago` determinism assertion; forbid serializing `byWindow` arrays.
10. **[FM-10, MEDIUM]** `27-02-PLAN.md` Task 2: add `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` to `files_modified`; update all six `15/15` occurrences (STATE.md ×2, directive ×4 including the verbatim Spanish handoff prompt); fix `all.mjs:2`'s stale "12"; verify `grep -rn "15/15\|15 validadores\|15 validators" .planning/` returns nothing.
11. **[FM-11, LOW-MED]** `27-01-PLAN.md` Task 2 acceptance: note `tsconfig.json` type-checks `scripts/**/*.mjs`; require `astro check` to stay at exactly 4 errors, all `ts(7031)` in `ComparatorPairsLinks.astro:28`; ban `@ts-nocheck` and tsconfig edits.
12. **[FM-12, LOW]** Add the `site/public` recursive `/facet/i` stray-file walk to `facets.mjs`; downgrade the `git status --porcelain` entry in `27-VALIDATION.md` to "tracked files only — the gitignored `site/public/data/` tree is covered by the `facets.mjs` walk".
13. **[FM-13, LOW]** `27-01-PLAN.md` Task 2: give `facets.mjs` an `argv[2]`/`FACETS_CURRENT_JSON` path override; run the negative demo entirely in `os.tmpdir()`, never writing anything under `data/`; add a `family: 'homicidios'` negative case; change the `<automated>` verify from `...; echo "EXIT:$?"` to `... && echo GREEN` so a non-zero exit actually propagates.
14. **[FM-14, MEDIUM]** `27-02-PLAN.md` Task 2: remove the "replace `**Plans**: TBD`" instruction; state that Phase 27's entry is already complete, that the six remaining `TBD` lines (343/360/378/394/409/425) belong to later phases and must not be touched, and restrict edits to the two Phase-27 checkboxes plus the Phase-27 Progress Table row.
15. **[FM-15, MEDIUM]** `27-01-PLAN.md`: add Planning Decision 8 reconciling FACET-03/ROADMAP-criterion-3's "CUT-length derivation" wording with the `region_id`-lookup implementation; add a `facets.mjs` assertion that `cut.length===4 ? cut.slice(0,1) : cut.slice(0,2)` equals `region_id` for all 346 communes and yields exactly 16 distinct values; annotate `REQUIREMENTS.md:54`.
16. **[FM-16, LOW/accepted]** `27-01-PLAN.md` Task 1 `<read_first>`: note that `data.ts`'s opening "NEVER use `process.cwd()`" comment is superseded by `data.ts:24-26`; `process.cwd()` is deliberate and must not be "fixed" to `import.meta.url` (cause of `news-page-build-path-drift`).
