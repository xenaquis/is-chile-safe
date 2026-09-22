# Phase 33 — Security Posture: PREMORTEM

**Written:** 2026-08-05 (Opus, adversarial)
**Frame:** Two weeks from now. Phase 33 shipped, verified, pushed to master, production is live. Something went wrong anyway.
**Method:** Every claim below that says PROVEN was produced by executing a command against a real
scratch reconstruction of the post-change tree at
`…/scratchpad/tree/` (all 13 refs pinned to the F-118 SHAs, 6 × `persist-credentials: false`,
2 × inline `# zizmor: ignore[artipacked]`, 3 new job-level `permissions:` blocks, 3 new
`lint-workflows` steps). Tools actually run: `uvx zizmor@1.10.0` (with and without a real
40-char `GH_TOKEN`), the repo's own `.tools/actionlint.exe` + `.tools/shellcheck.exe`, and the
research drafts of both new scripts.

---

## What I could NOT break (recorded so it is not re-litigated)

These were attacked and held. They are evidence, not reassurance.

- **The post-change tree is clean end-to-end.** On the reconstructed tree:
  `actionlint -shellcheck shellcheck .github/workflows/*.yml` → **exit 0**;
  `uvx zizmor@1.10.0 --persona=regular .github/workflows/` → **exit 0, "No findings to report.
  (2 ignored, 21 suppressed)"**; `check-sha-pins.sh` → **exit 0, "examined 13 uses: lines"**;
  `grep -rc 'persist-credentials: false'` over the four non-pushing workflows → **6**;
  `grep -c "permissions:" ci.yml` → **4**. Both new script drafts are **shellcheck-clean**
  (`.tools/shellcheck.exe -s bash` → exit 0), so `lint-workflows.sh:38`'s glob will not redden.
- **`persist-credentials: false` is safe on all six targets — verified from the code, not from
  the plan.** `.github/scripts/push-with-rebase.sh:17` does a bare `git push origin "$branch"`,
  i.e. it consumes the persisted `extraheader` credential. It is invoked from exactly two places:
  `news-pipeline.yml:78` and `cead-scraper.yml:97` — the two the plan excludes. The other four
  workflows contain **no** `git push` and no `push-with-rebase.sh` call:
  `ci.yml` (npm/pytest/lint only), `deploy-on-code.yml` (checkout + `require-env.sh` + `curl`),
  `r2-archive.yml` (python + `gh`, `contents: read`), `heartbeat.yml` (`git log`, `gh run/issue`
  — all of which use the explicit `GH_TOKEN: ${{ github.token }}` env, never the git credential).
  F-105's triage is correct as written. This was the prompt's flagged highest-risk item; it is
  **not** a Phase-32-class "guard that breaks a healthy system."
- **The token-gated zizmor audits do not add findings.** F-105/F-119's baseline was measured
  token-less, so the five online audits (`impostor-commit`, `ref-confusion`,
  `known-vulnerable-actions`, `forbidden-uses`, `stale-action-refs`) had never run against the
  *pinned* tree — a plausible way for CI to go red on the first PR (`stale-action-refs` in
  particular inspects SHA pins). I re-ran with a real `GH_TOKEN` (len 40) against the fully
  pinned + suppressed tree: **exit 0, same "2 ignored, 21 suppressed"**, only
  `forbidden-uses: audit not configured` skipped. PROVEN non-issue.
- **There is no circular import.** `pipeline/news/fulltext.py:29` imports `gnews_decoder` at
  module level; `gnews_decoder.py:33-45` imports `fulltext.USER_AGENT` lazily precisely to break
  that cycle. `scrape_news.py` is imported by neither. `from pipeline.news.fulltext import
  REQUEST_DELAY` inside `main()` closes no loop. The prompt's circular-import hypothesis is
  unfounded. (A different, real cost is FM-11 below.)
- **The inline `# zizmor: ignore[artipacked]` suppressions fail *safe*.** zizmor's finding span
  for a checkout step runs from the `- uses:` line through the following comment block up to the
  next step (observed in the pre-fix output). If a future edit moves or reformats the step, the
  comment either still sits inside that span (suppression holds, correct) or falls outside it
  (the finding returns, **CI goes red — annoying but safe**). There is no reachable arrangement
  where the comment silently suppresses a *different* finding: `ignore[artipacked]` is rule-keyed
  and the only artipacked findings in this repo are checkout steps, each with its own span.

