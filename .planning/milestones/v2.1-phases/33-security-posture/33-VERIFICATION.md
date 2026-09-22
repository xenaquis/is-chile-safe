---
phase: 33-security-posture
verified: 2026-08-05T00:00:00Z
status: human_needed
score: 3/5 success criteria fully verified (SC1, SC2, SC5); SC3 and SC4 PARTIAL pending one observation each
overrides_applied: 0
human_verification:
  - test: "Push the phase commits to origin/master, then wait for (or trigger) Dependabot and check that at least one dependabot PR is opened."
    expected: "At least one PR authored by dependabot[bot] against github-actions, pip, or npm. Settling command: `gh pr list --author 'app/dependabot' --state all --limit 10`, or `gh api repos/xenaquis/is-chile-safe/dependabot/alerts` is NOT the right check — the criterion is a PR, not an alert. Also confirm the config was accepted: Insights > Dependency graph > Dependabot must list three ecosystems with a last-checked timestamp, i.e. no 'dependabot.yml is invalid' banner."
    why_human: "Dependabot only reads .github/dependabot.yml once it is on the default branch of origin. Nothing has been pushed, so no PR can exist and the config has never been parsed by GitHub."
  - test: "After pushing, dispatch ci.yml on master (`gh workflow run ci.yml --ref master`) and read the lint-workflows job log."
    expected: "Job conclusion success AND the log contains zizmor's own version banner (e.g. `zizmor 1.10.0`) plus a findings summary — proving the step actually executed, not that it was skipped. This is also the only evidence that assumption A1 (pipx preinstalled on ubuntu-latest) holds on a real runner; if the `command -v pipx` guard step fails, F-112/A1 fallback applies. Then replace the PENDING paragraph in DEPLOYMENT.md (§ Zizmor CI Verification) with the run URL and the banner line."
    why_human: "ci.yml triggers on pull_request + workflow_dispatch only (F-95, deliberate). The zizmor step has never executed on a runner. A green job with a skipped step would look identical from the code."
gaps: []
deferred: []
---

# Phase 33: Security Posture — Verification Report

**Phase Goal:** Least-privilege Actions defaults, every third-party action pinned with a documented decision, automated dependency updates, and an Actions-specific static scanner running in CI — with no shipped frontend footprint.
**Verified:** 2026-08-05
**Status:** human_needed — 3/5 success criteria fully verified in code + live settings; **2 criteria (SC3, SC4) are PARTIAL and each names exactly one outstanding observation.**
**Re-verification:** No — initial verification.

## Verdict up front

The code is good. This is not a phase where the artifacts are stubs — every gate I attacked was substantive, canary-armed, and wired into a job that runs. The two open items are not code defects; they are **observation events that structurally could not happen before push**, and the project's own DEPLOYMENT.md already says so in writing rather than claiming them (F-124). That honesty is the reason this report can be short about waves 1–3 and precise about the two gaps.

**I am not softening either one to close the milestone.** SC3 and SC4 both say something happens *in the world*, not *in the tree*. Neither has happened.

