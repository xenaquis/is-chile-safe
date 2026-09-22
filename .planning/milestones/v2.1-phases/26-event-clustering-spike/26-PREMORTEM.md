---
phase: 26-event-clustering-spike
type: premortem
model: opus
created: 2026-07-29
premise: "Phase 26 failed. It is 2026-07-31 and the phase is a mess. Why?"
---

# Phase 26 — Premortem

Adversarial review of `26-01-PLAN.md` … `26-04-PLAN.md` against `26-RESEARCH.md`, `26-PATTERNS.md`, `26-VALIDATION.md`, `26-00-SPIKE-PING.md`, `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`, `.planning/REQUIREMENTS.md` (CLUS-01..09), and the **real code** (`pipeline/news/{clustering-absent,classifier,dedup,store,schema}.py`, `pipeline/tests/conftest.py`, `pipeline/tests/test_schema_incidents.py`, `pipeline/tests/test_classifier.py`, `pipeline/archive_r2.py`, `site/src/components/map/IncidentPinLayer.ts`) plus **live measurements against `data/incidents/current.json`** (1,215 incidents, 257 multi-article `(cut,date)` buckets, both mandatory buckets read in full, rapidfuzz scores computed).

The single most dangerous outcome is **a GO that is arithmetically 100% precise and factually wrong**. Four independent mechanisms in the current plans can produce exactly that (PM-01, PM-02, PM-03, PM-05). They are the priority.

## Summary table

| ID | Sev | One-line failure | Disposition |
|---|---|---|---|
| PM-01 | HIGH | Hand labels are wrong in the merge direction (Tongoy `6eed24180c36dbec` = "19 años / homicidio" vs the rest "8 años y medio / homicidio frustrado"), so a real false merge is scored as a TP and precision reads 1.0 | Amend `26-02` T2 |
| PM-02 | HIGH | CLUS-08 as planned cannot detect a model swap at all — the pytest reads only `cached_verdict`; swapping `MODEL` or editing `SYSTEM_PROMPT` leaves it green | Amend `26-03` T2 |
| PM-03 | HIGH | Vacuous precision: missing/invalid `OPENROUTER_API_KEY` or rate-limit failures make `adjudicate_pair` return the fail-safe no-merge verdict, which gets **cached as if real** → TP=FP=0 → precision "1.0" → false GO | Amend `26-01` T2, `26-02` T2, `26-03` T1/T2 |
| PM-04 | HIGH | On NO-GO, `test_golden_set_precision_100pct` is permanently red, violating the directive's "every phase leaves pytest green" rule and poisoning phases 27–33 | Amend `26-03` T2 + `26-04` T1 |
| PM-05 | MED | The pre-filter at `45.0` is **measured inert** on the real buckets (all 36 pairs in 2101 and all 28 in 4102 score ≥ 48.7); the report's CLUS-02 "bounds cost" evidence will be ~0% reduction, and any later threshold raise silently deletes the adversarial negatives that make the gate meaningful | Amend `26-01` T1, `26-02` T1, `26-03` T1 |
| PM-06 | MED | Pair-count control is unsound: the two mandatory buckets alone yield **64 pairs**; "15–20 supplemental buckets of size 2–5" yields anywhere from 15 to 200 → the 60–100 range is missed, and "trim" invites label cherry-picking | Amend `26-02` T1 |
| PM-07 | MED | The live fill loop is not resumable — a 429 halfway burns the spent calls again on restart and (with PM-03) silently caches fail-safe verdicts for the tail | Amend `26-02` T2 |
| PM-08 | MED | The ≤2,000-call cap is per-invocation prose, not a cumulative enforced ledger; five re-runs of 400 calls never trip it | Amend `26-02` T2 |
| PM-09 | MED | GO ships `cluster_id`/`is_primary` with **no producer**: `store.py` writes raw dicts, so the fields never appear in `current.json` and Phase 28's NEWSUI-05 has nothing to read | Amend `26-04` T2 |
| PM-10 | MED | `26-02` T1's verify command runs `--dry-run`, a flag the task never specifies implementing → executor improvises mid-plan | Amend `26-02` T1 |
| PM-11 | MED | `clustering_golden_set_draft.json` is written under `pipeline/tests/fixtures/` with no `.gitignore` entry (verified absent) → unlabeled draft gets committed | Amend `26-02` T1 |
| PM-12 | MED | `26-04` hand-copies precision/recall/FP into the report → report and test can disagree | Amend `26-04` T2 |
| PM-13 | MED | `26-04` treats *any* red `test_golden_set_precision_100pct` as NO-GO, so a bug or import error in the metric code issues a false NO-GO verdict | Amend `26-04` T1 |
| PM-14 | MED | The `confidence == "high"` half of the mergeable-state rule is probably a no-op (ping: 3/3 "high"), so the report implies a two-factor gate that is really one factor | Amend `26-03` T1 |
| PM-15 | MED | Ground truth is derived from the *same* information the adjudicator sees (headline only) → the golden set cannot be more informed than the model; systematic agreement is mistaken for accuracy | Amend `26-02` T1/T2 |
| PM-16 | LOW | Secret leakage into fixture/log/report | **Accepted** with one grep guard (see detail) |
| PM-17 | LOW | `data/` mutation | **Accepted** — verified no plan opens `data/` for write |
| PM-18 | LOW | Non-pytest backward-compat consumers (R2 CSV, JSONL, TS interface) | **Accepted** — verified safe; document in report |
| PM-19 | LOW | Golden set is same-date only; ±1-day same-event coverage is untested but the report may read as a general claim | Amend `26-03` T1 (one scope sentence) |

