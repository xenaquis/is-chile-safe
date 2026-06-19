# SEED-002 — Multi-Source Crime-Metric Enrichment: Findings & Go/No-Go

**Date:** 2026-06-19
**Method:** Autonomous browseros + WebSearch/WebFetch feasibility sweep (inline, main loop), feasibility-confirm depth, all 14 inventoried sources.
**Spikes:** `.planning/spikes/004-enusc-victimization` · `005-justice-funnel` · `006-special-crime-truth` · `007-supplementary-triage`
**Question:** Should we enrich the CEAD-only composite index with other official sources to combat infra-representation **before Phase 22 go-live** — and if so, how?

---

## TL;DR — Recommendation

**GO on a narrow, additive enrichment. NO-GO on a full multi-source funnel rebuild.**

Of 14 sources, **exactly one** adds genuinely new anti-infra-representation signal *at the site's unit (comuna)*: **ENUSC communal victimization (SAE)**, newly published by INE on 2026-01-21 for **136 of 346 comunas**. This is the only source that measures *unreported* crime (cifra negra) at comuna level — precisely the expert's concern.

Every other candidate is one of: **duplicative** of CEAD's existing police input (Carabineros, PDI, INE police layer), **sub-comuna** (Fiscalía, Poder Judicial, Gendarmería, INE judicial → regional at best), **wrong unit** (Gendarmería = prison location ≠ crime location), **statistically too small per comuna** (femicide), or **national-only / out-of-scope** (UAF, Aduanas, SML, juvenile reintegration). The homicide truth-source (Observatorio/SPD VHC) is **already integrated** (index M1).

**Bottom line:** Go-live is **not blocked**. The CEAD core (with its existing caveats) can ship. The single high-value enrichment — an **additive ENUSC "victimization context" layer** — is a small, optional phase that can slot before or after Phase 22 without touching any Phase-18 locked decision.

---

## The 14-source evaluation grid

Bars: **Comuna?** (drives the 346-choropleth) · **Per-100k?** (composite-compatible) · **New signal vs CEAD?** (anti-infra-rep) · **Editorial fit** · **Effort/risk**.

