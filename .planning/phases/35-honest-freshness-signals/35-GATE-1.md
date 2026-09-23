---
phase: 35
artifact: adversarial gate
round: 1
plans_evaluated: 35-01..35-07 @ 89f0d6a
verdict: GO-CONDICIONADO
blockers: 7
agents: 5 (haiku, 3 opus lenses high, fresh opus arbiter xhigh) + citation script
subagent_tokens: 1016458
cycle: 1 of 2
---

# Phase 35 — Adversarial Gate, Round 1

## Verdict: GO-CONDICIONADO

Árbitro, ronda 1, sobre 35-01..35-07 en 89f0d6a (repo C:\Users\Carlo\OneDrive - pjud.cl\Documentos\GitHub\Is Chile Safe). Las tres lentes dieron NO-GO. Verifiqué yo mismo cada bloqueante contra el repo y contra prod, y los siete que sobreviven son ediciones mecánicas de texto, verificables por diff. Ninguno exige re-diseñar la fase, así que el veredicto es GO-CONDICIONADO. La ejecución sigue además bloqueada por G-19 (Fase 34 abierta).

Dos verify fallan con cualquier implementación:
- 35-04 T2: el guard 'geolocated in' coincide con el intro de comuna. Medido: 115 archivos, rc=1.
- 35-05 T2: el `node -e` con `\\\\` da SyntaxError y M queda en /ics-cv-mut. Además, su mutación 'banned' no prueba el escaneo 3b.

Tres ediciones del premortem introducen o dejan afirmaciones falsas en superficies servidas:
- El tooltip de ResultPanel llama 'último año completo de CEAD' tanto a 2024 como a 2025, y el plan prohíbe corregirlo (R-02).
- El caption del outage toma {from}/{to} del rango declarado. Es falso en cuanto un día del rango tenga incidentes, cosa que 35-01, G-14/G-18 y NREC-10 prevén (R-01).
- El heading de comuna '(none in the last 7 days)' afirma cero justo en el escenario de outage. Es el gemelo de R-06 que quedó sin corregir.

Hay un gemelo no tratado de FRESH-02: NewsStrip en /map/ rellena hasta anchor−29, mientras 35-01 afirma 'every recency signal still holds'.

En el instrumento de FRESH-04, la regla del no-op se contradice entre 35-07:166 y :167, y el camino 'carry' no tiene procedimiento. Medí 116 de 116 commits del bot con ids agregados, así que D≤C y G=0 no discriminan con flujo sano. La inducción sí es factible según el research: 3a0d94e y f5761ea tuvieron 0 ids agregados.

Observaciones del orquestador:
- o1: no queda ninguna señal de fecha de build en prod.
- o2: el presupuesto de builds queda ≪ 500 y no hay loop.
- o3: está cubierto por G-19 más la política de freshness en rojo.

Los 11 hallazgos no bloqueantes quedan como recomendaciones. Lo que no medí (duración del build o del harness) queda como pendiente.

## Final blockers

