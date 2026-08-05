---
phase: 32-cron-consistency
plan: 01
subsystem: ci-scripts
tags: [bash, ci, lint, pytest, git-race, heartbeat]
dependency-graph:
  requires: []
  provides:
    - .github/scripts/require-env.sh
    - .github/scripts/check-heartbeat.sh
    - .github/scripts/push-with-rebase.sh
    - .github/scripts/fetch-lint-tools.sh
    - .github/scripts/lint-workflows.sh
    - .github/scripts/fixtures/canary-bad-workflow.yml
  affects:
    - Wave 2 (news-pipeline.yml, cead-scraper.yml, deploy-on-code.yml wiring)
    - Wave 3 (heartbeat.yml, r2-archive.yml wiring)
tech-stack:
  added:
    - actionlint v1.7.7 (SHA-256-pinned, deterministic .tools/)
    - shellcheck v0.11.0 (SHA-256-pinned, deterministic .tools/)
  patterns:
    - "armed-check + canary self-test before trusting a lint gate (F-85)"
    - "explicit git-bash resolution in pytest, never bare 'bash' (F-86)"
    - "real bare-clone git repos in tmp_path for race proofs (F-91)"
key-files:
  created:
    - .github/scripts/require-env.sh
    - .github/scripts/check-heartbeat.sh
    - .github/scripts/push-with-rebase.sh
    - .github/scripts/fetch-lint-tools.sh
    - .github/scripts/lint-workflows.sh
    - .github/scripts/fixtures/canary-bad-workflow.yml
    - pipeline/tests/test_workflow_guards.py
    - pipeline/tests/test_push_race.py
  modified:
    - .gitignore
decisions:
  - "Pinned actionlint v1.7.7 (not v1.7.12) per F-92 -- the version actually tested end to end"
  - "CEAD heartbeat threshold 150 days (not 100) per F-83c -- avoids false alarm on real 103-day gap"
  - "news heartbeat mode added per F-83a -- ci.yml is pull_request-only and cannot watch a quiet repo"
metrics:
  duration: "~35 min"
  completed: "2026-08-04"
---

# Phase 32 Plan 01: Cron-consistency shared-script foundation Summary

Five shellcheck-clean bash scripts (secret-presence guard, three-mode cadence heartbeat, extracted push-retry loop, SHA-256-verified lint-tool fetcher, armed-check-plus-canary lint entry point) plus two pytest files that drive every script directly against real subprocesses and real bare-clone git repos, raising the pipeline suite from 344 to 366 passed with 1 skipped / 1 xfailed unchanged.

## What Was Built

**Task 1** — `require-env.sh` (unchanged from cycle 0), `check-heartbeat.sh` (news/r2/cead modes, CEAD threshold raised to 150d), `push-with-rebase.sh` (new, extracted retry loop). All three created byte-identical to the plan's `<interfaces>` block.

**Task 2** — `fetch-lint-tools.sh` (deterministic `.tools/`, SHA-256-verified download of actionlint v1.7.7 + shellcheck v0.11.0, idempotent), `lint-workflows.sh` (armed `[ -x ]` check + canary self-test requiring the specific SC2034/SC2086 finding codes, not a bare nonzero exit + real lint), `canary-bad-workflow.yml` fixture, `.gitignore` gains `.tools/`.

**Task 3** — `pipeline/tests/test_workflow_guards.py` (20 tests: bash-resolution canary + 7 require-env tests + 2 r2 + 3 cead + 3 news + 4 common heartbeat tests) and `pipeline/tests/test_push_race.py` (2 tests: disjoint-path race survives, same-file race aborts loudly), both shelling out to the real scripts via explicit git-bash resolution and real `tmp_path`-scoped bare-clone git repos.

No workflow YAML was touched, per the plan's scope fence — Wave 2/3 wire these in.

## Verification Performed (measured, not assumed)

