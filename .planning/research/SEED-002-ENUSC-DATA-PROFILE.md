# SEED-002 — ENUSC VHDV Data Profile (grounding for Phase 23)

**Purpose:** Real-schema grounding for Phase 23 (ENUSC Communal Victimization Layer), captured inline via browseros + Python before planning, so the plan is built on the actual file — not assumptions.
**Captured:** 2026-06-19.

---

## Provenance

| Field | Value |
|-------|-------|
| Source | INE — Estadísticas Experimentales: Seguridad Ciudadana (ENUSC 2024, modelo SAE) |
| Indicator | **VHDV** — Victimización en Hogares por Delitos Violentos |
| Resolved file URL | `https://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/cuadros-estadisticos/2024/tabulados-sae--enusc-2024-vhdv.xlsx?sfvrsn=671c099f_4` |
| Landing page | `https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana` |
| How to reach (no stable URL) | The file is NOT linked statically — drill INE's JS widget: tab **CUADROS ESTADÍSTICOS** → node **cuadros estadísticos** → year **2024** → file appears. The `?sfvrsn=` token may rotate on republish; re-resolve via the widget each acquisition. |
| Metodología | `http://www.ine.gob.cl/docs/default-source/estadisticas-experimentales-seguridad-ciudadana/publicaciones-y-anuarios/2024/presentación-metodología-sae--enusc-2024.pdf?sfvrsn=2f5e8b5a_4` |
| ArcGIS map | `https://experience.arcgis.com/experience/53d8caa5ab904894bb9b52ba6189c5cf` |
| Local cache (git-ignored) | `pipeline/cache/enusc_vhdv.xlsx` |
| Size | 31,063 bytes |
| **sha256** | `ad9503826fd21590eca7cf37629872df09f3115ad0c6d80dfe5cedcb63c3d4ba` |
| Licence | Datos Abiertos Gobierno de Chile (INe terms) |
| Status | **Estadística experimental** (INE's own label — SAE, "etapa inicial de madurez") |
| Vintage | Reference year 2024; communal SAE first published 2026-01-21. Annual continuity NOT guaranteed. |

---

## Verified schema

Single sheet `Hoja1`, range `A1:G139`. Title in row 1, blank row 2, **header in row 3**, **data rows 4–139 = 136 comunas**.

| Col | Header (trimmed) | Type | Notes |
|-----|------------------|------|-------|
| A | Código comuna | string digits | CUT, raw/un-padded (`10101`, `1101`, `13101`) — **matches project CUT convention exactly** |
| B | Nombre comuna | string | |
| C | Porcentaje de hogares víctimas de delitos violentos 2024 | float | **Proportion 0–1** (e.g. 0.0478 = 4.78%). A rate already — NOT per-100k; do not rescale |
| D | Límite inferior | float | CI lower bound (proportion) |
| E | Límite superior | float | CI upper bound (proportion) |
| F | Tipo de estimación | enum | `Directa y sintética` (115) / `Sintética` (21) |
| G | Coeficiente de variación logarítmico | float | CV (precision quality) |

> Terminal showed mojibake (`C�digo`) — that is display-only; cell values decode fine (UTF-8). Headers carry trailing spaces/newlines — strip on parse.

## Verified validation (Python/openpyxl)

- **136 data rows, 136 unique CUTs, 0 duplicates.**
- **All 136 CUTs already exist** in `data/cead/comunas/*.json` (346 files) → 0 unknown. **Direct CUT join works; the name→CUT resolver is only a cross-check, not the primary mapping.**
- Value (proportion) range **0.031 – 0.1764** (Quinta Normal 17.6% highest; La Cisterna, Cerro Navia, La Pintana, Cerrillos next — all RM; plausible).
- CV range **0.0306 – 0.0875** — every estimate well under 0.15. **No low-precision suppression needed** at this vintage (but keep a CV/estimation-type quality flag in the pipeline for future vintages).

---

## Implications for the Phase 23 plan (refines VL-01..VL-05)

1. **VL-02 is largely pre-satisfied** — CUT is in the file as raw digits; join directly to existing comuna JSON. Keep the build-time assertion (all rows resolve to a valid CUT, count == 136) and use the name→CUT resolver as a redundant cross-check only.
2. **Unit is a percentage, not per-100k** — reinforces "parallel labeled indicator, never merged into the per-100k composite." Display as a % of households.
3. **Richer caveat available** — the file ships CIs (cols D/E) and CV (col G). VL-03's caveat can honestly show the estimate with its confidence range and "experimental/SAE-modeled" label; optionally surface the CI.
4. **Quality flags** — carry `tipo_estimacion` and `cv` into the snapshot; 21 comunas are "Sintética" (model-only, slightly weaker) — candidate for a subtle footnote, not exclusion.
5. **Ingestion (user-approved manual/assisted snapshot)** — mirror the SPD/SII convention: fetcher `pipeline/snapshots/fetch_enusc_vhdv.py`, committed processed snapshot `data/snapshots/enusc_vhdv.json`, and an entry in `data/snapshots/ATTRIBUTION.md`. Raw `.xlsx` stays in git-ignored `pipeline/cache/`. Because there is no stable URL, the fetcher should either accept the resolved URL as a param/config or assert the sha256 of a manually-dropped cache file before processing.
6. **Additive-only (VL-05)** — none of this touches the composite pipeline; `data/snapshots/` is the established REFERENCE-ONLY area, and wiring to comuna pages is purely additive UI.
