---
phase: quick-260726-dqf
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pipeline/news/classifier.py
  - pipeline/tests/test_classifier.py
  - pipeline/tests/test_classifier_traffic.py
  - .github/workflows/news-pipeline.yml
autonomous: true
requirements: [SPIKE-008]
user_setup:
  - service: openrouter
    why: "Granite 4.1 8B is served via OpenRouter; the pipeline needs an API key"
    env_vars:
      - name: OPENROUTER_API_KEY
        source: "OpenRouter Dashboard -> Keys (https://openrouter.ai/keys), then add as repo secret Settings -> Secrets -> Actions"

must_haves:
  truths:
    - "With no NEWS_PROVIDER env set, classifier defaults to OpenRouter/Granite"
    - "NEWS_PROVIDER=deepseek and NEWS_PROVIDER=minimax remain selectable"
    - "Granite's 'robos_ violentos' whitespace artifact is normalized before Pydantic validation and validates cleanly"
    - "The OpenRouter path sends NO response_format (fences stripped by existing path)"
    - "News Pipeline workflow exposes OPENROUTER_API_KEY to the scrape step, DEEPSEEK_API_KEY retained"
    - "pipeline tests pass green"
  artifacts:
    - path: "pipeline/news/classifier.py"
      provides: "openrouter default provider block + family whitespace normalization"
      contains: "openrouter.ai/api/v1"
    - path: ".github/workflows/news-pipeline.yml"
      provides: "OPENROUTER_API_KEY env on scrape step"
      contains: "OPENROUTER_API_KEY"
  key_links:
    - from: "pipeline/news/classifier.py"
      to: "https://openrouter.ai/api/v1"
      via: "OpenAI client base_url when _PROVIDER == openrouter"
      pattern: "openrouter\\.ai/api/v1"
    - from: "classify()"
      to: "ClassifierOutput.model_validate"
      via: "family whitespace normalization on data['family'] before validation"
      pattern: "family.*(sub|replace|split)"
---

<objective>
Adopt Granite 4.1 8B via OpenRouter as the DEFAULT news classifier provider, per spike 008 (VALIDATED: commune 100% vs DeepSeek 95.45%, family parity, 0% parse failures, ~6x cheaper, ~2.5x faster). The production SYSTEM_PROMPT is unchanged. DeepSeek and MiniMax stay selectable via NEWS_PROVIDER.

Purpose: cut news-classification cost ~6x and improve commune accuracy with zero prompt changes.
Output: openrouter provider block + default switch, a deterministic family-whitespace guard, updated tests, workflow env wired.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/spikes/008-granite-openrouter-classifier/README.md
@pipeline/news/classifier.py
@pipeline/tests/test_classifier.py
@pipeline/tests/test_classifier_traffic.py
@.github/workflows/news-pipeline.yml

<interfaces>
<!-- Key facts extracted from the codebase; no exploration needed. -->

Provider selection block (classifier.py lines 47-62) currently:
- Reads `_PROVIDER = os.environ.get("NEWS_PROVIDER", "deepseek").lower()`
- Branches: `minimax` -> api.minimaxi.chat/v1, model MiniMax-Text-01; else default deepseek -> api.deepseek.com, model deepseek-v4-flash

`_call_api()` (lines 183-218) sets `response_format={"type": "json_object"}` ONLY when `_PROVIDER == "deepseek"`. Non-deepseek providers already skip response_format and rely on `_strip_json_fence()` (lines 115, 177-180) to remove markdown fences. OpenRouter must follow the non-deepseek path (NO response_format).

`classify()` (lines 122-174) parses JSON at line 151 (`data = json.loads(raw_stripped)`), then validates at line 158 (`ClassifierOutput.model_validate(data)`). The family-whitespace normalization must run on `data["family"]` AFTER json.loads and BEFORE model_validate.

VALID_FAMILIES / FAMILY_KEYS enum values contain NO internal spaces (e.g. `robos_violentos`), so collapsing internal whitespace in `family` is safe for all providers.

Tests mock `pipeline.news.classifier.client` and feed `mock_client.chat.completions.create.return_value`. No test currently asserts `_PROVIDER`/`_MODEL` default values by name — but header docstrings and comments say "deepseek (default)".

