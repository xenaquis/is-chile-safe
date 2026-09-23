# Phase 37: Dependency & Security Hygiene — Research

**Researched:** 2026-09-23
**Domain:** GitHub Dependabot PR triage, npm/pip security advisories, CodeQL enablement
**Confidence:** HIGH (all findings are direct `gh`/`npm audit`/repo-read evidence, not training knowledge)

## Summary

17 open PRs exist (all Dependabot; oldest is 46 days), against a DEPS-02 target of ≤3, none >14 days.
29 open Dependabot alerts exist across npm transitive deps (2 critical — both `astro`). `npm audit
--omit=dev` confirms the critical is a real RCE (GHSA-26w7-cxv4-gfx2, AVIF image optimization,
CVSS 9.8) fixed at astro ≥7.2.8, exactly matching PR #39's target. One PR (#18, `typescript`
5.9.3→7.0.2, dev-only) already has a **failing CI** (`Frontend build + validate` and `Cloudflare
Pages` both FAILURE) — do not merge as-is; close with reason or defer pending a follow-up major
bump attempt outside this phase. PR #37 (openai 2.53.0→3.7.0) also shows a **FAILURE on Pipeline
pytest** at PR-open time (2026-09-05) — must be re-validated (tests may have since diverged; rerun
locally) and gated on `eval_classifier.py` reproducing identical metrics per DEPS-03, using the
Phase 34 winner `deepseek/deepseek-v4.1-flash` (reasoning disabled) recorded in `34-AB-RESULTS.json`.

CodeQL is currently **not enabled** (`code-scanning/alerts` → 404 "no analysis found"). The
directive text itself already flags the tension: enabling CodeQL via repo Settings is a "repo
setting change," forbidden by the standing "never change repo settings" rule — but a **committed
workflow file** (`.github/workflows/codeql.yml`, "advanced setup") is a normal git push, not a
settings change, and is the correct path here.

