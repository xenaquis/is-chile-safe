---
phase: 36-classification-fidelity-attribution
plan: 10
status: complete
outcome: NO-PUBLICATION (G-14)
---

# 36-10 SUMMARY — Backfill re-run under the shipped classifier

- **Task 1:** 2,122 rows re-classified with blob dcc33ead. 1,210 came from the reused 36-08 cache and 912 were new calls.
  - split: ok 1,051 / not_crime 1,070 / parse 1 / api 0
  - spend: USD 0.1538; failovers 0
- **Task 2 flagged-row review:** 138 hits → 9 exclusions.
- **Task 2 G-11 audit (seed 3610, fresh opus):** 36/50 overall. gnews 13/20, non_chile 6/10, random 17/20; every stratum fails. q1 47/50 (G-18: 40/50). publisher_url_decoded 20/20.
- **Decision (G-14, mechanical):** NO-PUBLICATION. Task 3 was skipped: no apply, no data commit, no push, no R2, no disclosure line. 36-BACKFILL-IDS.txt is not created, so 36-09/36-11 exclude 0 backfill rows.
- **Evidence:** 36-BACKFILL-AUDIT.md.