---

## Failure modes

### FM-01 — `check-secret-hygiene.sh` flags itself and exits 1 on a perfectly correct tree
**Severity: BLOCKER** · **PROVEN by execution**

The gate scans `.github/scripts/*.sh` (33-03 `<interfaces>`, Scope line: "`.github/workflows/*.yml`
and `.github/scripts/*.sh` ONLY"). It lives in `.github/scripts/`. Its own regex string and its own
`::error::` message text contain the patterns it hunts. I wrote the research draft verbatim to
`.github/scripts/check-secret-hygiene.sh` in the scratch tree and ran it against an otherwise
clean tree:

```
::error file=.github/scripts/check-secret-hygiene.sh,line=10::set -x enables command-echo:   echo "…::set -x enables command-echo: $content"
::error file=.github/scripts/check-secret-hygiene.sh,line=12::set -x …: done < <(grep -rHnE "set -x|set -o xtrace" …)
::error file=.github/scripts/check-secret-hygiene.sh,line=14::curl -v/--verbose:   echo "…::curl -v/--verbose: $content"
EXIT:1
```

Note that **two of the three self-hits come from the error-message strings, not the regexes** —
so rewording the patterns alone does not fix it. This is Phase 27's "a validator that scanned its
own source for the patterns it necessarily contained" (lesson 9), reproduced exactly, in the
phase that cites lesson 9. 33-03 Task 1's `<verify>` block asserts `EXIT:0` on the real tree; the
task as written **cannot pass**.

**AMENDMENT (33-03, Task 1):** in the `<action>`, require every scanning `grep` to carry
`--exclude=check-secret-hygiene.sh`, AND require the `::error::` message strings to be written so
they do not contain the literal patterns (e.g. `"xtrace/command-echo enabled"` and
`"verbose curl"`). Add to `<behavior>`: "Against the real tree *including this script itself*:
exits 0." Because self-exclusion is itself a way to disarm a gate, pair it with FM-06's canary.

---

### FM-02 — F-117's prescribed correction does not work: `set -euo pipefail` cannot see a failing grep in a process substitution
**Severity: BLOCKER** · **PROVEN by execution**

F-117 (binding) and 33-03 lines 104-108 / 161 / 170 instruct: remove `2>/dev/null || true` and
"let `set -euo pipefail` propagate a real grep error (rc ≥ 2) as a hard script failure."
Both scripts use `done < <(grep …)`. **A process substitution's exit status is never examined by
`set -e` and is not part of any pipeline, so `pipefail` does not apply either.** Minimal proof:

```bash
#!/usr/bin/env bash
set -euo pipefail
fail=0
while IFS=: read -r f l c; do fail=1; done < <(grep -rHnE "echo" /nonexistent/path/*.yml)
echo "reached end, fail=$fail"; exit "$fail"
```
→ `grep: /nonexistent/path/*.yml: No such file or directory` … `reached end, fail=0` … **`EXIT:0`**

So on an unreadable/mis-globbed tree, `check-secret-hygiene.sh` prints a clean green over a scan
of nothing — **the exact F-85 / Phase-32 `actionlint -shellcheck ""` defect the phase exists to
prevent**, shipped by the correction written to prevent it. Two consequences:
(a) the gate cannot fail on a broken scan; (b) 33-03 Task 1's `<behavior>` bullet *"Against an
unreadable target path … exits non-zero via `set -euo pipefail` propagation"* is a behaviour that
**cannot be demonstrated** — an executor proving it will either fake it or silently drop it.

`check-sha-pins.sh` survives this only by accident, via `EXPECTED_COUNT`.

**AMENDMENT (33-03 Task 1 and 33-01 Task 3, and the `<interfaces>` text of both):** replace the
process-substitution idiom with an explicitly-checked capture in **both** scripts:

```bash
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
set +e; grep -rHnE "$PAT" "${TARGETS[@]}" >"$tmp"; rc=$?; set -e
[ "$rc" -ge 2 ] && { echo "::error::scan failed (grep rc=$rc) — refusing to report a clean tree"; exit 1; }
while IFS=: read -r file line content; do …; done <"$tmp"
```
and restate the F-117 rationale in the plans with the corrected mechanism (F-117's *intent* is
right; its *named mechanism* is wrong and must not be copied into the scripts as prose).

---

### FM-03 — SHA-pinning breaks an existing pytest, and the failure message accuses the test suite of being vacuous
**Severity: BLOCKER** · **PROVEN by execution**

`pipeline/tests/test_workflow_guards.py:592` does a literal substring match:

```python
if "uses: actions/setup-python@v7" in line:
    skip_next_pip_block = True
```

inside `test_guard_is_non_vacuous_against_a_synthetic_regression`, which mutates the real
`cead-scraper.yml` text and asserts the mutation is detected. After 33-01 Task 2 the line reads
`uses: actions/setup-python@5fda3b95… # v7.0.0`, the mutation matches nothing, nothing is
removed, and the final assertion fires. I ran the module's own `_python_run_steps_missing_setup`
against the pinned scratch file:

```
clean on pinned tree: True
mutation found offenders: False -> test_guard_is_non_vacuous FAIL
```

The failure text is `"mutation removed setup-python/pip install but the guard found nothing —
vacuous test"` — i.e. the CI failure will read as *"a security-guard test has gone vacuous"*
rather than *"a string literal needs updating"*, which is exactly the kind of legible-looking,
misleading red that eats a fix cycle. `pipeline/tests/test_workflow_guards.py` appears in **no**
plan's `files_modified`, and 33-01's own verify blocks are all greps, so 33-01 will report
success and the breakage will surface at the phase-close gate (or on the PR's `ci.yml` pipeline
job) attributed to Plan 33-03.

Related, and checked: `_python_run_steps_missing_setup`'s job-reset heuristic (`startswith("  ")
and not startswith("   ")`) is **unaffected** by the new 4-space job-level `permissions:` blocks,
and `test_ci_yml_calls_lint_workflows_script` / `test_lint_workflows_shellchecks_its_own_scripts_directly`
both still pass. This one test is the whole exposure.

**AMENDMENT (33-01, Task 2):** add `pipeline/tests/test_workflow_guards.py` to `files_modified`
and add to the `<action>`: "change the mutation helper's match at line 592 from the version-tagged
literal to the version-agnostic prefix `\"uses: actions/setup-python@\"` (matching line 522's
existing `startswith(\"- uses: actions/setup-python\")` style, which is already pin-agnostic), then
re-run `python -m pytest pipeline/tests/test_workflow_guards.py -q` and confirm the non-vacuity
test still fails when the mutation is neutered." Add to Task 2's `<verify>`:
`cd pipeline && python -m pytest tests/test_workflow_guards.py -q` (exit-code gated, see FM-05).

