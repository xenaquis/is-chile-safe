---
phase: 33-security-posture
reviewed: 2026-08-05T00:00:00Z
depth: deep
files_reviewed: 13
files_reviewed_list:
  - .github/dependabot.yml
  - .github/scripts/check-secret-hygiene.sh
  - .github/scripts/check-sha-pins.sh
  - .github/scripts/fixtures/secret-hygiene-canary/canary-script.sh
  - .github/scripts/fixtures/secret-hygiene-canary/canary-workflow.yml
  - .github/scripts/fixtures/secret-hygiene-canary/canary_module.py
  - .github/workflows/cead-scraper.yml
  - .github/workflows/ci.yml
  - .github/workflows/deploy-on-code.yml
  - .github/workflows/heartbeat.yml
  - .github/workflows/news-pipeline.yml
  - .github/workflows/r2-archive.yml
  - DEPLOYMENT.md
  - pipeline/scrape_news.py
  - pipeline/tests/test_scrape_news.py
  - pipeline/tests/test_workflow_guards.py
findings:
  critical: 0
  blocker: 0
  high: 3
  medium: 3
  low: 3
  total: 9
status: issues_found
---

# Phase 33: Code Review Report (Security Posture)

**Depth:** deep · **Status:** issues_found · **Critical:** 0

## Summary

The phase's headline risk — breaking a live cron — did **not** materialize. I verified
from the tree, not the plans, that `news-pipeline.yml` and `cead-scraper.yml` both retain
`permissions: contents: write` + `issues: write`, both retain the persisted checkout
credential (no `persist-credentials` key), and both `# zizmor: ignore[artipacked]`
suppressions are load-bearing (removing news-pipeline's makes zizmor exit 13, proven
below). All ten `gh issue` steps still receive `GH_TOKEN`, so the six
`persist-credentials: false` checkouts break nothing. Phase 32's five instruments
(`lint-workflows.sh`, `fetch-lint-tools.sh`, `require-env.sh`, `check-heartbeat.sh`,
`push-with-rebase.sh`) are untouched — confirmed absent from `git diff ed0d7c7..HEAD --stat`.
The `command -v pipx` guard is a **separate, hard-failing step** (`exit 1`), not an `if:`
skip — SEC-04's coverage does not silently evaporate. `pipeline/news/fulltext` has no
circular import with `gnews_decoder` (the back-import is lazy, inside `_get_user_agent()`).
The courtesy-delay test is genuinely load-bearing (mutation-proven red below). All 13
`uses:` refs counted and matched against DEPLOYMENT.md's claim (checkout x8, setup-python
x4, setup-node x1).

What the orchestrator's green run **does not** cover, and what I found, is that the two
new gates are narrower than their own documentation and their own canaries claim. Both
new gates are blind to `.yaml` workflow files — reintroducing precisely the L-01 defect
Phase 32 fixed in `lint-workflows.sh` — and `check-secret-hygiene.sh` misses the single
most canonical Actions secret-leak shape (`echo "${{ secrets.X }}"`) while its canary is
structurally incapable of revealing the gap. Both are proven with executed reproductions.

---

## HIGH

### HI-01: `check-secret-hygiene.sh` misses `${{ secrets.X }}`, `printenv`, and here-string leaks; the canary cannot detect the gap

**File:** `.github/scripts/check-secret-hygiene.sh:76` (`ECHO_PATTERN`), canary at
`.github/scripts/fixtures/secret-hygiene-canary/canary-workflow.yml:16`

`ECHO_PATTERN="(echo|printf)[^|]*\$\{?(${SECRET_NAMES})\b"` requires the literal `$` or
`${` to be immediately followed by a secret *name*. The GitHub Actions expression form
`${{ secrets.DEEPSEEK_API_KEY }}` interposes `{ secrets.` and does not match. Neither
`printenv <SECRET>` nor `cat <<< "$CF_HOOK"` is covered by any of the four shapes.

