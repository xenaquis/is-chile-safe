# Stack Research — v2.1 (News Intelligence, Map UX & Ops Hardening)

**Domain:** Static-site news faceting/clustering + map control UI + Actions security, on top of a locked $0-budget Astro/Leaflet/Python stack
**Researched:** 2026-07-29
**Confidence:** HIGH (Astro/Leaflet/GH Actions mechanics, package versions verified) / MEDIUM (OpenRouter live pricing, embeddings catalog — WebSearch-sourced, no Context7 entry for OpenRouter)

## Recommended Stack

### Core Technologies — verdict per workstream

| Workstream | Verdict | New dependency? |
|---|---|---|
| (a) News faceting UI | Build-time faceting in Astro frontmatter + vanilla progressive-enhancement JS | **No** |
| (b) Event clustering | Lexical pre-filter (stdlib + rapidfuzz) then LLM pairwise adjudication via existing OpenRouter/DeepSeek client | **Yes, one small package** (`rapidfuzz`) |
| (c) Map control shell | Native `<details>`/`<dialog>` + CSS; no JS popover library | **No** |
| (d) Cron/security | `zizmor` (Actions static analyzer) + `actionlint` (already present) + SHA-pinning + Dependabot | **Yes, dev-only, doesn't ship** (`zizmor`, no runtime cost) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `rapidfuzz` | **3.14.5** (PyPI, verified Apr 2026 upload) | C++-backed fuzzy string similarity (Levenshtein/token-sort ratio) for the cheap pre-filter that groups candidate duplicate headlines before any LLM call | Phase 26 clustering — compute title similarity + comuna/date overlap to build small candidate pairs/clusters; only ambiguous pairs go to the LLM |
| `zizmor` | latest PyPI release (**shipped 2026-07-21**, actively maintained by Trail of Bits / zizmorcore) | Actions-specific static analyzer: unpinned actions, script-injection via `${{ }}` in `run:`, excessive `permissions:`, credential exfiltration patterns | Phase 33 security posture — run as a CI job or pre-commit / local audit; not a runtime dependency |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `actionlint` (already in `ci.yml` via `rhysd/actionlint@v1`) | YAML/expression correctness for workflow files | Keep — it is a *syntax* linter, not a *security* linter. `zizmor` is complementary, not a replacement. |
| Dependabot (`.github/dependabot.yml`, **new file needed**) | Automated PRs bumping pinned action SHAs and pip/npm deps | Repo currently has no `dependabot.yml` — add `package-ecosystem: "github-actions"` + `"pip"` + `"npm"`, weekly interval |
| GitHub secret scanning / push protection | Detect committed API keys (`OPENROUTER_API_KEY`, `R2_*`, `CF_DEPLOY_HOOK_URL`) | Native GitHub feature, free on public repos — verify it's enabled in repo Settings > Code security (no code change) |

## Installation

```bash
# Python pipeline (pipeline/requirements.txt) — add ONE line
echo "rapidfuzz==3.14.5" >> pipeline/requirements.txt

# zizmor — run via uvx/pipx in CI, not installed as a project dependency
# in a new .github/workflows/security-audit.yml step:
#   uses: pipx run zizmor@latest .github/workflows/
# or:
#   uvx zizmor .github/workflows/

# Frontend (site/package.json) — NOTHING to install for (a) or (c)
```