---

### FM-04 — The secret-hygiene gate does not know the name of the variable the workflows actually use
**Severity: HIGH** · **PROVEN by execution**

33-03's `<interfaces>` fixes the name list at "exactly the 7 real repo secrets (F-111) — do not
add `R2_BUCKET`". The research draft had an eighth entry, **`CF_HOOK`**, and the plan silently
drops it. But `CF_DEPLOY_HOOK_URL` is never referenced in a `run:` body anywhere: all three
workflows alias it at job level (`cead-scraper.yml:39`, `deploy-on-code.yml:45`,
`news-pipeline.yml:26` — `CF_HOOK: ${{ secrets.CF_DEPLOY_HOOK_URL }}`) and every consumer says
`"$CF_HOOK"` (`…:111`, `…:62`, `…:96`; `require-env.sh CF_HOOK`). So:

```
$ printf 'run: echo "$CF_HOOK"\n' > /tmp/x.yml
$ grep -HnE '(echo|printf)[^|]*\$\{?(CF_DEPLOY_HOOK_URL|DEEPSEEK_API_KEY|…|TOKEN_VALUE_R2)\b' /tmp/x.yml
rc=1        # NOT CAUGHT
```

The single highest-risk shape in the repo (a secret that *is* a URL, per F-107) is the one the
gate is blind to, and it is blind to it in the one spelling a developer would actually write.
The plan's rationale conflates "is a name in `gh secret list`" with "is a variable holding a
secret value". F-111's binding content is the **secret inventory**; extending the gate's
*variable* list is not a reopening of F-111 — it is the same guard-from-what-the-code-READS
discipline F-111/lesson 29 demand.

