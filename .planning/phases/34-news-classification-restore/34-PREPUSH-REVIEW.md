---
phase: 34-news-classification-restore
reviewed: 2026-09-23T00:00:00Z
depth: deep
diff: git diff d7815ed f7b738a -- pipeline site .github DEPLOYMENT.md
files_reviewed: 16
files_reviewed_list:
  - .github/workflows/news-pipeline.yml
  - .github/workflows/heartbeat.yml
  - .github/scripts/check-heartbeat.sh
  - DEPLOYMENT.md
  - pipeline/news/classifier.py
  - pipeline/news/model_config.py
  - pipeline/news/pending.py
  - pipeline/news/store.py
  - pipeline/news/schema.py
  - pipeline/news/clustering.py
  - pipeline/news_health_gate.py
  - pipeline/news_evidence.py
  - pipeline/scrape_news.py
  - site/scripts/validate/freshness.mjs
  - site/scripts/validate/all.mjs
  - pipeline/news/feeds.py (callee: load_seen/save_seen/parse_pub_date, unchanged)
findings:
  critical: 1
  warning: 5
  info: 6
  total: 12
status: issues_found
---

# Phase 34: Pre-push Code Review (34-01..34-03)

**Reviewed:** 2026-09-23
**Depth:** deep (cross-file: workflow -> scrape_news -> router -> classifier -> store/pending -> gate/evidence -> site consumers)
**Status:** issues_found

## Summary

I reviewed this code read-only. I ran no LLM calls, dispatched nothing, pushed nothing and edited only this file.
`pytest pipeline/tests`: 579 passed, 1 skipped, 2 xfailed.

Answers to the five questions:

1. **Does it classify correctly with `deepseek/deepseek-v4.1-flash`?** Mostly yes. The model id, the `{"reasoning":{"enabled":false}}` body and the OpenRouter path with no `response_format` match
   34-AB-RESULTS.json (0 parse errors, 0 API errors, 47/47 COMPLETE). One gap remains. The primary sends no
   `response_format`, and a parse path that crashes on valid non-object JSON can take down the whole run. See CR-01.
2. **Are URLs ever burned into seen.json on API errors?** No. `API_ERROR` goes to `pending.upsert_failure` and never touches `seen`
   (scrape_news.py:502-507). Router-exhausted and budget-exhausted items are queued with `attempted=False` (scrape_news.py:494-498). A URL
   is marked seen only in `_answered` (line 432), for OK, NOT_CRIME or PARSE_ERROR, and in `_expire` (line 320). Both are intended.
3. **Does the gate fail loudly when it should and pass when healthy?** The predicates are sound for healthy traffic. I checked them against 114 real runs from
   2026-08-05 to 09-04 (git history of seen.json and current.json). Every run had attempted >= 10 and accepted >= 4, so (a) and (d) would not
   false-fire. Loud-failure paths work: (c) fires on backup_exhausted, including a missing DEEPSEEK key during failover or force. A missing,
   malformed or wrong-schema summary fails closed.
4. **Do commit and deploy run before the gate?** Yes. Order is scrape -> commit -> guard hook -> deploy (`if: changed`) -> gate. The gate step has no `if:`,
   so it runs when every earlier step succeeded or was skipped. A skipped deploy (`changed=false`) does not block it. When the gate fails, the
   `if: failure()` label and alert steps fire. The gap is that the gate is skipped whenever push or deploy fails (WR-02).
5. **Can it corrupt data or break the build?** No corruption paths are introduced. pending.json uses `atomic_write_json` and has a
   deterministic envelope. current.json only gains an optional `last_new_incident_at` key. No site consumer does strict key
   validation: `news.astro`, `noticias.astro`, `CommuneNewsSection.astro`, `HomeNewsPulse.astro` and `IncidentPinLayer.ts` read `incidents` only. `newsFacets.ts` reads `archive/` only. The Cloudflare
   build (`npm run build`) does not run `freshness.mjs`.

