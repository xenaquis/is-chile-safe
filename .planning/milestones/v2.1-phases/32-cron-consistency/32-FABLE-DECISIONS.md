# Phase 32 — Fable pre-planning decisions (BINDING on PLAN.md)

Taken inline by the Fable orchestrator on 2026-08-04, after reading RESEARCH.md **and
re-deriving its claims from the workflow files directly** (Operating Lesson 24: a report is
not evidence). These resolve RESEARCH.md's two Open Questions and three Assumptions before
planning starts, so they are not decided under pressure at close.

They will be transcribed into `.planning/STATE.md` § Fable Decisions as F-75..F-82.

---

## F-75 — Routing enforced from the directive, not `config.json`

`gsd-sdk query init.plan-phase 32` returned `planner_model: opus`, `checker_model: sonnet` —
the INVERSE of the directive. As in F-59, the directive wins: researcher `sonnet`, planner
`sonnet`, plan-checker `opus`, premortem `opus`, review `opus`, verification `opus`.
No CONTEXT.md is produced (`skip_discuss: true`; F-01 precedent). The UI-SPEC gate is SKIPPED —
this phase ships no UI surface.

## F-76 — CRON-01: `CF_DEPLOY_HOOK_URL` is REQUIRED, not optional. The "dry-run" skip is REMOVED everywhere.

**This is the phase's single most consequential decision and it contradicts RESEARCH.md's
recommendation**, which proposed keeping the soft skip and only upgrading it to `::warning::`.

Evidence that overrides it, read from the files this session:
`deploy-on-code.yml:5-10` states that **Cloudflare Pages automatic production builds are
DISABLED** and that "the Deploy Hook is the sole production build trigger." Therefore an empty
`CF_DEPLOY_HOOK_URL` does not mean "nothing to do" — it means **every commit from that point on
silently never reaches production**, indefinitely, while all three workflows report green. That
is precisely the "green run that did nothing" CRON-01 exists to abolish, and it is the highest-
severity instance of it in the repo: it takes down the whole site's freshness, not one pipeline.

Decision:
1. In **all three** hook-calling workflows (`news-pipeline.yml`, `cead-scraper.yml`,
   `deploy-on-code.yml`), an empty `CF_HOOK` is a **hard failure**: `::error::` + `exit 1`.
2. The `env.CF_HOOK != ''` clause is **deleted** from the `if:` of the deploy steps in
   news-pipeline and cead-scraper. Keeping it would re-create the silent skip one layer up:
   the step would be reported as *skipped* — a state that never fails the job and never alerts.
   The remaining condition is `steps.commit.outputs.changed == 'true'` only.
3. `deploy-on-code.yml`'s "dry-run mode" `exit 0` (L38-41) is replaced by the same hard failure,
   and its header comment (L1-13) is amended to say so — the comment currently documents the
   behaviour being removed, and stale prose next to a changed behaviour is exactly the drift
   Phase 31 was spent deleting.
4. The secret is live and verified in production (STATE.md go-live record), so this does not
   break any currently-working path. A fork without the secret gets a loud, correct failure.

