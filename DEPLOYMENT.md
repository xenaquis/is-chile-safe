# DEPLOYMENT.md — Cloudflare Pages Go-Live Runbook

**ischilesafe.com** | Last updated: 2026-08-04

This runbook documents every human Cloudflare-dashboard and GitHub-secrets step required to take
the site live. GitHub Actions automation handles scraping and data commits; Cloudflare Pages
handles building and serving the static site. The two are connected via a Deploy Hook URL.

---

## 1. Deploy Model Overview

```
[GitHub cron trigger or workflow_dispatch]
        |
        v
[GH Actions: news-pipeline.yml (every 6h) or cead-scraper.yml (quarterly)]
  |-- python pipeline/scrape_news.py   (reads OPENROUTER_API_KEY from env; DEEPSEEK_API_KEY
  |                                      only if NEWS_PROVIDER=deepseek is set, M-01)
  |-- python pipeline/scrape_cead.py
  |-- git add data/
  |-- if data/ changed → git commit "data: auto-update [skip ci]" && push-with-rebase.sh
  |-- Guard deploy hook (always, AFTER the commit -- F-84): hard-fails the job if
  |     CF_DEPLOY_HOOK_URL is unset, but the data commit already happened and was
  |     pushed, so a rotated hook cannot also lose scraped data
  |-- if changed == true → curl -X POST $CF_DEPLOY_HOOK_URL
  |
  v
[Cloudflare Pages receives the Deploy Hook POST]
  |-- npm run build   (working directory: site/)
  |     └── prebuild: scripts/sync-data.mjs copies data/cead → public/data/
  |     └── astro build → dist/
  |-- serve dist/ from Cloudflare CDN at ischilesafe.com
```

**Key principle:** GitHub Actions does NOT build the site. It only scrapes data, commits
changed data to the repo, and pings the Deploy Hook. Cloudflare Pages does the Astro build.

**Code-push deploys (`deploy-on-code.yml`):** Disabling CF auto-build (§4) also stops code-only
pushes from redeploying production. `deploy-on-code.yml` closes that gap: a push to `master`
touching `site/**` (or the workflow file itself) curls the same Deploy Hook, producing a real
build. Data-only commits (`data/**`, `[skip ci]`) do not match its `paths` filter, so the
rebuild-loop guard (§4, §9) is unaffected. Verified 2026-06-19 (GL-01/GL-02).

---

## 2. Create the Cloudflare Pages Project

1. Go to **Cloudflare dashboard** → **Workers & Pages** → **Create** → **Pages** →
   **Connect to Git**.
2. Authorize GitHub if prompted. Select this repository (`Is Chile Safe`).
3. Click **Begin setup**.

---

## 3. Configure the Build Settings

In the **Build configuration** section, set:

| Setting | Value |
|---------|-------|
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory (Advanced) | `site` |

The Astro project lives in `site/` — the root directory setting tells Cloudflare Pages to `cd`
into `site/` before running `npm run build`. The build output `dist` is therefore `site/dist/`.

Click **Save and Deploy** to create the project (this triggers a one-time initial build — that
is fine). Wait for it to complete before proceeding to step 4.

---

## 4. Disable Automatic Production Deployments (PRIMARY Rebuild-Loop Guard)

**This is the most critical step. Do not skip it.**

Go to your new CF Pages project → **Settings** → **Builds** → **Branch control** →
find **"Enable automatic production branch deployments"** and turn it **OFF**.

**Why this matters (INFRA-02):** By default, Cloudflare Pages builds on every `git push` to
the production branch. GitHub Actions commits data updates every 6 hours. With auto-build
enabled, each data commit triggers a CF build — up to 4 builds per day from news alone, plus
additional pushes. This burns the 500 builds/month free quota in weeks and creates an infinite
rebuild loop.