| id | origin | title | evidence | required edit |
|---|---|---|---|---|
| F35-R1-01 | B-R1-01 (lente B, CONFIRMADO; re-medido por el árbitro) | 35-04 Task 2: el verify falla con cualquier implementación, porque el guard 'geolocated in' coincide con commune_news_intro | LEÍDA: 35-04-PLAN.md:173; site/src/config/i18n.ts:486 (EN intro 'geolocated in {name}') y :731 (ES 'geolocalizados en'); CommuneNewsSection.astro:137. MEDIDA por el árbitro sobre el dist local: `grep -rl 'geolocalizado incidentes\\|geolocated in' dist/commune dist/es/comuna \| wc -l` = 115, y el guard da rc=1. | En 35-04 Task 2 verify, reemplazar el guard por uno que solo detecte la frase vieja de la nota, por ejemplo `! grep -rlE 'has not geolocated\|no ha geolocalizado' dist/commune dist/es/comuna`, o limitarlo al contenido de `<p class="cnews-stale-note"…</p>`. commune_news_intro no se toca. Cómo se verifica: el diff de 35-04:173, y el guard nuevo da rc=0 sobre el dist actual. |
| F35-R1-02 | B-R1-02 (lente B, CONFIRMADO; re-medido por el árbitro) + A-R1-04/B-R1-03 (misma línea del verify) | 35-05 Task 2: la asignación de M aborta con SyntaxError y la prueba por mutación 'banned' no aísla el escaneo 3b | LEÍDA: 35-05-PLAN.md:94 (aserción latest-complete), :122 (3b), :131 (verify completo), :134. MEDIDA por el árbitro (Git Bash, solo lectura): la línea de asignación imprime 'SyntaxError: missing ) after argument list' y da rc=1 M=[/ics-cv-mut]. | (a) Asignar M sin barras invertidas dentro de comillas dobles, por ejemplo `M="$(cygpath -m "$TEMP")/ics-cv-mut"` o `node -e 'console.log(require("os").tmpdir().split(String.fromCharCode(92)).join("/"))'`, y agregar `[ -n "${M%/ics-cv-mut}" ] &&` antes del primer `rm -rf`. (b) La mutación 'banned' inyecta `<p>(partial data)</p>` antes de `</body>` de "$M/news/index.html", que es un nodo que el checker no parsea. Se exige banned-exit=1 y que la salida nombre ese archivo. El PASS imprime cuántos HTML escaneó 3b, y es FAIL si son 0. Cómo se verifica: el diff de 35-05:131, y correr la línea de M sola da rc=0 con una ruta bajo Temp. |
| F35-R1-03 | C-R1-01 (lente C, bloqueante) = A-R1-05 (lente A, no-bloqueante). El árbitro decide: bloqueante mecánico. | 35-03: la edición R-02 del tooltip de ResultPanel produce una afirmación contradictoria sobre el 'último año completo de CEAD', y el plan prohíbe corregirla | LEÍDA: site/src/components/map/ResultPanel.tsx:289-290; 35-03-PLAN.md:146; pipeline/composite_config.py:11-14 ('REFERENCE_YEAR = 2024 (latest year where SPD VHC + CEAD + SII are all final)'). MEDIDA: data/cead/national.json da la serie (2024,False),(2025,False),(2026,True) y last_updated 2026-06-16. | En 35-03 Task 2, reescribir yearMismatchTip completo. EN: 'Why do years differ? The Composite Index uses 2024, the latest year in which all of its sources (CEAD, SPD, SII) are final. The incident rate uses the latest complete CEAD year (2025). Rankings may differ because they come from two calculation methods.' ES equivalente. Limitar 'Change nothing else' a todo lo que está fuera de yearMismatchTip. Agregar al verify de 35-03 `! grep -nE '2024 as the latest complete CEAD year\|2024 como el año completo más reciente' src/components/map/ResultPanel.tsx`. |
| F35-R1-04 | C-R1-02 (lente C, bloqueante) = A-R1-03 (lente A, PLAUSIBLE). El árbitro lo confirma por lectura: bloqueante mecánico. | 35-04: el caption del outage toma {from}/{to} del rango declarado y no de los días que realmente son gap | LEÍDA: 35-04-PLAN.md:115 y :134; 35-01-PLAN.md:125, :137 y :196-197; directiva G-14, G-18 y G-21(2)(3) (:110, :114, :117); REQUIREMENTS.md NREC-10; 35-06-PLAN.md:83 y :100 (el chequeo R-01 cubre barras, no el caption). | En 35-04 Task 1 paso 6 (y su gemelo en la fila 'Gap copy' de 35-01:197 y en G-21(3) vía una enmienda registrada): {from}/{to} salen de cada tramo contiguo de buckets con gap=true, con un caption por tramo o un caption que liste los tramos, nunca del rango declarado. En la lib #18 de 35-06, agregar la aserción 'cada fecha nombrada en el caption es un bucket con data-gap="true"', más un caso con un incidente real el 09-22: el caption termina el 09-21. Cómo se verifica: el diff de 35-04, 35-01, 35-06 y la directiva. |
| F35-R1-05 | C-R1-03 (lente C, CONFIRMADO; texto re-leído por el árbitro) | 35-04 Task 2: el heading de comuna '(none in the last 7 days)' afirma cero, gemelo de R-06 sin corregir | LEÍDA: 35-04-PLAN.md:155-156; CommuneNewsSection.astro:108-110 y :133-135; 35-06-PLAN.md:60 y :102 (literales del heading duplicados en la lib); 35-PREMORTEM.md R-06 y R-07 (el propio R-07 cita '(none in the last 7 days)' como texto visible). | Cambiar commune_news_heading_stale por un heading sin cuantificador cero, por ejemplo EN 'Earlier Incidents in the News' / ES 'Incidentes Anteriores en la Prensa', o '(no listed report from the last 7 days)' / '(sin notas listadas de los últimos 7 días)'. Actualizar los gemelos literales en 35-06 (interfaces :60 y la lib). Agregar al verify de 35-04 Task 2 `! grep -rlE 'none in the last 7 days\|ninguno en los últimos 7 días' dist/commune dist/es/comuna`. |
| F35-R1-06 | C-R1-04 (lente C, CONFIRMADO; código re-leído por el árbitro) | Tercer gemelo de FRESH-02 sin tratar: NewsStrip (/map/, /es/mapa/) rellena hasta anchor−29 y dibujará los días del outage como ceros | LEÍDA: site/src/components/map/NewsStrip.tsx:68-81 (:72-73 extensión) y :118 (aria-label con n=0); MapIsland.tsx:125 (showEvents false por defecto) y :580-591 (monta NewsStrip con incidents filtrados por familia); ROADMAP.md § Phase 35 Goal; 35-01-PLAN.md:199. MEDIDA: grep 'NewsStrip\|MapIsland' en 35-0*-PLAN.md = 0 (solo aparece ResultPanel); GET prod current.json = 742 incidentes 08-24..09-04 y window 30. | Opción (a): agregar a 35-04 (Task 4) NewsStrip.tsx y MapIsland.tsx. El rango empieza en max(anchor−(windowDays−1), fecha mínima válida de incidentsFile.incidents SIN filtrar), pasada como prop, y se elimina la extensión de :72-73. Los días de COVERAGE_GAPS sin incidentes (en el conjunto sin filtrar) se marcan con estilo rayado y aria-label con la etiqueta de gap. Helper puro + vitest. Opción (b): registrar en la directiva (G-22) la exclusión del mapa con su razón, y quitar 'every recency signal still holds' de 35-01:199 y de la redacción de cierre de 35-07. Cómo se verifica: el diff. |
| F35-R1-07 | A-R1-01 (lente A, bloqueante; contradicción y medición 116/116 re-verificadas por el árbitro; el argumento probabilístico se atenúa con evidencia del research) | 35-07 Task 3: la regla del no-op de FRESH-04 se contradice entre :166 y :167, el camino 'carry' no tiene procedimiento, y el instrumento no declara qué discrimina | LEÍDA: 35-07-PLAN.md:155, :160-167 y :170-173; news-pipeline.yml:13-15 (concurrency, sin cancel-in-progress), :83-95 y :109-111; 35-RESEARCH.md:246-249. MEDIDA por el árbitro: git log origin/master 2026-08-05..2026-09-04T20:00Z de bot sobre current.json = 116 commits, 0 con 0 ids agregados, mínimo 3, suma 1.933. gh run list news-pipeline programadas: 03:04, 10:52, 16:10 y 20:48Z. | Reemplazar :166-167 por una sola regla: hasta K=4 intentos de inducción (dispatch encolado mientras corre la programada, o ≤15 min después de que termina), registrando cada uno. Si ≥1 es no-op, se cumple. Si no, el interim puede dar PASS con el residual 'camino no-op probado solo por pytest (test_store byte-identity + test_news_deploy_gate)', y el texto del chequeo de 7 días (RUN STATUS, STATE, cuerpo del issue) incluye el mismo procedimiento de inducción. Declarar en el instrumento que D ≤ C y G = 0 no discriminan con flujo sano (116/116), y que el gate de deploy cuenta como probado en vivo solo si el no-op observado commiteó seen/rejected y su step de deploy quedó skipped. Registrarlo como G-22 antes de ejecutar. |

