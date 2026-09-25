---
phase: 36-classification-fidelity-attribution
plan: 02
artifact: golden_set_v3.json fixture policy
status: FROZEN — golden_set_v3.json assembled (79 items = 47 v2 + 24 not_crime
  + 8 boundary crime), test_golden_v3.py passes.
---

# 36-GOLDEN-V3.md — golden_set_v3 fixture policy

## Fixture versioning policy (G-28)

- `golden_set_v2.json` is FROZEN: it stays the Phase-34 provenance set and the
  DEPS-03 (Phase 37) reproduction set. `eval_classifier.py` DEFAULT_GOLDEN
  stays v2. No item in v2 is ever edited in place.
- `golden_set_v3.json` (this plan) is the Phase-36 FID-02 gate set: the 47 v2
  items copied byte-identical, plus new keyword-passing non-crime items and
  labelled boundary items, all drawn from real stored production inputs
  (`data/incidents/rejected/*.json`).
- Further growth goes to a `golden_set_v4.json` and never edits v3 in place.

## Step 0 — precondition

`grep -c '^- \[x\] \*\*Phase 35' .planning/ROADMAP.md` → `1`. Same
Phase-35-closed precondition as 36-01 Step 0. Confirmed 2026-09-25.

## Step 0.5 — per-cue availability (G-39, premortem R-06)

