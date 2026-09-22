---
phase: 33-security-posture
plan: 02
subsystem: ci-security
tags: [dependabot, zizmor, sec-03, sec-04, artipacked]
requires: ["33-01"]
provides: ["dependabot.yml", "zizmor CI gate", "persist-credentials triage"]
affects: [".github/workflows/ci.yml", ".github/workflows/deploy-on-code.yml", ".github/workflows/heartbeat.yml", ".github/workflows/r2-archive.yml", ".github/workflows/news-pipeline.yml", ".github/workflows/cead-scraper.yml"]
tech-stack:
  added: ["dependabot (github-actions/pip/npm)", "zizmor==1.10.0 via pipx (CI) / uvx (local)"]
  patterns: ["persist-credentials: false on non-pushing checkouts", "inline zizmor ignore comments for accepted findings"]
key-files:
  created: [".github/dependabot.yml"]
  modified: [".github/workflows/ci.yml", ".github/workflows/deploy-on-code.yml", ".github/workflows/heartbeat.yml", ".github/workflows/r2-archive.yml", ".github/workflows/news-pipeline.yml", ".github/workflows/cead-scraper.yml"]
decisions:
  - "github-actions ecosystem grouped (one PR/cycle); pip and npm ungrouped per F-115"
  - "persist-credentials: false applied to the 6 non-pushing checkouts; news-pipeline.yml and cead-scraper.yml accepted with inline suppression because they push via push-with-rebase.sh (F-105)"
metrics:
  duration: "~35 min"
  completed: "2026-08-05"
---

# Phase 33 Plan 02: Dependabot + zizmor CI gate Summary

Shipped `.github/dependabot.yml` (github-actions grouped, pip and npm ungrouped, all weekly, PR limit 5) and wired `zizmor==1.10.0 --persona=regular` into `ci.yml`'s `lint-workflows` job behind a `command -v pipx` guard, then triaged all 8 baseline `artipacked` findings: `persist-credentials: false` added to the 6 non-pushing checkouts, and the 2 pushing workflows (news-pipeline.yml, cead-scraper.yml) accepted via inline `# zizmor: ignore[artipacked]` comments.

## Tasks Completed

1. **Task 1 — `.github/dependabot.yml`** (commit `b630470`): three ecosystems verbatim per F-115. Verified: `python3 -c "import yaml; ..."` prints `ecosystems OK`.

2. **Task 2 — zizmor wired into `ci.yml`** (commit `2c479cb`): pipx-availability guard step, then `pipx run zizmor==1.10.0 --persona=regular .github/workflows/` with `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`. Verified: `grep -c "pipx run zizmor==1.10.0 --persona=regular" .github/workflows/ci.yml` returns 1. Not added to `pipeline/requirements.txt` (SEC-04).

3. **Task 3 — triage all 8 `artipacked` findings** (commit `a4b8f6d`): `persist-credentials: false` added to `ci.yml` (frontend, pipeline, lint-workflows jobs — 3), `deploy-on-code.yml`, `heartbeat.yml` (alongside the existing `fetch-depth: 0`, not replacing it), `r2-archive.yml` — 6 total. Inline `# zizmor: ignore[artipacked]` suppression with the F-105 rationale added to `news-pipeline.yml` and `cead-scraper.yml`.

## Verification Actually Run

1. `uvx zizmor@1.10.0 --persona=regular .github/workflows/` on the finished tree:
   ```
   No findings to report. Good job! (2 ignored, 21 suppressed)
   ```
   Exit code 0.

2. **Falsification (F-110), actually executed:** removed `persist-credentials: false` from `heartbeat.yml`'s checkout step, re-ran zizmor scoped to that file:
   ```
   warning[artipacked]: credential persistence through GitHub Actions artifacts
     --> .github/workflows/heartbeat.yml:48:9
   ...
   6 findings (5 suppressed, 1 fixable): 0 unknown, 0 informational, 0 low, 1 medium, 0 high
   ```
   Exit code **13**. The line names `artipacked` by audit name. Restored the line afterward (confirmed via `git diff` showing a single clean 1-line addition, no other drift).

3. `python3 -c "import yaml; d=yaml.safe_load(open('.github/dependabot.yml')); ..."` — exits 0, prints `ecosystems OK`.

4. `bash .github/scripts/check-sha-pins.sh` → `check-sha-pins.sh: examined 13 uses: lines (>= 13)`, exit 0.
   `bash .github/scripts/lint-workflows.sh` → `canary fired correctly (SC2034 + SC2086 both present), instrument is armed`, exit 0.

5. `git status --porcelain -- data/` — empty output.

6. `grep -rn "^\s*persist-credentials:" .github/workflows/*.yml` — exactly 6 lines, in `ci.yml` (x3), `deploy-on-code.yml`, `heartbeat.yml`, `r2-archive.yml`. Confirmed absent from `news-pipeline.yml` and `cead-scraper.yml` (those two instead carry the inline ignore comment, 1 occurrence each per `grep -c "zizmor: ignore"`).

## Deviations from Plan

None — plan executed exactly as written. The falsification test transiently modified `heartbeat.yml` on disk during Task 3 verification; it was restored byte-for-byte (LF line endings preserved, confirmed via `git diff` showing only the intended 1-line addition) before the Task 3 commit.

## Auth Gates

None encountered.

## FM-10 Note (carried forward, not closed here)

Per the plan, the `workflow_dispatch` proof of `ci.yml` (run URL, `lint-workflows` conclusion, zizmor version banner in the log) is a BLOCKING item for Plan 33-03's phase-close gate, not this plan's responsibility. This plan ships the step correctly and guards a missing `pipx` with a named remedy; it does not perform the dispatch.

## Self-Check: PASSED

- `.github/dependabot.yml` — FOUND
- Commit `b630470` — FOUND (`git log --oneline --all | grep b630470`)
- Commit `2c479cb` — FOUND
- Commit `a4b8f6d` — FOUND
- All 6 `persist-credentials: false` occurrences and both `zizmor: ignore` comments — FOUND via grep above
