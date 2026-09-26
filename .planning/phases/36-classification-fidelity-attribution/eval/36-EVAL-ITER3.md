# FID-02 fidelity score

Model: deepseek/deepseek-v4.1-flash (openrouter)
spend_usd: 0.020575

## Gate

| member | value |
|---|---|
| not_crime_rate_ge_080 | False |
| v2_commune_uncontested_ge_39 | True |
| v2_family_uncontested_ge_37 | True |
| parse_errors_eq_0 | True |
| empty_eq_0 | True |
| finish_length_eq_0 | True |
| null_v2_correct_eq_3 | True |
| pass | False |

## Non-crime rejection

total=24 rejected=18 rate=0.75

| category | n | rejected | rate |
|---|---|---|---|
| accident | 6 | 3 | 0.500 |
| death_no_crime | 3 | 1 | 0.333 |
| fire_emergency | 2 | 1 | (n<3) |
| institutional_preventive | 13 | 13 | 1.000 |

## v2 subset (G-38)

uncontested (41): commune 41/41, family 40/41
all (44): commune 43/44, family 42/44

### Contested (reported, never gated)

- gs-030: {"status": "ok", "rejected_in_prod": false, "predicted_family": "incivilidades", "commune_match": true, "family_match": true}
- gs-032: {"status": "low_conf", "rejected_in_prod": true, "predicted_family": "incivilidades", "commune_match": false, "family_match": false}
- gs-038: {"status": "ok", "rejected_in_prod": false, "predicted_family": "propiedad", "commune_match": true, "family_match": true}

## Boundary family

7/8

## Parse / empty / truncation

parse_errors=0 empty=0 finish_length=0

null_v2_correct: 3/3

## Family confusion matrix

- None: null_item=3
- armas: armas=5, incivilidades=1
- drogas: drogas=8
- incivilidades: incivilidades=4
- not_crime: null_item=24
- propiedad: propiedad=6, rejected=1, robos_violentos=1
- robos_violentos: robos_violentos=11
- sexuales: sexuales=1
- vida: vida=10
- vif: vif=4
