/**
 * EN/ES UI string map + crime-family slug translations.
 * Sober editorial tone per D-05 — see CONTEXT.md for the full list of forbidden terms.
 * Ported from ischilesafe.com/data.js I18N and extended with Phase 2 UI-SPEC additions.
 */

export interface I18nStrings {
  // Navigation
  nav_home: string;
  nav_map: string;
  nav_methodology: string;
  nav_menu_open: string;

  // Page h1 patterns (use {name} placeholder)
  page_commune_h1: string;
  page_region_h1: string;
  page_crime_h1: string;

  // Rate stat
  rate_label: string;
  rate_unit: string;

  // Rank labels
  national_rank_label: string;
  regional_rank_label: string;
  rank_of: string;

  // Rank percentile cards (260620-hrh)
  rank_pct_value: string;
  rank_national_label: string;
  rank_regional_label: string;
  rank_sublabel: string;

  // Trend
  trend_up: string;
  trend_down: string;
  trend_stable: string;
  trend_label: string;

  // Sparkline
  sparkline_heading: string;

  // Year selector + longitudinal charts (260620-hrh)
  year_selector_label: string;
  charts_heading: string;
  chart_partial_note: string;

  // Partial year badge
  partial_year_badge: string;

  // vs-national / vs-regional callouts
  vs_national_above: string;
  vs_national_below: string;
  vs_national_near: string;
  vs_regional_above: string;
  vs_regional_below: string;
  vs_regional_near: string;

  // Family breakdown heading
  family_breakdown_heading: string;

  // Comparable commune headings
  comparable_same_region_heading: string;
  comparable_national_fallback_heading: string;

  // Map CTA label (TD-02 — replaced stale "coming soon" placeholder)
  map_cta_label: string;

  // Methodology caveat
  methodology_caveat_link: string;
  methodology_caveat_text: string;

  // Low-population caveat
  low_population_caveat: string;

  // Incidence level labels (matches --s1..--s5)
  level_1: string;
  level_2: string;
  level_3: string;
  level_4: string;
  level_5: string;

  // Footer legal links (EDIT-04, D-13)
  footer_privacy: string;
  footer_terms: string;
  footer_about: string;
  footer_contact: string;

  // Cookie consent banner (D-11)
  cookie_banner_text: string;
  cookie_banner_accept: string;
  cookie_banner_reject: string;

  // Data callout source prefix
  data_callout_source_prefix: string;

  // Phase 9 — rate tooltip
  rate_tooltip_title: string;
  rate_tooltip_body: string;

  // Phase 9 — glossary link
  glossary_link: string;

  // Phase 9 — comparison multiplier
  comparison_national: string;

  // Phase 9 — legend qualitative labels (5 levels)
  legend_qual_1: string;
  legend_qual_2: string;
  legend_qual_3: string;
  legend_qual_4: string;
  legend_qual_5: string;

  // Phase 9 — legend footnote
  legend_per_100k_note: string;

  // Phase 11 — directory nav + page strings
  nav_communes: string;

  // Phase 12 — rankings nav + footer spine labels
  nav_rankings: string;
  footer_spine_map: string;
  footer_spine_communes: string;
  footer_spine_rankings: string;
  footer_spine_guide: string;
  dir_title: string;
  dir_lead: string;
  dir_search_placeholder: string;
  dir_view_az: string;
  dir_view_region: string;
  dir_count: string;
  dir_lowpop_tag: string;
  dir_empty: string;

  // Phase 28 — news faceting UI (NEWSUI-01..07)
  news_filter_heading: string;
  news_filter_window_label: string;
  news_window_latest: string;
  news_window_7d_label: string;
  news_window_30d_label: string;
  news_window_all: string;
  news_filter_region_label: string;
  news_filter_family_label: string;
  news_search_comuna_label: string;
  news_search_comuna_placeholder: string;
  news_result_count: string;
  news_clear_filters: string;
  news_empty_heading: string;
  news_empty_body: string;
  news_cluster_source_count: string;