## Success Criteria

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Repo default read-only + every job has its own minimal `permissions:` | **MET** | Live API this session: `gh api repos/xenaquis/is-chile-safe/actions/permissions/workflow` → `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}`. All **8/8** jobs carry a job-level block: `cead-scraper.yml:29` (contents/issues: write), `ci.yml:16,41,62` (contents: read ×3), `deploy-on-code.yml:40`, `heartbeat.yml:39` (actions/contents read + issues write), `news-pipeline.yml:16`, `r2-archive.yml:16`. No job relies on the repo default alone. |
| 2 | Every third-party action SHA-pinned + version comment + documented per-action decision | **MET** | `grep -rn "uses:" .github/workflows/` → exactly **13** refs, every one a 40-hex SHA with `# vN.N.N` (e.g. `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`). Count matches F-114's correction of F-103/F-104 (13, not 11) and the `EXPECTED_MIN_COUNT=13` coverage floor in `check-sha-pins.sh:88`. Decision record for all three reference classes at `DEPLOYMENT.md:270-309` — (a) `uses:` refs → SHA-pin, refreshed via dependabot; (b) actionlint/shellcheck binaries → already SHA-256-pinned by Phase 32, recorded not re-made; (c) zizmor → version-pin `1.10.0` ephemeral, with the honest FM-16 note that **nothing will ever bump it automatically** and it must be re-evaluated each milestone close. |
| 3 | `dependabot.yml` covers github-actions/pip/npm **and a dependabot PR can be observed being opened** | **PARTIAL — pending observation** | Config half is MET: `.github/dependabot.yml` has all three ecosystems with correct directories (`/`, `/pipeline`, `/site`), weekly, `open-pull-requests-limit: 5`, github-actions grouped per F-115. Observation half is **not met and cannot be**: nothing has been pushed, so GitHub has never parsed this file. See judgement below. |
| 4 | zizmor **runs in CI** via pipx/uvx alongside actionlint, every finding triaged | **PARTIAL — pending observation** | Step exists and is correct: `ci.yml:87-91`, `pipx run zizmor==1.10.0 --persona=regular .github/workflows/`, preceded by a hard `command -v pipx` guard (`ci.yml:84`) that fails the job rather than skipping, and sitting in the same `lint-workflows` job as `lint-workflows.sh` and `check-sha-pins.sh`. Not in `pipeline/requirements.txt` (verified). Triage is complete: 8 artipacked findings → 6 fixed with `persist-credentials: false` (`ci.yml:21,46,67`, `deploy-on-code.yml:55`, `heartbeat.yml:51`, `r2-archive.yml:23`), 2 explicitly accepted with inline `# zizmor: ignore[artipacked]` + reason (`cead-scraper.yml:47-48`, `news-pipeline.yml:35-36` — both jobs push via `push-with-rebase.sh` and need the credential). **The step has never executed on a runner.** See judgement below. |
| 5 | Manual confirmation: secret scanning + push protection on, no key in logs/artifacts, courtesy delays adequate, clustering added no fetch volume | **MET** | Re-queried live this session, not taken from the summary: `secret_scanning.status: enabled`, `secret_scanning_push_protection.status: enabled`, `visibility: public`. Log hygiene enforced by `check-secret-hygiene.sh` — four checks, each with an individually-asserted canary (`fixtures/secret-hygiene-canary/`), aborting loudly if any shape fails to fire. Delays: CEAD 2.5 s (`scrape_cead.py:305,365`), full-text 1.5 s (`news/fulltext.py:39`), R2 1.5 s (`archive_r2.py:568`), and the new inter-feed 1.5 s (`scrape_news.py:238`) applied `if i > 0` so it never sleeps before the first feed. Clustering: `grep -c clustering pipeline/scrape_news.py` → **0** — Phase 26 was a NO-GO and `clustering.py` has no production caller, so fetch volume against upstreams is provably unchanged. |

## Requirements Coverage

| Req | Verdict | Note |
|-----|---------|------|
| SEC-01 | **MET** | Both halves verified live (see SC1). `REQUIREMENTS.md:109` still shows `- [ ]` unchecked — a bookkeeping lag, not a substantive gap; it should be ticked. |
| SEC-02 | **MET** | 13/13 pinned + three-class decision record. Note the honest scope fact recorded in F-103/F-114: **there is not one genuinely third-party `uses:` in this repo** — all 13 are `actions/*`. The requirement is satisfied against the reference classes that actually exist, and the roadmap's example (`rhysd/actionlint@v1`) was already removed by F-95/H-03. |
| SEC-03 | **MET as written** | SEC-03's own text stops at "a `.github/dependabot.yml` is added covering the three ecosystems" — no observation clause. That is satisfied. The observation clause lives only in success criterion 3, which is why SEC-03 and SC3 diverge here. |
| SEC-04 | **PARTIAL** | Wiring, pinning, non-inclusion in requirements.txt, and full finding triage are all MET. "Runs in CI" is unobserved. DEPLOYMENT.md:341 states it in the project's own words: *"Until that follow-up lands, SEC-04's success criterion 4 is not yet met."* |
| SEC-05 | **MET** | Settings re-verified by me this session; 0 open secret-scanning alerts cited from the correct API (HI-03 fixed the earlier `open_issues_count` mis-citation — that was a real evidence defect and it was properly corrected). |
| SEC-06 | **MET** | Delays present on every upstream path and the clustering claim is proven by absence of import, not by absence of evidence. |

## The two judgements you asked for

### 1. SEC-03 / criterion 3 — PARTIAL-pending-observation, not MET

The criterion has two conjuncts and deliberately uses the words *"can be observed being opened"*. Conjunct one is done. Conjunct two is not merely unobserved — it is currently **impossible**, because Dependabot reads `dependabot.yml` from the default branch of `origin` and this file has never left the working tree. There is also a real, non-theatrical risk being deferred here: a `dependabot.yml` that GitHub rejects as invalid (bad `directory`, unresolvable manifest) fails **silently from the repo's point of view** — the file sits there looking correct and no PR ever comes. `/pipeline` and `/site` must each contain the manifest Dependabot expects; that is plausible from the tree but has never been confirmed by GitHub's own parser.

