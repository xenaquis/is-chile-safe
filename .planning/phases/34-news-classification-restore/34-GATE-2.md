---
phase: 34
artifact: adversarial re-gate
round: 2
plans_evaluated: 34-01..34-06-PLAN.md @ 3786fdb
verdict: GO-CONDICIONADO
blockers: 3 (all mechanical)
agents: 3 (haiku diff-check, opus diff lens high, fresh opus arbiter xhigh) — cheap re-gate per corrida-autonoma §3.6
subagent_tokens: 490575
cycle: 2 of 2 (closed by conditions, no further gate round)
---

# Phase 34 — Adversarial Gate, Round 2

## Verdict: GO-CONDICIONADO

GO-CONDICIONADO para 34-01..34-06 @ 3786fdb (ronda 2). Las 23 ediciones de R1 están en el texto; verifiqué por muestreo BF-01, BF-02, BF-04, BF-06 y BF-09. Tres de ellas quedaron con defectos nuevos. Firmo 3 bloqueantes CONFIRMADOS y los tres se corrigen con ediciones mecánicas, sin rediseño:

- **BF2-01** (de D-R2-01): los polls de prod agregados para BF-07 usan grep -c sobre HTML minificado. Medí 1 contra 799 con prod sano. Además, el fetch va después de calcular L, y L se calcula una sola vez.
- **BF2-02** (de D-R2-02): la regla 'si falla random se retiene todo' se aparta de G-11 y, junto con el umbral por estrato, no está registrada como G-NN antes de ejecutar. Con p=0.9 la probabilidad de no publicar nada es 0.32. Se resuelve con un G-14 de contenido fijado.
- **BF2-03** (de D-R2-03 y D-R2-09): la rama sin publicación no tiene salida en 34-05 T3 ni en 34-06. step 1 lanza ValueError con BF vacío, step 2, la truth y el done no tienen condición, y el Partial pre-declarado no se alcanza.

Ninguno deja /news/ vacío ni publica datos erróneos; el peor efecto es un FAIL espurio o una pausa.

No-bloqueantes: D-R2-04, D-R2-05, D-R2-06, D-R2-08 y ARB-01. Descarto D-R2-07 con medición: el estrato cue tiene unos 25 delitos chilenos.

No escribí en el repo ni en data/, no hice commits ni deploys, y no llamé a ningún LLM. Solo hice GET a prod y lecturas y cálculos locales.

## Diff-check of R1 edits (haiku)

