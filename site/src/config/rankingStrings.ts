/**
 * rankingStrings.ts — strings added by the rankings v2 package.
 *
 * Lives outside config/i18n.ts on purpose: i18n.ts is a shared file whose
 * `I18nStrings` interface is consumed by ~40 components, and this package
 * should not force a change there. Everything that already existed in
 * i18n.ts is reused as-is (th_rank, th_commune, th_region,
 * th_rate_per_100k, low_pop_footnote, year_select_label, year_select_aria,
 * news_filter_region_label, news_clear_filters, sort_label, ci_band_*).
 */

export interface RankingStrings {
  rk_search_placeholder: string;
  rk_sort_high: string;
  rk_sort_low: string;
  rk_exclude_lowpop: string;
  rk_exclude_lowpop_title: string;
  rk_all_regions: string;
  rk_region_panel: string;
  rk_region_panel_hint: string;
  rk_region_panel_aria: string;
  rk_mean_marker: string;
  rk_count: string;
  rk_empty: string;
  rk_col_bar: string;
  rk_types_aria: string;
  rk_rank_year_note: string;
  rk_source_note: string;
  rk_more: string;

  rk_hub_h1: string;
  rk_hub_lead: string;
  rk_hub_types_heading: string;
  rk_hub_card_mean: string;
  rk_hub_card_top: string;
  rk_hub_card_def: string;
  rk_hub_other_heading: string;
  rk_hub_lowest: string;
  rk_hub_lowest_sub: string;
  rk_hub_directory: string;
  rk_hub_directory_sub: string;
  rk_hub_regions_heading: string;
  rk_hub_regions_lead: string;
  rk_hub_method: string;
}

export const RK_EN: RankingStrings = {
  rk_search_placeholder: 'Search commune',
  rk_sort_high: 'Highest incidence',
  rk_sort_low: 'Lowest',
  rk_exclude_lowpop: 'Exclude low population',
  rk_exclude_lowpop_title:
    'Communes under 10,000 inhabitants — rates per 100,000 are volatile at that size',
  rk_all_regions: 'All regions',
  rk_region_panel: 'Average by region',
  rk_region_panel_hint: 'Click to filter the table',
  rk_region_panel_aria: 'Regional averages — filter the table by region',
  rk_mean_marker: 'National average {v} per 100k',
  rk_count: '{n} of {total} communes',
  rk_empty: 'No communes match these filters.',
  rk_col_bar: 'Compared to the national average',
  rk_types_aria: 'Crime type',
  rk_rank_year_note:
    'Rank is published only for {year} (CEAD, latest complete year); for other years compare the rate per 100,000.',
  rk_source_note:
    'Source: CEAD, reported police cases. Position 1 = highest reported incidence for the selected crime type.',
  rk_more: 'Show more — {n} left',

  rk_hub_h1: 'Crime Incidence Rankings',
  rk_hub_lead:
    'Reported incidence rates per 100,000 inhabitants published by CEAD (Centro de Estudios y Análisis del Delito), the official Chilean police statistics body. Rates allow fair comparison across communes of very different sizes. Under-reporting varies by crime type; treat all figures as reported counts, not absolute measures of risk.',
  rk_hub_types_heading: 'By crime type',
  rk_hub_card_mean: 'National average {v} per 100k',
  rk_hub_card_top: 'Highest: {name} ({v})',
  rk_hub_card_def: 'What this category covers',
  rk_hub_other_heading: 'By commune',
  rk_hub_lowest: 'Communes with the lowest reported crime incidence in Chile',
  rk_hub_lowest_sub: 'Ranked by total reported rate (excludes low-population communes).',
  rk_hub_directory: 'Browse all 346 communes',
  rk_hub_directory_sub: 'Search by name, region or incidence level.',
  rk_hub_regions_heading: 'By region',
  rk_hub_regions_lead:
    'Each region page shows reported incidence trends, annual evolution, and the communes within it.',
  rk_hub_method: 'See Methodology for data definitions and caveats.',
};