  // Quick 260616-lu4 — ranking table controls
  sort_label: string;
  sort_ascending: string;
  sort_descending: string;
  year_select_label: string;
  year_select_aria: string;

  // Phase 16-04 — news nav
  nav_news: string;

  // Phase 19-06 — BIL-04 commune section headings
  map_spoke_heading: string;
  map_spoke_cta: string;
  similar_communes_heading: string;
  similar_communes_intro: string;
  crime_type_heading: string;

  // Phase 19-06 — BIL-04 table headers
  th_rank: string;
  th_commune: string;
  th_region: string;
  th_rate_per_100k: string;
  th_trend: string;

  // Phase 19-06 — BIL-04 low-pop footnote
  low_pop_footnote: string;

  // Phase 18-04 — composite index bands + rank + caveat
  ci_band_1: string;
  ci_band_2: string;
  ci_band_3: string;
  ci_band_4: string;
  ci_band_5: string;
  ci_rank_national: string;
  ci_rank_regional: string;
  ci_caveat_text: string;
  ci_section_heading: string;

  // Phase 23 — ENUSC SAE VHDV communal victimization module
  enusc_section_heading: string;
  enusc_section_aria: string;
  enusc_ci_label: string;
  enusc_caveat_text: string;
  enusc_no_estimate_text: string;
  enusc_no_estimate_aria: string;

  // Phase 21 — Commune Comparator
  nav_compare: string;
  cmp_page_h1: string;
  cmp_page_lead: string;
  cmp_input_placeholder: string;
  cmp_empty_heading: string;
  cmp_add_prompt: string;
  cmp_no_match: string;
  cmp_max_reached: string;
  cmp_avg_column: string;
  cmp_remove_aria: string;
  cmp_data_error: string;
  cmp_homicide_row: string;
  cmp_homicide_no_data: string;
  cmp_cross_links_heading: string;
  // Phase 25 — Compare island enrichments
  cmp_composite_label: string;
  cmp_what_is_this: string;
  cmp_trend_unavailable: string;
  cmp_empty_body: string;
  cmp_chips_label: string;
  cmp_case_singular: string;
  cmp_case_plural: string;
  avs_b_h1_pattern: string;

  // Phase 30 — map control-shell entry points
  map_entry_year: string;
  map_entry_family: string;
  map_entry_mode: string;
  map_news_toggle_long: string;
  map_news_toggle_short: string;
  map_filters_fab: string;
}