## Conditions

1. 1. 35-04 Task 2 verify: reemplazar `! grep -rl 'geolocalizado incidentes\\|geolocated in' …` por un guard que solo detecte la frase vieja de la nota (por ejemplo `! grep -rlE 'has not geolocated\|no ha geolocalizado' dist/commune dist/es/comuna`) o que esté limitado a .cnews-stale-note. commune_news_intro queda intacto (F35-R1-01).
2. 2. 35-05 Task 2 verify: (a) asignar M sin `\\` dentro de comillas dobles (cygpath -m "$TEMP" o split(String.fromCharCode(92))) y poner el guard `[ -n "${M%/ics-cv-mut}" ]` antes de rm -rf. (b) La mutación 'banned' inyecta `<p>(partial data)</p>` antes de </body> de $M/news/index.html, y exige banned-exit=1 con el archivo nombrado y la cantidad de HTML escaneados mayor que 0 (F35-R1-02).
3. 3. 35-03 Task 2: reescribir yearMismatchTip completo en EN/ES para que solo 2025 sea 'latest complete CEAD year' y 2024 se describa como el año en que CEAD, SPD y SII están todos finales. Limitar 'Change nothing else' a lo que queda fuera de yearMismatchTip, y agregar un `! grep` de '2024 as the latest complete CEAD year\|2024 como el año completo más reciente' sobre ResultPanel.tsx en el verify (F35-R1-03).
4. 4. 35-04 Task 1 paso 6 + fila 'Gap copy' de 35-01:197 + enmienda registrada a G-21(3): {from}/{to} se derivan de los tramos contiguos de buckets con gap=true, no del rango declarado. La lib #18 de 35-06 afirma que cada fecha del caption es un bucket con data-gap="true", con un caso de test en que un incidente del 09-22 hace terminar el caption el 09-21 (F35-R1-04).
5. 5. 35-04 Task 2: commune_news_heading_stale sin cuantificador cero (por ejemplo 'Earlier Incidents in the News' / 'Incidentes Anteriores en la Prensa'). Actualizar los literales en 35-06 (interfaces :60 y la lib) y agregar el `! grep -rlE 'none in the last 7 days\|ninguno en los últimos 7 días' dist/commune dist/es/comuna` al verify (F35-R1-05).
6. 6. NewsStrip: (a) agregar NewsStrip.tsx y MapIsland.tsx a 35-04 (recorte a max(anchor−(windowDays−1), fecha mínima sin filtrar), quitar :72-73, marcar los días de gap con test vitest), o (b) registrar la exclusión como G-22 con su razón y quitar 'every recency signal still holds' de 35-01:199 y del cierre de 35-07 (F35-R1-06).
7. 7. 35-07 Task 3: una sola regla de no-op, con hasta K=4 intentos de inducción. Si ninguno da no-op, el interim da PASS con el residual 'solo pytest', y el chequeo de 7 días (RUN STATUS, STATE, issue) incluye el mismo procedimiento. Declarar qué discrimina D≤C/G=0 (116/116) y en qué condición el gate de deploy cuenta como probado en vivo. Registrar como G-22 antes de ejecutar (F35-R1-07).

