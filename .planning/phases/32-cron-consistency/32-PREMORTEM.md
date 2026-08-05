# Phase 32 — PREMORTEM

**Frame:** It is 2026-08-25. Phase 32 shipped to the live repo. It failed.
**Method:** every claim below was re-derived against the real tree — the five real workflow
files, the real `pipeline/tests` baseline, the live (read-only) `gh` API, and the plans'
proposed YAML extracted into a scratchpad and linted with the pinned
`actionlint v1.7.12` + `shellcheck v0.11.0` from F-82. Nothing here is reasoned in the abstract.

**Baselines re-measured this session (all confirmed as the plans state them):**

| Fact | Measured |
|---|---|
| `cd pipeline && python -m pytest tests/ -q` | `344 passed, 1 skipped, 1 xfailed` ✅ |
| actionlint+shellcheck on the 5 real workflows | zero findings, exit 0 ✅ |
| actionlint+shellcheck on **all five proposed** workflow YAMLs + `heartbeat.yml` | zero findings, exit 0 ✅ |
| shellcheck on both proposed `.sh` scripts | zero findings, exit 0 ✅ |
| CRON-03 identity gate (`grep -h "curl -X POST" … \| sort -u`) | exactly **1** distinct line ✅ |
| `check-heartbeat.sh` boundary / empty / unparseable proofs | reproduce exactly as documented ✅ |
| Deletions-only diff, real vs proposed, all four files | **no accidental deletions** (see §13) ✅ |
| `git log -1 --format=%cI -- data/cead/` | `2026-06-19T17:24:23-04:00` (46 d) |
| `gh run list --workflow=r2-archive.yml` latest | `2026-08-04T07:58:30Z`, `success` |
| Open issues labelled `pipeline-failure` | **#2 — "[pipeline] CEAD Scraper failed on 2026-07-03", OPEN** |
| Repo `.git` pack size | 11.6 MiB → `fetch-depth: 0` is free, not a finding |

---

## 1. [CRITICAL] `heartbeat.yml` lacks `actions: read`, so it fails on its very first run and alerts about itself, daily, forever

**Scenario.** 2026-08-06 12:00 UTC. `heartbeat.yml` fires for the first time. Step 1 runs
`gh run list --workflow=r2-archive.yml …`. The workflow declares:

```yaml
permissions:
  contents: read
  issues: write
```

Declaring **any** scope sets every unlisted scope to `none`. `gh run list` calls
`GET /repos/{owner}/{repo}/actions/runs`, which requires the **Actions: read** permission.
`GITHUB_TOKEN` has `actions: none` → 403. Under the default `bash -e` shell, the failing
command substitution kills the step. `if: failure()` fires, creates
`[pipeline] Heartbeat detected a stalled cron on 2026-08-06`. Every subsequent day appends a
comment. **The first thing the new monitoring system ever says is a lie about a cron that is
in fact healthy** — and the issue body ("check which step failed") points a maintainer at R2,
which is fine.

**Evidence.** The permissions block is on `32-03-PLAN.md:111-113`. The plan's own "Verified
during planning" bullet ran `gh run list` **from this machine using the maintainer's PAT**,
which has full `repo` scope — that proves nothing about the workflow token, and the plan
treats it as if it did. I could not falsify this without a live run (forbidden), and the
repo being public does *not* settle it: anonymous access to that endpoint returns 200 (I
verified: `curl …/actions/runs?per_page=1` → `200`), but an authenticated installation token
with `actions: none` is evaluated against its installation permissions, not against public
visibility.

**Severity: CRITICAL.** Not because it breaks production, but because it burns the alert
channel on day one — which is the entire deliverable of CRON-02/CRON-04.

**Amendment (mandatory, free, zero downside):** in `32-03-PLAN.md`'s `heartbeat.yml`, change

```yaml
permissions:
  contents: read
  issues: write
```
to
```yaml
permissions:
  actions: read      # required by `gh run list` (GET /repos/…/actions/runs)
  contents: read
  issues: write
```

This is **not** a Phase-33 scope violation: F-82's scope fence puts `permissions:` blocks of
the *existing* files out of scope; `heartbeat.yml` is a new file whose permissions block is
authored by this phase by construction.