No `npm install` entries are recommended for this milestone. That absence is the headline finding for (a) and (c).

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| (a) Astro frontmatter faceting + vanilla JS | A client facet lib (e.g. `list.js`, `fuse.js` client-side, Alpine.js) | Only if facet state needed to survive without a full page reload/URL-param navigation AND record volume grows past ~1-2k items making client re-filtering worthwhile. At tens–low hundreds of records (30-day window) this is never justified here. |
| (a) Astro frontmatter faceting + vanilla JS | A React island (`client:load`/`client:visible`) for the facet panel | Only if facets need complex cross-filter interaction state (e.g. live multi-select combos with debounced search) that's painful in vanilla JS. CLAUDE.md explicitly bans `client:load` on the map island for JS-weight reasons; adding a *second* hydrated React tree for facets fights that same budget. Rejected. |
| (b) rapidfuzz + stdlib pre-filter, LLM pairwise adjudication | scikit-learn `TfidfVectorizer` + cosine similarity | Reasonable if candidate sets get large (hundreds of items compared pairwise); TF-IDF cosine scales better than O(n²) rapidfuzz string comparisons for big batches. At the pipeline's actual volume (tens of articles/day, RSS from 3 feeds) rapidfuzz's simplicity wins — no need to add scikit-learn (heavy, ~30MB wheel) to a `requirements.txt` that currently has zero ML libs. |
| (b) rapidfuzz pre-filter | MinHash/SimHash (`datasketch` package) | Datasketch shines at web-scale (millions of documents, LSH banding). Total daily volume here is far below the threshold where LSH beats brute-force pairwise comparison. Would be pure overhead. |
| (b) Lexical pre-filter + LLM pairwise adjudication | Embedding-based similarity via OpenRouter embedding endpoint | OpenRouter does expose an embeddings endpoint (`/api/v1/embeddings`, e.g. `qwen/qwen3-embedding-8b`, small OSS models) — MEDIUM confidence, WebSearch-sourced, not verified against Context7. But: (1) it's a second API surface + new SDK call pattern to build and maintain for a benefit rapidfuzz mostly captures (near-duplicate wording from the same wire copy), (2) still costs money per article even if cheap, (3) the real ambiguity in clustering — "same event, different framing/outlet" — is exactly the case lexical similarity misses and only the LLM step resolves anyway. Verdict: skip embeddings entirely for this volume; do lexical pre-filter → LLM adjudication only. Revisit only if Phase 26's spike shows lexical pre-filter recall is too low. |
| (d) zizmor | GitHub's own "Actions policy: SHA pinning" org-level control | That's an org/enterprise GitHub setting, not available on a personal-namespace free-tier repo the way this project is hosted; zizmor is the free, repo-local equivalent and also catches script-injection and permission issues policy-pinning doesn't. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| Any client-side search/facet JS library (`fuse.js`, `list.js`, Algolia, Pagefind for facets) for the news filter UI | Violates the "SSG/pre-rendered, JS only enhances" constraint for no benefit at tens–hundreds of records; adds a shipped-JS budget line to pages that today ship ~0 JS outside the map island | Compute facet groupings (by month, by region→comuna, by crime family) at Astro build time from `incidents/current.json` + archive, render as static links/sections (`?family=robo&region=...` style query-string pages or pre-rendered anchor sections), progressive-enhancement `<script>` only for client-side show/hide toggling of already-rendered DOM |
| A JS popover/disclosure library (Radix, Floating UI, headlessui, Popper) for the map control-shell rework | The site ships almost no UI framework by design; native `<details>`/`<dialog>` cover disclosure and modal-panel semantics with built-in keyboard (Esc, Tab-trap for `<dialog>`) and a11y support in every evergreen browser as of 2026, at zero JS cost | Native `<details>`/`<summary>` for the collapsible filter panel; native `<dialog>` (with `.showModal()`) for any modal-style mobile control tray; CSS only for the 375px layout — this matches the existing hamburger-nav pattern already in the codebase (`sr-only-but-focusable checkbox`, WR-03) |
| Floating UI / Popper specifically for the Leaflet map control positioning | Leaflet already provides its own `L.Control` positioning API (`topleft`/`topright`/etc.) which handles reflow correctly inside the Leaflet pane stack; a separate JS positioning library fighting Leaflet's own DOM/zoom transforms is a known source of drift bugs, especially on resize/orientation-change at 375px | `L.Control.extend()` custom controls, or plain absolutely-positioned HTML siblings outside the Leaflet pane with CSS media queries for 375px — do not let a floating-UI lib compute position against Leaflet-managed elements |
| scikit-learn / spaCy / sentence-transformers for clustering | Heavy dependencies (scikit-learn ~30MB, sentence-transformers pulls in torch, hundreds of MB) for a batch pipeline processing a few dozen articles per 6-hour cron run; GitHub Actions free-tier minutes and `pip install` time both get worse for no measurable precision gain at this volume | `rapidfuzz` (pure C++ extension, tiny) for pre-filter; the LLM already paid for (Granite 4.1 8B / DeepSeek v4-flash) for adjudication |
| OpenRouter/DeepSeek embeddings as the primary clustering signal | Adds a third billed API surface per article on top of classification+geolocation calls already made; the marginal same-event recall gain over rapidfuzz + LLM pairwise adjudication is unproven at this volume — see Alternatives Considered | Lexical pre-filter (rapidfuzz on title + published-date window + comuna match) narrows candidates to a handful of same-day, same-comuna pairs; only those go to one LLM adjudication call each |
| `deepseek-chat` / `deepseek-reasoner` model IDs for clustering adjudication | Already banned in CLAUDE.md — deprecated, stop working 2026-07-24 | `deepseek-v4-flash` (fallback) or Granite 4.1 8B via OpenRouter (default), same client already wired in `pipeline/` |
| GitHub Actions org-wide "policy" SHA-pin enforcement as a substitute for `zizmor` | Requires GitHub Enterprise/org-owned repo settings not available here | Manually pin `uses:` lines to full commit SHA with `# vX.Y.Z` trailing comment; verify via `zizmor` in CI; let Dependabot bump the pins |
| Adding `boto3`-style heavy SDKs for GH Actions security tooling | Not needed — `zizmor` and `actionlint` are self-contained Rust/Go binaries run via `pipx`/`uvx`, no Python SDK footprint added to `pipeline/requirements.txt` | Keep security tooling entirely at the CI-runner level, invoked via `pipx run` / `uvx`, never added to `pipeline/requirements.txt` |

## Stack Patterns by Variant

