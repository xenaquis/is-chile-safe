# 34 — Golden set v2: family relabel (blind review)

**Date:** 2026-09-22
**Output:** `pipeline/tests/fixtures/golden_set_v2.json` (golden_set.json is unchanged)
**Scope:** only `ground_truth.family` on the 44 labelled items. commune_name, cut, the 3 null items and every other field are byte-identical to the source.

## Method

This was a blind review. I read only headline + description for each item and did not open any model predictions, spike outputs, phase plans, the premortem or gate files. I kept a label unless I could tie a change to the taxonomy.

Taxonomy sources read:

- `pipeline/shared/schema.py:22-30` — FAMILY_KEYS (the 7 CEAD families).
- `pipeline/news/classifier.py:109-137` — the news SYSTEM_PROMPT: 8-value enum (the 7 CEAD keys + `sexuales`). Traffic accidents are not crimes. Sexual crimes go to `sexuales`, except that a killing goes to `vida` (line 131).
- `data/SOURCES.md:39-42` — familia = first digit of the CEAD grupo id (1xx vida, 2xx robos violentos, 3xx VIF, 4xx drogas, 5xx armas, 6xx propiedad, 7xx incivilidades, 999 otros).
- `pipeline/cache/cead_page.html` — the live CEAD grupo/subgrupo catalog. This is the authoritative mapping:
  - **2xx robos violentos:** 201 Robos con violencia o intimidación (20101; **20102 Robo violento de vehículo motorizado** = portonazo/encerrona), 202 Robo por sorpresa.
  - **6xx propiedad:** 601 robo en lugar habitado/no habitado, 602 robo de vehículo (non-violent), 603 otros robos con fuerza, 604 hurtos, 605 receptación. The 6xx family contains no violent robbery.
  - **1xx vida:** homicidios/femicidios, violaciones/abusos sexuales, lesiones (graves, menos graves, leves), amenazas.
  - **5xx armas:** 50101 disparo injustificado, **50102 porte/posesión de armas o explosivos**, 502 arma cortante.
  - **7xx incivilidades:** riña pública, consumo en vía pública, **703 daños**, desórdenes.
- `site/src/lib/familyDefs.ts:33,58,97,108` — robos_violentos = "robo con violencia y robo con intimidación". `:37,62,99,110` — propiedad = burglary, hurto, fraud.
- `.planning/research/v2.2-AUDIT-260922.md` § V-07 — `vida` used as a catch-all.

Decision rules I applied:

- Robbery by force against a person or by intimidation (armed or not), such as a portonazo, an *asalto*, a robbery at gunpoint (*a mano armada*) or a snatch-and-grab, goes to `robos_violentos`. It stays there when the victim is injured, as long as nobody dies.
- Theft with no confrontation (burglary, hurto, copper theft, fraud) goes to `propiedad`.
- Injury or death with no property motive goes to `vida`.

## Changed items (11)

