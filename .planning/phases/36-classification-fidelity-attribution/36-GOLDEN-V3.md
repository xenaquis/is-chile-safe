---
phase: 36-classification-fidelity-attribution
plan: 02
artifact: golden_set_v3.json fixture policy
status: DRAFT — steps 0-1 and step-4 helper done; step 2 (blind labelling) is
  running out-of-process; steps 3 and 5 (assembly + this file's remaining
  sections) are written by the resumed executor after labelling completes.
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

## Steps 2, 3, 5 — pending

Step 2 (blind labelling) is delegated to a fresh-opus subagent operating on
`v3-pool-blind.json` only (no model output, no stage, no thresholds shown).
Steps 3 (assembly of `golden_set_v3.json` + `test_golden_v3.py`) and 5 (the
rest of this file: EFFECTIVE_QUOTAS, exclusions, shingle-driven replacements,
per-item table, source_id leakage list) are written by the executor once
labelling results are available.