**AMENDMENT (33-03, `<interfaces>` + Task 1):** the name list is
`CF_DEPLOY_HOOK_URL|CF_HOOK|DEEPSEEK_API_KEY|OPENROUTER_API_KEY|R2_ACCESS_KEY_ID|R2_SECRET_ACCESS_KEY|R2_ENDPOINT_URL|TOKEN_VALUE_R2`,
with an explicit in-plan note: "`CF_HOOK` is not a repo secret; it is the job-level **alias** every
consumer reads, which is why it belongs here and `R2_BUCKET` still does not." Add to
`<behavior>`: a planted `echo "$CF_HOOK"` must fire.

---

### FM-05 — Exit-code laundering in six `<automated>` verify blocks, three of which cannot fail at all
**Severity: HIGH** · **PROVEN by execution**

Directive lesson 8, grepped across all three plans:

| Location | Block | Why it launders |
|---|---|---|
| `33-01-PLAN.md:154` | `grep -c "permissions:" .github/workflows/ci.yml` | `grep -c` exits **0** for any count ≥ 1. On the *unmodified* tree it prints 1 and exits 0. **Cannot fail.** |
| `33-01-PLAN.md:167` | `grep -rc … \| grep -v ':0' \| grep -v '^$' \| wc -l` | status is `wc`'s → always 0. Prints `6` pre-edit and `0` post-edit (I ran both), so the *output* discriminates, but the exit code never does. **Cannot fail.** |
| `33-01-PLAN.md:218`, `:261`, `:262` | `bash …; echo "EXIT:$?"` | the `;` breaks the chain; block exits with `echo`'s 0. |
| `33-02-PLAN.md:270` | `grep -rc … \| awk -F: '{s+=$2} END{print s}'` | status is `awk`'s → always 0. **Cannot fail.** |
| `33-02-PLAN.md:280` | `uvx zizmor …; echo "EXIT:$?"` | same `;` defect |
| `33-03-PLAN.md:191`, `:243`, `:329`, `:330` | `bash …; echo "EXIT:$?"` and **`python -m pytest …; echo "EXIT:$?"`** | a failing pytest run yields block exit 0 |

Phase 27 shipped this four times, once directly under prose banning it; 33-03 line 108 bans
`|| true` on evidence-gathering and line 191 launders its own gate's status three lines later.

**AMENDMENT (all three plans, every `<automated>` block):** drop `; echo "EXIT:$?"` entirely
(the harness reports the exit code) and convert every count assertion to an exit-code assertion:
- `test "$(grep -c 'permissions:' .github/workflows/ci.yml)" -eq 4`
- `! grep -rq 'uses: actions/.*@v7$' .github/workflows/*.yml`
- `test "$(grep -rhc 'persist-credentials: false' <4 files> | paste -sd+ | bc)" -eq 6`
  (or a `python3 -c` assertion, matching 33-02 Task 1's style, which is the one block in the
  phase that is already correctly exit-code gated)
- `bash .github/scripts/check-sha-pins.sh`
- `cd pipeline && python -m pytest tests/test_scrape_news.py -q`

---

### FM-06 — Neither new gate has a positive control; `check-secret-hygiene.sh` reports GREEN on the real tree today *before it is written*
**Severity: HIGH**