**Primary recommendation:** Merge the astro security PR (#39) first alone, verify green, then
walk the remaining 16 PRs in dependency-safe batches (site-only, pipeline-only, dev-only) via
`gh pr merge --squash`, closing #18 with a written reason and gating #37 behind an
`eval_classifier.py` rerun. Add `.github/workflows/codeql.yml` (advanced setup, default queries,
`on: push, pull_request, schedule`) as a new committed file — this is the only DEPS-04/CodeQL path
that doesn't touch repo settings.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dependency version bumps | CI / Build tooling | — | package-lock.json / requirements.txt changes only, no app-code changes in most PRs |
| Security advisory remediation | CI / Build tooling | Pipeline (openai client) | astro/devalue/js-yaml/sharp/svgo fixes are build-time; openai client touches pipeline runtime behavior |
| CodeQL static analysis | CI / GitHub Actions | — | New workflow file, no runtime code path affected |
| Triage policy documentation | Docs (DEPLOYMENT.md) | — | Governance artifact, not code |

## Open PR Triage Table

All 17 open PRs as of 2026-09-23, oldest first. CI columns reflect the **last recorded run** (not re-run today).

| # | Package | From→To | Bump | Runtime/Dev | Area | CI (last run) | Age (days) | Conflicts w/ P35/36 | Risk | Recommendation |
|---|---------|---------|------|-------------|------|----------------|------------|----------------------|------|-----------------|
| 18 | typescript | 5.9.3→7.0.2 | major | dev | site | **FAIL** (build+validate, Cloudflare Pages) | 46 | No (dev-only) | High — major TS bump broke build | **Close** with reason "major bump breaks astro check/build; needs dedicated follow-up, not autonomous-run scope" |
| 26 | python-dotenv | 1.2.2→1.2.3 | patch | dev (env load) | pipeline | SUCCESS | 32 | No | Low | Merge |
| 27 | @astrojs/react | 6.0.2→6.0.4 | patch | runtime | site | SUCCESS | 32 | Low (touches React island glue) | Low | Merge |
| 28 | vitest | 4.1.10→4.1.11 | patch | dev | site | SUCCESS | 32 | No | Low | Merge |
| 30 | @types/react-dom | 19.2.4→19.2.5 | patch | dev | site | SUCCESS | 25 | No | Low | Merge |
| 31 | scipy | >=1.18.0,<2 → >=1.18.1,<2 | patch (range) | runtime | pipeline (composite index) | SUCCESS | 25 | No | Low | Merge |
| 33 | astro | 7.1.6→7.2.7 | minor | runtime | site | SUCCESS | 25 | **Superseded by #39** (7.2.8) | Low | **Close as superseded** once #39 merges |
| 34 | fast-uri | 3.1.5→3.1.7 | patch | dev | site | SUCCESS | 20 | No | Low | Merge |
| 35 | pydantic | 2.13.4→2.13.5 | patch | runtime | pipeline | SUCCESS | 18 | No | Low | Merge |
| 36 | lxml | 6.1.1→6.1.3 | patch | runtime | pipeline (CEAD HTML parse) | SUCCESS | 18 | No — CEAD scraper untouched by P35/36 | Low | Merge |
| 37 | openai | 2.53.0→3.7.0 | **major** | runtime | pipeline (classifier/clustering/eval) | **FAIL** (Pipeline pytest, at PR-open 2026-09-05) | 18 | Yes — Phase 34 just rewrote classifier.py/clustering.py error handling on openai 2.x semantics; P36 also touches classification path | High | **Gate on DEPS-03**: rerun `pytest`, then `eval_classifier.py --provider openrouter --model deepseek/deepseek-v4.1-flash --reasoning-extra-body '{"reasoning":{"enabled":false}}'` against golden set, diff against `34-AB-RESULTS.json` (commune_correct 44/47, family_correct 42/47, parse_errors 0). Merge only if identical; else close with reason and re-open post-v2.2 |
| 39 | astro | 7.1.6→7.2.8 | minor (security) | runtime | site | SUCCESS | 13 | Low | **Merge first, alone** — closes GHSA-26w7-cxv4-gfx2 (critical RCE) and GHSA-376h-93r7-7g6f (moderate authz bypass) | DEPS-01 |
| 40 | @vitest/mocker + vitest | multi | minor | dev | site | SUCCESS | 13 | No | Low | Merge |
| 41 | sharp | 0.35.3→0.35.4 | patch | runtime | site (image optim) | SUCCESS | 12 | No | Low | Merge |
| 42 | js-yaml | 4.3.1→4.3.2 | patch (security) | runtime | site | SUCCESS | 10 | No | Low | Merge — closes GHSA-2883-xcg3-v3hh (high, CPU DoS) |
| 43 | devalue | 5.9.0→5.9.2 | patch (security) | runtime | site | SUCCESS | 5 | No | Low | Merge — closes GHSA-9rgm-9g3h-6x36 (medium, DoS) |

**Note:** PR #43 and #42 each independently patch a security advisory that is also implicitly fixed
by newer astro/vite transitive resolution — verify after merging #39 whether `npm audit` still
flags them before merging separately, to avoid a redundant merge that produces no lockfile diff.

## DEPS-01 Findings — Astro Advisory (V-14)

- `npm audit --omit=dev --json` in `site/` (2026-09-23) confirms:
  - `astro` **critical**, CVSS 9.8, GHSA-26w7-cxv4-gfx2 ("Remote code execution through AVIF image
    optimization"), range `<=7.2.7`, `fixAvailable: astro@7.3.4` (non-major). `[VERIFIED: npm audit]`
  - `astro` **moderate**, GHSA-376h-93r7-7g6f (authz bypass from missing path-segment boundary
    check when stripping configured base), range `<=7.2.3`. `[VERIFIED: npm audit]`
  - PR #39 targets `astro@7.2.8`, which is `>7.2.7` and `>7.2.3` — **both ranges are closed** at
    7.2.8. A later 7.3.4 exists per `fixAvailable` but is not required to close either advisory.
    `[VERIFIED: npm audit range comparison]`
- Site currently pins `astro: "7.1.6"` in `site/package.json` (exact pin, no caret) — vulnerable.
  `[VERIFIED: site/package.json read]`
- CLAUDE.md's own Standard Stack table already documents this exact advisory and instructs
  "Do NOT drop back below v7.0.9" — merging #39 is consistent with existing project guidance, no
  new decision needed. `[CITED: CLAUDE.md Core Technologies table]`
- `@astrojs/react` peer requirement (`^6.0.2`, needs React 19.x) is unaffected by the astro 7.1→7.2
  bump — no major-version peer conflict. `[VERIFIED: site/package.json]`

**Action:** Merge #39 alone first (it's the security-critical, non-major PR). Then close #33
(7.1.6→7.2.7) as superseded — merging it after #39 would just be a no-op or conflict.

## DEPS-02 Findings — PR Backlog Count/Age (V-15)

- 17 open PRs, oldest 46 days (#18), target is ≤3 open / none >14 days. `[VERIFIED: gh pr list]`
- 12 of 17 PRs are patch-level, CI-green, low-risk, no code touched beyond lockfiles — safe to
  batch-merge quickly to hit the ≤3 target.
- After closing #18 (broken) and #33 (superseded) and merging #39 + the 12 low-risk patches, only
  #37 (openai major, gated) should remain open pending the eval rerun — bringing backlog to 1,
  well under the ≤3 target, assuming #37 resolves within the phase window.
- **29 Dependabot alerts** exist but most map to only 2 critical (astro, already alerts #21/#22) and
  a handful of high/medium (sharp, svgo, js-yaml, fast-uri, postcss, nanoid, yaml, esbuild) that are
  transitive and will very likely auto-close once the parent packages (astro, vitest tooling) are
  bumped via the PRs above — no separate remediation PRs appear needed beyond what's already open.
  `[VERIFIED: gh api dependabot/alerts]`

## DEPS-03 Findings — openai 3.x Gate (V-?)

- PR #37 bumps `openai` 2.53.0 → **3.7.0** (major). Used directly in three files:
  `pipeline/news/classifier.py`, `pipeline/news/clustering.py`, `pipeline/experiments/eval_classifier.py`
  — all import `OpenAI`, `AuthenticationError`, `RateLimitError`, `APIStatusError` from the `openai`
  package. `[VERIFIED: grep in repo]`
- The PR's own CI run (2026-09-05) shows **Pipeline pytest FAILURE** while Frontend/Lint/Cloudflare
  all succeeded — meaning the openai 3.x bump broke pipeline tests at PR-open time. This predates
  Phase 34's classifier rewrite (commit history shows Phase 34 work landed after 2026-09-05), so the
  failure must be **re-triaged fresh**, not assumed still valid or still broken.
  `[VERIFIED: gh pr view statusCheckRollup]`
- `34-AB-RESULTS.json` records the Phase 34 eval winner: `deepseek/deepseek-v4.1-flash`
  (OpenRouter, `reasoning.enabled: false`), commune_correct 44/47, family_correct 42/47,
  parse_errors 0, null_correct 3/3, spend $0.010017 for the run. `[VERIFIED: file read]`
- `pipeline/experiments/eval_classifier.py` (commit `b73ad96`, "model-parameterized eval runner")
  accepts `--provider`/`--model`/reasoning flags — reproducible re-run command:
  ```bash
  cd pipeline && python3 experiments/eval_classifier.py \
    --provider openrouter --model deepseek/deepseek-v4.1-flash \
    --reasoning-extra-body '{"reasoning":{"enabled":false}}'
  ```
  (confirm exact flag names against `--help` before executing; argparse defines `--model` at line 978).
- DEPS-03 gate is satisfiable: (1) `git checkout` PR #37's branch or `pip install openai==3.7.0`
  locally, (2) run `pytest pipeline/` — must pass, (3) run the eval command above, (4) diff results
  against `34-AB-RESULTS.json` fields (commune_correct, family_correct, parse_errors, null_correct)
  — merge only on exact match; otherwise close PR #37 with a written reason citing the metric delta.

## DEPS-04 Findings — Triage Policy & CodeQL Decision (V-15, V-28)

- `DEPLOYMENT.md` already has content referencing "Dependabot PRs #5, #7" (stale — those PR numbers
  are long since closed/merged; current backlog is #18–#43). This section needs updating as part of
  this phase's DEPLOYMENT.md edit, not left stale. `[VERIFIED: grep DEPLOYMENT.md]`
- **CodeQL is not currently enabled**: `gh api repos/.../code-scanning/alerts` → `404 "no analysis
  found"`. `[VERIFIED: gh api]`
- Two enablement paths exist:
  1. **Default setup** (Settings → Code security → CodeQL → "Set up" → Default) — this is a
     Settings/API toggle (`PATCH /repos/{owner}/{repo}/code-scanning/default-setup`), which the
     directive's "never change repo settings" rule forbids for an autonomous run.
  2. **Advanced setup** — commit `.github/workflows/codeql.yml` directly (a normal file addition via
     PR/push, using `github/codeql-action` reusable actions). This does **not** touch any repo
     Settings page or call the Settings API — it's indistinguishable from adding any other CI
     workflow file. This is free on public repos (this repo is public per the
     `news-cron-billing-outage` memory note — "repo PÚBLICO → minutos Actions gratis ilimitados").
     `[CITED: GitHub Docs — CodeQL code scanning, advanced setup]` `[ASSUMED: exact YAML syntax
     current as of query date — verify `github/codeql-action` version tag before writing the
     workflow, e.g. `github/codeql-action/init@v3`]`
- **Recommendation:** use path 2 (advanced setup, committed workflow file). This satisfies "enable
  CodeQL" without violating "never change repo settings." Record this reasoning verbatim in
  DEPLOYMENT.md as the DEPS-04 CodeQL decision.
- Suggested workflow shape (verify action versions before committing):
  ```yaml
  name: CodeQL
  on:
    push:
      branches: [master]
    pull_request:
      branches: [master]
    schedule:
      - cron: '0 6 * * 1'
  jobs:
    analyze:
      runs-on: ubuntu-latest
      permissions:
        security-events: write
        contents: read
      strategy:
        matrix:
          language: ['javascript-typescript', 'python']
      steps:
        - uses: actions/checkout@v4
        - uses: github/codeql-action/init@v3
          with:
            languages: ${{ matrix.language }}
        - uses: github/codeql-action/autobuild@v3
        - uses: github/codeql-action/analyze@v3
  ```
  `[ASSUMED: language matrix values and action tags — confirm current tags via
  github.com/github/codeql-action releases before committing]`

## Merge Mechanics & Ordering (Orchestrator Decision Needed)

- **`gh pr merge --squash` after CI green is functionally equivalent to a push to master.** The
  v2.2 directive's "push after green gate" language covers direct pushes from this run's own
  branches; it does not explicitly address merging *pre-existing Dependabot PRs*. **Flag this to
  the orchestrator as a decision point**: either (a) treat PR merges the same as any other
  green-gated push (proceed), or (b) require explicit owner sign-off per PR before merge, given the
  weekly manual triage policy default noted in the phase brief. Given the brief explicitly states
  "NO auto-merge" as an owner default, the safer reading is: **triage and stage recommendations in
  this phase's PLAN, but require an explicit human/owner merge action per PR** (or a single batch
  confirmation) rather than the agent calling `gh pr merge` unsupervised.
- **Order to avoid lockfile conflicts** (rebase chain — merge sequentially, letting Dependabot
  auto-rebase remaining PRs, or manually rebase before each merge):
  1. #39 (astro security fix) — merge alone first, let CI/Dependabot settle.
  2. Close #33 (superseded by #39).
  3. #42, #43 (remaining site security patches) — small, unlikely to conflict with #39's lockfile
     region.
  4. #27, #28, #30, #34, #40, #41 (remaining site patch/minor, low risk) — merge one at a time,
     re-running `npm audit`/CI between each if package-lock conflicts appear (all touch
     `site/package-lock.json`, so serialize rather than parallelize).
  5. #26, #31, #35, #36 (pipeline patches, separate `pipeline/requirements.txt` — no lockfile
     conflict with site PRs, can merge in parallel with the site batch).
  6. #37 (openai major) — last, gated on DEPS-03 eval rerun; merge only after all other
     `pipeline/requirements.txt` PRs are settled to avoid re-triggering the eval on a moving base.
  7. #18 — close with reason, do not merge.
- Each merge must be followed by the OneDrive-safe chained verification command (build+validate+
  vitest in one shell invocation) and `pytest` for pipeline-touching PRs, per the
  `onedrive-build-artifacts-desync` project memory note.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| `gh` CLI | PR triage, alerts API | Yes | — | — |
| `npm audit` | DEPS-01 verification | Yes (site/) | audit v2 | — |
| Node.js | build+validate+vitest chain | Yes | v22.23.2 (≥22.12 required) | — |
| Python 3.12+ | pytest, eval_classifier.py | Assumed present (CI uses it) | not probed locally this session | verify before executing DEPS-03 gate |
| `code-scanning` API scope | Confirming CodeQL absence | Partial — 404 confirms no analysis; alert-list call needs `admin:repo_hook` scope (403) | — | 404 on the analysis-list endpoint is sufficient evidence CodeQL isn't running; the 403 on a different endpoint doesn't block that conclusion |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `github/codeql-action@v3` and `languages: javascript-typescript, python` are current/correct as of today | DEPS-04 | Workflow could fail to init; low risk, easily fixed by checking latest release tag before commit |
| A2 | Repo remains public (per memory note) making CodeQL free | DEPS-04 | If repo were private, CodeQL default setup requires GitHub Advanced Security (paid) — verify `gh repo view --json visibility` before committing the workflow |
| A3 | Exact `eval_classifier.py` CLI flag names (`--reasoning-extra-body` etc.) match current argparse definition | DEPS-03 | Run `python3 experiments/eval_classifier.py --help` first; flags could differ from the historical run command embedded in the file's docstring (lines 16/20) |

**Verify A2 before writing the CodeQL workflow** (cheap, one `gh` call) — not yet checked this session.

## Open Questions

1. **Does PR #37's Pipeline pytest failure still reproduce today?**
   - What we know: it failed on 2026-09-05, before Phase 34's classifier/clustering rewrite.
   - What's unclear: whether Phase 34's changes fixed, worsened, or are orthogonal to the openai 3.x break.
   - Recommendation: rebase/re-run CI on #37 (or locally install openai==3.7.0 against current master) as the first DEPS-03 planning task, before deciding merge vs. close.

2. **Orchestrator merge authority** (see Merge Mechanics above) — needs an explicit decision recorded before the plan executes any `gh pr merge`.

## Sources

### Primary (HIGH confidence)
- `gh pr list --state open --json ...` — 17 PRs, full CI rollups (2026-09-23)
- `gh api repos/xenaquis/is-chile-safe/dependabot/alerts --paginate` — 29 open alerts
- `npm audit --omit=dev --json` in `site/` — astro/devalue/js-yaml vulnerability ranges
- Repo files read directly: `site/package.json`, `pipeline/requirements.txt`, `.nvmrc`,
  `pipeline/news/classifier.py`, `pipeline/experiments/eval_classifier.py`,
  `.planning/phases/34-news-classification-restore/34-AB-RESULTS.json`, `.planning/ROADMAP.md`,
  `.planning/REQUIREMENTS.md`, `DEPLOYMENT.md`, `CLAUDE.md`

### Secondary (MEDIUM confidence)
- GitHub Docs CodeQL advanced-vs-default setup distinction — from training knowledge, cross-checked
  against the observed 404 on code-scanning/alerts (consistent with "not enabled" either way)

### Tertiary (LOW confidence)
- None used without verification attempt

## Metadata

**Confidence breakdown:**
- PR triage table: HIGH — direct `gh` API evidence for every row
- DEPS-01 astro advisory: HIGH — `npm audit` ranges directly confirm PR #39 closes both CVEs
- DEPS-03 openai gate: MEDIUM — mechanism and gate are clear; actual metric reproduction not yet run (requires phase execution, not research)
- DEPS-04 CodeQL path: MEDIUM — mechanism (advanced setup avoids settings change) is sound reasoning from public docs; exact action version tags not re-verified live

**Research date:** 2026-09-23
**Valid until:** 7 days (PR backlog and CI states change daily; re-check `gh pr list` immediately before planning execution)

## Orchestrator note (2026-09-23)
34-AB-RESULTS.json metrics for the winner are commune 44/44, family 42/44 (44 labelled items), parse_errors 0/47 — not "44/47, 42/47". The DEPS-03 reproduction check compares those counts.