Env vars check: all consumed names match the ones set in the workflow. `NEWS_MODEL`, `NEWS_BACKUP_MODEL` and `NEWS_PROVIDER` come in through `model_config.resolve`, which strips the value and falls back to the default when it is empty (model_config.py:44-46). `NEWS_FORCE_BACKUP` is compared as `.strip().lower() == "true"`, so the empty `inputs.*` on a scheduled run means false. `NEWS_RUN_SUMMARY_PATH` resolves to the same `${{ runner.temp }}/news-run-summary.json` in both steps. `NEWS_RUN_BUDGET_S` is unset, so it defaults to 1200.

## Critical Issues

### CR-01: A non-object JSON reply crashes the whole run and keeps crashing it on later runs (the "poison pill")

**File:** `pipeline/news/classifier.py:254-274` (`_parse_content`), reached unguarded from `classify_outcome` at `classifier.py:522`

**Issue:** When `json.loads(raw_stripped)` succeeds but returns something other than a dict, line 273 (`data.get("family")`) raises
`AttributeError`. This happens for a JSON array such as `[{...}]` (a plausible reply for a roundup headline covering several incidents), for `null`, or for a bare string. I confirmed it locally:
`_parse_content('[{"commune_name":null}]','t')`, `('null')` and `('"x"')` all raise `AttributeError`. Only
`_retrying_create` is wrapped in `try` inside `classify_outcome`, so the exception passes through `ProviderRouter.classify` and
`scrape_news.main`'s loop to the outer `except` (scrape_news.py:587-589), which makes the script exit 1.

What happens in production:
- The scrape step fails, so "Commit data if changed" and the health gate are skipped.
- Every item already classified in that run is lost, along with the LLM spend.
- The offending URL was never marked seen or queued, so the next 6-hourly run fetches it again and crashes again. News ingestion stops completely until the item drops out of the RSS feed, which can take hours to days.

This is the 18-day-outage class in a louder form. It is exposed by the new primary: OpenRouter runs without `response_format`
(classifier.py:311-314), so a top-level array is not ruled out. DeepSeek-direct json_object mode would rule it out. The typed-outcome contract says "every failure is a typed API_ERROR / PARSE_ERROR", and this path breaks that promise. The bug existed before this diff but was masked by Granite.

**Fix:** Make the parse path total, and put a backstop in the router:
```python
# classifier.py _parse_content, right after the json.loads / recovery block
if not isinstance(data, dict):
    logger.warning("Non-object JSON from %s for %r", _PROVIDER, title[:60])
    return "parse_error", None
```
Also consider wrapping `_parse_content(raw, title)` in `classify_outcome` with `except Exception -> PARSE_ERROR`, and add a regression test that feeds `'[{}]'`, `'null'` and `'"x"'`.

## Warnings

### WR-01: Candidates dropped by the cap are neither queued nor marked seen, and pending-first ordering makes that more likely

**File:** `pipeline/scrape_news.py:391-405`

**Issue:** Retry-queue items now go first (`candidates = queued_candidates + fresh`), and anything beyond `NEWS_MAX_CLASSIFY`
(200) is sliced off. The dropped fresh items go neither to `pending` nor to `seen`. The only trace is a log warning. After a multi-run provider outage the queue
fills toward about 200 items, because every run queues all its candidates as `attempted=False` or `attempted=True`. On the recovery run the backlog then uses up the whole
cap, and fresh items are silently skipped. Google News feeds rotate within hours, so those items are gone for good. That is a silent
loss the health gate cannot see, since none of its predicates counts cap drops.

**Fix:** Queue the overflow with `pq.upsert_failure(pending, item, now, None, attempted=False)` for every candidate past the cap. The 14-day age expiry plus (f) then still bounds it. At minimum, add a `capped` count to the summary and warn on it.

### WR-02: The health gate is skipped when push or deploy fails, so the classification-health signal is lost

**File:** `.github/workflows/news-pipeline.yml:582-585`

**Issue:** The gate step has no `if:`, so it inherits `success()`. If `push-with-rebase.sh` fails on a rebase conflict, if the hook guard fails, or if the
Cloudflare curl fails, the gate never runs. The job still fails and alerts, but the issue says "News Pipeline failed" with
no classification verdict. A run that was both unhealthy and hit a CF outage would look like a deploy problem only.