**Proof the amendment works:** cannot be proven offline. Add to 32-03 Task 1 a mandatory
post-merge step: `gh workflow run heartbeat.yml` is forbidden by the directive, so instead
require the *first scheduled run's* conclusion be checked at phase close
(`gh run list --workflow=heartbeat.yml --json conclusion --limit 1`) and recorded in
32-03-SUMMARY.md. If the phase closes before that run exists, STATE.md must record
"heartbeat.yml's first live run unverified" as an open item — do not claim CRON-02 closed.

---

## 2. [CRITICAL] The actionlint verify gate silently disables shellcheck and exits 0 — the phase's only YAML/shell instrument cannot fail

**Scenario.** The executor runs in a *new* session with a *new* scratchpad. The verify block
in `32-02-PLAN.md:508` is:

```
SCRATCH_SHELLCHECK="$(ls -1 /c/Users/*/AppData/Local/Temp/claude/*/*/scratchpad/shellcheck.exe 2>/dev/null | head -1)"
"$SCRATCH_ACTIONLINT" -no-color -oneline -shellcheck "$SCRATCH_SHELLCHECK" …; test $? -eq 0
```

The temp dir gets cleaned between sessions, or the two globs resolve into *different* session
directories. `SCRATCH_SHELLCHECK` becomes an empty string or a path that does not exist.

**Measured, this session, against the real pinned binaries:**

```
$ actionlint.exe -no-color -oneline -shellcheck "<real>/shellcheck.exe" bad.yml
bad.yml:7:9: … SC2034:warning … UNUSED appears unused …
bad.yml:7:9: … SC2086:info … Double quote to prevent globbing …
exit=1
$ actionlint.exe -no-color -oneline -shellcheck "" bad.yml
exit=0            # <-- shellcheck SILENTLY DISABLED
$ actionlint.exe -no-color -oneline -shellcheck "<nonexistent>/nope.exe" bad.yml
exit=0            # <-- ALSO silently disabled, no warning, no error
```

So the gate passes green with **every line of bash in this phase unlinted**, and the phase's
entire payload IS bash. F-82 spent its whole rationale on "without shellcheck actionlint does
NOT lint the bash inside `run:` blocks" and then wired a gate that can lose shellcheck
without saying so.

**Severity: CRITICAL** (this is the exact "gate that cannot fail" pattern the directive names).

**Amendment.** Replace every `<automated>` verify in 32-02 Task 1, 32-02 Task 2, and 32-03
Task 1 with this shape (resolve → assert executables → self-test the instrument on a known-bad
fixture → then lint for real):

```bash
AL="$(ls -1 /c/Users/*/AppData/Local/Temp/claude/*/*/scratchpad/actionlint.exe 2>/dev/null | head -1)"
SH="$(ls -1 /c/Users/*/AppData/Local/Temp/claude/*/*/scratchpad/shellcheck.exe 2>/dev/null | head -1)"
[ -x "$AL" ] || { echo "FATAL: actionlint not resolved"; exit 1; }
[ -x "$SH" ] || { echo "FATAL: shellcheck not resolved — actionlint would silently skip all run: bash"; exit 1; }
# instrument self-test: the tool MUST fire on known-bad input, or it is not measuring anything
mkdir -p /tmp/al-canary/.github/workflows
printf 'name: c\non: workflow_dispatch\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: |\n          UNUSED=x\n          FILE="a b"\n          cat $FILE\n' > /tmp/al-canary/.github/workflows/c.yml
( cd /tmp/al-canary && "$AL" -no-color -oneline -shellcheck "$SH" .github/workflows/c.yml ) && { echo "FATAL: canary did not fire — shellcheck is not running"; exit 1; }
# real lint
"$AL" -no-color -oneline -shellcheck "$SH" .github/workflows/*.yml
```

**Proof:** the canary block above was executed this session — it produced SC2034+SC2086 and
exit 1 with the real binary, and the `[ -x "$SH" ]` guard catches both silent-disable paths I
reproduced above.

---

## 3. [HIGH] The 15 new pytest tests do not run on this machine, and 8 of them would pass **vacuously** — including the secret-leak test

**Scenario.** The executor finishes 32-01 Task 2 and runs
`cd pipeline && python -m pytest tests/ -q`. The plan mandates
`subprocess.run(["bash", str(path), *args], …)`.

**Measured, this machine, both shells:**

