# Diagnóstico 360 de presentación — ischilesafe.com (producción)

**Fecha:** 2026-07-02 · **Método:** revisión E2E con BrowserOS sobre prod (desktop ~772px real + full-page 1295px, móvil emulado en iframe 375×812). Evidencia en `C:\Users\Carlo\bos-shots\`.
**Alcance:** Home EN/ES, /map/ (+?cut=), /commune/nunoa/ EN+ES, /rankings/, /compare/ (flujo completo), /news/, /methodology/, /is-santiago-safe/, /region/metropolitana/, 404, robots/sitemap, SEO técnico, a11y, performance.

---

## P0 — Críticos (arreglar antes de cualquier pulido)

### P0-1. Soft-404: toda URL inexistente sirve el HOME con status 200
- `GET /404-test-nonexistent/` → **200**, contenido = homepage completa, `canonical=https://ischilesafe.com/`, `robots=index,follow`.
- `GET /favicon.ico` → 200 `text/html` (mismo catch-all).
- Causa probable: fallback catch-all (`/* /index.html 200` en `_redirects` o equivalente en config de Pages).
- Impacto SEO: Google detecta soft-404s masivos, desperdicia crawl budget, puede degradar confianza del sitio entero; cualquier typo/link roto externo genera página indexable duplicada del home.
- Fix: `404.html` real con status 404 (Cloudflare Pages lo sirve automáticamente si existe y NO hay catch-all redirect). Verificar `public/_redirects`.

### P0-2. Overflow horizontal / breakpoint intermedio roto (~640–1080px)
- Con viewport 772px: `scrollWidth=1077` → ~305px de scroll horizontal.
- Culpables medidos: `nav.csm-nav` (no colapsa a hamburguesa hasta un breakpoint demasiado bajo), `.header-right/.lang-toggle`, y las dos `.lead-table-col` del home que quedan lado a lado (504px c/u) sin wrap.
- Síntoma visible: en capturas full-page el header se "rompe" — News / Crime type glossary / EN-ES quedan flotando fuera de la banda blanca del header en TODAS las páginas.
- En 375px el hamburger sí aparece → el problema es el rango tablet/laptop chico.
- Fix: media query intermedia — colapsar nav antes (≤1100px) y apilar las tablas del home (`flex-wrap` / grid 1 col ≤900px).

### P0-3. No hay favicon
- Ningún `<link rel="icon">` en el HTML y `/favicon.ico` no existe (ver P0-1). Pestañas del navegador y resultados de Google (que muestra favicons en móvil) salen con icono genérico. Fix barato de alto retorno de marca.

---

## P1 — Alto impacto en percepción/UX

### P1-1. Formato numérico inconsistente por locale (EN y ES mezclados)
- Panel del mapa (EN): **"~4.984"** — separador de miles español en UI inglesa; al lado, "Rate per 100,000 inhab." usa coma. El "~" además es ruido (no se explica).
- Página ES `/es/comuna/nunoa/`: héroe "4.984" y "Población: 266.906" (correcto ES) pero tabla "Similar Communes" muestra "4,991 / 5,017 / 4,918" (formato EN) en la misma página.
- `/compare/`: tasas sin separador de miles ("2871.5", "1059.9") y homicidio con 2 decimales ("8.69") vs 1 decimal del resto.
- Fix: helper único `formatNumber(value, locale)` (Intl.NumberFormat con `Astro.currentLocale`) usado por TODAS las islas y componentes estáticos; auditar MapIsland, CompareIsland, tablas Astro.