**Fix:** `if: ${{ !cancelled() && steps.scrape.outcome == 'success' }}` on the gate step. The summary file exists whenever scrape succeeded.

### WR-03: Non-crime items are under-represented in the A/B evidence behind predicate (e)

**File:** `pipeline/news_health_gate.py:260-264` together with `pipeline/news/schema.py:112-123`

**Issue:** `ClassifierOutput.family` is a required enum. The prompt tells the model to return `commune_name:null, confidence:0.0` for non-crime,
but nothing says what `family` should be. A reply of `"family": null` or `"none"` becomes PARSE_ERROR. In production about 50-60% of
keyword-passed items are non-crime: Aug 2026 had roughly 2225 candidates and roughly 570-800 accepted. The golden set has only 3 null items out of 47. The winner handled all 3,
but predicate (e) (parse_errors/attempted >= 0.20) would turn the gate red on healthy runs if the model's null-family behaviour differs on
real non-crime traffic.

**Fix:** Add to the prompt: "for non-crime items still emit a valid family (best guess)". Or treat `confidence == 0 and commune_name is None` with
an invalid family as NOT_CRIME before Pydantic runs. After the push, watch the first 2-3 `Run summary:` lines for `parse_errors`.

### WR-04: Deterministic 400s (provider content moderation) turn into periodic expired-item gate failures

**File:** `pipeline/news/classifier.py:376-384`, `pipeline/news/pending.py:170-185`, `pipeline/news_health_gate.py:266-268`

