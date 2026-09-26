---
phase: 36-classification-fidelity-attribution
plan: 06
subsystem: news-pipeline
tags: [classifier, prompt, FID-01, FID-02, G-28, G-38, G-41, R-07, R-18, R-21, R-22]
requires:
  - phase: 36-02
    provides: "golden_set_v3 gate set, eval_classifier.py --score, shingle_guard.py, 36-EVAL-BASELINE (nc 12/24, boundary 5/8)"
  - phase: 36-04
    provides: "scrape_news no longer reads result.title_es (title_es := title_src)"
provides:
  - "pipeline/news/classifier.py: SYSTEM_PROMPT without title_es; title_en = faithful translation of the HEADLINE; category-level non-crime rules + CEAD family boundaries (blob dcc33ead)"
  - "pipeline/news/schema.py: ClassifierOutput without title_es (stray key ignored)"
  - "36-EVAL-RESULTS.md: Decision PASS (iter2, nc 20/24)"
  - "36-DEPS03-BASELINE.json: v2 44/43/0/3 + served_by + classifier_blob (G-41) for Phase 37 DEPS-03"
affects: [36-08, 36-09, 36-10, 36-11, 37]
tech-stack:
  added: []
  patterns:
    - "prompt rules at category level only, enforced by a 5-word shingle guard (rules text vs v3 items)"
    - "gate declared before the first run; decision = scorer pass ∧ boundary ≥ baseline"
key-files:
  created:
    - .planning/phases/36-classification-fidelity-attribution/36-EVAL-RESULTS.md
    - .planning/phases/36-classification-fidelity-attribution/36-DEPS03-BASELINE.json
    - .planning/phases/36-classification-fidelity-attribution/eval/run-iter1.json
    - .planning/phases/36-classification-fidelity-attribution/eval/run-iter2.json
    - .planning/phases/36-classification-fidelity-attribution/eval/run-backup.json
    - .planning/phases/36-classification-fidelity-attribution/eval/36-EVAL-ITER1.{json,md}
    - .planning/phases/36-classification-fidelity-attribution/eval/36-EVAL-ITER2.{json,md}
    - .planning/phases/36-classification-fidelity-attribution/eval/36-EVAL-BACKUP.{json,md}
    - .planning/phases/36-classification-fidelity-attribution/eval/spend-ledger-36-06.json
  modified:
    - pipeline/news/classifier.py
    - pipeline/news/schema.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_schema_incidents.py
decisions:
  - "FID-02 PASS at iteration 2 of 3: not_crime 20/24 = 0.833 [Wilson 0.641, 0.933]; v2 uncontested 41/41 commune, 41/41 family; boundary 7/8 (baseline 5); parse/empty/length 0; null 3/3."
  - "The iter2 gain came from institutional 12→13, not from the targeted accident (4/6) and death_no_crime (1/3) categories. The margin is one item; out-of-sample evidence comes from 36-08 (FID-03) and 36-10 (G-11)."
  - "Backup DeepSeek direct deepseek-v4-flash on the final prompt: nc 19/24 = 0.79 → deferred-live note 'backup weaker on non-crime' (failover only)."
  - "DEPS-03 baseline = run-iter2 v2 subset; classifier_blob dcc33ead6c517787f9fde2858b06571702421f3c (classifier.py at c3f1be2). If 36-08 forces an extra iteration that passes, re-extract."
metrics:
  duration: "~1 h executor + orchestrator eval runs"
  completed: 2026-09-25
  tasks: 3
  files: 4
---

# Phase 36 Plan 06: Headline fidelity + category-level non-crime rules Summary

The classifier no longer writes its own headline: it only translates the outlet's HEADLINE into `title_en`, and `title_es` is gone from both the prompt and `ClassifierOutput`. Non-crime rules are now written by category and derived from the CEAD taxonomy. With them, non-crime rejection on golden_set_v3 rose from 12/24 to 20/24, and the FID-02 gate passed with no commune/family regression.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Part A: title_en = faithful HEADLINE translation, ClassifierOutput without title_es, shingle guard + guard-scope tests | b1a1730 |
| 2 | Part B: category-level non-crime rules + CEAD family boundaries | 64e0217 |
| 3 | Eval loop (orchestrator): iter1 FAIL 19/24 → iter2 edit (c3f1be2) PASS 20/24; backup run; results + DEPS-03 baseline | c3f1be2, 61f3157 |

## Prompt rule categories (all category-level, no item text)

1. Deaths or injuries where no crime is alleged: natural death, suicide, drowning, a body found with no crime established, third-party involvement ruled out.
2. All accident kinds: workplace/mining, aviation, sport/recreation, domestic, explosive remnants/landmines, traffic.
3. From iter2: a death counts as a crime only when the article names an aggressor, a suspect or a criminal investigation. An accident stays non-crime even when responders or a prosecutor investigate it, unless a person is accused of causing it.
4. Fires, explosions, emergencies and disasters, unless arson or another crime is alleged.
5. Institutional, policy and administrative news: meetings, plans, preventive deployments, enforcement balances, prisoner transfers, protests without incidents.
6. Specific crime cases stay in scope with the underlying crime's family. Family boundaries follow the CEAD catalog, and vida is never a default for a death.

## Deviations from Plan

None in code. Task 3 was run by the orchestrator as planned. The executor wrote the iteration-2 edit and the results write-up.

## Deferred

- Deferred-live note: backup weaker on non-crime (19/24). It matters only during failover.
- In accident (4/6) and death_no_crime (1/3), the targeted categories stayed weak. The out-of-sample audits in 36-08 and 36-10 will show whether this holds on live data.

## Verification

- Full pytest before each code commit, pass by exit code 0: 796 passed, 1 skipped, 2 xfailed. The shingle guard is green.
- Task 3 verify: VERIFY_OK. The in-sample line and the Decision line are present, spend is 0.1497 ≤ 0.25, and the DEPS-03 keys are present.
- Spend: 36-06 USD 0.1497. Phase 36 so far is USD 0.171.

## Self-Check: PASSED

- FOUND: 36-EVAL-RESULTS.md, 36-DEPS03-BASELINE.json, eval/run-iter2.json
- FOUND commits: b1a1730, 64e0217, c3f1be2, 61f3157