## Non-blockers

| id | title | detail |
|---|---|---|
| A-R1-02 | SHIP tomado del commit y no del push | `git log -1 --format=%cI HEAD` puede quedar antes del push si no hubo rebase. En ese caso W incluye corridas que corren el código viejo. El impacto es bajo, porque con flujo sano esas corridas agregan ids y cuentan en C. Recomendado: SHIP = hora UTC después del push, más un filtro por headSha. |
| A-R1-06 | Paridad JS/Python de G-05 en fechas no canónicas | JS acepta '2026-02-30' y Python acepta '20260904'. feeds.py escribe fechas canónicas. Recomendado: un round-trip toISOString en latestIncidentDate y un fixture H compartido. |
| A-R1-07 | La cadencia real del cron no es '(at most 6h later)' | Medido por el árbitro: 7,8 h entre las corridas 03:04 y 10:52Z del 09-22, y el heartbeat del cron 12:00 corre entre las 14:56 y las 17:17Z. Recomendado: corregir la redacción de 35-07:95 y anotar la cota real del desfase del aviso en 35-02 T3. |
| A-R1-08 | Regla de retiro de COVERAGE_GAPS | 'Se retira si se publica el backfill' es riesgoso con una publicación parcial (G-14/G-18), porque dejaría días en 0 como falsos ceros. La condición count>0 por día ya se desactiva sola. Recomendado: 'never removed; per-day count>0 self-disables it'. |
| A-R1-09 | El aviso 'none' de la home vive dentro de una tarjeta oculta | La tarjeta solo se muestra cuando hay incidentes (HomeNewsPulse.astro:25, :164 y :180), así que el aviso 'none' nunca se ve. Recomendado: documentarlo en 35-04 T3 o sacar el <p> del contenedor [hidden]. |
| B-R1-04 | Gemelo de R-09 en la redacción ('staged') | 35-02:31 y G-20(6) todavía dicen 'staged index/diff'. Recomendado: alinearlos con HEAD~1..HEAD post-push para que el executor no use --cached. |
| B-R1-05 | Exit codes enmascarados o contradictorios | `npx astro check 2>&1 \| tail -3` devuelve el rc de tail (35-07:100 y otros verify), y en <verification> de 35-03/35-04 la cadena `validate && vitest` no corre vitest si freshness está en rojo. Recomendado: capturar el rc de astro check y separar los comandos. |
| B-R1-06 | Gate de un solo comando frente al tope de 10 min del tool | PLAUSIBLE, no medido. Recomendado: correr el harness con run_in_background y registrar su tiempo. |
| C-R1-05 | 35-07 no verifica la home en prod | R-03 agregó la home, pero el fetch de 35-07 T2 no la incluye y .pulse-card no lleva data-build-now. Recomendado: agregar data-build-now a la tarjeta y la home EN/ES al lote de prod. |
| C-R1-06 | Posible <p> anidado en /news/ | 35-04 paso 4 no dice explícitamente que .news-stale-notice va como hermano, después de </p> de .freshness. Recomendado: precisarlo. |
| C-R1-07 | El aviso 'none' afirma '>48 horas' sin evidencia | Solo es inexacto si current.json falta o es ilegible en el build: con incidents vacío, la afirmación se sostiene porque no hay ids en la ventana. Recomendado: una copy neutra para el caso nodate. |