---

## PM-01 — Golden-set label circularity (HIGH)

**Mechanism.** `26-02-PLAN.md`'s `<interfaces>` block hard-codes the ground truth: all 8 Tongoy/4102 articles = one event (28 `merge` pairs), and 2101 splits A/B/C with 13 `merge` + 23 `no_merge` pairs. I read the real titles. The Tongoy bucket is **not** obviously one event:

```
9b1e83ae50fd427e  LaTercera         Condenan a 8 años a hombre que disparó a madre, bebé y perro en Tongoy
6eed24180c36dbec  fiscaliadechile   Condenan a 19 años por homicidio y porte de armas en Tongoy      <-- outlier
282067156cf95860  G5noticias        ... 8 años y medio por homicidio frustrado y porte de armas en Caleta Tongoy
c3ec78c8f3e3be83  fiscaliadechile   ... 8 años y medio por homicidio frustrado en Caleta Tongoy
```
`6eed24180c36dbec` reports **19 años** for **homicidio (consumado)**; the other seven report **8–8.5 años** for **homicidio frustrado** plus a dog killed. A 10.5-year sentence delta together with a consummated-vs-frustrated charge difference is the signature of a *different case*, not "reporting noise". The plan pre-declares it noise.

Now the arithmetic. Golden `merge` + pipeline merge = **TP**. So if that pair is really `no_merge` and Granite merges it, the harness records a **TP**, not an FP. Precision stays 1.0. **A genuine false merge is laundered into the numerator.** The same laundering is available in 2101 Event C, which mixes an aggregate article (`16439f8dc78173a6`, "Dos operativos … 6 detenidos") and a *later procedural stage* (`b01de8947aa555f6`, "formalizados por receptación") with the arrest-day operativo articles.

**Why it fails silently.** Every downstream artifact is derived from the label file: `compute_pairwise_metrics` trusts `label`, the report table prints `label`, the pytest asserts against `label`, and the Fable verdict reads the report. Nothing in the chain can contradict the label. And the failure is *asymmetric in the dangerous direction*: over-labeling `merge` inflates precision, while over-labeling `no_merge` would only depress it (safe). The plan's mandatory bucket happens to over-label `merge`.