```
# from PowerShell
shutil.which('bash')  -> C:\WINDOWS\system32\bash.EXE          (the WSL launcher)
subprocess.run(['bash','-c','echo hi']) -> rc=1, stdout='', stderr=
  "<3>WSL (…) ERROR: CreateProcessCommon:800: execvpe(/bin/bash) failed: No such file or directory"

# from git-bash-launched python — same failure
```
`C:\Program Files\Git\bin\bash.exe` **does** work (`rc=0, stdout='ok\n1785454647\n'`, and
`date -u -d "5 days ago"` works there too), but bare `"bash"` never resolves to it.

Consequences, exactly as the plan specifies the tests:

- Every test asserting **exit 1** passes for the wrong reason — WSL returns 1.
  That is `test_fails_on_all_blank`, `test_fails_on_unset_var`, `test_require_env_all_blank`,
  `test_fails_on_empty_timestamp`, `test_fails_on_unparseable_timestamp`,
  `test_r2_fails_beyond_threshold`, `test_cead_fails_beyond_threshold`.
- **`test_never_prints_secret_value` passes vacuously** — empty stdout/stderr trivially
  contains no secret. The single security assertion in the phase is the most vacuous one.
- Every exit-0 and exit-2 test fails, so the run is visibly red and the `359 passed` gate
  blocks. The realistic executor response under autonomy is to "fix" it by skipping on
  Windows — which then breaks the `359 passed / 1 skipped / 1 xfailed` count and invites
  adjusting the expected number to match, the thing 32-03 Task 2 explicitly forbids.

CI (ubuntu) is fine, so real coverage does exist there — but it is invisible to the executor,
and the executor is the only reader before this ships.

**Severity: HIGH** (blocks execution; corrupts the F-81 falsifiability claim).

**Amendment.** In 32-01 Task 2's `<action>`, replace "calls
`subprocess.run(["bash", str(path), …])`" with:

```python
import os, shutil, subprocess
from pathlib import Path

def _find_bash() -> str:
    if os.name == "nt":
        for c in (r"C:\Program Files\Git\bin\bash.exe",
                  r"C:\Program Files\Git\usr\bin\bash.exe"):
            if Path(c).exists():
                return c
    b = shutil.which("bash")
    if not b:
        raise RuntimeError("no usable bash found")
    return b

BASH = _find_bash()
```

and add a **16th test that makes every other test non-vacuous**:

```python
def test_bash_interpreter_is_usable():
    """Canary: if bash is broken (e.g. Windows resolves it to the WSL stub, which
    returns rc=1 with empty output), every exit-1 assertion below would pass for the
    wrong reason. This test fails first and loudly."""
    r = subprocess.run([BASH, "-c", "echo ok"], capture_output=True, text=True, timeout=10)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ok"
    assert "WSL" not in r.stderr
```

Additionally: **no negative test may assert on the exit code alone.** Every exit-1 test must
also assert the expected `::error::…` substring is present in stdout. That is what actually
kills the vacuity, independent of which bash is found.

Cascade: the pytest close bar moves **344 → 360**, not 359. Update
`32-01-PLAN.md` must_haves, `<done>`, `<verification>`, `<success_criteria>`, and
`32-03-PLAN.md` Task 2 step 3 and `<verification>` consistently, or the phase closes on a
number nobody can reproduce.

---

## 4. [HIGH] Making `CF_DEPLOY_HOOK_URL` a first-step hard gate converts a deploy-only outage into a total news-data outage

**Scenario.** 2026-09-10, the Cloudflare deploy hook is rotated (or the secret is
accidentally cleared during an unrelated settings edit). Today: news-pipeline still scrapes,
classifies, commits, and pushes `data/incidents/current.json`; only the deploy step skips —
the site is stale but the corpus keeps growing and one later successful deploy publishes
everything. After Phase 32: the **first step** of the job (`32-02-PLAN.md:133-138`) exits 1.
No scrape. No commit. No data. Four times a day, forever, each run adding a comment to the
same alert issue.

So a single missing secret now takes down **both** publication *and* collection, and the
corpus develops a permanent hole no later run can backfill (RSS feeds age out).

**Evidence.** `32-02-PLAN.md:133-138` places `CF_DEPLOY_HOOK_URL` in the same first-step guard
as the API keys. F-76 §"Required secrets per workflow, all asserted by the shared guard as the
FIRST step of the job" mandates it.

