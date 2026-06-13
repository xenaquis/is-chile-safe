# Phase 6: CI/CD + Cloudflare Deployment - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss (3 grey areas, all accepted with recommended values)

<domain>
## Phase Boundary

The automation + go-live layer: GitHub Actions cron workflows that run the Phase-5 news pipeline (every ~6h) and the Phase-1 CEAD scraper (quarterly), commit changed data back to the repo, and trigger a Cloudflare Pages deploy ONLY when data actually changed — without burning the 500-builds/month free quota. Plus a deployment runbook (`DEPLOYMENT.md`) documenting the human Cloudflare-dashboard steps that this environment cannot perform (account, repo connect, disable auto-build, create Deploy Hook, custom domain, secrets).

Requirements: INFRA-01, INFRA-02, INFRA-03.

**Out of this phase:**
- The actual Cloudflare account setup, repo connection, auto-build disable, Deploy-Hook creation, secret entry, and `ischilesafe.com` DNS/custom-domain binding — these are HUMAN dashboard actions (no CF API token available here); documented in DEPLOYMENT.md as the go-live gate (INFRA-03).
- The scrapers themselves (Phase 1 CEAD, Phase 5 news) — reused, not rebuilt; this phase only schedules + wires them.

</domain>

<decisions>
## Implementation Decisions

### Deploy Trigger Architecture
- **D-01:** **Cloudflare Pages builds from the repo** when its Deploy Hook is curled (CF runs `npm run build`, which includes the `prebuild` sync-data step). GitHub Actions does NOT build the site — it scrapes, commits data, and pings the hook.
- **D-02:** **Rebuild-loop prevention (INFRA-02):** Cloudflare auto-build-on-push is DISABLED (human dashboard step); the Deploy Hook is curled ONLY when the cron run's `git diff` shows files under `data/**` changed. Normal commits (docs, `.planning/`) never trigger a deploy.
- **D-03:** **The cron workflow commits scraped `data/**` back to the repo using `GITHUB_TOKEN`**, commit-only-if-changed (`git diff --quiet || git commit`) to avoid empty commits / spurious rebuilds.
- **D-04:** **Secrets** = repo Actions secrets `DEEPSEEK_API_KEY` (news classify) + `CF_DEPLOY_HOOK_URL` (deploy trigger). Never hardcoded; referenced via `${{ secrets.* }}`.

### Cron Schedules & Runtime
- **D-05:** **News pipeline cadence** = every 6h (`cron: '0 */6 * * *'`, 4×/day) — inside the 4–6h band (INFRA-01), conservative on DeepSeek cost + GH-Actions minutes.
- **D-06:** **CEAD scraper cadence** = quarterly (`cron: '0 3 1 1,4,7,10 *'`, 1st of Jan/Apr/Jul/Oct) with the existing courtesy inter-batch delays preserved (INFRA-01 rate limiting).
- **D-07:** **Runtime pinning** = Python 3.12 + Node 20 LTS (`.nvmrc`); `pip install -r pipeline/requirements.txt`, `npm ci`.
- **D-08:** **Safety** = a `concurrency` guard per workflow (no overlapping runs) + `timeout-minutes`; `workflow_dispatch` enabled for manual/testing runs.

### Manual-Setup Boundary & Docs
- **D-09:** **Human CF-dashboard steps** (no API access here) are captured in a `DEPLOYMENT.md` runbook: create CF Pages project, connect repo, **disable auto-build**, set build command `npm run build` / output `dist`, create the Deploy Hook (→ `CF_DEPLOY_HOOK_URL` secret), add the two repo secrets, bind `ischilesafe.com` custom domain + HTTPS. This phase ships the workflows + runbook; the live cutover (INFRA-03) is the human gate.
- **D-10:** **Workflow self-test** — each cron workflow supports `workflow_dispatch` and a dry-run/no-deploy path (e.g. skip the hook curl when the secret is unset) so the human can test the Action before the CF hook exists.
- **D-11:** **CI guard** — a CI workflow runs `npm run build && node scripts/validate/all.mjs` (frontend, 9 validators) + `pytest pipeline/tests/ -q` (pipeline) on PRs / dispatch, so regressions are caught before deploy.

