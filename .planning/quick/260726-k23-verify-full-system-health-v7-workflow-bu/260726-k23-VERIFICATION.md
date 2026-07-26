---
quick_id: 260726-k23
status: passed
date: 2026-07-26
---

# System Health Verification — 2026-07-26

Post-deploy verification of the full news→classify→archive stack after the
Granite adoption (dqf), R2 research archive (ep0), Google News decoder +
rejected capture + security hardening (gf7), and the GitHub Actions v7 bump (jya).

## Verdict: PASS — all checks green

### 1. GitHub Actions v7 bump (jya) — live-validated
| Check | Result |
|-------|--------|
| news-pipeline run 30214729523 | ✅ success |
| r2-archive run 30214730767 | ✅ success |
| Node-20 deprecation annotation | ✅ GONE (both runs) — logs show `actions/checkout@v7`, `actions/setup-python@v7` |
| Stale pins in repo (`@v4`/`setup-python@v5`/`@v3`) | ✅ none |
| All 5 workflows parse (`yaml.safe_load`) | ✅ pass |

### 2. News pipeline (Granite / OpenRouter)
- OpenRouter classifier live: `POST https://openrouter.ai/api/v1/chat/completions 200 OK` throughout the run.
- Non-crime/low-confidence correctly rejected (e.g. foreign festival attack → confidence 0.00).
- **Rejected-candidate capture working**: `data/incidents/rejected/2026-07.json` = 16 items (15 `classifier_none`, 1 `resolver_fail`), committed by the pipeline's data step.

### 3. R2 research archive (corpus)
- corpus-state **schema v2**, per-kind totals.
- Full-text backfill advancing: incidents fetched_ok **248** (was 154 pre-run), total_chars **536,676**, pending 1,010.
- **Google News decoder working in production**: gnews ledger rows = 133 fetched (was 0 before the decoder), 4 permanent_failure, 1 failed, 555 pending — the decoder recovers the previously-unfetchable Google News URLs.
- All 6 top-level R2 objects present: corpus-state.json, incidents.csv, incidents.jsonl, manifest.json, rejected.jsonl, url-ledger.jsonl.

### 4. Test suite
- `pytest pipeline/tests/` → **288 passed**, 0 failed. Network + boto3 fully mocked; is_safe_url DNS stubbed (hermetic).

### 5. Secret hygiene
- Full-history (`git log --all -S`) + tracked-tree scan for all 8 secrets (OpenRouter, DeepSeek, MiniMax, 4×R2, FAL): **0 leaks**.
- `.env` git-ignored; no secret values in any tracked file or commit.

## Notes
- The r2-archive run logged "0 rejected candidates" because it was dispatched in
  parallel with news-pipeline and read `data/incidents/rejected/` before the news
  run committed it. Not a defect — the 16 rejected items will be consolidated and
  archived on the next r2-archive run. (Sequential cron scheduling avoids this in
  normal operation: news every 6h, archive daily at 05:30 UTC.)
