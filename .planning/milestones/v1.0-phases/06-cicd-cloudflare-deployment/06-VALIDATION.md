---
phase: 6
slug: cicd-cloudflare-deployment
status: draft
nyquist_compliant: true
nyquist_reconciled: "v1.3 P19 TD-07 — milestone shipped; superseded by v1.2 audit (0 blockers)"
wave_0_complete: false
created: 2026-06-13
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 06-RESEARCH.md "## Validation Architecture".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Workflow linter** | `rhysd/actionlint@v1` (validates cron, expressions, concurrency; flags deprecated set-output) |
| **Frontend guard** | `npm run build && node scripts/validate/all.mjs` (9 validators, working-dir: site) |
| **Pipeline guard** | `pytest pipeline/tests/ -q` (existing suite) |
| **Config file** | pipeline/pytest.ini |
| **Local lint command** | `docker run --rm -v "$PWD:/repo" rhysd/actionlint:latest -color` (or the GH Action in CI) |
| **Estimated runtime** | CI ~2–4 min (3 parallel jobs) |

---

## Sampling Rate

- **Per PR / push:** full `ci.yml` (frontend + pipeline + lint-workflows jobs)
- **Per workflow_dispatch:** same 3 jobs + the cron workflows' dry-run path (no DEEPSEEK key → no new data → `changed=false` → no hook curl)
- **Phase gate:** `ci.yml` green + actionlint clean on all 3 workflow files; human go-live verification for INFRA-03
- **Max feedback latency:** ~4 minutes (CI)

---

## Per-Task Verification Map

| Task ID | Requirement | Behavior | Test Type | Automated Command | Status |
|---------|-------------|----------|-----------|-------------------|--------|
| 6-?-? | INFRA-01 | news + cead cron syntax valid; concurrency + timeout present | static lint | `actionlint` (in ci.yml) | ⬜ |
| 6-?-? | INFRA-01 | py 3.12 + pipeline deps import | smoke | `pip install -r pipeline/requirements.txt && python -c "import feedparser,openai,tenacity,pydantic"` | ⬜ |
| 6-?-? | INFRA-02 | data-change gate: commit step emits changed=true/false; hook curl gated `if changed==true` | review + dispatch | `workflow_dispatch` dry-run; inspect step output | ⬜ |
| 6-?-? | INFRA-02 | dry-run path: hook curl skipped when CF_DEPLOY_HOOK_URL env unset | static + dispatch | actionlint + dispatch (no secret) | ⬜ |
| 6-?-? | INFRA-03 | DEPLOYMENT.md runbook covers all human CF steps | doc review | `grep -i "deploy hook\|auto.build\|custom domain\|DEEPSEEK_API_KEY\|CF_DEPLOY_HOOK_URL" DEPLOYMENT.md` | ⬜ |
| 6-?-? | regression | 9 frontend validators pass in CI | automated | `node scripts/validate/all.mjs` | ⬜ |
| 6-?-? | regression | pipeline pytest passes in CI | automated | `pytest pipeline/tests/ -q` | ⬜ |

*Status: ⬜ pending · ✅ green. Plan/Task IDs finalized by planner.*

---

## Wave 0 Requirements

- [ ] `.github/workflows/news-pipeline.yml`, `cead-scraper.yml`, `ci.yml` (all new)
- [ ] `DEPLOYMENT.md` runbook (new)
- [ ] No test-infra gaps: pipeline/tests/ (17 files) + site validators (9) already exist and are the CI guard.

---

## Manual-Only Verifications (human go-live gate — INFRA-03)

| Behavior | Requirement | Why Manual | Instructions |
|----------|-------------|------------|--------------|
| CF auto-build disabled | INFRA-02 | CF dashboard toggle (no API token) | Settings → Builds → turn off automatic deployments |
| No spurious rebuild after doc-only commit | INFRA-02 | Requires live CF + push | Push a `.planning/` commit; confirm CF build count stays flat |
| Deploy Hook created + secret set | INFRA-02 | CF dashboard | Create hook → store URL as `CF_DEPLOY_HOOK_URL` repo secret |
| `DEEPSEEK_API_KEY` repo secret set | INFRA-01 | GitHub settings | Add secret (also unblocks Phase-5 live run + D-16 audit) |
| Site reachable at ischilesafe.com + valid HTTPS | INFRA-03 | DNS + CF custom domain | Bind domain in CF Pages; `curl -I https://ischilesafe.com` returns 200 |

---

## Validation Sign-Off

- [ ] actionlint clean on all 3 workflow files
- [ ] ci.yml runs (and passes) frontend build+validate + pipeline pytest + workflow lint
- [ ] Data-change gate verified via workflow_dispatch dry-run (changed=false → no curl)
- [ ] DEPLOYMENT.md covers every human CF step
- [ ] Human go-live items tracked in HUMAN-UAT (INFRA-03)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