Workflow: the file is `.github/workflows/news-pipeline.yml` (NOT `scrape-news.yml`). The scrape step is "Run news scraper" (lines 34-37) with `env: DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add OpenRouter default provider + family whitespace normalization in classifier.py</name>
  <files>pipeline/news/classifier.py</files>
  <behavior>
    - With NEWS_PROVIDER unset, module-load resolves _PROVIDER == "openrouter", _MODEL == "ibm-granite/granite-4.1-8b", client.base_url points at openrouter.ai/api/v1, api_key from OPENROUTER_API_KEY.
    - NEWS_PROVIDER=deepseek still yields deepseek-v4-flash + api.deepseek.com; NEWS_PROVIDER=minimax still yields MiniMax-Text-01 + api.minimaxi.chat/v1.
    - _call_api sends response_format ONLY for deepseek; openrouter and minimax omit it.
    - classify() normalizes internal whitespace in data["family"] (e.g. "robos_ violentos" -> "robos_violentos") after json.loads, before model_validate. Guard is defensive: only apply when family is a str; leave None/missing untouched so Pydantic still reports missing-field errors.
  </behavior>
  <action>Refactor the provider-selection block (lines 47-62) into three explicit branches. Default (NEWS_PROVIDER unset or "openrouter"): api_key from OPENROUTER_API_KEY, base_url https://openrouter.ai/api/v1, model ibm-granite/granite-4.1-8b. Keep the deepseek branch (api.deepseek.com, deepseek-v4-flash) and minimax branch (api.minimaxi.chat/v1, MiniMax-Text-01) selectable via NEWS_PROVIDER. Set the fallback (unrecognized value) to openrouter so the default is explicit. In _call_api, the existing `if _PROVIDER == "deepseek"` response_format gate already excludes openrouter — leave it as-is (openrouter follows the fence-stripping path). In classify(), immediately after `data = json.loads(raw_stripped)`, collapse internal whitespace in the family value: if data.get("family") is a str, replace runs of whitespace with empty (or use "".join(value.split())) so "robos_ violentos" becomes "robos_violentos"; assign back to data["family"]. Do NOT touch SYSTEM_PROMPT. Update the module header docstring (lines 4-19) to list openrouter (default, Granite 4.1 8B, no response_format), deepseek, minimax, and note the family-whitespace guard as a Granite tokenizer artifact per spike 008.</action>
  <verify>
    <automated>python -c "import os; os.environ.pop('NEWS_PROVIDER', None); import pipeline.news.classifier as c; assert c._PROVIDER=='openrouter', c._PROVIDER; assert c._MODEL=='ibm-granite/granite-4.1-8b', c._MODEL; assert 'openrouter.ai/api/v1' in str(c.client.base_url), c.client.base_url; print('OK')"</automated>
  </verify>
  <done>Default provider is openrouter/ibm-granite/granite-4.1-8b at openrouter.ai/api/v1; deepseek and minimax still selectable; classify() collapses internal whitespace in family before Pydantic; header docstring updated; SYSTEM_PROMPT untouched.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Update tests for openrouter default + add family-whitespace normalization test</name>
  <files>pipeline/tests/test_classifier.py, pipeline/tests/test_classifier_traffic.py</files>
  <behavior>
    - A new test feeds a mocked response with family "robos_ violentos" (internal space) and asserts classify() returns a ClassifierOutput whose family == "robos_violentos" (normalization applied before Pydantic).
    - A test asserts the module default provider/model: with NEWS_PROVIDER unset, _PROVIDER == "openrouter" and _MODEL == "ibm-granite/granite-4.1-8b".
    - Existing mocked-client tests continue to pass unchanged (client is mocked, provider-agnostic).
  </behavior>
  <action>In test_classifier.py, add test_family_internal_whitespace_normalized: patch pipeline.news.classifier.client, return a mock response built from _VALID_RESPONSE with family="robos_ violentos" and confidence 0.9, call classify(), assert result is not None and result.family == "robos_violentos". Add test_default_provider_is_openrouter: assert classifier_mod._PROVIDER == "openrouter" and classifier_mod._MODEL == "ibm-granite/granite-4.1-8b" (module is imported once at process start with NEWS_PROVIDER unset in the test env). Fix any stale docstring/comment in the test file headers that says "DeepSeek classification"/"DeepSeek NEVER called live" to be provider-neutral ("the configured LLM provider is NEVER called live"). Do the same header wording fix in test_classifier_traffic.py. Do not weaken existing assertions.</action>
  <verify>
    <automated>python -m pytest pipeline/tests/test_classifier.py pipeline/tests/test_classifier_traffic.py -q</automated>
  </verify>
  <done>New normalization test and default-provider test pass; all existing classifier tests green; header comments no longer hardcode "DeepSeek".</done>
</task>

<task type="auto">
  <name>Task 3: Wire OPENROUTER_API_KEY into the news-pipeline workflow</name>
  <files>.github/workflows/news-pipeline.yml</files>
  <action>In the "Run news scraper" step (lines 34-37), add `OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}` to the step `env:` alongside the existing `DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}` (keep DeepSeek for NEWS_PROVIDER=deepseek fallback). Do not add a NEWS_PROVIDER var — the code default is now openrouter, so the workflow runs Granite without an explicit override.</action>
  <verify>
    <automated>python -c "import yaml,io; d=yaml.safe_load(open('.github/workflows/news-pipeline.yml',encoding='utf-8')); s=[x for x in d['jobs']['scrape']['steps'] if x.get('name')=='Run news scraper'][0]; assert 'OPENROUTER_API_KEY' in s['env'] and 'DEEPSEEK_API_KEY' in s['env'], s['env']; print('OK')"</automated>
  </verify>
  <done>Scrape step env contains both OPENROUTER_API_KEY and DEEPSEEK_API_KEY; no NEWS_PROVIDER override added.</done>
</task>

</tasks>

<verification>
- `python -m pytest pipeline/tests/test_classifier.py pipeline/tests/test_classifier_traffic.py -q` passes.
- With NEWS_PROVIDER unset, classifier module resolves to openrouter/ibm-granite/granite-4.1-8b at openrouter.ai/api/v1.
- Workflow scrape step exposes OPENROUTER_API_KEY (and still DEEPSEEK_API_KEY).
- SYSTEM_PROMPT byte-for-byte unchanged from spike baseline.
</verification>

<success_criteria>
- openrouter is the default provider; deepseek/minimax selectable via NEWS_PROVIDER.
- family whitespace artifact ("robos_ violentos") normalized to "robos_violentos" before Pydantic validation; covered by a new unit test with mocked client (no live API).
- OpenRouter path omits response_format.
- news-pipeline.yml wires OPENROUTER_API_KEY; DEEPSEEK_API_KEY retained.
- All pipeline classifier tests green.
</success_criteria>

<output>
Create `.planning/quick/260726-dqf-adopt-granite-4-1-8b-openrouter-as-defau/260726-dqf-SUMMARY.md` when done.
</output>