export const EN_STRINGS: I18nStrings = {
  // Navigation
  nav_home: 'Home',
  nav_map: 'Map',
  nav_methodology: 'Methodology',
  nav_menu_open: 'Open navigation menu',

  // Page h1 patterns
  page_commune_h1: '{name} — Reported Crime Data',
  page_region_h1: '{name} Region — Crime Incidence Overview',
  page_crime_h1: '{name} — National Crime Incidence',

  // Rate stat
  rate_label: 'Rate per 100,000 inhabitants ({year})',
  rate_unit: 'per 100k inh.',

  // Rank labels
  national_rank_label: 'National rank',
  regional_rank_label: 'Regional rank',
  rank_of: 'of',

  // Rank percentile cards (260620-hrh)
  rank_pct_value: 'More reported crime than {pct}%',
  rank_national_label: "of Chile's communes",
  rank_regional_label: 'of communes in {region}',
  rank_sublabel: 'CEAD {year} · #{rank} of {total} · 1 = most reported incidence',

  // Trend
  trend_up: 'Rising',
  trend_down: 'Declining',
  trend_stable: 'Stable',
  trend_label: 'Trend',

  // Sparkline
  sparkline_heading: 'Annual evolution (2005–present)',

  // Year selector + longitudinal charts (260620-hrh)
  year_selector_label: 'View data for year:',
  charts_heading: 'Crime evolution by category (2005–present)',
  chart_partial_note: 'Faded points indicate partial-year data.',

  // Partial year badge
  partial_year_badge: 'Partial year ({year})',

  // vs-national / vs-regional callouts
  vs_national_above: '{pct}% above national average',
  vs_national_below: '{pct}% below national average',
  vs_national_near: 'Near the national average',
  vs_regional_above: '{pct}% above regional average',
  vs_regional_below: '{pct}% below regional average',
  vs_regional_near: 'Near the regional average',

  // Family breakdown heading
  family_breakdown_heading: 'Reported incidence by crime category ({year})',

  // Comparable commune headings
  comparable_same_region_heading: 'Comparable commune (same region)',
  comparable_national_fallback_heading: 'Comparable commune (national)',

  // Map CTA label (TD-02 — replaced stale "coming soon" placeholder)
  map_cta_label: 'View the interactive map',

  // Methodology caveat
  methodology_caveat_link: 'Methodology',
  methodology_caveat_text:
    'Figures represent reported crimes per 100,000 inhabitants. Under-reporting varies by crime type. Source: CEAD — Centro de Estudios y Análisis del Delito (official Chilean police statistics). See our {link} for details.',

  // Low-population caveat
  low_population_caveat:
    'This commune has a small resident population. Rates per 100,000 inhabitants can show high statistical volatility even with small changes in absolute counts. Interpret trends with caution and compare with regional context rather than national rankings.',

  // Incidence level labels
  level_1: 'Low incidence',
  level_2: 'Medium-low incidence',
  level_3: 'Medium incidence',
  level_4: 'Medium-high incidence',
  level_5: 'High incidence',

  // Footer legal links (EDIT-04, D-13)
  footer_privacy: 'Privacy Policy',
  footer_terms: 'Terms of Use',
  footer_about: 'About',
  footer_contact: 'Contact',

  // Cookie consent banner (D-11)
  cookie_banner_text: 'We use cookies to serve ads and analyze traffic. See our',
  cookie_banner_accept: 'Accept',
  cookie_banner_reject: 'Reject',

  // Data callout source prefix
  data_callout_source_prefix: 'Source: CEAD',

  // Phase 9 — rate tooltip
  rate_tooltip_title: 'Rate per 100,000 inhabitants',
  rate_tooltip_body: 'This figure counts police-reported incidents for every 100,000 people living in the area, allowing fair comparison between places of very different population sizes. Source: CEAD official police statistics.',

  // Phase 9 — glossary link
  glossary_link: 'Glossary',

  // Phase 9 — comparison multiplier
  comparison_national: '{multiplier}× the national average',

  // Phase 9 — legend qualitative labels
  legend_qual_1: 'Very low',
  legend_qual_2: 'Low',
  legend_qual_3: 'Medium',
  legend_qual_4: 'High',
  legend_qual_5: 'Very high',

  // Phase 9 — legend footnote
  legend_per_100k_note: 'Reported rate per 100,000 inhabitants',

  // Phase 11 — directory nav + page strings
  nav_communes: 'Communes',

  // Phase 12 — rankings nav + footer spine labels
  nav_rankings: 'Rankings',
  footer_spine_map: 'Map',
  footer_spine_communes: 'Communes',
  footer_spine_rankings: 'Rankings',
  footer_spine_guide: 'Is Chile Safe?',
  dir_title: 'All 346 communes of Chile',
  dir_lead: 'Every commune with CEAD reported-incidence data has a page. Search by name or browse all 16 regions.',
  dir_search_placeholder: "Filter by name… (e.g. 'la ', 'puerto', 'vina')",
  dir_view_az: 'A–Z',
  dir_view_region: 'By region',
  dir_count: '{n} of 346 communes',
  dir_lowpop_tag: 'low pop.',
  dir_empty: 'No results for "{q}".',

  // Phase 28 — news faceting UI (NEWSUI-01..07)
  news_filter_heading: 'Filter news',
  news_filter_window_label: 'Time',
  news_window_latest: 'Latest data: {date}',
  news_window_7d_label: 'Last 7 days',
  news_window_30d_label: 'Last 30 days',
  news_window_all: 'All dates',
  news_filter_region_label: 'Region',
  news_filter_family_label: 'Crime type',
  news_search_comuna_label: 'Search by comuna',
  news_search_comuna_placeholder: "Filter by comuna name… (e.g. 'la ', 'puerto', 'vina')",
  news_result_count: '{n} incidents shown',
  news_clear_filters: 'Clear filters',
  news_empty_heading: 'No incidents match these filters',
  news_empty_body: 'Try a different time window, region, or crime type, or clear all filters to see every reported incident.',
  news_cluster_source_count: '{n} sources',

  // Quick 260616-lu4 — ranking table controls
  sort_label: 'Sort by {column}',
  sort_ascending: 'ascending',
  sort_descending: 'descending',
  year_select_label: 'Year',
  year_select_aria: 'Select data year',

  // Phase 16-04 — news nav
  nav_news: 'News',

  // Phase 19-06 — BIL-04 commune section headings
  map_spoke_heading: 'View on Map',
  map_spoke_cta: 'See {name} on the interactive Chile crime map →',
  similar_communes_heading: 'Similar Communes in This Region',
  similar_communes_intro: 'Communes in {region} with similar reported CEAD incidence rates:',
  crime_type_heading: 'Rankings by Crime Type',

  // Phase 19-06 — BIL-04 table headers
  th_rank: 'Rank',
  th_commune: 'Commune',
  th_region: 'Region',
  th_rate_per_100k: 'Rate per 100k',
  th_trend: 'Trend',

  // Phase 19-06 — BIL-04 low-pop footnote
  low_pop_footnote: '* This commune has a small resident population. Rates per 100,000 inhabitants can show high statistical volatility. Interpret with caution.',

  // Phase 18-04 — composite index bands + rank + caveat
  ci_band_1: 'Very Low',
  ci_band_2: 'Low',
  ci_band_3: 'Moderate',
  ci_band_4: 'High',
  ci_band_5: 'Very High',
  ci_rank_national: '#{rank} of {total} nationally',
  ci_rank_regional: '#{rank} in {region}',
  ci_caveat_text: 'Composite of reported crimes (CEAD/SPD), adjusted for SII economic activity. Does not reflect unreported crime. Reference year: 2024.',
  ci_section_heading: 'Composite Crime Index (2024)',

  // Phase 23 — ENUSC SAE VHDV communal victimization module
  enusc_section_heading: "Household Victimization (ENUSC 2024)",
  enusc_section_aria: "ENUSC household victimization estimate",
  enusc_ci_label: "95% confidence interval",
  enusc_caveat_text:
    "INE experimental estimate (SAE-modeled). Proportion of households reporting at least one violent crime. Covers 136 of 346 comunas. Distinct from CEAD reported-crime index — measures victimization survey responses, not police denuncias. Source: INE Estadísticas Experimentales, Seguridad Ciudadana.",
  enusc_no_estimate_text:
    "No INE ENUSC victimization estimate available for this comuna (SAE model covers 136 of 346 comunas).",
  enusc_no_estimate_aria: "ENUSC no estimate available",

  // Phase 21 — Commune Comparator
  nav_compare: 'Compare',
  cmp_page_h1: 'Compare Chile Communes — Reported Crime Data',
  cmp_page_lead: 'Select 2 or 3 communes to view reported crime statistics side by side. Source: CEAD official statistics.',
  cmp_input_placeholder: 'Search commune name…',
  cmp_empty_heading: 'Select 2 or 3 communes to compare',
  cmp_add_prompt: 'Add another commune to compare',
  cmp_no_match: 'No commune found — try removing accents',
  cmp_max_reached: 'Maximum 3 communes reached',
  cmp_avg_column: 'Chile avg.',
  cmp_remove_aria: 'Remove {name}',
  cmp_data_error: 'Could not load data for {name}. Try refreshing.',
  cmp_homicide_row: 'Homicide (per 100k, {year})',
  cmp_homicide_no_data: 'No reported cases — CEAD {year}',
  cmp_cross_links_heading: 'Compare with other communes',
  // Phase 25 — Compare island enrichments
  cmp_composite_label: 'Composite Crime Index',
  cmp_what_is_this: '(what is this?)',
  cmp_trend_unavailable: 'Trend data unavailable for this commune.',
  cmp_empty_body: 'Select 2 or 3 communes to view a side-by-side comparison of reported crime rates.',
  cmp_chips_label: 'Popular comparisons:',
  cmp_case_singular: 'case',
  cmp_case_plural: 'cases',
  avs_b_h1_pattern: '{a} vs {b} — Reported Crime Comparison',

  // Phase 30 — map control-shell entry points
  map_entry_year: 'Year',
  map_entry_family: 'Crime type',
  map_entry_mode: 'Map mode',
  map_news_toggle_long: 'Recent incidents',
  map_news_toggle_short: 'News',
  map_filters_fab: 'Filters',
};

