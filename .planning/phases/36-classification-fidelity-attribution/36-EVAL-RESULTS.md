# 36-EVAL-RESULTS — FID-02 prompt iterations (plan 36-06 Task 3)

Gate set: `pipeline/tests/fixtures/golden_set_v3.json` (79 items: 44 labelled v2 + 3 null v2 + 24 not_crime + 8 boundary).
Primary model: `deepseek/deepseek-v4.1-flash` via OpenRouter, variant `enabled_false` (G-16). Prompt = `pipeline/news/classifier.py` SYSTEM_PROMPT.
Scorer: `pipeline/experiments/eval_classifier.py --score`. The gate was declared before the first run (plan must_haves, G-32 amended by G-38).

FID-02 is in-sample by construction; out-of-sample evidence = 36-FID03-AUDIT and 36-BACKFILL-AUDIT

## Declared gate

- not_crime_rate ≥ 0.80 (≥ 20/24)
- v2 commune ≥ 39/41 and v2 family ≥ 37/41 on the 41 uncontested ids (G-38). Contested ids gs-030/gs-032/gs-038 are reported, not gated.
- parse_errors = 0, empty_content = 0, finish_length = 0 (G-13)
- v2 null 3/3
- boundary family ≥ the 36-02 baseline count (5/8). The scorer's gate dict has no boundary member, so Decision = scorer pass ∧ boundary ≥ 5 (NB-03).

## Baseline vs iterations

Wilson 95 % intervals are in brackets. They are informational and never gating (premortem R-21).

| run | prompt | not_crime (gate ≥ 20/24) | v2u commune (≥ 39/41) | v2u family (≥ 37/41) | all-44 commune / family | boundary family (≥ 5/8) | parse / empty / length | v2 null | scorer pass | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline (36-02) | pre-36-06 prompt | 12/24 = 0.500 [0.314, 0.686] | 41/41 [0.914, 1.000] | 39/41 [0.839, 0.987] | 44/44 / 42/44 | 5/8 [0.306, 0.863] | 0 / 0 / 0 | 3/3 [0.438, 1.000] | False | FAIL (reference) |
| iter1 | Part A + Part B (`64e0217`) | 19/24 = 0.792 [0.595, 0.908] | 41/41 [0.914, 1.000] | 40/41 [0.874, 0.996] | 43/44 / 42/44 | 7/8 [0.529, 0.978] | 0 / 0 / 0 | 3/3 [0.438, 1.000] | False | FAIL (by 1 item) |
| **iter2** | + death / accident wording (`c3f1be2`) | **20/24 = 0.833 [0.641, 0.933]** | 41/41 [0.914, 1.000] | 41/41 [0.914, 1.000] | 44/44 / 43/44 | 7/8 [0.529, 0.978] | 0 / 0 / 0 | 3/3 [0.438, 1.000] | True | **PASS** |
| iter3 (FID-03-triggered, reverted) | + procedural/statement non-crime, routine death inquiry, CEAD family boundaries (`e5f866e`, reverted in `c0c58b9`) | 18/24 = 0.750 [0.551, 0.880] | 41/41 [0.914, 1.000] | 40/41 [0.874, 0.996] | 43/44 / 42/44 | 7/8 [0.529, 0.978] | 0 / 0 / 0 | 3/3 [0.438, 1.000] | False | FAIL, reverted |
| backup (informational) | iter2 prompt, DeepSeek direct `deepseek-v4-flash`, `thinking_disabled` | 19/24 = 0.792 [0.595, 0.908] | 41/41 [0.914, 1.000] | 40/41 [0.874, 0.996] | 43/44 / 42/44 | 7/8 [0.529, 0.978] | 0 / 0 / 0 | 3/3 [0.438, 1.000] | False (nc only) | not gating |

served_by_counts per run (informational, R-21):

- baseline: Together 30, DeepInfra 25, Novita 16, OpenInference 2, Relace 2, StreamLake 1, Wafer 1, Alibaba 1, Fireworks 1
- iter1: DeepInfra 36, Together 21, Novita 8, InferenceNet 6, Fireworks 2, Relace 2, Wafer 1, Morph 1, OpenInference 1, Sail Research 1
- iter2: DeepInfra 36, Together 29, InferenceNet 6, Krea 2, Phala 1, Wafer 1, Relace 1, StreamLake 1, OpenInference 1, NextBit 1
- iter3: DeepInfra 35, Together 19, Parasail 13, Morph 4, Relace 2, DekaLLM 1, OpenInference 1, NextBit 1, DigitalOcean 1, Fireworks 1, BaseTen 1
- backup: deepseek-flash 79

### Contested v2 ids (G-38, reported per id, never gated)

| id | baseline | iter1 | iter2 | iter3 | backup |
|---|---|---|---|---|---|
| gs-030 | ok, incivilidades, family ✓ | ok, incivilidades, family ✓ | ok, incivilidades, family ✓ | ok, incivilidades, family ✓ | ok, incivilidades, family ✓ |
| gs-032 | ok, propiedad, family ✓ | low_conf (rejected), commune ✗ | ok, incivilidades, family ✗ | low_conf (rejected), commune ✗ | low_conf (rejected), commune ✗ |
| gs-038 | ok, propiedad, family ✓ | ok, propiedad, family ✓ | ok, propiedad, family ✓ | ok, propiedad, family ✓ | ok, propiedad, family ✓ |

The contested items explain the gap between the uncontested and all-44 figures. In iter2, the only all-44 family miss is gs-032.

## Per-category non-crime rejection

Rates are reported only when n ≥ 3 (G-39).