The repo's existing `lint-workflows.sh:24-30` refuses to trust itself until a canary fixture
produces **two specific finding codes** (F-85's countermeasure). Neither new script has an
equivalent. `check-secret-hygiene.sh`'s success condition is "zero findings", and I confirmed
that all three of its greps already return rc 1 on the real tree — so an accidentally-inert
version of the script (broken regex, mis-globbed `TARGETS`, FM-01's exclusion applied too
broadly, FM-02's swallowed rc≥2) is **byte-indistinguishable from success**. `check-sha-pins.sh`
has one (`EXPECTED_COUNT`) and it is the only reason FM-02 does not sink it too.

**AMENDMENT (33-03, Task 1):** require a committed fixture directory
`.github/scripts/fixtures/secret-hygiene-canary/` containing one `.yml` and one `.sh` file that
between them exhibit all four risk shapes, and require the script to scan the fixture first and
**abort loudly if it does not produce all four named findings**, before scanning the real tree —
mirroring `lint-workflows.sh:24-30` verbatim in structure. Ensure the real-tree scan excludes
the fixture directory. This also converts FM-01's `--exclude` from a disarming mechanism into a
verified one.

---

### FM-07 — All three plans are `wave: 1`, `depends_on: []`, and all three edit `.github/workflows/ci.yml`
**Severity: HIGH**

`33-01` (permissions blocks + SHA pins + a new `lint-workflows` step), `33-02` (a second new step
+ `persist-credentials:` inside the *same three checkout steps* 33-01 is rewriting), and `33-03`
(a third new step) all list `.github/workflows/ci.yml` in `files_modified` with no declared
ordering. 33-02 and 33-01 additionally both edit all five other workflow files, at the same
lines. 33-02's `<interfaces>` says "append, do not reorder" and "after whatever steps Plan 33-01
already added there" — that is a *hope* about ordering, not a declared dependency; the executor
dispatcher has nothing to enforce it. Worst case is not a merge conflict (loud) but a
last-writer-wins overwrite of 33-01's `permissions:` blocks or SHA pins by a stale in-memory copy
in 33-02 — silent, and 33-02's verify blocks would not notice.

**AMENDMENT (frontmatter):** set `33-02: depends_on: ["33-01"]`, `wave: 2`;
`33-03: depends_on: ["33-01","33-02"]`, `wave: 3`. This costs nothing (the phase is three small
plans) and removes the only concurrency hazard in it.

---

### FM-08 — `EXPECTED_COUNT=13` turns the first legitimate workflow step into what reads as a security violation
**Severity: MEDIUM**

F-117/F-114 fix the count at 13. The invariant that actually matters is *"every `uses:` ref is
pinned, and the scan examined a non-zero, plausible number of them."* An exact-equality check
additionally asserts *"nobody ever adds or removes an action"*, which is false by design —
33-02 ships dependabot precisely so the refs churn, and the very first `actions/cache` or
`actions/upload-artifact` step anyone adds makes the gate emit
`::error::expected 13 uses: lines, examined 14` on a **correctly pinned** tree. The contributor's
reasonable reading is "the security gate rejected my pinned action."

Note this is *not* a dependabot problem: dependabot bumps the SHA in place and never changes the
line count (verified conceptually and by the shape of the edit — 13 in, 13 out).

I am **not** proposing to drop the assertion: without it, FM-02 sinks this script too.

**AMENDMENT (33-01, Task 3):** keep `EXPECTED_COUNT` but make it a **floor plus a legibility
contract**: fail if `count -lt EXPECTED_MIN_COUNT` (13) — an undercounted/empty scan still hard-
fails, which is the whole point of F-117 — and on `count -gt EXPECTED_MIN_COUNT` emit a
**non-fatal notice** (`::notice::examined N uses: lines; EXPECTED_MIN_COUNT is 13 — bump it in
check-sha-pins.sh if refs were legitimately added`). Every ref is still individually pin-checked,
so a new *unpinned* ref fails on its own merits, not on arithmetic. If the orchestrator prefers
strict equality (defensible), then amend the error text to say explicitly *"this is a coverage
assertion, not a pin failure; if you legitimately added a step, update EXPECTED_COUNT"* and add
that instruction to DEPLOYMENT.md's decision record in 33-03 Task 3.

---

### FM-09 — `curl -v` / `set -x` fire on legitimate explanatory prose in this repo's comment-heavy workflows
**Severity: MEDIUM**

The patterns are unanchored line greps over `.yml`, and these workflows are ~40 % comment by line
count, much of it about exactly these mechanisms (`cead-scraper.yml:32-36`, `news-pipeline.yml:19-23`,
`r2-archive.yml:22-35`, `heartbeat.yml:47-51`). Today the tree is clean (all three greps rc 1,
verified). But 33-03 Task 3 itself instructs the executor to write documentation about "`-v` would
[leak the URL]" — put one sentence of that rationale into a workflow comment (the natural place
for it, and this repo's established habit) and CI goes red on a comment. This is Phase 31's
"guard that banned ordinary correct Spanish" (lesson 26) in a new alphabet.

**AMENDMENT (33-03, Task 1):** anchor the two shape checks to non-comment content — skip lines
whose first non-space character is `#` for the `.sh` scan and lines matching `^\s*#` for the
`.yml` scan — and add to `<behavior>` the two-direction list lesson 26 requires: MUST fire on
`run: curl -v "$CF_HOOK"` and on `set -x` in a script body; MUST stay silent on
`# never add curl -v here — it would print the hook URL` and on `# set -x is banned in this repo`.

---

### FM-10 — `pipx run zizmor` (A1) is proved on a runner exactly once, by a step that nothing schedules
**Severity: MEDIUM** · **ACCEPT with a hardening amendment**

A1 is `[CITED: actions/runner-images Ubuntu2404-Readme.md]`, never executed (pipx is absent on
this dev machine; I confirmed `uvx` present, and used it for every zizmor measurement above).
Failure mode if wrong: `pipx: command not found`, exit 127, red `lint-workflows` job. Observability:
`ci.yml` is `pull_request` + `workflow_dispatch` only (F-95, F-110 — re-opening that is rejected and
I do not propose it), so **nothing observes it until someone opens a PR**, and this run does not
push PRs. F-113's single `workflow_dispatch` is therefore not belt-and-braces — it is the *only*
observation event in the phase, and it is an orchestrator action recorded in 33-02 Task 2's
`<done>` as something "this task does not need to perform".

Accepting the risk is right (the fallback is one line, the blast radius is a red check on a
read-only job). What is not right is leaving the observation optional.

**AMENDMENT (33-02, Task 2 `<done>` and the phase-close gate in 33-03 Task 3):** promote the
F-113 dispatch to a **blocking phase-close item**, with the recorded evidence being the run URL,
the step's conclusion, and the log line proving zizmor's version banner printed (not merely "the
job was green" — a job can be green with a skipped step). Add to the step in `ci.yml` a preceding
one-line guard `command -v pipx || { echo "::error::pipx absent on this runner image — see F-112/A1 fallback in DEPLOYMENT.md"; exit 1; }` so the failure names its own remedy instead of
reading as a zizmor crash (research Pitfall 3).

---

### FM-11 — The courtesy-delay import makes `trafilatura` a hard dependency of the 4×/day cron for the sake of one float
**Severity: MEDIUM** · **ACCEPT, with the symptom named**

`from pipeline.news.fulltext import REQUEST_DELAY` (33-03 Task 2) pulls in `requests`,
`trafilatura`, `tenacity` and `pipeline.news.gnews_decoder` at `main()` time, into a code path
that previously imported none of them. All are in `pipeline/requirements.txt` (verified:
`trafilatura` is present, unpinned), so this works today. If a future `trafilatura` release
breaks import on Python 3.12, the news pipeline dies — but **loudly**: the import sits inside
`main()`'s `try:` and `scrape_news.py:381-383` does `logger.error("Pipeline failed: %s", exc,
exc_info=True); return 1`, which is a red job and an alert issue, not a silent no-op.

Reusing one constant (F-108) is the right call and I am not proposing to reopen it. The observable
symptom, for the record: a `news-pipeline` run failing at "Pipeline failed: … ModuleNotFoundError"
before any feed is fetched, with `fetched=0`. **ACCEPT.**

---

### FM-12 — The new pytest patches the global `time.sleep` and can be inflated by any other sleeper
**Severity: MEDIUM**

33-03 Task 2 says patch `pipeline.scrape_news.time.sleep` "the name as imported into
`scrape_news`'s module namespace, not `time.sleep` globally". Because `scrape_news` does
`import time` (module object, not `from time import sleep`), `pipeline.scrape_news.time` **is**
the global `time` module — the two are the same object and the distinction the plan draws does
not exist. `call_count == 2` therefore counts every sleep anywhere in the run. With `fetch_feed`,
the classifier, the resolver and the centroid all mocked (per the referenced
`test_per_feed_failure_isolated` shape) nothing else sleeps today, so the test passes — but any
future `tenacity` retry or added backoff on an un-mocked path turns it into an off-by-N flake,
and the plan's own stated mechanism is wrong, which the next reader inherits.

**AMENDMENT (33-03, Task 2):** replace the mechanism sentence with: "patch `time.sleep` via
`monkeypatch.setattr(sn.time, 'sleep', mock)` and note in the test docstring that this is the
process-global `time` module. Assert on `[c.args[0] for c in mock.call_args_list] ==
[REQUEST_DELAY] * (len(FEEDS) - 1)` rather than on a bare `call_count`, so an extra sleep from an
unrelated path is distinguishable from an extra *feed-gap* sleep." Keep the mutation proof
(revert the line → RED) that Task 2's `<done>` already requires; it is correct and its failure is
possible.

---

### FM-13 — The phase-close pytest figure is stated as a floor, so it cannot detect a test that vanished
**Severity: MEDIUM**

33-03 Task 3 states "pytest 390 passed / 1 skipped / 1 xfailed **at minimum**, PLUS this phase's
new tests … the exact new total is confirmed by running the full suite, not assumed here." I
collected the current suite: **392 tests collected** (= 390 + 1 skipped + 1 xfailed, matching
STATE.md:300). A floor is honest but not a gate: with FM-03 unfixed, the run is 389 passed / 1
failed / … which is *below* the floor and would be caught — but with FM-03 fixed and, say, a
different test silently deleted, 390 + 2 new − 1 deleted = 391 still clears "at minimum 390".

**AMENDMENT (33-03, Task 3):** once FM-03 and the exact number of new tests are settled, state
the close figure as an **equality**: "pytest **392 passed / 1 skipped / 1 xfailed** (390 + 2
courtesy-delay tests; `test_workflow_guards.py`'s count is unchanged — its literal was updated,
not its cases)", gated on the process exit code, with the existing (correct) warning that
`*failed*` also matches `1 xfailed`.

---

### FM-14 — `check-sha-pins.sh` parses `grep "uses:"` output, which is a substring match over comment text
**Severity: LOW** · **ACCEPT**

The scan is `grep -rHn "uses:" .github/workflows/*.yml`, not a YAML parse. Today the count is
exactly 13 with **zero** non-step matches (verified: `grep -rHn "uses" … | grep -v "uses: actions/"`
returns nothing). But a future comment such as `# this job uses: the persisted credential`
becomes a phantom 14th "ref", fails the sed extraction, and emits
`::error::malformed uses: line, no @ref`. Fail-safe direction, legible-ish message, and the
alternative (a YAML dependency in `.github/scripts/`) is worse — `test_workflow_guards.py:499-503`
already records the project's deliberate choice not to add one. Observable symptom: a red
`check-sha-pins` step naming a comment line. **ACCEPT.** (Cheap optional hardening if the
orchestrator wants it: anchor the grep to `-E "^[[:space:]]*-?[[:space:]]*uses:"`.)

---

### FM-15 — The version-comment regex vs. what dependabot actually writes
**Severity: LOW** · **ACCEPT**

The check is `#[[:space:]]*v[0-9]+(\.[0-9]+){0,2}`, which accepts `# v7`, `# v7.0`, `# v7.0.2`
and `# v8.0.0` — every shape dependabot emits when it rewrites a SHA pin's trailing comment (it
preserves the comment position and substitutes the new tag name; when the pin is to a tag it
writes that tag's name). A dependabot PR therefore cannot be rejected by this gate on comment
*shape*. The only rejection path is a bump PR that drops the comment entirely, which dependabot
does not do for comment-bearing pins. Residual, stated rather than hidden: nothing machine-checks
that the comment is *true* (F-118 already names this), so a dependabot PR that updates the SHA
but not the comment would pass — that is a review responsibility, recorded in 33-03 Task 3's
decision record. **ACCEPT.**

---

### FM-16 — zizmor's version pin never rots into a red CI, and never gets updated either
**Severity: LOW** · **ACCEPT, with one documentation line**

The prompt asks whether the 1.10.0 pin is sufficient against a future zizmor release adding an
audit that fires on this repo. It is: `pipx run zizmor==1.10.0` is an exact `==` pin resolved at
run time, and zizmor's own transitive deps do not change its audit set. So the "unrelated PR goes
red because zizmor 1.11 added an audit" scenario **cannot happen**. The mirror risk is the real
one: **nothing bumps it**. `pipx run` is not a manifest entry, so 33-02's dependabot `pip`
ecosystem (scoped `directory: /pipeline`) will never see it, and SEC-04 forbids adding it to
`requirements.txt`. The scanner will sit at 1.10.0 indefinitely, silently missing every audit
added after Aug 2026, while DEPLOYMENT.md records it as "the OWASP/GitHub-ecosystem-endorsed
Actions scanner."

**AMENDMENT (33-03, Task 3, one sentence — not a new mechanism):** in class (c) of the decision
record, state explicitly: "this version pin is **not** covered by dependabot (it is not a manifest
entry) and will not self-update; re-evaluate the pinned zizmor version at each milestone close."
An unstated tolerance is read as coverage (lesson 30).

---

## Ranked amendments the orchestrator should require before approving

| # | Amendment | Plan / Task | Severity | Why first |
|---|-----------|-------------|----------|-----------|
| 1 | Exclude the script from its own scan **and** reword its `::error::` strings so they don't contain the hunted patterns (FM-01) | 33-03 T1 | BLOCKER | Task cannot pass on a correct tree; PROVEN exit 1 |
| 2 | Replace the process-substitution grep idiom with an explicit `rc` capture in **both** new scripts, and correct the F-117 mechanism prose (FM-02) | 33-03 T1 + 33-01 T3 + both `<interfaces>` | BLOCKER | The phase's own anti-F-85 correction does not work; PROVEN `EXIT:0` over an unscanned tree |
| 3 | Update `test_workflow_guards.py:592`'s `@v7` literal to a version-agnostic prefix; add the file to 33-01's `files_modified` and its pytest to Task 2's verify (FM-03) | 33-01 T2 | BLOCKER | SHA-pinning reddens an existing test; PROVEN |
| 4 | Add `CF_HOOK` to the secret-name list, with the alias-vs-secret rationale in-plan (FM-04) | 33-03 `<interfaces>` + T1 | HIGH | The highest-risk secret is invisible to the gate in the only spelling used; PROVEN |
| 5 | De-launder all six `<automated>` blocks: drop `; echo "EXIT:$?"`, convert `grep -c` / `wc -l` / `awk` counts to `test … -eq N` or `! grep -q` (FM-05) | all three plans | HIGH | Three blocks cannot fail, including the pytest one; directive lesson 8 |
| 6 | Give `check-secret-hygiene.sh` a committed canary fixture it must make fire before it trusts a clean tree (FM-06) | 33-03 T1 | HIGH | Its success condition is "silence"; makes #1's exclusion verified rather than disarming |
| 7 | Serialize the plans: 33-02 `depends_on: [33-01]` wave 2; 33-03 `depends_on: [33-01, 33-02]` wave 3 (FM-07) | frontmatter | HIGH | Three concurrent plans editing the same `ci.yml` steps; free to fix |
| 8 | Turn `EXPECTED_COUNT` into a floor + `::notice::` on overcount, or make the equality's error text self-explaining (FM-08) | 33-01 T3 | MEDIUM | Otherwise the first legitimate new step reads as a security violation |
| 9 | Skip comment lines in the `set -x` / `curl -v` checks; add the two-direction MUST-fire / MUST-stay-silent lists (FM-09) | 33-03 T1 | MEDIUM | Lesson 26; the phase's own documentation prose would trip it |
| 10 | Make the F-113 `workflow_dispatch` a blocking phase-close item with named evidence, and add a `command -v pipx` guard that names the fallback (FM-10) | 33-02 T2 + 33-03 T3 | MEDIUM | A1 is the only unexecuted premise, and it has exactly one observation event |
| 11 | Fix the sleep-patching mechanism sentence and assert on the argument list, not `call_count` (FM-12) | 33-03 T2 | MEDIUM | The plan's stated mechanism is factually wrong; test is otherwise sound |
| 12 | State the phase-close pytest figure as an equality (392/1/1) rather than a floor (FM-13) | 33-03 T3 | MEDIUM | A floor cannot detect a deleted test |
| 13 | One sentence recording that the zizmor pin is not dependabot-covered and must be re-evaluated per milestone (FM-16) | 33-03 T3 | LOW | Unstated tolerance reads as coverage |

**Not amended, accepted on the merits:** FM-11 (heavy import — fails loudly, F-108's single-constant
rule is right), FM-14 (`uses:` substring scan — fail-safe, and a YAML dep is a worse trade),
FM-15 (dependabot comment shapes — the regex accepts every shape dependabot emits), plus the four
items in "What I could NOT break", none of which requires a plan change.

**Locked decisions this premortem reopens:** none. FM-04 extends a *gate's variable list*, not
F-111's secret inventory. FM-08 refines *how* F-117's coverage assertion reports, not whether it
exists. FM-02 says F-117's **intent** is right and its **named mechanism** is wrong — that is a
correction to a stated mechanism, in the F-114→F-103 correction-chain style, and should be
recorded as such rather than by editing F-117.
