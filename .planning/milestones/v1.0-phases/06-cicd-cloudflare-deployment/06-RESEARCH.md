# Phase 6: CI/CD + Cloudflare Deployment — Research

**Researched:** 2026-06-13
**Domain:** GitHub Actions cron automation + Cloudflare Pages Deploy Hook + deployment runbook
**Confidence:** HIGH (all locked decisions in CONTEXT.md D-01..D-11 are confirmed; mechanics verified against official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01** CF Pages builds from the repo when its Deploy Hook is curled; GH Actions does NOT build the site — it scrapes, commits data, and pings the hook.
- **D-02** Rebuild-loop prevention: CF auto-build-on-push DISABLED (human dashboard step); Deploy Hook curled ONLY when `git diff` shows `data/**` changed.
- **D-03** Cron workflow commits scraped `data/**` with `GITHUB_TOKEN`, commit-only-if-changed.
- **D-04** Secrets: `DEEPSEEK_API_KEY` + `CF_DEPLOY_HOOK_URL` in repo Actions secrets; never hardcoded.
- **D-05** News cadence: every 6h (`cron: '0 */6 * * *'`, 4×/day).
- **D-06** CEAD cadence: quarterly (`cron: '0 3 1 1,4,7,10 *'`, 1st of Jan/Apr/Jul/Oct); existing inter-batch delays preserved.
- **D-07** Runtime: Python 3.12 + Node 20 LTS; `pip install -r pipeline/requirements.txt`; `npm ci`.
- **D-08** Safety: `concurrency` guard per workflow + `timeout-minutes`; `workflow_dispatch` on all crons.
- **D-09** `DEPLOYMENT.md` runbook covers every human CF-dashboard step (create project, connect repo, disable auto-build, build command, deploy hook, secrets, custom domain + HTTPS).
- **D-10** Dry-run / no-deploy path: skip the hook curl when `CF_DEPLOY_HOOK_URL` is unset so `workflow_dispatch` works before the hook exists.
- **D-11** CI guard: `npm run build && node scripts/validate/all.mjs` + `pytest pipeline/tests/ -q` on PRs / dispatch.

### Claude's Discretion

- Exact workflow file names (`news-pipeline.yml`, `cead-scraper.yml`, `ci.yml`) and step ordering.
- The precise `git diff` data-change detection snippet and the conditional hook-curl step.
- Whether CI runs on every push vs PRs only.
- DEPLOYMENT.md structure/depth (as long as every human CF step is covered).

### Deferred Ideas (OUT OF SCOPE)

- Live CF account setup, repo connect, auto-build off, Deploy-Hook creation, secrets, ischilesafe.com DNS/domain — documented in DEPLOYMENT.md as human gate.
- The live DeepSeek run + Phase-5 D-16 50-incident audit.
- Post-launch GSC submission + flipping `ADSENSE_ENABLED=true`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | GH Actions cron: news pipeline 4–6h, CEAD quarterly, courteous rate limiting | Cron syntax confirmed; concurrency + timeout patterns documented; courtesy delays preserved in scraper entrypoints |
| INFRA-02 | No rebuild loop: GITHUB_TOKEN data commits, CF auto-build OFF, Deploy Hook on data change only | CF Deploy Hook mechanism confirmed (POST); branch-control disable path confirmed; data-change-gate pattern documented |
| INFRA-03 | Site live at ischilesafe.com | Human-gate runbook scope confirmed; every CF-dashboard step enumerated in DEPLOYMENT.md section |
</phase_requirements>

---

## Summary

Phase 6 is a workflow-and-docs phase: three YAML files and one Markdown runbook. No new libraries, no schema changes, no new Python modules. The scraper entrypoints (`pipeline/scrape_news.py`, `pipeline/scrape_cead.py`) and the frontend build chain (`npm run build` with its `prebuild` sync-data step) are fully reusable. The only substantive engineering decisions are (1) the exact data-change-gated commit+curl pattern, (2) the dry-run/no-secret fallback, and (3) the `concurrency` + `timeout-minutes` safety envelope. All three are well-established GH Actions patterns.

The Cloudflare side is simple: a Deploy Hook is a unique HTTPS URL you HTTP-POST to from `curl`; CF runs its configured build command against the connected branch. Disabling automatic builds is a single toggle in the CF dashboard under Settings → Builds → Branch control. These mechanics are confirmed against official CF Pages documentation.

The CI workflow (`ci.yml`) re-uses the already-existing `npm run build`, `node scripts/validate/all.mjs` (9 validators), and `pytest pipeline/tests/ -q` suite (17 test files). Workflow linting via `actionlint` is the additional verification surface specific to this phase.

**Primary recommendation:** Three workflows (`news-pipeline.yml`, `cead-scraper.yml`, `ci.yml`) + `DEPLOYMENT.md`. The data-change gate uses `id: commit` step with a shell `changed` output written to `$GITHUB_OUTPUT`; the curl step is gated with `if: steps.commit.outputs.changed == 'true' && secrets.CF_DEPLOY_HOOK_URL != ''`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Scrape RSS + classify | GH Actions runner | — | Stateless cron job; reads DEEPSEEK_API_KEY from env |
| Scrape CEAD | GH Actions runner | — | Stateless quarterly job; writes data/cead/ |
| Commit data to repo | GH Actions runner | — | GITHUB_TOKEN push; no server needed |
| Trigger CF build | GH Actions → CF Pages API | — | HTTP POST to Deploy Hook URL; CF does the build |
| Build site (Astro) | Cloudflare Pages CI | — | `npm run build` including `prebuild` sync-data |
| Serve static assets | Cloudflare CDN | — | dist/ from CF Pages |
| Custom domain + HTTPS | Cloudflare DNS | — | Human dashboard step |
| Workflow validation (lint) | GH Actions (ci.yml) | local dev | actionlint static analysis |
| Frontend regression guard | GH Actions (ci.yml) | — | 9 validators + pytest |

---

## Standard Stack

### Core — no new packages required

All dependencies for this phase already exist in the repo. This phase ships only YAML files and a Markdown doc.

| Asset | Already in Repo | Used by |
|-------|-----------------|---------|
| `pipeline/scrape_news.py` | yes | `news-pipeline.yml` |
| `pipeline/scrape_cead.py` | yes | `cead-scraper.yml` |
| `pipeline/requirements.txt` | yes | both cron workflows |
| `site/package.json` scripts (`build`, `validate`, `check`) | yes | `ci.yml` |
| `pipeline/tests/` (17 test files) | yes | `ci.yml` |

### GitHub Actions — official actions [VERIFIED: official GH marketplace]

| Action | Version to Pin | Purpose |
|--------|---------------|---------|
| `actions/checkout` | `v4` | Checkout with `persist-credentials: true` (default) for GITHUB_TOKEN push |
| `actions/setup-python` | `v5` | Python 3.12 setup (v5.6.0 is latest stable as of June 2026) |
| `actions/setup-node` | `v4` | Node 20 LTS setup (v4 series; v5 exists but v4 is safe and widely used) |

**Note on setup-node:** `actions/setup-node@v5` is the newest major version (Sept 2025+); both v4 and v5 support Node 20 LTS. Pin `v4` for stability; upgrade to `v5` is easy later. [ASSUMED — pinning recommendation based on stability tradeoff; verify at github.com/actions/setup-node/releases]

**Note on Node.js runtime deprecation:** GitHub is forcing Node.js 24 as the Actions runner default starting June 2026; Node.js 20 will be removed from runners September 2026. This affects the *runner's own Node.js*, not the project's Node.js version for building. `actions/setup-node` with `node-version: '20'` sets the project version correctly regardless of runner default. [CITED: github.com/wled/WLED/issues/5422]

### actionlint — workflow linter [CITED: github.com/rhysd/actionlint]

| Tool | Install | CI Use |
|------|---------|--------|
| `actionlint` | Binary download from GitHub releases / `brew install actionlint` / `go install` | `rhysd/actionlint` GitHub Action on `ci.yml` |

**Recommended CI pattern** — use the official GitHub Action (no binary install needed):

```yaml
- name: Lint workflows
  uses: rhysd/actionlint@v1
```

This runs on the runner without a separate install step. [CITED: github.com/marketplace/actions/actionlint]

---

## Package Legitimacy Audit

No new external packages are installed in this phase. All Python deps come from the existing `pipeline/requirements.txt` (already vetted in Phases 1 and 5). All Node deps come from the existing `site/package.json`. The `rhysd/actionlint` action is used via the official GitHub Marketplace action reference, not as an npm/pip package.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
[GitHub push / cron trigger]
        |
        v
[GH Actions: news-pipeline.yml / cead-scraper.yml]
  |-- python pipeline/scrape_news.py (reads DEEPSEEK_API_KEY)
  |-- python pipeline/scrape_cead.py
  |-- git diff --quiet -- data/  ?
  |      YES (changed) ─────────────────────────────┐
  |      NO  (unchanged) → workflow exits 0, no curl |
  |                                                   v
  |-- git add data/ && git commit (GITHUB_TOKEN)      |
  |-- curl -X POST $CF_DEPLOY_HOOK_URL ←─────────────┘
                  |
                  v
        [Cloudflare Pages]
          npm run build
            └── prebuild: sync-data.mjs copies data/ → public/data/
            └── astro build → dist/
          Serve dist/ on CDN at ischilesafe.com

[PR / workflow_dispatch]
        |
        v
[GH Actions: ci.yml]
  |-- npm ci && npm run build && node scripts/validate/all.mjs (9 validators)
  |-- pip install -r pipeline/requirements.txt
  |-- pytest pipeline/tests/ -q (17 test files)
  |-- rhysd/actionlint (lint .github/workflows/)
```

### Recommended Project Structure (new files only)

```
.github/
└── workflows/
    ├── news-pipeline.yml   # cron every 6h + workflow_dispatch
    ├── cead-scraper.yml    # cron quarterly + workflow_dispatch
    └── ci.yml              # PR + dispatch: build + validate + pytest + actionlint
DEPLOYMENT.md               # human CF-dashboard runbook (repo root)
```

### Pattern 1: Data-Change-Gated Commit + Conditional Deploy Hook

**What:** After scraping, only commit if `data/` actually changed; only curl the Deploy Hook in the same run where a commit happened.

**When to use:** Every cron run.

```yaml
# Source: CLAUDE.md cron pattern + official GH Actions $GITHUB_OUTPUT docs
- name: Commit data if changed
  id: commit
  run: |
    git config user.name  "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/
    if git diff --staged --quiet; then
      echo "changed=false" >> "$GITHUB_OUTPUT"
    else
      git commit -m "data: auto-update [skip ci]"
      git push
      echo "changed=true" >> "$GITHUB_OUTPUT"
    fi

- name: Trigger Cloudflare Pages deploy
  if: steps.commit.outputs.changed == 'true' && secrets.CF_DEPLOY_HOOK_URL != ''
  run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

**Key details:**
- `git add data/` stages only the data directory — docs and `.planning/` changes from the same push never trigger a deploy.
- `git diff --staged --quiet` exits 0 if nothing staged; exits 1 if staged changes exist.
- `echo "changed=false/true" >> "$GITHUB_OUTPUT"` writes a step output consumable by downstream `if:` conditions. [ASSUMED — exact `$GITHUB_OUTPUT` syntax; this is the documented current pattern replacing `set-output` which was deprecated]
- `[skip ci]` in the commit message is a CF Pages convention that may suppress CF's own GitHub App trigger even if auto-build is left on — but the primary guard is disabling auto-build in the dashboard (D-02).
- `secrets.CF_DEPLOY_HOOK_URL != ''` is the dry-run gate (D-10): if the secret is absent or empty, the curl is skipped silently.

### Pattern 2: Concurrency + Timeout + workflow_dispatch

```yaml
# Source: [ASSUMED] standard GH Actions concurrency docs
on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

concurrency:
  group: news-pipeline
  cancel-in-progress: false   # do NOT cancel — let the in-flight run finish

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: write          # required for git push with GITHUB_TOKEN
```

**Why `cancel-in-progress: false`:** Cancelling a half-finished scrape would leave partial data in `data/`. Let the current run finish; the next cron run is 6h away.

**timeout-minutes:** 30 for news (DeepSeek latency + RSS fetches); 60 for CEAD (346 communes × families × years).

### Pattern 3: Subdirectory Build (site/ root)

The Astro site lives in `site/` — the CF Pages project must be configured with:

| CF Build Setting | Value |
|-----------------|-------|
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory (advanced) | `site` |

In GH Actions `ci.yml`, the Node build step uses `working-directory: site`:

```yaml
- name: Build site
  working-directory: site
  run: |
    npm ci
    npm run build
    node scripts/validate/all.mjs
```

Python steps run from repo root (no `working-directory`):
```yaml
- name: Install pipeline deps
  run: pip install -r pipeline/requirements.txt

- name: Run pytest
  run: pytest pipeline/tests/ -q
```

`pipeline/pytest.ini` sets `pythonpath = ..` and `testpaths = tests`, so running from repo root with `pytest pipeline/tests/ -q` works correctly. [VERIFIED: read pipeline/pytest.ini]

### Anti-Patterns to Avoid

- **`actions/checkout@v4` without persist-credentials:** Default is `persist-credentials: true` — do not override to false or `git push` will 401.
- **`git add .` instead of `git add data/`:** Risks staging unintended files (`.planning/`, temp files, etc.) and triggering spurious deploys.
- **`set-output` command:** Deprecated since 2022; use `>> "$GITHUB_OUTPUT"` instead or actionlint will flag it.
- **Hardcoding the Deploy Hook URL:** Must be `${{ secrets.CF_DEPLOY_HOOK_URL }}` — never literal in YAML.
- **`client:load` on news workflow secrets:** Already locked in D-04; reinforced here for YAML authoring.
- **Using `deepseek-chat` model ID:** Deprecated 2026-07-24 per CLAUDE.md; `scrape_news.py` already uses `deepseek-v4-flash`.
- **Leaving CF auto-build enabled:** The ENTIRE rebuild-loop prevention (INFRA-02) depends on disabling this in the CF dashboard. The `[skip ci]` commit message convention is a backup, not the primary guard.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Workflow YAML validation | Custom schema checker | `rhysd/actionlint` | Type-checks expressions, validates action inputs, catches `${{ }}` syntax errors, pipes shell scripts to shellcheck automatically |
| Data-change detection | File hash comparison script | `git diff --staged --quiet` | Atomic, reliable, already understood by the git history |
| Retry on transient network failure | Custom sleep loop | `tenacity` (already in requirements.txt) | Already in pipeline; scraper entrypoints inherit it |
| HTTP POST to Deploy Hook | Node.js fetch script | `curl -X POST` in run: | One line; zero dependencies; available on every ubuntu-latest runner |

---

## Common Pitfalls

### Pitfall 1: Rebuild Loop (the central risk for INFRA-02)

**What goes wrong:** GH Actions commits data → CF detects new push → CF builds → GH Actions commits data → infinite loop burning 500 builds/month in hours.

**Why it happens:** CF Pages GitHub integration auto-builds on every push by default.

**How to avoid:** Disable automatic production branch deployments in CF dashboard (Settings → Builds → Branch control → "Enable automatic production branch deployments" OFF). The Deploy Hook remains the only build trigger. The data-change gate adds a second layer: if the scraper produces no new data, no commit happens, so no Hook curl fires.

**Warning signs:** CF build count climbing faster than 4×/day (news) or 1×/quarter (CEAD); builds triggered without a Deploy Hook curl in the logs.

### Pitfall 2: Empty Commits Triggering Unnecessary Builds

**What goes wrong:** Cron runs even when no new news items are found; an unconditional `git commit` creates an empty commit, which fires the Hook.

**How to avoid:** The `git diff --staged --quiet || git commit` pattern — `git add data/` followed by checking `--staged` diff before committing. If nothing staged differs from HEAD, skip commit entirely. [CITED: CLAUDE.md GitHub Actions cron patterns]

### Pitfall 3: GITHUB_TOKEN Push Permission

**What goes wrong:** `git push` fails with "remote: Permission to ... denied to github-actions[bot]".

**Why it happens:** Workflow `permissions` block defaults to `read` for `contents` in some repo configurations.

**How to avoid:** Explicitly set `permissions: contents: write` in the job. `actions/checkout@v4` with default `persist-credentials: true` provides the token; the permission grant makes it writable.

### Pitfall 4: scrape_cead.py Runtime (60min timeout)

**What goes wrong:** CEAD scraper times out at 30 minutes; partial data is never committed.

**Why it happens:** 346 communes × 7 families × ~20 years with inter-batch sleeps can exceed 30min. The scraper writes atomically only on full success (D-14).

**How to avoid:** Set `timeout-minutes: 60` for the CEAD job. The atomic write means a timeout produces no corrupted data — the previous JSON remains intact.

### Pitfall 5: Working-Directory Mismatch in CI

**What goes wrong:** `npm ci` fails because `package.json` is in `site/`, not repo root.

**How to avoid:** `working-directory: site` on all Node steps. Python steps run from repo root (where `pipeline/` lives). Confirm `sync-data.mjs` path resolution uses `__dirname` relative paths (it does — verified in `site/scripts/sync-data.mjs`).

### Pitfall 6: Cron Timing Drift

**What goes wrong:** News pipeline at `0 */6 * * *` is expected at 00:00, 06:00, 12:00, 18:00 UTC — actual trigger can be 15–30 minutes late under GH Actions load.

**Impact:** Not a functional issue — the data window is 30 days and runs 4×/day; 30min drift is irrelevant.

**Document in DEPLOYMENT.md** so the operator does not raise an incident when observing drift.

---

## DEPLOYMENT.md Runbook — Required Sections

Every human CF-dashboard step that this automation cannot perform (D-09) must appear. Required coverage:

| Step | Dashboard Path | Notes |
|------|---------------|-------|
| 1. Create CF Pages project | Workers & Pages → Create → Pages → Connect to Git | Select GitHub, authorize, pick this repo |
| 2. Configure build settings | Build configuration | Command: `npm run build`; Output: `dist`; Root directory: `site` |
| 3. Disable automatic production deployments | Settings → Builds → Branch control | Toggle "Enable automatic production branch deployments" OFF |
| 4. Create Deploy Hook | Settings → Builds → Deploy Hooks → Add | Name e.g. `data-update`; Branch: `master`; Copy the generated URL |
| 5. Add repo secrets | GitHub repo → Settings → Secrets → Actions | `CF_DEPLOY_HOOK_URL` (from step 4); `DEEPSEEK_API_KEY` |
| 6. Bind custom domain | Settings → Custom domains → Add | `ischilesafe.com`; CF auto-provisions HTTPS via Let's Encrypt |
| 7. Trigger first deploy | Run `news-pipeline.yml` via workflow_dispatch (dry-run) then with real data; or curl the hook manually | Confirm build succeeds and ischilesafe.com resolves |
| 8. Verify rebuild-loop guard | Push a doc commit; confirm no CF build fires | CF build history should stay flat |

---

## Code Examples

### news-pipeline.yml skeleton

```yaml
# Source: CLAUDE.md cron patterns, official GH Actions docs
name: News Pipeline

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

concurrency:
  group: news-pipeline
  cancel-in-progress: false

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install pipeline deps
        run: pip install -r pipeline/requirements.txt

      - name: Run news scraper
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: python pipeline/scrape_news.py

      - name: Commit data if changed
        id: commit
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          if git diff --staged --quiet; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            git commit -m "data: auto-update news [skip ci]"
            git push
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Trigger Cloudflare Pages deploy
        if: steps.commit.outputs.changed == 'true' && secrets.CF_DEPLOY_HOOK_URL != ''
        run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

### cead-scraper.yml skeleton

```yaml
name: CEAD Scraper (Quarterly)

on:
  schedule:
    - cron: '0 3 1 1,4,7,10 *'
  workflow_dispatch:

concurrency:
  group: cead-scraper
  cancel-in-progress: false

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 60        # CEAD takes longer than news
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install pipeline deps
        run: pip install -r pipeline/requirements.txt

      - name: Run CEAD scraper
        run: python pipeline/scrape_cead.py

      - name: Commit data if changed
        id: commit
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          if git diff --staged --quiet; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            git commit -m "data: auto-update CEAD [skip ci]"
            git push
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Trigger Cloudflare Pages deploy
        if: steps.commit.outputs.changed == 'true' && secrets.CF_DEPLOY_HOOK_URL != ''
        run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK_URL }}"