| category | n | baseline | iter1 | iter2 | iter3 | backup |
|---|---|---|---|---|---|---|
| accident | 6 | 0/6 | 4/6 | 4/6 = 0.667 [0.300, 0.903] | 3/6 | 3/6 = 0.500 [0.188, 0.812] |
| death_no_crime | 3 | 0/3 | 1/3 | 1/3 = 0.333 [0.061, 0.792] | 1/3 | 1/3 |
| fire_emergency | 2 | 0/2 | 2/2 | 2/2 (n<3) | 1/2 (n<3) | 2/2 (n<3) |
| institutional_preventive | 13 | 12/13 | 12/13 | 13/13 = 1.000 [0.772, 1.000] | 13/13 | 13/13 |
| suicide | 0 | — | — | — | — | — (G-39 shortfall, no items) |
| **total** | 24 | 12/24 | 19/24 | **20/24** | 18/24 | 19/24 |

## Final confusion matrix (iter2, winning run)

Rows are the ground-truth family. Cells are the predicted family, or the item status for null and not_crime rows (`null_item` = scored through the rejection path; rejections are counted in the table above).

| ground truth | predictions |
|---|---|
| robos_violentos | robos_violentos 11 |
| propiedad | propiedad 6, incivilidades 1, robos_violentos 1 |
| drogas | drogas 8 |
| vif | vif 4 |
| armas | armas 6 |
| vida | vida 10 |
| incivilidades | incivilidades 4 |
| sexuales | sexuales 1 |
| null (v2) | null_item 3 |
| not_crime | null_item 24 (20 rejected in prod, 4 accepted) |

## Honesty note (orchestrator)

- The iteration-2 gain came from institutional_preventive (12 → 13), not from the targeted categories: accident and death_no_crime are unchanged at 4/6 and 1/3.
- The margin is one item: 20/24 passes and 19/24 fails. The Wilson lower bound for not_crime is 0.641.
- Out-of-sample checks are 36-08 (FID-03, fresh 2-week audit) and 36-10 (G-11 audit).

## Iteration 3 (FID-03-triggered, reverted)

- **Trigger:** the 36-08 out-of-sample FID-03 audit FAILED at 37/50 agreement, with vida precision 19/25. Under 36-08 Task 3 step 3, that allows one extra category-level iteration, the last one under the 3-iteration cap.
- **Category edits** (commit `e5f866e`):
  - A routine police or prosecutor inquiry into a death, including a body found, is not by itself a criminal investigation.
  - Court or administrative proceedings not tied to a concrete crime incident are non-crime (prison transfer or prison condition rulings, pension or benefit disputes), as are officials' or politicians' statements, protests or commemorations about past cases, and requests for more police.
  - The "escape of a convicted person" clause was removed from the crime-case rule.
  - Family boundaries: a shooting or attack with a person hit or targeted = vida; armas only when no person is targeted; kidnapping for money or goods = robos_violentos; threats, harassment, damage or theft against a partner or family member, including restraining-order breaches = vif; escape or evasion from custody = incivilidades.
- **Result:** FAIL. not_crime 18/24 = 0.750 [0.551, 0.880]: accident 3/6, death_no_crime 1/3, fire 1/2, institutional 13/13. v2 uncontested was 41/41 commune and 40/41 family, boundary 7/8, parse/empty/length 0, null 3/3.
- **Spend:** USD 0.020575 (eval/spend-ledger-36-06-iter3.json).
- **Action:** reverted with `git revert` (`c0c58b9`); no force or reset was used. classifier.py hash-object = `dcc33ead6c517787f9fde2858b06571702421f3c` again, so 36-DEPS03-BASELINE.json `classifier_blob` still matches and was not re-extracted.

Iteration 3 (FID-03-triggered) failed FID-02 and was reverted; shipped prompt = iteration 2 (blob dcc33ead6c517787f9fde2858b06571702421f3c).

Honesty note: iteration 2's 20/24 passes the gate by one item. Iteration-to-iteration swings of ±2 items on the 24 non-crime items are within provider-routing noise; the Wilson 95 % intervals of 18/24, 19/24 and 20/24 overlap almost entirely. The PASS is a mechanical result against the pre-declared threshold, not evidence that iteration 2 is strictly better than iteration 1 or 3. The FID-03 out-of-sample failure (36-08) stands, independently of this in-sample gate.

## Backup (informational)

DeepSeek direct `deepseek-v4-flash` (`thinking_disabled`), run once on the final iter2 prompt: not_crime 19/24 = 0.79 < 0.80. v2 uncontested is 41/41 and 40/41, and boundary is 7/8.

Deferred-live note: **backup weaker on non-crime**. This matters only during failover to the backup provider.

## Spend

| run | ledger | USD |
|---|---|---|
| baseline (36-02) | eval/spend-ledger.json | 0.021245 |
| iter1 | eval/spend-ledger-36-06.json | 0.025324 |
| iter2 | eval/spend-ledger-36-06.json | 0.013584 |
| backup | eval/spend-ledger-36-06.json | 0.110837 |
| iter3 (reverted) | eval/spend-ledger-36-06-iter3.json | 0.020575 |
| **36-06 total** | both 36-06 ledgers | **0.170319** (cap 0.25) |

Phase-36 spend so far (RUN STATUS) = 0.021245 (36-02) + 0.170319 (36-06) = **USD 0.192** (phase cap USD 5).

## DEPS-03 baseline (G-41)

`36-DEPS03-BASELINE.json` is extracted from `eval/run-iter2.json` (v2 subset: 44 labelled + 3 null). Values: commune 44/44, family 43/44, parse 0, null 3/3. `classifier_blob` = `dcc33ead6c517787f9fde2858b06571702421f3c`, which is classifier.py at `c3f1be2`.

Decision applies to iteration 2 (shipped prompt, blob dcc33ead).

**Decision**: PASS