## Discarded

| id | title | reason |
|---|---|---|
| C-R1-08 | depends_on de 35-05 es superconjunto del de R-12 | No es un defecto. 35-04 ya depende de 35-03, la wave 4 no cambia y G-21(1) se respeta. Las tres lentes coinciden (A-R1-C5, B-R1-C06, C-R1-08). |
| ESC-01 | Escalada: ¿los validadores de 35-06/35-07 deberían enlazar archivos concretos en lugar de describir el comportamiento con paráfrasis? | No hace falta edición. Las 9 marcas LITERAL_AUSENTE/DESPLAZADO son paráfrasis de comportamiento sobre líneas que B y C leyeron. Los literales que cargan peso (headings, copy de gap, markup) sí figuran literalmente, y los que cambian se corrigen en F35-R1-04 y F35-R1-05. |
| C-R1-02-sub | Sub-reclamo: 'collected' es inexacto porque los 2.122 ítems sí se recolectaron | Se descarta como bloqueante. La frase habla de incidentes, no de ítems RSS, y en el rango no se produjo ningún incidente publicado. Ajustar la palabra es opcional. El defecto real, {from}/{to}, queda en F35-R1-04. |
| A-R1-01-prob | Sub-reclamo: P(no-op inducido en 2 intentos) ≈ 0,31-0,65 (modelo de Poisson) | Es un modelo, no una medición. La evidencia del research (3a0d94e y f5761ea, 0 ids agregados en corridas inmediatas del 09-23) muestra que la inducción es factible. El bloqueante se mantiene por la contradicción de la regla y por la falta de procedimiento, no por la probabilidad. |