| id | status | evidence |
|---|---|---|
| BF-01 | APLICADO | 34-01-PLAN.md:348 verification section states decision.status ∈ {WINNER, FALLBACK_WINNER, DEEPSEEK_DIRECT}; 34-02-PLAN.md:204/281-284 branches by decision.status with DEEPSEEK_DIRECT probe JSON key read; 34-02-PLAN.md:465 Revision R2 confirms both edits |
| BF-02 | APLICADO | 34-03-PLAN.md:229-230 behavior states: start/end sha256 snapshot of real data/incidents replaces git status empty assertion; data/ dirty at 34-05 gate allowed; 34-03-PLAN.md Revision R2 confirms snapshot approach |
| BF-03 | APLICADO | 34-05-PLAN.md:137 must_haves redefines gnews_title_only = url host news.google.com; Task 1 behavior includes real BioBio row test; Task 2 step 7b states exit 5 STOP on 0-candidate strata; 34-05-PLAN.md:350 Revision R2 confirms |
| BF-04 | APLICADO | 34-05-PLAN.md:26 must_haves states exit codes 0/3/4 with no per-run budget; :118-119 Task 1 behavior: budget_s=inf, exit codes 0=complete/3=cap/4=exhausted; :220 step 5 exit 4 → re-invoke; 34-05-PLAN.md:351 Revision R2 confirms |
| BF-05 | APLICADO | 34-01-PLAN.md:29 must_haves truth 4 states finish_length_count == 0 AND empty_content_count == 0 disqualify in BOTH tiers; Task 2 behavior line 212 transient_truncation/_empty in both tiers; 34-01-PLAN.md:372 Revision R2 confirms |
| BF-06 | APLICADO | 34-01-PLAN.md:312/373 Fast-path does NOT trigger on G-08 outcome; fires only on 09-30 or pause 1; 34-02-PLAN.md:395-412 section 'Fast-path fallback' documents directive triggers only; no IMMEDIATELY as active instruction; 34-02-PLAN.md:465 Revision R2 confirms IMMEDIATELY removed |
| BF-07 | APLICADO | 34-04-PLAN.md:17 must_haves states served prod is curled and verified; :78/105 Task 2 step 11/6b curl polls of ischilesafe.com/data/incidents/current.json count+max(date) and /news/ counts; 34-04-PLAN.md Revision R2 confirms curl verification steps |
| BF-08 | APLICADO | 34-06-PLAN.md:23 must_haves states NREC-01 Complete only if decision.status == WINNER else Partial; NREC-09 only if residual == 0; :129-131 Task 2 step 5 sets these conditionally; 34-06-PLAN.md:183 Revision R2 confirms conditional status setting |
| BF-09 | APLICADO | 34-05-PLAN.md:267-268 Residual check computes api_error_remaining + not_attempted + withheld; :296-297 done/resume-signal explicitly states residual == these three; 34-05-PLAN.md:353 Revision R2 confirms withheld in residual |
| NB-01 | APLICADO | 34-01-PLAN.md:140-143 Task 0 action: blind first pass over all 44 items without candidate list; :156 re-score paragraph states G-08 expected route; 34-01-PLAN.md:375 Revision R2 confirms |
| NB-02 | APLICADO | 34-01-PLAN.md:302 Task 3 loop only breaks on exit 3 ([ $rc -eq 3 ] && break); Task 2 probe rule disqualifies reasoning_unfixable; 34-01-PLAN.md:376 Revision R2 confirms |
| NB-03 | APLICADO | 34-05-PLAN.md:25 must_haves states per-stratum threshold ceil(0.86·n_s) AND overall ≥43/50; :229-231 Task 2 step 7b: failing stratum withheld, re-audit 30 at ≥26/30, random fail → all withheld; 34-05-PLAN.md:350 Revision R2 confirms |
| NB-04 | APLICADO | 34-05-PLAN.md:157 Task 2 step 4 c labeled 'ceiling-priced' when usage_cost_present=false; :296 report breaks down spend; 34-05-PLAN.md:352 Revision R2 confirms ceiling-priced label |
| NB-05 | APLICADO | 34-01-PLAN.md:178-180 describe 7+3=10 tests; 34-02-PLAN.md:108 test count corrected in behaviors; 34-02-PLAN.md:408-409 Fast-path NEWS_PROVIDER=deepseek flip in DEEPSEEK_DIRECT branch; 34-02-PLAN.md:467 Revision R2 confirms |
| NB-06 | APLICADO | 34-05-PLAN.md:169 must_haves states redispatched items drained; Task 2 step 3 router.classify and pop_redispatched in classification loop; per-item cache writes; 34-05-PLAN.md:349 Revision R2 notes backfill drains pop_redispatched |
| NB-07 | APLICADO | 34-01-PLAN.md:223-224 spend guard test: 0.499+0.0025 → exit 3; 0.4975+0.0025=0.50 → call made; 34-01-PLAN.md:380 Revision R2 confirms boundary arithmetic |
| NB-08 | APLICADO | 34-02-PLAN.md:388 verify uses 'git grep -l' (tracked files only, no .pyc); :390 explanation confirms no __pycache__ in grep count; 34-02-PLAN.md:468 Revision R2 confirms git grep approach |
| NB-09 | APLICADO | 34-03-PLAN.md Task 2 §Task 2 (line 194-197) news alert step id=news_hb and separate alert for pipeline-failure-news-heartbeat; 34-06-PLAN.md Task 2 step 3b closure exception for heartbeat before first run; 34-06-PLAN.md:184 Revision R2 confirms |
| NB-10 | APLICADO | 34-05-PLAN.md:226 Task 2 step 3 fourth question on title fidelity recorded but not gated; :232 re-audit allows v-06 class recording; deferred-live note that cards carry LLM-rewritten headlines until FID-01; 34-05-PLAN.md Revision R2 notes deferred-live |
| NB-11 | APLICADO | 34-05-PLAN.md:234-237 methodology disclosure wording uses date range, 'current classifier', and 'items not verified were not published'; :232 no commit if no publication; 34-06-PLAN.md:300 regex amplified; deferred-live records literal disclosure text |
| NB-12 | APLICADO | 34-06-PLAN.md:300 Task 2 step 3 regex reuses 34-05 pattern plus grandfather\|grandmother\|father-in-law\|mother-in-law\|nephew\|niece\|brother-in-law\|sister-in-law\|prison\|inmate; 34-06-PLAN.md:186 Revision R2 confirms regex amplification |
| NB-13 | APLICADO | 34-05-PLAN.md:312 Task 3 before step 2: git add .planning && git commit before pull --rebase; git status --porcelain empty check; rebase.autoStash not assumed; 34-05-PLAN.md shows committed plan edits before pull |
| NB-14 | APLICADO | 34-02-PLAN.md:363 Task 2 verify: git status --porcelain data/ → empty; 34-03-PLAN.md Task 3 fixture NEWS_DATA_DIR autouse in conftest; 34-03-PLAN.md:239 conftest.py autouse fixture at 34-03; 34-02-PLAN.md:285 BF-01 verify includes NB-14 |

