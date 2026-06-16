---
phase: quick-260616-huj
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - site/src/lib/familyDefs.ts
  - site/src/pages/crime-ranking/[crime].astro
  - site/src/pages/es/ranking-delito/[crime].astro
autonomous: true
requirements: [HUJ-CLARIFY-RATES]
must_haves:
  truths:
    - "EN ranking column header explicitly says rates are reported complaints per 100k residents per year"
    - "ES ranking column header explicitly says rates are denuncias por 100.000 hab. per year"
    - "Rate cells and national mean show 1 decimal (EN 3,746.3 / ES 3.746,3) instead of rounded integers"
    - "A short bilingual inline explainer sentence sits near the table, stating these are reported-denuncia rates per 100k residents and that small/touristic communes can show very high rates"
    - "Build + 12 validators (incl. forbidden-language) still pass with CEAD attribution intact"
  artifacts:
    - path: "site/src/lib/familyDefs.ts"
      provides: "RANKING_RATE_EXPLAINER_EN / RANKING_RATE_EXPLAINER_ES shared explainer strings"
      contains: "RANKING_RATE_EXPLAINER_EN"
    - path: "site/src/pages/crime-ranking/[crime].astro"
      provides: "EN clarified labels, 1-decimal rates, inline explainer"
      contains: "RANKING_RATE_EXPLAINER_EN"
    - path: "site/src/pages/es/ranking-delito/[crime].astro"
      provides: "ES clarified labels, 1-decimal rates, inline explainer"
      contains: "RANKING_RATE_EXPLAINER_ES"
  key_links:
    - from: "site/src/pages/crime-ranking/[crime].astro"
      to: "site/src/lib/familyDefs.ts"
      via: "import RANKING_RATE_EXPLAINER_EN"
      pattern: "RANKING_RATE_EXPLAINER_EN"
    - from: "site/src/pages/es/ranking-delito/[crime].astro"
      to: "site/src/lib/familyDefs.ts"
      via: "import RANKING_RATE_EXPLAINER_ES"
      pattern: "RANKING_RATE_EXPLAINER_ES"
---

<objective>
Clarify how crime-ranking rates are presented on both the EN (`crime-ranking/[crime].astro`) and ES (`es/ranking-delito/[crime].astro`) pages so users understand the figures are reported-complaint (denuncia) rates per 100,000 residents per year.

Purpose: The underlying values are already correct per-100k denuncia rates. The defect is comprehension only — bare rounded integers under a vague "Rate per 100k" header invite users to misread large family-aggregate values for small communes as errors or as absolute danger. Clarifying the label, showing 1 decimal, and adding one explainer sentence fixes the misread without touching any data.

Output: Two presentational `.astro` edits plus one pair of shared explainer strings in `familyDefs.ts`. NO changes to data files, rate math, sorting, low-population logic, or JSON-LD numeric values.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<interfaces>
<!-- Existing shared constants in site/src/lib/familyDefs.ts. The two new
     explainer strings are added alongside the existing methodology maps.
     RANKING_METHODOLOGY_EN / RANKING_METHODOLOGY_ES already exist per family. -->

From site/src/lib/familyDefs.ts:
- FAMILY_LABELS_EN / FAMILY_LABELS_ES: Record<string, string>
- FAMILY_DEFS_EN / FAMILY_DEFS_ES: Record<string, string>
- RANKING_METHODOLOGY_EN / RANKING_METHODOLOGY_ES: Record<string, string>  (already used by ranking pages)

Current EN render (crime-ranking/[crime].astro):
- ~line 220 national mean: `{Math.round(familyNationalMean).toLocaleString('en-US')} per 100k`
- ~line 238 column header: `<th scope="col" class="col-num">Rate per 100k</th>`
- ~line 257 rate cell: `{Math.round(row.rate).toLocaleString('en-US')}`
- ~line 264-268 low-population footnote already present
- region-breakdown bars (~line 285) also use Math.round(r.rate) — OUT OF SCOPE, leave unchanged

