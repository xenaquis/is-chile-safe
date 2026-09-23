# Phase 34: News Classification Restore — Research

**Researched:** 2026-09-22
**Domain:** LLM-classifier outage recovery (OpenRouter model delisting), Python pipeline, GitHub Actions alerting
**Confidence:** HIGH (all core claims measured directly against repo HEAD and live OpenRouter API; no LLM completion calls made)

## Summary

The news classification pipeline has been silently dead since 2026-09-04T20:12Z because
`pipeline/news/classifier.py` hard-codes `ibm-granite/granite-4.1-8b`, which OpenRouter
delisted (0 endpoints, confirmed live today). Every classification attempt returns `None`,
which `scrape_news.py` files as a permanent `rejection_stage: "classifier_none"` — but the URL
is marked `seen` at the top of the classify loop (line 304), so it is never retried. The
pipeline exits 0 every run (by design — WR-03 "fail with grace"), so neither the 6-hourly cron
nor the daily heartbeat (which reads `current.json.generated`, rewritten on every run
regardless of whether anything was classified) has ever fired an alert.

Today (2026-09-22), **2,296** items in `data/incidents/rejected/2026-09.json` carry
`rejection_stage: classifier_none`; **2,057** of them have `first_seen >= 2026-09-04T20:13:49Z`
(the outage start), growing ~80-145/day. `current.json` holds only incidents dated
2026-08-23..2026-09-04 (30-day rolling window) — it goes empty on/around 2026-10-04/05 as the
window slides past the last successful classification, exactly matching the directive's
deadline.

Recovery is cheap in one specific sense: `record_rejected()` already persisted the exact
classifier inputs (title/description/url/outlet/date) for every lost item, so a backfill tool
can reclassify without refetching. The existing A/B harness (`pipeline/experiments/ab_score.py`)
already drives the **production** `classify()` function against a 47-item golden set and
already computes the 5 required metrics — it needs to become model-parameterized (currently
only `--provider {deepseek,minimax}`, no OpenRouter model override) rather than rebuilt. All 4
NREC-01 candidates are live on OpenRouter today with real endpoints and pricing, and — new risk
surfaced this session — **all 4 support a `reasoning` parameter that defaults to enabled** on
several endpoints, which could silently eat the `max_tokens=512` budget before the JSON answer
is emitted; this must be tested/disabled explicitly, not assumed off.

**Primary recommendation:** Model-parameterize `pipeline/experiments/ab_score.py` to accept
`--provider openrouter --model <candidate>` (rather than writing a new eval script), run it
against all 4 NREC-01 candidates with `extra_body={"reasoning": {"enabled": False}}` (or
equivalent) set explicitly and measured for both content presence and reasoning_tokens=0, pick
a winner by the pre-declared thresholds, then harden `classifier.py` (config-driven model id,
typed outcomes, retry/backoff — tenacity is already a dependency), add a post-commit health-gate
+ issue step to `news-pipeline.yml`, backfill the 2,057 lost items from
`rejected/2026-09.json`, and verify prod before 2026-10-05.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Model selection / provider config | Python pipeline (classifier.py) | GitHub Actions env | Model id must be config-driven (env var), not hard-coded; workflow only supplies secrets |
| Classification retry/backoff | Python pipeline (classifier.py `_call_api`) | — | In-process; tenacity already a pipeline dependency |
| Circuit breaker / typed outcome propagation | Python pipeline (classifier.py → scrape_news.py) | — | classify() must distinguish "API down" from "genuinely non-crime" so scrape_news.py can choose NOT to mark-seen on transient failure |
| Post-commit health gate + alert | GitHub Actions (news-pipeline.yml) | GitHub Issues API | Existing `if: failure()` alert pattern only fires on non-zero exit; needs a new step that inspects classification counts, not just exit code |
| Freshness/heartbeat | GitHub Actions (heartbeat.yml) + site/scripts/validate/freshness.mjs | — | Both read `current.json.generated`, which is a rewrite-every-run field — orthogonal signal to health gate; do not conflate |
| Backfill of lost items | Local machine (`python pipeline/...`) | data/incidents/rejected + current.json | Golden rule from directive: race-avoidance requires this NOT run inside the 6-hourly cron's concurrency group |
| Golden-set eval / A/B | Local machine or CI dispatch | pipeline/experiments/ab_score.py | Already exists, reuses production classify() — extend, don't rebuild |

## User Constraints