## Blockers (mechanical)

| id | origin | title | required edit |
|---|---|---|---|
| BF2-01 | D-R2-01 (lente), verificado y medido por el árbitro | Los polls de ruta servida agregados en R2 (BF-07) usan grep -c, que cuenta líneas y no cards: con prod sano dan 1 contra 799 y el paso falla | - En 34-04:78, 34-04:105 y 34-05:284, reemplazar `grep -cE '<pat>'` por `grep -oE '<pat>' \| wc -l`. - En 34-04:78 y :105, poner `git fetch origin` ANTES de calcular L. En 34-05:284 ya está antes. - En los tres polls, recalcular L dentro de cada iteración del loop (`git fetch origin` + `git show origin/master:...`) y comparar R con ese L. |
| BF2-02 | D-R2-02 (lente), verificado por el árbitro. La severidad bajó de rediseño a registro mecánico. | La regla de auditoría G-11 del plan se aparta de G-11 y no está registrada como G-NN: 'random falla → se retiene todo' y el umbral por estrato | Antes de ejecutar 34-05 Task 2, agregar G-14 fechado a la directiva § Decision log con: (i) ceil(0.86·n_s) como definición de 'failing stratum' de G-11, anotando que la publicación completa exige de hecho ≥45/50; (ii) qué pasa si falla random, eligiendo una de dos: ratificar 'retener todo' (el texto actual) o alinearse con G-11 literal (retener random y re-auditar 30 del resto no retenido a ≥26/30). La recomendada es la segunda, porque no agrega una regla más estricta que la registrada; (iii) si la re-auditoría de 30 usa solo ≥26/30 global o también umbrales por estrato. Después, 34-05:25 y :229-232 deben citar G-14 y decir exactamente lo mismo. En :232, 'Record the G-NN' queda solo para registrar el resultado. |
| BF2-03 | D-R2-03 + D-R2-09 (lente), verificado por el árbitro | La rama withheld/no-publicación de 34-05 no tiene salida en 34-05 T3 ni en 34-06: el Partial pre-declarado de NREC-10 no se alcanza | En 34-05, rama de no publicación: - declarar que Task 3 NO corre: sin apply, sin commit de datos, sin push y sin R2; - el done/resume de Task 2 o Task 3 dice 'no-publication recorded (G-14); Task 3 skipped'; - el residual NREC-09 = selected (todo sin aplicar).  En 34-06: - step 1: la comparación G-07(a) corre solo si existe el commit data(34-05); si no, registrar 'no backfill commit' y seguir; - step 2: con resultado withheld o sin publicación, las fechas con 0 cards se reportan como k días sin cobertura, no como FAIL. Se mantienen max(date) ≥ hoy−1 y la igualdad EN=ES; - truth :21 y done/resume :141-142: aceptar ese estado con NREC-10 'Partial (<k> days uncovered: withheld)' y la pregunta al owner en deferred-live. |

## Conditions