With auto-build **disabled**, the only way to trigger a CF Pages build is via the Deploy Hook
(step 5). The data-pipeline workflows already gate the Deploy Hook curl on actual data changes:
if no new data was scraped, no commit happens, no Hook is called.

**Note on `[skip ci]`:** The data-commit messages include `[skip ci]`. This is a secondary
belt-and-suspenders measure that may suppress CF's GitHub App trigger even if auto-build is
accidentally left on. It is **not** the primary guard — disabling auto-build in the dashboard
is. Do not rely on `[skip ci]` alone.

---

## 5. Create the Deploy Hook

1. CF Pages project → **Settings** → **Builds** → **Deploy Hooks** → **Add**.
2. Name: `data-update` (or any descriptive name).
3. Branch: **must match the branch the scheduled workflows push to** — i.e. this repo's
   *default* branch (scheduled GitHub Actions always run on, and `git push` to, the default
   branch). This repo currently has both `master` and `main`; set the Deploy Hook branch to
   whichever you set as the GitHub **default branch**, and confirm CF Pages' production branch
   matches it too. A mismatch means the Hook silently builds stale content from the wrong branch.
4. Click **Generate Deploy Hook**.
5. **Copy the generated URL** — it looks like
   `https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/<uuid>`.
   You will need this in step 6. Treat it as a secret — anyone with this URL can trigger a build.

---

## 6. Add Repository Secrets

Go to the GitHub repository → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Add all of the following:

| Secret Name | Value | Source | Consumed by |
|-------------|-------|--------|-------------|
| `CF_DEPLOY_HOOK_URL` | The Deploy Hook URL from step 5 | Cloudflare Pages dashboard | `news-pipeline.yml`, `cead-scraper.yml` (guarded post-commit, F-84), `deploy-on-code.yml` (guarded first-step) |
| `OPENROUTER_API_KEY` | Your OpenRouter API key | [OpenRouter console](https://openrouter.ai/) | `news-pipeline.yml` — the default news classifier (Granite 4.1 8B) runs through OpenRouter |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key (optional) | [DeepSeek console](https://platform.deepseek.com/) | `news-pipeline.yml` scrape step's `env:`, only if `NEWS_PROVIDER=deepseek` is set — NOT hard-guarded (M-01, see below) |
| `R2_ENDPOINT_URL` | R2 (S3-compatible) endpoint URL | Cloudflare R2 dashboard | `r2-archive.yml` |
| `R2_ACCESS_KEY_ID` | R2 access key ID | Cloudflare R2 dashboard | `r2-archive.yml` |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key | Cloudflare R2 dashboard | `r2-archive.yml` |

There is no `R2_BUCKET` secret and none is needed — `pipeline/archive_r2.py` defaults it to
`"ischilesafe"` when unset. Do not add one to the guard list in `r2-archive.yml`; a prior phase
did this by mistake (H-01) and it would have hard-failed the daily archive on a correctly
configured repo.

**Without `CF_DEPLOY_HOOK_URL`:** As of Phase 32 (F-76, amended F-84), this is a HARD failure,
not a silent skip. In `news-pipeline.yml` and `cead-scraper.yml` the guard runs AFTER the data
commit/push, so scraping and the data commit still happen and are not lost — only the job goes
red and an issue is filed. In `deploy-on-code.yml` the guard is the first step (there is no data
collection to protect in that job), so a missing hook there fails immediately. There is no
"dry-run mode" that skips the curl silently; the closest equivalent is running with all secrets
set via `workflow_dispatch` against a scratch branch.

**Without `OPENROUTER_API_KEY`:** `news-pipeline.yml`'s "Guard required secrets" step fails the
job immediately, before any scraping happens — this is the required secret for the default
classifier.

**Without `DEEPSEEK_API_KEY`:** No effect on the default configuration. `scrape_news.py` only
reads this key when `NEWS_PROVIDER=deepseek` is explicitly set, which nothing in this repo does
today. CEAD scraping is unaffected either way (it does not use any LLM).

---

## 7. Bind the Custom Domain and Provision HTTPS

1. CF Pages project → **Settings** → **Custom domains** → **Add**.
2. Enter `ischilesafe.com`.
3. If your domain's DNS is managed in Cloudflare: CF auto-creates the CNAME record and
   provisions a Let's Encrypt TLS certificate automatically. HTTPS is live within minutes.
4. If DNS is managed elsewhere: CF will display the CNAME target — add it at your DNS provider,
   then wait for propagation (up to 48h depending on TTL).

After the domain is active, confirm with:

```bash
curl -I https://ischilesafe.com
```

Expected output: `HTTP/2 200` (or `HTTP/1.1 200`), with `cf-ray` and `content-type: text/html`
headers confirming Cloudflare CDN delivery.

---

## 8. First Deploy and Dry-Run Test

### 8a. Structural check (before setting CF_DEPLOY_HOOK_URL)

There is no silent-skip dry-run mode as of Phase 32 (F-76, amended F-84) — a missing
`CF_DEPLOY_HOOK_URL` is a hard, red-job failure, by design (see §6). If you want to confirm the
scrape/commit path works before the CF project exists, run `news-pipeline.yml` via
**Actions** → **News Pipeline** → **Run workflow** with `OPENROUTER_API_KEY` set but
`CF_DEPLOY_HOOK_URL` still unset. The workflow will:

- Guard `OPENROUTER_API_KEY` (fails first if missing).
- Scrape news and, if data changed, commit and push it — this part completes and is preserved.
- Then hard-fail at the "Guard deploy hook" step (placed AFTER the commit, F-84) and open a
  `pipeline-failure-news` issue. This red job is EXPECTED and confirms the scrape/commit path
  works; it is not a structural problem.

Set `CF_DEPLOY_HOOK_URL` before relying on this cron in production — an intentionally red job
is only acceptable as a one-off structural check, not as an ongoing state.

### 8b. Real first deploy (after setting both secrets)

Option A — trigger via workflow_dispatch:
1. Go to **Actions** → **News Pipeline** → **Run workflow**.
2. The workflow scrapes, commits if new data, then POSTs to the Deploy Hook.
3. Monitor the CF Pages build in the Cloudflare dashboard.

Option B — curl the hook directly for an immediate deploy (no scrape):
```bash
curl -X POST "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/<your-uuid>"
```
Replace `<your-uuid>` with your actual UUID. This triggers CF to build from the current HEAD
of `master` without going through GitHub Actions.

After the CF build completes, verify:
```bash
curl -I https://ischilesafe.com
# Expect: HTTP/2 200 or HTTP/1.1 200
```

---

## 9. Rebuild-Loop Verification (INFRA-02 Acceptance)

After go-live, verify the rebuild-loop guard is working:

1. Make a documentation-only change (edit this file, any `.planning/` file, or a `README.md`)
   and push it to `master`.
2. Wait 5 minutes.
3. Go to CF Pages → **Deployments** (build history).
4. **The build count must NOT increase.** No new deployment should appear.

**Why this works:** The cron workflows stage only `data/` (`git add data/`). A docs-only push
contains no `data/` changes, so `git diff --staged --quiet` exits 0, no commit from the scraper
happens, and no Deploy Hook is curled. The auto-build is already disabled (step 4), so the
direct push to `master` also cannot trigger CF Pages.

**Warning signs that the rebuild loop is active:** CF deployments increasing faster than
4/day (news cadence) or 1/quarter (CEAD cadence); CF builds appearing without a corresponding
`curl` in the workflow logs; deploys triggered within seconds of a data commit (indicates
CF's GitHub App is still watching the branch).

**Where to find the build count:** CF Pages project → **Deployments** tab. Each row is one
build. The timestamp and trigger source (Deploy Hook vs Git push) are shown per row.

---

## 10. Operational Notes

### Workflow Cadences (CRON-07, audited 2026-08-04, Phase 32; corrected fix-cycle 1)

| Workflow | File | Schedule | Trigger | Secrets Consumed (hard-guarded only where the code actually requires them, F-94) | Permissions | Writes |
|----------|------|----------|---------|-----------------------------------------------|-------------|--------|
| News Pipeline | `.github/workflows/news-pipeline.yml` | Every 6 hours (`0 */6 * * *`) | `schedule` + `workflow_dispatch` | `OPENROUTER_API_KEY` (scrape, hard-guarded), `DEEPSEEK_API_KEY` (scrape `env:` only, NOT guarded -- M-01, consumed only if `NEWS_PROVIDER=deepseek`), `CF_DEPLOY_HOOK_URL` (deploy, guarded AFTER the data commit per F-84 -- a rotated hook fails the job loudly but no longer also blocks collection) | `contents: write`, `issues: write` | `data/` (news), pushes to `master` via `push-with-rebase.sh`, triggers CF deploy hook |
| R2 Research Archive | `.github/workflows/r2-archive.yml` | Daily 05:30 UTC (`30 5 * * *`) | `schedule` + `workflow_dispatch` | `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` -- NOT `R2_BUCKET` (H-01/F-94: it is not a secret, `archive_r2.py` defaults it to `"ischilesafe"`) | `contents: read`, `issues: write` | R2 bucket only -- no `data/` write, no push |
| CEAD Scraper | `.github/workflows/cead-scraper.yml` | Quarterly (`0 3 1 1,4,7,10 *`) | `schedule` + `workflow_dispatch` | `CF_DEPLOY_HOOK_URL` (guarded AFTER the data commit per F-84) | `contents: write`, `issues: write` | `data/` (CEAD + composite/enrichment), pushes to `master` via `push-with-rebase.sh`, triggers CF deploy hook -- **expected to fail with HTTP 403 on Actions IPs; documented in the file's own header comment (CRON-05)**. `actions/setup-python@v7` + `pip install -r pipeline/requirements.txt` restored after a wave-2 rewrite dropped them (H-02, fix-cycle 1) -- without them every `python …` step fails with `ModuleNotFoundError` instead of the expected 403, destroying the reminder's one useful signal. |
| Pipeline Heartbeat | `.github/workflows/heartbeat.yml` | Daily 12:00 UTC (`0 12 * * *`) | `schedule` + `workflow_dispatch` | none (uses `github.token` only) | `actions: read`, `contents: read`, `issues: write` | nothing -- read-only checks against all three data-cron cadences (news/R2/CEAD, CRON-02). The CEAD check is quarter-boundary based, not a flat day threshold (F-93, fix-cycle 1) -- it counts how many quarterly due dates (Jan 1 / Apr 1 / Jul 1 / Oct 1 UTC) have elapsed since the last `data/cead/` commit; 1 elapsed boundary is a maintainer running late (silent), 2+ means a whole quarter was genuinely skipped (alert). **The cost of that tolerance, stated in days rather than left to be inferred: detection latency is up to ~92 days, because the alert fires on the SECOND consecutive missed release, not the first.** Concretely, as of 2026-08-04 the Jul-1 release has already been missed, the guard is correctly green, and it will fire on 2026-10-01 if no local scrape lands before then. If a single missed quarter ever needs to be caught immediately, the fix is a second, softer signal — not a lower boundary count, which would just reintroduce the false alarms on a legitimate cadence that F-83c and F-93 were spent removing. This replaces a flat-day threshold that could not be tuned without either crying wolf on a healthy system (100d) or staying green through an already-missed quarter (150d) -- Operating Lesson 26. News/R2 thresholds now compare epoch seconds, not truncated integer days (F-96, fix-cycle 1) -- a "3-day" threshold used to only fire after 3d23h59m; it now fires precisely at >3 days, still passing at exactly 3 days. Named residuals (F-89): an R2 run that succeeds while archiving zero items still passes; dedup is per open issue, so closing an alert without fixing the cron reopens a new one the next day -- both intended, not hidden. This workflow's OWN silence is not monitored by anything else in this repo (F-79) -- news staleness has a second, independent instrument (`freshness.mjs`, validator #15); R2 staleness does not. |
| Deploy on Code Push | `.github/workflows/deploy-on-code.yml` | On push to `master` touching `site/**` or `.github/workflows/deploy-on-code.yml` itself (L-07) | `push` | `CF_DEPLOY_HOOK_URL` (guard stays first-step -- this job has no data collection to protect) | `contents: read` | nothing -- triggers CF deploy hook only. **No failure alert** (M-06, accepted): this job is push-triggered, so a human is already present at the keyboard when it runs; adding `issues: write` to a deploy-only job's token for a marginal alerting gain was judged not worth the widened scope. This is a deliberate asymmetry with the other four workflows, not an oversight. |
| CI | `.github/workflows/ci.yml` | PRs + `workflow_dispatch` | `pull_request` + `workflow_dispatch` | none | explicit workflow-level `permissions: contents: read` (`ci.yml:8-9` -- NOT the repo default; M-09 fix-cycle 1) | nothing. Three jobs: `frontend` (build + validate), `pipeline` (pytest), `lint-workflows` (runs `.github/scripts/lint-workflows.sh`, the armed/canary-proven instrument -- wired in fix-cycle 1, H-03/F-95; previously this job ran `rhysd/actionlint@v1` directly, whose shellcheck-wiring silently disables shell linting when misconfigured). **Not covered:** direct pushes to `master` (this repo's actual commit pattern) are NOT linted by CI, because `ci.yml` triggers on `pull_request` + `workflow_dispatch` only. F-95 explicitly rejected adding a `push: branches: [master]` trigger — it would run build+validate (including `freshness`, which can go red purely from data age, F-19) on every push to a live repo, manufacturing a recurring red CI signal. Master-push linting is the maintainer's responsibility: run `bash .github/scripts/lint-workflows.sh` locally before pushing workflow changes. |

**CRON-06 claim (F-90, narrowed from an earlier unconditional statement):** every
workflow that writes to `data/` fetches and rebases before pushing (`push-with-rebase.sh`,
shared by News Pipeline and CEAD Scraper). This guarantees **no SILENT lost update**: a
race on DISJOINT paths (the real news-vs-CEAD shape) survives with both commits landing
on `origin`; a race on the SAME file aborts loudly (`::error::` + exit 1, `origin` left
exactly as the first writer left it) rather than silently merging or silently discarding
data -- proven in both directions via real local bare-clone git repos, encoded in
`pipeline/tests/test_push_race.py`. This is NOT a claim that no data is ever lost under
any race; a same-file conflict's losing side is intentionally discarded for a human to
re-trigger, loudly, not silently.

**Clustering audit note (CRON-07):** this audit was originally scoped in ROADMAP.md to run
"after Phase 28 wires clustering into the news pipeline," on the premise that clustering
would change the news cron's cost/latency profile. Phase 26 returned NO-GO on clustering
(fp=11, precision 0.667 against a 100%/zero-false-merge gate) and Phase 28 shipped
faceting-only -- **no clustering code was ever wired into `news-pipeline.yml`.** The cron's
shape is unchanged: one `python pipeline/scrape_news.py` invocation, `timeout-minutes: 30`.
There is no cost/latency change to account for; this note exists so a future reader does
not infer one from the requirement's original phrasing.

### SHA-Pin and Version-Pin Decision Record (SEC-02, F-103)

SEC-02 requires a documented pin decision for every reference class this repo's CI/CD
tooling depends on, not just the `uses:` lines. Three classes exist:

**(a) The 13 `actions/*` `uses:` refs** (`actions/checkout@v7` x8, `actions/setup-python@v7`
x4, `actions/setup-node@v7` x1, across all six workflow files) -- **decision: SHA-pin, with
a `# vN.N.N` comment.** GitHub-owned tags are force-moved by design on every patch release
(a `@v7` tag today can point at a different commit tomorrow without any repo-side signal),
so a tag-only reference lets upstream silently change what code runs with this repo's
`GITHUB_TOKEN`. `.github/dependabot.yml`'s `github-actions` ecosystem (Plan 33-02) is what
keeps these pins from rotting -- it opens a bump PR whenever `actions/checkout`,
`actions/setup-python`, or `actions/setup-node` cut a new release, so the pin is refreshed
on a reviewable cadence instead of silently going stale. `.github/scripts/check-sha-pins.sh`
is the enforcing gate (SEC-02 success criterion 1): it fails the build on any `uses:` ref
whose `@`-suffix is not a full 40-hex commit SHA with a trailing version comment, and
carries its own coverage floor (`EXPECTED_MIN_COUNT=13`) so a future glob typo cannot
silently narrow the scan to fewer refs than exist today.

**(b) The two binaries `.github/scripts/fetch-lint-tools.sh` downloads** (`actionlint`
v1.7.7, `shellcheck` v0.11.0) -- **decision: already SHA-256-pinned, by Phase 32 (F-92); this
plan only records that decision, it does not re-pin anything.** This decision predates and
is unchanged by Phase 33 -- `fetch-lint-tools.sh` itself is untouched by this phase.

**(c) `zizmor`** -- **decision: version-pinned at `1.10.0`, invoked ephemerally** via
`pipx run zizmor==1.10.0` in CI (Plan 33-02) and `uvx zizmor@1.10.0` locally, never added
to `pipeline/requirements.txt` (SEC-04 forbids it). There is no SHA to pin here -- this is
not a `uses:`-style reference, it is a pinned-version ephemeral CLI invocation. zizmor is
cited as the OWASP/GitHub-ecosystem-endorsed Actions scanner (10k+ stars, `zizmorcore` org,
referenced by GitHub's own blog; research's Package Legitimacy Audit, `docs.zizmor.sh`).
**FM-16 (required note): this version pin is NOT covered by dependabot** -- `pipx run` is
not a manifest entry, and SEC-04 explicitly forbids adding zizmor to
`pipeline/requirements.txt`, so nothing will ever bump this pin automatically. Left alone,
it will sit at `1.10.0` indefinitely, silently missing every audit zizmor adds after this
phase. **The pinned zizmor version must be re-evaluated at each milestone close**, not left
to rot the way an un-dependaboted pin otherwise would.

**Local pre-push gate:** run `uvx zizmor@1.10.0 --persona=regular .github/workflows/`
locally before pushing any workflow change, using the exact same pinned version as CI's
`pipx run zizmor==1.10.0` step (Plan 33-02) -- this is in addition to, not a replacement
for, the existing `bash .github/scripts/lint-workflows.sh` local-gate instruction in the
Workflow Cadences table above.

**Zizmor CI Verification (FM-10, BLOCKING):** `ci.yml`'s `lint-workflows` job must be proven
to actually execute the zizmor step on a real `ubuntu-latest` runner -- a green job with the
step skipped by a misconfigured `if:` would not satisfy this. **This evidence cannot be
produced by this plan's executor**, because producing it requires a `workflow_dispatch` run
of `ci.yml` against the commits this plan lands, which in turn requires those commits to
already be on `origin` -- and per this phase's execution contract, the executor does not
push; the orchestrator pushes after the phase-close gate. **Status: PENDING.** The nearest
available evidence today is a real, already-executed PR-triggered run of the
`lint-workflows` job (run `30975549062`, job `92208670221`, 2026-08-05,
`https://github.com/xenaquis/is-chile-safe/actions/runs/30975549062/job/92208670221`),
which confirms the job's mechanics (checkout, `lint-workflows.sh`'s canary firing correctly)
on the real runner image -- but that run's `ci.yml` ref predates this phase's zizmor step
being wired in, so its log contains no zizmor version banner and does **not** satisfy this
item. **Required follow-up, to be completed by the orchestrator after push:** dispatch
`ci.yml` via `workflow_dispatch` on `master` once this phase's commits land, then replace
this paragraph with the real run URL, the `lint-workflows` job's conclusion, and the
specific log line showing zizmor's own version banner (e.g. `zizmor 1.10.0`) actually
printed. This is the only observation event that can prove A1 ("pipx ships preinstalled on
`ubuntu-latest`") true on a real runner rather than merely cited from GitHub's own image
manifest (F-112). Until that follow-up lands, SEC-04's success criterion 4 is not yet met.

**SEC-01/SEC-05 settings re-verification (re-run at this plan's close, per F-107):** rather
than re-doing the full settings history sweep, this plan re-ran the same specific API reads
F-107/F-111 already used. `gh api repos/xenaquis/is-chile-safe` (2026-08-05, this session)
confirms: repo **PUBLIC** (`"visibility":"public"`), `secret_scanning.status: "enabled"`,
`secret_scanning_push_protection.status: "enabled"`. `default_workflow_permissions: "read"`
and `can_approve_pull_request_reviews: false` were established and unchanged since
F-107/F-111 (Phase 32) -- this plan did not re-query the Actions permissions endpoint
separately since neither this plan nor Plan 33-01/33-02 touch repository-level Actions
settings, only workflow-file content. 0 secret-scanning alerts open -- verified via
`gh api repos/xenaquis/is-chile-safe/secret-scanning/alerts --jq 'length'` (2026-08-05,
returned 0; F-111). `open_issues_count` from `gh api repos/xenaquis/is-chile-safe` counts
open issues **and pull requests** and has no relationship to secret-scanning alerts -- it
is not cited as evidence here.

### Known Gaps (documented, not remediated in fix-cycle 1 -- F-97)

**H-05 -- new CEAD data pushed by a maintainer never triggers a production build.**
`deploy-on-code.yml` filters on `site/**` (and its own workflow file); `data/**` matches
neither. CF auto-build is disabled (§4). So the documented quarterly runbook -- run
`pipeline/scrape_cead.py` locally, commit, `git push` -- lands new CEAD data on `master`, but
nothing curls the Deploy Hook for it. Production keeps serving the previous quarter's numbers
until the next unrelated `site/**` push happens to rebuild. This is a REAL, pre-existing gap.
It is not fixed here because changing production deploy triggers is a live-risk change outside
this phase's approved scope (Phase 32 is about cron *consistency*, not deploy topology) --
tracked in `.planning/STATE.md` backlog for a future phase that owns deploys to pick a shape
(either an explicit `curl` step appended to the local runbook, or a `workflow_dispatch`-only
`deploy.yml` the maintainer runs after a manual data push).

**M-07 -- four `continue-on-error: true` steps in `cead-scraper.yml` can commit and deploy
partial data with a green job.** `fetch_enusc_vhdv.py`, `build_enusc_enrichment.py`,
`build_composite_index.py`, `build_map_payload.py` all swallow their exit codes. If
`build_map_payload.py` crashes halfway, "Commit data if changed" still stages and pushes
whatever `data/` contains. In practice this is masked today by CRON-05 (the CEAD scraper is
blocked with an HTTP 403 from GitHub Actions runner IPs, so it never reaches these enrichment
steps on Actions) -- H-02 (the missing setup-python/pip install) was fixed in Phase 32's fix
cycle 1 and no longer contributes to the masking. This is a data-quality defect in the
CEAD enrichment path, not a cron-consistency one -- fixing it here would re-open CEAD's data
path unattended, outside this phase's scope. Tracked in `.planning/STATE.md` backlog.

**M-08 -- `fetch-lint-tools.sh` does not re-verify an already-present binary against its
pinned SHA-256 on every invocation.** The idempotency short-circuit
(`.github/scripts/fetch-lint-tools.sh:42`) checks executability only, not the hash, once
`.tools/` exists. Accepted: `.tools/` is gitignored and machine-local (never shipped or
shared), and `lint-workflows.sh`'s canary (F-85) proves at every invocation that whatever
binary is present actually still works correctly on the known-bad fixture -- a silently
swapped-but-functional shellcheck would need to also produce the exact SC2034+SC2086 findings
to pass undetected, which is a narrow enough bar that this residual is accepted rather than
adding a stat/hash check on every local run.

### Cron Timing Drift

GitHub Actions cron triggers are best-effort — expect 15–30 minutes of drift under load. A
news pipeline that was scheduled for 06:00 UTC may run at 06:18 UTC. This is normal and not
an incident. The 30-day news data window and 6-hour cadence make this drift operationally
irrelevant.

### Build Quota

Cloudflare Pages free tier allows **500 builds/month**. With the rebuild-loop guard in place:
- News pipeline: up to 4 builds/day when news data changes = ~120 builds/month.
- CEAD scraper: 1 build/quarter = negligible.
- Total expected: well under 500/month. If approaching 500, check the CF deployment history
  for unexpected build triggers.

### OPENROUTER_API_KEY / DEEPSEEK_API_KEY Absence Behavior (updated, M-01)

If `OPENROUTER_API_KEY` is not set as a repo secret, `news-pipeline.yml`'s "Guard required
secrets" step fails immediately, before any scraping happens. This is the required key for the
default classifier (Granite 4.1 8B via OpenRouter).

`DEEPSEEK_API_KEY` is NOT hard-guarded. `pipeline/scrape_news.py` only reads it when
`NEWS_PROVIDER=deepseek` is explicitly set, which nothing in this repo does today. Its absence
has no effect on the default configuration — this was corrected in fix-cycle 1 (M-01) after a
prior guard made this unused-by-default secret load-bearing, which would have hard-failed the
6-hourly news cron the day someone tidied up the unused key.

The CEAD scraper is unaffected by either key (it does not use any LLM).

### CF Pages Build Failure Recovery

If a CF Pages build fails (bad Astro build, missing npm package, etc.):
1. Investigate the build log in CF Pages → Deployments → click the failed build.
2. The previous successful deployment remains live on the CDN — no outage for users.
3. Fix the code, push to `master`, then manually curl the Deploy Hook to trigger a new build.

---

## Quick Reference Checklist

- [ ] CF Pages project created (Workers & Pages → Create → Pages → Connect to Git)
- [ ] Build settings: command `npm run build`, output `dist`, root directory `site`
- [ ] Automatic production deployments **disabled** (Settings → Builds → Branch control)
- [ ] Deploy Hook created (branch `master`), URL copied
- [ ] `CF_DEPLOY_HOOK_URL` secret added to GitHub repo
- [ ] `OPENROUTER_API_KEY` secret added to GitHub repo (required for the default news classifier)
- [ ] `DEEPSEEK_API_KEY` secret added to GitHub repo (optional, only if `NEWS_PROVIDER=deepseek`)
- [ ] Custom domain `ischilesafe.com` bound, HTTPS confirmed (`curl -I`)
- [ ] `news-pipeline.yml` `workflow_dispatch` run succeeded (all secrets set — there is no silent-skip dry-run mode, §8a)
- [ ] Docs-only push confirmed CF build count stayed flat (rebuild-loop guard verified)
- [x] Code-push deploy trigger verified — a `site/**` push fired `deploy-on-code.yml`, which curled the Deploy Hook and produced a real CF build (GL-01, 2026-06-19)