Current ES render (es/ranking-delito/[crime].astro):
- ~line 226 national mean: `{Math.round(familyNationalMean).toLocaleString('es-CL')} por 100k`
- ~line 244 column header: `<th scope="col" class="col-num">Tasa por 100k</th>`
- ~line 263 rate cell: `{Math.round(row.rate).toLocaleString('es-CL')}`
- ~line 270-274 low-population footnote already present
- region-breakdown bars also use Math.round(r.rate) — OUT OF SCOPE, leave unchanged
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add shared bilingual rate-explainer strings to familyDefs.ts</name>
  <files>site/src/lib/familyDefs.ts</files>
  <action>
    Append two new exported constants after RANKING_METHODOLOGY_ES (do NOT alter any existing strings):

    `export const RANKING_RATE_EXPLAINER_EN: string` — one sober sentence stating the rates are reported complaints (denuncias) per 100,000 residents per year, sourced from CEAD, and that small or touristic communes can show very high rates because their resident population is small. Keep CEAD attribution explicit. Per locked decision, sober tone consistent with existing FAMILY_DEFS / RANKING_METHODOLOGY wording.
    Suggested EN: "Rates are reported complaints (denuncias) per 100,000 residents per year, sourced from CEAD official police statistics. Communes with small or seasonal/touristic resident populations can show very high rates because the figure is divided by a small resident base."

    `export const RANKING_RATE_EXPLAINER_ES: string` — Spanish mirror.
    Suggested ES: "Las tasas corresponden a denuncias por 100.000 residentes al año, según estadísticas policiales oficiales del CEAD. Las comunas con población residente pequeña o estacional/turística pueden presentar tasas muy altas porque la cifra se divide por una base residente reducida."

    FORBIDDEN-LANGUAGE GUARD: do not use the words safe/unsafe/dangerous/danger/peligros*/seguro-as-a-territorial-label or any absolute safety judgement. Describe statistics, not territories. (Use a neutral verb tense; "seguridad"/"safety" as a topic noun is fine only if it already passes — prefer avoiding it entirely here.)
  </action>
  <verify>
    <automated>node -e "const s=require('node:fs').readFileSync('site/src/lib/familyDefs.ts','utf8'); if(!/RANKING_RATE_EXPLAINER_EN/.test(s)||!/RANKING_RATE_EXPLAINER_ES/.test(s)) process.exit(1); if(/\b(dangerous|unsafe|peligros|safe to live)\b/i.test(s)) {console.error('forbidden term');process.exit(1);}"</automated>
  </verify>
  <done>Both explainer constants exported; no existing string mutated; no forbidden safety-judgement terms present.</done>
</task>

