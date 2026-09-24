---
phase: 34-news-classification-restore
plan: 06
status: complete
requirements: [NREC-10]
closed: 2026-09-24
---

# 34-06 SUMMARY — Live recovery proof and Phase 34 close

## Task 1: 3 consecutive scheduled runs (PASSED)

| Run | classified | HTTP 404 | failovers | expired | Health gate |
|---|---|---|---|---|---|
| 35850190207 | 4 | 0 | 0 | 0 | success |
| 35885597357 | 25 | 0 | 0 | 0 | success |
| 35919642993 | 14 | 0 | 0 | 0 | success |

## Task 2: served-route verification

1. **Freshness (2026-09-23 ~21:30Z):** served 789 incidents, newest date 2026-09-23, last_new_incident_at 2026-09-23T21:02:31Z. No `data(34-05)` commit exists (G-18 no-publication), so the G-07(a) comparison is recorded as "no backfill commit" (C3).
2. **Card coverage:** EN = ES = 789. Days 2026-09-05..09-19 have 0 cards, so there are **15 uncovered days, all withheld** (backfill not published, G-18). The C3 exception applies, and NREC-10 = Partial.
3. **Hotfix survival:** all 8 t59 ids are absent, and the title of 514872e1d06db7f2 is intact. The regex sweep found 123 hits. A fresh Opus reviewer returned 103 OK, 1 V06_KINSHIP and 19 OTHER_DEFECT (`34-06-HITS-VERDICTS.json`). The kinship hit is 63fb0c3ef0adca19 (it says "abuela"; the source says "madre"). That triggered pause point 5 (G-26). The owner delegated the decision, and the card was dropped (G-27, commit f3a84af, deploy 36069817363). Prod /news/ and /es/noticias/ were re-curled and no longer contain the card. The 19 OTHER_DEFECT items are input for Phase 36.
3b. **Heartbeat:** the news heartbeat is green and 0 news-heartbeat issues are open. A CEAD heartbeat red from 2026-10-01 is an expected named signal (HYG-06, Phase 38).
4. **Phase-close gate (re-run 2026-09-24 on HEAD after G-27):**

| Check | Result |
|---|---|
| pytest | 611 passed, 1 skipped, 2 xfailed |
| validators | 16/16 (freshness PASS) |
| vitest | 97/97 |
| astro check | 0 errors |
| lint-workflows | 0 |
| `git status data/` | clean |
| ci.yml | 36070261344 — 3/3 jobs success |

## Requirement statuses (BF-08, conditional)

- NREC-01: Complete (decision.status WINNER = deepseek/deepseek-v4.1-flash, G-16).
- NREC-02..08: Complete (the 34-02/34-03 verifies passed; 34-04 was live-verified, including the 5b forced backup, G-25).
- NREC-09: Partial (0 not_attempted / 2,122 withheld / 2 api_error — the 2 api_error and 5 parse_error rows are inside the 2,122 withheld). Classify ran on all 2,122 rows, but the G-11 audit failed at 38/50, so everything was withheld (G-18). The residual stays `classifier_none` in `data/incidents/rejected/2026-09.json`.
- NREC-10: Partial (15 days uncovered: withheld).

## Spend

USD 0.53 of the USD 10 run cap.
