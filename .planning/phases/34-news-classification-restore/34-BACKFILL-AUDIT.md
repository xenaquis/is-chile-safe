---
phase: 34
plan: 05
artifact: backfill G-11 audit
date: 2026-09-23
decision: NO-PUBLICATION (G-14) — 34-05 Task 3 skipped
---

# Phase 34 — Backfill audit (G-11 / G-14)

## Classify phase (measured)

- Population: 2,122 rows (stage classifier_none, first_seen ≥ 2026-09-04T20:13:49Z, parsed datetime; frozen subset 2,073 ✓). Instrument: `pipeline/backfill_classifier_outage.py --classify`, model deepseek/deepseek-v4.1-flash (G-16), cache in the session scratchpad (never under data/).
- Outcomes: {'not_crime': 953, 'ok': 1162, 'parse_error': 5, 'api_error': 2}.
- Spend: USD 0.410796 (cap 4.63). failovers 0.

## Flagged-row review (step 7, fresh opus)

- 147 regex-flagged accepted rows reviewed; 17 would be excluded (2 V-06 headline additions, the rest accidents / natural deaths / fires / non-incidents labelled vida).

## G-11 stratified audit (step 7b, fresh opus, seed 3405)

| stratum | agree | n | pass needs ceil(0.86·n) | result |
|---|---|---|---|---|
| gnews_title_only | 17 | 20 | 18 | FAIL |
| non_chile_cue | 7 | 10 | 9 | FAIL |
| random | 14 | 20 | 18 | FAIL |
| **overall** | **38** | 50 | 43 | **FAIL** |

Pass = q1 crime incident in Chile ∧ q2 commune as in source ∧ q3 family correct. q1 alone: 40/50 (80%).

## Decision (G-14, applied mechanically)

All three strata fail, so every stratum is withheld (G-14 ii) and there is no non-withheld remainder to re-audit. Outcome: **no-publication recorded (G-14); Task 3 skipped** — no apply, no data commit, no push, no R2 regeneration, no methodology disclosure line. The 2,122 rows stay `classifier_none` in `rejected/2026-09.json` (seen.json untouched). NREC-09 residual = selected = 2,122 → NREC-09 **Partial**; NREC-10 is judged on live data only (C3).

## What the audit says about the LIVE classifier

The same prompt and model run in production since push 8095928. The dominant failure is non-crime acceptance (accidents, natural deaths, fires, preventive-security notices, a border-minefield explosion) labelled `vida`/`armas`. This is the pre-existing V-07 defect (the Granite-era spot check found ~12/30), not a regression, and it is the scope of Phase 36 FID-02/FID-03 (non-crime rejection ≥ 80%, hand audit ≥ 85%). See G-18.

## Per-item verdicts