<task type="auto">
  <name>Task 2: Wire clarified labels, 1-decimal formatting, and inline explainer into BOTH ranking pages</name>
  <files>site/src/pages/crime-ranking/[crime].astro, site/src/pages/es/ranking-delito/[crime].astro</files>
  <action>
    Apply mirrored presentational edits to both files. No data, math, sorting, low-population, or JSON-LD changes.

    EN — site/src/pages/crime-ranking/[crime].astro:
    1. Add `RANKING_RATE_EXPLAINER_EN` to the existing familyDefs import.
    2. Column header (~line 238): change `Rate per 100k` to `Reported complaints per 100k residents (${latestYear})`. Header text must convey reported-complaint/denuncia framing within `.col-num` column width — if full phrase is too wide visually, keep the concise form above (the explainer sentence carries the full denuncia detail). Keep `class="col-num"`.
    3. Rate cell (~line 257): replace `{Math.round(row.rate).toLocaleString('en-US')}` with `{row.rate.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`.
    4. National mean (~line 220): replace `Math.round(familyNationalMean).toLocaleString('en-US')` with `familyNationalMean.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })`. Keep the `per 100k ({latestYear})` suffix.
    5. Inline explainer: add a single `<p class="rate-explainer">{RANKING_RATE_EXPLAINER_EN}</p>` immediately after the `<h2 class="section-heading">` inside the ranking-section (before `.table-wrapper`), so it sits directly above the table. Do NOT remove the existing low-pop footnote or methodology note.
    6. Do NOT touch the region-breakdown bars (Math.round(r.rate) stays).

    ES — site/src/pages/es/ranking-delito/[crime].astro (mirror):
    1. Add `RANKING_RATE_EXPLAINER_ES` to the familyDefs import.
    2. Column header (~line 244): change `Tasa por 100k` to `Denuncias por 100.000 hab. (${latestYear})`. Keep `class="col-num"`.
    3. Rate cell (~line 263): replace `{Math.round(row.rate).toLocaleString('es-CL')}` with `{row.rate.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`.
    4. National mean (~line 226): replace `Math.round(familyNationalMean).toLocaleString('es-CL')` with `familyNationalMean.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 })`. Keep `por 100k ({latestYear})` suffix.
    5. Inline explainer: add `<p class="rate-explainer">{RANKING_RATE_EXPLAINER_ES}</p>` immediately after the `<h2 class="section-heading">` in the ranking-section, above `.table-wrapper`. Keep existing footnote/methodology.
    6. Do NOT touch the ES region-breakdown bars.

    Optional styling: if no `.rate-explainer` style exists, add a small muted style (e.g. font-size ~0.85em, muted color, margin below) in the page's existing `<style>` block, matching `.low-pop-footnote` treatment. Keep it minimal and consistent across both files.
  </action>
  <verify>
    <automated>node -e "const fs=require('node:fs');for(const f of ['site/src/pages/crime-ranking/[crime].astro','site/src/pages/es/ranking-delito/[crime].astro']){const s=fs.readFileSync(f,'utf8');if(!/rate-explainer/.test(s)){console.error('missing explainer '+f);process.exit(1);}if(!/minimumFractionDigits:\s*1/.test(s)){console.error('missing 1-decimal '+f);process.exit(1);}if(/\bRate per 100k\b|\bTasa por 100k\b/.test(s)){console.error('old header remains '+f);process.exit(1);}}"</automated>
  </verify>
  <done>Both pages import the explainer, render it above the table, show 1-decimal rates in cells and national mean, and use the clarified denuncia-framed column headers. Region-breakdown bars unchanged.</done>
</task>

<task type="auto">
  <name>Task 3: Chained build + validate (OneDrive desync guard)</name>
  <files>(no file changes — verification only)</files>
  <action>
    From the `site/` directory, run build and validate in ONE chained command so dist/ does not desync under OneDrive: `npm run build && npm run validate`. The repo lives inside OneDrive — do NOT run build and validate as separate tool calls. If the build emits a different validate entrypoint, use the project's canonical chained command, but it MUST be a single invocation. Fix any forbidden-language validator failure by adjusting the explainer wording (Task 1 strings) — never by altering numbers or attribution.
  </action>
  <verify>
    <automated>cd site && npm run build && npm run validate</automated>
  </verify>
  <done>Build succeeds and all 12 validators pass, including the forbidden-language validator, with CEAD attribution intact.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| build-time content → static HTML | Copy/label strings rendered into indexable pages; only risk is editorial/forbidden-language, no untrusted runtime input |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-huj-01 | Information disclosure | Misleading rate copy | mitigate | Explainer + denuncia-framed header clarify the statistic; CEAD attribution retained |
| T-huj-02 | Tampering | Editorial forbidden-language regression | mitigate | Task 1 guard + Task 3 forbidden-language validator gate |
| T-huj-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed; pure copy/format edits |
</threat_model>

<verification>
- Both ranking pages render the new explainer paragraph above the table.
- Rate cells and national mean display exactly one decimal in locale-correct format (EN `,`/`.`; ES `.`/`,`).
- Column headers convey reported-complaint/denuncia per 100k residents per year.
- `npm run build && npm run validate` (single chained command from site/) passes all 12 validators.
- No edits to data JSON, rate math, sorting, low-population logic, JSON-LD numbers, or region-breakdown bars.
</verification>

<success_criteria>
- A reader of either ranking page can tell at a glance that the figures are reported complaints (denuncias) per 100,000 residents per year and why small/touristic communes can look high.
- Numbers are unchanged in value; only their precision (1 decimal) and surrounding labels changed.
- All validators green, CEAD attribution intact, sober tone preserved.
</success_criteria>

<output>
Create `.planning/quick/260616-huj-clarify-rate-labels/260616-huj-SUMMARY.md` when done.
</output>