**Reproduction (executed):** three real leak shapes injected into `heartbeat.yml`'s
`steps:` block:

```
      - name: LEAK A
        run: echo "${{ secrets.DEEPSEEK_API_KEY }}"
      - name: LEAK B
        run: printenv OPENROUTER_API_KEY
      - name: LEAK C
        run: cat <<< "$CF_HOOK"
```

```
$ bash .github/scripts/check-secret-hygiene.sh
check-secret-hygiene.sh: canary armed (echo=1 xtrace=1 curl=1 botocore=1)
check-secret-hygiene.sh: clean -- no log-hygiene findings against the real tree
HYGIENE_EXIT=0
```

(Tree restored; `git status --porcelain` empty.) A control run with the `${DEEPSEEK_API_KEY}`
form *did* fire, confirming the gate is armed for exactly one of the four written forms.

The aggravating factor is FM-06: the canary fixture only exercises `run: echo "$DEEPSEEK_API_KEY"`,
so "canary armed (echo=1 …)" is printed while three sibling shapes of the *same* check
pass silently. The canary proves the grep runs; it does not prove the pattern is adequate.
This is the F-85 defect class relocated one layer down — a positive control that cannot
fail for the reason the instrument would actually fail.

**Failure scenario:** a future debugging step `run: echo "${{ secrets.OPENROUTER_API_KEY }}"`
lands in a PR, CI's SEC-05 gate reports "clean", and the phase's stated deliverable
("fails the build on any of four named log-hygiene risk shapes") is false in a public repo.

**Fix:** extend `ECHO_PATTERN` to cover the expression and env-dump forms, and add each new
shape to the canary fixture so the arming check is per-shape and non-vacuous:

```bash
ECHO_PATTERN="(echo|printf)[^|]*(\\\$\\{?|\\\$\\{\\{[[:space:]]*secrets\\.)(${SECRET_NAMES})\\b"
ENVDUMP_PATTERN="(printenv|env[[:space:]]*\$|env[[:space:]]+\\|)|printenv[[:space:]]+(${SECRET_NAMES})\\b"
```

Add to `canary-workflow.yml` (and bump the arming check to require each shape ≥ 1):

```yaml
      - name: leak via Actions expression (shape 1b)
        run: echo "${{ secrets.OPENROUTER_API_KEY }}"
      - name: leak via printenv (shape 1c)
        run: printenv DEEPSEEK_API_KEY
```

---

### HI-02: both new gates are blind to `.yaml` workflow files — direct regression of Phase 32's L-01 lesson

**File:** `.github/scripts/check-sha-pins.sh:244`, `.github/scripts/check-secret-hygiene.sh:188,193,198`

Both scan `.github/workflows/*.yml` only. `lint-workflows.sh:42-48` explicitly fixed this
exact defect in Phase 32 with a documented comment:

> `# L-01: GitHub accepts both .yml and .yaml for workflow files; a *.yml-only glob would silently skip a .yaml workflow from the very gate meant to be un-skippable.`

Both new gates reintroduce it. Worse, `check-sha-pins.sh`'s coverage floor
(`EXPECTED_MIN_COUNT=13`) cannot catch it: a `.yaml` workflow *adds* refs the scan never
sees, so `count` stays at exactly 13 and the floor reports success.

**Reproduction (executed):** created `.github/workflows/evil.yaml` containing an unpinned
`uses: actions/checkout@v1` and `run: echo "$DEEPSEEK_API_KEY"` — a file GitHub would
happily execute:

```
--- check-sha-pins ---
check-sha-pins.sh: examined 13 uses: lines (>= 13)
SHA_EXIT=0
--- check-secret-hygiene ---
check-secret-hygiene.sh: canary armed (echo=1 xtrace=1 curl=1 botocore=1)
check-secret-hygiene.sh: clean -- no log-hygiene findings against the real tree
HYG_EXIT=0
```