### P1-2. /compare/ — número principal sin etiqueta y estado vacío pobre
- Tarjetas muestran "39.0 Very High" y "8.4 Very Low" sin decir QUÉ es (es el Composite Crime Index, pero no lo dice; la tarjeta "Chile avg." tampoco muestra índice → asimetría).
- "Very High/Very Low" sin atribución al índice roza la restricción editorial (no calificar territorios); con la etiqueta "Composite Crime Index" + link a metodología queda cubierto.
- La selección NO se refleja en la URL → comparaciones no compartibles/bookmarkeables ni indexables. Fix: `?a=santiago&b=las-condes` + history.replaceState (las páginas pre-generadas `/compare/x-vs-y/` del commune page ya existen; la isla debería sincronizar).
- Estado vacío: solo un buscador y aire. Agregar chips de comparaciones populares (Santiago vs Las Condes, Providencia vs Ñuñoa...).
- Todos los trends muestran "→" — verificar que la isla realmente recibe datos de tendencia y no un default.

### P1-3. Mapa: encuadre inicial y jerarquía visual
- Zoom inicial muestra Chile como franja delgada a la IZQUIERDA con 60%+ del canvas ocupado por Argentina/océano. Fix: `fitBounds` al bbox de Chile continental + `maxBounds`, o center/zoom calibrado por aspect-ratio del contenedor.
- Leyenda "Crime Index" ocupa ~40% de la altura del mapa en móvil 375px. Fix: leyenda colapsable o compacta en móvil.
- Móvil: los pills "Index / By crime" se superponen al input de búsqueda (mismo row, z-index encima del placeholder). Fix: apilar en 2 filas ≤480px.
- Pins de incidentes casi del mismo naranjo que el nivel "High" del coroplético → se confunden figura/fondo. Fix: color distintivo (p.ej. morado/negro) o forma distinta + entrada en la leyenda cuando la capa está activa (hoy la leyenda no menciona los pins).
- Sin `?cut` inválido (`99999`) el fetch a `/data/cead/comunas/99999.json` igual se dispara (404 de red silencioso). El guard pre-fetch de la memoria v1.2 sigue pendiente. Menor.