1. C1 (BF2-01). Cambios en 34-04:78, 34-04:105 y 34-05:284: - `grep -cE` pasa a `grep -oE ... \| wc -l`; - `git fetch origin` va antes de calcular L en 34-04:78 y :105; - L se recalcula (fetch + git show) dentro de cada iteración del poll en los tres sitios. Se verifica por diff: `grep -n 'grep -cE' 34-04-PLAN.md 34-05-PLAN.md` no da hits en los checks de news-date, y cada loop contiene `git fetch origin`.
2. C2 (BF2-02). Antes de ejecutar 34-05 Task 2, la directiva § Decision log contiene un G-14 fechado que fija: (i) ceil(0.86·n_s) como definición de 'failing stratum', con la nota de que la publicación completa exige de hecho ≥45/50; (ii) qué pasa si falla random: retener todo, o seguir G-11 literal (retener random y re-auditar 30 del resto a ≥26/30), que es la opción recomendada; (iii) el umbral de la re-auditoría de 30. 34-05:25 y :229-232 citan G-14 y dicen exactamente lo mismo. Se verifica por diff de la directiva y de 34-05.
3. C3 (BF2-03). Rama withheld o sin publicación. En 34-05: - Task 3 se declara omitida (sin apply, commit de datos, push ni R2); - el done/resume acepta 'no-publication recorded (G-14); Task 3 skipped'; - el residual NREC-09 = selected. En 34-06: - step 1: el check G-07(a) queda condicionado a que exista el commit data(34-05); si no existe, registrar 'no backfill commit'; - step 2: los días con 0 cards por withheld o sin publicación se reportan como k días sin cobertura, no como FAIL; - la truth :21 y el done/resume :141-142 aceptan ese estado con NREC-10 'Partial (<k> days uncovered: withheld)'. Se verifica por diff de 34-05 y 34-06.
4. C4. Cada condición se aplica en un commit docs(34) con una sección '## Revision R3 (gate R2)' en los planes afectados. El orquestador (no un nuevo gate) comprueba C1-C3 por diff antes de ejecutar 34-01. Según la directiva (máx. 2 ciclos) esto no reabre el gate.

## Non-blockers

| id | title | detail |
|---|---|---|
| D-R2-04 | La definición de INCOMPLETE (api_errors>0) contradice que transient ⊂ api_errors no vuelve INCOMPLETE | CONFIRMADO en el texto. 34-01:213 y :253 definen INCOMPLETE por api_errors>0. Pero :29 y :245 (G-13) cuentan transient dentro de api_errors, y :245 aclara explícitamente que transient no hace INCOMPLETE. Además, :314 exige api_errors == 0 en la fila backup, así que con un solo finish_length la evidencia NREC-04 queda en falso rojo. La frase explícita de :245 hace improbable el error. Edición sugerida: INCOMPLETE ⇔ (api_errors − transient) > 0 en :213 y :253, con un test; en :314, non-transient api_errors == 0. |
| D-R2-05 | Fast-path G-12: el pull --rebase sobre el hotfix literal choca con los commits locales de 34-01/34-02 | CONFIRMADO en el texto. El paso 1 del hotfix edita classifier.py:79 y los kwargs de _call_api (:211-247), y el paso 3 edita test_classifier.py:115-122. 34-01 refactoriza _call_api y 34-02 reescribe :58-79 y ese test. Así que `git switch master && git pull --rebase` (34-02:403) casi seguro choca, y no hay regla de resolución. Es solo contingencia y el gate de 34-04 re-corre todo. Sugerido: ante conflicto, conservar el lado local (en el rebase es --theirs) y verificar que model_config coincida con el modelo del fast-path, o diferir el pull hasta 34-04. |
| D-R2-06 | 34-04 T1 step 11 es vacuo | CONFIRMADO. 34-01..34-03 no tocan data/, así que lo servido ya coincide con origin/master antes del build de Cloudflare (medido: 799/09-04 en ambos). El step 10 solo ve la conclusión del workflow que hace POST al hook. Es inocuo; la prueba con contenido real es 6b. Sugerido: declararlo smoke no discriminante. |
| D-R2-08 | El slug de probe-/run-<slug>.json no está definido; 34-02 hardcodea probe-deepseek-deepseek-v4-flash.json | CONFIRMADO en el texto: 34-01:262 y :271 no definen el slug, y 34-02:219 y :284 lo hardcodean. Si slug = provider-model, el probe DIRECTO se llama exactamente así, y REASONING_EXTRA_BODY_OPENROUTER se copiaría de la variante thinking_disabled; el assert pasaría en falso. El impacto es PLAUSIBLE, solo en la rama DEEPSEEK_DIRECT, y el forced-backup en vivo de 34-04 5b lo atraparía. Sugerido: fijar slug = model.replace('/','-') para openrouter y 'direct-'+model para deepseek, o un equivalente sin colisión, y usarlo en 34-02 y 34-05. |
| ARB-01 | 34-05 7b exige que los conteos 'must show' non_chile_cue ≥ 10, pero el sampler (:141) admite 0<n<cuota con shortfall | Hallazgo del árbitro. Si hay menos de 10 OK en cue, el sampler toma lo que hay e imprime el shortfall (:141), pero 7b (:225) lo trata como mismatch, es decir FAIL. Es poco probable: medí unos 25 delitos chilenos en el estrato. Sugerido: en 7b, un shortfall se completa con random y se registra; STOP solo con 0 (exit 5). |