**Severity: HIGH.** The failure is at least *loud* (that is the phase's win), but the blast
radius is wider than F-76 accounted for — F-76 reasoned only about "green run that did
nothing", not about coupling collection to publication.

**Amendment (strictly dominates; keeps every F-76 property):** split the guard in
`news-pipeline.yml` and `cead-scraper.yml` into two steps —

```yaml
      - name: Guard required secrets
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: bash .github/scripts/require-env.sh OPENROUTER_API_KEY DEEPSEEK_API_KEY

      # …scrape + commit steps…

      # CRON-01 (F-76): still a HARD failure, not a skip — but placed AFTER the commit
      # so a rotated deploy hook cannot also stop data collection. The job still fails
      # and still alerts; the corpus survives.
      - name: Guard deploy hook
        run: bash .github/scripts/require-env.sh CF_HOOK
```

Note this also fixes a smaller latent bug: the plan's guard checks a **step-level alias**
`CF_DEPLOY_HOOK_URL` while the curl consumes the **job-level** `CF_HOOK`. Two names for one
value is a rename waiting to decouple the assertion from the thing asserted. Guarding
`CF_HOOK` (which is already in scope from the job `env:`) removes the alias and the extra
`env:` block entirely.

**Proof:** `bash .github/scripts/require-env.sh CF_HOOK` with `CF_HOOK=""` exits 1 and prints
`::error::CF_HOOK is not set …` — same two-direction proof as Wave 1, one extra pytest case.
Add a grep gate: `grep -c 'require-env.sh CF_HOOK' .github/workflows/news-pipeline.yml` ≥ 1
and `grep -c 'CF_DEPLOY_HOOK_URL:' .github/workflows/news-pipeline.yml` == 0.

*If the planner rejects this and keeps F-76 literally:* then say so explicitly in the plan as
**"accepted risk: a cleared deploy-hook secret halts news collection, not just publication;
accepted because the failure is loud within 6h and the secret is not rotated on any schedule."*
Do not leave it implicit.

---

## 5. [HIGH] The heartbeat does not watch the 6-hour cron at all, and its stated compensating control does not exist

**Scenario.** 2026-09-01, the OpenRouter key expires mid-quarter and `scrape_news.py` starts
raising. The news alert fires — good. But now consider the case CRON-02 was actually written
for: GitHub silently stops scheduling `news-pipeline.yml` (the exact thing that happened in
this repo during the billing outage). No run, no failure, no alert. `heartbeat.yml` as drafted
checks **only `r2` and `cead`** — `check-heartbeat.sh` has only those two modes
(`32-01-PLAN.md:138-141`), and `heartbeat.yml` has only those two steps
(`32-03-PLAN.md:128-138`). The highest-frequency, highest-value, most-recently-broken cron in
the repo has **no cron-side liveness detection**.

**Evidence against the plan's justification.** F-79 and `heartbeat.yml`'s own header comment
claim news is covered because `freshness.mjs` "is run on every local `npm run validate` **and
in ci.yml**". I verified: `site/scripts/validate/all.mjs:19,54` does include `freshness.mjs`
(≤3 days on `data/incidents/current.json`), and `ci.yml:3-5` triggers on **`pull_request` +
`workflow_dispatch` only**. On a quiet repo — which is precisely the state during an outage —
`ci.yml` never runs. F-79 rejected folding the heartbeat into `ci.yml` for exactly this reason
(`32-FABLE-DECISIONS.md:98-100`) and then leaned on `ci.yml` as the compensating control three
paragraphs later. The two statements cannot both be true.

**Severity: HIGH.** The phase would ship claiming CRON-02 closed while the requirement's
motivating case is uncovered.

**Amendment.** Add a third mode to `check-heartbeat.sh` — no new logic, only a case-arm
widening — and a third step to `heartbeat.yml`:

```bash
case "$mode" in
  news|r2|cead) ;;
  *) usage ;;
esac
```
```yaml
      - name: Check news pipeline heartbeat (data/incidents/current.json evidence, 3-day threshold per F-79)
        run: |
          LAST_NEWS=$(python -c "import json,sys; print(json.load(open('data/incidents/current.json'))['generated'])")
          bash .github/scripts/check-heartbeat.sh news 3 "$LAST_NEWS"
```

**Proof:** two-direction pytest cases mirroring the r2/cead pairs (fresh passes, 4-days-stale
fails, exact-3-days passes), plus one live read of the real
`data/incidents/current.json.generated` fed through the script. Verify the field name against
the real file before writing the plan text — I did not confirm it is `generated` at top level.

Also correct the false sentence in both `heartbeat.yml`'s header and DEPLOYMENT.md: replace
"run on every local `npm run validate` and in ci.yml" with "run on every local
`npm run validate` and in `ci.yml` — **which is `pull_request`-triggered and therefore does not
run on a quiet repo**". F-79's honesty clause is the best thing in this phase; do not let it
rest on a wrong fact.

---

## 6. [HIGH] `gh label create` at the head of the `if: failure()` block is a new way to lose the alert about the original failure

**Scenario.** 2026-09-14, `news-pipeline.yml` fails for a real reason. The alert step's
**first** line is now `gh label create pipeline-failure-news … --force`. Under GitHub's default
`bash -e`, if that call returns non-zero — secondary rate limit during a burst of 4-failures-a-day
retries, a transient 502, or a future tightening of what `issues: write` covers for label
mutation — the step dies **before `gh issue create` is ever reached**. The original failure is
reported nowhere. Today, with no label-create call, that path does not exist.

**Evidence.** `32-02-PLAN.md:200, 340, 412` and `32-03-PLAN.md:145`. F-77 forbids `|| true`
(Operating Lesson 8), so there is no in-shell escape hatch by design. `gh --version` on this
machine is 2.88.1 and `--force` is supported, so the flag itself is not the risk; the
serialization is.

The plan already half-recognises this — 32-03 Task 1 creates all four labels once, up front —
but that creation happens in **Wave 3**, *after* Wave 2 has already committed workflows that
depend on the labels. If the run is interrupted between waves, every alerting workflow ships
pointing at labels that do not exist.

**Counter-evidence I gathered (this reduces but does not remove the risk):** I probed the live
repo read-only — `gh issue list --label pipeline-failure-news --state open --json number` on a
label that does **not** exist returns empty output and **exit 0**. So the *dedup query* is safe
against a missing label; only `gh label create` and `gh issue create --label <missing>` are not.

**Severity: HIGH** (silent loss of the alert channel is the one unrecoverable failure).

**Amendment (satisfies F-77's no-`|| true` rule — this is workflow-level, not shell-level):**
hoist the label creation into its own step so its failure is visible but non-fatal:

```yaml
      - name: Ensure alert label exists
        if: failure()
        continue-on-error: true
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh label create pipeline-failure-news --color e11d48 --description "News Pipeline failure alert" --force

      - name: Alert via GitHub Issue on failure
        if: failure()
        …unchanged, minus the gh label create line…
```

`continue-on-error: true` is an existing, already-used pattern in `cead-scraper.yml` (lines
39/45/49/53 today), it shows as a visible ⚠ in the Actions UI rather than being swallowed, and
it is not a `|| true`.

**And reorder the waves:** move the four `gh label create --force` calls from 32-03 Task 1 into
**32-02 Task 1**, executed *before* the workflow files are edited. A label referenced by a
committed workflow must never predate its own existence.

**Proof:** `gh label list --json name --jq '.[].name'` must show all five `pipeline-failure*`
labels *before* 32-02's edits are committed; assert it as a `<automated>` gate in 32-02 Task 1
(`gh label list --json name --jq '.[].name' | grep -c '^pipeline-failure-news$'` == 1, etc.).

---

## 7. [MEDIUM-HIGH] The CEAD 100-day threshold is guaranteed to trip on 2026-09-27, and the dedup logic turns an acknowledged alert into a new issue every day

**Scenario.** `data/cead/` was last committed **2026-06-19** (measured; and every commit in
that path's history is a Phase-01…Phase-23 development commit — the "quarterly local scrape"
has *never* produced one). 2026-06-19 + 100 days = **2026-09-27**. Fifty-four days after this
phase ships, `heartbeat.yml` starts failing every day and never stops until a human runs the
CEAD scraper locally. The Q3 boundary (2026-07-01) has already passed with no commit, so the
condition is arguably a *true* positive — which makes it worse, not better: it is a true
positive nobody is going to act on for weeks.

Then the acknowledgement dynamics. Dedup is `gh issue list --label X --state open`:
- Day 1: no open issue → **create**.
- Days 2..N: open issue found → **comment**. One comment/day for as long as it lasts.
- A maintainer closes the issue to acknowledge → next day there is no *open* issue →
  **a brand-new issue is created**. Closing it again → another. **One new issue per day, forever.**

This dedup shape was copied unchanged from the quarterly and 6-hourly workflows, where the
close-to-ack loop is 4x/day at worst and quarterly at best. On a *daily* cron watching a
*quarterly* signal it is a permanent issue treadmill. F-77 rewrote which label is queried but
never re-derived whether `--state open` is the right dedup key at a daily cadence.

**Severity: MEDIUM-HIGH.** Alert fatigue is exactly how the *next* real alert (finding 1, 5,
or 6) gets ignored.

**Amendment, two parts:**

1. **Raise the CEAD threshold to 120 days** and say why in `heartbeat.yml` and DEPLOYMENT.md:
   a quarter is up to 92 days, plus realistic human lag on a manual local task. 100 is below
   the maximum *legitimate* gap and therefore cannot distinguish "late" from "stalled".
   Re-run the boundary proofs at 120.
2. **Change the dedup key from "open" to "open or recently closed"**, so a closed issue is a
   real acknowledgement rather than a reset button:
   ```bash
   RECENT=$(gh issue list --label pipeline-failure-heartbeat --state all \
     --search "created:>=$(date -u -d '7 days ago' +%F)" --json number --jq '.[0].number // empty')
   ```
   If `$RECENT` is non-empty, comment on it; otherwise create. A closed issue then suppresses
   re-creation for 7 days — the maintainer's close means something.

**Proof:** the query above is read-only and can be executed against the live repo during
planning to confirm its shape and exit code (I confirmed the `--state all --json` form returns
`[{"number":2,…}]` for the existing generic label, exit 0). Encode the threshold change as two
more pytest cases (`cead 120` at 120 d → exit 0; at 121 d → exit 1).

*If the planner prefers to keep 100 days:* then record explicitly in STATE.md
**"heartbeat.yml is expected to begin alerting on ~2026-09-27 unless a local CEAD scrape is
committed before then"** — a foreseeable alert must not arrive as a surprise.

---

## 8. [MEDIUM] The heartbeat's R2 step masks the CEAD step entirely, contradicting the issue body it writes

**Scenario.** R2 archive stalls *and* CEAD is overdue. The R2 step exits 1; step 2 never runs
(`if:` defaults to success-only). The alert body says "check which step (R2 archive or CEAD
reminder) failed" — but only one was ever evaluated, so the CEAD signal is invisible until R2
is fixed. Same in reverse: because R2 is first, an `actions: read` bug (finding 1) hides the
CEAD check permanently.

**Severity: MEDIUM.** Silent narrowing of a gate the phase advertises as covering "all three
cadences" (F-79).

**Amendment.** Run each check with `continue-on-error: true` and an `id:`, then a single
aggregation step:

```yaml
      - name: Check R2 archive heartbeat …
        id: r2
        continue-on-error: true
        …
      - name: Check CEAD reminder heartbeat …
        id: cead
        continue-on-error: true
        …
      - name: Aggregate heartbeat result
        run: |
          fail=0
          [ "${{ steps.r2.outcome }}" = "success" ] || { echo "::error::R2 heartbeat FAILED"; fail=1; }
          [ "${{ steps.cead.outcome }}" = "success" ] || { echo "::error::CEAD heartbeat FAILED"; fail=1; }
          exit "$fail"
```

**Proof:** re-lint with the fixed gate from finding 2 (must stay zero findings), and add a
grep gate that the number of `continue-on-error: true` occurrences equals the number of
`check-heartbeat.sh` invocations in `heartbeat.yml`.

---

## 9. [MEDIUM] The CRON-06 proof only covers the race that succeeds; the race that actually loses data is unproven and the success criterion overclaims

**Scenario.** `32-02-PLAN.md`'s must_have #5 and `<success_criteria>` state the loop "survives
a real git push race with **no lost update**", proven by a two-bare-clone simulation in which
"both commits end up on origin/master". That simulation uses **non-overlapping content**.

I ran the *overlapping* case against the exact loop body from the committed step:

```
push rejected, attempt 1
CONFLICT (content): Merge conflict in data/f.json
error: could not apply … B
::error::rebase conflict — aborting
pushed=0
--- origin log:   c1b25a8 A / 945922c seed        # B's data is GONE
```

The loop behaves **correctly** (loud, `exit 1`, origin unharmed, alert fires) — but the run's
scraped data is discarded, and RSS items that aged out are not recoverable on the next run.
The two workflows write whole-file JSON (`scrape_news.py:122` is a full `write_text` of
`current.json`), so *any* same-path race is a guaranteed conflict, never an auto-merge.

**Mitigating evidence (this is why it is MEDIUM, not HIGH):** `concurrency: group:
news-pipeline` prevents news-vs-news overlap, and news (`data/incidents/`) vs CEAD
(`data/cead/`) touch disjoint subtrees, so the realistic bot-vs-bot race *does* auto-merge and
the loop *does* recover. The lossy case needs a human pushing `data/` by hand concurrently.

Also checked and **cleared**: no infinite loop (bounded 5), no `--force` anywhere, no history
reordering beyond the ordinary rebase-on-top, `git rebase --abort` failing still exits
non-zero, `fetch-depth: 0` gives `git fetch origin master` + `git rebase origin/master` a real
merge-base (and the pack is 11.6 MiB, so it costs nothing), and every pipeline write lands
under `data/` (`pipeline/cache/` is gitignored) so the tree is never dirty at rebase time.

**Severity: MEDIUM** (the claim, not the code).

**Amendment.** Rewrite must_have #5 and `<success_criteria>` to state **both** directions, and
require **both** to be simulated:

> "…survives a race on *disjoint* `data/` paths with no lost commit (both land on origin);
> and on a *same-file* race it aborts loudly with `::error::` and exit 1, leaving origin
> unmodified and this run's data intentionally discarded for a human to re-trigger."

Add the same-file simulation to the `<verification>` block verbatim (the script above
reproduces it in ~15 lines against a scratch bare repo).

---

## 10. [LOW-MEDIUM] Stale prose: the CR-01 comment now documents an `if:` condition that no longer exists

Both `32-02-PLAN.md:116-117` and `:248-249` keep:

```yaml
    # CR-01: CF_HOOK MUST be job-level — a step-level env var is NOT in scope for
    # that same step's `if:` condition, so the deploy gate would never fire.
```

After this phase, **no `if:` in either file references `env.` at all** (the deletions-only diff
confirms `if: … && env.CF_HOOK != ''` is removed from both). The comment now explains a bug
class that the file no longer contains, and a future reader will look for the `if:` it
describes and not find it. F-76 ¶3 condemns exactly this in `deploy-on-code.yml` and then
reproduces it in the other two files.

**Amendment.** Replace with:

```yaml
    # CF_HOOK is job-level so the deploy step's `run:` can read it. NOTE (F-76): the old
    # `if: … && env.CF_HOOK != ''` gate was DELETED in Phase 32 — an empty hook is now a
    # hard failure at the guard step, not a silent skip. Do not reintroduce it.
    # (CR-01 history: a step-level env var is not in scope for that step's own `if:`.)
```

**Proof:** `grep -c "would never fire" .github/workflows/*.yml` == 0, and
`grep -c "Do not reintroduce it" .github/workflows/news-pipeline.yml .github/workflows/cead-scraper.yml` == 1 each.

---

## 11. [LOW] Existing open issue #2 is orphaned by the label split

Live read: issue **#2, "[pipeline] CEAD Scraper failed on 2026-07-03", state OPEN**, carrying
only the generic `pipeline-failure` label. After Phase 32, the CEAD alert queries
`pipeline-failure-cead`, finds nothing, and opens a **second** open CEAD issue on
2026-10-01 while #2 sits there. Minor, but it is the first visible artifact of the change and
it looks like the dedup broke.

**Amendment.** Add one line to 32-02 Task 1's action (a label add is the same class of
metadata mutation F-77 already authorised): `gh issue edit 2 --add-label pipeline-failure-cead`.
Verify: `gh issue list --label pipeline-failure-cead --state open --json number --jq '.[0].number'`
→ `2`.

