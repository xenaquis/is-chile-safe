---
id: 260810-tqr
slug: seccion-noticias-comuna
type: quick
status: complete
created: 2026-08-11
workflow: dynamic (sonnet executor, opus verifier, fable strategist)
---

# Quick: sección de noticias geolocalizadas en páginas de comuna

## Objetivo

Cada página de comuna (`/commune/{slug}/` y `/es/comuna/{slug}/`) muestra una sección estática con los incidentes de prensa geolocalizados en ESA comuna (desde `site/public/data/incidents/current.json`), con atribución de fuente, buen UX y respetando el design system existente. Solo linkear y presentar — cero lógica nueva de datos.

## Contexto clave (scouting ya hecho — NO re-explorar)

- **Datos**: `site/public/data/incidents/current.json` → `{ generated, incidents: [{ id, cut, lat, lng, title_es, title_en, date (YYYY-MM-DD), outlet, url, family, slug }] }`. 1550 incidentes, todos con `cut` (string, 4-5 dígitos). Distribución long-tail: Santiago 13101=129, muchas comunas con 0.
- **Páginas comuna**: `site/src/pages/commune/[slug].astro` (EN) y `site/src/pages/es/comuna/[slug].astro` (ES espejo). Estáticas, cero `client:*` (D-09). Secciones numeradas en comentarios HTML.
- **Página news existente**: `site/src/pages/news.astro` + `es/noticias.astro` — soporta `?q={texto}` (búsqueda por comuna vía `parseFilterParams`; matchea `data-commune-norm` con `norm()`). Ese es el destino del link "ver todas".
- **Design tokens**: `var(--xl) --md --sm --xs --line --radius --bg --card --ink --muted --primary --text-heading --text-body --text-label --weight-strong)`. Patrón de sección: `.section-heading` + `margin: var(--xl) 0`.
- **Paleta familias** (dot de color por tipo de delito) — copiar el bloque `[data-family='...'] { --fam: oklch(...) }` + `.fam-dot` de `news.astro` líneas ~732-755 (incluye ring para homicidios).
- **i18n**: `site/src/config/i18n.ts` — interfaz tipada + `EN_STRINGS` + `ES_STRINGS`. Agregar claves nuevas en los TRES lugares.

## Restricciones duras (violarlas = FAIL)

1. **NO usar la clase `news-card`** ni `news-month-section` en el componente nuevo. `site/scripts/validate/facets.mjs` (assertion 12) cuenta/inspecciona esos selectores. Prefijo propio: `cnews-`.
2. **Assertion 11**: todo `toLocaleDateString` con opción `month:` DEBE pasar `timeZone: 'UTC'`.
3. **Leer JSON vía `path.resolve(process.cwd(), 'public/data/incidents/current.json')`** — nunca `import.meta.url` (memoria: build path drift). Fallback `existsSync` → sin sección, build no crashea.
4. **Performance de build**: ~340 páginas comuna × 2 idiomas. Parsear current.json UNA vez a nivel módulo (memo `Map<cut, Incident[]>`), no por página.
5. **Cero JS cliente** en el componente (D-09 de la página comuna). Nada de `{expr}` dentro de `<script>` (no habrá script).
6. **Tono legal**: nunca "peligroso/seguro"; atribuir outlet; cada incidente linkea su fuente (`site/scripts/validate/forbidden-language.mjs` y `commune.mjs` escanean páginas comuna).
7. **`safeUrl()`**: solo http/https, si no `#` (copiar patrón de news.astro líneas 156-166).
8. **Links externos**: `target="_blank" rel="noopener noreferrer"`.
9. Título por locale: EN→`title_en`, ES→`title_es`.

## Diseño (decidido — no reabrir)