(File removed; tree clean.) Note the `echo "$DEEPSEEK_API_KEY"` in that file is the *exact*
shape the canary proves the gate detects — it is missed purely on extension.

**Failure scenario:** any future workflow authored as `.yaml` (a coin-flip convention choice)
is permanently exempt from both SEC-02 and SEC-05, with a green check, and no coverage
floor or canary will ever report it.

**Fix:** mirror `lint-workflows.sh`'s own construction in both scripts:

```bash
shopt -s nullglob
targets=(.github/workflows/*.yml .github/workflows/*.yaml)
shopt -u nullglob
[ "${#targets[@]}" -gt 0 ] || { echo "::error::no workflow files found -- refusing to report a clean tree"; exit 1; }
grep -rHn "uses:" "${targets[@]}" >"$tmp"
```

---

### HI-03: DEPLOYMENT.md asserts a security posture from evidence that cannot produce it

**File:** `DEPLOYMENT.md` (SEC-01/SEC-05 re-verification paragraph, ~line 624)

> `0 secret-scanning alerts open (visible via open_issues_count distinct from alert count -- confirmed no secret_scanning_alert notification exists in this session's gh api output).`

`gh api repos/xenaquis/is-chile-safe` returns repository metadata; `open_issues_count` is
the count of open issues + PRs and has no relationship whatsoever to secret-scanning
alerts. Secret-scanning alerts live at `GET /repos/{owner}/{repo}/secret-scanning/alerts`,
which this session did not query. The parenthetical is an evidence chain that cannot
support its own conclusion, and it is load-bearing for a *security* claim — a future reader
auditing SEC-01 will read "0 alerts open, verified" and not re-check.

This is Phase 31's documented lesson ("a phase that writes documentation writes drift")
recurring, but on a security assertion rather than a mechanical one.

**Failure scenario:** a real secret-scanning alert exists (or later appears) and the
milestone-close audit skips re-querying because DEPLOYMENT.md records it as verified zero.

**Fix:** either run the real query and cite it, or strike the claim:

```
0 secret-scanning alerts open -- verified via
`gh api repos/xenaquis/is-chile-safe/secret-scanning/alerts --jq 'length'` (2026-08-05, returned 0).
```

Remove the `open_issues_count` parenthetical entirely; it is not evidence of anything.

---

## MEDIUM

### ME-01: DEPLOYMENT.md claims the local zizmor gate is "the exact same" as CI's — it silently runs 4 fewer audits

**File:** `DEPLOYMENT.md` ("Local pre-push gate" paragraph, ~line 589); `.github/workflows/ci.yml:88-92`

> `run uvx zizmor@1.10.0 --persona=regular .github/workflows/ locally … using the exact same pinned version as CI's pipx run zizmor==1.10.0 step`

Same *version*, materially different *audit set*. CI's step sets
`GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`; the documented local command sets nothing.

**Reproduction (executed, local run):**

```
 INFO zizmor: skipping impostor-commit: can't run without a GitHub API token
 INFO zizmor: skipping ref-confusion: can't run without a GitHub API token
 INFO zizmor: skipping known-vulnerable-actions: can't run without a GitHub API token
 INFO zizmor: skipping stale-action-refs: can't run without a GitHub API token
```

Four audits skip locally, three of which (`impostor-commit`, `known-vulnerable-actions`,
`stale-action-refs`) are precisely the ones that guard the SHA pins this phase just
introduced.

**Failure scenario:** a maintainer bumps a pin, runs the documented local gate, sees green,
pushes to `master` — where `ci.yml` has no `push` trigger (F-95) — and the token-gated
audits never run at all on that ref. The "local pre-push gate" is presented as equivalent
coverage and is not.

**Fix:** document the token requirement explicitly.