---

## 12. [LOW] `gh run list` measures that R2 *ran*, not that it *did anything*

`--json createdAt` ignores `conclusion`. An `r2-archive.yml` that fires daily and fails daily
passes the heartbeat. This is *acceptable* — r2-archive has its own `issues: write` alert path,
so its failures are covered by a different instrument, and F-79 explicitly scoped the heartbeat
to detecting **silence**. **Accept this risk**, but add `conclusion` to the `--json` list and
print it in the OK message so the run log shows *what* was found, not just how old it was.
(Cost: one word. I verified the live command returns
`{"conclusion":"success","createdAt":"2026-08-04T07:58:30Z"}`.)

---

## 13. Categories where I found nothing real — stated plainly rather than padded

- **Full-file replacement deleting something (prompt item 7): NOTHING FOUND.** I extracted the
  four proposed YAMLs and ran a deletions-only `diff -u` against the real files. The only
  removed lines are the four intended ones (`git push` → retry loop; the
  `&& env.CF_HOOK != ''` clause; the old curl lines; the shared-label dedup query; the
  `deploy-on-code.yml` dry-run block). **Every** `concurrency:` group, `permissions:` block,
  `timeout-minutes:`, `continue-on-error: true` (all four in `cead-scraper.yml`), `PYTHONPATH: .`,
  `ARCHIVE_MAX_FETCH: '100'`, action version (`@v7` throughout), `paths:` filter and header
  comment survives verbatim. This is unusually clean full-file-replacement work.