| # | Source | Scrapeable / format | Comuna? | Periodicity | Per-100k | New signal (anti-infra-rep) | Editorial | Effort | **Verdict** |
|---|--------|---------------------|---------|-------------|----------|-----------------------------|-----------|--------|-------------|
| 1 | **INE Policiales-Judiciales** | Excel (2013–Q1'25), annual boletines | ✗ regional | Annual + semestral | ✓ | LOW — police dup CEAD; judicial/custody regional | ✓ | Low | Regional caveat only |
| 2 | **ENUSC (INE/Min.Seg)** | `tabulados-sae--enusc-2024-vhdv.xlsx` + ArcGIS map | **✓ 136/346 (SAE)** | Annual (communal SAE new 2026, continuity TBD) | ✓ (victimization rate) | **HIGH — only cifra-negra source** | ✓ w/ "experimental/modelado" caveat | Low-Med | **✓ INTEGRATE** |
| 3 | **Fiscalía (SAF)** | Power BI `view` embed + Excel boletines | ✗ regional | Semestral/annual (2026) | ✓ | MED (prosecution) but regional | ✓ | **High (brittle PBI)** | ✗ comuna |
| 4 | **Poder Judicial** | DECS one-off Excel; PDF boletines | ✗ tribunal | Irregular/static | ✓ | MED (courts) but no sustained feed | ✓ | High | ✗ |
| 5 | **Defensoría Penal (SIGDP)** | Informes | ✗ | — | ~ | LOW (only defended subset) | ✓ | — | ✗ |
| 6 | **Gendarmería** | Interactive region tables | ✗ region | Monthly | unit mismatch | LOW + **prison loc ≠ crime loc** | ✓ | Med | ✗ wrong unit |
| 7 | **Reinserción Juvenil** | Semestral PDF, by zone | ✗ zone | Semestral | ~ | LOW (sanctioned youth, not incidence) | ✓ | Med | ✗ |
| 8 | **Observatorio Homicidios (SPD)** | Informe Nacional (validated) | **✓** | Annual+semestral | ✓ (6.0/100k) | HIGH (homicide truth) | ✓ | — | **✓ ALREADY IN USE (M1)** |
| 9 | **SernamEG / CIF femicidio** | Annual report PDF | ✗ (counts tiny ~43/yr) | Annual | region | MED but sub-comuna noise | ⚠ sensitive | Med | ✗ comuna (nat/regional ctx) |
| 10 | **Carabineros / datos.gob.cl** | **Comuna CSV** (DMCS, VIF, drogas) | **✓** | Periodic | ✓ | **NONE — same source as CEAD** | ✓ | Low | ~ duplicate (cleaner path) |
| 11 | **PDI / INE** | Via CEAD/INE | ✓ via CEAD | — | ✓ | NONE (already in CEAD) | ✓ | — | ~ duplicate |
| 12 | **Servicio Médico Legal** | datos.gob.cl datasets | partial | Irregular | ~ | LOW complementary, dated | ✓ | Med | ✗ |
| 13 | **UAF** | National ROS reports | ✗ national | Annual | ✗ | LOW (econ crime, not street) | ✓ | — | ✗ national only |
| 14 | **Aduanas** | National/port seizures | ✗ national | Periodic | ✗ | LOW (cross-border) | ✓ | — | ✗ national only |

**Shortlist of viable sources:** ENUSC (#2, new) · Observatorio homicidios (#8, already integrated) · Carabineros datos.gob.cl (#10, cleaner duplicate of an existing input — *not* enrichment).

**Key surprise:** the seed/expert assumed ENUSC was "probablemente NO por comuna." As of **2026-01-21** that is no longer true — INE's SAE communal release flips the single most important source from "regional caveat only" to "comuna-level feasible (partial)." This is the finding that makes a GO possible at all.

---

## Candidate metric designs

All designs keep Phase-18 locked decisions intact (D-03 SII fallback, locked weights, [0,100] winsorized min-max, 5-band levels, SPD VHC = homicide truth). Enrichment is **additive/versioned**, never a silent rewrite.

### Design A — Additive ENUSC victimization layer  ✅ RECOMMENDED
- **What:** Keep the CEAD composite index exactly as-is. Add a **separate, parallel "victimization context" indicator** sourced from ENUSC SAE VHDV, shown *alongside* the reported-crime index on comuna pages for the 136 covered comunas.
- **Traceability:** ENUSC `.xlsx` → new **F-series figure(s)** → `SOURCES.md` canonical block (INE ENUSC SAE, experimental). Zero-orphan discipline preserved.
- **Graceful degrade:** 210 comunas without an estimate render a "Sin estimación de victimización ENUSC para esta comuna (cobertura 136 comunas)" caveat; CEAD index still shown.
- **Editorial:** labeled "estimación modelada / estadística experimental," attributed to INE, never an absolute verdict. EN/ES parity.
- **Effort:** ~1 small phase — one annual XLSX scraper (136 rows), figure-registry entries, SOURCES block, one comuna-page UI module (EN/ES), degrade logic. ~$0 infra.
- **Why it wins:** directly answers the infra-representation concern at comuna level, cheaply, additively, with honest coverage caveats.

### Design B — Region-level under-reporting adjustment factor
- **What:** Derive an ENUSC-based "reporting gap" factor at **region** level and present it as a documented regional context band (optionally an adjusted secondary index variant).
- **Trade-offs:** region-only (16 values, not 346); mixes measures (victimization vs reported) which is methodologically delicate; higher explanation burden. Useful as a complement to A, **not** a substitute.
- **Effort:** Med. **Defer** (post-launch consideration).

### Design C — Full multi-stage funnel composite  ❌ REJECTED
- **What:** Blend prosecution (Fiscalía) + courts (PJUD) + custody (Gendarmería) into a funnel index.
- **Why rejected:** Spike 005 proved none are comuna-level on a sustainable feed (Fiscalía = brittle Power BI, PJUD = one-off snapshots, Gendarmería = region + wrong unit). The result would be mostly regional and partly duplicative of CEAD — high effort, low marginal comuna signal, against the ~$0/fail-gracefully constraints.

---

## Go / No-Go

| Decision | Verdict | Rationale |
|----------|---------|-----------|
| **Block go-live to rebuild the metric?** | **NO** | CEAD core + existing caveats is shippable. No source forces a pre-launch rewrite. |
| **Enrich with ENUSC victimization (Design A)?** | **GO (narrow, additive, optional timing)** | Only true comuna-level anti-infra-rep gain; cheap; additive; honest caveats. Slot as one small phase before or right after Phase 22. |
| **Build the regional funnel band (B) / full funnel (C)?** | **NO (defer / reject)** | Sub-comuna, brittle, duplicative, high effort. Revisit only if Fiscalía/PJUD publish comuna open data later. |
| **Swap CEAD ingestion to Carabineros datos.gob.cl CSV?** | **Out of scope (tech-debt note)** | Not enrichment; a possible robustness improvement for the known CEAD-endpoint fragility — track separately. |

**One-line answer for the user:** *Ship on CEAD. The one worthwhile enrichment is an additive ENUSC communal-victimization layer (136/346 comunas, new since Jan 2026) — small phase, no Phase-18 changes; everything else the expert listed is duplicative, sub-comuna, or national-only.*

---

## Constraints honored
- No absolute "seguro/peligroso" verdicts; every proposed figure attributed + caveated.
- Additive/versioned vs Phase-18 locks; comuna unit = 346; CEAD rates already per-100k (not rescaled).
- ~$0 infra (one annual XLSX); fail-gracefully (210-comuna degrade path); EN/ES + SEO-static compatible.
- Research/feasibility only — **no production metric change without user sign-off.**

## Suggested next step
If GO on Design A: `/gsd-quick` or a small `/gsd-plan-phase` — "ENUSC communal-victimization additive layer" — with the ENUSC SAE `.xlsx` as the single new input. Otherwise, file Design A as a backlog item and proceed to Phase 22 on CEAD.
