# Phase 1: Data Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 1-Data Foundation
**Areas discussed:** Estrategia de extracción, Alcance y granularidad, Población y cálculo de tasas, Fallos y alertas

---

## Estrategia de extracción

| Option | Description | Selected |
|--------|-------------|----------|
| Excel bulk | `descarga=true` entrega datasets completos — menos requests, menos parsing frágil | ✓ |
| Tablas HTML por request | Por comuna/familia/año, parsing bs4+lxml — más granular pero más carga y frágil | |
| Híbrido según researcher | Researcher valida ambos y elige | |

**User's choice:** Excel bulk, con fallback HTML automático en el mismo run si el formato cambia (pregunta 2), rate limiting 2–3 s + backoff (pregunta 3), raw cacheado local sin commitear (pregunta 4).

---

## Alcance y granularidad

| Option | Description | Selected |
|--------|-------------|----------|
| Familias + grupos | 7 familias para mapa + 22 grupos para desglose/páginas | ✓ |
| Solo 7 familias | Mínimo, archivos chicos, menos contenido SEO | |
| Todo incl. subgrupos | Máxima riqueza, ~3x datos | |

**User's choice:** Familias + grupos; serie anual 2005–presente; solo casos policiales (tipoVal=1,2); map-payload del último año (total + 7 familias) más `map-payload-{año}.json` por año.
**Notes:** Mid-discussion el usuario pidió relevancia para **homicidios** (menor cifra negra), **secuestros** y **delitos contra la propiedad** → se acordó incluir subgrupos selectivos si CEAD solo los expone a ese nivel, con flag `featured` en el schema.

---

## Población y cálculo de tasas

| Option | Description | Selected |
|--------|-------------|----------|
| Tasas CEAD (medida=2) + población INE aparte | Tasas oficiales de la fuente; INE solo para ranking/contexto | ✓ |
| Calcular nosotros (frecuencia/INE) | Control total pero riesgo de divergencia con CEAD | |
| Ambas y comparar | Validación cruzada, más requests | |

**User's choice:** Tasas CEAD; población = proyecciones INE estáticas commiteadas (researcher localiza dataset); comunas <10k excluidas de ranking con `rank: null` + flag pero con tasa visible; trend = variación % últimos 3 años con umbral ~5%.

---

## Fallos y alertas

| Option | Description | Selected |
|--------|-------------|----------|
| Todo-o-nada | Cualquier violación de schema → sin commit, último JSON bueno intacto | ✓ |
| Parcial con umbral | Aceptar ≥340/346 con flags | |
| Parcial por familia | Commitear familias válidas | |

**User's choice:** Todo-o-nada; alertas = email de Actions + GitHub issue automático con log; plausibilidad de tasas contra rango histórico por comuna/familia (±3x máx histórico, línea base en primera corrida); ID canónico = código CUT oficial + slug para URLs.

---

## Claude's Discretion

- Estructura exacta de modelos Pydantic, naming de campos, layout de `meta/`
- Manejo del año en curso parcial
- Umbral exacto de tendencia y márgenes exactos de plausibilidad

## Deferred Ideas

None — discussion stayed within phase scope.
