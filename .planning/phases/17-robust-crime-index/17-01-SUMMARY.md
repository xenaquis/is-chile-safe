# Phase 17 — Wave 0 Spike Results (S1 + S4)

**Run:** 2026-06-18, local Chilean egress (sandbox returns HTTP 403; local OK).
**Scripts:** `pipeline/experiments/test_subgroup_discovery.py` (initial),
`probe_grupo_totals.py`, `probe_grupo_catalog.py`, `probe_delito_tree.py` (refinements).
**Raw output:** `pipeline/cache/*.txt`, full taxonomy in `17-CEAD-CATALOG.json`.

---

## TL;DR — answers to the runbook stubs

- `lesiones`   → `grupo[] = 103, 104, 105`  (familia 1) — **three grupos, not one**
- `secuestros` → `familia[] = —  grupo[] = —`  → **NOT in CEAD at all** (see S1c)
- `tipoVal` mapping → denuncias=`1`  detenciones=`2`  aprehendidos=`3`
- additive? → **YES** (`1+2 == "1,2"`, `1+2+3 == "1,2,3"`, exact)

---

## S1 — CEAD grupo/subgrupo catalog (FULLY ENUMERATED)

The delito selectors are populated by `POST ajax_2.php` with `seleccion=9`
(familia → grupos) — **not** the codes the original spike tried. The response
returns `opcionGrupos` / `opcionSubgrupos` as HTML with
`ckH('grupo_<id>', level, '<id>', '<name>')`. Key structural fact:

> The grupo/subgrupo list is **GLOBAL** — `ajax_2.php seleccion=9` returns the
> same 22 grupos + 45 subgrupos regardless of the `familia` param. The familia
> is encoded as the **first digit of the grupo id** (1xx=vida, 2xx=robos
> violentos, 3xx=vif, 4xx=drogas, 5xx=armas, 6xx=propiedad, 7xx=incivilidades,
> 999=otros). The *data* endpoint (`get_estadisticas_delictuales.php`) still
> filters correctly by `grupo[]`.

### Familia 1 (vida) grupos — confirmed names + 2024 national counts
(`medida=1`, `tipoVal="1,2"`, TOTAL PAÍS; via `probe_grupo_totals.py`)

| grupo | name | 2024 count | metric mapping |
|------:|------|-----------:|----------------|
| 101 | Homicidios y femicidios | 1,019 | homicidio (but see note) |
| 102 | Violaciones y otros delitos sexuales | 21,436 | (sexual — not in 7-metric taxonomy) |
| 103 | Lesiones graves o gravísimas | 7,283 | **lesiones** |
| 104 | Lesiones menos graves | 9,391 | **lesiones** |
| 105 | Lesiones leves | 60,634 | **lesiones** |
| 106 | Amenazas | 154,107 | (not lesiones) |

> ⚠️ The original spike's `_nonzero_rows()` heuristic was structurally broken
> (expected flat numeric cells; `parse_cead_table` returns nested
> `{'values': {year: 'NNN,0000000000'}}` strings), so it reported `nonzero=0`
> for **every** grupo and never dumped magnitudes. Had it "worked" it would
> have flagged grupo 106 (154k, the largest) as lesiones — **wrong**; 106 is
> Amenazas. Lesiones is the 103/104/105 triplet. Fixed in `probe_grupo_totals.py`.

### Lesiones decision (for Wave 1/2)
`lesiones` = **sum of grupos 103 + 104 + 105** (graves/gravísimas + menos graves
+ leves) ≈ 77,308 nationally 2024. Subgrupo equivalents: 10301 / 10401 / 10501.
VIF-context lesiones (subgrupos 30101/30102) are a *separate* familia — do NOT
double-count them into `lesiones` (they belong to the VIF metric).

### Homicide note (affects D-HOM)
Grupo 101 is "Homicidios **y femicidios**" combined. Homicide alone = subgrupo
**10101**, femicidio = 10102 — but `subgrupo[]` is silently ignored by the data
endpoint (Phase 14 finding), so CEAD cannot isolate homicide from femicide at
grupo granularity. Reinforces **D-HOM → switch to SPD** for the homicide metric.

### S1c — secuestros: NOT IN CEAD (blocking finding)
Full enumeration of all 7 familias → 22 grupos → 45 subgrupos contains **no
secuestro / kidnapping entry**. CEAD's current taxonomy (the post-2024 "7
familias" scheme) simply does not track secuestro. Closest libertad-type
offence: none present.

**Implication for D-TAX:** the 7th metric (`secuestros`) cannot be sourced from
the CEAD subgroup API. It needs an alternate source — same situation as homicide
(D-HOM→SPD). Candidates to investigate in a new spike: Fiscalía/Ministerio
Público boletines estadísticos (secuestro/sustracción de personas), or the
legacy CEAD DMCS classification. **Add S5 to Wave 0** before committing to the
7-metric taxonomy, or demote `secuestros` from the headline set if no national
commune-level source exists.

---

## S4 — tipoVal measure codes (denuncias / detenciones / aprehendidos)

Probe: homicide grupo 101, `medida=1` (counts), 2024, TOTAL PAÍS, vary tipoVal.

| tipoVal | 2024 count | meaning |
|--------:|-----------:|---------|
| `1`     | 287   | Denuncias |
| `2`     | 732   | Detenciones (flagrantes) |
| `3`     | 349   | Aprehendidos (personas) |
| `1,2`   | 1,019 | **Casos policiales** (= 1 + 2) |
| `1,2,3` | 1,368 | (= 1 + 2 + 3) |

**Additivity: CONFIRMED exact.** `287+732 = 1,019` and `287+732+349 = 1,368`.
The codes are strictly additive at the offence level.

Label mapping is inferred from (a) the CEAD page text ordering — *"casos
policiales, denuncias, detenciones flagrantes y personas aprehendidas"* — and
(b) the established fact that `tipoVal="1,2"` = casos policiales. The
1/2/3 → denuncias/detenciones/aprehendidos assignment should be **visually
re-confirmed on the CEAD UI** before locking the schema, but the magnitudes are
internally consistent.

**D-AGG constraint (satisfied):** because the measures are additive and a single
event can appear as both a denuncia and an aprehensión, the index must **pick a
measure semantics per offence and normalize per offence** — never naively sum
denuncias + detenciones + aprehendidos as independent events. Recommended: keep
`casos policiales` (`1,2`) as the canonical incidence measure, and surface
`aprehendidos` (`3`) separately as a clearance/enforcement signal rather than
folding it into incidence.

---

## Status of Wave 0 spikes

| Spike | Status |
|-------|--------|
| S1 lesiones | ✅ DONE — grupos 103/104/105 |
| S1 secuestros | ⛔ BLOCKED — not in CEAD; needs alternate source (new S5) |
| S4 tipoVal | ✅ DONE — additive; 1=denuncias 2=detenciones 3=aprehendidos |
| S2 SPD homicide | ✅ DONE — see 17-02-SUMMARY.md (comuna-level VHC xlsx) |
| S3 exposure proxy (SII) | ✅ DONE — see 17-02-SUMMARY.md (PUB_COMU.xlsb 2024) |
| **S5 secuestro source (NEW)** | ⚠️ PARTIAL — see 17-02-SUMMARY.md (Fiscalía, regional only) |

**Next:** S2/S3/S5 resolved in `17-02-SUMMARY.md`. Wave 0 complete enough to
plan Wave 1 (pipeline). Only open item: secuestro comuna granularity (S5b),
non-blocking if v1 ships secuestro at region level.
