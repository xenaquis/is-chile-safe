---
phase: 06-cicd-cloudflare-deployment
plan: "02"
subsystem: ci
tags: [ci, github-actions, actionlint, pytest, astro-build]
dependency_graph:
  requires: [06-01]
  provides: [INFRA-01-regression-guard]
  affects: [.github/workflows/ci.yml, .nvmrc]
tech_stack:
  added: []
  patterns:
    - "3-job parallel CI: frontend build+validate, pipeline pytest, actionlint"
    - "working-directory: site for all Node steps; repo root for Python steps"
    - "No contents:write + no CF hook = CI never deploys (safe for untrusted PRs)"
key_files:
  created:
    - .github/workflows/ci.yml
    - .nvmrc
  modified: []
decisions:
  - "ci.yml triggers pull_request + workflow_dispatch only (no push — push is reserved for data cron commits with [skip ci])"
  - "Three jobs run in parallel (no needs:) — all must pass before PR merge"
  - "actionlint via rhysd/actionlint@v1 marketplace action (no Docker required in CI)"
metrics:
  duration: "8m"
  completed: "2026-06-13"
  tasks: 2
  files: 2
---

# Phase 06 Plan 02: CI Workflow + .nvmrc Summary

**One-liner:** 3-job parallel CI guard (Astro build+9 validators, pytest, actionlint) triggered on PR and workflow_dispatch, with zero deploy/push capability.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Pin Node 20 in .nvmrc | c4a7db0 | .nvmrc |
| 2 | Create ci.yml (frontend, pipeline, lint-workflows) | 14ec4b9 | .github/workflows/ci.yml |

## What Was Built

**.nvmrc** — single line `20` at repo root. Pins Node 20 LTS for local dev (`nvm use`) and documents the version used by `actions/setup-node@v4` in CI.

**.github/workflows/ci.yml** — workflow named "CI" with three parallel jobs:

- **frontend** (ubuntu-latest, timeout 20min): `actions/checkout@v4` → `actions/setup-node@v4` (node `'20'`) → `npm ci` (working-directory: site) → `npm run build && node scripts/validate/all.mjs` (working-directory: site). `npm run build` triggers the `prebuild` hook (`sync-data.mjs`) automatically, so the validator sees a fully-populated dist/.
- **pipeline** (ubuntu-latest, timeout 10min): `actions/checkout@v4` → `actions/setup-python@v5` (python `'3.12'`) → `pip install -r pipeline/requirements.txt` → `pytest pipeline/tests/ -q` (from repo root; pytest.ini sets pythonpath=.. and testpaths=tests).
- **lint-workflows** (ubuntu-latest, timeout 5min): `actions/checkout@v4` → `rhysd/actionlint@v1` (lints all .github/workflows/*.yml including the two plan-06-01 cron workflows).

No `needs:` between jobs — they run concurrently.

## Verification Results

All grep assertions passed locally:
- `rhysd/actionlint@v1` present
- `scripts/validate/all.mjs` referenced
- `pytest pipeline/tests/ -q` present
- `working-directory: site` present
- `node-version: '20'` present
- `python-version: '3.12'` present
- `pull_request` trigger present
- `CF_DEPLOY_HOOK_URL` absent (no-deploy confirmed)
- `contents: write` absent (no-write confirmed)
- `push:` trigger absent

YAML parsed clean with Python `yaml.safe_load`.

**actionlint local run:** Docker unavailable in this environment — actionlint was not run locally. The `lint-workflows` job IS the gate; it will run on the first PR or `workflow_dispatch` and catch any YAML/expression errors. This is the intended fallback noted in the plan's acceptance criteria.

## Deviations from Plan

None — plan executed exactly as written.

## Threat Mitigations Applied

| Threat | Mitigation |
|--------|------------|
| T-06-06 Elevation of Privilege | No `permissions: write` granted; default read-only GITHUB_TOKEN |
| T-06-07 DoS via CF build quota | No Deploy Hook curl, no data commit — CI cannot trigger CF builds |
| T-06-08 Supply chain tampering | All actions pinned: checkout@v4, setup-node@v4, setup-python@v5, rhysd/actionlint@v1 |
| T-06-09 Untrusted PR deps | npm ci uses committed lockfile; pip uses version-pinned requirements.txt |

## Known Stubs

None.

## Self-Check: PASSED

- .github/workflows/ci.yml: FOUND
- .nvmrc: FOUND
- Commit c4a7db0: FOUND (git log confirms)
- Commit 14ec4b9: FOUND (git log confirms)