| id | headline (short) | old family | new family | reason |
|----|------------------|-----------|-----------|--------|
| gs-001 | Portonazo en Las Condes a punta de pistola | vida | robos_violentos | Portonazo at gunpoint = CEAD 20102 robo violento de vehículo motorizado. Nobody hurt, so no basis for vida. |
| gs-002 | Asalto a sucursal bancaria en Providencia, dos heridos | vida | robos_violentos | Armed bank robbery = 201 robo con violencia o intimidación. The employees were injured during the robbery and nobody died. Under Chilean law, injuries during a robbery are part of *robo con violencia*, not separate lesiones. |
| gs-003 | Robo con violencia en centro de Santiago, víctima hospitalizada | vida | robos_violentos | Headline literally says "robo con violencia" (grupo 201). Phone and wallet taken, head injury, no death. |
| gs-012 | Roban camión con mercadería en Temuco | propiedad | robos_violentos | The driver was "reducido a golpes", so this is violence against a person to take the vehicle (201/20102). Not a non-violent 602 vehicle theft. |
| gs-013 | Asalto a turistas en puerto de Valparaíso | propiedad | robos_violentos | Tourists "asaltados" and robbed of cash, phones and documents from their person. In Chilean usage an asalto is robbery with violence or intimidation (201). Nothing suggests a hurto. |
| gs-021 | Asaltan farmacia en Coquimbo | propiedad | robos_violentos | Two men with covered faces "asaltaron" a pharmacy and took the till in front of staff. That is robo con intimidación (201) even though nobody was hurt. |
| gs-026 | Portonazo en Providencia, matrimonio perdió camioneta | vida | robos_violentos | Portonazo with firearm threats = 20102. No injury. |
| gs-029 | Robo a mano armada en local de La Florida | propiedad | robos_violentos | Armed robbery with employees "reducidos con pistolas" = robo con intimidación (201). |
| gs-033 | Portonazo en Las Condes termina en persecución y volcamiento | vida | robos_violentos | Core event is a portonazo (20102). Only the offenders were hurt, in a crash during the chase, and the owner was unharmed. No crime against life. |
| gs-036 | Mujer robada en mercado municipal de San Miguel | propiedad | robos_violentos | Description says "robo con violencia" and the bag was snatched from the victim. That is 201, or 202 robo por sorpresa, and both are robos_violentos. |
| gs-046 | Atacan con explosivo sede de empresa en Maipú | propiedad | armas | Setting off an improvised explosive device is a Ley 17.798 offence = CEAD 50102 "porte/posesión de armas o explosivos". Nothing was stolen, so no 6xx group applies, and property damage (daños) is 703 incivilidades in any case. |

Result: 5 items move vida → robos_violentos, which is the V-07 pattern, and 5 move propiedad → robos_violentos. 1 item moves propiedad → armas.

## Borderline items KEPT (8)

| id | headline (short) | family kept | reason for keeping |
|----|------------------|-------------|--------------------|
| gs-004 | Incendio intencional destruye empresa en Antofagasta | propiedad | Arson has no CEAD group (it would fall in 999 otros). In the Chilean Código Penal, incendio sits under Libro II Título IX "Crímenes y simples delitos contra la propiedad", and nobody was hurt. propiedad is the closest news family. |
| gs-007 | Cocaína y armas en allanamiento en La Florida | drogas | Mixed seizure: 3 kg cocaine base plus one revolver and 200 rounds. The headline leads with the drugs and the quantity points to Ley 20.000, so armas is secondary. |
| gs-016 | Balacera en Quintero, herido crítico | vida | A person was shot and critically injured = lesiones graves (103). armas (50101 disparo) is secondary when there is a victim. |
| gs-023 | Anciana estafada por falso funcionario bancario | propiedad | CEAD puts fraud in 999, but the project's propiedad definition explicitly includes fraud (familyDefs.ts:37,62). No violence, so it cannot be robos_violentos. |
| gs-030 | Personas en situación de calle en Zofri, Iquique | incivilidades | Disorder, public drug use (702) and petty theft reported by neighbours. Arguably not a discrete crime incident, but disorder is the dominant theme. |
| gs-032 | UNESCO preocupada por alza de incendios en Valparaíso | propiedad | Institutional/trend news, not a discrete incident. Arguably it should be a non-crime (null). I did not null it because that would also change commune_name/cut, which is out of scope. Flagged for the owner. |
| gs-037 | Pelea masiva entre barras bravas, 8 heridos | vida | Could be 70102 riña pública (incivilidades), but 8 people were injured with chains, rocks and clubs, which makes this lesiones (1xx). |
| gs-038 | Aumento de robos de celulares y carteras en Festival de Viña | propiedad | A trend report on phone and bag theft that does not say whether force was used (hurto vs lanzazo/robo por sorpresa). Without evidence of violence, propiedad (hurto) stays. |

## Verification

- ids and order are identical (47 items).
- Only `ground_truth.family` differs, on exactly the 11 ids above. All other fields, including commune_name and cut, are identical.
- A textual diff shows exactly 11 changed lines, so the formatting is preserved.
- `git diff --quiet pipeline/tests/fixtures/golden_set.json` passes: the source is unchanged.