export const ES_STRINGS: I18nStrings = {
  // Navegación
  nav_home: 'Inicio',
  nav_map: 'Mapa',
  nav_methodology: 'Metodología',
  nav_menu_open: 'Abrir menú de navegación',

  // Patrones de h1
  page_commune_h1: '{name} — Datos de Incidencia Delictiva Reportada',
  // NOTE: do NOT wire this static template directly — "Región de {name}" is
  // ungrammatical for Metropolitana/Maule/Biobío (F-006). Build the region
  // phrase with regionNameEs() and append the suffix instead.
  page_region_h1: 'Región de {name} — Panorama de Incidencia Delictiva',
  page_crime_h1: '{name} — Incidencia Nacional',

  // Estadística de tasa
  rate_label: 'Tasa por 100.000 hab. ({year})',
  rate_unit: 'por 100k hab.',

  // Etiquetas de ranking
  national_rank_label: 'Ranking nacional',
  regional_rank_label: 'Ranking regional',
  rank_of: 'de',

  // Tarjetas de percentil de ranking (260620-hrh)
  rank_pct_value: 'Más delitos reportados que el {pct}%',
  rank_national_label: 'de las comunas de Chile',
  rank_regional_label: 'de las comunas de {region}',
  rank_sublabel: 'CEAD {year} · #{rank} de {total} · 1 = mayor incidencia reportada',

  // Tendencia
  trend_up: 'Al alza',
  trend_down: 'A la baja',
  trend_stable: 'Estable',
  trend_label: 'Tendencia',

  // Sparkline
  sparkline_heading: 'Evolución anual (2005–presente)',

  // Selector de año + gráficos longitudinales (260620-hrh)
  year_selector_label: 'Ver datos del año:',
  charts_heading: 'Evolución de delitos por categoría (2005–presente)',
  chart_partial_note: 'Los puntos atenuados indican datos de año parcial.',

  // Distintivo año parcial
  partial_year_badge: 'Año parcial ({year})',

  // Comparaciones vs. nacional / regional
  vs_national_above: '{pct}% sobre el promedio nacional',
  vs_national_below: '{pct}% bajo el promedio nacional',
  vs_national_near: 'Cercano al promedio nacional',
  vs_regional_above: '{pct}% sobre el promedio regional',
  vs_regional_below: '{pct}% bajo el promedio regional',
  vs_regional_near: 'Cercano al promedio regional',

  // Encabezado desglose por familia
  family_breakdown_heading: 'Incidencia reportada por categoría delictiva ({year})',

  // Encabezados de comuna comparable
  comparable_same_region_heading: 'Comuna comparable (misma región)',
  comparable_national_fallback_heading: 'Comuna comparable (a nivel nacional)',

  // Etiqueta CTA del mapa (TD-02 — reemplaza marcador obsoleto "próximamente")
  map_cta_label: 'Ver el mapa interactivo',

  // Nota metodológica
  methodology_caveat_link: 'Metodología',
  methodology_caveat_text:
    'Las cifras representan delitos reportados por 100.000 habitantes. La sub-notificación varía según el tipo de delito. Fuente: CEAD — Centro de Estudios y Análisis del Delito (estadísticas policiales oficiales de Chile). Ver {link} para más detalles.',

  // Advertencia de baja población
  low_population_caveat:
    'Esta comuna tiene una pequeña población residente. Las tasas por 100.000 habitantes pueden presentar alta volatilidad estadística incluso ante pequeños cambios en los valores absolutos. Interprete las tendencias con cautela y compare con el contexto regional más que con los rankings nacionales.',

  // Etiquetas de nivel de incidencia
  level_1: 'Incidencia baja',
  level_2: 'Incidencia media-baja',
  level_3: 'Incidencia media',
  level_4: 'Incidencia media-alta',
  level_5: 'Incidencia alta',

  // Enlaces legales del pie de página (EDIT-04, D-13)
  footer_privacy: 'Política de Privacidad',
  footer_terms: 'Términos de Uso',
  footer_about: 'Acerca de',
  footer_contact: 'Contacto',

  // Banner de consentimiento de cookies (D-11)
  cookie_banner_text: 'Usamos cookies para mostrar anuncios y analizar el tráfico. Ver nuestra',
  cookie_banner_accept: 'Aceptar',
  cookie_banner_reject: 'Rechazar',

  // Prefijo de fuente para callout de datos
  data_callout_source_prefix: 'Fuente: CEAD',

  // Fase 9 — tooltip de tasa
  rate_tooltip_title: 'Tasa por 100.000 habitantes',
  rate_tooltip_body: 'Esta cifra cuenta los incidentes reportados a la policía por cada 100.000 personas residentes en la zona, permitiendo comparar lugares de tamaños muy distintos en igualdad de condiciones. Fuente: estadísticas policiales oficiales CEAD.',

  // Fase 9 — enlace al glosario
  glossary_link: 'Glosario',

  // Fase 9 — multiplicador de comparación
  comparison_national: '{multiplier}× el promedio nacional',

  // Fase 9 — etiquetas cualitativas de la leyenda
  legend_qual_1: 'Muy baja',
  legend_qual_2: 'Baja',
  legend_qual_3: 'Media',
  legend_qual_4: 'Alta',
  legend_qual_5: 'Muy alta',

  // Fase 9 — nota al pie de leyenda
  legend_per_100k_note: 'Tasa reportada por 100.000 habitantes',

  // Fase 11 — directorio nav + strings de página
  nav_communes: 'Comunas',

  // Fase 12 — rankings nav + etiquetas del footer spine
  nav_rankings: 'Rankings',
  footer_spine_map: 'Mapa',
  footer_spine_communes: 'Comunas',
  footer_spine_rankings: 'Rankings',
  footer_spine_guide: '¿Es seguro Chile?',
  dir_title: 'Las 346 comunas de Chile',
  dir_lead: 'Toda comuna con datos de incidencia reportada CEAD tiene su página. Busca por nombre o explora las 16 regiones.',
  dir_search_placeholder: "Filtra por nombre… (ej. 'la ', 'puerto', 'viña')",
  dir_view_az: 'A–Z',
  dir_view_region: 'Por región',
  dir_count: '{n} de 346 comunas',
  dir_lowpop_tag: 'baja pob.',
  dir_empty: 'Sin resultados para "{q}".',

  // Fase 28 — UI de facetas de noticias (NEWSUI-01..07)
  news_filter_heading: 'Filtrar noticias',
  news_filter_window_label: 'Fecha',
  news_window_latest: 'Últimos datos: {date}',
  news_window_7d_label: 'Últimos 7 días',
  news_window_30d_label: 'Últimos 30 días',
  news_window_all: 'Todas las fechas',
  news_filter_region_label: 'Región',
  news_filter_family_label: 'Tipo de delito',
  news_search_comuna_label: 'Buscar por comuna',
  news_search_comuna_placeholder: "Filtra por comuna… (ej. 'la ', 'puerto', 'viña')",
  news_result_count: '{n} incidentes mostrados',
  news_clear_filters: 'Limpiar filtros',
  news_empty_heading: 'Ningún incidente coincide con estos filtros',
  news_empty_body: 'Prueba otro período, región o tipo de delito, o limpia los filtros para ver todos los incidentes reportados.',
  news_cluster_source_count: '{n} fuentes',

  // Quick 260616-lu4 — ranking table controls
  sort_label: 'Ordenar por {column}',
  sort_ascending: 'ascendente',
  sort_descending: 'descendente',
  year_select_label: 'Año',
  year_select_aria: 'Seleccionar año de datos',

  // Phase 16-04 — news nav
  nav_news: 'Noticias',

  // Phase 19-06 — BIL-04 commune section headings
  map_spoke_heading: 'Ver en el Mapa',
  map_spoke_cta: 'Ver {name} en el mapa interactivo de Chile →',
  similar_communes_heading: 'Comunas Similares en Esta Región',
  similar_communes_intro: 'Comunas de {region} con tasas de incidencia CEAD similares:',
  crime_type_heading: 'Rankings por Tipo de Delito',

  // Phase 19-06 — BIL-04 table headers
  th_rank: 'Posición',
  th_commune: 'Comuna',
  th_region: 'Región',
  th_rate_per_100k: 'Tasa por 100k',
  th_trend: 'Tendencia',

  // Phase 19-06 — BIL-04 low-pop footnote
  low_pop_footnote: '* Esta comuna tiene una pequeña población residente. Las tasas por 100.000 habitantes pueden presentar alta volatilidad estadística. Interprete con cautela.',

  // Phase 18-04 — composite index bands + rank + caveat
  ci_band_1: 'Muy Bajo',
  ci_band_2: 'Bajo',
  ci_band_3: 'Moderado',
  ci_band_4: 'Alto',
  ci_band_5: 'Muy Alto',
  ci_rank_national: '#{rank} de {total} a nivel nacional',
  ci_rank_regional: '#{rank} en {region}',
  ci_caveat_text: 'Compuesto de delitos reportados al sistema policial (CEAD/SPD), ajustado por actividad económica SII. No refleja delitos no denunciados. Datos de referencia: 2024.',
  ci_section_heading: 'Índice Compuesto de Delincuencia (2024)',

  // Phase 23 — ENUSC SAE VHDV communal victimization module
  enusc_section_heading: "Victimización en Hogares (ENUSC 2024)",
  enusc_section_aria: "Estimación de victimización en hogares ENUSC",
  enusc_ci_label: "Intervalo de confianza al 95%",
  enusc_caveat_text:
    "Estimación experimental de INE (modelo SAE). Proporción de hogares que reportaron al menos un delito violento. Cubre 136 de 346 comunas. Distinto del índice CEAD de delitos reportados — mide respuestas de encuesta de victimización, no denuncias policiales. Fuente: INE Estadísticas Experimentales, Seguridad Ciudadana.",
  enusc_no_estimate_text:
    "Sin estimación de victimización ENUSC disponible para esta comuna (el modelo SAE cubre 136 de 346 comunas).",
  enusc_no_estimate_aria: "Sin estimación ENUSC disponible",

  // Phase 21 — Commune Comparator
  nav_compare: 'Comparar',
  cmp_page_h1: 'Comparar Comunas de Chile — Incidencia Delictiva Reportada',
  cmp_page_lead: 'Selecciona 2 o 3 comunas para ver estadísticas de incidencia delictiva en paralelo. Fuente: estadísticas oficiales CEAD.',
  cmp_input_placeholder: 'Buscar nombre de comuna…',
  cmp_empty_heading: 'Selecciona 2 o 3 comunas para comparar',
  cmp_add_prompt: 'Agrega otra comuna para comparar',
  cmp_no_match: 'No se encontró la comuna — prueba sin tildes',
  cmp_max_reached: 'Máximo 3 comunas alcanzado',
  cmp_avg_column: 'Prom. Chile',
  cmp_remove_aria: 'Quitar {name}',
  cmp_data_error: 'No se pudieron cargar los datos de {name}. Intenta recargar.',
  cmp_homicide_row: 'Homicidios (por 100k, {year})',
  cmp_homicide_no_data: 'Sin casos reportados — CEAD {year}',
  cmp_cross_links_heading: 'Comparar con otras comunas',
  // Phase 25 — Compare island enrichments
  cmp_composite_label: 'Índice Compuesto de Criminalidad',
  cmp_what_is_this: '(¿qué es esto?)',
  cmp_trend_unavailable: 'Datos de tendencia no disponibles para esta comuna.',
  cmp_empty_body: 'Selecciona 2 o 3 comunas para ver una comparación lado a lado de las tasas de incidencia delictiva reportadas.',
  cmp_chips_label: 'Comparaciones populares:',
  cmp_case_singular: 'caso',
  cmp_case_plural: 'casos',
  avs_b_h1_pattern: '{a} vs {b} — Comparación de Incidencia Delictiva',

  // Phase 30 — map control-shell entry points
  map_entry_year: 'Año',
  map_entry_family: 'Tipo de delito',
  map_entry_mode: 'Modo',
  map_news_toggle_long: 'Noticias recientes',
  map_news_toggle_short: 'Noticias',
  map_filters_fab: 'Filtros',
};

