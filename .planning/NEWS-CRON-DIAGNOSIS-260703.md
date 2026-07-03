# Diagnóstico — cron de noticias "no funciona" (2026-07-03)

**Método:** gh CLI (runs + logs), git fetch/compare, curl a prod, BrowserOS sobre prod (/news/ y /map/ con capa de incidentes activa).

## TL;DR

El cron **hoy SÍ funciona** y prod está fresco (generated 2026-07-03, 137 incidentes, hasta 2026-07-02). Lo que pasó:

1. **Causa raíz del apagón (06-23 → 06-30):** TODOS los runs programados fallaron en 2–3 s con
   > "The job was not started because recent account payments have failed or your spending limit needs to be increased"
   — **billing de GitHub Actions** (repo es PRIVADO → cuota de minutos aplica). Se recuperó solo el **07-01** (reset mensual de cuota/facturación). 32 runs consecutivos fallidos, **en silencio** — nadie se enteró en 8 días.
2. **Ventana de datos perdida para siempre:** histograma prod: 06-22 (18 items) → **nada 06-23..06-28** → 06-29 (5), 06-30 (6) capturados a medias al reanudar. RSS es rolling; no recuperable.
3. **La percepción "noticias muy antiguas" viene del repo LOCAL:** el `current.json` local es del **06-20** (42 incidentes) — es lo que se vio en el preview de la Fase 25. El repo local está **divergido: 45 commits adelante (toda la Fase 25, sin push) / 17 atrás (auto-updates de datos)**.
4. **Fallas secundarias encontradas:**
   - Run 07-02 19:18: deploy hook Cloudflare devolvió **HTTP 400** → `curl --fail --retry 3` NO reintenta errores HTTP (solo de red) → ese deploy se perdió (el siguiente run lo cubrió).
   - **CEAD scraper roto** (07-01): `ModuleNotFoundError: No module named 'pipeline'` — bug de import path, independiente del billing.
   - Warnings DeepSeek `JSONDecodeError` en cada run (items sueltos descartados) — ruido tolerable, endurecible con `response_format=json_object`.
   - Deprecation: actions/checkout@v4 y setup-python@v5 corren forzadas en Node 24 (aviso, no falla aún).

## Evidencia

- `gh run list --workflow=news-pipeline.yml`: failure ×32 del 06-23T09:32 al 06-30T19:49; success desde 07-01T03:26; annotation de billing en run 28471578319.
- `gh repo view`: `"isPrivate": true`.
- Prod: `curl /data/incidents/current.json` → generated 07-03T02:37, 137 incidentes, rango 06-17→07-02. BrowserOS: /news/ muestra "Updated July 3, 2026"; /map/ renderiza 137 pins (todos con lat/lng, capa estructura: fetch client-side de current.json → IncidentPinLayer).
- Local: `git rev-list --left-right --count master...origin/master` → `45 17`. current.json local generated 06-20.
- CEAD: run 07-01 log → `ModuleNotFoundError: No module named 'pipeline'`.

## Qué habría que hacer (plan)

**A. Acción del dueño (no automatizable) — PRIMERO:**
1. GitHub → Settings → Billing: verificar método de pago fallido / subir spending limit de Actions. Alternativa estructural: hacer el repo público (Actions gratis ilimitado) — decisión del usuario (expone .planning/ con estrategia SEO).

**B. Fixes de código (automatizables, ~1 sesión):**
2. **Alerting en fallo** (constraint de CLAUDE.md: "pipeline debe fallar con gracia y alertar"): step `if: failure()` en `news-pipeline.yml` y `cead-scraper.yml` que abra/actualice un GitHub Issue (`gh issue create/comment`, label `pipeline-failure`) — un apagón de 8 días no puede volver a ser silencioso.
3. **Guard de frescura en build**: validador que falle/avise si `data/incidents/current.json.generated` > 3 días al momento del build (validador #15 junto a los 14 existentes).
4. **Deploy hook resiliente**: reemplazar `curl --fail --retry 3` por retry que también cubra 4xx/5xx (`--retry-all-errors` + backoff), manteniendo el fallo visible si agota reintentos.
5. **CEAD import fix**: correr como módulo (`python -m pipeline.scrape_cead`) o `PYTHONPATH=.` en el workflow; verificar con run manual `workflow_dispatch`.
6. **Sync del repo local + deploy de Fase 25**: `git pull --rebase origin master` (los 17 commits remotos solo tocan `data/` — sin conflicto esperado con Fase 25) → `git push` → dispara deploy-on-code → prod queda con UI nueva + datos frescos.
7. (Menor) DeepSeek: `response_format={"type":"json_object"}` en el classifier para eliminar los JSONDecodeError.

**C. No hacer:** intentar recuperar 06-23..06-28 (RSS rolling, irrecuperable); cambiar frecuencia del cron (4×/día está bien y no fue la causa).

## Prompt listo para contexto limpio

Ver `.planning/PROMPT-news-cron-fix-260703.md` (pegarlo tras `/clear`).