## Discarded

| id | title | reason |
|---|---|---|
| D-R2-07 | Exit 5 del sampler en non_chile_cue con un clasificador sano | Medí el estrato (no-gnews con cue): tiene 102 filas, y al leerlas cuento unos 25 delitos claramente chilenos. Ejemplos: 'Detienen en Antofagasta a condenado por homicidio', 'Concepción: Fiscalía acusó a hermanos por parricidio frustrado', 'Incautan en Calama 660 kilos', 'Detienen a tres colombianos que asaltaron ... barrio Franklin', 'Ciudadano colombiano murió baleado ... en Santiago', 'Prisión preventiva ... secuestrar a ciudadano venezolano en Puerto Montt'. Que un clasificador sano no deje ningún OK ahí es muy improbable. Si pasa, el exit 5 detecta un clasificador roto, no un estrato mal definido. El hallazgo queda en PLAUSIBLE y no firma. El residuo real (el requisito de ≥10 frente a la regla de shortfall) queda como ARB-01 no-bloqueante. |

## Closures verified by the arbiter

- Muestreo de BF APLICADOS, leído por mí @ 3786fdb: - BF-01: 34-01:324-325/:348; 34-02:204, :210-221, :281-285 con verify ramificado; 34-04:96-98, :142. - BF-02: 34-03:229 con snapshot sha256 más 'writes under tmp_path', y gemelo en 34-05:274. - BF-04: 34-05:26, :118-119, :158-160, :220. - BF-06: grep -i 'immediate' sin ninguna instrucción activa de fast-path inmediato; 34-01:312, 34-02:397-403, 34-04:112 alineados con G-12. - BF-09: 34-05:296-297. - Revisé además que BF-03 (34-05:25, :136-142, :225), BF-05/G-13 (34-01:29, :213, :216, :245, :269, :275) y BF-08 (34-06:23, :129-131) estén aplicados en el texto.
- D-R2-01 medido por mí con GET a prod el 2026-09-22: /news/ tiene grep -c=1 y grep -o=799; /es/noticias/ tiene grep -c=1 y grep -o=799. El current.json servido tiene 799 incidentes, max 2026-09-04, generated 2026-09-22T20:49:36.886Z, igual que origin/master. El one-liner de L funciona sin PYTHONIOENCODING (rc=0).
- D-R2-02, aritmética recalculada con python: ceil(0.86·n) = 9/18/26/43. P(falla random) y P(falla algún estrato) según p: 0.85 → 0.595/0.911; 0.88 → 0.437/0.791; 0.90 → 0.323/0.663; 0.92 → 0.212/0.496.
- D-R2-03: `git log -1 --grep='data(34-05)'` devuelve vacío hoy. Las filas no-gnews por día (09-05..09-22) van de 40 a 68, así que retener solo gnews no deja días sin cobertura.
- Población NREC-09 re-medida: selected=2073, gnews=1089, no-gnews=984, cue no-gnews=102.
- classifier.py:58-79 leído: la rama deepseek usa por defecto 'deepseek-v4-flash' (:65) y el literal granite está en :79. _call_api está en :211-247. test_classifier.py:115-122 afirma el literal muerto. Esto confirma la base de D-R2-05 y D-R2-11.
- D-R2-10/11 (cierres de la lente): coinciden con lo que leí. La rama DEEPSEEK_DIRECT es coherente con classifier.py:65; budget_s=float(env or 1200) acepta 'inf' (34-02:267); classify() devuelve None solo por budget o exhausted (34-02:145), así que exit 4 queda bien definido con budget inf.
- Diff de la ronda (git diff --stat 2728b05 3786fdb): solo cambian los 6 PLAN.md de la fase 34, con 170 inserciones y 65 borrados. No hay cambios fuera de alcance.

## Condition closure log (append)

