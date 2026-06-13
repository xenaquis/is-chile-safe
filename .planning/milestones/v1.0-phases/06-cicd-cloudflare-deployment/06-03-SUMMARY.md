---
phase: 06-cicd-cloudflare-deployment
plan: "03"
subsystem: deployment-runbook
tags: [deployment, cloudflare-pages, runbook, infra]
dependency_graph:
  requires: ["06-01", "06-02"]
  provides: [DEPLOYMENT.md, INFRA-02-human-dashboard-docs, INFRA-03-go-live-gate]
  affects: [site-live, rebuild-loop-guard]
tech_stack:
  added: []
  patterns:
    - "Deploy Hook only — CF auto-build disabled as primary rebuild-loop guard"
    - "workflow_dispatch dry-run (no CF_DEPLOY_HOOK_URL) before real deploy"
key_files:
  created:
    - DEPLOYMENT.md
  modified: []
decisions:
  - "Disabling CF auto-build in dashboard is the primary INFRA-02 guard; [skip ci] in commit messages is secondary belt-and-suspenders only"
  - "Deploy Hook URL stored as CF_DEPLOY_HOOK_URL repo secret; curl guarded by env.CF_HOOK != '' (env-var pattern, not secrets.* in if)"
  - "Task 2 (live cutover) recorded as pending human-UAT gate — no CF access available in this autonomous environment"
metrics:
  duration: "10m"
  completed: "2026-06-13"
  tasks_completed: 1
  tasks_deferred_to_human: 1
  files_created: 1
---

# Phase 6 Plan 3: DEPLOYMENT.md Go-Live Runbook Summary

**One-liner:** Human CF-dashboard runbook: CF Pages project + Deploy Hook + auto-build OFF + ischilesafe.com domain + rebuild-loop verification.

## What Was Built

`DEPLOYMENT.md` at the repo root — a 10-section ordered runbook covering every human step
required to take ischilesafe.com live via Cloudflare Pages.

Sections:
1. Deploy model overview (GH Actions scrapes → CF Pages builds — never the reverse)
2. Create CF Pages project (Workers & Pages → Connect to Git)
3. Build config: `npm run build` / output `dist` / root directory `site`
4. Disable automatic production deployments (PRIMARY rebuild-loop guard, INFRA-02)
5. Create Deploy Hook (branch master, copy URL)
6. Add repo secrets: `CF_DEPLOY_HOOK_URL` + `DEEPSEEK_API_KEY`
7. Bind custom domain `ischilesafe.com` + HTTPS via Let's Encrypt
8. First deploy: dry-run via `workflow_dispatch` (no secret) then real deploy
9. Rebuild-loop verification: push a docs-only commit, confirm CF build count stays flat
10. Operational notes: cron drift (15–30 min normal), 500 builds/month quota, failure recovery

Quick-reference checklist at the end for the operator.

## Tasks

| # | Name | Status | Commit |
|---|------|--------|--------|
| 1 | Write DEPLOYMENT.md runbook | COMPLETE | 0262c64 |
| 2 | Human go-live gate (INFRA-03 + INFRA-02 dashboard) | PENDING HUMAN | — |

## Deviations from Plan

None — plan executed exactly as written. Task 2 is correctly deferred to human as documented
in the sequential_execution instructions (no CF access available in this environment).

## Human Go-Live Gate (Task 2 — PENDING)

**Status:** Awaiting human execution of DEPLOYMENT.md.

**What to do:** Follow `DEPLOYMENT.md` end to end:

1. Create CF Pages project, connect repo, set build command `npm run build` / output `dist` / root `site`.
2. Disable automatic production deployments (Settings → Builds → Branch control).
3. Create Deploy Hook (branch master), store URL as `CF_DEPLOY_HOOK_URL` repo secret.
4. Add `DEEPSEEK_API_KEY` repo secret (DeepSeek console).
5. Bind `ischilesafe.com` + confirm HTTPS: `curl -I https://ischilesafe.com` → HTTP 200.
6. Run `news-pipeline.yml` via `workflow_dispatch` (dry-run without CF secret first, then real).
7. Push a docs-only commit; confirm CF build count stays flat (rebuild-loop guard).

**Resume signal:** Type "approved" once `ischilesafe.com` is live over HTTPS and CF build count
is flat after a doc commit, or describe what failed.

## Grep Verification (All Pass)

- "deploy hook" in DEPLOYMENT.md: PASS
- "automatic production" / "auto-build": PASS
- "custom domain": PASS
- "ischilesafe.com": PASS
- "DEEPSEEK_API_KEY": PASS
- "CF_DEPLOY_HOOK_URL": PASS
- "Root directory" / "root directory.*site": PASS
- "npm run build": PASS
- "dist": PASS
- "workflow_dispatch": PASS
- "build count" / "build history" / "rebuild": PASS

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced. `DEPLOYMENT.md` uses
placeholders only — no real secret values or real Deploy Hook URLs committed (T-06-10 mitigated).

## Self-Check

- `DEPLOYMENT.md` exists at repo root: CONFIRMED
- Commit `0262c64` exists: CONFIRMED
- All plan grep assertions pass: CONFIRMED (verified above)