### P1-4. Panel del mapa: años mezclados sin explicación
En un mismo panel conviven: Composite Index **(2024)**, Rate **(2025)**, evolución **(2005–2026)**, ranks de dos sistemas distintos (#158 composite vs #169 rate). El usuario promedio no distingue por qué hay dos rankings y tres años. Fix: agrupar visualmente por bloque con su año como badge y tooltip "por qué difieren los años"; ya existe el patrón "?" para tooltips.

### P1-5. "Is Santiago Safe" (página SEO prioritaria) sin un solo elemento visual
916 palabras de texto puro + 2 KPI. Cero mapas, cero tablas, cero charts, para la query de mayor volumen del sitio. Competidores muestran tablas comparativas. Fix (todo generable estático desde JSON existente): tabla "Reported rate por comuna del Gran Santiago" (top/bottom 10), mini-mapa estático o iframe del mapa filtrado a RM, sparkline de tendencia. Igual aplica a `/is-chile-safe/` y `/safest-cities-in-chile/`.

### P1-6. /news/: 129 items en lista plana, títulos sin semántica
- Sin paginación, filtros (comuna/región/tipo), ni agrupación por fecha; scroll de 129 tarjetas.
- Títulos de tarjetas NO son `h2/h3` (0 headings en toda la página) → semántica/SEO/a11y pobre.
- Tarjetas sin chip de tipo de delito ni comuna visible ("View commune" no dice cuál).
- Clasificación con ruido: "Collision leaves at least one dead… in Carahue" (accidente de tránsito) publicado como incidente delictivo → revisar prompt/filtro de clasificación del pipeline.
- Fuentes bien balanceadas (Cooperativa 54, LaTercera 38, BioBio 37) y frescura OK (17-jun → 2-jul).

---

## P2 — Mejoras de calidad/consistencia

### P2-1. Accesibilidad
- **~130 botones sin nombre accesible** en el mapa (markers de incidentes Leaflet) — lector de pantalla anuncia "button" x130. Fix: `aria-label` con título del incidente, o `aria-hidden` + lista alternativa.
- `outline: none` en foco de links (verificado computed style en home) y sin skip-link. Fix: `:focus-visible` visible global + skip-to-main.
- Resto OK: alt en imágenes, labels en inputs, landmarks (main/nav/header/footer), 1 h1/página, jerarquía de headings sana en páginas estáticas.

### P2-2. SEO técnico (lo que falta; la base está bien)
- Bien: canonical, hreflang en/es/x-default coherentes, sitemap-index + robots, JSON-LD (Dataset+Place+BreadcrumbList+ItemList en comuna, FAQPage en Santiago), OG/Twitter completos, og:image 1200×630, meta descriptions ≤160.
- Falta: JSON-LD `WebSite` (+SearchAction) y `Organization` en home; title del home corto (32 chars — cabe "crime map", "by commune 2025").
- **Riesgo de canibalización**: home H1 "Is Chile Safe? …" compite con `/is-chile-safe/` por la misma query. Decidir cuál targetea "is chile safe" (sugerencia: home) y re-enfocar la otra (p.ej. "Chile crime statistics 2025 — national overview") o consolidar con canonical.
- `/rankings/` es thin content y la sección "By region" NO enlaza a las 16 regiones (dice "usa el mapa") — agregar la lista de 16 links = interlinking + anchor text regional gratis.

### P2-3. Consistencia visual/copy menor
- Chip nav "Crime type glossary" envuelve en 3 líneas en el header (desktop ancho medio) — acortar a "Glossary"/"Glosario".
- Región: KPI "#13 of 16" sin dirección (¿13º más alto o más bajo?) — mismo patrón directional-label que ya se aplicó en comuna (memoria: rank #1 = más delitos). Añadir "1 = highest reported".
- Región: título de evolución dice "(2005–2025)" pero el chart incluye barra 2026 parcial.
- Compare homicidio "8.69 (48)" — unificar decimales; y "(1 cases)" singular/plural en algunos casos del panel ("11 cases" ok, revisar plural EN/ES con n=1).
- Placeholder "View the interactive map" en región es una caja gris con pin — se ve como mapa que falló en cargar; darle estilo de CTA/card intencional.

### P2-4. Performance (excelente — solo mantener)
- Home: 8 requests / ~12KB transfer / DCL 829ms. Map: 45 requests / 274KB (topo 95KB, MapIsland 72KB, react 58KB). Consola limpia en todas las páginas visitadas.
- Único punto: TTFB ~700ms observado (edge/cache CF, poco accionable). Nada bloqueante.
- Sugerencia AdSense-futuro: al insertar ads, medir CLS (hoy no hay ads; layout estable).

---

## Lo que está BIEN (no tocar en la fase de mejora)
1. Arquitectura de información de la página de comuna: hero KPI + percentil natural-language + evolución + categorías + sparklines + composite + ENUSC + comparable + interlinking. Es la mejor página del sitio.
2. Región: tabla completa con rank/trend + nota de volatilidad para comunas chicas (Alhué *).
3. Disciplina editorial: atribución CEAD consistente, "reported incidence" en todo el copy, disclaimer de cifra negra, "What this site does NOT say" en metodología (2.813 palabras, completa).
4. i18n: sin fugas de inglés en ES (verificado programáticamente en /es/comuna/), hreflang correcto, slugs localizados.
5. Búsqueda de comuna con autocomplete funciona en map y compare; ?cut= deep-linking funciona.
6. News pipeline vivo y balanceado entre 3 medios, actualizado el mismo día.

## Orden sugerido para la fase de mejora
1. P0-1 404 real + P0-3 favicon (½ día, máximo impacto SEO/branding).
2. P0-2 breakpoints header/home (1 día).
3. P1-1 formatNumber único por locale (½ día, toca MapIsland/Compare/tablas ES).
4. P1-3 mapa: fitBounds + leyenda móvil + colores pins (1 día).
5. P1-5 visuales en páginas editoriales (1–2 días, generación estática desde JSON existente).
6. P1-6 news: headings semánticos + filtros + fix clasificador (1 día front + pipeline).
7. P1-2 compare: etiqueta índice + URL sync + sugerencias (1 día).
8. P2 restantes en un barrido de polish.
