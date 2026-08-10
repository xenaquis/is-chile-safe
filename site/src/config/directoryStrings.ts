/**
 * directoryStrings.ts — strings added by the commune-directory redesign.
 *
 * Deliberately a SEPARATE module rather than new keys in config/i18n.ts:
 * i18n.ts is a 750-line file with a Strings interface that every page depends
 * on; adding keys there means a diff in a shared file and a type change.
 * These six keys are used by exactly one component, so they live next to it.
 *
 * Everything else the directory shows already exists in i18n.ts and is reused
 * verbatim: dir_title, dir_lead, dir_count, dir_lowpop_tag, dir_empty,
 * dir_search_placeholder, th_rank, th_commune, th_region, th_rate_per_100k,
 * sort_label, sort_ascending, sort_descending, ci_band_1..5,
 * news_clear_filters, low_pop_footnote.
 */

export interface DirectoryStrings {
  dir_all_regions: string;
  dir_near_me: string;
  dir_near_denied: string;
  dir_near_chip: string;
  dir_scale_hint: string;
  dir_scale_aria: string;
  dir_rank_title: string;
  dir_source_note: string;
}

export const DIR_EN: DirectoryStrings = {
  dir_all_regions: 'All regions',
  dir_near_me: 'Near me',
  dir_near_denied: 'Location unavailable. Use the search box or pick a region.',
  dir_near_chip: 'Near you · {name}',
  dir_scale_hint: 'Lowest → highest reported incidence',
  dir_scale_aria: 'Filter by incidence band',
  dir_rank_title: 'National position by reported incidence rate (1 = highest)',
  dir_source_note:
    'Source: CEAD, police cases {year}, rate per 100,000 inhabitants. Communes with a small resident population are tagged — their rates are volatile.',
};

export const DIR_ES: DirectoryStrings = {
  dir_all_regions: 'Todas las regiones',
  dir_near_me: 'Cerca de mí',
  dir_near_denied: 'No pudimos obtener tu ubicación. Usa el buscador o elige una región.',
  dir_near_chip: 'Cerca de ti · {name}',
  dir_scale_hint: 'Incidencia reportada más baja → más alta',
  dir_scale_aria: 'Filtrar por banda de incidencia',
  dir_rank_title: 'Posición nacional por tasa de incidencia reportada (1 = más alta)',
  dir_source_note:
    'Fuente: CEAD, casos policiales {year}, tasa por 100.000 habitantes. Las comunas de baja población van marcadas: su tasa es volátil.',
};