**Issue:** A 400 (for example DeepSeek's "Content Exists Risk" on sexual-crime news, or an OpenRouter endpoint moderation block) is classified as
`API_ERROR`. It is queued, retried on 5 runs, then expires, and (f) `expired > 0` fails the job. The same item also counts toward the
consecutive-error breaker. The failure is loud, which is intended, but a steady trickle of such items produces a recurring red job about 30 hours after each one arrives.
That trains the owner to ignore the alert.

**Fix:** Record the status code in `last_error`, which is already done (`f"{res.error}:{res.status_code}"`). In the gate, or in `_expire`, split
out `expired` items whose `last_error` ends in `:400` as a warning-level `expired_permanent_4xx`. Alternatively, send a 400 with a non-empty
body straight to PARSE_ERROR-like rejection with stage `provider_refused`.

### WR-05: A malformed pending.json halts ingestion on every run until someone fixes it by hand

**File:** `pipeline/news/pending.py:93-103`, called at `scrape_news.py:323`

**Issue:** Raising on a malformed queue is deliberate: it fails loudly, and a partial write cannot happen because of `atomic_write_json`. The cost is that every
run then exits 1 before classifying anything, so the commit is skipped and RSS items age out. Also, `envelope.get` on a top-level list
raises `AttributeError` rather than the documented `ValueError`. The behaviour is the same, but the log message is less clear.

**Fix:** Keep failing loudly, but quarantine the file: rename it to `pending.corrupt-<ts>.json`, which gets committed, and continue with `[]`. Emit a
summary field such as `pending_corrupt: true` that the gate treats as a failure predicate. That way the corpus keeps flowing and the job still goes red.

## Info

### IN-01: `NEWS_CLUSTERING_MODEL` is documented as a repo variable but is not passed in the workflow

**File:** `DEPLOYMENT.md:204-213`, `.github/workflows/news-pipeline.yml:534-541`
Clustering is not on the production path (nothing in `scrape_news` imports `clustering.py`), so nothing breaks. The docs overstate it.

### IN-02: An unknown `NEWS_PROVIDER` value silently falls back to openrouter

**File:** `pipeline/news/classifier.py:815-821`
A typo in the repo variable (for example `deepseek-direct`) quietly runs the default, and nothing in the log flags it as an override that was ignored. Log a warning.

### IN-03: The news heartbeat will open an issue on its first scheduled run after push, unless a news run lands first

**File:** `.github/workflows/heartbeat.yml:70-75`
The current evidence is `2026-09-05T00:00:00Z` (fallback: max date 2026-09-04 + 1d; `last_new_incident_at` is absent). It is red today. That is correct, because
the outage is real, but expect a `pipeline-failure-news-heartbeat` issue at the next 12:00 UTC run if no new incident has been written by then.

### IN-04: The job-timeout margin is fine but not asserted

**File:** `pipeline/news/classifier.py:612-621, 698-707`; `news-pipeline.yml:481`
Worst case is the 1200 s budget (which already includes feed fetching, because the budget clock starts at router construction), plus up to about 192 s for one in-flight classify (a timed-out call
plus the empty-content re-call), plus setup and commit. That totals about 1500 s, under the 1800 s `timeout-minutes`. A job timeout is `cancelled()`, not `failure()`,
so no alert would fire. Keep `NEWS_RUN_BUDGET_S` well below 1500 if it is ever overridden.

### IN-05: record_rejected is still non-atomic (not introduced by this diff)

**File:** `pipeline/scrape_news.py:88-98, 128`
A torn write of `rejected/YYYY-MM.json` is swallowed as "malformed", and the next run overwrites the month file with only its new items. This diff adds
two more stages to that file (`api_error_expired`, `parse_error`). Consider switching to `atomic_write_json`.

### IN-06: pending.json is published publicly

**File:** `site/scripts/sync-data.mjs:44-48`
`sync-data.mjs` copies the whole `data/incidents` directory, so `pending.json` (`last_error` values like `RateLimitError:429`) is publicly served, as `rejected/` already is. It contains no secrets and adds one file to the budget. Noting it for awareness only.

## Verified (no finding)

- `merge_and_write` sets `last_new_incident_at` only when a new id lands in the window and `bump_last_new` is true, and otherwise carries the old value forward verbatim
  (store.py:228-241). scrape_news calls it with the defaults, so it bumps on live runs.
- `news_evidence.py`, `check-heartbeat.sh` and `freshness.mjs` agree on the evidence (last_new, else max(date)+1d). A microsecond `...123456Z` string
  parses in both GNU `date -d` and Node `Date.parse`, which I tested.
- The breaker, re-dispatch and pending interplay is correct: re-dispatched backup answers call `pq.remove`, which undoes the attempt increment. A failed backup keeps the
  single increment. `final[rkey]` is replaced, so `api_errors` reflects final outcomes and a healthy failover passes (b).
- Retries: tenacity makes 3 attempts with waits of 2 s then 4 s, and SDK `max_retries=0`, so there are no 9x retries. 400/401/402/403/404 are not retried.
- Preflight: an inconclusive result (`unknown`, i.e. a transient catalog error or bad JSON) stays on the primary. Only `zero_endpoints`, `model_unknown` and `no_credit`
  fail over, and failover is warning-only in the gate.
- Import-time side effects in classifier.py: it constructs OpenAI clients (no network) and reads `data/cead/meta/index.json`, which exists in checkout.
  model_config.py has no side effects.
- `save_pending` does no write when nothing changed, and its serialization is byte-identical to `atomic_write_json(compact=False)`.

---

_Reviewed: 2026-09-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Orchestrator resolution (2026-09-23)
- CR-01 FIXED: `_parse_content` returns parse_error on non-object JSON (array/null/string/number) + test `test_parse_content_non_object_json_is_parse_error`.
- WR-02 NOT APPLIED: `test_news_health_gate.py::test_health_gate_step_has_no_if_or_continue_on_error` pins the no-`if` design deliberately; a failed push/deploy already fails the job and fires the alert. Accepted.
- WR-01, WR-03: accepted, to watch in the first Run summaries (34-04/34-06).
- Live local smoke before push: 3 real outage items through `build_router_from_env()` → 3/3 OK on deepseek/deepseek-v4.1-flash (served by Relace, Together), reasoning_tokens 0, cost $0.00024–0.00129/item.
- Ship gate: pytest 580 passed / 1 skipped / 2 xfailed (exit 0), data/ clean; build 834 pages; validators 15/16 (freshness FAIL as the named expected failure, max(date)+1d = 2026-09-05T00:00:00Z); vitest 97/97; astro check 0 errors; lint/sha-pins/secret-hygiene exit 0; 0 granite-4.1-8b in pipeline/*.py; winner endpoints at switch time = 25.
