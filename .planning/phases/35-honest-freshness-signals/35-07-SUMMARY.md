---
phase: 35-honest-freshness-signals
plan: 07
status: complete
requirements: [FRESH-01, FRESH-02, FRESH-03, FRESH-04, FRESH-05]
closed: 2026-09-25
---

# 35-07 SUMMARY — Close gate, prod verification, FRESH-04 live measurement

## Pre-push opus review (orchestrator addition)

The verdict was GO with 5 minor findings. F1 (NewsStrip hid the oldest store day) and F2 (a stray space in an aria-label) were fixed in 396eef9. F3, F4 and F5 are in deferred-live and routed to Phase 38 (G-71, G-63).

## Task 1: close gate at one HEAD

The harness printed PASS and the gate took 190 s of wall time.

| Check | Result |
|---|---|
| Validators | 18/18 |
| vitest | 183 before the F1 fix, 184 after |
| astro check | 0 errors |
| pytest | 642 passed / 1 skipped / 2 xfailed |
| lint-workflows | 0 |
| check-secret-hygiene | 0 |

## Task 2: push, deploy, served routes

- **Push:** SHA 396eef9, SHIP 2026-09-25T00:14:08Z. deploy-on-code run 36076592181 succeeded, and prod was live 2 min later.
- **Consistency guard:** the batch fetched into prod35/ matched on the first try (latest incident 2026-09-24 on EN and ES).
- **Validators on the served HTML:**
  - news-freshness: PASS (stale=false; communes EN 2/0, ES 2/0).
  - cead-vintage subset: PASS (2 methodology + 1/1 region + 2/2 commune pages, 0 banned labels).
- **Greps:**
  - Latest incident: 1 on EN and 1 on ES. The Updated/Actualizado stamp: 0.
  - First histogram bar 2026-08-26 ≥ earliest incident date 2026-08-25.
  - The 15 no-data dates in 09-05..09-22 carry `data-gap="true"` (15/15).
  - Antofagasta EN/ES has no Jan–Jun and one as-of line.
  - Methodology shows the as-of line and "(currently 2025)" / "(actualmente 2025)".
  - The Santiago partial-year label is present in EN and ES.
  - Home carries data-coverage-gaps, and .pulse-stale is 0 (verdict fresh).
- **Fresh opus validator:** PASS, with 5 low or informational findings. Those went to deferred-live and Phase 38 (G-71).

## Task 3: FRESH-04 live (instrument W = [SHIP, …), measured 2026-09-25 ~22:55Z)

| Run | Event | Conclusion | Deploy step | Health gate | classified | Store no-op |
|---|---|---|---|---|---|---|
| 36089397586 | schedule | success | success | success | 20 | no |
| 36089456308 | dispatch (attempt 1) | failure | skipped | skipped | 19 | no |
| 36127128480 | schedule | success | success | success | 6 | no |
| 36160556890 | schedule | success | success | success | 14 | no |
| 36189283388 | schedule | success | success | success | 16 | no |
| 36198502749 | dispatch (primer, not counted) | success | success | success | 5 | no |
| 36198632047 | dispatch (attempt 2) | success | **skipped** | success | 0 | **yes** |

- **Interim window counts:** N_sched = 4, D = 4, C = 4, G = 0. Every bot commit changed the incident set, and every scheduled run succeeded.
- **Attempt 1:** failed with a diagnosed reason. It was queued behind the scheduled run and checked out the stale trigger SHA, so the rebase conflicted and it aborted before committing (G-59, issue #44 closed with the diagnosis).
- **Attempt 2 was a live no-op.** It was dispatched right after the primer completed:
  - current.json sha1 33390f0fe883 → 33390f0fe883, and origin/master unchanged (57cd841 → 57cd841, no commit);
  - the log says "write skipped (FRESH-04)" and deploy step = skipped.
  - The no-op path is proven live.
- **Residual:** the deploy-gate branch "run commits only seen/rejected and skips deploy" hasn't been observed live. test_news_deploy_gate covers it, and the 7-day check carries it.
- **Interim verdict:** PASS (D ≤ C, G = 0, N_noop = 1).
- **7-day check:** due 2026-10-02T00:14:08Z, issue #45. It is recorded in RUN STATUS, the STATE deferred-live list and the directive deferred-live list.

## Requirement statuses

FRESH-01, FRESH-02, FRESH-03 and FRESH-05 are Complete. FRESH-04 is at "Interim PASS" with its checkbox still `[ ]` until the 7-day check passes.
