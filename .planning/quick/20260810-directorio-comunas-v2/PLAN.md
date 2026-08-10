---
quick_id: 260810-j51
slug: directorio-comunas-v2
date: 2026-08-10
---

# Quick — Directorio de comunas v2 (propuesta 1b)

Instalar el rediseño del directorio de comunas entregado en
`C:\Users\Carlo\Downloads\Optimizar diseño de comunas\install` (ver `INSTALL.md`).

## Tareas

1. Copiar los archivos nuevos y reemplazar las dos páginas índice:
   - nuevo `site/src/components/CommuneDirectory.astro`
   - nuevo `site/src/config/directoryStrings.ts`
   - nuevo `scripts/build-comuna-centroids.mjs`
   - reemplazo `site/src/pages/communes/index.astro` (507 → 21 líneas)
   - reemplazo `site/src/pages/es/comunas/index.astro` (503 → 21 líneas)
2. Generar `site/src/data/comuna-centroids.json` (habilita "Cerca de mí").
3. Alinear la dirección del ranking con la convención del sitio.
4. Gates: `astro check`, `npm run build`, `npm run validate`, `npm test`,
   y el conteo de links de `INSTALL.md` §5 (346 por página, no 692).

## Decisión tomada durante la ejecución

El paquete definía `rank 1 = tasa más baja`. El validador `figure-registry`
(guard DOCS-01) lo rechaza: la convención del sitio (`national_rank`) es
**rank 1 = tasa más alta**. Se alineó el componente a la convención del sitio
en vez de relajar el guard.
</content>
</invoke>
