# DEPLOYMENT.md — Cloudflare Pages Go-Live Runbook

**ischilesafe.com** | Last updated: 2026-06-19

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
  |-- python pipeline/scrape_news.py   (reads DEEPSEEK_API_KEY from env)
  |-- python pipeline/scrape_cead.py
  |-- git add data/
  |-- if data/ changed → git commit "data: auto-update [skip ci]" && git push
  |                             AND
  |-- if changed == true AND CF_DEPLOY_HOOK_URL is set
  |       → curl -X POST $CF_DEPLOY_HOOK_URL
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
**New repository secret**. Add both of the following:

| Secret Name | Value | Source |
|-------------|-------|--------|
| `CF_DEPLOY_HOOK_URL` | The Deploy Hook URL from step 5 | Cloudflare Pages dashboard |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | [DeepSeek console](https://platform.deepseek.com/) |

**Without `CF_DEPLOY_HOOK_URL`:** The `curl` step in both cron workflows is skipped silently
(guarded by `env.CF_HOOK != ''`). Scraping and data commits still happen; only the CF Pages
trigger is absent. This is the dry-run mode — safe to use before the CF project exists.

**Without `DEEPSEEK_API_KEY`:** `pipeline/scrape_news.py` exits with an error. CEAD scraping
is unaffected (it does not use DeepSeek).

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

### 8a. Dry-run (before setting CF_DEPLOY_HOOK_URL)

Run `news-pipeline.yml` via **Actions** → **News Pipeline** → **Run workflow** while
`CF_DEPLOY_HOOK_URL` is **not yet set** as a repo secret. The workflow will:

- Attempt to scrape news (exits 1 if `DEEPSEEK_API_KEY` is also missing — that is fine for
  a structural dry-run).
- If scraping succeeds and data changed: commit and push.
- Skip the `curl` step because `env.CF_HOOK` is empty.

This confirms the workflow structure is sound without triggering a CF build.

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

### Workflow Cadences

| Workflow | File | Schedule | Trigger |
|----------|------|----------|---------|
| News Pipeline | `.github/workflows/news-pipeline.yml` | Every 6 hours (`0 */6 * * *`) | `schedule` + `workflow_dispatch` |
| CEAD Scraper | `.github/workflows/cead-scraper.yml` | Quarterly (`0 3 1 1,4,7,10 *`) | `schedule` + `workflow_dispatch` |
| Deploy on Code Push | `.github/workflows/deploy-on-code.yml` | On push to `master` touching `site/**` | `push` |
| CI | `.github/workflows/ci.yml` | PRs + `workflow_dispatch` | `pull_request` + `workflow_dispatch` |

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

### DEEPSEEK_API_KEY Absence Behavior

If `DEEPSEEK_API_KEY` is not set as a repo secret, `pipeline/scrape_news.py` will exit with
a non-zero code and the GH Actions job will fail. The CEAD scraper is unaffected. Set the
key in repo secrets before enabling the news pipeline in production.

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
- [ ] `DEEPSEEK_API_KEY` secret added to GitHub repo
- [ ] Custom domain `ischilesafe.com` bound, HTTPS confirmed (`curl -I`)
- [ ] `news-pipeline.yml` dry-run via `workflow_dispatch` succeeded
- [ ] Docs-only push confirmed CF build count stayed flat (rebuild-loop guard verified)
- [x] Code-push deploy trigger verified — a `site/**` push fired `deploy-on-code.yml`, which curled the Deploy Hook and produced a real CF build (GL-01, 2026-06-19)