```
uvx zizmor@1.10.0 --persona=regular .github/workflows/
```
→
```
GH_TOKEN="$(gh auth token)" uvx zizmor@1.10.0 --persona=regular .github/workflows/
```
and add: "without `GH_TOKEN`, zizmor skips `impostor-commit`, `ref-confusion`,
`known-vulnerable-actions`, and `stale-action-refs` — a tokenless local pass is NOT
equivalent to CI's."

---

### ME-02: the courtesy delay drags `requests`/`trafilatura`/`tenacity` onto the news cron's critical path to read a float

**File:** `pipeline/scrape_news.py:221`; `pipeline/requirements.txt:14` (`trafilatura`, unpinned)

`from pipeline.news.fulltext import REQUEST_DELAY` executes `fulltext.py:21-28`, which hard-imports
`requests`, `trafilatura`, and `tenacity` at module load — verified:

```
$ python -c "import importlib,sys; m=importlib.import_module('pipeline.news.fulltext'); print(m.REQUEST_DELAY); print([k for k in sys.modules if k in ('requests','trafilatura','tenacity')])"
1.5
['requests', 'trafilatura', 'tenacity']
```

The 6-hourly news cron previously imported none of these. `trafilatura` is **unpinned** in
`pipeline/requirements.txt`, and dependabot's `pip` ecosystem does not produce bump PRs for
unpinned entries — so `pip install -r pipeline/requirements.txt`
(`news-pipeline.yml:62`) resolves whatever trafilatura released that morning.

Failure is at least loud (`scrape_news.py:389` `except Exception` → `return 1` → alert
issue), but it is a broad handler that reports "pipeline failed", not "dependency broke",
and it is a brand-new failure mode acquired in exchange for the number `1.5`.

**Failure scenario:** a trafilatura release with a bad transitive dep (or a `lxml` ABI
mismatch) makes the news cron exit 1 every 6 hours until someone reads the traceback,
despite the pipeline needing zero full-text functionality.

**Fix:** define the constant where it is used, or pin the dependency. Preferred:

```python
# pipeline/news/feeds.py (or scrape_news.py module scope)
REQUEST_DELAY = 1.5  # SEC-06/F-108 -- same courtesy interval as fulltext.py
```
and have `fulltext.py` import it from there, inverting the dependency. At minimum, pin
`trafilatura==<current>` in `pipeline/requirements.txt` so dependabot covers it.

---

### ME-03: `check-sha-pins.sh`'s scan and coverage floor both count comment lines

**File:** `.github/scripts/check-sha-pins.sh:244,259-288`

`grep -rHn "uses:"` is an unanchored substring match with no comment filter — unlike
`check-secret-hygiene.sh`, which added `_report_noncomment` for exactly this reason (FM-09),
and unlike `TestPersistCredentialsRegression._persist_credentials_key_lines`, which strips
`#` lines. The inconsistency is within this one phase.

Two consequences: (a) a prose comment such as `# the old uses: actions/checkout@v7 line` becomes
a false BLOCKER (`sed` extracts `actions/checkout@v7`, fails the 40-hex test); (b) the same
comment inflates `count`, so the `EXPECTED_MIN_COUNT=13` floor can be satisfied by commentary
while a real ref was deleted — the floor is spoofable by the very comments SEC-02 mandates
(`# vN.N.N`).

**Failure scenario:** a maintainer documents a pin change in a workflow comment; CI goes red
with "malformed uses: line" on a comment, or the floor silently absorbs a lost step.

**Fix:** skip comment lines in the read loop, mirroring the sibling script:

```bash
while IFS=: read -r file line content; do
  stripped="${content#"${content%%[![:space:]]*}"}"
  case "$stripped" in "#"*) continue ;; esac
  count=$((count + 1))
  ...
```

---

## LOW

### LO-01: `test_inter_feed_courtesy_delay_never_before_first_feed` is near-tautological

**File:** `pipeline/tests/test_scrape_news.py:418-439`

