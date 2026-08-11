/**
 * homeV2Strings.ts — EN/ES strings for the Home v2 dashboard modules.
 * NEW module (Landing v2 / proposal 6b). Page-level copy (H1, intro, prose)
 * stays verbatim in each index.astro; only module strings live here.
 * config/i18n.ts is NOT touched.
 */
export interface HomeV2Strings {
  glance_title: string;
  glance_note: string;          // "{n} communes · CEAD {year}"
  glance_low: string;
  glance_high: string;
  glance_band_aria: string;     // "{label}: {n} communes — isolate on the map"
  glance_open_map: string;
  glance_svg_aria: string;      // LPX-11: SVG aria-label carries the continental-scope qualifier
  extremes_high_title: string;
  extremes_low_title: string;
  extremes_toggle_high: string;
  extremes_toggle_low: string;
  extremes_band_note: string;   // "{label} · {n} communes (excl. low population)"
  extremes_see_ranking: string;
  extremes_browse_all: string;
  bands: string[];              // level 1..5 qualitative labels
  news_title: string;
  news_all_types: string;
  news_incidents: string;       // "incidents"
  news_see_all: string;
  news_days_window: string;     // "last {n} days"
  search_no_match: string;
  search_count_one: string;     // V-02: aria-live announcement, singular
  search_count_many: string;    // V-02: aria-live announcement, "{n} communes"
  suggest_lowpop: string;       // LPX-10: verbatim copy of i18n.ts dir_lowpop_tag
  stats_communes: string;
  stats_mean: string;
  stats_press: string;
  explore_title: string;
}

export const HOME_V2_EN: HomeV2Strings = {
  glance_title: 'Chile at a glance',
  glance_note: '{n} communes · CEAD {year}',
  glance_low: 'Lowest incidence',
  glance_high: 'Highest',
  glance_band_aria: '{label}: {n} communes — isolate on the map',
  glance_open_map: 'Open the interactive map →',
  glance_svg_aria: 'Chile at a glance — continental communes',
  extremes_high_title: 'Highest Reported Rate',
  extremes_low_title: 'Lowest Reported Rate',
  extremes_toggle_high: 'Highest',
  extremes_toggle_low: 'Lowest',
  extremes_band_note: '{label} · {n} communes (excl. low population)',
  extremes_see_ranking: 'See full ranking of 346 communes →',
  extremes_browse_all: 'Browse all communes →',
  bands: ['Very low incidence', 'Low incidence', 'Medium incidence', 'High incidence', 'Very high incidence'],
  news_title: 'News pulse',
  news_all_types: 'All types',
  news_incidents: 'incidents',
  news_see_all: 'See all news →',
  news_days_window: 'last {n} days',
  search_no_match: 'No commune matches',
  search_count_one: '1 commune',
  search_count_many: '{n} communes',
  suggest_lowpop: 'low pop.',
  stats_communes: 'communes with data',
  stats_mean: 'national mean /100k',
  stats_press: 'press incidents · 30 days',
  explore_title: 'Explore by Topic',
};

export const HOME_V2_ES: HomeV2Strings = {
  glance_title: 'Chile en un vistazo',
  glance_note: '{n} comunas · CEAD {year}',
  glance_low: 'Menor incidencia',
  glance_high: 'Mayor',
  glance_band_aria: '{label}: {n} comunas — aislar en el mapa',
  glance_open_map: 'Abrir el mapa interactivo →',
  glance_svg_aria: 'Chile en un vistazo — comunas continentales',
  extremes_high_title: 'Mayor incidencia reportada',
  extremes_low_title: 'Menor incidencia reportada',
  extremes_toggle_high: 'Mayor',
  extremes_toggle_low: 'Menor',
  extremes_band_note: '{label} · {n} comunas (excl. baja población)',
  extremes_see_ranking: 'Ver ranking completo de 346 comunas →',
  extremes_browse_all: 'Ver todas las comunas →',
  bands: ['Incidencia muy baja', 'Incidencia baja', 'Incidencia media', 'Incidencia alta', 'Incidencia muy alta'],
  news_title: 'Pulso de noticias',
  news_all_types: 'Todos los tipos',
  news_incidents: 'incidentes',
  news_see_all: 'Ver todas las noticias →',
  news_days_window: 'últimos {n} días',
  search_no_match: 'Ninguna comuna coincide',
  search_count_one: '1 comuna',
  search_count_many: '{n} comunas',
  suggest_lowpop: 'baja pob.',
  stats_communes: 'comunas con datos',
  stats_mean: 'media nacional /100k',
  stats_press: 'incidentes en prensa · 30 días',
  explore_title: 'Explorar por tema',
};

export function homeV2Strings(locale: 'en' | 'es'): HomeV2Strings {
  return locale === 'en' ? HOME_V2_EN : HOME_V2_ES;
}

export function fmt(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ''));
}