- **Fork / PR paths breaking the deploy (prompt item 1): NOTHING FOUND.** None of the four
  edited workflows run on `pull_request`; `deploy-on-code.yml` is `push`-to-`master`-only on the
  origin; `schedule` never fires on forks. There is no fork or PR path into the hard-fail guard.
- **actionlint / shellcheck findings on the proposed content: NONE.** All five proposed
  workflow YAMLs plus `heartbeat.yml` and both `.sh` scripts lint clean at exit 0 with the real
  pinned binaries (I ran them). The lint *gate* is broken (finding 2); the linted *content* is not.
- **The plans' documented two-direction script proofs: ALL REPRODUCED.** `require-env.sh` blank
  → exit 1 with the variable name; `check-heartbeat.sh` at exactly the threshold → exit 0;
  empty timestamp → exit 1; unparseable → exit 1. The CRON-03 identity grep returns exactly one
  distinct line. The pytest baseline is exactly 344/1/1. No verify gate other than the actionlint
  one (finding 2) is vacuous, and none of them fails on a correct tree.
- **Line endings / `chmod +x` (prompt item 5): NOT A RISK HERE.** `core.autocrlf=false` locally
  and globally, there is no `.gitattributes`, and the plans already mandate `bash <script>`
  rather than bare execution — so the x-bit never matters. The *only* cross-platform problem is
  finding 3, and it is the interpreter, not the file.