With `_TEST_FEEDS` holding exactly one entry (`test_scrape_news.py:88-90`), the only
implementation change this test can detect is deletion of the `if i > 0:` guard. It passed
unchanged under my mutation that removed `time.sleep(REQUEST_DELAY)` entirely — i.e. it
contributes no signal on whether the delay exists, only on where it starts. It is not
worthless, but its docstring ("no delay before the first feed") overstates its reach, and
the bare `assert mock_sleep.call_args_list == []` will go red on any future un-mocked sleep
anywhere in `main()`. **Fix:** assert against a ≥2-feed dict with an explicit
`[REQUEST_DELAY]` expectation, which subsumes both properties in one non-vacuous assertion.

*(For contrast, `test_inter_feed_courtesy_delay` IS load-bearing — proven by mutating
`time.sleep(REQUEST_DELAY)` → `pass`: `assert [] == [1.5, 1.5]`, 1 failed.)*

### LO-02: `TestPersistCredentialsRegression` hardcodes per-file key counts

**File:** `pipeline/tests/test_workflow_guards.py:770-775`

`_MUST_HAVE_FALSE = {"ci.yml": 3, ...}` goes red on any legitimately added job, turning a
security guard into a maintenance tax that trains maintainers to edit the assertion. **Fix:**
assert the *property* — every `uses: actions/checkout@` step in a non-pushing workflow is
followed by `persist-credentials: false` — rather than a magic count; keep the explicit
allow-list only for the two pushing crons.

### LO-03: `eval` used to set a fixed local flag

**File:** `.github/scripts/check-secret-hygiene.sh:125,138`

`eval "$fail_var=1"` where `fail_var` is always the literal `fail`. `eval` here buys nothing
and is a code-injection shape in a security script. **Fix:** drop the third parameter and
assign the global directly (`fail=1`), or use `declare -n ref="$fail_var"; ref=1`.

---

## Verified-Clean (checked, no finding)

- **Live crons intact.** `news-pipeline.yml:16-18` and `cead-scraper.yml:30-32` retain
  `contents: write` + `issues: write`; neither carries a `persist-credentials` key; both
  `# zizmor: ignore[artipacked]` suppressions proven load-bearing — stripping
  news-pipeline's produced `warning[artipacked] … news-pipeline.yml:32:9`, `ZIZMOR_EXIT=13`.
- **pipx guard is loud, not silent.** `ci.yml:90` is a standalone step ending in `exit 1`,
  with no `if:` or `continue-on-error:`. SEC-04 cannot skip green.
- **No circular import.** `gnews_decoder.py:36-45` back-imports `fulltext.USER_AGENT` lazily
  inside a function with a fallback; `import pipeline.news.fulltext` succeeds standalone.
- **Phase 32 instruments untouched.** `lint-workflows.sh`, `fetch-lint-tools.sh`,
  `require-env.sh`, `check-heartbeat.sh`, `push-with-rebase.sh` absent from the phase diffstat.
- **All 10 `gh issue` steps still receive `GH_TOKEN`** — `persist-credentials: false` on
  heartbeat/r2-archive/deploy-on-code/ci breaks no `gh` call (they read env, not git config).
- **DEPLOYMENT.md ref counts are accurate.** Measured: checkout ×8, setup-python ×4,
  setup-node ×1 = 13, matching both the prose and `EXPECTED_MIN_COUNT`.
- **Dependabot paths resolve.** `pipeline/requirements.txt` and `site/package.json` both exist.
- **Canary fixtures are not double-scanned.** `.github/scripts/*.sh`, `.github/workflows/*.yml`,
  and `pipeline/*.py` are non-recursive globs; `lint-workflows.sh:38` shellchecks
  `.github/scripts/*.sh` only. No self-inflicted permanent finding.

---

_Reviewer: Claude (gsd-code-reviewer) · Depth: deep · Tree restored clean after every falsification (`git status --porcelain` empty)._