| id | stratum | q1 | q2 | q3 | q4 | correct family if q3 no | reason |
|---|---|---|---|---|---|---|---|
| 47cc2bedb1442b90 | gnews_title_only | True | True | True | False |  | Homicidio de adolescente en Calama con 2 detenidos: vida y Calama son correctos. El titular es fiel al original. |
| 4c8b86eb7d7f374e | gnews_title_only | True | True | False | False | sexuales (alternativa: robos_violentos); nunca vida | La persecución terminó en Coquimbo, así que la comuna es razonable. El delito es 'robo con violación' y no hubo muerte. La regla del prompt manda los delitos sexuales a sexuales, no a vida. vida funciona aquí como cajón de sastre. Los títulos son fieles. |
| 5cba8d6bcd36fc7c | gnews_title_only | True | True | True | False |  | Detención por amenazas y delitos sexuales en Coquimbo: sexuales es correcto. El titular es fiel. |
| b2f330935b07d752 | gnews_title_only | True | True | False | False | propiedad (la fuente no indica violencia ni intimidación) | 'Robo de camión con celulares' en San Bernardo. La fuente (solo el titular) no menciona violencia, intimidación ni conductor agredido. Por la regla del relabel, un robo sin confrontación va a propiedad. Es un caso ambiguo, pero robos_violentos no tiene respaldo en el texto. |
| 6f4bb69f0a40d512 | gnews_title_only | True | True | True | False |  | Robo sin más calificación en el centro de Antofagasta. propiedad es aceptable a falta de señales de violencia. El titular es fiel. |
| 76ca48d37bdacced | gnews_title_only | True | True | True | False |  | Banda de asaltos 'salida de banco': un asalto es robo con violencia o intimidación, así que robos_violentos es correcto. 'PDI Antofagasta' podría ser la región, pero la comuna Antofagasta es una inferencia razonable. |
| 751d8260dc1569f2 | gnews_title_only | True | True | True | False |  | Robo en el sector Puertas del Mar de La Serena. propiedad es aceptable porque no se indica violencia. El titular es fiel. |
| 79ac288350f6b44e | gnews_title_only | True | True | True | True |  | Homicidio tentado con armas blancas contra un menor en La Serena: vida es correcto. El title_en está mal construido: 'formalizes charges for attempted homicide of attackers' convierte a los atacantes en víctimas y así tergiversa quién sufrió el ataque. El title_es es fiel. |
| de1e92f61b62df4f | gnews_title_only | False | True | False | False | ninguna (no es delito: muerte natural) | La propia fuente dice que la PDI descarta el homicidio y que el hombre murió de un paro cardíaco. Es una muerte natural, no un crimen, y no debió aceptarse como vida. Pitrufquén es correcto. |
| eed75d5db474f451 | gnews_title_only | True | True | True | False |  | Nota institucional sobre la fuga en Copiapó de un condenado por homicidio. Es un caso real y el delito de fondo es homicidio, así que vida es correcto. El titular es fiel. |
| b0c335a0cae62baf | gnews_title_only | True | True | True | False |  | Mismo caso de fuga en Copiapó. vida es correcto por el delito de fondo. El title_en traduce 'romance con funcionaria' sin agregar nada. |
| f4c1739e4f0547a1 | gnews_title_only | True | True | True | False |  | Novedad judicial del triple homicidio de La Reina: vida y La Reina son correctos. El titular es fiel. |
| 22dfc2453386299e | gnews_title_only | True | True | True | False |  | Robo de combustible en Bomberos de Temuco. Es un hurto o robo sin violencia, así que propiedad es correcto. El titular es fiel. |
| 61ef620f7c32cbeb | gnews_title_only | True | True | True | False |  | Homicidio frustrado en Iquique (lo roció con bencina y le prendió fuego): vida es correcto. El titular es fiel. |
| 6360f5022a0f8d95 | gnews_title_only | True | True | True | False |  | Extradición del imputado por un homicidio 'en Santiago'. La fuente nombra Santiago, y aunque podría ser la ciudad, la comuna Santiago es una lectura razonable. vida es correcto. |
| c2ef39fad5033667 | gnews_title_only | True | True | True | False |  | Robo de equipos y alimentos en una escuela de La Serena. Es robo en lugar no habitado, así que propiedad es correcto. |
| 3f5d5be1bfee9b0f | gnews_title_only | True | True | True | False |  | Detenidos por un homicidio en Calama: vida es correcto. El titular es fiel. |
| 85a51b3c9b2167ad | gnews_title_only | True | True | True | False |  | Robo de cobre en trenes, acumulado sobre 200 toneladas. Es una cifra agregada y no un incidente puntual (caso límite), y 'Antofagasta' podría ser la región. Aun así la fuente nombra Antofagasta y el robo de cobre es propiedad. |
| 356b32dd34d0d030 | gnews_title_only | True | True | True | False |  | Hombre muerto a balazos en su auto en el centro de Santiago: vida es correcto. El titular es fiel. |
| f59e611ec1aa0c11 | gnews_title_only | True | True | True | False |  | Fiscalía se pronuncia sobre la fuga del condenado por homicidio en Copiapó. Es un caso real y vida es correcto. |
| 92cd35fd1138995c | non_chile_cue | False | True | False | False | ninguna (accidente: camioneta activó una mina en campo minado fronterizo) | Explosión de una camioneta en el campo minado del hito 16, en la frontera con Perú, con el conductor fallecido. La fuente no describe ningún delito: es el estallido de una mina heredada, un accidente. vida es incorrecto. Arica es correcto. |
| a37146a50219cb46 | non_chile_cue | True | True | True | False |  | Enfrentamientos de manifestantes con Carabineros en Av. Brasil, Valparaíso. Son desórdenes públicos, así que incivilidades es correcto. |
| 17a661f21b8aaeb0 | non_chile_cue | True | True | True | False |  | Acusación contra hermanos por parricidio frustrado en Concepción (contrataron un sicario). vida es correcto. El parentesco (hermanos, padre) está en la fuente. |
| f8251d6b261a9ceb | non_chile_cue | True | True | True | False |  | Incautación de 1.258 kg de marihuana: drogas es correcto. La fuente dice 'en Santiago' refiriéndose a la capital o la RM, así que la comuna Santiago es aceptable aunque imprecisa. El origen boliviano no saca el hecho de Chile. |
| fdf8c470886a52ae | non_chile_cue | True | True | True | False |  | El robo del celular ocurrió en el centro de Santiago y la recuperación en el aeropuerto (Pudahuel). Santiago como lugar del delito es razonable. Robo o receptación de teléfonos: propiedad es correcto. |
| 0be6b9e7f7ee99a9 | non_chile_cue | False | True | False | False | ninguna (hallazgo de cadáver sin delito establecido) | Hallazgo del cuerpo de un boliviano en el río San José, en Arica. La fuente solo informa que hay una investigación y no indica homicidio ni lesiones. No hay un incidente delictual establecido, así que vida no se sostiene. Arica es correcto. |
| 1c49c011fc62c312 | non_chile_cue | False | True | False | False | ninguna (accidente con mina antitanque; no es porte de explosivos) | Es el mismo evento del hito 16: una camioneta activó una mina antitanque. Es un accidente con una mina heredada, no porte ni uso delictual de explosivos, así que armas es incorrecto. El title_es quita el condicional ('se habría activado' pasa a 'tras activarse'), una pérdida menor de matiz. |
| 2f60fa77a4351192 | non_chile_cue | True | True | True | False |  | Recaptura en Antofagasta de un condenado por homicidio que se fugó en Copiapó. Copiapó, lugar de la fuga, es defendible. vida por el delito de fondo. El bautizo del hijo está en la fuente. |
| 079ca6e6f17e8548 | non_chile_cue | True | True | True | False |  | Presunto secuestro en la ruta A-16 hacia Alto Hospicio. La comuna es razonable, aunque la A-16 también cruza Iquique. Ninguna familia refleja bien un secuestro, así que vida es aceptable como delito contra la persona (caso límite). El titular es fiel. |
| 52ad72aceb45417a | non_chile_cue | True | True | True | False |  | Robo a mano armada de cajas de carne en un frigorífico de Recoleta, con trabajadores intimidados. robos_violentos es correcto. |
| 09fb832af5811fae | random | False | True | False | False | ninguna (volcamiento de vehículo; no hay delito establecido) | Mujer hallada sin vida tras el volcamiento de un vehículo en un humedal de Valdivia. Las circunstancias están en investigación y la fuente no indica delito. Parece un accidente de tránsito, que el prompt excluye. vida es incorrecto. |
| a5516bcd1987faba | random | True | True | True | False |  | Homicidio frustrado con un disparo 9mm en Tierra Amarilla: vida es correcto. |
| 635bdfeebf2f1033 | random | False | True | False | False | ninguna (muerte sin delito establecido) | Muerte de un hombre de 72 años cuyo brazo comieron unos perros en Pitrufquén. La fuente no atribuye la muerte a un delito y solo recuerda otros hechos. Otro ítem de la muestra (de1e92f61b62df4f) indica que la PDI descartó el homicidio. vida es incorrecto. |
| 183889a4fe9aef1c | random | False | True | False | False | ninguna (anuncio de seguridad preventiva, sin incidente) | Refuerzo de seguridad en la fonda del Estadio Nacional. Es un anuncio preventivo y no hay ningún incidente delictual. Ñuñoa es una inferencia correcta del Estadio Nacional. |
| 7b1194654ff61520 | random | True | True | True | False |  | Doble homicidio frustrado en La Pintana y prisión preventiva: vida es correcto. El título lo llama 'autor' aunque la fuente dice 'imputado', un leve prejuzgamiento que no agrega hechos. |
| 9f16fb9847c9bea6 | random | True | True | True | False |  | Joven muerto con arma cortopunzante en Limache, posible robo con homicidio. La muerte domina, así que vida es correcto. |
| 69c0174d3f149358 | random | True | True | True | False |  | Guardia baleado en un intento de asalto en un mall de Talca, herido grave pero sin muertos. Por la regla del relabel es robos_violentos. El titular es fiel. |
| 8b8a202e94f9eaa9 | random | True | True | True | False |  | Homicidio con arma de fuego frente a una botillería de La Pintana: vida es correcto. |
| ca8223653a749636 | random | True | True | True | False |  | Hombre baleado en un matrimonio en Estación Central. Son lesiones por arma de fuego, así que vida es correcto. |
| 5a94f9f836618ec3 | random | False | True | False | False | ninguna (fiscalización de tránsito); si se forzara, incivilidades, nunca drogas | Balance de fiscalizaciones viales en la RM: conductores ebrios, drogados o con exceso de velocidad. Son infracciones o delitos de la Ley de Tránsito en un operativo, no un incidente puntual. drogas (grupo 401, Ley 20.000) es incorrecto. Curacaví sí aparece en la fuente. |
| c6fc72dd0a7ebf43 | random | True | True | True | False |  | Motociclista asesinado a balazos en Quinta Normal: vida es correcto. |
| a8f9a1c98340d761 | random | True | True | True | False |  | Turbazo o saqueo masivo de un Líder Express en Maipú. Es robo con intimidación, así que robos_violentos es aceptable. |
| 0a1230100e633948 | random | True | True | True | False |  | Robo a un cantante y su mánager, cometido por dos mujeres en el centro de Santiago. No se describe violencia, así que propiedad es aceptable. El titular es fiel. |
| ee98bbc394b55908 | random | True | True | True | False |  | Condenas por el ataque al molino de Contulmo (2022). Es una nota judicial sobre un caso real. vida es plausible por la gravedad del 'brutal ataque' y penas de 80 años, aunque la fuente no detalla el tipo de delito (caso límite). |
| b8d433bbbeb4c06c | random | True | True | True | False |  | Gendarme detenido con celulares y dinero en el penal Colina 1 tras evadir un control. Es ingreso de objetos prohibidos. Ninguna familia CEAD encaja, así que incivilidades es aceptable como residual (caso límite). Colina es correcto. |
| e9fe4684e5a283fc | random | True | True | True | False |  | Femicidio en Alto Hospicio: vida es correcto. La fuente dice 'femicidio' y 'pareja', así que el título no agrega nada. |
| fffddd07c49b2208 | random | True | True | True | False |  | Gendarmería se pronuncia sobre la fuga del condenado por homicidio en Copiapó. Es un caso real y vida es correcto. |
| fcf53d0277666884 | random | True | True | True | False |  | Sujetos armados baleados por un carabinero en un control en San Joaquín. Es porte de armas, así que armas es correcto. |
| 6d95b6be9d66266d | random | False | True | False | False | ninguna (incendio sin delito indicado) | Incendio en un hogar de ancianos de Pitrufquén con 16 muertos. La fuente trata de la dotación de personal y no indica intencionalidad ni delito, así que vida es incorrecto. Pitrufquén es correcto. |
| 578a89d569037cb8 | random | False | True | False | False | ninguna (incendio accidental/emergencia) | Incendio del Hotel Altos Nevados, propagado por el viento, sin delito. La fuente dice 'en Chillán', así que es defendible, pero la 'zona cordillerana' apunta a Nevados de Chillán, en la comuna de Pinto. incivilidades es incorrecto. |

