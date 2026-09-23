# 34-AB-RESULTS

Generated: 2026-09-23T02:45:21Z
Rule: G-02/G-06/G-08/G-10/G-13

## A/B table

| model | commune | family | parse_errors | endpoints | status | disqualified_by (strict) |
|---|---|---|---|---|---|---|
| deepseek/deepseek-v4.1-flash | 44/44 | 42/44 | 0/47 | 24 | COMPLETE |  |
| deepseek/deepseek-v4-flash | 42/44 | 39/44 | 0/47 | 15 | COMPLETE | family |
| ibm-granite/granite-4.2-8b | 42/44 | 36/44 | 1/47 | 2 | COMPLETE | family, parse_fail |
| qwen/qwen3.5-9b | 44/44 | 40/44 | 3/47 | 6 | COMPLETE | parse_fail |
| deepseek-v4-flash (backup) | 44/44 | 42/44 | 0/47 | None | COMPLETE | not eligible (backup) |

## Served-by providers seen

- deepseek/deepseek-v4.1-flash: ['CoreWeave', 'DeepInfra', 'Sail Research', 'Together']
- deepseek/deepseek-v4-flash: ['Alibaba', 'AtlasCloud', 'Azure', 'DigitalOcean', 'GMICloud', 'NextBit', 'Novita', 'OpenInference', 'Parasail', 'SiliconFlow', 'StreamLake', 'Venice']
- ibm-granite/granite-4.2-8b: ['CoreWeave', 'DeepInfra']
- qwen/qwen3.5-9b: ['Darkbloom', 'DeepInfra', 'SiliconFlow', 'Together', 'Venice']
- deepseek-v4-flash: ['deepseek-flash']

## Family confusion matrix per candidate

### deepseek/deepseek-v4.1-flash
- armas: armas=5
- drogas: drogas=8
- incivilidades: incivilidades=4
- propiedad: propiedad=6
- robos_violentos: robos_violentos=10
- vida: armas=1, incivilidades=1, vida=5
- vif: vif=4

### deepseek/deepseek-v4-flash
- armas: armas=4, robos_violentos=1
- drogas: drogas=8
- incivilidades: incivilidades=4
- propiedad: incivilidades=1, propiedad=4, robos_violentos=1
- robos_violentos: robos_violentos=10
- vida: vida=7
- vif: vif=4

### ibm-granite/granite-4.2-8b
- armas: armas=4, robos_violentos=1
- drogas: drogas=8
- incivilidades: incivilidades=4
- propiedad: propiedad=3, robos_violentos=3
- robos_violentos: robos_violentos=10
- vida: robos_violentos=2, vida=5
- vif: vida=2, vif=2

### qwen/qwen3.5-9b
- armas: armas=4, propiedad=1
- drogas: drogas=8
- incivilidades: incivilidades=4
- propiedad: propiedad=5, robos_violentos=1
- robos_violentos: propiedad=1, robos_violentos=9
- vida: incivilidades=1, vida=6
- vif: vif=4

### deepseek-v4-flash
- armas: armas=5
- drogas: drogas=8
- incivilidades: incivilidades=4
- propiedad: propiedad=6
- robos_violentos: robos_violentos=10
- vida: armas=1, incivilidades=1, vida=5
- vif: vif=4

## Decision

**WINNER** — max family_correct=42 among strict qualifiers (G-02/G-06/G-10) (rule G-02/G-06)

Winner: `{"model": "deepseek/deepseek-v4.1-flash", "provider": "openrouter", "reasoning_variant": "enabled_false", "reasoning_extra_body": {"reasoning": {"enabled": false}}, "endpoints": 24, "family_correct": 42, "commune_correct": 44}`

spend_total_usd: 0.111128