Measured 2026-09-25 by a read-only scratchpad script over
`data/incidents/rejected/*.json` (2026-07.json, 2026-08.json, 2026-09.json;
**4,485** stored rejected rows total — one day newer than the 4,427 figure
measured 2026-09-24 in the plan's `<interfaces>`).

| cue | regex | rows matched |
|---|---|---|
| suicide | `suicid\|quit\w* la vida` | **6** |
| institutional/preventive | `reuni[oó]n\|seminario\|anuncia\|plan de seguridad\|balance\|mesa de trabajo\|cuenta p[uú]blica` | **151** |

The 6 suicide-cue rows are the same 6 ids read in the plan's `<interfaces>`
(premortem R-06): `6e01560428d326a1` (femicide, suspect's suicide),
`50db4a0f35b80801` (Ilse Koch anniversary, Germany 1967), `3702eac72a58c587`
(postpartum psychosis health note), `2899498ea6b50be0` (murder-suicide, USA),
`bcacb259d20d6d43` (suicide in Spain with a hate complaint), `d077c357afe3756a`
(stabbing). At most 2 of these are non-crime suicides and none are in Chile —
**the nominal `suicide >= 3` quota cannot be met from stored inputs.** This is
the G-39 shortfall case; the shortfall and the resulting EFFECTIVE_QUOTAS are
recorded in step 3/5 below (after blind labelling assigns final categories).

The 25 candidate ids listed in the plan's `<interfaces>` are **25/25 present**
in stored rows (re-verified 2026-09-25, same as the plan's 2026-09-24 check):

| category | listed ids | n |
|---|---|---|
| accident | 92cd35fd1138995c, 1c49c011fc62c312, 09fb832af5811fae, 5cf2a3a5d46c25a7, c92089ceee13bb8a, 55a4ffa1afc805b3, 3d3ea292cab52e9a, b1257359c32a8956, e89d73a9a375d4a2, dfa687821128d4e5, be407ac7f70b35ba, cd93b9eed2592cce | 12 |
| death_no_crime | de1e92f61b62df4f, 0be6b9e7f7ee99a9, 635bdfeebf2f1033 | 3 |
| fire_emergency | 6d95b6be9d66266d, 578a89d569037cb8, af9b5c6730c423f2 | 3 |
| institutional_preventive | 183889a4fe9aef1c, 5a94f9f836618ec3, dd462453224e1b11 | 3 |
| boundary (labelled, not not_crime) | 4c8b86eb7d7f374e, b2f330935b07d752, 45bf5b41fc7f3eb2, a13b289a57848648 | 4 |

Premortem R-08 (traffic/criminal-liability exclusion candidates, within the
accident category above): `55a4ffa1afc805b3` (driver formalised, pre-trial
detention), `b1257359c32a8956` (drunk driver, serious injuries),
`e89d73a9a375d4a2` (accused detained), `5cf2a3a5d46c25a7` (son-driver
detained) — these 4 are flagged for the labeller's `exclude: true` instruction
(R-08) and are not pre-excluded here; the labeller decides per item.

## Step 1 — candidate pool

Built by a read-only scratchpad script (`build_v3_pool.py`), `v3_selection_seed: 3602`
(gate R1 NB-06 — the same seed is reused in step 3 for any category trim).

Pool construction:
1. All 25 ids listed above.
2. All 6 suicide-cue rows.
3. Institutional cue: 151 rows matched, **> 40**, so `random.Random(3602)` over
   the **sorted** 151 ids drew exactly 40 (`random.Random(3602).sample(sorted_ids, 40)`).
4. Deduped by id (no overlap found between the three sources: 25 + 6 + 40 = 71
   distinct ids pre-filter).
5. Each row's `description` was run through `html.unescape` then `"\xa0" -> " "`
   (FID-06 parity, reimplemented locally per the plan's instruction not to
   import 36-01 code).
6. Kept only rows where `feeds.is_crime_item({"title": title, "description": desc})`
   is `True`. **1 row dropped**: `578a89d569037cb8` ("Viento puelche favoreció
   propagación del incendio en Hotel Altos Nevados") — a fire_emergency
   candidate whose (title, cleaned description) does not contain any
   `CRIME_KEYWORDS` term, so it would never have reached the classifier via the
   production RSS pre-filter in the first place. It is dropped from the pool,
   not relabelled.

**Final candidate pool size: 70** (24 listed25 + 6 suicide + 40 institutional).

| cue in pool | n |
|---|---|
| listed25 (25 minus the 1 keyword-filter drop) | 24 |
| suicide | 6 |
| institutional | 40 |
| **total** | **70** |

Per-category presence in the pool (listed25 subset only; the labeller assigns
final categories independently in step 2 — this table is availability, not a
pre-label):

| category | listed | kept in pool |
|---|---|---|
| accident | 12 | 12 |
| death_no_crime | 3 | 3 |
| fire_emergency | 3 | 2 (1 dropped by the keyword filter, see above) |
| institutional_preventive | 3 | 3 |
| boundary (labelled) | 4 | 4 |

The 70-row pool (title + html-unescaped/NBSP-normalized description only, no
model output, no stage, no family) was written for a fresh-opus blind
labeller to:

```
C:/Users/Carlo/AppData/Local/Temp/claude/C--Users-Carlo-OneDrive---pjud-cl-Documentos-GitHub-Is-Chile-Safe/f0fddcb8-19c9-4f13-b1cc-c394072c3c3f/scratchpad/v3-pool-blind.json
```

A private map (`{id: {source_outlet, source_url, source_id, cue, stored_title_raw}}`)
for later assembly is at:

```
C:/Users/Carlo/AppData/Local/Temp/claude/C--Users-Carlo-OneDrive---pjud-cl-Documentos-GitHub-Is-Chile-Safe/f0fddcb8-19c9-4f13-b1cc-c394072c3c3f/scratchpad/v3-pool-meta.json
```

## Step 4 — shingle guard (premortem R-07)

`pipeline/tests/shingle_guard.py` (stdlib only, no repo imports) implements
`prompt_rules_text`, `normalize`, `shared_shingles`. Verified against the real
prompt (`pipeline/tests/test_shingle_guard.py`, 2026-09-25): `prompt_rules_text`
over `classifier.SYSTEM_PROMPT` / `classifier._COMMUNE_LIST_STR` leaves 1,445
of 10,359 characters, contains no `"commune_name": "<` schema-block marker, and
does not contain "san pedro de la paz" (the known full-prompt collision from
the premortem measurement) after normalization. The guard against the v3
pool/candidate items runs in `test_golden_v3.py` in step 4 of the assembly
task, once v3 is frozen.

## G-77 — boundary shortfall extension (second pool)

The first blind-labelled pool (70 rows) gave not_crime 39 (>= 20 OK; suicide 0
=> G-39 shortfall) but only **4** boundary crimes (< 8, the plan's own STOP
threshold). Per G-77 (2026-09-26, orchestrator, under the owner's 2026-09-24
delegation), because the shortfall came from the pool definition (no boundary
cue was searched in step 1), not from the underlying data, the pool was
**extended** instead of pausing:

- Boundary cue regex: `femicid|parricid|violencia intrafamiliar|VIF|apuñal|baleado|homicidio|asalt|portonazo|encerrona|turbazo|robo con violencia|abuso sexual|violación|agredi|golpiz`
- Population: stored `rejected/*.json` rows matching the cue, excluding
  Google-News rows whose description equals the title, excluding v2/v3 ids and
  the first-pool's 70 ids, passing `feeds.is_crime_item` — **926 matches**.
- Draw: `random.Random(3602).sample(sorted(matches), 40)` — **40 rows**
  (`v3_selection_seed: 3602`, same seed as pool 1, gate R1 NB-06).
- Labelled by a **second, independent, fresh-opus blind labeller**, same
  instructions and blind-input shape as pool 1 (title + html-unescaped
  description only; no model output, no stage, no thresholds).
- Boundary items are taken from **both** pools; the plan's STOP applies only
  to the combined count. Combined boundary crimes = 4 (pool 1) + 6 (pool 2) =
  **10**, of which 8 resolve to a valid CUT (see below) — clears the >= 8 bar,
  no STOP needed.

Blind input: `scratchpad/v3-pool2-blind.json`. Private map:
`scratchpad/v3-pool2-meta.json` (cue = `boundary_ext` for every row). Labels:
`scratchpad/v3-labels2.json`.

## Step 2 — blind labels (record)

| pool | rows | excluded | not_crime | crimes | boundary |
|---|---|---|---|---|---|
| pool 1 (70, step 1) | 70 | 23 | 39 (institutional_preventive 26, accident 6, death_no_crime 3, fire_emergency 2, other_non_crime 2, suicide 0) | 8 | 4 |
| pool 2 (40, G-77 boundary extension) | 40 | 2 | 9 (other_non_crime 6, institutional_preventive 3) | 29 | 6 |
| **combined** | **110** | **25** | **48** | **37** | **10** |

Pool 1's 39 not_crime + 8 crimes + 23 excluded = 70. Pool 2's 9 + 29 + 2 = 40.
Both check out against the labeller's raw output counts.

## Step 3 — assembly

Reproducible by a read-only scratchpad script
(`assemble_v3.py` + `build_golden_v3.py`, seed `random.Random(3602)` for every
draw below — the same seed as steps 1/1-ext per gate R1 NB-06).

### not_crime selection and EFFECTIVE_QUOTAS (G-39)

Nominal quotas: accident >= 6, suicide >= 3, death_no_crime >= 3,
fire_emergency >= 2, institutional_preventive >= 6. Total >= 20, target 24.

Available (combined, non-excluded, both pools): accident 6, suicide **0**,
death_no_crime 3, fire_emergency 2, institutional_preventive 29,
other_non_crime 8 (not part of any nominal quota — held in reserve, unused).

Shortfall: **suicide -3** (0 available against a nominal 3). Per the shortfall
rule, the deficit is filled from `death_no_crime` first — but death_no_crime's
own 3 available items are already fully consumed by its own nominal quota (no
surplus) — so the fill moved to `institutional_preventive`, which has the
largest surplus (29 available vs. 6 nominal). +3 institutional_preventive
items closed the suicide shortfall, bringing the total to the 20-item floor.
A further +4 institutional_preventive items (still well within its 29-item
supply) closed the gap to the 24-item target.

| category | nominal | available | EFFECTIVE quota (selected) |
|---|---|---|---|
| accident | 6 | 6 | **6** |
| suicide | 3 | 0 | **0** (shortfall, filled below) |
| death_no_crime | 3 | 3 | **3** |
| fire_emergency | 2 | 2 | **2** |
| institutional_preventive | 6 | 29 | **13** (6 nominal + 3 shortfall-fill + 4 target-fill) |
| **total not_crime** | >= 20 | 48 | **24** (== target) |

institutional_preventive's 13 kept ids (of 29 available) were drawn with
`random.Random(3602).sample(sorted(ids), 13)` (over-supply draw, gate R1
NB-06). All 6 accident, all 3 death_no_crime, and all 2 fire_emergency
available items were kept (no draw needed — available == or below nominal).
`other_non_crime`'s 8 available items were not needed to hit the 24-item
target and are not in v3 (available for a future v4 if quotas change).

### Boundary crime items (>= 8 required)

All `boundary=true` crime items from both pools (10 total) were resolved via
`pipeline.news.resolver.resolve_cut(ground_truth.commune_name)`:

| id | pool | commune_name | resolves? |
|---|---|---|---|
| 4c8b86eb7d7f374e | pool1 | Coquimbo | yes -> 4102 |
| 6e01560428d326a1 | pool1 | Arica | yes -> 15101 |
| b2f330935b07d752 | pool1 | San Bernardo | yes -> 13401 |
| cc8cccea479378a5 | pool1 | Huechuraba | yes -> 13107 |
| 60320bb51f70fd79 | pool1 | null | **no — dropped** |
| 769afef09d9c8755 | pool1 | null | **no — dropped** |
| fd746c0e79fb6f71 | pool2 | Colina | yes -> 13301 |
| 6e6454aa99cb2cb2 | pool2 | Renca | yes -> 13128 |
| e858c780ffd1a114 | pool2 | Algarrobo | yes -> 5602 |
| 2621b25109f44fc9 | pool2 | Maipú | yes -> 13119 |

**8 of 10 resolve** (2 dropped for a null commune_name — the labeller did not
identify a commune for those two headlines). 8 >= 8: the plan's STOP condition
does not fire. Both `4c8b86eb7d7f374e` and `b2f330935b07d752` (explicitly
named in the plan) are among the 8 kept.

### Exclusions (never enter v3)

25 items were labelled `exclude: true` and are NOT in v3 (17 for being
non-Chile datelines — Indonesia, Nepal, Argentina, Mexico, Spain, Peru,
Ecuador, USA earthquakes/crime — 1 historical (1967 Germany), 4 for the
premortem-R-08 traffic-liability rule (driver detained/formalised/drunk:
`55a4ffa1afc805b3`, `5cf2a3a5d46c25a7`, `b1257359c32a8956`, `c92089ceee13bb8a`,
`e89d73a9a375d4a2`, `dfa687821128d4e5` — note: `5a94f9f836618ec3`, one of the
25 originally-listed institutional_preventive candidates, was also excluded
for describing drunk/drugged-driver detentions rather than a preventive
notice), and 3 miscellaneous (a fraud/money-laundering court case with no
commune, a denial statement with no concrete incident, a querella-announcement
with no location). Full list with per-item reasons:

pool1 exclusions (23): `2899498ea6b50be0`, `44b97cb55db860b2`,
`4959321dc428e074`, `50db4a0f35b80801`, `55a4ffa1afc805b3`,
`5a94f9f836618ec3`, `5cf2a3a5d46c25a7`, `6c1deb5b4dd2aebb`,
`7bf3a03ef172c422`, `8186cf6ecaabf321`, `819b1ac39dc712b8`,
`a888d4b3df6067cd`, `b1257359c32a8956`, `bcacb259d20d6d43`,
`bee8f67576c8a6c8`, `c92089ceee13bb8a`, `ca4e704161816098`,
`cf8ff9897875d977`, `d210d665943a7396`, `dc95068008c33c30`,
`dfa687821128d4e5`, `e89d73a9a375d4a2`, `ed74a3ba93b4dd79`.

pool2 exclusions (2): `99dcedc830b18a08` (Mendoza, Argentina),
`3749a80a0c57c849` (Mexico homicide case).

Per-item reasons are preserved verbatim in `scratchpad/v3-labels.json` and
`scratchpad/v3-labels2.json` (not committed — session scratchpad only); the
exclusion rationale category (non-Chile / historical / traffic-liability /
no-location) is summarized above for the record.

### Shingle pre-check (premortem R-07)

Ran `shared_shingles(headline/description, prompt_rules_text(...), n=5)` for
every one of the 32 new items (24 not_crime + 8 boundary) against the current
`classifier.SYSTEM_PROMPT` rules text. **Zero collisions** — no replacement
was necessary.

## Per-item table (id, source_id, category/family, commune/reason)

| gs3 id | source_id | pool | type | category/commune | label reason (truncated) |
|---|---|---|---|---|---|
| gs3-001 | 09fb832af5811fae | pool1 | not_crime | accident | "tras volcamiento en humedal": vehicle fell into wetland; no crime alleged |
| gs3-002 | 1c49c011fc62c312 | pool1 | not_crime | accident | "Camioneta explota... mina antitanque" at border highway |
| gs3-003 | 3d3ea292cab52e9a | pool1 | not_crime | accident | "cayó con su vehículo a humedal en Valdivia": vehicle accident |
| gs3-004 | 92cd35fd1138995c | pool1 | not_crime | accident | "explosión de camioneta" in "campo minado en el hito 16": landmine |
| gs3-005 | be407ac7f70b35ba | pool1 | not_crime | accident | "investigan el hecho como un accidente... no hay antecedentes de intervención" |
| gs3-006 | cd93b9eed2592cce | pool1 | not_crime | accident | "falleció tras sufrir un accidente en los faldeos del volcán Llaima" |
| gs3-007 | 0be6b9e7f7ee99a9 | pool1 | not_crime | death_no_crime | "encontrado muerto en río San José": body found, cause under investigation |
| gs3-008 | 635bdfeebf2f1033 | pool1 | not_crime | death_no_crime | "muerte de adulto mayor" with dogs eating arm: no crime stated |
| gs3-009 | de1e92f61b62df4f | pool1 | not_crime | death_no_crime | "PDI descarta homicidio... murió de un paro cardíaco": natural death |
| gs3-010 | 6d95b6be9d66266d | pool1 | not_crime | fire_emergency | "incendio en hogar de ancianos" Pitrufquén: fire, no arson mentioned |
| gs3-011 | af9b5c6730c423f2 | pool1 | not_crime | fire_emergency | "incendio que destruyó el Hogar El Edén de Pitrufquén": fire, no arson |
| gs3-012 | 18334610c7e20273 | pool1 | not_crime | institutional_preventive | "Presidente Kast anuncia agenda contra el crimen organizado": policy |
| gs3-013 | 183889a4fe9aef1c | pool1 | not_crime | institutional_preventive | "250 funcionarios reforzarán la seguridad de fonda": preventive deployment |
| gs3-014 | 3c9e4255fea946b1 | pool1 | not_crime | institutional_preventive | "Gobierno evalúa implementar estado de excepción": policy news |
| gs3-015 | 3ea1ccc99ef31ff9 | pool1 | not_crime | institutional_preventive | "Gobierno plantea aplicar Estado de Excepción": policy news |
| gs3-016 | 476837ef11c7893d | pool1 | not_crime | institutional_preventive | Opposition critique of Kast security plan; political news |
| gs3-017 | 6088823df8bfa6f6 | pool1 | not_crime | institutional_preventive | "Protestas del 11 de septiembre dejaron 284 detenidos en el país": aggregate |
| gs3-018 | 84da3e065a148f23 | pool1 | not_crime | institutional_preventive | "Gobierno anuncia baja en homicidios": statistics |
| gs3-019 | 89e3a73217471d94 | pool2 | not_crime | institutional_preventive | 'Subsecretario de DD.HH. cuestiona visita del INDH' - political comment |
| gs3-020 | 93a5b1357f23c9ad | pool1 | not_crime | institutional_preventive | "Balance final de Fiestas Patrias": aggregate statistics |
| gs3-021 | 9de88e1e6aca774b | pool2 | not_crime | institutional_preventive | 'presentó un proyecto que propone castigar' - legislative bill |
| gs3-022 | b4731bb11786d29f | pool1 | not_crime | institutional_preventive | "Gobierno anuncia baja en homicidios": statistics |
| gs3-023 | b4fb5b8831aa1fb7 | pool1 | not_crime | institutional_preventive | "Balance de seguridad Ministro Arrau": statistics |
| gs3-024 | bcc1507bf29d092d | pool1 | not_crime | institutional_preventive | "subsecretario Guerrero con los alcaldes... Ley de Seguridad": institutional |
| gs3-025 | 2621b25109f44fc9 | pool2 | boundary/propiedad | Maipú | 'banda dedicada al robo de vehículos en Maipú' ligada a robo con homicidio |
| gs3-026 | 4c8b86eb7d7f374e | pool1 | boundary/robos_violentos | Coquimbo | "robo con violación... tres detenidos tras persecución" |
| gs3-027 | 6e01560428d326a1 | pool1 | boundary/vida | Arica | "Fiscalía investiga como femicidio... San Miguel de Azapa" |
| gs3-028 | 6e6454aa99cb2cb2 | pool2 | boundary/vida | Renca | 'robo con homicidio del carabinero ... en la comuna de Renca' |
| gs3-029 | b2f330935b07d752 | pool1 | boundary/propiedad | San Bernardo | "Robo de camión con celulares en San Bernardo: capturan a tres" |
| gs3-030 | cc8cccea479378a5 | pool1 | boundary/armas | Huechuraba | "ataques con bombas molotov a Carabineros y Bomberos en Huechuraba" |
| gs3-031 | e858c780ffd1a114 | pool2 | boundary/sexuales | Algarrobo | 'secuestró a ex, la golpeó y agredió sexualmente' in Algarrobo |
| gs3-032 | fd746c0e79fb6f71 | pool2 | boundary/vida | Colina | 'robo y homicidio de un hombre ... en Colina' |

## v3 source_ids (leakage guard for 36-08 / 36-10 audit samples)

36-08 and 36-10 must exclude these 32 `source_id` values from their audit
samples:

```
09fb832af5811fae, 1c49c011fc62c312, 183889a4fe9aef1c, 18334610c7e20273,
2621b25109f44fc9, 3c9e4255fea946b1, 3d3ea292cab52e9a, 3ea1ccc99ef31ff9,
476837ef11c7893d, 4c8b86eb7d7f374e, 6088823df8bfa6f6, 635bdfeebf2f1033,
6d95b6be9d66266d, 6e01560428d326a1, 6e6454aa99cb2cb2, 84da3e065a148f23,
89e3a73217471d94, 92cd35fd1138995c, 93a5b1357f23c9ad, 9de88e1e6aca774b,
af9b5c6730c423f2, b2f330935b07d752, b4731bb11786d29f, b4fb5b8831aa1fb7,
bcc1507bf29d092d, be407ac7f70b35ba, cc8cccea479378a5, cd93b9eed2592cce,
de1e92f61b62df4f, e858c780ffd1a114, fd746c0e79fb6f71, 0be6b9e7f7ee99a9
```

## Final composition

- **Total: 79** (47 v2 + 32 new)
- **not_crime: 24** (accident 6, death_no_crime 3, fire_emergency 2,
  institutional_preventive 13, suicide 0)
- **boundary: 8** (robos_violentos 1, vida 3, propiedad 2, armas 1, sexuales 1)
- `pipeline/tests/test_golden_v3.py`: 8 passed (structure, quotas, boundary,
  html-entity, shingle-guard).
- `golden_set_v2.json`: byte-identical, no diff.