```

### ci.yml skeleton

```yaml
name: CI

on:
  pull_request:
  workflow_dispatch:

jobs:
  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install deps
        working-directory: site
        run: npm ci

      - name: Build + validate
        working-directory: site
        run: |
          npm run build
          node scripts/validate/all.mjs

  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install pipeline deps
        run: pip install -r pipeline/requirements.txt

      - name: Run pytest
        run: pytest pipeline/tests/ -q

  lint-workflows:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - uses: actions/checkout@v4
      - uses: rhysd/actionlint@v1
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Python framework | pytest (pinned `pytest==8.*` in requirements.txt) |
| Config file | `pipeline/pytest.ini` (`pythonpath = ..`, `testpaths = tests`) |
| Quick run command | `pytest pipeline/tests/ -q` |
| Full suite command | `pytest pipeline/tests/ -v` |
| Node build check | `npm run build` (working-dir: site) |
| Node validators | `node scripts/validate/all.mjs` (9 validators, working-dir: site) |
| Workflow linter | `rhysd/actionlint@v1` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| INFRA-01 | Cron syntax correct (news + CEAD) | Static lint | `rhysd/actionlint@v1` in ci.yml | actionlint validates cron expressions |
| INFRA-01 | Python 3.12 + deps install | Smoke | `pip install -r pipeline/requirements.txt && python -c "import feedparser, openai, tenacity"` | Part of pipeline job setup |
| INFRA-01 | Concurrency + timeout present | Static lint | actionlint | actionlint validates concurrency groups |
| INFRA-02 | Data-change gate: no commit when data unchanged | Unit/integration | manual `workflow_dispatch` dry-run (no DEEPSEEK key → no new data → commit step outputs `changed=false`) | Automatable via dispatch; observable in step output |
| INFRA-02 | Deploy hook curl only fires when changed==true | Static review | Code review of `if:` condition on curl step | Also verifiable via dispatch dry-run |
| INFRA-02 | CF auto-build disabled | Manual | CF dashboard inspection | Human gate — not automatable here |
| INFRA-02 | No spurious rebuild after doc-only commit | Manual | Push a `.planning/` commit; confirm CF build count stays flat | Human post-deploy verification |
| INFRA-03 | Site reachable at ischilesafe.com | Manual | `curl -I https://ischilesafe.com` | Human go-live gate |
| INFRA-03 | HTTPS valid | Manual | Browser + `curl` TLS check | Human go-live gate |
| (Regression) | 9 validators pass | Automated | `node scripts/validate/all.mjs` in ci.yml | Existing suite — guards build regressions |
| (Regression) | 17 pytest files pass | Automated | `pytest pipeline/tests/ -q` in ci.yml | Existing suite — guards pipeline regressions |

