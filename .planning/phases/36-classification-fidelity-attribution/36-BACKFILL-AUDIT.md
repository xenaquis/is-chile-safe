---
phase: 36
plan: 10
artifact: backfill re-run audit (G-11 / G-14, unchanged)
date: 2026-09-26
decision: NO-PUBLICATION (G-14) — 36-10 Task 3 skipped
---

# Phase 36 — Backfill re-run with the shipped classifier (36-10)

## Task 1 — classify

- Pulled onto ship_sha 91b1e80 (ancestor check ok). Backups of current.json and rejected/2026-09.json are in the scratchpad (bf36-backup/, sha256 recorded in the session). archive/2026-09.json did not exist at the time.
- dry-run: selected=2122, would_archive=1, priority days 09-05..09-22 all populated.
- Cache reuse (orchestrator decision): bf36-cache.jsonl was seeded with the 36-08 FID-03 cache. It is the same classifier blob (dcc33ead…) on the same stored inputs, so 1,210 rows were already final and only 912 calls were made. Recorded so the spend and provenance are explicit.
classify_split: ok=1051 not_crime=1070 parse_error=1 api_error=0 (selected 2122; G-18 was 1162 / 953 / 5 / 2)
spend_usd: 0.1538 (4 foreground chunks: 0.075557 + 0.042926 + 0.022610 + 0.012660; ledger overwritten per invocation, see the 36-08 deviation). The 1,210 reused rows were paid in 36-08. failovers 0.

## Task 2 — flagged-row review (fresh opus, as 34-05 step 7)

- review_hits=138. Verdict: KEEP 129, EXCLUDE 9: 4 accidents or unexplained deaths, 4 institutional or non-crime items, and 1 title_en fact change (a02f0cbb473f2ecb: gender added to "bebé").
- 0 kinship errors; 0 absolute safe/dangerous wording.
- Withhold list: scratchpad/bf36-withhold-ids.txt. Moot, because nothing is published.

## Task 2 — G-11 stratified audit (fresh opus, seed 3610)

- Excludes: golden v3 source_ids plus the 36-08 sampled ids (82 ids).
- Google-News rows were given decoded publisher URLs (G-43).
publisher_url_decoded: 20/20

| stratum | agree (q1∧q2∧q3) | n | needs ceil(0.86·n) | result | Wilson 95 % |
|---|---|---|---|---|---|
| gnews_title_only | 13 | 20 | 18 | FAIL | 0.43–0.82 |
| non_chile_cue | 6 | 10 | 9 | FAIL | 0.31–0.83 |
| random | 17 | 20 | 18 | FAIL | 0.64–0.95 |

overall: 36/50 (needs 43; Wilson 0.58–0.83)
agreement_by_basis: source=34/48 headline_only=2/2
q1_only: 47/50 (G-18 audit on the old prompt: 40/50)
q4_true: 0/50

**Decision**: NO-PUBLICATION

Every stratum fails, so every stratum is withheld (G-14 ii) and there is no non-withheld remainder to re-audit. 36-10 Task 3 is skipped: no apply, no data commit, no push, no R2, no disclosure line. The 2,122 rows stay classifier_none in rejected/2026-09.json.

Sensitivity: the auditor's least-certain call was 4 prison-escape items (vida vs incivilidades). Counting the escapes as vida gives 38/50, which still fails.

## What this says

- Non-crime rejection is fixed: q1 rose from 40/50 on the G-18 prompt to 47/50.
- The remaining errors are commune and family precision:
  - evasion or escape tagged vida;
  - shootings at people tagged armas;
  - phone-snatching gangs tagged propiedad instead of robos_violentos;
  - threats to an ex-partner tagged armas instead of vif;
  - the airport placed in Santiago instead of Pudahuel;
  - the commune taken from the court's location.
- These are the same classes FID-03 (G-33) found. Iteration 3 targeted them, failed FID-02 and was reverted. They are the input for the owner question in deferred-live.
