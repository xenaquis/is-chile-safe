---
phase: 35-honest-freshness-signals
plan: 02
subsystem: news-pipeline / CI workflows
tags: [FRESH-04, FRESH-01, FRESH-03, store.py, deploy-gate, heartbeat, R-04, R-09]
requires:
  - pipeline/news/store.py merge_and_write (G-05 last_new_incident_at rule)
  - news-pipeline.yml commit step + canonical deploy curl (CRON-03)
  - heartbeat.yml news_hb step (G-05, check-heartbeat.sh news 2)
provides:
  - no-op merge_and_write leaves current.json and archive months byte-identical
  - .github/scripts/news-deploy-needed.sh (deploy=true|false from git diff <from> <to>)
  - news cron deploys only when current.json or archive/ changed (fail-open, post-push)
  - deploy-on-code.yml deploys human data pushes (current.json, archive/**, data/cead/**)
  - heartbeat.yml rebuilds prod once per failing day while news is stale
affects:
  - 35-07 (live no-op proof per G-22(c), deploy count D/C/G/H measurement)
  - any consumer reading current.json `generated` (now = last content change, not last run)
tech-stack:
  added: []
  patterns:
    - "deploy decision after commit+push, fail-open (|| { deploy=true; ::warning:: })"
    - "temp git repo pytest fixtures for workflow shell scripts"
key-files:
  created:
    - .github/scripts/news-deploy-needed.sh
    - pipeline/tests/test_news_deploy_gate.py
  modified:
    - pipeline/news/store.py
    - pipeline/tests/test_store.py
    - .github/workflows/news-pipeline.yml
    - .github/workflows/deploy-on-code.yml
    - .github/workflows/heartbeat.yml
    - DEPLOYMENT.md
decisions:
  - "current.json `generated` now means 'time content last changed'; G-05 liveness stays last_new_incident_at"
  - "Archive month files use the run clock ref_now for `generated` (deterministic, was datetime.now())"
  - "Heartbeat rebuild step appended as the LAST step, after both alert steps, so both issues are filed before the deploy call"
metrics:
  duration: ~35 min
  completed: 2026-09-24
  tasks: 3
  files: 8
---

# Phase 35 Plan 02: No-op runs stay byte-identical and deploy nothing Summary

merge_and_write now skips the write when nothing was added or aged out. The news cron deploys only when `git diff HEAD~1 HEAD` after the push touches `data/incidents/current.json` or `data/incidents/archive/`, and that decision fails open. Human data pushes deploy through deploy-on-code.yml. While news evidence is older than 48h, the daily heartbeat triggers one Cloudflare rebuild so the FRESH-01/03 notices reach prod.

## Tasks

| # | Task | Commit(s) |
|---|------|-----------|
| 1 | store.py no-op guard (byte-identical current.json + archive) — TDD | f46ee6e (RED test), a16daae (GREEN feat) |
| 2 | Deploy only on served incident-set change + deploy-on-code data paths + DEPLOYMENT.md §10 | 676156a |
| 3 | Heartbeat-triggered rebuild while news is stale | 821752d |

Step 0 G-19 precondition: `grep -c '^- \[x\] \*\*Phase 34' .planning/ROADMAP.md` gave `1`, so execution proceeded.

## What changed

- **store.py**: the no-op guard runs after validation. It applies only when previous_payload is non-empty, has only the keys {generated, window_days, incidents, last_new_incident_at}, and its incidents, window_days and last_new_incident_at are deep-equal to the new payload. When all of that holds it logs at INFO and returns without writing. An archive month is skipped when its file exists and the merge adds no id. Archive `generated` now comes from `ref_now`. The docstring records the new meaning of `generated`. The last_new bump/carry lines and the `bump_last_new` parameter are unchanged.
- **news-deploy-needed.sh**: takes exactly 2 arguments and runs `git diff --quiet <from> <to> -- data/incidents/current.json data/incidents/archive/`. Exit 0 prints `deploy=false` and exit 1 prints `deploy=true`. Exit 2 or higher, or a wrong argument count, writes `::error::` to stderr and exits 1.
- **news-pipeline.yml**: the unchanged branch now also writes `deploy=false`. The changed branch keeps commit, push and `changed=true` exactly as before, then runs the decision with the fail-open fallback. The deploy step's `if:` became `steps.commit.outputs.deploy == 'true'`, with a comment. The Guard, Health gate, label and alert steps are byte-unchanged.
- **deploy-on-code.yml**: adds the three data paths with the R-04 comment. Nothing else changed.
- **heartbeat.yml**: a new final step "Rebuild site so stale-news notices render (FRESH-01/03)". It runs on `if: failure() && steps.news_hb.outcome == 'failure'`, with step env `CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}`, and its run body is `require-env.sh CF_HOOK` plus the canonical curl. The news_hb step, the threshold, the permissions and the checkout are untouched.
- **DEPLOYMENT.md §10**: one operational line (FRESH-04 / R-04).

## Verification

- `pytest pipeline/tests/test_store.py pipeline/tests/test_backfill_classifier_outage.py`: 57 passed, exit 0.
- `pytest test_news_deploy_gate.py test_news_health_gate.py test_workflow_guards.py`: 100 passed, exit 0 (after Task 2). After Task 3, `test_news_deploy_gate + test_workflow_guards` gave 78 passed.
- `bash .github/scripts/lint-workflows.sh`: exit 0, "canary fired correctly".
- `bash .github/scripts/check-secret-hygiene.sh`: exit 0, clean.
- Full `python -m pytest pipeline`: **642 passed, 1 skipped, 2 xfailed**, exit 0 (baseline 611/1/2 plus 31 new).
- `git status --porcelain data/`: empty.
- Negative controls, each observed failing and then reverted:
  - removing the guard `return` fails 2 byte-identity tests;
  - adding `seen.json` to the pathspec fails seen-only and the pass-through test;
  - moving the decision line above `git commit` fails the ordering pin;
  - removing `data/cead/**` fails the R-04 pin;
  - changing the heartbeat step `if:` to `failure()` fails the if-literal pin.
- TDD gate: the RED `test(35-02)` commit f46ee6e precedes the GREEN `feat(35-02)` commit a16daae. Tasks 2 and 3 were written test-first and their pins were observed failing before the workflow edits (7 failed pre-edit in Task 2). Those tests were committed together with the implementation, not as separate RED commits.

## Deviations from Plan

- **Heartbeat step placement:** the new step is appended at the very end of heartbeat.yml, after the shared "Alert via GitHub Issue on failure" step as well as after "Alert news heartbeat via GitHub Issue". This satisfies "AFTER Alert news heartbeat", and both alert issues are filed before the deploy call. The pin asserts it is after news_hb and after the news alert.
- **DEPLOYMENT.md wording:** the plan's line is used verbatim, except that the paths are in backticks and deploy-on-code is written `deploy-on-code.yml`. Without the backticks, `**` would render as bold in Markdown.
- **Extra test:** `test_fresh04_unknown_key_forces_write` pins the "no unknown keys" condition (T-35-05). A pass-through fallback test checks that the fail-open wrapper does not emit a warning on success. Both add coverage and neither changes scope.

No files outside files_modified were touched, apart from this SUMMARY.

## Deferred live steps (to 35-07, orchestrator)

- Push these commits, then prove the live no-op and deploy gate per G-22(c): up to 4 induced dispatches, observe a no-op commit of seen/rejected with the deploy step skipped, and run the D ≤ C / G = 0 measurement.
- Observe a heartbeat rebuild (H) only if news goes stale. No dispatch was done here.
- Confirm that deploy-on-code fires on a human data-only push. The first real one will be HYG-06 or a hotfix.

## Known Stubs

None.

## Threat Flags

None. T-35-03/04/05/06/16/17 are mitigated as planned: no `${{` appears in the run bodies (pinned), secret hygiene is clean, the gate is untouched, and the fallback is fail-open.

## Self-Check: PASSED

- FOUND: .github/scripts/news-deploy-needed.sh, pipeline/tests/test_news_deploy_gate.py
- FOUND commits: f46ee6e, a16daae, 676156a, 821752d