### Automatable vs Human-Gate Summary

| Check | Automatable in CI | Human Gate |
|-------|-------------------|------------|
| Workflow YAML lint (actionlint) | YES — `ci.yml` lint-workflows job | — |
| Frontend build + 9 validators | YES — `ci.yml` frontend job | — |
| Pipeline pytest (17 files) | YES — `ci.yml` pipeline job | — |
| Data-change gate logic (dry-run) | PARTIAL — `workflow_dispatch` + inspect step output | confirm CF_DEPLOY_HOOK_URL unset for dry-run |
| CF auto-build disabled | NO | CF dashboard toggle |
| Custom domain + HTTPS live | NO | CF dashboard + DNS propagation |
| ischilesafe.com reachable | NO (until domain is live) | Post-deploy curl check |
| Rebuild-loop guard (push test) | NO | Operator pushes a doc commit; inspects CF build history |

### Sampling Rate

- **Per PR:** Full `ci.yml` (all 3 jobs: frontend + pipeline + lint-workflows)
- **Per dispatch (workflow_dispatch):** Same as PR
- **Phase gate:** `ci.yml` green + human go-live verification before closing INFRA-03

### Wave 0 Gaps

- [ ] `.github/workflows/news-pipeline.yml` — does not exist (created this phase)
- [ ] `.github/workflows/cead-scraper.yml` — does not exist (created this phase)
- [ ] `.github/workflows/ci.yml` — does not exist (created this phase)
- [ ] `DEPLOYMENT.md` — does not exist (created this phase)