## Orchestrator observations

| obs | status | detail |
|---|---|---|
| (o1) Con el sello 'Updated' fuera (G-20(1)), ¿queda dateModified u otra señal de build-time que siga mintiendo? | CUBIERTA-POR-LENTE | Lo cubrió C-R1-09 y el árbitro lo re-midió. GET prod /news/, /es/noticias/, /, /es/, /commune/santiago/ y /methodology/: 0 dateModified, 0 datePublished, 0 modified_time/updated_time. El JSON-LD de /news/ es un WebPage sin fechas. sitemap-0.xml tiene 0 <lastmod>. En site/src, `generated` solo se usa en news.astro:64-75 y es/noticias.astro:63-74, y el único literal 'Updated/Actualizado' está en news.astro:242 y es/noticias.astro:241, que 35-04 elimina. No queda ninguna señal de build-time visible. El data-build-now nuevo es un atributo y no texto. |
| (o2) Rebuild del heartbeat (G-20(7)) más deploy-on-code con data paths (G-21(6)): ¿presupuesto de builds de Cloudflare (500/mes) y ausencia de loops? | CUBIERTA-POR-LENTE | Lo cubrieron A-R1-C4, B-R1-C03 y B-R1-C04, y el árbitro re-leyó los archivos. Presupuesto en el peor caso: el deploy de news ≤ 4/día (≤124/mes, igual o menor que hoy, porque hoy cada corrida despliega), más el heartbeat ≤ 1/día y solo en rojo (≤31/mes), más los pushes humanos (site/**, data/**, Dependabot), lo que da ≪ 500. No hay loop: news-pipeline y cead-scraper hacen checkout sin token (GITHUB_TOKEN persistido, news-pipeline.yml:37-41) y commits '[skip ci]' (:92). Los pushes con GITHUB_TOKEN no disparan workflows. heartbeat, r2-archive y ci usan persist-credentials: false y no pushean. El deploy hook no genera pushes. Historial: la última corrida de deploy-on-code fue el 09-23 03:35Z (push). |
| (o3) ¿El cierre depende de que current.json tenga last_new_incident_at? Hoy no lo tiene. ¿Qué pasa si la Fase 34 tarda? | DESCARTADA | No es un defecto. freshness.mjs y newsEvidence usan G-05 con fallback max(date)+1d, así que el cierre exige evidencia ≤48h, no el campo en sí. El campo aparece solo la primera vez que una corrida viva agrega ids (store.py:237-241). Mientras la 34 no cierre, el Step 0 de los 7 planes (grep '^- \[x\] \*\*Phase 34' = 0 hoy; ROADMAP.md:119 '- [ ]') bloquea la ejecución (G-19). Si la 34 cierra y aun así freshness da rojo, 35-07 Task 1 paso 4 retiene el push, re-chequea y, si sigue >24h en rojo, abre un gap plan de la 34, sin excluir freshness (G-20(9), R-16 aceptado). Residual menor: el '(at most 6h later)' de 35-07:95 es inexacto (medido: 7,8 h entre las corridas 03:04 y 10:52Z del 09-22), ver no-bloqueante A-R1-07. Prod hoy: 742 incidentes 08-24..09-04, sin last_new (GET del árbitro). |

## Closures verified

- B-R1-01 confirmado por el árbitro: el guard de 35-04:173 da rc=1 sobre el dist actual (115 archivos con 'geolocated in'), por i18n.ts:486.
- B-R1-02 confirmado por el árbitro: la asignación de M de 35-05:131 da SyntaxError, rc=1 y M=[/ics-cv-mut].
- C-R1-01/A-R1-05 confirmado: ResultPanel.tsx:289-290 más 35-03:146 dan un tooltip contradictorio. composite_config.py:11-14 fija 2024 como el año en que todas las fuentes son finales, y national.json tiene 2025 partial=False.
- C-R1-04 confirmado: NewsStrip.tsx:72-73 extiende el rango a anchor−(windowDays−1), y los planes no mencionan NewsStrip ni MapIsland.
- A-R1-01: la contradicción en 35-07:166 frente a :167 está confirmada por lectura, y la medición de 116 commits del bot con 0 no-ops (mínimo 3 ids, suma 1.933) la re-midió el árbitro.
- Guard de literales prohibidos de 35-03 alcanzable: solo hay coincidencias en ResultPanel.tsx y region/[slug].astro EN/ES, y en el dist aparecen en 16+16 páginas de región, todas editadas por 35-03.
- Precondición G-19: ROADMAP.md:119 dice '- [ ] **Phase 34', así que el Step 0 detiene hoy los 7 planes.
- El store.py actual (:232-253) escribe generated=ref_now siempre, y las claves de current.json son generated, window_days e incidents (sin last_new). El guard de 35-02 con subconjunto de claves es consistente con eso.
- news.astro:45-66 y :190 no filtran incidentes antes de computeDayBuckets, así que el chequeo por barra de #18 (payload completo) es coherente con los buckets.
- HomeNewsPulse.astro:25 (card hidden), :164 (return si no hay incidentes) y :180 (card.hidden=false) confirman A-R1-09: el aviso 'none' de la home es código muerto. No es bloqueante.
- Cadencia medida con gh run list: las corridas programadas de news salen 3-5 h tarde (03:04, 10:52, 16:10 y 20:48Z) y el heartbeat del cron 12:00 corre entre las 14:56 y las 17:17Z (A-R1-07).
- Las ediciones del premortem R-01..R-14 están presentes en el texto de los planes (B-R1-C10). Sus defectos de ejecución están en ediciones_previas_no_aplicadas.

## Measurements reserved to the orchestrator

- Duración real del gate de 35-07 T1 (harness de 2 builds + build + 18 validadores + vitest + astro check + pytest) frente al tope de 10 min del tool. No se midió porque requiere escribir dist; conviene correr el harness con run_in_background y registrar el tiempo (B-R1-06).
- Confirmar al cierre de la Fase 34 que astro check sigue en 0 errores (línea base: 0 errores en e565ce8) y que la línea base de pytest/vitest es la que registró el cierre de la 34.
- Al ejecutar 35-07: capturar SHIP después de un `git push` exitoso (`date -u +%FT%TZ`) y excluir de W las corridas cuyo headSha no descienda de SHA (A-R1-02, recomendado).
- Al ejecutar 35-07 T2: agregar al lote de prod index.html y es/index.html con data-coverage-gaps y el conteo de .pulse-stale contra el veredicto (C-R1-05, recomendado; requiere data-build-now en .pulse-card).

## Lens verdicts

- C — Producto y ruta servida (ronda 1, commit 89f0d6a): NO-GO (13 findings)
- B — EJECUTABILIDAD (ronda 1, planes 35-01..35-07 @ 89f0d6a): NO-GO (16 findings)
- A — MEDICIONES E INSTRUMENTOS (ronda 1, 35-01..35-07 @ 89f0d6a): NO-GO (14 findings)

## Condition closure log (append)

