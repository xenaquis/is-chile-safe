# Prompt para fix del pipeline de noticias (pegar tras /clear)

> Prerequisito manual ANTES de correr esto: arreglar GitHub Billing
> (Settings → Billing: payment method / spending limit de Actions).
> El código no puede arreglar eso.

---

Lee .planning/NEWS-CRON-DIAGNOSIS-260703.md (diagnóstico 2026-07-03: apagón del
cron de noticias 06-23→06-30 por billing de GitHub Actions en repo privado,
recuperado el 07-01; prod hoy fresco; repo local divergido 45↑/17↓). Ejecuta con
/gsd:quick los fixes B del diagnóstico, en este orden (commits atómicos):

1. SYNC + DEPLOY: `git pull --rebase origin master` (17 commits remotos, solo
   tocan data/ — si hay conflicto en current.json, gana la versión remota) y
   `git push` — esto publica la Fase 25 + datos frescos vía deploy-on-code.
   Tras el deploy: `curl -I https://ischilesafe.com/404-test/` debe dar 404
   (verificación pendiente de Fase 25) y /news/ debe mostrar el layout nuevo
   (h2 por mes + chips) con fechas de julio.
2. ALERTING: en .github/workflows/news-pipeline.yml y cead-scraper.yml, agregar
   step final `if: failure()` con permissions issues:write que haga
   `gh issue create` (o comment si ya existe uno abierto con label
   pipeline-failure) usando GH_TOKEN=${{ github.token }}. Título:
   "[pipeline] {workflow} failed on {date}". Motivo: 32 runs fallaron en
   silencio durante 8 días.
3. FRESHNESS GUARD: nuevo validador (#15) en site/scripts/validate/ que lea
   data/incidents/current.json y FALLE si `generated` tiene más de 3 días
   (mensaje debe decir que probablemente el cron está caído y linkear el
   diagnóstico). Registrarlo en all.mjs.
4. DEPLOY HOOK: en news-pipeline.yml reemplazar
   `curl -X POST --fail --silent --show-error --retry 3 "$CF_HOOK"` por
   `curl -X POST --fail --silent --show-error --retry 5 --retry-all-errors "$CF_HOOK"`
   (el 400 del 07-02 no se reintentó porque --retry no cubre errores HTTP).
5. CEAD FIX: el workflow cead-scraper.yml falla con
   `ModuleNotFoundError: No module named 'pipeline'` — cambiar la invocación a
   `python -m pipeline.<entrypoint>` o exportar `PYTHONPATH=.` en el step
   (mirar cómo lo hace news-pipeline.yml que sí funciona). Verificar con
   `gh workflow run cead-scraper.yml` + `gh run watch`.
6. DEEPSEEK JSON: en pipeline/news/classifier.py agregar
   `response_format={"type": "json_object"}` a la llamada (elimina los
   JSONDecodeError por respuestas truncadas). Correr pytest de pipeline.

Restricciones: modelo solo deepseek-v4-flash/pro; NO tocar la lógica de
clasificación ni el rolling window; NO intentar recuperar la ventana perdida
06-23..06-28 (RSS rolling, irrecuperable); OneDrive: encadenar build+validate
en un solo comando (`cd site && npm run build && npm run validate`); verificar
workflows con `gh workflow run` + `gh run watch`, no esperando al cron.