No test infrastructure gaps for the existing suites — `pipeline/tests/` (17 files) and `site/scripts/validate/all.mjs` (9 validators) are already present and functional.

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| `ubuntu-latest` GH Actions runner | all workflows | N/A (cloud) | Free tier includes Python 3.12, Node 20, curl |
| `curl` | Deploy Hook trigger | built-in on ubuntu-latest | No install needed |
| `git` | data commit + push | built-in on ubuntu-latest | `actions/checkout@v4` configures GITHUB_TOKEN credential |
| `pip` / Python 3.12 | scraper jobs | via `actions/setup-python@v5` | |
| `npm` / Node 20 | ci.yml frontend job | via `actions/setup-node@v4` | |
| `DEEPSEEK_API_KEY` | `scrape_news.py` | Repo secret (human sets) | Missing → scraper exits 1 (exit code D-14) |
| `CF_DEPLOY_HOOK_URL` | Deploy Hook curl | Repo secret (human creates after CF setup) | Missing → curl skipped (dry-run safe) |
| Cloudflare Pages account | INFRA-03 | Human must create | Free tier supports this project's scale |

**Missing with fallback:**
- `CF_DEPLOY_HOOK_URL` — absent during development; the `secrets.CF_DEPLOY_HOOK_URL != ''` guard makes workflows safe to `workflow_dispatch` before CF setup exists.

