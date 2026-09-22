# Phase 33: Security Posture - Research

**Researched:** 2026-08-05
**Domain:** GitHub Actions supply-chain hardening (SHA-pinning, permissions, dependabot, static Actions scanning, secret log-hygiene, scraping courtesy)
**Confidence:** HIGH (all claims verified by direct execution against this repo's tree or against official docs; two items degrade to CITED/ASSUMED, flagged below)

## Summary

This phase closes five mechanical gaps in a GitHub Actions surface that already has strong CRON-01..07 discipline from Phase 32: (1) 13 `uses:` refs need SHA-pinning — **not 11 as F-103/F-104 assumed**, see the corrected count below; (2) five jobs need job-level `permissions:` blocks (F-106, unchanged); (3) `.github/dependabot.yml` does not exist and needs three ecosystem blocks; (4) `zizmor` needs to run in CI via `pipx run zizmor==1.10.0` (F-112 supersedes the `uvx`-in-CI premise — `uv`/`uvx` are not preinstalled on `ubuntu-latest`, `pipx` is); (5) one real courtesy-delay gap exists in `pipeline/scrape_news.py`'s 9-feed loop, and clustering is confirmed by code inspection to add zero fetch volume (Phase 26 was a NO-GO, `clustering.py` is never imported by `scrape_news.py`).

Every proposed check in this document was executed against the real tree during research, not merely described: the SHA-pin gate fires on all 13 current unpinned refs and stays silent on a correctly-pinned fixture; the secret-log-hygiene grep returns clean on the real tree and was proven to fire on a planted `echo $DEEPSEEK_API_KEY`; zizmor's exit-code table was confirmed against its own docs (11-14 for findings, distinct from 1-3 for errors) so a "canary" falsification analogous to `lint-workflows.sh`'s SC2034/SC2086 check is possible for zizmor too.

**Primary recommendation:** SHA-pin all 13 `uses:` refs with `# vN.N.N` comments using the exact SHAs already resolved in F-104/F-111 (reverified live against the GitHub API in this session and unchanged); add the five job-level `permissions:` blocks from F-106 verbatim; ship `.github/dependabot.yml` with three ecosystems; add a `zizmor` step to `ci.yml`'s existing `lint-workflows` job using `pipx run zizmor==1.10.0 --persona=regular` with `GH_TOKEN` set and the two accepted `artipacked` findings suppressed in-file; add a 1.5s inter-feed `time.sleep` to `pipeline/scrape_news.py`'s feed loop, costing 8 × 1.5s = 12s per run × 4 runs/day = 48s/day of added wall-clock time.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SHA-pinning / permissions / dependabot / zizmor | CI/CD (GitHub Actions config) | — | Pure workflow-YAML supply-chain hardening; no application tier touched |
| Secret log-hygiene check | CI/CD (GitHub Actions config) + Build tooling | Python pipeline (log statements) | The check itself is a CI gate script; the risk surface it audits spans both `.yml`/`.sh` (workflow layer) and `pipeline/*.py` (application layer, via `logger.info`/`logger.warning` calls that could interpolate a URL) |
| Courtesy delay (SEC-06) | Python pipeline (`pipeline/scrape_news.py`) | — | Runtime behavior of the scraper, not a CI concern |

This phase has no frontend (`site/`) or data (`data/`) tier involvement, consistent with the hard constraints.

## Package Legitimacy Audit

No new Python or npm packages are installed by this phase's changes. `zizmor` is invoked ephemerally via `pipx run` (never added to `pipeline/requirements.txt`, per SEC-04 and CLAUDE.md's explicit prohibition) and via `uvx` locally — both are execute-in-place invocations, not dependency additions, so the standard Package Legitimacy Gate (slopcheck / registry-version verification for installed deps) does not apply. For completeness:

| Tool | Registry | Version pinned | Install method | Verdict |
|------|----------|----------------|-----------------|---------|
| zizmor | PyPI (`zizmor`) | 1.10.0 (F-109, reconfirmed) | `pipx run` (CI) / `uvx` (local) — ephemeral, never in requirements.txt | Not gated by slopcheck — zizmor is the OWASP/GitHub-ecosystem-endorsed Actions scanner (10k+ stars, `zizmorcore` org, referenced by GitHub's own blog); treat as `[CITED: docs.zizmor.sh]` |

**Packages removed due to slopcheck verdict:** none — no new installed dependency in this phase.
**Packages flagged as suspicious:** none.

## Correction to Pre-Planning Facts (read before using F-103/F-104)

**F-103/F-104's "11 `uses:` refs" count is WRONG. The verified count is 13.**

Verified this session via `grep -rHn "uses:" .github/workflows/*.yml` [VERIFIED: repo grep, executed this session] — full output:

```
.github/workflows/cead-scraper.yml:44:      - uses: actions/checkout@v7
.github/workflows/cead-scraper.yml:54:      - uses: actions/setup-python@v7
.github/workflows/ci.yml:17:      - uses: actions/checkout@v7
.github/workflows/ci.yml:19:      - uses: actions/setup-node@v7
.github/workflows/ci.yml:38:      - uses: actions/checkout@v7
.github/workflows/ci.yml:40:      - uses: actions/setup-python@v7
.github/workflows/ci.yml:55:      - uses: actions/checkout@v7
.github/workflows/deploy-on-code.yml:51:      - uses: actions/checkout@v7
.github/workflows/heartbeat.yml:44:      - uses: actions/checkout@v7
.github/workflows/news-pipeline.yml:32:      - uses: actions/checkout@v7
.github/workflows/news-pipeline.yml:55:      - uses: actions/setup-python@v7
.github/workflows/r2-archive.yml:21:      - uses: actions/checkout@v7
.github/workflows/r2-archive.yml:43:      - uses: actions/setup-python@v7
```

Corrected tally: **`actions/checkout@v7` × 8** (not 7 — `ci.yml` alone has 3, one per job: `frontend`, `pipeline`, `lint-workflows`), **`actions/setup-python@v7` × 4** (not 3 — `cead-scraper.yml`, `ci.yml`, `news-pipeline.yml`, `r2-archive.yml`), **`actions/setup-node@v7` × 1** (unchanged). 8+4+1 = **13**.

The pinned SHAs themselves (F-104/F-111) are still correct and were reverified live via the GitHub API this session:

| Tag | Resolved SHA (reverified live) |
|-----|-------------------------------|
| `actions/checkout@v7` | `3d3c42e5aac5ba805825da76410c181273ba90b1` [VERIFIED: GitHub API `GET /repos/actions/checkout/git/refs/tags/v7`, executed this session] |
| `actions/setup-python@v7` | `5fda3b95a4ea91299a34e894583c3862153e4b97` [VERIFIED: GitHub API, same method] |
| `actions/setup-node@v7` | `820762786026740c76f36085b0efc47a31fe5020` [VERIFIED: GitHub API, same method] |

**Why this matters for planning:** a plan written against "11 refs, 7+3+1" will undercount `ci.yml`'s three separate checkout steps (one per job) and miss one `setup-python` instance. The planner must pin all 13 occurrences, using the same three SHA/comment pairs above repeated at the correct line for each occurrence — the pin itself is identical everywhere the tag is identical, only the count of edit sites was wrong.

## 1. SHA-Pinning Mechanics + Falsifiable Gate

### Pin format

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

Two things must both be verified independently for a real tag→SHA pin: (a) the current SHA the tag points to (already resolved above), and (b) the human-readable version string for the comment. `actions/checkout`'s `v7` tag currently resolves to release `v7.0.1` — verify with `git ls-remote --tags https://github.com/actions/checkout | grep v7` or the GitHub Releases API before writing the comment, since the comment is documentation for humans/dependabot, not machine-checked by actionlint.

`actionlint` has no opinion on whether a `uses:` ref is a tag or a SHA — it validates YAML/expression syntax only, so SHA pins with trailing `# vN.N.N` comments pass `actionlint` unchanged [VERIFIED: `lint-workflows.sh` ran clean against every workflow in this repo both before and is expected to after re-pinning, since neither `-shellcheck` nor the default rule set inspects `uses:` ref format]. `zizmor`'s `unpinned-uses` audit is the tool that specifically checks this — after pinning, that audit's findings for these 13 lines should disappear from a zizmor scan.

### Falsifiable gate — proven both directions this session

A grep/sed-based checker was written to a real file (not embedded in a shell-quoted `node -e` — this repo's git-bash silently corrupts regex escapes like `\b` inside shell-quoted `node -e`, F-36) and executed three times:

```bash
#!/usr/bin/env bash
# .github/scripts/check-sha-pins.sh (proposed)
set -euo pipefail
fail=0
while IFS=: read -r file line content; do
  ref="$(printf '%s' "$content" | sed -n 's/.*uses:[[:space:]]*\([^[:space:]#]*\).*/\1/p')"
  if [[ "$ref" != *@* ]]; then
    echo "::error file=$file,line=$line::malformed uses: line, no @ref: $content"; fail=1; continue
  fi
  sha="${ref##*@}"
  if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "::error file=$file,line=$line::uses: ref is not pinned to a 40-hex commit SHA: $ref"
    fail=1
  elif ! printf '%s' "$content" | grep -qE '#[[:space:]]*v[0-9]+(\.[0-9]+){0,2}'; then
    echo "::error file=$file,line=$line::SHA-pinned ref missing a '# vN.N.N' version comment: $content"
    fail=1
  fi
done < <(grep -rHn "uses:" .github/workflows/*.yml)
exit "$fail"
```

**Critical gotcha found and fixed live:** `grep -rn` on a single-file glob match does **not** print the filename prefix unless `-H`/`--with-filename` is forced (POSIX grep suppresses the filename when only one file is being searched, and `.github/workflows/*.yml` can expand to a single match during iterative testing). Without `-H` the `IFS=:` field-split misparses `file`/`line`/`content` silently (observed: `file=4`, `line="      - uses"`, garbled content) — this is exactly the class of defect this repo's `lint-workflows.sh` canary exists to catch for a different tool (F-85), reproduced here for a new script during research. **The gate as written above (with `-H`) is confirmed correct.**

**What makes it fire:** any `uses:` value whose `@`-suffix is not exactly 40 lowercase hex characters (a tag like `@v7`, a branch, a short SHA, or a moving alias like `@main`), OR a 40-hex SHA with no trailing `# vN.N.N`-shaped comment.

**What must leave it silent:** `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` — full 40-hex SHA + version comment.

**Executed proof, both directions, this session:**
- Against the **real tree**: fires on all 13 current `uses:` lines (all still `@v7`-style tags) — exit 1. [VERIFIED: executed]
- Against a **fixture with a correct pin** (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`): exit 0, no output. [VERIFIED: executed]
- Against a **fixture with the current unpinned form** (`actions/checkout@v7`): exit 1 with the expected error. [VERIFIED: executed]

**Integration point:** append as a step in `ci.yml`'s existing `lint-workflows` job, calling a new `.github/scripts/check-sha-pins.sh` (mirroring the existing `lint-workflows.sh` pattern — a real script file, shellchecked by the same `.github/scripts/*.sh` glob `lint-workflows.sh` already shellchecks at line 38). Do not duplicate `lint-workflows.sh`'s own responsibilities (actionlint + shellcheck); this is a new, narrower check that composes alongside it.

## 2. `.github/dependabot.yml`

No file exists today at `.github/dependabot.yml` [VERIFIED: `ls .github/` shows only `scripts/` and `workflows/`, executed this session]. Real paths confirmed: `pipeline/requirements.txt` (pip) and `site/package.json` (npm), both at those exact relative paths [VERIFIED: `find`, executed this session].

Schema verified against GitHub's current dependabot-options-reference and dependabot-version-updates docs [CITED: docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference]:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      github-actions:
        patterns:
          - "*"

  - package-ecosystem: "pip"
    directory: "/pipeline"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "npm"
    directory: "/site"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

Notes:
- `directory` is relative to the repo root and must point at the directory *containing* the manifest (`/pipeline` for `pipeline/requirements.txt`, `/site` for `site/package.json`), not the file path itself — this is documented GitHub behavior [CITED: docs.github.com dependabot-version-updates].
- `github-actions` ecosystem scans `.github/workflows/*.yml` for `uses:` lines regardless of `directory` value; GitHub's docs specify `directory: "/"` as the conventional value for this ecosystem even though the actual files it scans live under `.github/workflows/`.
- `open-pull-requests-limit: 5` is the GitHub default; setting it explicitly documents the choice rather than relying on an implicit default, matching this repo's convention (F-102-style: state defaults explicitly, don't rely on silence).
- Grouping (`groups:`) is optional; a single `github-actions` group of `patterns: ["*"]` is a reasonable choice given only 3 distinct actions (`checkout`, `setup-python`, `setup-node`) — one PR per weekly cycle instead of up to 3. **This is Claude's-discretion territory** (no CONTEXT.md exists for this phase at research time — see Open Questions) — the planner may omit grouping and accept up to 3 separate PRs if simplicity is preferred.
- `commit-message` prefix customization is optional and has no functional effect here; omit unless the project later adopts commitlint-style conventions (none exist today — CLAUDE.md's Conventions section is explicitly empty).
- **This pairing is why SHA-pinning is safe at all (F-104):** Dependabot's `github-actions` ecosystem opens a PR bumping the pinned SHA (with the tag comment updated) whenever `actions/checkout`, `setup-python`, or `setup-node` cut a new release — without it, SHA pins would silently rot and never receive security patches.

## 3. zizmor in CI

### Invocation form — F-112 supersedes F-109's `uvx`-in-CI premise

**CI (per F-112, this session's coordinator update):** `pipx run zizmor==1.10.0 ...` — not `uvx`. Rationale confirmed: `uv`/`uvx` are not part of the standard GitHub-hosted `ubuntu-latest` toolset; adding them would require `astral-sh/setup-uv`, a genuinely third-party action (F-103's corrected count is still zero third-party actions today — see the correction section above, which only revises the *count* of first-party refs, not the third-party-action-count claim). `pipx`, by contrast, ships preinstalled: **pipx 1.16.0** is listed in the `actions/runner-images` Ubuntu 24.04 (current `ubuntu-latest`) readme's installed-software table [CITED: github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md — fetched this session]. **This is a claim about the runner image that cannot be verified by executing anything locally** (this dev machine has `uvx` but no `pipx` installed — confirmed: `command -v pipx` returned nothing, `command -v uvx` resolved to a conda-installed binary, executed this session) — it rests entirely on the runner-images repo's own published manifest, which is the closest thing to an authoritative source available (GitHub publishes and version-pins these images itself) but is not something this research session could independently execute-and-confirm the way the SHA-pin gate was. Tag this premise `[CITED: actions/runner-images Ubuntu2404-Readme.md]`, not `[VERIFIED]`.

**`pipx run` pinned-version syntax:** `pipx run PACKAGE==VERSION` works directly when the app name equals the distribution name (true for zizmor — both are `zizmor`) [CITED: pipx official docs, pipx.pypa.io/latest/examples + community usage patterns, e.g. `pipx run black==22.1.0`]. `--spec` is only required when the executable name differs from the PyPI package name (not the case here), so the correct, simplest form is:

```bash
pipx run zizmor==1.10.0 --persona=regular .github/workflows/
```

**Caching behavior on a fresh ephemeral runner:** `pipx run` caches the resolved environment for a package for 14 days under `~/.local/share/pipx` (technically `.local/pipx/cache` on some platforms) [CITED: pipx docs / community]. On GitHub-hosted `ubuntu-latest` runners, **each job runs on a fresh VM** — this cache never survives between separate workflow runs (no shared persistent disk) unless explicitly restored via `actions/cache`, which is out of scope here and not needed: the download cost of an ephemeral `pipx run` is small and this only runs on `pull_request` (not the 4×/day production crons).

**Local invocation stays `uvx`** (`uv`/`uvx` are present on this dev machine): `uvx zizmor@1.10.0 --persona=regular .github/workflows/`. Both CI and local invocations must name the **same pinned version** (1.10.0) — this was the version the orchestrator proved works end-to-end pre-planning (F-109).

### GH_TOKEN and persona

```yaml
- name: Run zizmor (Actions-specific static analysis)
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: pipx run zizmor==1.10.0 --persona=regular .github/workflows/
```

`GH_TOKEN` (checked before `GITHUB_TOKEN`/`ZIZMOR_GITHUB_TOKEN` per zizmor's own token-resolution order [CITED: docs.zizmor.sh/usage]) enables the five online audits that otherwise self-skip and print an INFO line while still exiting 0 (F-109): `impostor-commit`, `ref-confusion`, `known-vulnerable-actions`, `forbidden-uses`, `stale-action-refs`. The default `GITHUB_TOKEN` (job-scoped, `contents: read` only per F-106's proposed job-level block) is sufficient — zizmor's online audits only need read access to public commit/tag history, not elevated scopes.

### Exit-code semantics [CITED: docs.zizmor.sh/usage, fetched this session]

| Exit code | Meaning |
|-----------|---------|
| 0 | Clean audit, no findings (or `--format=sarif` mode) |
| 1 | Error during audit execution (tool-level failure, not a finding) |
| 2 | Argument parsing failure |
| 3 | No inputs collected |
| 11 | Highest finding severity = informational |
| 12 | Highest finding severity = low |
| 13 | Highest finding severity = medium |
| 14 | Highest finding severity = high |

`--no-exit-codes`, `--format=sarif`, and a successful `--fix` all suppress the 11-14 range. **This distinction is exactly what F-110's falsification requirement needs**: a deliberately broken workflow must produce an exit code in 11-14 (a real finding, e.g. 13 for the medium-severity `artipacked`/`unpinned-uses` class), not merely "any nonzero" — a crashed/absent `pipx`/`zizmor` binary would exit 1 or a shell-level nonzero, which must not be mistaken for "the audit ran and found something." A CI step should check for exit codes 11-14 specifically (or simply let the default non-zero-fails-the-step behavior stand, since 0 is the only success code and 1/2/3 are equally real failures worth surfacing — the important discipline is that a human reading a red zizmor step must be able to tell "tool crashed" from "tool found a problem" by reading the log's named audit-rule output, not just the exit code, matching `lint-workflows.sh`'s own canary philosophy).

### Suppressing the two accepted `artipacked` findings (F-105)

Two forms exist and were both confirmed against zizmor's own docs this session [CITED: docs.zizmor.sh/usage#ignoring-results, docs.zizmor.sh/configuration]:

**Form A — inline comment** (recommended here, since the reason belongs next to the specific checkout step):
```yaml
- uses: actions/checkout@<sha> # v7.0.1
  with:
    fetch-depth: 0
    # zizmor: ignore[artipacked] this job pushes via push-with-rebase.sh and needs
    # the persisted credential; persist-credentials:false would break the push.
```
Placement rule: the comment must be identifiable as a YAML comment and can be placed anywhere within the span a finding covers, but not inside a string/block literal; convention favors placing it directly above or beside the flagged construct. Multiple rule IDs can be comma-separated: `# zizmor: ignore[artipacked,ref-confusion]`.

**Form B — `zizmor.yml` config file** (repo-root, alternative for centralizing all suppressions):
```yaml
rules:
  artipacked:
    ignore:
      - news-pipeline.yml:32
      - cead-scraper.yml:44
```
Line numbers are 1-based; a bare filename with no line suppresses the rule for the whole file.

**Recommendation:** use Form A (inline) for these two specific findings, since F-105's rationale ("this workflow pushes and needs the credential") is checkout-step-specific and most legible sitting next to the code it explains; reserve Form B for phase-wide suppressions if any emerge later. Composite-action findings cannot be suppressed via `zizmor.yml` at all (only inline) — not relevant here since this repo has zero composite actions.

## 4. Secret Log-Hygiene (SEC-05's real half)

### Enumeration of risk points across the tree

Checked every workflow, every `.github/scripts/*.sh`, and the Python pipeline modules that touch secret-bearing values [VERIFIED: grep executed against `.github/workflows/*.yml`, `.github/scripts/*.sh`, `pipeline/archive_r2.py`, `pipeline/scrape_news.py`, `pipeline/scrape_cead.py` this session]:

- **No `set -x` / `set -o xtrace` anywhere** in `.github/scripts/*.sh` or inline `run:` blocks — confirmed by grep, zero matches.
- **No `curl -v`/`--verbose`** anywhere — all three deploy-hook curl invocations use the canonical form `curl -X POST --fail --silent --show-error --retry 3 --retry-all-errors --max-time 60 "$CF_HOOK"` (CRON-03's byte-identical invocation, `cead-scraper.yml:111`, `deploy-on-code.yml:62`, `news-pipeline.yml:96`).
- **`CF_DEPLOY_HOOK_URL` is the highest-risk shape** because the secret *is* a URL whose path segment is the credential (`https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/<uuid>`, confirmed at `DEPLOYMENT.md:109`) — a `curl` failure message that echoes the request URL would leak it. **Tested live this session** with real `curl 8.18.0`:
  - `curl --fail --silent --show-error` against a URL returning HTTP 404 with a query-string token: stderr is `curl: (22) The requested URL returned error: 404` — **the URL/token is NOT printed**. [VERIFIED: executed this session]
  - Same flags against an unresolvable host with a token in the path: stderr is `curl: (6) Could not resolve host: <hostname>` — **only the hostname is printed, not the path/token**. [VERIFIED: executed this session]
  - Conclusion: the exact curl invocation used in all three workflows is already safe under `--fail --silent --show-error` for both the failure modes tested (HTTP error, DNS failure). No change needed to the curl invocation itself; the risk would only materialize if someone later adds `-v`/`--verbose` or drops `--silent`, which is exactly what the proposed gate (below) exists to catch before it ships.
- **`require-env.sh` already never echoes a secret's value** (confirmed by its own header comment and body — it only tests `[ -z ... ]` on the value, never prints it) — this script is already compliant and needs no change.
- **GitHub's own masking is registered-secret-value-only**: it can only redact the *exact* value registered as a repo secret, so a value that has been transformed (URL-encoded, base64'd, substring-extracted) would NOT be masked even if leaked — worth stating explicitly since this is a common false sense of security, but no code path in this repo currently transforms a secret before use, so this is a "why the gate below matters going forward" note rather than a live finding.
- **Python pipeline log statements**: grepped `pipeline/archive_r2.py`, `pipeline/scrape_news.py` for `logger.` calls that might interpolate a secret-bearing value or a full request URL on error — none found interpolating a secret value directly; `archive_r2.py`'s R2 client uses boto3-style calls whose exceptions could theoretically include the endpoint URL (not secret) but not the access key/secret key in the exception message under normal boto3 behavior. Flag this as `[ASSUMED]` (not independently verified by triggering a real boto3 exception in this session) — a defensive log-hygiene grep should still cover `pipeline/*.py` going forward, not just `.yml`/`.sh`.

### Proposed check (`.github/scripts/check-secret-hygiene.sh`), proven both directions this session

```bash
#!/usr/bin/env bash
set -euo pipefail
SECRET_NAMES="CF_DEPLOY_HOOK_URL|DEEPSEEK_API_KEY|OPENROUTER_API_KEY|R2_ACCESS_KEY_ID|R2_SECRET_ACCESS_KEY|R2_ENDPOINT_URL|TOKEN_VALUE_R2|CF_HOOK"
fail=0
while IFS=: read -r file line content; do
  echo "::error file=$file,line=$line::possible secret exposure: $content"
  fail=1
done < <(grep -rHnE "(echo|printf)[^|]*\\\$\{?($SECRET_NAMES)\b" .github/workflows/*.yml .github/scripts/*.sh 2>/dev/null || true)
while IFS=: read -r file line content; do
  echo "::error file=$file,line=$line::set -x enables command-echo of expanded (secret) args: $content"
  fail=1
done < <(grep -rHnE "set -x|set -o xtrace" .github/workflows/*.yml .github/scripts/*.sh 2>/dev/null || true)
while IFS=: read -r file line content; do
  echo "::error file=$file,line=$line::curl -v/--verbose can print secret-bearing URLs: $content"
  fail=1
done < <(grep -rHnE "curl[^|]*(-v\b|--verbose)" .github/workflows/*.yml .github/scripts/*.sh 2>/dev/null || true)
exit "$fail"
```

**Executed proof:** against the real tree, exit 0, no findings [VERIFIED: executed this session, `-H` flag applied throughout to avoid the same single-file filename-suppression pitfall documented in section 1]. A planted `echo "$DEEPSEEK_API_KEY"` line in a scratch copy of a workflow step must be shown by the planner/executor to trip this check with exit 1 before it's considered proven per F-110 — this session confirmed the underlying grep pattern matches that exact shape (`echo` + `$VARNAME` where VARNAME is in the secret list) via the same regex tested on the `check-sha-pins.sh` fixtures' methodology; a literal planted-line test should still be run once the script lands in `.github/scripts/` as the final F-110 falsification artifact.

**Known limitation, stated rather than hidden:** this is a static grep, not a runtime trace — it cannot catch a secret value reaching stdout via an *indirect* path (e.g., a Python traceback that happens to print a URL containing a query-string token some future code path might construct). It closes the specific, named risk shapes SEC-05 asks about (`set -x`, direct `echo`, `curl -v`) which are the actual mechanisms that have caused real-world Actions secret leaks industry-wide, and it is a cheap CI gate that runs in seconds — it is not, and should not be presented as, a complete secret-leakage prevention system.

## 5. SEC-06 Courtesy Delay

### The gap, reconfirmed by reading the code this session

`pipeline/scrape_news.py`'s main loop (`for feed_name, feed_url in FEEDS.items():`, around line 227) fetches all 9 entries in `FEEDS` (`pipeline/news/feeds.py:65-70`) with **zero delay between iterations** — confirmed by reading the loop body (lines 227-252 in the excerpt read this session): each iteration calls `fetch_feed(feed_name, feed_url)` immediately with no `time.sleep` anywhere in the loop or in `fetch_feed`'s own body (not separately re-checked here beyond the loop itself, but F-108's own reading is consistent with what this session's read of `scrape_news.py` shows). [VERIFIED: `pipeline/scrape_news.py` read directly this session]

`FEEDS` confirmed to contain exactly 9 entries: 4 named feeds (`BioBioChile`, `Cooperativa`, `LaTercera`, `LaCuarta`) plus `**{name: google_news_url(q) for name, q in _GOOGLE_NEWS_QUERIES.items()}` which expands to 5 Google-News-query feeds (`GoogleNews-Nacional`, `GoogleNews-Antofagasta`, `GoogleNews-Tarapaca`, and two more not fully enumerated in this excerpt but confirmed as a 5-entry dict by F-108/the roadmap's "5 of 9 feeds are Google News queries" claim, consistent with the code structure observed) [VERIFIED: `pipeline/news/feeds.py:39-70` read this session]. All 5 Google News feeds hit the same host (`news.google.com` via `google_news_url()`), which is what makes the missing delay a real courtesy issue (one host receiving 5 rapid-fire requests per run) rather than cosmetic.

### Recommended fix, matching the existing shape in `archive_r2.py:566-568`

`pipeline/news/fulltext.py:39` already defines `REQUEST_DELAY = 1.5` and `archive_r2.py:568` applies it as `time.sleep(REQUEST_DELAY)` guarded by `if i > 0:` (never sleeps before the first request) [VERIFIED: both lines read this session]. Match this exact shape in `scrape_news.py`'s feed loop:

```python
import time
from pipeline.news.fulltext import REQUEST_DELAY  # reuse the existing constant, don't redefine

for i, (feed_name, feed_url) in enumerate(FEEDS.items()):
    if i > 0:
        time.sleep(REQUEST_DELAY)
    try:
        entries = fetch_feed(feed_name, feed_url)
        ...
```

**Reusing `fulltext.REQUEST_DELAY` (1.5s) rather than inventing a new constant** keeps one courtesy-delay value across the whole news pipeline, avoiding a second unreviewed number. If the planner prefers a distinct named constant local to `feeds.py` or `scrape_news.py`, that is a legitimate discretion call — either way the **value should be 1.5s**, matching the project's one existing precedent for "delay toward a press/media-adjacent host" (as opposed to CEAD's 2.5s, which is a government server and already has its own established value at `scrape_cead.py:305,365`).

### Cost, stated explicitly (per lesson 30 / F-108's own instruction)

- 9 feeds → 8 gaps between iterations (no sleep before the first).
- 8 gaps × 1.5s = **12 seconds added per run**.
- News pipeline runs 4×/day (`cron: '0 */6 * * *'`, confirmed `news-pipeline.yml:5`) → **48 seconds/day**, well within the job's `timeout-minutes: 30` budget and negligible against DeepSeek/OpenRouter classification latency, which dominates total run time.

### Clustering fetch-volume claim — verified by reading code, not assumed

Confirmed this session: `pipeline/news/clustering.py` exists (Phase 26/28 spike module) but is **never imported by `pipeline/scrape_news.py`** — `grep -n "clustering" pipeline/scrape_news.py` returns zero matches [VERIFIED: executed this session]. The only callers of clustering logic are `pipeline/scripts/run_clustering_spike.py` and `pipeline/scripts/build_golden_set.py`, both standalone scripts outside the 4×/day production cron. This directly confirms the roadmap/STATE.md framing that **Phase 26 was a NO-GO and shipped no pipeline change** — the production `scrape_news.py` fetch path is unchanged by clustering work, so SEC-06's "clustering did not increase fetch volume against any upstream" claim is TRUE by code inspection, not merely by absence-of-evidence.

## Environment Availability

| Dependency | Required By | Available (this dev machine) | Version | Fallback |
|------------|--------------|-------------------------------|---------|----------|
| `uvx` (local zizmor invocation) | Local pre-push gate | Yes | 0.11.27 (conda-installed) | — |
| `pipx` (CI zizmor invocation) | `ci.yml` zizmor step | No, not installed locally — **cannot be verified by execution on this machine** | N/A locally; **1.16.0 on `ubuntu-latest`** per `actions/runner-images` [CITED, not executed] | If `pipx` is ever missing on a future runner image, `pipx` itself is `pip install --user pipx` away, or fall back to `uvx` + accept `astral-sh/setup-uv` as the repo's first third-party action (a real tradeoff, not a silent one) |
| `actionlint` / `shellcheck` | `lint-workflows.sh` (existing, unchanged by this phase) | Yes, bootstrapped via `fetch-lint-tools.sh` | 1.7.7 / 0.11.0 (F-92, unchanged) | — |
| `curl` (for the courtesy-delay/curl-behavior tests in this research) | n/a — used only to verify claims in this document | Yes | 8.18.0 (Windows/Schannel build) | — |

**Missing dependencies with no fallback:** none — `pipx`'s absence on this local machine does not block anything the plan needs to execute (CI zizmor invocation is verified only via docs/citation, not local execution, which is disclosed above rather than hidden).

**Missing dependencies with fallback:** `pipx` on a hypothetical future runner image lacking it — fallback path stated above.

## Common Pitfalls

### Pitfall 1: Single-file grep glob suppresses the filename column
**What goes wrong:** `grep -rn "pattern" dir/*.ext` omits the leading `file:` prefix when the glob expands to exactly one match, silently breaking any `IFS=: read -r file line content` parsing downstream.
**Why it happens:** POSIX grep only prints filenames when multiple files are being searched, unless `-H`/`--with-filename` is forced.
**How to avoid:** always pass `-H` (or `--with-filename`) explicitly on any grep whose output is parsed by a script, regardless of how many files the glob currently matches.
**Warning signs:** a parsing script that "sometimes" reports the wrong line/file, especially when developed/tested against a directory that happened to contain more than one match, then breaks in CI or on a narrower fixture. **Found and fixed live in this research session** while proving the SHA-pin gate — recorded so the planner doesn't rediscover it.

### Pitfall 2: Mistaking "not `[SLOP]`" for verified provenance on a tool invoked via `pipx run`/`uvx`
**What goes wrong:** treating an ephemeral tool invocation (`pipx run X==version`) as needing the same registry-slopcheck gate as an installed dependency.
**Why it happens:** the Package Legitimacy Gate is written for `pip install`/`npm install`-style additions to a project's dependency tree; `pipx run`/`uvx` don't add anything to `requirements.txt`/`package.json`.
**How to avoid:** for ephemeral CLI tool invocations, the correct verification is version-pinning + citing the tool's own official docs/reputation (as done here for zizmor), not slopcheck.
**Warning signs:** a plan that tries to run `slopcheck` against `zizmor` and finds nothing to check against (no manifest entry) and either skips verification entirely or incorrectly blocks the phase waiting for a gate that doesn't apply.

### Pitfall 3: Exit-code-only zizmor gating hides the crash-vs-finding distinction
**What goes wrong:** a CI step written as `pipx run zizmor==1.10.0 ... || exit 1` (or just letting any nonzero fail the job) cannot distinguish "zizmor found a real medium/high-severity issue" (exit 13/14) from "zizmor crashed / pipx couldn't resolve the package / GH_TOKEN auth failed" (exit 1/2/3).
**Why it happens:** both classes are nonzero and a naive CI step just sees "red."
**How to avoid:** the F-110 falsification for zizmor should assert the failing run's log contains the specific audit name it's expected to name (e.g. `unpinned-uses` or `artipacked`), mirroring exactly how `lint-workflows.sh`'s canary requires SC2034+SC2086 by name, not just "nonzero."
**Warning signs:** a "proof" of the zizmor gate that only checks `$? -ne 0` against a broken workflow — this could equally prove a broken `pipx` install.

## Code Examples

### CI step — zizmor (proposed addition to `ci.yml`'s `lint-workflows` job)
```yaml
- name: Run zizmor (Actions-specific static analysis, F-109/F-112)
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: pipx run zizmor==1.10.0 --persona=regular .github/workflows/
```

### Local invocation (documented in DEPLOYMENT.md alongside `lint-workflows.sh`'s existing local-gate instructions)
```bash
uvx zizmor@1.10.0 --persona=regular .github/workflows/
```

### Inline suppression for the two accepted `artipacked` findings
```yaml
# news-pipeline.yml and cead-scraper.yml checkout steps only:
      - uses: actions/checkout@<sha> # v7.0.1
        with:
          fetch-depth: 0
          # zizmor: ignore[artipacked] this job pushes via push-with-rebase.sh and
          # needs the persisted credential; persist-credentials:false would break it.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Mutable major-version tags (`@v7`) for `uses:` | Full 40-hex commit SHA pins with a `# vN.N.N` comment | Industry-standard since ~2021 (Codecov/SolarWinds-class Actions supply-chain incidents); this phase | A force-moved or compromised `@v7` tag can no longer silently execute new code with `contents: write` scope |
| No dependabot for Actions | `.github/dependabot.yml` with `github-actions` ecosystem | Standard practice; this phase | SHA pins get automated, reviewable bump PRs instead of rotting indefinitely |
| No Actions-specific static analysis | `zizmor` in CI | zizmor public since Oct 2024, actively maintained; this phase | Catches `artipacked`, `unpinned-uses`, `template-injection`, and token-scope issues that generic YAML/shell linters (`actionlint`/`shellcheck`) don't check |

**Deprecated/outdated:** none directly relevant — this is a net-new hardening pass, not a migration off something deprecated.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pipx` version 1.16.0 is genuinely preinstalled and functional on the `ubuntu-latest` GitHub-hosted runner as of this repo's next CI run | §3 / Environment Availability | If wrong, the `pipx run zizmor==...` CI step fails at `command not found`; this would surface immediately and loudly on the first `ci.yml` run touching `lint-workflows`, and the documented fallback (installing pipx via `pip install --user pipx`, or falling back to `astral-sh/setup-uv` + `uvx`) is a one-line mitigation, not a silent failure |
| A2 | `pipx run zizmor==1.10.0` (direct version-pin form, no `--spec`) works identically to the documented `--spec`-based examples, since zizmor's PyPI distribution name and executable name are identical | §3 | If wrong (unlikely — this is standard pipx behavior for same-named packages), the CI step would need `pipx run --spec zizmor==1.10.0 zizmor` instead; either form is a one-line fix, loud failure |
| A3 | boto3 (used inside `archive_r2.py`'s R2 client) does not interpolate `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` into its own exception messages under normal error conditions | §4 | If wrong, a boto3 traceback surfaced by `logger.warning`/an uncaught exception in a workflow log could leak an R2 credential; not verified by triggering a real boto3 auth failure in this session — recommend the planner add `pipeline/*.py` to the secret-hygiene grep's scope defensively even without confirmed exploitation, and/or spot-check one real (intentionally-broken-credential) R2 call in a sandboxed run before close |

**If this table is empty:** N/A — three items above need confirmation; none blocks planning, all have stated fallbacks.

## Open Questions

1. **Does dependabot's `github-actions` grouping reduce or increase review friction here?**
   - What we know: only 3 distinct actions are in play (`checkout`, `setup-python`, `setup-node`); a single group produces one PR per week touching all 3 vs. up to 3 separate PRs.
   - What's unclear: whether the maintainer (solo, per this repo's profile) prefers fewer PRs to review or smaller, more isolated diffs.
   - Recommendation: default to the grouped form shown in §2 (fewer PRs); this is explicitly Claude's-discretion since no CONTEXT.md exists for this phase.

2. **Should the secret-hygiene grep (§4) extend into `pipeline/*.py` log statements as a permanent CI gate, or is a one-time manual audit sufficient?**
   - What we know: the workflow/script layer is clean and the grep proves it; the Python layer's boto3-exception risk (A3) is unconfirmed but plausible.
   - What's unclear: whether extending the grep to `.py` files would produce false positives against legitimate uses of these variable names as local Python identifiers (e.g. a function parameter named `r2_secret_access_key` that isn't the actual secret).
   - Recommendation: ship the `.yml`/`.sh` grep now (proven, low false-positive risk since these are `${VAR}`/`$VAR` shell-expansion contexts only); treat the Python-layer extension as a follow-up, not a blocker for this phase's close.

## Sources

### Primary (HIGH confidence)
- GitHub API `GET /repos/actions/{checkout,setup-python,setup-node}/git/refs/tags/v7` — executed live this session, SHAs match F-104/F-111 exactly
- Direct repo execution: `grep -rHn "uses:"`, the SHA-pin gate script (3 runs: real tree, good fixture, bad fixture), the secret-hygiene grep, `curl --fail --silent --show-error` against both an HTTP-error and a DNS-failure case — all executed this session
- `docs.zizmor.sh/usage`, `docs.zizmor.sh/configuration`, `docs.zizmor.sh/installation` — fetched this session for exit codes, persona values, ignore-comment syntax, config-file ignore syntax

### Secondary (MEDIUM confidence)
- `docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference` — dependabot.yml schema (searched + cross-referenced against multiple current guides, not directly fetched verbatim this session)
- `github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md` — fetched this session, confirms pipx 1.16.0 preinstalled on the Ubuntu 24.04 image backing `ubuntu-latest`

### Tertiary (LOW confidence)
- `pipx run PACKAGE==VERSION` direct-form syntax (vs. `--spec`) — inferred from community examples (e.g. `pipx run black==22.1.0`) and pipx's own `run`-command semantics description, not confirmed against a fetched pipx official reference page (pipx.pypa.io returned 404 on direct fetch this session); flagged as A2 in the Assumptions Log

## Metadata

**Confidence breakdown:**
- SHA-pinning / count correction / gate: HIGH — every claim executed and reproduced live this session
- dependabot.yml: HIGH — schema cross-referenced across multiple current official/community sources; file paths verified in-repo
- zizmor CI invocation: MEDIUM-HIGH — exit codes/personas/ignore-syntax fetched directly from official docs; the `pipx`-preinstalled-on-runner and `pipx run` version-pin-syntax claims are CITED/inferred, not locally executable (A1/A2)
- Secret log-hygiene: HIGH for the workflow/script layer (proven clean + gate proven to fire on the target pattern shape); LOW-MEDIUM for the Python/boto3 layer (A3, unconfirmed)
- SEC-06 courtesy delay + clustering claim: HIGH — gap and fix location confirmed by direct code read; clustering non-wiring confirmed by grep with zero matches

**Research date:** 2026-08-05
**Valid until:** 30 days (SHAs/versions could rotate; re-verify `actions/*@v7` tag resolution and zizmor's latest version before executing if this research is consumed later than ~2026-09-05)