**What settles it:** push, then `gh pr list --author 'app/dependabot' --state all` returning ≥1 PR — *and* the repo's Dependabot page (Insights > Dependency graph > Dependabot) showing all three ecosystems with a last-checked timestamp and no invalid-config banner. The second half matters more than the first, because it is what distinguishes "no PR yet, nothing to update" from "no PR ever, config rejected".

### 2. SEC-04 / criterion 4 — PARTIAL. The criterion requires the observed run.

Criterion 4's verb is **"runs in CI"**. Not "is wired into CI", not "would run". I read the step and it is correct — pinned version, correct persona, correct path argument, `GH_TOKEN` supplied so the four token-requiring audits (`impostor-commit`, `ref-confusion`, `known-vulnerable-actions`, `stale-action-refs`) are not silently skipped, and a preceding `command -v pipx ||` guard that *exits 1* rather than degrading. That is about as good as an unexecuted step gets.

It is still unexecuted. `ci.yml` is `pull_request` + `workflow_dispatch` only (F-95, and that choice is well-reasoned — a `push` trigger would manufacture recurring red CI from data-age freshness failures). The one prior real run cited in DEPLOYMENT.md (`30975549062`) predates the zizmor step and its log contains no zizmor banner; DEPLOYMENT.md says exactly that and refuses to count it. Good.

Given this project's named recurring failure mode — *a gate that was never observed to fire* — and given that this very phase's F-125 review found **two HIGH findings where a countermeasure printed a confident green over shapes it did not actually cover**, treating an unexecuted step as MET would be repeating the phase's own central lesson at the phase's own close. The local `uvx` pass is a weaker instrument by four audits (ME-01, correctly documented). The pipx assumption A1 is cited from GitHub's image manifest, never executed.

**Verdict: PARTIAL.** **What settles it:** one `workflow_dispatch` of `ci.yml` on `master` after push, with the `lint-workflows` log showing zizmor's own version banner. One command, one log line.

## Accepted-rather-fixed items — are the acceptances reasoned?

| Item | Acceptance | Judgement |
|------|-----------|-----------|
| **ME-02** — courtesy-delay constant imported from `news/fulltext.py`, putting `requests`/`trafilatura`/`tenacity` on the news-cron import path to read one float | Accepted; failure mode is a loud `ModuleNotFoundError` before any feed is fetched (red job + alert issue) | **Reasoned.** The trade is stated, the symptom is named and observable, and F-108's one-constant rule is genuinely worth more than the decoupling. Fails loud, not silent. |
| **RR-L2** — comment-skip in both gates blind to a `#`-leading line inside a heredoc body in a `run:` block | Accepted; needs a YAML/shell parser to distinguish, and narrowing the skip is what produced the F-126 regression. No heredoc exists in any `run:` body today | **Reasoned, and the strongest of the three.** It names the exact contrived precondition, states that no instance exists, notes GitHub's value-masking as residual defence, and cites a real regression caused by the alternative. This is what an accepted gap should look like. |
| **RR-L3** — the courtesy-delay tests import `REQUEST_DELAY` from `fulltext.py`, deepening ME-02's coupling | Accepted as marginal | **Reasoned but thin.** It is a genuine second-order coupling and the tests would fail loudly too, so the residual risk is small. Fine to accept; not worth reopening. |

I checked one thing the acceptances imply and it holds: `check-secret-hygiene.sh` excludes itself from every scanning grep and words its own `::error::` strings so they don't contain the hunted literals (FM-01) — the self-flag defect the comment-skip discussion could easily have reintroduced is not present.

## Anti-patterns

No `TBD` / `FIXME` / `XXX` in any file this phase touched (`.github/workflows/`, `.github/scripts/`, `pipeline/scrape_news.py`, `.github/dependabot.yml`). The one PENDING marker (DEPLOYMENT.md § Zizmor CI Verification) is a deliberate, fully-specified, owner-assigned follow-up with the exact command to discharge it — that is the correct shape for an honest open item, and it is why this report can trust the rest of the document.

## Milestone v2.1 close recommendation

**Do not close the milestone yet.** Close it after the two observations, which together are: push → `gh workflow run ci.yml --ref master` → read the log for the zizmor banner → check `gh pr list --author 'app/dependabot'` and the Dependabot config page. That is one push and two reads. Every other Phase 33 obligation is discharged in the tree and confirmed against live repo settings.

If either observation comes back wrong (pipx absent on the runner, or dependabot.yml rejected as invalid), that is a real finding this verification is deliberately leaving room for rather than assuming away.

---

_Verified: 2026-08-05_
_Verifier: Claude (gsd-verifier)_