## Reviewer summaries

Revisé los 50 ítems contra el texto fuente. q1 (¿es un incidente delictual en Chile?): 40 de 50 pasan. Los 10 falsos son hechos que no son delito: una muerte natural que la propia fuente dice que no fue homicidio (de1e92f61b62df4f), dos notas de la camioneta que explotó en el campo minado del hito 16 (92cd35fd1138995c, 1c49c011fc62c312), un cadáver hallado sin delito establecido (0be6b9e7f7ee99a9), un volcamiento de vehículo (09fb832af5811fae), la muerte del adulto mayor de Pitrufquén (635bdfeebf2f1033), un anuncio de seguridad preventiva (183889a4fe9aef1c), un balance de fiscalizaciones de tránsito (5a94f9f836618ec3) y dos incendios sin delito (6d95b6be9d66266d, 578a89d569037cb8). De esos 10, 9 fueron etiquetados como delitos reales, casi todos vida (7) y los otros armas y drogas: sigue presente el patrón de vida como cajón de sastre para cualquier muerte. Por estrato: gnews_title_only tiene 1 falso de 20, non_chile_cue 3 de 10 y random 6 de 20. Ningún non_chile_cue resultó ser un hecho fuera de Chile: la pista extranjera (boliviano, colombiano, frontera con Perú) no generó falsos positivos de ubicación. q2 (comuna): 50 de 50 aceptables. No encontré comunas inventadas. Hay imprecisiones menores: 'Santiago' usado por la capital, 'Antofagasta' que podría ser la región, y Chillán en vez de Pinto para el Hotel Altos Nevados. q3 (familia): 38 de 50 correctas. Los 12 errores son los 10 no-delitos más dos: 4c8b86eb7d7f374e ('robo con violación' etiquetado vida, debería ser sexuales o robos_violentos) y b2f330935b07d752 (robo de camión sin violencia descrita etiquetado robos_violentos, debería ser propiedad; caso ambiguo). Hay casos límite aceptados: secuestro como vida, contrabando de un gendarme como incivilidades y el caso Contulmo como vida. q4 (el titular agrega hechos): 1 de 50. El title_en de 79ac288350f6b44e invierte víctima y atacantes ('attempted homicide of attackers'). Fuera de eso los títulos son fieles, con pérdidas menores de matiz (condicional eliminado en 1c49c011fc62c312, 'autor' por 'imputado' en 7b1194654ff61520). Conclusión: el problema dominante no es la ubicación ni la invención en los títulos, sino que el clasificador acepta como delito muertes, accidentes, incendios y notas preventivas; el filtro de no-delito (confianza 0) no está funcionando para esos casos.

