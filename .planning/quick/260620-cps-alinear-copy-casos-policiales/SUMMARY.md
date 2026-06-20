---
id: 260620-cps
title: Alinear copy de medida a "casos policiales" (denuncias + detenciones flagrantes)
type: quick
status: complete
created: 2026-06-20
completed: 2026-06-20
commit: 2feb81a
---

# Summary — Copy alignment: "casos policiales", not "denuncias"

## What & why
Investigación de metodología (a pedido del usuario) confirmó que el pipeline scrapea
**casos policiales** (`tipoVal="1,2"` = denuncias + detenciones por flagrancia) — la premisa
de que "solo usamos denuncias / perdemos flagrancia" era incorrecta a nivel de datos. El defecto
real era de **copy**: superficies secundarias de alto tráfico SEO mislabelaban la cifra mostrada
como "denuncias", contradiciendo la página de metodología (que dice casos policiales correctamente).

## Changes (copy-only, EN+ES, cero cambios en datos/lógica/pipeline)
- `site/src/lib/familyDefs.ts`:
  - `RANKING_METHODOLOGY_EN` ×7 + `RANKING_METHODOLOGY_ES` ×7 → "casos policiales (complaints plus arrests in the act)" / "(denuncias más detenciones flagrantes)"
  - `RANKING_RATE_EXPLAINER_EN` / `_ES` → casos policiales
  - `FAMILY_DEFS_ES.vif` → "Incidentes reportados" (antes "Denuncias", inconsistente con las otras familias)
- `methodology.astro:248` + `metodologia.astro:256` → "casos policiales" (antes decían "police denuncias" / "denuncias policiales" para describir el índice CEAD)
- `es/rankings.astro:50` → "registros policiales (casos policiales)" (alinea con gemelo EN "reported counts")

## Out of scope (intencional)
- Prose editorial sobre conducta de denuncia / subregistro en glosario, mapa-seguridad-santiago,
  delitos-por-comuna, comunas-mas-seguras, is-chile-safe — correcta, NO tocada.
- D-08 preservado: no se muestra split denuncias vs detenciones; solo el total casos policiales.

## Verification
- `cd site && npm run build && npm run validate` → build verde, **14/14 validators PASS**.
- Grep post-fix: 0 ocurrencias de las strings mislabel.

## Follow-up (diferido, no en este task)
- Opcional: revisar D-08 para exponer el split denuncias/detenciones (útil en drogas/armas).
  Usuario eligió mantener D-08 por ahora.
