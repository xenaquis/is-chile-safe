# Phase 33 (Security Posture) — Independent Re-Review After Fix Cycle 1 + F-126

**Reviewer:** independent adversarial re-reviewer (second pass, no deference to `33-REVIEW.md` or to the fixer's report)
**Range under review:** `ace8423..HEAD` (fix cycle 1 = `467e0a1`, `9e00a8d`, `46474d0`, `e5377a8`, `8d4896d`, plus the inline F-126 fix `baaab2e`/`5322f6a`)
**Whole-phase re-check:** `ed0d7c7..HEAD`
**Date:** 2026-08-05
**Working tree:** every reproduction below was run against the live tree and the tree was restored afterwards. Verified clean at the end of the session (`git status --porcelain` empty; both gates re-run at exit 0).

---

## Verdict

**CRITICAL: none. HIGH: none.**

The thing this re-review existed to find — a second regression planted by the fix cycle, in the pattern of Phase 30 cycle 1 and Phase 28 — **is not there**. I attacked the five specific surfaces the orchestrator flagged and could not break any of them. The two substantive findings below are one **MEDIUM** (an unfixed first-review item, ME-03, which the fix cycle did *not* create but did make asymmetric and which I reproduced as a live build-reddening false positive) and three **LOW**s (one of them a fresh, small documentation drift introduced by the very commit that was correcting documentation — the Phase 31 pattern, in miniature).

Notably, F-126 is not merely a patch: it **hardened** FM-01. `check-secret-hygiene.sh` now itself contains lines matching its own `PRINTENV_PATTERN` and `SECRETS_EXPR_PATTERN` (lines 104-105, the F-126 rationale comment). Before F-126 those lines were protected only by the single `--exclude="$SELF_NAME"` basename filter; they are now protected by that *and* the first-character comment test. The self-flag blocker is now double-guarded rather than single-guarded.

---

## What I attacked and could not break (negative results, stated plainly)

These are not findings. They are falsification attempts that failed, recorded so the next reviewer does not repeat them.

### 1. The combined `EXPOSURE_PATTERN` (`check-secret-hygiene.sh:47-51`) — CORRECT in ERE

Top-level alternation binds the four sub-patterns as four whole alternatives (`SECRET_NAMES`' internal `|` is safely enclosed in `(...)` in each). Proven empirically, not by reading: I planted a six-shape probe workflow in the real-tree scan path.

```
$ cat > .github/workflows/zz-tmp-probe.yml   # 6 live leak shapes + 1 heredoc-body shape
$ bash .github/scripts/check-secret-hygiene.sh
check-secret-hygiene.sh: canary armed (echo=1 secrets_expr=1 printenv=1 herestring=1 xtrace=1 curl=1 botocore=1)
::error file=...zz-tmp-probe.yml,line=4::possible secret exposure (...):       - run: echo "$DEEPSEEK_API_KEY"
::error file=...zz-tmp-probe.yml,line=5::possible secret exposure (...):       - run: echo "${{ secrets.OPENROUTER_API_KEY }}"
::error file=...zz-tmp-probe.yml,line=6::possible secret exposure (...):       - run: printenv R2_SECRET_ACCESS_KEY
::error file=...zz-tmp-probe.yml,line=7::possible secret exposure (...):       - run: cat <<< "$CF_HOOK"
::error file=...zz-tmp-probe.yml,line=8::possible secret exposure (...):       - run: echo "# $CF_DEPLOY_HOOK_URL"
::error file=...zz-tmp-probe.yml,line=9::possible secret exposure (...):       - run: printf '%s' "${R2_ACCESS_KEY_ID}"
```

All four sub-patterns fire independently through the combined regex, on secret names other than the canary's. `echo "# $CF_DEPLOY_HOOK_URL"` (line 8) fires — confirming the F-126 rationale's central claim that a first-*character* test cannot silence an `echo` of a `#`-prefixed string. Probe removed; tree restored.

**The `run: |` block-scalar question the orchestrator raised is answered: safe.** Inside a `run: |` body a line whose first non-whitespace character is `#` is a shell comment, so skipping it is semantically right. The only construct where a leading-`#` line inside `run: |` is *not* a comment is a heredoc body (see LO-02 below) — which is contrived enough not to justify weakening the skip.

### 2. All seven canary shapes arm independently — PROVEN, 7/7

I broke exactly one arming line at a time (`sed` neutralisation, `git checkout --` restore between each) and confirmed the script aborts naming *that* shape and only that shape:

```
--- BREAK: shape1 echo ---       echo=0 secrets_expr=1 printenv=1 herestring=1 xtrace=1 curl=1 botocore=1   rc=1
--- BREAK: shape1b secrets-expr - echo=1 secrets_expr=0 printenv=1 herestring=1 xtrace=1 curl=1 botocore=1   rc=1
--- BREAK: shape1c printenv ---  echo=1 secrets_expr=1 printenv=0 herestring=1 xtrace=1 curl=1 botocore=1   rc=1
--- BREAK: shape1d herestring -- echo=1 secrets_expr=1 printenv=1 herestring=0 xtrace=1 curl=1 botocore=1   rc=1
--- BREAK: shape3 curl ---       echo=1 secrets_expr=1 printenv=1 herestring=1 xtrace=1 curl=0 botocore=1   rc=1
--- BREAK: shape2 xtrace ---     echo=1 secrets_expr=1 printenv=1 herestring=1 xtrace=0 curl=1 botocore=1   rc=1
--- BREAK: shape4 botocore ---   echo=1 secrets_expr=1 printenv=1 herestring=1 xtrace=1 curl=1 botocore=0   rc=1
```

Baseline is `1` on every counter — no shape is armed by a line that also satisfies another shape's pattern (a cross-satisfied line would have shown a baseline of 2 somewhere, or a residual 1 after neutralisation). **The arming is exactly as strong as it reports.** This is the specific F-85 relocation the orchestrator asked me to hunt for, and it is not present.

### 3. `.yaml` globbing with `nullglob` (`check-secret-hygiene.sh:189-195`, `check-sha-pins.sh:27-33`) — CORRECT

`shopt -s nullglob` does **not** leak: it is unset on the very next line in both scripts, before any other glob is expanded (`.github/scripts/*.sh` at `check-secret-hygiene.sh:199` and `pipeline/*.py` at `:217` are both evaluated after `shopt -u`). Both scripts are invoked as `bash <script>` from `ci.yml:84,95`, so there is no caller shell state to clobber either. Both globs are now byte-for-byte the same construct as `lint-workflows.sh:40-48`, including the nullglob rationale comment.

Proven with a real `.yaml` workflow carrying both defect classes:

```
|SHA| ::error file=.github/workflows/zz-probe.yaml,line=4::uses: ref is not pinned to a 40-hex commit SHA: actions/checkout@v4
|SHA| ::notice::check-sha-pins.sh: examined 14 uses: lines; EXPECTED_MIN_COUNT is 13 -- this is a coverage floor, not a pin failure; ...
|HYG| ::error file=.github/workflows/zz-probe.yaml,line=5::possible secret exposure (...):       - run: echo "$DEEPSEEK_API_KEY"
```

`EXPECTED_MIN_COUNT`'s notice-on-overcount stays coherent: an added `.yaml` workflow produces a `::notice::` and `rc` driven purely by the pin verdict, not by the count. Correct behaviour. Probe removed; tree restored.

Also checked and clean: under `set -u`, `${#WORKFLOW_FILES[@]}` on an empty array is safe and both scripts exit **before** expanding an empty `"${arr[@]}"`. The script also survives `bash --posix` (rc=0).

### 4. LO-01's rewrite is genuinely falsifiable — PROVEN by 3 mutations

`test_inter_feed_courtesy_delay_never_before_first_feed` (`pipeline/tests/test_scrape_news.py:452-484`) now uses a 2-feed dict and asserts `[REQUEST_DELAY]`. I mutated `pipeline/scrape_news.py:232-238` three ways; **both** the rewritten test and its sibling `test_inter_feed_courtesy_delay` went red on all three:

| Mutation | Result |
|---|---|
| M1 — `if i > 0:` → `if True:` (always sleep) | both FAILED |
| M2 — `time.sleep(REQUEST_DELAY)` → `pass` | both FAILED |
| M3 — `time.sleep(REQUEST_DELAY)` → `time.sleep(0.001)` | both FAILED |

```
=== M1: drop the i>0 guard (always sleep) ===
FAILED pipeline\tests\test_scrape_news.py::test_inter_feed_courtesy_delay
FAILED pipeline\tests\test_scrape_news.py::test_inter_feed_courtesy_delay_never_before_first_feed
2 failed in 1.67s
```
(identical shape for M2 and M3). `pipeline/scrape_news.py` restored via `git checkout --` after each. The near-tautology is gone and the sibling is still non-vacuous. **LO-01 is properly closed.**

### 5. `DEPLOYMENT.md`'s HI-03 and ME-01 substantive claims are TRUE

**ME-01 — the four token-gated audits.** `DEPLOYMENT.md:308-316` names exactly `impostor-commit`, `ref-confusion`, `known-vulnerable-actions`, `stale-action-refs`. Verified against a real tokenless run:

```
$ unset GH_TOKEN GITHUB_TOKEN; uvx zizmor@1.10.0 --persona=regular .github/workflows/
 INFO zizmor: skipping impostor-commit: can't run without a GitHub API token
 INFO zizmor: skipping ref-confusion: can't run without a GitHub API token
 INFO zizmor: skipping known-vulnerable-actions: can't run without a GitHub API token
 INFO zizmor: skipping forbidden-uses: audit not configured
 INFO zizmor: skipping stale-action-refs: can't run without a GitHub API token
No findings to report. Good job! (2 ignored, 21 suppressed)
```

The list is **exactly right** — and correctly *excludes* `forbidden-uses`, which also self-skips but for an unrelated reason (not configured), not for want of a token. That is a precise distinction the doc got right. (One word is wrong: see LO-01 below.)

**HI-03 — the secret-scanning evidence.** `DEPLOYMENT.md:348-352` now cites `gh api repos/xenaquis/is-chile-safe/secret-scanning/alerts --jq 'length'`. Verified: returns `0`, exit 0. The doc's added retraction — that `open_issues_count` counts issues *and* pull requests and has no relationship to secret-scanning alerts — is correct and is the right kind of correction (it names the discredited evidence rather than quietly dropping it).

### 6. Regression sweep — CLEAN

- `git diff ace8423..HEAD --stat -- .github/workflows/ lint-workflows.sh fetch-lint-tools.sh require-env.sh check-heartbeat.sh push-with-rebase.sh` → **empty**. The fix cycle touched none of them. `news-pipeline.yml` / `cead-scraper.yml` push capability is untouched by construction.
- File modes: all `100644`, unchanged. No mode drift.
- Line endings: `check-secret-hygiene.sh`, `check-sha-pins.sh`, `canary-workflow.yml` all **LF**, no CRLF drift (repo is inside OneDrive, so this was worth checking).
- The canary fixture grew from 2 shapes to 5 in `canary-workflow.yml`; `canary-script.sh` and `canary_module.py` are byte-identical to their pre-fix-cycle state.
- `lint-workflows.sh` (which shellchecks `.github/scripts/*.sh`) exits 0 against the rewritten scripts, so the `shopt`/array/`eval` constructs the fix cycle added are shellcheck-clean.
- LO-03 (`eval` to set a fixed local flag) got *better*, not worse: F-126 deleted `_report_all`, removing one of the two `eval` sites. One remains at `:118`. Still cosmetic.
- LO-02 (`TestPersistCredentialsRegression` hardcoded per-file key counts) untouched, still cosmetic — the fix cycle did not change any workflow file, so nothing made it load-bearing.

---

## MEDIUM

### RR-M1 — `check-sha-pins.sh` fails the build on a commented-out `uses:` line (ME-03, unfixed, now demonstrably load-bearing)

**File:** `.github/scripts/check-sha-pins.sh:38, 53-69, 75-82`

`grep -rHn "uses:"` scans comment lines, and the parsing loop has no comment test — so a *commented-out* step is parsed as a live one, fails the SHA-pin check, and reddens the build. The first review classified ME-03 as an unfixed cosmetic issue about the coverage floor. It is not cosmetic; it is a live false positive, and I reproduced it:

```
$ cat > .github/workflows/zz-probe.yaml
# uses: actions/checkout@v4
jobs: {}
$ bash .github/scripts/check-sha-pins.sh
::error file=.github/workflows/zz-probe.yaml,line=1::uses: ref is not pinned to a 40-hex commit SHA: actions/checkout@v4
::notice::check-sha-pins.sh: examined 14 uses: lines; EXPECTED_MIN_COUNT is 13 -- ...
```

**Concrete failure scenario.** A developer temporarily disables a step the normal way — `# - uses: actions/upload-artifact@v4` — and CI fails with `uses: ref is not pinned to a 40-hex commit SHA`, an error that instructs them to SHA-pin a step that no longer runs. There is no way to satisfy the gate except by deleting the comment. Second-order: a comment mentioning `uses:` also inflates `count`, so the coverage floor of 13 can be satisfied by comments while a real step has been deleted — the exact silent-narrowing failure `EXPECTED_MIN_COUNT` exists to catch.

**Why the fix cycle escalated this.** After F-126, `check-secret-hygiene.sh` skips comment lines in **all four** checks. `check-sha-pins.sh`, sitting in the same job (`ci.yml:84` and `:95`), skips them in none. The two sibling gates now disagree about whether a `#` line is content, and the F-126 rationale comment (`check-secret-hygiene.sh:106-107`) explicitly names "a guard that bans documenting the rule it enforces" as the Phase 31 defect class — while its sibling still does exactly that.

**Suggested fix — validated, not merely plausible.** Add the same first-character test the sibling uses, at the top of the loop body at `:53`:

```bash
while IFS=: read -r file line content; do
  # ME-03: a commented-out `uses:` line is documentation, not a live step.
  stripped="${content#"${content%%[![:space:]]*}"}"
  case "$stripped" in "#"*) continue ;; esac
  count=$((count + 1))
```

I applied it and confirmed all three behaviours (fix reverted afterwards, tree clean):

```
=== comment-only .yaml probe ===  check-sha-pins.sh: examined 13 uses: lines (>= 13)   rc=0   <- false positive gone
=== clean tree ===                check-sha-pins.sh: examined 13 uses: lines (>= 13)   rc=0   <- floor still exact
=== real unpinned still caught === ::error ...not pinned to a 40-hex commit SHA...     rc=1   <- detection intact
lint-workflows(shellcheck) rc=0                                                              <- shellcheck-clean
```

Note the middle row: with comment lines excluded the count is still exactly 13, so `EXPECTED_MIN_COUNT` needs **no** adjustment — the current 13 real `uses:` lines happen to contain no commented ones today. That is luck, not design, and is precisely why the guard should go in now rather than after someone comments a step out.

---

## LOW

### RR-L1 — `DEPLOYMENT.md` says zizmor "silently skips" — it does not; it prints five INFO lines at default verbosity

**File:** `DEPLOYMENT.md:310` ("Without a `GH_TOKEN`, zizmor **silently** skips four audits")

The commit correcting a documentation defect introduced a small new one — the Phase 31 pattern the orchestrator warned about. At default verbosity (no `-v`), zizmor 1.10.0 prints the skip notices to stderr:

```
$ unset GH_TOKEN GITHUB_TOKEN; uvx zizmor@1.10.0 --persona=regular .github/workflows/ 2>&1 | grep -ci "skipping"
5
```

**Failure scenario.** A reader who trusts "silently" concludes there is no way to tell locally whether the token-gated audits ran, and does not look for the signal that is in fact printed on every run. The correct guidance is stronger than what the doc gives: *check for the `skipping … can't run without a GitHub API token` lines.* Fix: replace "silently skips" with "skips (printing `INFO zizmor: skipping <audit>: can't run without a GitHub API token`)". The first review's own wording ("silently runs 4 fewer audits", `33-REVIEW.md:205`) is the source of the word; it should not be inherited.

### RR-L2 — a leaking line inside a heredoc body whose first character is `#` is not detected

**File:** `.github/scripts/check-secret-hygiene.sh:110-120` (the comment skip), triggered via any `run: |` body

The one construct where a leading `#` inside `run: |` is *not* a shell comment is a heredoc body. Reproduced (this is the 7th shape in the probe from §1 above; it is the only one of seven that produced no `::error::`):

```yaml
      - run: |
          cat > gen.sh <<'INNER'
          # echo "$DEEPSEEK_API_KEY"
          INNER
          bash gen.sh
```

**Failure scenario.** A workflow generates a script file via heredoc, and a line of that generated script that begins with `#` — as a comment *in the generated file*, later stripped or reinterpreted — carries a secret expansion. Genuinely contrived: it requires a heredoc, an unquoted-or-expanded delimiter, and a `#`-leading line that leaks. **No fix recommended.** Any first-character heuristic has this blind spot, and closing it requires YAML+shell parsing whose false-positive cost (the F-126 regression, again) far exceeds this scenario's likelihood. Recorded so it is a known and accepted limit rather than an unexamined one. It should be added to `DEPLOYMENT.md`'s "Known Gaps" section.

### RR-L3 — the LO-01 fix ratifies ME-02's coupling in a test assertion

**Files:** `pipeline/tests/test_scrape_news.py:466` (`from pipeline.news.fulltext import REQUEST_DELAY`), `pipeline/scrape_news.py:221`

ME-02 (unfixed) observed that reading a float pulls `requests`/`trafilatura`/`tenacity` (`pipeline/news/fulltext.py:21-22`) onto the news cron's critical path. The LO-01 rewrite now imports that same constant from that same module **in the test**, so the eventual ME-02 remediation (moving `REQUEST_DELAY` to a dependency-free constants module) must now update a test import as well as the source. This is a one-line increase in remediation cost, not a defect — flagged only so ME-02's eventual fixer is not surprised, and so it is on record that the fix cycle marginally entrenched an unfixed finding.

---

## Coverage of the orchestrator's six attack items

| # | Item | Verdict |
|---|---|---|
| 1 | `EXPOSURE_PATTERN` + F-126 comment skip | **Clean.** ERE correct, 4/4 sub-patterns fire independently (§1). Block-scalar concern resolved; one contrived heredoc blind spot → RR-L2. |
| 2 | `.yml`+`.yaml` globbing, `nullglob` | **Clean.** No nullglob leak, globs equivalent to `lint-workflows.sh:40-48`, overcount notice coherent (§3). |
| 3 | Canary — seven shapes, independent arming | **Clean, 7/7 proven by one-at-a-time neutralisation** (§2). No cross-satisfied arming line. |
| 4 | LO-01 rewrite falsifiability | **Clean, 3/3 mutations red**, sibling still red too (§4). |
| 5 | DEPLOYMENT.md HI-03/ME-01 claims | **Substantively true and precisely scoped** (§5); one word wrong → RR-L1. |
| 6 | ME-03 / LO-02 / LO-03 | ME-03 **escalated to MEDIUM** (RR-M1, reproduced live false positive). LO-02 still cosmetic. LO-03 improved (one `eval` site deleted). |
| 7 | Regression sweep | **Clean** — no untouched-script drift, no push-capability change, no mode/EOL/fixture drift (§6). |

## Recommended disposition

- **Fix now:** RR-M1 (validated four-line patch, no `EXPECTED_MIN_COUNT` change needed).
- **Fix now, trivial:** RR-L1 (one word in `DEPLOYMENT.md:310`).
- **Document, do not fix:** RR-L2 → `DEPLOYMENT.md` "Known Gaps".
- **Note only:** RR-L3, carried with ME-02.
- **No CRITICAL or HIGH finding exists.** Fix cycle 1 plus F-126 did not plant a second regression. Phase 33's fix cycle is the first in four phases that did not trade one defect class for another.
