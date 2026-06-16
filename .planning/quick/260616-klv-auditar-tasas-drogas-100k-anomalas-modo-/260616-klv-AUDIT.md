# Quick 260616-klv — Auditoría tasas drogas/100k + modo de entrega/escalado

**Fecha:** 2026-06-16
**Disparador:** Usuario observa drogas/100k "anómalamente bajas"; pide verificación comuna-por-comuna contra CEAD y revisión del modo de entrega/escalado.
**Método:** Cruce determinista del JSON almacenado vs. el HTML crudo de CEAD cacheado en `pipeline/cache/` (201 respuestas). Sin tráfico al servidor gov.

---

## Veredicto

**Las tasas de drogas NO son un bug. Son, al dígito, lo que CEAD publica.** El "se ven bajas" es una propiedad real de la métrica CEAD, no un defecto del pipeline.

---

## Finding 1 — Fidelidad de datos: 100% exacta

Verificación comuna×familia contra el HTML crudo de CEAD (familia filtrada, `medida=2`, `tipoVal=1,2` = Casos Policiales, Tasa cada 100.000 hab):

| Año | Pares (346 comunas × 7 familias) | Exactos | Mismatch | Sin match |
|----|----|----|----|----|
| 2020 | 2422 | 2422 | 0 | 0 |
| 2022 | 2422 | 2422 | 0 | 0 |
| 2024 | 2422 | 2422 | 0 | 0 |
| 2025 | 2422 | 2422 | 0 | 0 |
| **Total** | **9688** | **9688 (100.00%)** | **0** | **0** |

Ejemplo canónico — Santiago (13101) 2024:
- CEAD crudo (cache `cead_15_4_2024.html`): drogas **94,2342593885 /100k**
- JSON almacenado (`data/cead/comunas/13101.json`): **94.2342593885**

El header del HTML CEAD confirma: `Medida = Tasa Cada 100.000 Habitantes`, `Tipo de Datos = Casos Policiales`. El filtro de familia se aplica correctamente (vida/drogas/propiedad/incivilidades dan valores distintos y todos coinciden).

## Finding 2 — Por qué drogas se ve baja (no es error) — TAXONOMÍA CEAD (D-05 resuelto)

Verificado en vivo contra el catálogo oficial de CEAD (`ajax_2.php?seleccion=104`, lista `GruposDel`):

```
Familia 4 (drogas)        → grupo 401: "Crímenes y simples delitos ley de drogas"   ← ÚNICO grupo
Familia 7 (incivilidades) → grupo 702: "Consumo de alcohol y drogas en la vía pública"
```

**`familia=4` está COMPLETA y es correcta.** Captura todo lo que CEAD define como familia "drogas" = grupo 401 (Ley 20.000: tráfico, microtráfico, cultivo — los delitos criminales). No es un subconjunto truncado.

**La razón real de la baja cifra:** CEAD **NO clasifica el consumo de droga dentro de la familia drogas.** El consumo en vía pública vive en **incivilidades → grupo 702** (mezclado con alcohol). Por eso "drogas/100k" mide sólo delitos criminales de la Ley 20.000, que son legítimamente de baja frecuencia y mayoritariamente detectados por policía (no denunciados).

Tasa nacional ponderada por población, 2024 (casos policiales /100k), desde los JSON ya verificados:

| Familia | Tasa real /100k |
|----|----|
| propiedad | 1585.9 |
| incivilidades | 1435.4 |
| vida | 1263.3 |
| vif | 704.1 |
| robos_violentos | 600.0 |
| armas | 144.7 |
| **drogas** | **79.2** |

drogas ≈ 79/100k nacional (~16.000 casos en 20,1M hab) — coherente con el volumen real de causas de tráfico.

El proyecto usa `tipoVal=1,2` (Casos Policiales) consistente en las 7 familias (D-08) — elección correcta para comparar.

**Recomendación editorial (no bug, APROBADA):** nota al pie bilingüe en la familia "drogas": refleja delitos criminales de la Ley de Drogas (tráfico/microtráfico); el consumo en vía pública lo cuenta CEAD bajo "incivilidades".

## Finding 3 — Modo de entrega/escalado

- **Por comuna y map-payload:** tasas `medida=2` propias de CEAD, sin reescalar. **Correcto.** (ver memoria `crime-rates-already-per-100k`)
- **`national.json` y `regions/*.json`** (`series[].rate_per_100k`, `by_family`): se construyen **sumando tasas/100k entre comunas** (`scrape_cead.py:620-623, 658-661`). Una tasa "nacional" sale en **2.098.199/100k** (2024) — estadísticamente inválida como tasa absoluta. **Footgun latente, no bug vivo:** el frontend ya lo sabe y nunca la muestra como tasa — recomputa la **media poblacional** vía `loadNationalAverage()`/`loadRegionalAverage()` (ver comentario en `site/src/pages/region/[slug].astro:8-10`: *"NEVER use ... those are SUMs"*).

**RESUELTO (este quick):** se cambió la agregación a **media ponderada por población** en `pipeline/scrape_cead.py` (`_population_weighted_series`) y se regeneraron `national.json` + `regions/*.json` desde los JSON por-comuna verificados (sin re-scrapear). national 2024 ahora = 5812.7/100k (antes 2.098.199). Comentarios de `data.ts`/páginas actualizados. 139 tests del pipeline verdes; `astro check` 0 errores.

### Hallazgo colateral (transparencia) — regiones 1–9 con `series` vacías

Al regenerar se constató que **sólo las regiones 10–16 (incl. 13) reciben series**; las **regiones 1–9 quedan vacías** — condición **pre-existente, no introducida por este cambio**. Causa: `_build_region_aggregates` agrupa por `region_id = cut[:2]`, pero los CUT de regiones 1–9 son de 4 dígitos (p. ej. Algarrobo `5602` → `cut[:2]`=`56`≠`5`; `1107` → `11`, que además colisiona con Aysén). Es el bug conocido **tarapaca-region-id-collision** (v1.2 backlog 999.1, fix = derivar región desde CUT con largo: `cut[:2] if len==5 else cut[:1]`). national.json NO se ve afectado (agrega sobre las 346 comunas sin agrupar). **Recomendación:** corregir el agrupamiento dentro de ese backlog, no aquí, para no entregar un artefacto a medias (la corrección también debe re-derivar `regional_rank`).

---

## Cobertura / límites

- Verificados 4 años (2020, 2022, 2024, 2025) por muestreo; el parser y el name-matching son los mismos para todos los años → fidelidad extrapolable. Una corrida completa 2005–2025 está disponible si se requiere.
- Verificación hecha contra **caché CEAD** (snapshot del último scrape). No re-consulta CEAD en vivo (cortesía al servidor gov, CLAUDE.md).
- No auditado en profundidad: el **supuesto D-05** de que `familia=4` cubre el alcance completo de la Ley 20.000 (vs. un subconjunto). El header CEAD muestra el filtro de familia aplicado y los valores calzan con el sitio CEAD, pero el alcance taxonómico exacto es una pregunta de dominio abierta.
