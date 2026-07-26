---
phase: quick-260726-jya
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/cead-scraper.yml
  - .github/workflows/ci.yml
  - .github/workflows/news-pipeline.yml
  - .github/workflows/r2-archive.yml
autonomous: true
requirements: [OPS-node24-bump]
must_haves:
  truths:
    - "No workflow references a Node-20-era action major (checkout@v4, setup-node@v4, setup-python@v5)"
    - "All four workflow YAML files still parse as valid YAML"
    - "Action inputs (python-version, node-version) are unchanged and remain compatible with the new majors"
  artifacts:
    - path: ".github/workflows/cead-scraper.yml"
      provides: "checkout + setup-python bumped to current Node-24 majors"
      contains: "actions/checkout@v7"
    - path: ".github/workflows/ci.yml"
      provides: "checkout + setup-node + setup-python bumped"
      contains: "actions/setup-node@v7"
    - path: ".github/workflows/news-pipeline.yml"
      provides: "checkout + setup-python bumped"
      contains: "actions/checkout@v7"
    - path: ".github/workflows/r2-archive.yml"
      provides: "checkout + setup-python bumped"
      contains: "actions/checkout@v7"
  key_links: []
---

<objective>
Bump all GitHub Actions runner action pins across the repo's four workflow files off their Node-20-era majors and onto the current Node-24 majors, eliminating the deprecation annotation GitHub emits on every run.

Purpose: GitHub deprecated Node 20 on Actions runners. Every workflow run currently emits a deprecation annotation because our action pins (checkout@v4, setup-node@v4, setup-python@v5) still resolve to Node-20 runtimes. Bumping to the current majors clears the annotation and keeps CI/pipeline runners on a supported Node.
Output: Four edited workflow YAML files with updated action version tags. One atomic commit. No behavioral change.

CRITICAL — target-major correction: The originating task assumed the current majors are checkout@v5, setup-node@v5, setup-python@v6. Web verification against the official release pages on 2026-07-26 shows the ACTUAL current majors are higher:
- actions/checkout → latest major is **v7** (v7.0.1, 2026-07-20) — NOT v5
- actions/setup-node → latest major is **v7** (v7.0.0, 2026-07-14) — NOT v5
- actions/setup-python → latest major is **v7** (v7.0.0) — NOT v6

Per the task's own instruction ("if any bump target is wrong, pin to the actual latest major and note it"), this plan targets **v7 across all three actions**. All targets bump to the same major (v7), which is coincidental, not a typo.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<interfaces>
<!-- Exact current action pins and line numbers, extracted from the four files. -->
<!-- Executor edits these tags only; no other lines change. -->

.github/workflows/cead-scraper.yml
  L26: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  L28: `      - uses: actions/setup-python@v5`    → actions/setup-python@v7

.github/workflows/ci.yml
  L17: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  L19: `      - uses: actions/setup-node@v4`      → actions/setup-node@v7
  L38: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  L40: `      - uses: actions/setup-python@v5`    → actions/setup-python@v7
  L55: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  (L57: `rhysd/actionlint@v1` — third-party action, NOT in scope, leave unchanged)

.github/workflows/news-pipeline.yml
  L25: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  L27: `      - uses: actions/setup-python@v5`    → actions/setup-python@v7

.github/workflows/r2-archive.yml
  L21: `      - uses: actions/checkout@v4`        → actions/checkout@v7
  L23: `      - uses: actions/setup-python@v5`    → actions/setup-python@v7
</interfaces>

<compatibility_notes>
- setup-python v7 keeps the `python-version` input — our `'3.12'` value is unchanged and supported.
- setup-node v7 keeps the `node-version` input — our `'20'` value is unchanged and supported (bumping the ACTION major does not force a Node RUNTIME change for our build; `node-version: '20'` still installs Node 20 for the build step, which is fine — CLAUDE.md pins Node 20/22 LTS for Astro 6).
- checkout v7 keeps all inputs we use (we use none beyond defaults).
- Keep the tag style already in the repo (`@vN`). Do NOT switch to SHA pinning.
</compatibility_notes>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Bump all action pins to v7 across the four workflows</name>
  <files>.github/workflows/cead-scraper.yml, .github/workflows/ci.yml, .github/workflows/news-pipeline.yml, .github/workflows/r2-archive.yml</files>
  <action>
    Edit each of the four workflow files, changing only the action version tags per the &lt;interfaces&gt; map above. In every occurrence:
    - `actions/checkout@v4` → `actions/checkout@v7`
    - `actions/setup-node@v4` → `actions/setup-node@v7`
    - `actions/setup-python@v5` → `actions/setup-python@v7`

    Leave `rhysd/actionlint@v1` in ci.yml UNCHANGED — it is a third-party action outside this Node-24 bump. Change nothing else: no whitespace, no step reordering, no input changes. This is a pure version-string bump implementing OPS-node24-bump. Targets are v7 per verified-latest-major correction (originating task assumed v5/v5/v6, which are stale as of 2026-07-26).
  </action>
  <verify>
    <automated>python -c "import glob,sys; import yaml if False else None" ; python - &lt;&lt;'PY'
import re, glob, yaml, sys
files = sorted(glob.glob('.github/workflows/*.yml'))
target = {'cead-scraper','ci','news-pipeline','r2-archive'}
bad = []
for f in files:
    txt = open(f, encoding='utf-8').read()
    # YAML must still parse
    yaml.safe_load(txt)
    # No stale Node-20-era majors remain
    for pat in (r'actions/checkout@v4\b', r'actions/setup-node@v4\b', r'actions/setup-python@v5\b'):
        if re.search(pat, txt):
            bad.append((f, pat))
if bad:
    print('STALE PINS REMAIN:', bad); sys.exit(1)
print('OK: all four workflows parse and no stale action majors remain')
PY</automated>
  </verify>
  <done>
    Zero occurrences of `actions/checkout@v4`, `actions/setup-node@v4`, or `actions/setup-python@v5` remain in any workflow file. All four YAML files parse via yaml.safe_load. `rhysd/actionlint@v1` is unchanged. No non-version lines changed (git diff shows only the tag characters differ).
  </done>
</task>

</tasks>

<verification>
- `git diff .github/workflows/` shows ONLY version-tag characters changed (v4→v7, v5→v7). No structural, whitespace, or input changes.
- The Task 1 automated check passes: all four files parse as YAML and contain zero stale action majors.
- Do NOT trigger any workflow run — a follow-up verification quick task handles live validation (per constraints).
</verification>

<success_criteria>
- All 12 in-scope action pins bumped to @v7 (5 in ci.yml, 2 each in the other three files, but checkout appears 3x in ci.yml → count is: cead 2, ci 5, news 2, r2 2 = 11 checkout/setup pins; actionlint excluded).
- No behavioral change to any workflow logic.
- One atomic commit.
</success_criteria>

<output>
Create `.planning/quick/260726-jya-bump-github-actions-to-node-24-versions-/260726-jya-SUMMARY.md` when done. Note in the summary that targets were corrected from the task's assumed v5/v5/v6 to the actual current majors (all v7) verified against official release pages on 2026-07-26.
</output>
