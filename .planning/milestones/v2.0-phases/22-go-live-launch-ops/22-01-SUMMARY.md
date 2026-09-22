---
phase: 22-go-live-launch-ops
plan: 01
subsystem: infra
tags: [cloudflare-pages, github-actions, deploy-hook, astro, nvmrc, ci-cd]

requires:
  - phase: 20-and-earlier
    provides: deploy-on-code.yml, news-pipeline.yml, DEPLOYMENT.md runbook
provides:
  - Live production deploy pipeline for ischilesafe.com (code push → deploy hook → CF build)
  - Verified rebuild-loop guard (auto-build OFF + paths filter + [skip ci])
  - Node 22.12.0 pin so Astro 6.4.6 builds on Cloudflare
affects: [22-03, news-pipeline, future-deploys]

tech-stack:
  added: []
  patterns:
    - "Code-push deploys via deploy-on-code.yml curling CF_DEPLOY_HOOK_URL (auto-build stays OFF)"

key-files:
  created: []
  modified:
    - .nvmrc
    - site/.nvmrc
    - site/astro.config.mjs
    - DEPLOYMENT.md

key-decisions:
  - "Pinned Node 22.12.0 in both .nvmrc files — Astro 6.4.6 requires >=22.12.0; the prior pin of 20 caused the first CF build to fail"
  - "Connecting the repo via CF Git integration is the documented setup (DEPLOYMENT.md §2); the deploy hook + auto-build-OFF layer on top of it, not as an alternative"

patterns-established:
  - "Rebuild-loop guard: CF auto-build paused + deploy-on-code.yml paths:site/** + data commits use [skip ci]"

requirements-completed: [GL-01, GL-02]

duration: ~50min
completed: 2026-06-19
---

# Phase 22-01: Activate Production Deploys Summary

**Live Cloudflare Pages deploy pipeline for ischilesafe.com — a `site/**` push fires `deploy-on-code.yml` → curls the Deploy Hook → real CF build, while data-only commits add zero builds.**

## Performance

- **Duration:** ~50 min (incl. Node-version deploy failure + fix)
- **Completed:** 2026-06-19
- **Tasks:** 4 (1 human-action, 2 human-verify, 1 auto) + 1 deviation fix
- **Files modified:** 4

## Accomplishments
- `CF_DEPLOY_HOOK_URL` and `DEEPSEEK_API_KEY` set as repo secrets; CF auto-build confirmed **paused** (primary rebuild-loop guard).
- **GL-01:** code push (`6ed437c`, touching `site/**`) triggered `deploy-on-code.yml` → run succeeded with `CF_HOOK` in scope and Cloudflare returned `"errors": []` (not dry-run) → new Deploy-Hook build `baac4529` succeeded; production serves v2.0 (composite index renders on commune pages, HTTP 200).
- **GL-02:** data-only commit (`075df53`, `[skip ci]`, only `data/incidents/current.json`) produced **"No deployment available"** in CF — zero builds; no workflow triggered. Guard verified.
- DEPLOYMENT.md documents the code-push trigger (§1 note, §10 cadence row, Quick Reference item).

## Task Commits

1. **Task 1: User sets CF deploy hook + secrets, confirms auto-build OFF** — no repo commit (Cloudflare dashboard + GitHub Secrets UI; secrets verified via `gh api`, names only)
2. **Task 2: Verify code push triggers CF build (GL-01)** — `6ed437c` (chore)
3. **Task 3: Confirm data-only commit adds no build (GL-02)** — `075df53` (test push) + `1e21366` (restore)
4. **Task 4: Document the code-push trigger in DEPLOYMENT.md** — `4112089` (docs)

**Deviation fix:** `ec41b72` (fix) — Node pin bump.

## Files Created/Modified
- `.nvmrc`, `site/.nvmrc` — Node pin 20 → 22.12.0 (Astro 6.4.6 floor)
- `site/astro.config.mjs` — trivial comment to exercise the code-push deploy path
- `DEPLOYMENT.md` — code-push trigger documented; guard sections (§4, §9) unchanged

## Decisions Made
- See key-decisions frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Blocking] First CF build failed on unsupported Node version**
- **Found during:** Task 2 (first production build)
- **Issue:** Both `.nvmrc` files pinned Node `20`; Astro 6.4.6 requires `>=22.12.0`. CF honored the pin (installed 20.20.0) and `astro build` aborted with "Node.js v20.20.0 is not supported by Astro". Node 20 is also EOL.
- **Fix:** Bumped both `.nvmrc` files to `22.12.0` and pushed; CF rebuilt successfully on Node 22.
- **Files modified:** `.nvmrc`, `site/.nvmrc`
- **Verification:** Subsequent CF build (`ec41b72` → `619e9dc0`) succeeded; production returns 200 with v2.0 content.
- **Committed in:** `ec41b72`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to achieve GL-01 (deploys could not succeed on Node 20). No scope creep.

## Issues Encountered
- Repo secrets were empty at start (`total_count: 0`) — neither `CF_DEPLOY_HOOK_URL` nor `DEEPSEEK_API_KEY` was set, contradicting DEPLOYMENT.md §6's assumption that DeepSeek's key was already configured. Surfaced to the user; both set before proceeding.

## User Setup Required
None outstanding — `CF_DEPLOY_HOOK_URL` and `DEEPSEEK_API_KEY` are set; CF auto-build paused; custom domain `ischilesafe.com` serving HTTPS 200.

## Next Phase Readiness
- v2.0 deploy is live → unblocks 22-03 (sitemap submission to GSC).
- `DEEPSEEK_API_KEY` now set → unblocks 22-02 (live News Pipeline run + commune audit).

---
*Phase: 22-go-live-launch-ops*
*Completed: 2026-06-19*