No CONTEXT.md exists for Phase 34 (not yet produced by discuss-phase). The governing constraints
instead come from `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md` (verbatim excerpts below — this
section substitutes for CONTEXT.md per that file's authority as source of truth for this run).

### Locked Decisions (from AUTONOMOUS-DIRECTIVE.md, Phase 34 notes + owner-decision defaults)
- Replacement model: winner of the NREC-01 A/B by pre-declared thresholds. Tie-break: more live endpoints, then lower cost.
- Backup provider: DeepSeek direct API (`DEEPSEEK_API_KEY`) — already funded, balance USD 23.24 confirmed today.
- Backfilled incidents keep original publication dates; add one bilingual methodology-page line about the 2026-09-04..N reclassification.
- Do NOT re-classify Granite-era published incidents (07-27..09-04) this milestone — fix forward only, list in deferred-live.
- Order inside phase: (1) eval runner+A/B → pick winner (G-NN) → (2) config/preflight/backup/typed-outcomes/retry/circuit-breaker → (3) alarm (post-commit health gate + issue) + heartbeat → (4) push+verify live classifying → (5) backfill 2,057+ items → (6) prod verification before 2026-10-05.
- Fast-path rule: if no green classifier on prod by 2026-09-30, ship a minimal hotfix via `/gsd:quick` (env-configurable model id = A/B winner or `deepseek/deepseek-v4-flash` fallback), single opus validation, then continue the rest of Phase 34 normally (record as G-NN).
- Spend cap: USD 10 for the whole run; over USD 5 in this phase or over run cap → pause. A/B estimate ~USD 0.2, backfill ~USD 0.3-1.4.
- Push authorized only after green gate, never mid-phase, never `--force`, always after `git pull --rebase` (cron commits ~4x/day — expect rebases, see § Race below).
- Backfill: dry-run first (counts only, zero writes), then real run on branch-free working tree, backup copies of `current.json`/`rejected/2026-09.json` in scratchpad first. Report accepted/rejected split as measured numbers.
- `data/` mutation allowed ONLY for: NREC-09 backfill (dry-run+backup first), pipeline's own normal runs, HYG-06 CEAD output. Any other edit → pause.
- Never touch locked decisions: CEAD FAMILY_KEYS=7 (never add "sexuales" there — it stays news-only per project memory), national_rank #1=most-reported, no heat maps/severity scores, no LLM clustering.

### Claude's Discretion
- Exact candidate model chosen among the 4 NREC-01 candidates — decided by measured A/B, not preference.
- Internal structure of typed outcomes / retry / circuit breaker (as long as functionally equivalent to what's described).
- Whether the health-gate step lives in news-pipeline.yml as a new step vs. a separate script — directive says "post-commit health gate", implementation detail is open.

### Deferred Ideas (OUT OF SCOPE)
- Granite-era (07-27..09-04) re-classification — explicit owner "NO" this milestone.
- GSC sitemap submission (HYG-07).
- `/map/` vs `/chile-crime-map/` noindex/redirect decision.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NREC-01 | Select a replacement classifier model via measured A/B across ≥3 candidates | §"Endpoints census" below: all 4 candidates confirmed live with pricing/params today; `ab_score.py` extension plan in §Code Examples |
| NREC-02 (implied: config-driven model) | Classifier model id must not be hard-coded | §"Classifier code map": exact 3 hard-code sites found (classifier.py:79, clustering.py:60, test_classifier.py:120-121) |
| NREC-03 | Unit test proving granite-4.1-8b returns 0 live endpoints | Verbatim JSON fixture captured in §"Endpoints census" |
| NREC-08 (implied: alerting) | Post-commit health gate + issue on classifier failure | §"Workflow" — exact `if: failure()` pattern, label-then-alert two-step, to extend |
| NREC-09 | Backfill 2,057+ lost items from rejected/2026-09.json | §"Backfill population" — exact counts, date range, seen.json overlap measured |
| (heartbeat/freshness accuracy) | Both instruments currently blind to classifier failure | §"Workflow" — heartbeat reads `current.json.generated`, freshness.mjs same field, neither reflects classification success rate |

## Standard Stack

### Core (already installed — pipeline/requirements.txt, verified via `pip show`/import)
| Library | Version (pinned in requirements.txt) | Purpose | Why Standard |
|---------|---------|---------|---------------|
| openai | 2.53.0 (repo pin; **2.34.0 installed locally** — drift, see Pitfall below) | LLM client (OpenRouter + DeepSeek both OpenAI-compatible) | Already the project's sole LLM client; `max_retries` default=2 confirmed via `inspect.signature(OpenAI.__init__)` on the locally installed 2.34.0 |
| tenacity | 9.1.4 | Retry/backoff | Already a pinned dependency — NOT missing, contrary to a naive assumption. Use it for the classifier retry step instead of hand-rolling a loop. |
| pydantic | 2.13.4 | Response validation (`ClassifierOutput`) | Already used; extend, don't replace |
| PyYAML | 6.0.3 | Workflow-order tests (`test_workflow_order.py`) parse `.github/workflows/*.yml` | Already a dependency — comment in requirements.txt warns CI installs only this file, so absence there silently SKIPs 6 tests |

No new packages are required for this phase — the model swap is a config/string change, the
retry logic reuses `tenacity` already in requirements.txt, and the eval harness already exists.
**Package Legitimacy Audit is not applicable** — no new external packages are being installed.

### Alternatives Considered (NREC-01 candidates — all confirmed live via `GET /models/{id}/endpoints` today, 2026-09-22)

| Model | Endpoints (count) | Cheapest endpoint (in/out per 1M) | Context | `reasoning` param present | Notes |
|-------|---|---|---|---|---|
| `deepseek/deepseek-v4-flash` | 15 (OpenInference, StreamLake, DeepInfra, GMICloud, Venice, DigitalOcean, SiliconFlow, Alibaba, Baidu, Novita, AtlasCloud, Parasail, NextBit, Mancer 2, Azure) | OpenInference $0.04/$0.50/1M (cache-read $0.014) | up to 1,048,576 | **yes, on every listed endpoint** | Cheapest input token price of the 4; huge endpoint diversity = resilience against a repeat delisting |
| `deepseek/deepseek-v4.1-flash` | 24 (even more providers incl. official `DeepSeek` endpoint itself, Fireworks, CoreWeave, Together, Modal, BaseTen, Phala, Morph, Wafer, Relace, Sail Research, Alibaba w/ time-of-day pricing) | Morph $0.12/$0.48/1M | up to 1,048,576 | **yes, on every listed endpoint** | Most endpoints of the 4 (most resilient); official DeepSeek-provider endpoint listed among them |
| `ibm-granite/granite-4.2-8b` | **2 only** (DeepInfra, CoreWeave) | CoreWeave $0.10/$0.15/1M | 131,072 | yes | Thin endpoint pool — same single-vendor-dependency risk class that killed 4.1-8b; NOT recommended as primary given the outage this phase exists to fix |
| `qwen/qwen3.5-9b` | 6 (Darkbloom, SiliconFlow, DeepInfra, Venice, Parasail, Together) | Darkbloom $0.08/$0.13/1M | 262,144 | yes | Untested against this prompt/golden-set; needs the A/B run like the others |
| `ibm-granite/granite-4.1-8b` (current, DEAD) | **0** | — | — | n/a | Confirmed dead again today — see exact JSON below |

**Tie-break rule from the directive ("more live endpoints, then lower cost") currently favors
`deepseek/deepseek-v4.1-flash` (24 endpoints) or `deepseek/deepseek-v4-flash` (15 endpoints) over
the two thin-pool candidates — but this is ONLY the endpoint-count prior; the actual A/B on
accuracy/null-rate/parse-failure must still run and could override it per the directive's
pre-declared-metrics rule.**

**Installation:** none required — this phase is a config change, not a new dependency.

## Endpoints Census (raw evidence)

`ibm-granite/granite-4.1-8b` — verbatim `GET /api/v1/models/ibm-granite/granite-4.1-8b/endpoints`
response body, captured 2026-09-22 (this is the exact fixture body for the NREC-03 unit test):

```json
{"data":{"id":"ibm-granite/granite-4.1-8b","name":"IBM: Granite 4.1 8B","created":1777577071,"description":"Granite 4.1 8B is a dense, decoder-only 8-billion-parameter language model from IBM, part of the Granite 4.1 family. It supports a 131K-token context window and is designed for enterprise tasks...","architecture":{"tokenizer":"Other","instruct_type":null,"modality":"text->text","input_modalities":["text"],"output_modalities":["text"]},"endpoints":[]}}
```

`endpoints: []` — confirms V-01. A unit test asserting `len(data["endpoints"]) == 0` against
this exact structure (or a live re-check) is the NREC-03 regression proof. **[VERIFIED: OpenRouter API, live GET, no auth needed]**

**Implications for the plan:** the eval runner must be able to select an OpenRouter model by
full id string (`ibm-granite/granite-4.2-8b`, etc.), not rely on `classifier.py`'s current
hard-coded three-branch `if _PROVIDER == ...` structure. The cleanest change is an env var
`NEWS_MODEL` (or `--model` CLI override for the eval script that sets `NEWS_MODEL` before
import) layered on top of the existing `NEWS_PROVIDER` env var, defaulting to the current
literal only for backward compat during the transition.

## Classifier Code Map

**`pipeline/news/classifier.py`** (full file read, 247 lines):
- Provider selection: lines 58-79. Three branches: `deepseek` (65: `deepseek-v4-flash`),
  `minimax` (66-71: `MiniMax-Text-01`), else/default `openrouter` (72-79: hard-codes
  `_MODEL = "ibm-granite/granite-4.1-8b"` at line 79). **This is the single hard-code site that
  must become config-driven.**
- Module-level `client` (OpenAI instance, lines 61/67/75) and `_MODEL` (65/71/79) are both
  **module-level globals set at import time** — this is what `test_default_provider_is_openrouter`
  (test_classifier.py:115-122) and `ab_score.py`'s explicit "each provider MUST be run in a
  separate process invocation" comment (lines 106-119) both depend on. Any refactor that makes
  `_MODEL`/`client` lazily-constructed instead of import-time constants will break both call
  sites — note as an explicit compat constraint for the plan.
- `classify()` (144-202): two-attempt retry already exists but ONLY for the "empty content"
  case (line 163-166: "Empty-content retry (Pitfall 4)"), not for transient HTTP
  errors/timeouts — `_call_api` (211-247) catches `AuthenticationError`, `RateLimitError`,
  `_APIStatusError` (all HTTP-status-derived), and a bare `Exception` catch-all, and **all of
  them return `None` with no distinction from "genuinely not classifiable"**. This is exactly the
  V-01/V-02 root cause: a delisted model produces the same `None` as a low-confidence real
  classification, and `scrape_news.py` cannot tell them apart.
- `_call_api` (211-247): `kwargs` dict built at 214-222, `max_tokens=512` at line 217. No
  `reasoning`/`extra_body` param is passed today — for the 4 NREC-01 candidates (all of which
  advertise `reasoning` as a `supported_parameter`), this is the exact place to add
  `extra_body={"reasoning": {"enabled": False}}` if the eval shows reasoning tokens consuming
  the budget (see §Risks).

**`pipeline/news/clustering.py:60`**: `MODEL = "ibm-granite/granite-4.1-8b"` — a **second,
independent** hard-code of the same dead model, in a different module. Grep-confirmed this is
the only other production hard-code (see full grep below). This is used by the LLM-clustering
feature, which is **explicitly NO-GO / locked per v2.1** (project memory: "LLM clustering stays
NO-GO"). **Implication for the plan: this constant should still be updated for correctness (or
the module documented as dead code) but must NOT be used as a justification to build or run LLM
clustering — that is out of scope and locked.**

**`pipeline/tests/test_classifier.py:116-121`** (`test_default_provider_is_openrouter`):
asserts `_PROVIDER == "openrouter"` AND `_MODEL == "ibm-granite/granite-4.1-8b"` verbatim. This
test **will need updating** to assert the new default model — it currently pins the exact
broken string as "correct" behavior. Flag as a required test change in the plan, not a
regression to preserve.

**Full grep for `granite-4.1-8b` across pipeline/ and .github/ (exhaustive, 5 hits, no others exist):**
```
pipeline/news/classifier.py:8   (docstring)
pipeline/news/classifier.py:73  (comment)
pipeline/news/classifier.py:79  (_MODEL literal)
pipeline/news/clustering.py:60  (MODEL literal)
pipeline/tests/test_classifier.py:116,120,121 (test assertions/docstring)
```

**Mocking surface for tests:** all tests patch `pipeline.news.classifier.client`
(`unittest.mock.patch("pipeline.news.classifier.client")`) — 6 occurrences in
test_classifier.py (lines 45, 58, 72, 82, 92, 107). **Any restructuring that removes the
module-level `client` global breaks all 6 tests.** Keep `client` as a module-level object;
change only what model string it's constructed with / what env var drives it.

## Architecture Patterns

### Data Flow Diagram (current, broken state → target state)

```
RSS feeds (9 sources)
   │
   ▼
scrape_news.py: fetch → keyword filter (is_crime_item) → seen-URL filter
   │
   ▼
candidates[] (capped at NEWS_MAX_CLASSIFY=200)
   │
   ▼
for each candidate:
   seen[url] = date   ◄── CR-02: marked BEFORE classify() result is known
   │
   ▼
classify(title, description)  [pipeline/news/classifier.py]
   │
   ├── _call_api() ── OpenAI-compatible client → OpenRouter (default) or DeepSeek/MiniMax
   │        │
   │        ├── AuthenticationError → None  (silent)
   │        ├── RateLimitError      → None  (silent)
   │        ├── APIStatusError      → None  (silent)  ◄── model-not-found (delisted) lands HERE
   │        └── Exception (catch-all) → None (silent)
   │
   ▼
result is None?
   │
   ├── YES → rejected_items.append(rejection_stage="classifier_none")
   │           → record_rejected() → data/incidents/rejected/YYYY-MM.json
   │           (URL already in `seen` — NEVER retried)
   │
   └── NO  → resolve_cut() → get_centroid() → build_incident() → new_incidents[]
                │
                ▼
          dedup.deduplicate() (0.82 title-similarity within cut+date bucket)
                │
                ▼
          store.merge_and_write() → current.json (30-day window) + archive/YYYY-MM.json
                │
                ▼
          save_seen() → seen.json

[Target state adds:]
   - classify() returns a typed outcome (success | transient-error | genuinely-rejected)
     instead of a bare None, so scrape_news.py can choose NOT to mark transient-error URLs
     as seen (only genuinely-rejected ones), closing the CR-02-created retry gap for outages.
   - _call_api() retried via tenacity (already a dependency) with exponential backoff on
     transient error classes (RateLimitError, APIConnectionError, APITimeoutError,
     InternalServerError) — NOT on AuthenticationError/model-not-found (fail fast, those
     need a human).
   - A post-commit health-gate step in news-pipeline.yml inspects the run's own
     classified/rejected counts (already logged: "Classification summary: classified=%d,
     rejected=%d") and opens/reuses a pipeline-failure-news issue if classified==0 while
     candidates>0 for N consecutive runs — orthogonal to the existing if:failure() step,
     which only fires on a non-zero process exit that this pipeline is designed never to
     produce (WR-03).
```

### Recommended Project Structure (no new files needed beyond what's implied)
```
pipeline/
├── news/
│   ├── classifier.py       # MODIFY: config-driven model, typed outcomes, retry, reasoning-off
│   ├── clustering.py       # MODIFY (constant only, F-scope: not activating clustering)
├── experiments/
│   └── ab_score.py         # EXTEND: --model override for openrouter provider
├── backfill_classifier_none.py   # NEW (name TBD by planner) — reads rejected/2026-09.json,
│                                   reclassifies classifier_none items, writes into current.json
│                                   via the same store.merge_and_write() path
├── tests/
│   ├── test_classifier.py  # MODIFY: update default-model assertion; ADD granite-0-endpoints fixture test
```

### Pattern: Typed classifier outcome (recommended, not yet in code)
**What:** Replace `classify() -> ClassifierOutput | None` with a 3-state result (e.g. an Enum
or a small dataclass wrapping `ClassifierOutput | None` plus a `reason: Literal["ok",
"transient_error", "rejected"]`) so `scrape_news.py` can decide seen-marking per branch.
**When to use:** Any call site currently treating "API down" and "confidently not a crime" as
the same `None`.
**Why:** This is literally V-02 — the audit's own words: "every API error is swallowed as a
permanent classifier_none rejection and the URL is marked seen before classification." Fixing
this is the only way today's fix doesn't quietly repeat the exact outage shape on the next
delisting.

### Anti-Patterns to Avoid
- **Hard-coding a second model string anywhere** (mirrors the exact defect that caused V-01) —
  every model id must come from one place (env var/config), never duplicated as a literal.
- **Assuming `reasoning` defaults to off** — training-data assumption about DeepSeek/OpenRouter
  "thinking mode". Every one of the 4 candidates lists `reasoning` in `supported_parameters` on
  every endpoint measured today. Do not ship without an explicit `reasoning: {enabled: false}`
  (or provider equivalent) AND a measured check that `reasoning_tokens == 0` and content is
  non-empty at `max_tokens=512`.
- **Retrying `AuthenticationError` or a delisted-model 404** — these need a human/config fix,
  not backoff; retrying them wastes quota and delays the circuit-breaker trip.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Retry/backoff on transient LLM API errors | A custom `for attempt in range(3): try/except/sleep` loop | `tenacity` (already pinned 9.1.4 in requirements.txt) `@retry(retry=retry_if_exception_type(...), wait=wait_exponential(...), stop=stop_after_attempt(...))` | Already a project dependency; hand-rolling duplicates exactly the kind of "second copy of the same logic" pattern the model-string bug already demonstrates is dangerous in this codebase |
| A/B eval harness | A new script from scratch | Extend `pipeline/experiments/ab_score.py` (add `--model` override, keep `--provider openrouter`) | It already imports and calls the **production** `classify()` (not a copy of the prompt), already computes all 5 required metrics, already has the cost-estimate scaffolding — the spike 008 scripts under `.planning/spikes/008-granite-openrouter-classifier/` show the exact pattern (monkeypatch classifier module, production code untouched) to follow for a 4-model loop |
| Backfill reclassification | Refetching RSS/full-text for 2,057 items | `data/incidents/rejected/2026-09.json` — it already holds title/description/url/outlet/date for every lost item (the exact `classify()` inputs) | `record_rejected()` was already storing the raw candidate before classification failed; nothing needs to be refetched |
| Circuit breaker | A hand-rolled failure counter with a sleep | Same tenacity toolkit supports `stop_after_attempt` + can be composed with a small module-level failure-streak counter that flips a boolean after N consecutive `_call_api` failures — keep it simple (no new dependency needed for a breaker at this scale: ~4-8 calls per 6h run window) | Avoid reaching for a new circuit-breaker library (e.g. `pybreaker`) for a pipeline that runs a few times a day — that would be new dependency + slopcheck overhead for no real benefit at this call volume |

**Key insight:** almost everything this phase needs (retry lib, eval harness, backfill source
data, repair-script pattern) already exists in the repo. This is a config/wiring/typed-outcome
phase, not a build-from-scratch phase.

## Common Pitfalls

### Pitfall 1: `reasoning` mode silently consuming `max_tokens=512`
**What goes wrong:** DeepSeek-family "flash" models on OpenRouter can run a reasoning/thinking
pass before emitting the JSON answer. If `max_tokens` caps total tokens including reasoning
tokens, a 512-token budget can be entirely consumed by hidden reasoning, leaving `content` empty
→ `classify()` treats it as parse failure → same silent-rejection failure mode as the current
outage, just for a different reason.
**Why it happens:** The orchestrator's own smoke test today reported `reasoning_tokens > 0`
even with `max_tokens=3`. All 4 candidate models list `reasoning` as a supported parameter on
every endpoint (confirmed above).
**How to avoid:** Pass `extra_body={"reasoning": {"enabled": False}}` (OpenRouter's documented
mechanism for turning off reasoning per-request — **[ASSUMED]**, not confirmed against
OpenRouter's docs in this research session; the planner must verify the exact key name against
OpenRouter's `reasoning` parameter docs before relying on it, or test empirically by checking
`resp.usage` for a `reasoning_tokens` field after a real call). Add a hard assertion/log in the
eval harness that content is non-empty AND (if reasoning fields are exposed) reasoning_tokens is
0 or small, for every candidate, before trusting its accuracy numbers.
**Warning signs:** `parse_failure_rate` anomalously high for a candidate relative to its
advertised quality; empty `content` string despite HTTP 200.

### Pitfall 2: `openai` SDK version drift (repo pin vs. locally installed)
**What goes wrong:** `pipeline/requirements.txt` pins `openai==2.53.0`; the locally installed
package (used for the `inspect.signature` check in this research) is `2.34.0`. Behavior
(exception hierarchy, `max_retries` default, `extra_body` handling) could differ between the two.
**Why it happens:** Local dev env not reinstalled against the latest requirements.txt.
**How to avoid:** `pip install -r pipeline/requirements.txt` before running the eval harness
locally so measured behavior matches what CI/cron actually runs. Do not trust local
`inspect.signature` output as authoritative for the pinned version without reinstalling.
**Warning signs:** eval harness passing locally but CI showing different retry/error behavior.

### Pitfall 3: Rejected-file month rollover (2026-10-01) during backfill
**What goes wrong:** `record_rejected()` computes `month_key = now.strftime("%Y-%m")` at
call-time (scrape_news.py / store logic, confirmed in `record_rejected`, lines 76-81 of
scrape_news.py). If the backfill tool runs on/after 2026-10-01, any **new** rejections it
generates (e.g., re-classification failures) will be written to `rejected/2026-10.json`, not
`2026-09.json` — but the **source** data being backfilled (the outage-era items) will still be
read from `2026-09.json`. A backfill script written to only look at `2026-09.json` will miss
outage items that happen to be re-recorded as still-rejected after 2026-10-01 unless it also
checks `2026-10.json`.
**Why it happens:** Pure calendar-month partitioning; the deadline (2026-10-05) straddles the
boundary.
**How to avoid:** The backfill tool should scan `rejected/2026-09.json` AND (if present)
`rejected/2026-10.json` for `rejection_stage == "classifier_none"` items with
`first_seen >= 2026-09-04T20:13:49Z`, deduping by `id`/`url`.
**Warning signs:** backfill "accepted/rejected split" total is smaller than the pre-backfill
dry-run count taken on a different calendar day.

### Pitfall 4: 30-day window aging out backfilled items before the fix ships
**What goes wrong:** `current.json`'s window (30 days, `store.merge_and_write`, line 122
`window_days: int = 30`) is computed from `today` at write-time. Today (2026-09-22) the cutoff
is 2026-08-23. If the backfill actually runs later — e.g. 2026-10-03 — the cutoff moves to
2026-09-03, meaning backfilled items dated 2026-09-05 through 2026-09-02 would already be
**aged out on arrival** (written straight to `archive/2026-09.json` instead of `current.json`).
**Why it happens:** `merge_and_write` partitions by `inc_date >= cutoff` at write time,
regardless of when the record was created.
**How to avoid:** Backfill as early as possible in the phase order (directive already places it
5th of 6 steps, but "5th" should still mean days not weeks); if it slips past ~2026-10-01,
explicitly flag in the phase-close report which backfilled items landed in `archive/` instead of
`current.json` and whether that's acceptable (it changes what's visible on `/news/` even though
the data isn't lost).
**Warning signs:** backfill's "accepted" count is high but `current.json`'s incident count
barely moves.

### Pitfall 5: Race between the 6-hourly cron and a local backfill run
**What goes wrong:** `news-pipeline.yml`'s `concurrency: group: news-pipeline,
cancel-in-progress: false` only serializes **Actions-triggered** runs against each other — a
local `git push` from the backfill tool is NOT part of that concurrency group and can race the
cron's own `git commit`/`push-with-rebase.sh` step.
**Why it happens:** the concurrency group is scoped to GitHub Actions workflow runs, not to the
git remote itself.
**Measured cadence:** last 10 `news-pipeline.yml` runs (today back to 2026-09-20), all
`success`, gaps of 4h38m, 5h18m, 7h48m, 5h26m, 3h55m(ish), etc. — roughly every 4-8 hours, not a
precise 6h (GitHub's documented cron jitter, matches `.github/workflows/news-pipeline.yml`
comments referencing 15-30 min delay as "normal").
**How to avoid:** the directive already mandates `git pull --rebase` before push and says "the
news cron commits to data/incidents/ ~4x/day, so expect rebases" — follow that literally for the
backfill's own push, and prefer running the backfill mid-gap (checked via `gh run list
--workflow=news-pipeline.yml --limit 1`) rather than immediately after a cron run when a new one
could start soon.
**Warning signs:** a rebase conflict on `data/incidents/current.json` or
`rejected/2026-09.json` during the backfill's push step.

## Code Examples

### Extending ab_score.py for OpenRouter model override (pattern to follow)
```python
# Source: pipeline/experiments/ab_score.py:96-101 (existing _check_key pattern) — extend, don't replace
def _check_key(provider: str) -> bool:
    key_name = {"deepseek": "DEEPSEEK_API_KEY", "minimax": "MINIMAX_API_KEY"}.get(
        provider, "OPENROUTER_API_KEY"
    )
    return bool(os.environ.get(key_name, "").strip())

# New: before importing pipeline.news.classifier, set both NEWS_PROVIDER and an
# override env var the classifier module must be taught to read (e.g. NEWS_MODEL),
# mirroring how NEWS_PROVIDER is already read at classifier.py:58.
os.environ["NEWS_PROVIDER"] = "openrouter"
os.environ["NEWS_MODEL"] = args.model  # e.g. "deepseek/deepseek-v4.1-flash"
```

### Existing retry pattern already used elsewhere in the repo (tenacity is idiomatic here)
```python
# Source: pipeline/requirements.txt already pins tenacity==9.1.4 — grep shows it is not
# yet imported in pipeline/news/classifier.py (opportunity, not existing code):
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APIConnectionError, APITimeoutError, InternalServerError

@retry(
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_api_with_retry(...):
    ...
```

### Existing "reads current.json.generated" pattern (both instruments — do not fork them)
```python
# Source: .github/workflows/heartbeat.yml:73
LAST_NEWS=$(python3 -c "import json; print(json.load(open('data/incidents/current.json', encoding='utf-8'))['generated'])")
bash .github/scripts/check-heartbeat.sh news 3 "$LAST_NEWS"
```
```js
// Source: site/scripts/validate/freshness.mjs:25-27, MAX_AGE_DAYS=3 (line 27)
const CURRENT_JSON_PATH = path.join(REPO_ROOT, 'data', 'incidents', 'current.json');
const MAX_AGE_DAYS = 3;
```
**Implication:** the new health-gate step must be a THIRD, independent signal (classification
success rate), not a modification of these two — they correctly detect "the file stopped being
written" but are blind, by design/measurement, to "the file is being written with 0 new
classifications every time," which is exactly this outage's shape.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Single hard-coded OpenRouter model (`ibm-granite/granite-4.1-8b`) | Config-driven model id (env-var override) | This phase | Removes the single point of failure that caused V-01 |
| `None` as the only classify() failure signal | Typed outcome distinguishing transient-error vs genuinely-rejected | This phase | Closes V-02 (seen-before-classify swallowing outage-era items permanently) |
| Exit-code-only + `current.json.generated`-only alerting | + post-commit classification-count health gate | This phase | Closes V-03 (20/20 green heartbeats through a total classifier outage) |

**Deprecated/outdated:** `ibm-granite/granite-4.1-8b` on OpenRouter — 0 endpoints, confirmed
dead again today (was delisted 2026-09-04, still delisted 2026-09-22 — not a transient gap).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OpenRouter's mechanism to disable reasoning is `extra_body={"reasoning": {"enabled": False}}` | Common Pitfalls #1 | If the key/shape is wrong, reasoning stays on and `max_tokens=512` could still be silently consumed by hidden reasoning tokens, reproducing a parse-failure-shaped outage under the new model too |
| A2 | The exact backfill accepted/rejected split and final cost will differ from the ~USD 0.3-1.4 directive estimate, since that estimate predates today's measured 2,057-item count (vs. the audit's 2,073 figure from 09-22 morning, itself already grown) | Backfill population §, Standard Stack | If the real backfill call volume is meaningfully larger by the time it runs (item count grows ~80-145/day), the USD 5/phase soft cap could bind — plan should re-measure the exact backlog count immediately before running the backfill, not trust this session's number |
| A3 | `deepseek/deepseek-v4.1-flash`'s official `DeepSeek`-branded OpenRouter endpoint has time-of-day/weekday pricing overrides (seen in the raw endpoint JSON) that could make its effective price higher during Chile business hours (UTC 00-10 roughly aligns with Chile daytime) | Standard Stack / Alternatives table | If the A/B's cost estimate uses only the base rate, actual backfill/production cost on this specific endpoint could be ~2x higher during certain UTC windows |

## Open Questions

1. **Does OpenRouter's `reasoning: {enabled: false}` actually suppress reasoning tokens for
   these 4 specific models, or does DeepSeek v4-family require a different flag
   (`reasoning_effort: "none"` — also present in `supported_parameters`)?**
   - What we know: both `reasoning` and `reasoning_effort` appear in `supported_parameters` for
     every endpoint of all 4 candidates.
   - What's unclear: which one (or combination) actually zeroes reasoning_tokens for each
     specific model/provider pairing — this can vary per underlying provider even for the same
     model id, since OpenRouter is a router over heterogeneous backends.
   - Recommendation: the eval runner (wave 1) must empirically test both and log
     `resp.usage` reasoning-token fields per candidate before the A/B numbers are trusted.

2. **What exactly triggers a "health gate" failure — count-based or ratio-based?**
   - What we know: `scrape_news.py` already logs `Classification summary: classified=%d,
     rejected=%d` (line 359-362) every run.
   - What's unclear: the directive doesn't pre-declare a numeric threshold (e.g. "classified==0
     while candidates>N for M consecutive runs"). This is exactly the kind of gate threshold the
     directive requires be numeric BEFORE execution (roles table, Plan step).
   - Recommendation: planner must pre-declare this threshold explicitly, informed by the measured
     cadence above (~80-145 rejected candidates/day when totally dead vs. some non-zero
     classified/day when healthy — historical healthy-era ratio would need one more measurement:
     inspect `archive/2026-07.json` or `2026-08.json` for typical classified-vs-rejected ratios
     before the outage, if a baseline is wanted).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| OPENROUTER_API_KEY | classifier.py default provider, eval harness | Not verified in this research session (no completion calls made per HARD PROHIBITIONS) — orchestrator confirmed catalog reachable without auth for GET | — | — |
| DEEPSEEK_API_KEY | Backup provider | ✓ (orchestrator: funded, balance USD 23.24, smoke call succeeded today) | — | — |
| gh CLI | Workflow/issue inspection | ✓ (used in this research session) | — | — |
| tenacity | Retry/backoff | ✓ installed, pinned 9.1.4 | 9.1.4 | — |
| openai SDK | LLM client | ✓ installed, but **2.34.0 local vs 2.53.0 pinned** — see Pitfall 2 | 2.34.0 (local) / 2.53.0 (pinned) | reinstall from requirements.txt before trusting local behavior |
| PyYAML | test_workflow_order.py | ✓ installed, pinned 6.0.3 | 6.0.3 | — |

**Missing dependencies with no fallback:** none identified.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.* (pipeline), vitest (frontend, via `npm run test` = `vitest run`) |
| Config file | none dedicated found for pytest (relies on `pytest.ini`/defaults; `pipeline/tests/` convention) |
| Quick run command | `cd pipeline && python -m pytest tests/test_classifier.py -q` |
| Full suite command | `cd pipeline && python -m pytest tests/ -q` (measured baseline below) AND `cd site && npm run build && node scripts/validate/all.mjs && npx vitest run` (chain per OneDrive-desync memory) |

**Measured baseline (2026-09-22, this session, `pytest pipeline/tests/ -q`):**
```
395 passed, 1 skipped, 1 xfailed, 67 warnings in 63.22s
```
This is the exact number the phase-close gate must meet or exceed (per directive: "A phase
closes only at ≥ baseline plus its own new tests").

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NREC-02 | classifier model is config-driven, not hard-coded | unit | `pytest pipeline/tests/test_classifier.py -k default_provider -x` | ✅ exists, needs modification (currently asserts the OLD broken model as correct) |
| NREC-03 | granite-4.1-8b confirmed 0 endpoints (regression fixture) | unit (mocked HTTP or a documented live-check script) | new test, e.g. `pytest pipeline/tests/test_classifier.py -k granite_delisted -x` | ❌ Wave 0 — use the verbatim JSON captured in this doc as the mock fixture |
| NREC-01 | A/B across ≥3 candidates produces comparable metrics | integration (real API calls, run manually/orchestrator, NOT in pytest — costs money) | `python pipeline/experiments/ab_score.py --provider openrouter --model <id>` | ✅ script exists, needs `--model` flag added |
| NREC-09 | backfill dry-run reports counts with zero writes | integration | new script `--dry-run` flag | ❌ Wave 0 |
| (typed outcome) | classify() distinguishes transient vs rejected | unit | extend `pytest pipeline/tests/test_classifier.py -k outcome -x` | ❌ Wave 0 — needs new test cases mocking each exception class |
| (health gate) | workflow step correctly flags 0-classified runs | workflow-level (mirrors `test_workflow_guards.py`/`test_workflow_order.py` pattern: real subprocess against the real script/YAML, not a mock) | `pytest pipeline/tests/test_workflow_guards.py -x` (extend) or new `test_health_gate.py` | ❌ Wave 0, follow `test_workflow_guards.py`'s `_find_bash()` Windows-safe pattern exactly (F-86) |

### Sampling Rate
- **Per task commit:** `cd pipeline && python -m pytest tests/test_classifier.py tests/test_workflow_guards.py -q`
- **Per wave merge:** full suite (`pytest pipeline/tests/ -q` + `cd site && npm run build && node scripts/validate/all.mjs`)
- **Phase gate:** Full suite green (≥395 passed) before `/gsd:verify-work`, PLUS `bash .github/scripts/lint-workflows.sh` (workflow YAML changes are in scope) PLUS a live curl of prod after the deploy per the directive's "Validation... against the served route" rule.

### Wave 0 Gaps
- [ ] `pipeline/tests/test_classifier.py` — update `test_default_provider_is_openrouter` for new default model; add granite-0-endpoints regression fixture test (NREC-03)
- [ ] New test file or extension covering typed-outcome behavior (transient vs rejected) in classify()
- [ ] New test(s) for backfill tool `--dry-run` (zero writes) and real-run (accepted/rejected split correctness)
- [ ] `test_workflow_guards.py`/new file — health-gate step logic, following the existing Windows-safe `_find_bash()` pattern (F-86) exactly, since this dev machine's bare `bash` resolves to the non-functional WSL stub

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | no | Phase touches no user-facing auth |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Pydantic `ClassifierOutput` already validates LLM JSON output (existing); backfill tool must reuse the same `resolve_cut`/`get_centroid`/`build_incident` validated path, never write incidents directly to `current.json` |
| V6 Cryptography | no | No secrets are generated/stored by this phase; existing repo-secret pattern (`OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`) is unchanged |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| LLM prompt injection via scraped RSS title/description | Tampering | Existing `ClassifierOutput` schema + closed-set `resolve_cut()` (deterministic, closed-list commune matching) already prevents hallucinated CUTs from reaching the map — unchanged by this phase, verify the backfill tool goes through the same path, not a shortcut |
| Secret leakage in logs during retry/backoff instrumentation | Information Disclosure | Existing pattern in `scrape_news.py`/`classifier.py` never logs key values, only "check X_API_KEY" messages — new retry logging must follow the same convention |
| GitHub Actions health-gate step with `issues: write` scope creating unbounded issues | Denial of Service (on maintainer attention) | Existing pattern already dedupes via `gh issue list --label ... --state open` before creating a new issue (see news-pipeline.yml:121, heartbeat.yml:100) — new health-gate step must reuse this exact dedup pattern, not create a parallel un-deduped issue stream |

## Sources

### Primary (HIGH confidence — read directly from repo HEAD or live authoritative API)
- `pipeline/news/classifier.py` (full file, 247 lines)
- `pipeline/scrape_news.py` (full file, 395 lines)
- `pipeline/news/store.py`, `pipeline/news/dedup.py` (full files)
- `pipeline/news/clustering.py:60`, `pipeline/tests/test_classifier.py` (full file)
- `.github/workflows/news-pipeline.yml`, `.github/workflows/heartbeat.yml`, `.github/scripts/check-heartbeat.sh`, `.github/scripts/lint-workflows.sh` (full files)
- `site/scripts/validate/freshness.mjs` (full file)
- `pipeline/experiments/ab_score.py` (lines 1-250+, full scoring logic)
- `.planning/spikes/008-granite-openrouter-classifier/README.md`
- `data/incidents/rejected/2026-09.json`, `data/incidents/seen.json`, `data/incidents/current.json` — measured via python3 today
- `GET https://openrouter.ai/api/v1/models/{id}/endpoints` for all 5 model ids — live, no auth, today
- `pipeline/requirements.txt`, local `pip`/`inspect` checks for openai SDK signature
- `gh run list --workflow=news-pipeline.yml --limit 10` — live, today
- `.planning/v2.2-AUTONOMOUS-DIRECTIVE.md`, `.planning/research/v2.2-AUDIT-260922.md` (preview)
- `pipeline/repair_sexual_family.py`, `pipeline/archive_r2.py` (partial reads, function signatures + docstrings)
- `.github/workflows/ci.yml`, `site/package.json` (scripts section)
- Local pytest run: `pytest pipeline/tests/ -q` → baseline captured today

### Secondary (MEDIUM confidence)
- none beyond what's captured above — no WebSearch was used or needed; all findings are direct repo/API measurements

### Tertiary (LOW confidence)
- OpenRouter's exact `reasoning: {enabled: false}` parameter shape for disabling reasoning (A1 in Assumptions Log) — based on training knowledge of OpenRouter's API conventions, NOT verified against OpenRouter's own docs in this session (WebFetch was available but not used, given the HARD PROHIBITIONS focus on zero completion calls; a docs fetch would have been in-budget but was not performed — planner/executor should verify before relying on it)

## Metadata

**Confidence breakdown:**
- Standard stack / endpoint census: HIGH — all measured live today via authoritative GET endpoints, zero LLM calls
- Architecture / code map: HIGH — every claim cites file:line read directly
- Pitfalls: MEDIUM-HIGH — pitfalls 2-5 are fully measured; pitfall 1 (reasoning-token risk) is HIGH-confidence on the *existence* of the risk (supported_parameters confirmed live) but MEDIUM on the *exact fix* (A1 assumption)
- Backfill population count: HIGH — measured directly against `rejected/2026-09.json`/`seen.json` today; will drift upward by the time the plan executes (see A2)

**Research date:** 2026-09-22
**Valid until:** ~2026-09-29 (fast-moving: OpenRouter endpoint counts/pricing shift, and the backfill population count itself grows ~80-145 items/day until the fix ships — re-measure immediately before executing the backfill step)
