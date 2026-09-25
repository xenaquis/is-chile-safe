# FID-02 fidelity score

Model: deepseek/deepseek-v4.1-flash (openrouter)
spend_usd: 0.021245

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

total=24 rejected=12 rate=0.5

| category | n | rejected | rate |
|---|---|---|---|
| accident | 6 | 0 | 0.000 |
| death_no_crime | 3 | 0 | 0.000 |
| fire_emergency | 2 | 0 | (n<3) |
| institutional_preventive | 13 | 12 | 0.923 |

## v2 subset (G-38)

uncontested (41): commune 41/41, family 39/41
all (44): commune 44/44, family 42/44

### Contested (reported, never gated)

- gs-030: {"status": "ok", "rejected_in_prod": false, "predicted_family": "incivilidades", "commune_match": true, "family_match": true}
- gs-032: {"status": "ok", "rejected_in_prod": false, "predicted_family": "propiedad", "commune_match": true, "family_match": true}
- gs-038: {"status": "ok", "rejected_in_prod": false, "predicted_family": "propiedad", "commune_match": true, "family_match": true}

## Boundary family

5/8

## Parse / empty / truncation

parse_errors=0 empty=0 finish_length=0

null_v2_correct: 3/3

## Family confusion matrix

- None: null_item=3
- armas: armas=6
- drogas: drogas=8
- incivilidades: incivilidades=4
- not_crime: null_item=24
- propiedad: propiedad=6, robos_violentos=2
- robos_violentos: robos_violentos=10, sexuales=1
- sexuales: sexuales=1
- vida: armas=1, incivilidades=1, vida=8
- vif: vif=4