**Nuevo componente**: `site/src/components/CommuneNewsSection.astro`
- Props: `cut: string`, `communeName: string`, `locale: 'en' | 'es'`.
- Frontmatter: loader módulo-scope memoizado (Map cut→incidents ordenados desc por date). Selecciona top **6** más recientes para el cut.
- **Si 0 incidentes: no renderiza nada** (return null / render condicional). Sin estado vacío ruidoso.
- Markup (todo estático):
  - `<section class="cnews-section" aria-label={...}>` con `<h2 class="section-heading">` — heading i18n.
  - Sub-línea intro corta (i18n) explicando: incidentes reportados por prensa, geolocalizados en esta comuna, cada uno linkea su fuente.
  - Lista `<ul class="cnews-list">` — cada `<li class="cnews-item" data-family={family}>`:
    - `.fam-dot` coloreado por familia (title = label familia; + `<span class="cnews-sr">` con label para lectores de pantalla).
    - `<a href={safeUrl(url)} target="_blank" rel="noopener noreferrer">` título por locale.
    - `<span class="cnews-meta">` outlet · `<time datetime={date}>` fecha corta (formato `{ month: 'short', day: 'numeric', timeZone: 'UTC' }`, locale 'en-US'/'es-CL'; agregar `year: 'numeric'` si el año ≠ año del incidente más reciente — simplificación aceptada: incluir siempre día+mes, y año solo si difiere del año actual del dato `generated`).
  - Footer: link "ver todos" → EN: `/news/?q={encodeURIComponent(communeName)}` / ES: `/es/noticias/?q={...}` — estilo link primario simple (no botón CTA, para no competir con map-spoke).
  - Caveat corto (i18n, clase `cnews-caveat` estilo `.enusc-caveat`: borde izq primary, texto muted, 13px): fuente = medios de prensa, clasificación automática, no estadística oficial.
- Estilos scoped en el componente, solo tokens existentes. Lista densa: filas con `border-bottom: 1px solid var(--line)`, padding vertical `var(--xs)`/`--sm`, título `var(--text-body)` weight strong, meta `var(--text-label)` muted. Responsive: ya es una columna, nada especial.

**i18n — claves nuevas** (interfaz + EN + ES):
- `commune_news_heading`: 'Recent Incidents in the News' / 'Incidentes Recientes en la Prensa'
- `commune_news_intro`: 'Incidents reported by Chilean news media and geolocated in {name}. Each entry links to its source article.' / 'Incidentes reportados por medios de prensa chilenos y geolocalizados en {name}. Cada entrada enlaza a su artículo original.'
- `commune_news_see_all`: 'See all news incidents for {name} →' / 'Ver todos los incidentes de prensa de {name} →'
- `commune_news_caveat`: 'Automatically classified from press coverage; not official statistics. Sources are always cited.' / 'Clasificación automática desde cobertura de prensa; no es estadística oficial. Las fuentes siempre se citan.'
- `commune_news_aria`: 'Recent incidents reported in the news' / 'Incidentes recientes reportados en la prensa'

**Integración** — en AMBAS páginas comuna, insertar `<CommuneNewsSection cut={data.cut} communeName={data.name} locale=... />` como sección nueva **después del bloque ENUSC (6c) y antes de ComparableCommune (7)**, comentario `<!-- 6d. Recent news incidents (quick-260810-tqr) -->`. Nota: EN usa `data.cut`; verificar que la página ES expone el mismo dato (espejo).

## Verificación (obligatoria antes de commit)

Encadenar en UN comando (OneDrive desync):
```
cd site; npm run build; if ($?) { node scripts/validate/facets.mjs; node scripts/validate/commune.mjs; node scripts/validate/forbidden-language.mjs }
```
(ajustar a los nombres reales de scripts npm; si `all.mjs` es rápido, correrlo)
- Comprobar en dist: `dist/commune/santiago/index.html` contiene `cnews-section` con ≥1 item y links con outlet; una comuna sin incidentes NO contiene `cnews-section`.
- `npx astro check` no debe sumar errores nuevos (hay 8 preexistentes conocidos).

## Commits

Atómicos, formato repo: `feat(commune): add geolocated news incidents section (quick-260810-tqr)` + co-author Claude.