**Missing, potentially blocking:**
- `DEEPSEEK_API_KEY` — scraper will exit 1 without it. For CI dry-run testing of the workflow structure itself (not the scraper logic), this is fine (pytest mocks the API). For a real `workflow_dispatch` news run, the key must be set.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `set-output` (`echo "::set-output name=..."`) | `echo "key=value" >> "$GITHUB_OUTPUT"` | Old form deprecated 2022; actionlint flags it; must use new form |
| `actions/setup-python@v4` | `actions/setup-python@v5` (v5.6.0 Jun 2026) | v5 adds .tool-versions support and free-threaded Python; use v5 |
| `actions/setup-node@v3` | `actions/setup-node@v4` (stable) / `v5` (newest) | Both support Node 20; v4 is safe and widely used |
| CF Pages auto-build on push | Deploy Hook only (auto-build disabled) | Prevents rebuild loop on data commits |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `actions/setup-node@v4` is stable and supports Node 20 (vs upgrading to v5) | Standard Stack | Low — both v4 and v5 support Node 20; upgrade is trivial |
| A2 | `$GITHUB_OUTPUT` syntax is correct for step output (replaced `set-output`) | Code Examples | Medium — if wrong, the `changed` output never propagates and the curl never fires; actionlint would catch the old form |
| A3 | `secrets.CF_DEPLOY_HOOK_URL != ''` is valid in a GH Actions `if:` condition | Code Examples | Medium — the condition syntax for checking secret presence; alternative is `env.CF_DEPLOY_HOOK_URL != ''` with an env: block mapping |
| A4 | `[skip ci]` in commit message suppresses CF Pages GitHub App auto-build trigger | Common Pitfalls | Low — this is a secondary guard; the primary guard (dashboard toggle) makes it moot |