export const RK_ES: RankingStrings = {
  rk_search_placeholder: 'Buscar comuna',
  rk_sort_high: 'Mayor incidencia',
  rk_sort_low: 'Menor',
  rk_exclude_lowpop: 'Excluir baja población',
  rk_exclude_lowpop_title:
    'Comunas de menos de 10.000 habitantes — a ese tamaño la tasa por 100.000 es volátil',
  rk_all_regions: 'Todas las regiones',
  rk_region_panel: 'Media por región',
  rk_region_panel_hint: 'Clic para filtrar la tabla',
  rk_region_panel_aria: 'Medias regionales — filtra la tabla por región',
  rk_mean_marker: 'Media nacional {v} por 100k',
  rk_count: '{n} de {total} comunas',
  rk_empty: 'Sin comunas con esos filtros.',
  rk_col_bar: 'Comparación con la media nacional',
  rk_types_aria: 'Tipo de delito',
  rk_rank_year_note:
    'La posición se publica solo para {year} (CEAD, último año completo); para otros años compara la tasa por 100.000.',
  rk_source_note:
    'Fuente: CEAD, casos policiales reportados. Posición 1 = mayor incidencia reportada del tipo de delito seleccionado.',
  rk_more: 'Ver más — quedan {n}',

  rk_hub_h1: 'Rankings de Incidencia Delictiva',
  rk_hub_lead:
    'Tasas de incidencia reportada por 100.000 habitantes publicadas por el CEAD (Centro de Estudios y Análisis del Delito), el organismo oficial de estadísticas policiales de Chile. Las tasas permiten comparar comunas de tamaños muy distintos en igualdad de condiciones. La sub-notificación varía según el tipo de delito; los datos reflejan registros policiales, no una medida absoluta de riesgo.',
  rk_hub_types_heading: 'Por tipo de delito',
  rk_hub_card_mean: 'Media nacional {v} por 100k',
  rk_hub_card_top: 'Mayor: {name} ({v})',
  rk_hub_card_def: 'Qué incluye esta categoría',
  rk_hub_other_heading: 'Por comuna',
  rk_hub_lowest: 'Comunas con menor incidencia delictiva reportada en Chile',
  rk_hub_lowest_sub: 'Clasificadas por tasa total reportada (excluye comunas de baja población).',
  rk_hub_directory: 'Ver las 346 comunas',
  rk_hub_directory_sub: 'Busca por nombre, región o nivel de incidencia.',
  rk_hub_regions_heading: 'Por región',
  rk_hub_regions_lead:
    'Cada página regional muestra las tendencias de incidencia, la evolución anual y las comunas que la componen.',
  rk_hub_method: 'Ver Metodología para definiciones y advertencias sobre los datos.',
};

/**
 * The 8 ranking routes — single source of truth for both [crime].astro pages,
 * the chip row inside RankingBoard and the hub cards.
 *
 * Hoisted verbatim from the CRIME_RANKING_DEFS literal that today lives
 * duplicated inside pages/crime-ranking/[crime].astro and
 * pages/es/ranking-delito/[crime].astro. Order = display order of the chips.
 */
export interface RankingDef {
  en: string;
  es: string;
  familyKey: string;
  dataSource: 'featured_rates' | 'by_family';
}

export const RANKING_DEFS: RankingDef[] = [
  { en: 'homicide', es: 'homicidios', familyKey: 'homicidios', dataSource: 'featured_rates' },
  { en: 'life-crimes', es: 'delitos-contra-la-vida', familyKey: 'vida', dataSource: 'by_family' },
  { en: 'violent-robbery', es: 'robos-violentos', familyKey: 'robos_violentos', dataSource: 'by_family' },
  { en: 'property', es: 'propiedad', familyKey: 'propiedad', dataSource: 'by_family' },
  { en: 'disorder', es: 'incivilidades', familyKey: 'incivilidades', dataSource: 'by_family' },
  { en: 'domestic-violence', es: 'violencia-intrafamiliar', familyKey: 'vif', dataSource: 'by_family' },
  { en: 'drug-crimes', es: 'drogas', familyKey: 'drogas', dataSource: 'by_family' },
  { en: 'weapons', es: 'armas', familyKey: 'armas', dataSource: 'by_family' },
];

export const rankingPath = (def: RankingDef, lang: 'en' | 'es') =>
  lang === 'es' ? `/es/ranking-delito/${def.es}/` : `/crime-ranking/${def.en}/`;

/** One accent per family — used for the chip dot and the row bar. */
export const FAMILY_ACCENT: Record<string, string> = {
  homicidios: 'oklch(0.48 0.16 25)',
  vida: 'oklch(0.58 0.14 25)',
  robos_violentos: 'oklch(0.60 0.13 60)',
  propiedad: 'oklch(0.62 0.12 95)',
  incivilidades: 'oklch(0.62 0.07 150)',
  vif: 'oklch(0.58 0.13 345)',
  drogas: 'oklch(0.58 0.13 305)',
  armas: 'oklch(0.58 0.12 265)',
};