Required secrets per workflow, all asserted by the shared guard as the FIRST step of the job:
- `news-pipeline.yml`: `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `CF_DEPLOY_HOOK_URL`
- `r2-archive.yml`: `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`
- `cead-scraper.yml`: `CF_DEPLOY_HOOK_URL`
- `deploy-on-code.yml`: `CF_DEPLOY_HOOK_URL`
- `ci.yml`: none

Guard shape: RESEARCH.md's **Option (b)**, a shared `.github/scripts/require-env.sh`, ACCEPTED —
because it is the only option that is directly executable locally with a blanked variable, which
is what directive gate amendment 2 substitutes for the live dry run. It must never print a
secret's value, only its name.

## F-77 — CRON-04: three per-pipeline labels, created BOTH once and idempotently at alert time

The dedup lookup today (`gh issue list --label pipeline-failure`) is not merely imprecise: with
one shared label across three workflows it will post an R2 failure as a **comment on the News
Pipeline's open issue**. The alert is then attributed to the wrong pipeline — actively worse
than no dedup.

Decision:
- Labels: `pipeline-failure-news`, `pipeline-failure-r2`, `pipeline-failure-cead`,
  `pipeline-failure-heartbeat`. The generic `pipeline-failure` label is **kept and additionally
  applied** to every alert, so a single "all pipeline alerts" view still exists; the dedup query
  is changed to filter on the SPECIFIC label only.
- They are created once during execution via `gh label create <name> --color e11d48 --description
  "…" --force`. This is repo *metadata*, additive and reversible — it is not a settings change
  and not a secret, so it does not fall under the directive's "no GitHub settings/secrets changes"
  rule. It is also not a `workflow_dispatch`.
- **AND** each alert step runs the same `gh label create … --force` for its own label immediately
  before `gh issue create`. `--force` is idempotent. Rationale: if someone later deletes a label,
  `gh issue create --label <missing>` fails, and the thing that fails is *the alert about a
  failure* — the one code path whose silent breakage is unrecoverable. Self-healing is worth one
  extra API call on a path that runs only when something is already broken.
- **No `|| true`, no `; echo`, no pipe** anywhere in these steps (Operating Lesson 8).

## F-78 — CRON-03: one canonical deploy-hook invocation, byte-identical in all three files

```
curl -X POST --fail --silent --show-error --retry 3 --retry-all-errors --max-time 60 "$CF_HOOK"
```

`--retry 3` (the majority policy; news-pipeline's 5 is the outlier and 3 retries against a
Cloudflare hook is ample), `--retry-all-errors` (news-pipeline's stricter behaviour wins — the
hook is a fire-and-forget POST whose 5xx/4xx responses are worth retrying), `--max-time 60`
added so a hung connection cannot burn the job's timeout budget. The compressed `-fsS` form in
`deploy-on-code.yml` is rewritten to the long form so the three lines are **textually identical**
and a grep can prove it. A plan gate must assert that identity mechanically, not by eyeball.

## F-79 — CRON-02: a new, dedicated `heartbeat.yml`, and the residual gap is DOCUMENTED, not hidden

RESEARCH.md's Pitfall 3 is correct and decisive: a heartbeat inside the workflow it watches
cannot detect that workflow's total silence. Folding it into `ci.yml` fails the same way — `ci.yml`
is `pull_request`-triggered and would never fire on a quiet repo, which is exactly the state
during an outage.

Decision: a new `.github/workflows/heartbeat.yml`, daily cron + `workflow_dispatch`, running
`.github/scripts/check-heartbeat.sh`, which asserts **all three** cadences and alerts through the
same issue mechanism under `pipeline-failure-heartbeat`. Thresholds, each justified from the
cadence read out of the yml (not invented):

| Cron | Cadence | Threshold | Evidence source |
|---|---|---|---|
| News | 6h (`0 */6 * * *`) | 3 days | `data/incidents/current.json`'s `generated` field — same source and same number as `freshness.mjs`, deliberately, so the two instruments cannot disagree |
| R2 archive | daily (`30 5 * * *`) | 4 days | `gh run list --workflow=r2-archive.yml` — the archive writes only to the R2 bucket and leaves NO artifact in `data/`, so no repo-local evidence exists |
| CEAD | quarterly (`0 3 1 1,4,7,10 *`) | 100 days | `git log -1 --format=%ci -- data/cead/` — the cron itself is *expected* to fail (403), so its run status is not the signal; the signal is whether a human ran the scraper locally |

**Accepted residual, recorded rather than papered over:** `heartbeat.yml`'s OWN silence is not
detected by anything inside this repo — a monitor cannot fully monitor itself, and closing that
would need an external service, which the ~$0 infrastructure constraint forbids. The exposure is
mitigated but NOT eliminated by layering: `freshness.mjs` (validator #16) re-derives the news
signal from `data/` on every local `npm run validate` and in every CI run, so news staleness is
caught even with both crons dead. **R2 archive staleness is the one signal that depends on
`heartbeat.yml` being alive.** This sentence must survive into STATE.md; a phase about
self-diagnosing crons that quietly implies total coverage would be its own worst finding.

## F-80 — CRON-07's "audit after clustering" premise is MOOT and must be stated, not silently satisfied

CRON-07 requires the schedule surface be audited *after Phase 28 wired clustering into the news
pipeline*. Phase 26 returned NO-GO and Phase 28 shipped faceting-only, so **no clustering was ever
wired into `news-pipeline.yml`** and there is no cost/latency change to account for. The cron's
shape is one `python pipeline/scrape_news.py` invocation with `timeout-minutes: 30`, unchanged.
The deliverable table must say this explicitly. Otherwise a future reader sees "audited for
clustering impact: OK" and reasonably infers clustering exists.

## F-81 — Falsifiability: every guard ships with a two-direction proof, wired into pytest

The rule this run has re-learned in every phase since 27: an assertion that cannot fire reads as
coverage and is worse than none. Each new script (`require-env.sh`, `check-heartbeat.sh`, the
push-retry logic) ships with:
- the explicit list of inputs that MUST make it exit non-zero, and
- the explicit list of legitimate inputs that must leave it silent (Operating Lesson 26 —
  widening a gate on one axis routinely narrows it on another),
- both encoded in `pipeline/tests/test_workflow_guards.py`, which shells out to the real scripts
  with fixtures. It runs in CI's existing pipeline job automatically; a documented manual command
  depends on someone remembering.

Consequence, stated up front so it is not mistaken for a regression at close: **the pytest
baseline moves from 344.** The new total is recorded in STATE.md and the directive's RUN STATUS at
close. The `1 skipped / 1 xfailed` counts must stay exactly 1 and 1 (F-08: the xfail is Phase 26's
deliberate quarantine).

**No new frontend validator.** The close bar stays **16/16** (F-64), the "16 validators" figure
does not cascade (F-21), and F-73's accepted debt is not disturbed.

## F-82 — Verification of the workflow YAML: `actionlint` runs, locally, pinned — or the phase says it did not

`actionlint` is NOT installed on this machine and `ci.yml` only runs it on `pull_request`
(this run pushes straight to master, so that job would never fire for these changes). Directive
gate amendment 2 names actionlint explicitly as half of CRON-01's substitute verification, so
"CI will catch it" is not available here.

Decision, in order: (1) try `go install`; (2) if Go is absent, download the pinned actionlint
release binary for Windows into the scratchpad — a read-only fetch of a public release, no repo
or settings mutation; (3) if BOTH fail, the phase does **not** claim actionlint coverage — it
records the gap in STATE.md § Blockers and closes on the YAML-parse + local shell proofs alone.
Silently dropping a named gate is the failure mode; a recorded gap is not.

**RESOLVED 2026-08-04 by the orchestrator, before planning — branch (2) taken and PROVEN in both
directions. The plan must USE this exact invocation; it is not optional and it is not a guess.**

Go is absent (`which go` → not found), so both binaries were downloaded from their official
GitHub releases into the scratchpad, outside the repo:

- `actionlint` **v1.7.12** — SHA-256 verified against the release's own
  `actionlint_1.7.12_checksums.txt` (`sha256sum -c` → `OK`).
- `shellcheck` **v0.11.0** — added deliberately: without it actionlint does NOT lint the bash
  inside `run:` blocks, and this phase's entire payload IS bash. Linting the YAML while ignoring
  the shell would have been an instrument aimed away from the work.

Canonical invocation (`SC` = scratchpad path to `shellcheck.exe`):

```
actionlint.exe -no-color -oneline -shellcheck "$SC" .github/workflows/*.yml
```

Note `-color=never` is NOT a valid flag (it exits 2 on a usage error, which a careless gate would
misread as "findings"); the correct flag is `-no-color`.

Two-direction proof, executed:
- **Silent on correct input:** the five current workflow files produce **zero findings, exit 0** —
  so this is a real baseline and any post-edit finding is genuinely introduced by this phase.
- **Fires on bad input:** a synthetic workflow with an unquoted variable and an unused assignment
  returned two `SC2086`/`SC2034` findings and **exit 1**.

Both binaries live in the scratchpad only. Nothing is installed into the repo or the user's PATH,
and `.gitignore` needs no change because nothing lands under the repo tree.

## Scope fences

- **IN:** the five existing workflow files, one new `heartbeat.yml`, new `.github/scripts/*.sh`,
  one new pytest file, the CRON-07 table (in `.planning/` and/or `DEPLOYMENT.md`), and the
  `gh label create` calls.
- **OUT (Phase 33, do not touch):** `permissions:` blocks, SHA-pinning of third-party actions,
  `dependabot.yml`, `zizmor`, scraping courtesy delays. Phase 32 must not pre-empt them.
- **OUT:** `data/` generated artifacts stay read-only. No `workflow_dispatch` is triggered. No
  secret is read, written, or printed. `pipeline/` Python is not modified except for the NEW test
  file — in particular `archive_r2.py` does NOT gain a `data/` heartbeat marker (F-79 chose the
  `gh run list` evidence source precisely to avoid that write).