---

## Open Questions

1. **`secrets.*` in `if:` conditions**
   - What we know: GH Actions masks secret values in logs and has restrictions on using them in `if:` expressions.
   - What's unclear: Whether `if: secrets.CF_DEPLOY_HOOK_URL != ''` evaluates correctly or silently evaluates to false when the secret is unset vs empty string.
   - Recommendation: Use an `env:` block to map the secret to an env var, then check the env var: `if: env.CF_HOOK != '' ` where `env: CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}`. This is the safer pattern. The planner should use the env-var pattern.

2. **`[skip ci]` reliability with CF GitHub App**
   - What we know: CF Pages honors `[skip ci]` and `[cf-skip]` in commit messages to suppress builds triggered by its GitHub App.
   - What's unclear: Whether this is documented officially or community-observed behavior.
   - Recommendation: Rely on disabling auto-build in the dashboard (D-02). `[skip ci]` is belt-and-suspenders only; document it but do not depend on it.

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on This Phase |
|-----------|---------------------|
| CF Pages Deploy Hook only — never Git auto-build | Dashboard auto-build disable is a required human step (DEPLOYMENT.md item 3) |
| 500 builds/month free limit | Data-change gate is mandatory; CI workflow should not trigger builds |
| `git diff --staged --quiet \|\| git commit` pattern | Canonical commit pattern for cron workflows |
| `actions/checkout@v4` with persist-credentials | Required for GITHUB_TOKEN push to succeed |
| DEEPSEEK_API_KEY in repo secrets | Never hardcode; `scrape_news.py` reads from env |
| Node 20 LTS | `node-version: '20'` in setup-node |
| Python 3.12 | `python-version: '3.12'` in setup-python |
| `deepseek-v4-flash` model — never `deepseek-chat` | Already in `scrape_news.py`; this phase doesn't change scraper code |
| OneDrive desync (LOCAL dev only) | No impact on CI — runners use clean ubuntu-latest checkouts |

