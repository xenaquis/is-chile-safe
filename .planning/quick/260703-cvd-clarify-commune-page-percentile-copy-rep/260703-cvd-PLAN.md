---
phase: quick-260703-cvd
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [site/src/config/i18n.ts]
autonomous: true
requirements: [CVD-01]
must_haves:
  truths:
    - "Commune national rank card reads as one explicit directional sentence: 'More reported crime than {pct}% of Chile's communes' (EN) / 'Más delitos reportados que el {pct}% de las comunas de Chile' (ES)"
    - "Commune regional rank card reads coherently: 'More reported crime than {pct}% of communes in {region}' / 'Más delitos reportados que el {pct}% de las comunas de {region}'"
    - "No forbidden absolute wording (safe/dangerous/seguro/peligroso) is introduced"
    - "Direction stays consistent with rank #1 = most reported incidence"
    - "Build + validate pass after the copy change"
  artifacts:
    - path: "site/src/config/i18n.ts"
      provides: "rank_pct_value + rank_national_label rewritten in EN_STRINGS and ES_STRINGS"
      contains: "More reported crime than"
  key_links:
    - from: "site/src/config/i18n.ts (rank_pct_value)"
      to: "site/src/pages/commune/[slug].astro & site/src/pages/es/comuna/[slug].astro"
      via: "StatCard value/label props"
      pattern: "rank_pct_value.replace"
---

<objective>
Clarify the ambiguous commune-page percentile card copy. Today the national card renders "Higher than 99%" (big) over "of Chile's communes (reported incidence)" (small), which reads as "higher than 99% of Chile's communes" — higher WHAT is left implicit and the qualifier is buried in a parenthetical. Rewrite the copy so the value+label render as ONE explicit directional sentence that names the thing compared (reported crime), in both EN and ES.

Purpose: Remove reader ambiguity on the single most-viewed stat on commune pages, while staying within editorial/legal constraints (attributed, "reported" qualifier, no safe/dangerous verdict).
Output: Updated strings in `site/src/config/i18n.ts` (EN_STRINGS + ES_STRINGS).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<interfaces>
<!-- StatCard renders value (28px bold) over label (14px) over optional sublabel (14px light).
     The value+label are read together as a sentence, so the compared quantity must live in
     the value string, not only the label. Extracted from site/src/components/StatCard.astro. -->

Card wiring (site/src/pages/commune/[slug].astro lines 260-269; ES mirror at
site/src/pages/es/comuna/[slug].astro lines 264-271) — DO NOT edit these files:
```
value={t.rank_pct_value.replace('{pct}', String(natPct))}
label={t.rank_national_label}
sublabel={t.rank_sublabel.replace('{year}', ...).replace('{rank}', ...).replace('{total}', ...)}
```

Current strings (site/src/config/i18n.ts):
- EN line 229: rank_pct_value: 'Higher than {pct}%'
- EN line 230: rank_national_label: "of Chile's communes (reported incidence)"
- EN line 231: rank_regional_label: 'of communes in {region}'
- EN line 232: rank_sublabel: 'CEAD {year} · #{rank} of {total} · 1 = most reported incidence'
- ES line 436: rank_pct_value: 'Mayor que el {pct}%'
- ES line 437: rank_national_label: 'de las comunas de Chile (incidencia reportada)'
- ES line 438: rank_regional_label: 'de las comunas de {region}'
- ES line 439: rank_sublabel: 'CEAD {year} · #{rank} de {total} · 1 = mayor incidencia reportada'
</interfaces>

Usage grep (confirms `rank_pct_value` / `rank_national_label` are ONLY consumed by the two
commune-page templates — no other context breaks when rephrased):
- site/src/pages/commune/[slug].astro
- site/src/pages/es/comuna/[slug].astro
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rephrase percentile card copy directionally in EN and ES</name>
  <files>site/src/config/i18n.ts</files>
  <action>
Edit four string values only (no interface, no logic, no template changes). Per CVD-01, move the compared quantity ("reported crime") into `rank_pct_value` so value+label read as one explicit sentence, and drop the now-redundant national parenthetical.

EN_STRINGS (around lines 229-230):
- `rank_pct_value`: change `'Higher than {pct}%'` to `'More reported crime than {pct}%'`
- `rank_national_label`: change `"of Chile's communes (reported incidence)"` to `"of Chile's communes"`

ES_STRINGS (around lines 436-437):
- `rank_pct_value`: change `'Mayor que el {pct}%'` to `'Más delitos reportados que el {pct}%'`
- `rank_national_label`: change `'de las comunas de Chile (incidencia reportada)'` to `'de las comunas de Chile'`

Leave `rank_regional_label` unchanged in both locales — it now reads coherently with the new value ("More reported crime than {pct}% of communes in {region}" / "Más delitos reportados que el {pct}% de las comunas de {region}"). Leave `rank_sublabel` unchanged in both locales — it already carries CEAD attribution plus the "1 = most reported incidence / 1 = mayor incidencia reportada" direction note, which stays consistent with rank #1 = most reported incidence (per memory national-rank-direction).

Constraints: keep the "reported/reportado(s)" qualifier (no unqualified "crime/delito" implying actual prevalence); introduce NO absolute safe/dangerous/seguro/peligroso wording. Preserve the existing single-quote vs double-quote style already used on each line (EN national label uses double quotes because of the apostrophe in "Chile's").
  </action>
  <verify>
    <automated>cd site && npm run build && npm run validate</automated>
  </verify>
  <done>All four strings updated; `cd site && npm run build && npm run validate` completes green (build succeeds, validator suite passes). Rendered national card reads "More reported crime than {pct}%" / "of Chile's communes" (EN) and "Más delitos reportados que el {pct}%" / "de las comunas de Chile" (ES); regional card reads coherently with the same value; no forbidden wording introduced.</done>
</task>

</tasks>

<verification>
- `cd site && npm run build && npm run validate` (ONE chained command — OneDrive dist desync gotcha) passes.
- Grep confirms `rank_pct_value` / `rank_national_label` are consumed only by the two commune templates, so no other page context is affected by the rephrase.
</verification>

<success_criteria>
- National and regional commune rank cards each read as one explicit directional sentence naming the compared quantity (reported crime) and the comparison set (Chile's communes / communes in region).
- "reported/reportado" qualifier retained; no safe/dangerous verdict language.
- Direction consistent with rank #1 = most reported incidence.
- Build + validate green.
</success_criteria>

<output>
Create `.planning/quick/260703-cvd-clarify-commune-page-percentile-copy-rep/260703-cvd-SUMMARY.md` when done.
</output>
