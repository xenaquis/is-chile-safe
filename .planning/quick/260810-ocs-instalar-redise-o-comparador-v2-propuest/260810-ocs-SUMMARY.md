---
id: 260810-ocs
status: complete
verdict: PASS_WITH_NOTES (verificador opus)
commit: 5f6b601
date: 2026-08-10
---

# Summary: Comparador v2 (propuesta 4b) instalado vía dynamic workflow

Pipeline: premortem (3 revisores Opus, wf_5d4dbfb6-e5f) → decisiones locked + PLAN.md (Fable) → ejecución (Sonnet, wf_bb847f88-3a1) → verificación adversarial (Opus) → validación final (Fable).

## Qué se instaló

Rediseño del comparador de comunas (`/compare/`, `/es/comparar/`): las 2-3 tablas paralelas colapsan en un gráfico de una fila por familia delictiva con línea nacional punteada, año de referencia común (`sharedYear`), tarjetas headline con chip de banda `--s1…--s5`, resumen en lenguaje llano, bloque de homicidios separado, soporte de 3.ª comuna (`&c=`), tabla accesible oculta.

- Nuevo: `site/src/config/comparatorStrings.ts` (19 claves `cx_*` EN/ES + `SLOT_COLORS`)
- Reemplazados: `site/src/islands/ComparatorIsland.tsx` (863→~700 líneas), `site/src/pages/compare/index.astro`, `site/src/pages/es/comparar/index.astro` (+props `regionNames`, `low_population`)

## Premortem: 27 hallazgos, 15 fixes aplicados sobre el paquete

Claves: **CX-A1 BLOCKER** color de slot desalineado entre píldoras y gráfico (fix `colorFor(id)` por posición en `selected`); **CX-A3/C1** deep-links `?a=&b=` muertos por orden de efectos React (fix `initializedRef`); **CX-A2/C3** botón ordenar borraba comunas no cargadas; **CX-A4 + C4/A8/B2/B3** rotulado de año incoherente en modo años-mixtos y `national.json` caído; más rank direccional+CEAD, enlace metodología repuesto, etiqueta única "Tasa nacional", fuente CEAD en caption/nota, targets 44px, fallback hex para oklch, reintento tras fetch fallido, title baja población, URL no destructiva (conserva utm_*).

Rechazado a conciencia: CX-C9 (reformular `cmp_homicide_no_data` exigiría tocar `i18n.ts`, fuera de alcance del paquete).

## Gates

`npm run check` 0 errores · `npm test` 82/82 · `npm run build` verde · `npm run validate` 16/16 (re-verificado independientemente por el verificador Opus). Commit atómico `5f6b601` toca exactamente los 4 archivos; `[pair].astro`, `i18n.ts`, `data.ts`, `global.css` intactos.

## Deuda conocida (LOW, sin acción)

- V-02: con `national.json` caído, span de año vacío y columna nacional de la sr-table en guiones (cosmético).
- V-03: `cmp_avg_column` sigue pasándose como prop desde ambas páginas pero ya no se consume (prop muerta; útil si se revierte CX-A9).
- CX-C9: `cmp_homicide_no_data` dice "Sin casos reportados" ante dato ausente (paridad con conducta previa; requiere edición futura de `i18n.ts`).