---

## Sources

### Primary (HIGH confidence)
- [Cloudflare Pages Deploy Hooks official docs](https://developers.cloudflare.com/pages/configuration/deploy-hooks/) — POST trigger, dashboard creation steps
- [Cloudflare Pages Branch Build Controls](https://developers.cloudflare.com/pages/configuration/branch-build-controls/) — disabling automatic deployments
- [actionlint GitHub repo](https://github.com/rhysd/actionlint) — install methods, CI action reference
- [actionlint GitHub Marketplace Action](https://github.com/marketplace/actions/actionlint) — `rhysd/actionlint@v1` usage
- `pipeline/pytest.ini` — read directly; confirms pythonpath and testpaths settings
- `site/package.json` — read directly; confirms build/validate/prebuild script names
- `site/scripts/sync-data.mjs` — read directly; confirms path resolution uses `__dirname`
- `pipeline/scrape_news.py` — read directly; confirms DEEPSEEK_API_KEY from env, no git ops
- `pipeline/scrape_cead.py` — read directly; confirms atomic write pattern
- `pipeline/requirements.txt` — read directly; exact pinned versions
- `.planning/phases/06-cicd-cloudflare-deployment/06-CONTEXT.md` — D-01..D-11 locked decisions

### Secondary (MEDIUM confidence)
- [github.com/actions/setup-python releases](https://github.com/actions/setup-python/releases) — v5.6.0 confirmed June 2026
- [github.com/actions/setup-node releases](https://github.com/actions/setup-node/releases) — v4 and v5 both current
- [GH Actions Node.js 24 transition notice](https://github.com/wled/WLED/issues/5422) — runner runtime vs project node-version distinction

### Tertiary (LOW confidence)
- `[skip ci]` suppressing CF Pages GitHub App builds — community-observed, not officially documented in CF Pages docs reviewed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; existing deps verified by reading repo files
- Architecture: HIGH — all locked decisions confirmed; CF mechanism verified against official docs
- Pitfalls: HIGH — rebuild-loop and GITHUB_TOKEN patterns are well-documented; `$GITHUB_OUTPUT` syntax is the documented current form
- Open questions: LOW — `secrets.*` in `if:` conditions needs planner verification (use env-var pattern to be safe)

**Research date:** 2026-06-13
**Valid until:** 2026-09-13 (stable domain; only risk is GH Actions action version bumps)