Revisé 147 filas (la línea 148 del archivo es el contador review_hits=147, no un incidente) y excluí 18. Dos por V-06, porque title_es agrega hechos ausentes en la fuente: ad1e6a40420e069b ('imputado por parricidio', 'Los Lagos') y 7b1194654ff61520 ('prisión preventiva', 'doble homicidio frustrado', 'La Pintana'). Otras 12 no son un incidente delictual: accidentes de tránsito o vehiculares (5cf2a3a5d46c25a7, c92089ceee13bb8a, 55a4ffa1afc805b3, 3d3ea292cab52e9a, 09fb832af5811fae, b1257359c32a8956, e89d73a9a375d4a2, dfa687821128d4e5), muertes accidentales o sin delito acreditado (cd93b9eed2592cce volcán, be407ac7f70b35ba caída, 635bdfeebf2f1033 perros, af9b5c6730c423f2 incendio). Otra más tampoco es un incidente: dd462453224e1b11, una advertencia de Conaf. Las 3 restantes tienen una familia dañina: 45bf5b41fc7f3eb2 y a13b289a57848648 etiquetan vida la muerte accidental en un auto robado. No encontré parentescos alterados; los que revisé (hermana, madre, hijastra, expololo=expareja) coinciden con la fuente. Conservé las noticias judiciales e institucionales sobre casos reales: fugas, condenas, querellas y el caso Ojeda, este último publicado por un medio venezolano sobre un crimen ocurrido en Chile. Los casos límite los dejé: 142 (atropello a un carabinero juzgado penalmente) y 031 (posible encerrona en un choque de camiones). Usé solo lectura del archivo, sin llamadas LLM y sin escrituras en el repo.