1. `require-env.sh CF_HOOK` with `CF_HOOK=""` → exit 1, `::error::CF_HOOK is not set`. With value set → exit 0, `All required secrets present: CF_HOOK`.
2. `check-heartbeat.sh`: news 1d/3d→0, 4d/3d→1, exactly 3d/3d→0; cead 104d/150d→0 (measured real gap), 151d/150d→1, exactly 150d/150d→0. All reproduced exactly as documented.
3. `push-with-rebase.sh` against two real local bare-clone repos, both directions:
   - Disjoint paths (`data/file-a.txt` vs `data/file-b.txt`): plain push rejected, script fetched+rebased+retried, exit 0, `push succeeded`; origin log contains both `from A` and `from B`.
   - Same file (`data/current.json`): rebase hit a real conflict, script printed `::error::rebase conflict during data commit — aborting, a human must resolve`, exit 1; origin log contains ONLY `from A`; `git show master:data/current.json` on origin is byte-for-byte A's content.
4. `fetch-lint-tools.sh`: first run downloads and SHA-256-verifies both binaries, exit 0; second run is idempotent (0.14s, no network); tampered-checksum mutation (`7f12f180...` → `deadbeef...`) refuses install with `::error::SHA-256 mismatch...`, exit 1, `.tools/` left without the tampered binary.
5. `lint-workflows.sh`:
   - No args (five real pre-existing workflow files) → canary fires correctly, exit 0.
   - Canary fixture alone as target → exit 1 (two real SC2034/SC2086 findings reported).
   - Zero-byte `shellcheck.exe` mutation (kept executable) → actionlint's fork/exec error is caught by the specific-finding-code check (neither SC2034 nor SC2086 present in the fork/exec error text), prints the documented `::error::lint canary did not produce its expected findings` message, exit 1 — NOT the bare-nonzero-exit false pass the premortem's first design would have produced.
   - Restored binary → exit 0 again.
6. All five scripts run through `shellcheck` (fetched by `fetch-lint-tools.sh`): zero findings.
7. `pipeline/tests/test_workflow_guards.py -v` → 20 passed, `test_bash_interpreter_is_usable` first.
8. `pipeline/tests/test_push_race.py -v` → 2 passed.
9. `pipeline/tests/ -q` → **366 passed, 1 skipped, 1 xfailed** (measured; matches the plan's prediction of 344 + 20 + 2 exactly).
10. Confirmed the F-86 bash-misresolution defect is real and would be caught: `subprocess.run(["bash", "-c", "echo hello; exit 3"])` on this machine resolves to the WSL launcher stub, returning `rc=1`, `stdout=""`, stderr containing a WSL relay error — which fails the canary test's `rc==3`/`stdout=="hello"` assertions immediately, exactly as F-86 requires.

## Measured pytest total

**366 passed, 1 skipped, 1 xfailed** — matches the plan's predicted number exactly (344 pre-existing + 20 in `test_workflow_guards.py` + 2 in `test_push_race.py`). No adjustment to any expectation was needed; the plan's transcription reproduced every documented exit code and message without deviation.

## Deviations from Plan

None. All five scripts were created byte-identical to the plan's `<interfaces>` block, the `.gitignore` line was appended (not previously present), and both pytest files implement exactly the test names and counts specified in the plan's `<behavior>` blocks. No auto-fixes, no architectural changes, no Rule 1-4 triggers.

## Threat Flags

None — the two new pytest files shell out only to the real scripts and to throwaway `tmp_path`-scoped bare-clone git repos with synthetic values, matching the plan's threat model (T-32-04, disposition: accept). `fetch-lint-tools.sh`'s download surface (T-32-02) is unchanged from the plan's specification.

## Self-Check: PASSED

- FOUND: `.github/scripts/require-env.sh`
- FOUND: `.github/scripts/check-heartbeat.sh`
- FOUND: `.github/scripts/push-with-rebase.sh`
- FOUND: `.github/scripts/fetch-lint-tools.sh`
- FOUND: `.github/scripts/lint-workflows.sh`
- FOUND: `.github/scripts/fixtures/canary-bad-workflow.yml`
- FOUND: `pipeline/tests/test_workflow_guards.py`
- FOUND: `pipeline/tests/test_push_race.py`
- FOUND commit `42674b7`: feat(32-01): create require-env, check-heartbeat, push-with-rebase scripts
- FOUND commit `3dfc51e`: feat(32-01): create F-85 lint infrastructure (fetch-lint-tools, lint-workflows, canary)
- FOUND commit `27fec44`: test(32-01): two-direction pytest proofs for guard scripts (F-81, F-86, F-91)