// D-17: Crime-family URL slug translations
// family key (data) -> { en: EN URL slug, es: ES URL slug }
export interface FamilySlugPair {
  en: string;
  es: string;
}

export const FAMILY_SLUGS: Record<string, FamilySlugPair> = {
  vida: { en: 'homicide', es: 'homicidios' },
  robos_violentos: { en: 'violent-robbery', es: 'robos-violentos' },
  vif: { en: 'domestic-violence', es: 'violencia-intrafamiliar' },
  drogas: { en: 'drug-crimes', es: 'drogas' },
  armas: { en: 'weapons', es: 'armas' },
  propiedad: { en: 'property', es: 'propiedad' },
  incivilidades: { en: 'disorder', es: 'incivilidades' },
};

export interface NavStrings {
  home: string;
  map: string;
  methodology: string;
}

export const NAV_STRINGS: Record<'en' | 'es', NavStrings> = {
  en: {
    home: EN_STRINGS.nav_home,
    map: EN_STRINGS.nav_map,
    methodology: EN_STRINGS.nav_methodology,
  },
  es: {
    home: ES_STRINGS.nav_home,
    map: ES_STRINGS.nav_map,
    methodology: ES_STRINGS.nav_methodology,
  },
};

/**
 * Grammatically correct Spanish region phrase from the bare region name as
 * stored in data/cead/regions/*.json (e.g. "Metropolitana", "Biobío").
 *
 * Most regions take "Región de {name}", but a few don't:
 *   - "Región Metropolitana"  (no preposition)
 *   - "Región del Maule" / "Región del Biobío"  ("del")
 *
 * Use this instead of the literal `Región de {name}` template, which produced
 * the ungrammatical "Región de Metropolitana" (F-006). The static
 * `page_region_h1` string can't encode this rule — call this helper instead.
 */
export function regionNameEs(name: string): string {
  const NO_PREPOSITION = new Set(['Metropolitana']);
  const DEL = new Set(['Maule', 'Biobío']);
  if (NO_PREPOSITION.has(name)) return `Región ${name}`;
  if (DEL.has(name)) return `Región del ${name}`;
  return `Región de ${name}`;
}