### Claude's Discretion
- Exact workflow file names (`news-pipeline.yml`, `cead-scraper.yml`, `ci.yml`) and step ordering.
- The precise `git diff` data-change detection snippet and the conditional hook-curl step.
- Whether CI runs on every push vs PRs only.
- DEPLOYMENT.md structure/depth (as long as every human CF step is covered).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — INFRA-01 (cron cadences + rate limiting), INFRA-02 (no rebuild loop: GITHUB_TOKEN data commits, CF auto-build off, Deploy Hook only on data change), INFRA-03 (live at ischilesafe.com).
- `CLAUDE.md` — GitHub Actions cron patterns (`git diff --staged --quiet || git commit`, `actions/checkout@v4` persist-credentials, `DEEPSEEK_API_KEY` secret), Cloudflare Pages limits (500 builds/month free, 20min timeout, 20k files), Deploy-Hook-only rule (never Git auto-build), Node 20 LTS, Python 3.12.
- `pipeline/scrape_news.py` — the news entrypoint the news workflow runs (reads DEEPSEEK_API_KEY from env; writes data/incidents/; does NO git ops by design — the workflow commits).
- `pipeline/scrape_cead.py` — the CEAD entrypoint the quarterly workflow runs.
- `pipeline/requirements.txt` — pip deps to install in Actions.
- `site/package.json` — `build` (with `prebuild` sync-data) + `validate` scripts; `site/scripts/sync-data.mjs` (copies data→public/data at build).
- `pipeline/pytest.ini`, `pipeline/tests/` — the test suite the CI workflow runs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/scrape_news.py` + `pipeline/scrape_cead.py` — orchestrators the cron workflows invoke.
- `site/package.json` scripts: `build` (prebuild runs sync-data.mjs), `validate` (9 validators), `check`.
- `pipeline/requirements.txt` (incl. feedparser, openai, tenacity, python-dotenv, pydantic, pytest).

### Established Patterns
- Data store is JSON-in-repo; a data commit + CF build is the whole "deploy".
- OneDrive desync is a LOCAL dev concern only — CI runs on clean ubuntu-latest checkouts, so the chain-build-and-validate caveat does not apply in Actions (still chain for safety).
- scrape_news.py / scrape_cead.py do NOT commit — git is the workflow's responsibility (D-03).

### Integration Points
- News workflow → `data/incidents/current.json` + archive; CEAD workflow → `data/cead/**`. Either changing → curl CF Deploy Hook.
- CF build runs `npm run build` → `prebuild` sync-data copies `data/` into `public/data` → `dist/` served on CDN.

</code_context>

<specifics>
## Specific Ideas

- The single hard constraint is INFRA-02: no rebuild loop. CF auto-build OFF + data-change-gated Deploy Hook is the mechanism; verify by checking the CF build count stays flat after a no-data-change cron run.
- Infra budget is ~$0: GH Actions free minutes + CF Pages free tier; only variable cost is DeepSeek (already capped in Phase 5).
- The phase is "done" (code-wise) when the workflows + runbook exist and pass a dispatch dry-run; the true go-live (secrets + CF dashboard + domain) is the human gate (INFRA-03).

</specifics>

<deferred>
## Deferred Ideas

- Live `ischilesafe.com` cutover (CF account, repo connect, auto-build off, Deploy Hook, secrets, custom domain + HTTPS) — human dashboard actions documented in DEPLOYMENT.md; cannot be automated without a CF API token.
- The live DeepSeek run + Phase-5 D-16 50-incident audit — unblocked once `DEEPSEEK_API_KEY` is set as a repo secret here.
- Post-launch GSC submission of editorial pages (Phase-4 deferred item) + flipping `ADSENSE_ENABLED=true` after first indexing wave (Phase-4 / Phase-6 todo).

</deferred>

---

*Phase: 6 - CI/CD + Cloudflare Deployment*
*Context gathered: 2026-06-13 (autonomous smart-discuss)*