---

## Amendment checklist for the planner

| # | Sev | Change | Where |
|---|-----|--------|-------|
| 1 | CRIT | add `actions: read` to `heartbeat.yml` permissions | 32-03 interfaces |
| 2 | CRIT | replace all actionlint `<automated>` gates with resolve-assert-canary-lint | 32-02 T1/T2, 32-03 T1 |
| 3 | HIGH | explicit `BASH` resolution + canary test + substring assertions on every negative test; baseline **360** not 359 | 32-01 T2 (+ 32-03 T2 step 3) |
| 4 | HIGH | split the deploy-hook guard out of the first-step guard; guard `CF_HOOK`, drop the `CF_DEPLOY_HOOK_URL` alias — **or** record the accepted risk | 32-02 interfaces |
| 5 | HIGH | add `news` mode to `check-heartbeat.sh` + a news step to `heartbeat.yml`; fix the false `ci.yml` claim in F-79/header/DEPLOYMENT.md | 32-01 + 32-03 |
| 6 | HIGH | hoist `gh label create` into its own `continue-on-error: true` step; move label creation from Wave 3 to Wave 2, before the edits | 32-02, 32-03 T1 |
| 7 | MED+ | CEAD threshold 100 → 120 d; dedup on `--state all` + `created:>=7 days ago` | 32-01, 32-03 |
| 8 | MED | `continue-on-error` + aggregation step in `heartbeat.yml` | 32-03 |
| 9 | MED | state and simulate BOTH race directions; stop claiming "no lost update" unconditionally | 32-02 must_haves + verification |
| 10 | LOW+ | rewrite the now-stale CR-01 comment in both files | 32-02 interfaces |
| 11 | LOW | `gh issue edit 2 --add-label pipeline-failure-cead` | 32-02 T1 |
| 12 | LOW | add `conclusion` to the heartbeat's `gh run list --json` | 32-03 |

Findings 1, 2, 3, 5 and 6 are the ones that make the phase *fail* rather than merely disappoint:
each one leaves the repo believing it has monitoring it does not have.
