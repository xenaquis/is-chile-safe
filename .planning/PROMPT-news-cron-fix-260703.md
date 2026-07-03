# Prompt para fix del pipeline de noticias (pegar tras /clear)

> Decisión 2026-07-03: el repo se hará PÚBLICO (Actions gratis ilimitado) en vez
> de arreglar billing. Cambiar visibilidad es acción manual del dueño:
> GitHub → Settings → General → Danger Zone → Change visibility.

---

Lee .planning/NEWS-CRON-DIAGNOSIS-260703.md (diagnóstico 2026-07-03: apagón del
cron de noticias 06-23→06-30 por cuota/billing de GitHub Actions en repo privado,
recuperado el 07-01; prod hoy fresco; repo local divergido 45↑/17↓). Decisión ya
tomada: el repo pasa a PÚBLICO (lo hace el dueño a mano) — no propongas
alternativas de billing. Ejecuta con /gsd:quick los fixes, en este orden
(commits atómicos):

0. PRE-PUBLIC AUDIT (antes de que el dueño cambie la visibilidad): barrido de
   secretos en TODO el historial y working tree — `git log -p` grep de patrones
   (sk-, api_key, DEEPSEEK, token, password, CF_DEPLOY_HOOK, secret) + revisar
   .env* no commiteados + pipeline/cache/ y .planning/ por credenciales o URLs
   de deploy hook pegadas en docs. Reportar hallazgos ANTES de publicar; si hay
   un secreto en el historial, detenerse y avisar (requeriría rotarlo). Los
   GitHub Secrets del repo (DEEPSEEK_API_KEY, CF_DEPLOY_HOOK_URL) no se exponen
   al publicar — eso está OK.
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