**If Phase 26 clustering spike returns NO-GO (per PROJECT.md's GO/NO-GO gate):**
- Skip `rapidfuzz` addition entirely — Phase 27/28 ship faceting only, no clustered-event cards
- Document the negative finding; no stack change needed downstream

**If Phase 26 is GO and article volume later grows materially (e.g. more RSS feeds added):**
- Revisit scikit-learn `TfidfVectorizer` + cosine similarity as the pre-filter once daily article count moves from tens to many hundreds — rapidfuzz's O(n²) pairwise comparison degrades before TF-IDF's vectorized approach would
- This is a future-scale note, not a v2.1 action

**If the map control-shell rework (Phase 30) needs a genuinely reusable multi-instance disclosure pattern beyond `<details>`/`<dialog>`:**
- Consider the Popover API (`popovertarget`/`popover` HTML attributes, baseline-available across evergreen browsers by 2026) as a zero-JS escape hatch before reaching for any JS library — verify current browser support at implementation time via caniuse, since this project has no polyfill budget philosophy

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| `rapidfuzz==3.14.5` | Python 3.10+ | Pipeline runs 3.12 in CI (`ci.yml`, `news-pipeline.yml`) — compatible. Pure C-extension wheel, no compiled-toolchain step needed on `ubuntu-latest`. |
| `zizmor` (latest) | Any GitHub Actions YAML, run via `pipx`/`uvx` | Not a Python package dependency of this repo — install ephemeral in the CI job only, keep out of `pipeline/requirements.txt` |
| `actions/checkout@v7`, `actions/setup-python@v7`, `actions/setup-node@v7` (current pins in workflows) | SHA-pinning | Currently pinned by **tag**, not SHA, across all 5 workflow files (`ci.yml`, `news-pipeline.yml`, `cead-scraper.yml`, `r2-archive.yml`, `deploy-on-code.yml`) — Phase 33 should convert these `@v7` tags to full-SHA + version comment; this is a workflow-file edit, not a new dependency |
| Native `<dialog>`/`<details>`/Popover API | Astro 6.4 SSR output | These are plain HTML/CSS features Astro passes through untouched; no Astro-specific compatibility concern |

## Notes on Astro 6 view transitions / `client:visible`

- This project does **not** currently use Astro's View Transitions (`<ClientRouter />`) — confirmed absent from `site/package.json` and not mentioned in existing architecture notes. Introducing it for the news facet UI is out of scope and unnecessary: full-page navigation between facet query-string URLs is fine for SSG/SEO and keeps behavior identical to the rest of the site (comuna/region page navigation already works this way).
- `client:visible` remains reserved for genuinely optional below-the-fold interactive islands (per CLAUDE.md's existing guidance to keep it off the map island entry point). For facets, no hydration directive is needed at all — the enhancement script should be a plain `<script>` tag (module, deferred) operating on server-rendered DOM, not an Astro island.
- If a future phase *does* want smooth cross-navigation between facet views without full reloads, `<ClientRouter />` (Astro's view-transitions router) is the correct built-in mechanism to reach for before any client router library — but that is not needed for v2.1's stated scope (facets computed at build time, JS only enhances).

## Sources

- Context7 — not used (no Context7 entries queried for Astro/Leaflet in this pass; version numbers taken directly from `site/package.json`, already-verified per CLAUDE.md's own sourced STACK section)
- [zizmor PyPI](https://pypi.org/project/zizmor/) — confirmed active release, most recent 2026-07-21, MEDIUM-HIGH confidence (WebSearch, corroborated by Trail of Bits blog post and zizmor docs site)
- [Trail of Bits: We hardened zizmor's GitHub Actions static analyzer](https://blog.trailofbits.com/2026/05/22/we-hardened-zizmors-github-actions-static-analyzer/) — MEDIUM confidence, single-source but authoritative (tool's own security auditor)
- [OpenRouter — Granite 4.1 8B pricing page](https://openrouter.ai/ibm-granite/granite-4.1-8b) — $0.05/M input, $0.10/M output, MEDIUM confidence (WebSearch summary of official pricing page, not independently re-fetched)
- [OpenRouter embedding models collection](https://openrouter.ai/collections/embedding-models) — confirms an embeddings endpoint and OSS model options exist; LOW-MEDIUM confidence, not verified against official API reference page directly
- DeepSeek v4-flash pricing — $0.14/M input (cache miss), $0.0028/M (cache hit), $0.28/M output — MEDIUM confidence, aggregator-sourced (pricepertoken.com), consistent with the "économica" characterization already in CLAUDE.md
- [RapidFuzz PyPI](https://pypi.org/project/RapidFuzz/) — v3.14.5, HIGH confidence (package registry, direct)
- [pydevtools: How to pin GitHub Actions by SHA](https://pydevtools.com/handbook/how-to/how-to-pin-github-actions-by-sha-for-python-projects/) — MEDIUM confidence, corroborates standard Dependabot SHA-pin workflow pattern
- Repo files read directly: `site/package.json`, `pipeline/requirements.txt`, `.github/workflows/{ci,news-pipeline,cead-scraper,r2-archive,deploy-on-code}.yml`, `.planning/PROJECT.md`, `CLAUDE.md` — HIGH confidence, ground truth for current state

---
*Stack research for: Chile Safety Map v2.1 (news faceting, event clustering, map control shell, cron/security)*
*Researched: 2026-07-29*