**Amendment (`26-02-PLAN.md`, Task 2).**
1. Reclassify the Tongoy bucket as **two label groups pending verification**: `{6eed24180c36dbec}` vs the other seven. The 7 pairs spanning them get `label: "no_merge"` unless the source articles (fetch/read `url`) affirmatively show one case; record the deciding fact in `note`.
2. **Blind second pass, precision-conservative:** every pair labeled `merge` must be confirmed by a second labeling pass that sees only `title_a/title_b/outlet_a/outlet_b/url_a/url_b` and **not** `cached_verdict` (spawn a separate agent for this; do not reuse the first labeler's context). Any disagreement is resolved to `no_merge`, or the pair is dropped with `excluded: "label_disputed"`. Pairs labeled `no_merge` need no second pass (mislabeling in that direction cannot manufacture a TP).
3. Every pair carries `label_basis` — the concrete discriminator used (`fecha`, `lugar`, `actores`, `sentencia`, `etapa_procesal`) — so a human can re-check the label without re-reading the corpus.
4. Fixture retains `title_a`, `title_b`, `outlet_a`, `outlet_b`, `url_a`, `url_b` **for every pair**. Delete the plan's permission to "remove `title_a`/`title_b` from the pairs that carry no labeling ambiguity" — labels that cannot be audited from the fixture alone are not labels.
5. Add to `26-03`'s report a line: `merge-labels independently confirmed: N/N (blind second pass)`. If that line is absent, the GO is not confirmable.

## PM-02 — Cached-verdict staleness defeats CLUS-08's stated intent (HIGH)

**Mechanism.** CLUS-08's purpose is literally "a future model swap cannot silently regress clustering quality". The planned test does: load fixture → read `cached_verdict` → assert FP==0. `MODEL`, `SYSTEM_PROMPT`, `max_tokens`, provider base URL, and the mergeable-state rule are all **inputs that the test never touches**. Someone changes `MODEL = "ibm-granite/granite-4.1-8b"` to whatever is cheap in November; the test stays green forever. The requirement is not satisfied — only its file path is.

**Amendment (`26-03-PLAN.md`, Task 2).** Three additions:
1. Fixture gains a top-level `meta` block written by `26-02`: `{"model": MODEL, "base_url": ..., "system_prompt_sha256": <sha256 of clustering.SYSTEM_PROMPT>, "max_tokens": 220, "temperature": 0.0, "mergeable_rule": "same_event and confidence=='high'", "generated": <iso>, "calls": N}`.
2. New test `test_cached_verdicts_match_current_model_config`: imports `MODEL`, `SYSTEM_PROMPT` from `pipeline.news.clustering`, recomputes the prompt hash, and asserts equality with `meta`. Failure message: *"clustering model/prompt changed — the cached golden-set verdicts are stale; re-run `pipeline/scripts/build_golden_set.py --fill-verdicts` and re-confirm the GO gate before shipping."* This is the mechanism that makes a model swap loud.
3. New opt-in live test `test_golden_set_live_reeval`, decorated `@pytest.mark.live_llm` and `@pytest.mark.skipif(not os.environ.get("CLUSTERING_LIVE_EVAL"))`, which re-adjudicates the golden set and recomputes metrics. Register the `live_llm` marker (add a `pytest.ini`/`pyproject` marker entry or a `conftest.py` `pytest_configure` line — `pipeline/tests/conftest.py` currently has no marker registration, so an unregistered mark would emit a warning). It must remain skipped by default so CI stays offline and the budget is untouched.

## PM-03 — Vacuous precision from fail-safe verdicts (HIGH)

**Mechanism — verified against real code.** `26-01`'s `client = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"), ...)` copies `classifier.py:75-79`. **No plan calls `load_dotenv`** — grep shows dotenv is loaded only in `scrape_news.py:162-165`, `archive_r2.py:59`, `repair_sexual_family.py:173`. A gsd-executor subprocess will very plausibly have no `OPENROUTER_API_KEY` in its environment even though `.env` has one. Then:

`_call_verdict_api` → `AuthenticationError` → returns `None` → `adjudicate_pair` returns `_NO_MERGE_VERDICT` → `26-02` T2 writes that object into `cached_verdict` **indistinguishably from a real verdict** → `26-03` computes TP=0, FP=0, FN=all → `precision = TP/(TP+FP) = 0/0`. Whatever convention the executor picks for 0/0 (`1.0` guard is the natural one, since "no merges ⇒ no wrong merges"), the pytest `assert fp == 0 and precision == 1.0` **passes**, the report prints "precision 1.0, FP 0", and Fable issues **GO on a run that made zero successful LLM calls**. The same happens partially under sustained `RateLimitError`.

**Amendments.**
- `26-01-PLAN.md` Task 2: `_NO_MERGE_VERDICT`'s `rationale` must be a machine-detectable sentinel (`"__FAILSAFE_NO_MERGE__"`), and `adjudicate_pair` must expose *why* it failed — either a second return value or a `ClusterVerdict` extra field `source: Literal["model","failsafe_api","failsafe_parse"]`. Add a unit test asserting an `AuthenticationError` path yields `source == "failsafe_api"`, not a bare `same_event=False`.
- `26-02-PLAN.md` Task 2 (preflight): before any call, assert `os.environ.get("OPENROUTER_API_KEY")` is a non-empty, non-`"placeholder"` value and make exactly **one** probe call; abort the task with a loud error if it fails. Load `.env` the way `scrape_news.py:162-165` does (try/except `dotenv`). Also: **never persist a verdict whose `source != "model"`** — leave `cached_verdict: null` and record the pair in a `failed_pairs` list; the fixture is not final while `failed_pairs` is non-empty. (Note the memory gotcha: *unset GH secrets = empty strings*, so check emptiness, not just presence.)
- `26-03-PLAN.md` Task 1/2: `compute_pairwise_metrics` must return `tp, fp, fn, tn, precision, recall, n_pairs, n_failsafe` and set `precision = None` when `tp + fp == 0` (never 1.0). The report must print TP as an integer next to precision. The pytest must assert `fp == 0 **and** tp > 0 and n_failsafe == 0` — a run that merges nothing is not a passing run, it is an unmeasured run. This does not reopen the locked gate; it defines its denominator.

## PM-04 — NO-GO leaves a permanently red suite (HIGH)

**Mechanism.** `26-03` T2 says the assertion must not be loosened; `26-04` says on NO-GO make no changes. Correct on evidence integrity, catastrophic on process: the directive requires "*Every phase leaves validators (14) + pytest green before being marked complete*". A NO-GO therefore leaves `pipeline/tests` red for the remaining 7 phases, and every later phase's green-suite gate becomes unreadable (executors will be tempted to "fix" the red test — the worst possible outcome).

**Amendment (`26-03-PLAN.md` Task 2 + `26-04-PLAN.md` Task 1).** Split the concern:
- `test_golden_set_metrics_match_recorded_baseline` — asserts the computed `tp/fp/fn/precision/recall` equal a `baseline` block written into the fixture `meta` by `26-03`. **Always green**, and it is the true regression sentinel (any fixture or metric-code change breaks it).
- `test_golden_set_meets_go_gate` — asserts `fp == 0 and tp > 0`. On GO it passes. On NO-GO, `26-04` Task 1 does **not** weaken it: it adds `@pytest.mark.xfail(reason="Phase 26 NO-GO: measured FP=<n> on <date>; see 26-SPIKE-REPORT.md", strict=True)`. `strict=True` means the day the gate would pass, the xfail itself fails and forces a re-decision. Suite green, evidence intact, verdict recorded in code.

## PM-05 — The pre-filter is measured inert, and its threshold is the gate's silent kill switch (MEDIUM)

**Mechanism — measured, not theorized.** I ran `rapidfuzz.fuzz.token_set_ratio` over the two mandatory buckets:

- 2101/2026-07-01: 36 pairs — 13 same-event, 23 cross-event. **Minimum score across all 36 = 48.7.** At `_PREFILTER_THRESHOLD = 45.0`, **36/36 proposed** (including 23/23 negatives).
- 4102/2026-07-01: 28 pairs — **28/28 proposed**.

Two consequences. (a) `26-03` T1 step 7 must report a "reduction ratio" as CLUS-02 evidence; the honest number here is ~0% — the pre-filter bounds nothing on real data, and the actual cost bound is the `(cut,date)` bucketing (also note bucket sizes: 130 buckets of 2, but one of 26 → 325 pairs, one of 16 → 120). Presenting 45.0 as a cost control would be a false claim in the spike report. (b) The reverse is the real hazard: cross-event scores cluster in 48–61 and same-event in 52–85, i.e. **they overlap**. Any later "tuning" of the threshold to 55/60 for cost silently removes most adversarial negatives from the candidate set — FP has no opportunity to occur, precision is 1.0 by construction. This is Pitfall 2 in `26-RESEARCH.md` and the plans currently have no structural defense.

**Amendments.**
- `26-01-PLAN.md` Task 1: keep `_PREFILTER_THRESHOLD = 45.0` and add a docstring line stating it was **pre-registered before measuring precision** and that on the mandatory buckets it proposes 100% of pairs (measured 2026-07-29, min observed score 48.7) — so its purpose is a lexical floor, not a cost lever.
- `26-02-PLAN.md` Task 1: store `prefilter_score` on every candidate pair, and additionally emit **all** intra-bucket pairs for the two mandatory buckets regardless of threshold, marking each `proposed: true|false`. Pairs with `proposed: false` are labeled and, if `label=="merge"`, counted as FN ("filtered before LLM"); they are never adjudicated (no cost) and never enter the precision numerator/denominator.
- `26-03-PLAN.md` Task 1: the report must state, as separate integers: negatives in the golden set, **negatives actually adjudicated by the LLM**, positives adjudicated, and pairs filtered pre-LLM. A GO where `negatives_adjudicated` is small relative to `negatives` is not a GO — add an explicit line `negatives_adjudicated / negatives = N/M` immediately above the verdict line.

## PM-06 — Pair-count control invites cherry-picking (MEDIUM)

**Mechanism.** Mandatory buckets = 36 + 28 = **64 pairs**, already at the top of the 60–100 band before a single supplemental bucket. `26-02` T1 then asks for "15–20 additional buckets with between 2 and 5 articles" — that is 1 to 10 pairs each, i.e. **15 to 200 more pairs**. The plan's remedy is "trim or re-run the sampling stride", and trimming individual pairs after seeing labels is precisely the biasing move `26-RESEARCH.md` Pitfall 2 forbids.

**Amendment (`26-02-PLAN.md` Task 1).** Replace step 4 with a deterministic accumulation: sort eligible buckets (size 2–5, excluding the two mandatory) by `(cut, date)`; walk them in order adding **whole buckets** while `total_pairs + C(size,2) <= 100`; stop. Record `selected_buckets` and `total_pairs` in the fixture `meta`. Individual pairs may never be dropped to hit a count; only whole buckets, and only from the tail of the deterministic order.

## PM-07 — Live fill loop is not resumable (MEDIUM)

**Mechanism.** OpenRouter 429s are routine. As written, the fill loop makes N calls, dies at pair 61, and the executor re-runs it from zero — paying 60 calls again — or, worse (with PM-03), completes with 40 fail-safe verdicts baked in.

**Amendment (`26-02-PLAN.md` Task 2).** The `--fill-verdicts` loop must: (1) write the fixture back to disk after **every** pair (or every 10) so progress survives; (2) skip pairs that already carry `cached_verdict` with `source == "model"` — making re-invocation idempotent and cheap; (3) sleep-and-retry once on `RateLimitError` (mirror `classifier.py`'s hand-rolled single retry — do **not** add tenacity, per research); (4) abort the whole loop after 3 consecutive non-model outcomes rather than grinding through 100 failures.

## PM-08 — The 2,000-call cap is not actually enforced (MEDIUM)

**Mechanism.** The counter lives inside one invocation of the fill loop. Nothing accumulates across invocations, across the exploratory calls `26-RESEARCH.md` budgets (~20–50), across the 3 ping calls, or across re-runs after a threshold change. Four re-runs at 400 calls = 1,600 calls with the in-process counter never exceeding 400. The cap is prose.

**Amendment (`26-02-PLAN.md` Task 2).** `26-CALL-LOG.md` becomes an **append-only ledger** (one row per invocation: timestamp, script, calls, cumulative). The fill loop reads the last cumulative total at startup, adds its own projected `len(pairs_to_fill)`, and **refuses to start** if the projection exceeds 2,000 — writing the NO-GO-by-cost note the directive requires. Seed the ledger with the 3 spike-ping calls.

## PM-09 — GO ships a schema field with no producer (MEDIUM)

**Mechanism — verified in code.** `store.py:merge_and_write` builds `payload = {..., "incidents": current_incidents}` from **plain dicts** and validates them; it never calls `model_dump()`. `build_incident()` returns a fixed 11-key dict with no `cluster_id`. So after a GO, `IncidentRecord` accepts the fields, but **no code path ever writes them** and `current.json` never contains them. Phase 28's NEWSUI-05 ("clustered events render as a primary-article card") would then be planned against data that does not exist, and Phase 28 would either discover this late or improvise a clustering call into the news cron unplanned. (Silver lining, which should also be stated: because `store.py` writes dicts rather than dumped models, the schema addition causes **zero** `data/` churn and cannot fire a spurious Cloudflare rebuild — that is worth recording as verified rather than assumed.)

**Amendment (`26-04-PLAN.md` Task 2).** The report's "Schema change status" section must add, verbatim in substance: *"`store.py:merge_and_write` writes raw dicts (not `model_dump()`), so adding these fields changes no existing output byte and produces no `data/` diff. It also means **nothing populates `cluster_id` yet**: a producer step (clustering run after `dedup.deduplicate` inside `scrape_news.py`, writing `cluster_id`/`is_primary` into `build_incident`'s dict) is required before Phase 28 can render clusters. Recorded as a Phase 28 prerequisite in STATE.md."* Add the matching STATE.md entry in the same task.

## PM-10 — Verify command references an unimplemented flag (MEDIUM)

`26-02` T1's `<verify>` runs `python pipeline/scripts/build_golden_set.py --dry-run`, but the `<action>` never specifies a `--dry-run` mode (nor `--fill-verdicts`, which T2 mentions only as one of three vague options: "may live inline … or as an ad-hoc one-time invocation — either is acceptable"). An autonomous executor facing a failing verify command improvises, and "ad-hoc one-time invocation" means no reproducible artifact.

**Amendment (`26-02-PLAN.md` Tasks 1–2).** Specify the CLI contract explicitly in T1: `--dry-run` (sample + report counts, write nothing), default (write the draft), `--fill-verdicts` (live calls, resumable per PM-07), `--out PATH`. Delete the "ad-hoc invocation is acceptable" language in T2 — the filling path must be the committed `--fill-verdicts` mode so the fixture is reproducible.

## PM-11 — Draft fixture leaks into the commit (MEDIUM)

`26-02` T1 writes `pipeline/tests/fixtures/clustering_golden_set_draft.json`; T2's acceptance says it must be "cleaned up or gitignored". I checked `.gitignore`: **there is no such entry**, and the GSD executor commits atomically per task — so T1's commit almost certainly includes an unlabeled draft with `label: null`, which a later reader can mistake for the golden set (note there is already an unrelated `pipeline/tests/fixtures/golden_set.json` for the classifier — name confusion is live).

**Amendment (`26-02-PLAN.md` Task 1).** Write the draft to `.planning/phases/26-event-clustering-spike/26-golden-set-draft.json` (phase-local working artifact, clearly not a fixture) or to the session scratchpad, and never under `pipeline/tests/fixtures/`. Only the final labeled fixture lands in `fixtures/`.

## PM-12 — Report/test divergence at close-out (MEDIUM)

`26-04` T2 replaces the verdict line and asks the executor to write "the exact measured precision value … copied from the live test result". Hand-copying a number that already exists in a generated artifact is how the report ends up saying `precision 1.0, FP 0` while the fixture says otherwise (e.g. after a PM-07 partial refill).

**Amendment (`26-04-PLAN.md` Task 2).** Re-run `python pipeline/scripts/run_clustering_spike.py` first so the entire report body (matrix + metrics) is machine-regenerated from the current fixture, then edit **only** the verdict line. Add an acceptance criterion: the precision/FP/recall values in the report equal the values printed by `run_clustering_spike.py` in the same session (diff-checked, not remembered).

## PM-13 — A red test is not automatically a NO-GO (MEDIUM)

`26-04` T1: "IF the test PASSES … GO. IF the test FAILS (FP > 0) … NO-GO." But a test can be red from an `ImportError` (`pipeline.scripts.run_clustering_spike` import), a missing fixture, a `ZeroDivisionError` in the 0/0 case (PM-03), or a `KeyError` on a malformed pair. An autonomous executor following the letter of the plan would then publish **NO-GO** — a wrong verdict in the pessimistic direction, killing NEWSUI-05 for the milestone on a typo.

**Amendment (`26-04-PLAN.md` Task 1).** Require the executor to read the failure reason: NO-GO **only** when the failure is the gate assertion with `fp > 0` and the FP `pair_id`s are printed. Any error/collection failure is a **blocker** → record in STATE.md `## Blockers`, fix (max 2 cycles per directive), do not issue a verdict. Also require the FP `pair_id`s to be copied into the report so a NO-GO is auditable pair-by-pair (and so PM-01's mislabel risk can be re-examined against them).

## PM-14 — The confidence half of the mergeable rule is probably inert (MEDIUM)

`26-00-SPIKE-PING.md` shows 3/3 verdicts with `confidence: "high"`, including both negatives. `ClusterVerdict.confidence` is `Literal["high","low"]`, so a model emitting `"medium"` fails Pydantic and lands on the fail-safe path (correct, but invisible). Net effect: the "high-confidence edge threshold" that `26-RESEARCH.md` presents as a precision safeguard may never reject anything, and the report will imply a two-factor gate.

**Amendment (`26-03-PLAN.md` Task 1).** The report must include the confidence distribution across the golden set (`high: N, low: M`), the count of pairs that reached the fail-safe path, and — if `low == 0` — an explicit sentence: *"the `confidence == 'high'` condition rejected 0 pairs on this golden set; measured precision rests entirely on `same_event`."*

## PM-15 — Ground truth is no better informed than the model (MEDIUM)

**Mechanism.** `26-02` T2 tells the labeler to "read `title_a`/`title_b` and assign `merge` only when both headlines plainly describe the same real-world incident" — i.e. the labeler sees **exactly the same 2 strings** `_build_user_content` sends to Granite (`26-01` T2 restricts the user turn to the two `Titular` lines). An evaluation where the oracle and the system have identical evidence measures *agreement*, not *correctness*, and it biases toward agreement precisely on ambiguous pairs — the Tongoy case in PM-01 is the concrete instance.

**Amendment (`26-02-PLAN.md` Tasks 1–2).** The fixture keeps `url_a`/`url_b` (PM-01), and the labeler must consult the source article (or, where the URL is unfetchable — remember Google News URLs are JS pages and unfetchable, per project memory — the archived R2 full text) for **every pair it labels `merge`**. Pairs whose `merge` label rests on headlines alone get `label_confidence: "low"` and are **excluded from the precision denominator** (still reported, in a separate "headline-only, excluded" table). This is the amendment that makes the 100% gate mean something.

## PM-16 — Secret leakage (LOW) — **accepted with one guard**

Verified: the fixture stores only IDs, labels, notes, titles/URLs and model verdict JSON; `26-CALL-LOG.md` stores counts; `.env` and `.env.*` are gitignored; `clustering.py` reads the key once into the `OpenAI` object; `classifier.py`'s log lines carry status codes and `title[:60]` only. Residual risk is a bare `except Exception` printing a traceback that includes request kwargs, or an executor pasting a shell env dump into a summary.

**Accepted**, with one cheap guard added to `26-01-PLAN.md` Task 2 acceptance criteria: `grep -riE "sk-or-|OPENROUTER_API_KEY\s*=" pipeline/ .planning/phases/26-event-clustering-spike/` returns nothing, and no log statement passes the `messages` list or the `kwargs` dict to the logger.

## PM-17 — `data/` mutation (LOW) — **accepted**

I traced every command in all four plans. No task opens anything under `data/` in write mode: `build_golden_set.py` reads `current.json` only and is explicitly forbidden from importing `merge_and_write`/`atomic_write_json` (T-26-05, with a grep acceptance criterion); `run_clustering_spike.py` reads the fixture; `26-04` touches `schema.py`, a test file, and the report. `26-04`'s `npm run build` runs `sync-data.mjs`, which copies repo-root `data/cead` **into** the gitignored `site/public/data` (one-way, source untouched). `26-02`/`26-04` both verify with `git diff --stat -- data/`. **Accepted.** One note for the executor: `26-04`'s chained `python -m pytest … && cd site && npm run build && npm run validate` already respects the OneDrive single-command rule — keep it chained.

## PM-18 — Non-pytest backward-compat consumers (LOW) — **accepted, document**

Swept the consumers `26-PATTERNS.md` flags plus the ones it does not:
- `pipeline/tests/test_schema_incidents.py:59` — exact `set(incident.keys())` assertion. **Will break** on the schema change; `26-04` T1 correctly makes the edit mandatory. ✔
- `pipeline/tests/test_scrape_news.py:346` — uses `required_fields - set(...)` (subset). Safe.
- `pipeline/archive_r2.py:245-251` — `csv.DictWriter(fieldnames=[...], extrasaction="ignore")` with `inc.get(f, "")`. Safe; new fields silently omitted from `incidents.csv`. Worth one report line so a future reader knows the R2 CSV deliberately does not carry `cluster_id`.
- `incidents.jsonl` / `corpus-state.json` — built from raw dicts. Unaffected (see PM-09).
- `site/src/components/map/IncidentPinLayer.ts:42-54` — hand-kept mirror with `slug?: string`. Extra JSON keys are inert at runtime and, per PM-09, will not appear in the data anyway. Mirroring the fields in TS is **not** required by Phase 26 and would be dead code; note the deliberate deferral to Phase 28 in the report rather than editing `site/**` in a pipeline-only phase.
**Accepted**; fold the four bullets into `26-SPIKE-REPORT.md`'s backward-compat section so the Opus code reviewer does not re-litigate.

## PM-19 — Same-date-only scope (LOW)

Every golden-set bucket is a single `(cut, date)`; the "±1 day optional" extension is never exercised, and multi-day follow-up coverage (arrest → formalization → sentencing, which the 2101 bucket hints at) is untested. A GO sentence reading "Granite can group same-event coverage" over-claims.

**Amendment (`26-03-PLAN.md` Task 1).** One scope sentence in the report: *"measured on same-`(cut,date)` buckets only; the ±1-day window and cross-day procedural follow-ups are untested and out of scope for this verdict."*

---

## Amendments for the planner

Apply mechanically. Each line names the plan file, the task, and the change.

**`26-01-PLAN.md`**
1. **Task 1** — add a docstring/comment on `_PREFILTER_THRESHOLD = 45.0` recording it as pre-registered before any precision measurement, and that on the two mandatory buckets it proposes 100% of pairs (min observed `token_set_ratio` = 48.7, measured 2026-07-29) → it is a lexical floor, not a cost control. *(PM-05)*
2. **Task 2** — make fail-safe outcomes machine-detectable: `_NO_MERGE_VERDICT.rationale = "__FAILSAFE_NO_MERGE__"`, and `adjudicate_pair` must report provenance (`source: Literal["model","failsafe_api","failsafe_parse"]` on `ClusterVerdict`, or a second return value). Add a unit test that an `AuthenticationError` side-effect yields `source == "failsafe_api"`. *(PM-03)*
3. **Task 2 acceptance** — add: `grep -riE "sk-or-|OPENROUTER_API_KEY\s*=" pipeline/ .planning/phases/26-event-clustering-spike/` returns nothing; no logger call receives `messages` or the `kwargs` dict. *(PM-16)*

**`26-02-PLAN.md`**
4. **Task 1, step 4** — replace the "15–20 buckets" stride with deterministic whole-bucket accumulation: sort eligible size-2–5 buckets by `(cut,date)`, add whole buckets while `total_pairs + C(size,2) <= 100`, stop. Record `selected_buckets`/`total_pairs` in fixture `meta`. Never drop individual pairs to hit a count. *(PM-06)*
5. **Task 1, step 5** — store `prefilter_score` per pair; for the two mandatory buckets emit **all** intra-bucket pairs with `proposed: true|false`; `proposed: false` pairs are labeled but never adjudicated and never enter precision (count `merge` ones as FN). *(PM-05)*
6. **Task 1, step 6** — write the draft to `.planning/phases/26-event-clustering-spike/26-golden-set-draft.json`, **not** under `pipeline/tests/fixtures/`. *(PM-11)*
7. **Task 1** — specify the CLI contract explicitly: `--dry-run`, default (write draft), `--fill-verdicts`, `--out PATH`; the verify command must match an implemented flag. *(PM-10)*
8. **Task 2 (labels)** — re-label the 4102 bucket as `{6eed24180c36dbec}` vs the other 7, with the 7 cross pairs defaulting to `no_merge` unless the source articles prove one case ("19 años / homicidio" vs "8 años y medio / homicidio frustrado" is a case difference, not reporting noise). Re-examine 2101 Event C for `16439f8dc78173a6` (aggregate "dos operativos") and `b01de8947aa555f6` (later formalization stage) on the same standard. *(PM-01)*
9. **Task 2 (labels)** — every `merge` label requires a **blind second pass** by a separate agent seeing only titles/outlets/URLs (never `cached_verdict`); disagreement resolves to `no_merge` or `excluded: "label_disputed"`. `no_merge` labels need no second pass. *(PM-01)*
10. **Task 2 (labels)** — every pair carries `label_basis` (`fecha|lugar|actores|sentencia|etapa_procesal`) and retains `title_a/title_b/outlet_a/outlet_b/url_a/url_b`. Delete the permission to strip titles from the final fixture. *(PM-01)*
11. **Task 2 (labels)** — `merge` labels resting on headlines alone get `label_confidence: "low"` and are excluded from the precision denominator (reported separately); labels for `merge` pairs should consult the source URL (or the R2 archived full text where the URL is unfetchable). *(PM-15)*
12. **Task 2 (preflight)** — load `.env` as `scrape_news.py:162-165` does; assert `OPENROUTER_API_KEY` is non-empty and not `"placeholder"`; make one probe call; abort loudly on failure. *(PM-03)*
13. **Task 2 (fill loop)** — never persist a verdict with `source != "model"` (leave `cached_verdict: null`, append to `failed_pairs`; fixture is not final while non-empty); write the fixture after every pair; skip pairs already holding a model verdict (idempotent restart); one sleep-retry on `RateLimitError`; abort after 3 consecutive non-model outcomes. *(PM-03, PM-07)*
14. **Task 2 (budget)** — make `26-CALL-LOG.md` an append-only ledger with a cumulative column, seeded with the 3 spike-ping calls; the fill loop reads the last cumulative total and refuses to start if `cumulative + projected > 2000`, writing the NO-GO-by-cost note. *(PM-08)*
15. **Task 2 (fixture `meta`)** — write `meta`: `model`, `base_url`, `system_prompt_sha256`, `max_tokens`, `temperature`, `mergeable_rule`, `generated`, `calls`, `selected_buckets`, `total_pairs`. *(PM-02)*

**`26-03-PLAN.md`**
16. **Task 1** — `compute_pairwise_metrics` returns `tp, fp, fn, tn, precision, recall, n_pairs, n_failsafe`; `precision = None` when `tp + fp == 0` (never 1.0). Report prints TP as an integer beside precision. *(PM-03)*
17. **Task 1, step 7** — report these as separate integers: negatives in set, **negatives actually adjudicated**, positives adjudicated, pairs filtered pre-LLM, plus the honest reduction ratio (expect ≈0% — state that the real cost bound is `(cut,date)` bucketing, and note the largest buckets: 26 articles → 325 pairs, 16 → 120). Add the line `negatives_adjudicated / negatives = N/M` directly above the verdict line. *(PM-05)*
18. **Task 1** — report the confidence distribution and fail-safe count; if `low == 0`, state explicitly that the `confidence == "high"` condition rejected 0 pairs and precision rests entirely on `same_event`. *(PM-14)*
19. **Task 1** — add the scope sentence: measured on same-`(cut,date)` buckets only; ±1-day and cross-day procedural follow-ups untested. *(PM-19)*
20. **Task 1** — add the line `merge-labels independently confirmed: N/N (blind second pass)`. *(PM-01)*
21. **Task 2** — split the tests: `test_golden_set_metrics_match_recorded_baseline` (asserts computed metrics equal fixture `meta.baseline`; always green) **and** `test_golden_set_meets_go_gate` (asserts `fp == 0 and tp > 0 and n_failsafe == 0`). *(PM-03, PM-04)*
22. **Task 2** — add `test_cached_verdicts_match_current_model_config`: recompute `sha256(SYSTEM_PROMPT)` and compare `MODEL`/prompt-hash/`max_tokens`/`temperature`/`mergeable_rule` against fixture `meta`; failure message tells the reader to re-run `--fill-verdicts` and re-confirm the gate. *(PM-02)*
23. **Task 2** — add `test_golden_set_live_reeval`, `@pytest.mark.live_llm` + skipped unless `CLUSTERING_LIVE_EVAL` is set; register the `live_llm` marker (`pytest_configure` in `pipeline/tests/conftest.py`, which currently registers none) so no unknown-mark warning appears. *(PM-02)*

**`26-04-PLAN.md`**
24. **Task 1** — verdict rule: NO-GO **only** when `test_golden_set_meets_go_gate` fails on the gate assertion with `fp > 0`; any import/collection/runtime error is a STATE.md blocker, never a verdict. Copy the FP `pair_id`s into the report. *(PM-13)*
25. **Task 1** — on NO-GO, do not weaken the gate test: add `@pytest.mark.xfail(reason="Phase 26 NO-GO: FP=<n> <date>; see 26-SPIKE-REPORT.md", strict=True)` so the suite is green, the verdict is encoded, and a future pass re-opens the decision. *(PM-04)*
26. **Task 2** — regenerate the report by re-running `run_clustering_spike.py`, then edit only the verdict line; add an acceptance criterion that the report's precision/FP/recall equal the values printed in the same session. *(PM-12)*
27. **Task 2** — add to "Schema change status": `store.py:merge_and_write` writes raw dicts (not `model_dump()`), so the addition produces **zero** `data/` diff — and consequently **nothing populates `cluster_id` yet**; a producer step (clustering after `dedup.deduplicate` inside `scrape_news.py`) is a Phase 28 prerequisite. Add the matching STATE.md entry. *(PM-09)*
28. **Task 2** — add a backward-compat section recording the verified consumer sweep: `test_schema_incidents.py:59` key-set (edited), `test_scrape_news.py:346` (subset, safe), `archive_r2.py:245-251` (`extrasaction="ignore"`, new fields deliberately absent from `incidents.csv`), `incidents.jsonl`/`corpus-state.json` (raw dicts, unaffected), `IncidentPinLayer.ts:42-54` (TS mirror deliberately **not** edited in this pipeline-only phase; deferred to Phase 28). *(PM-18)*
