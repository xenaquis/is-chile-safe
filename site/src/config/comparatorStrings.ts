/**
 * comparatorStrings.ts — new EN/ES strings for the redesigned commune comparator.
 *
 * WHY A SEPARATE FILE (and not config/i18n.ts):
 * ComparatorIsland mounts with client:only="react". Importing i18n.ts from the
 * island would bundle the entire i18n module (~700 strings + helpers) into the
 * client chunk — the reason the existing island receives a hand-picked `strings`
 * object as a prop. This module has NO imports and no side effects, so importing
 * it directly from the island adds only the keys below.
 *
 * Same pattern as config/directoryStrings.ts and config/rankingStrings.ts.
 * All keys are prefixed cx_ so they can be folded into I18nStrings later
 * mechanically if desired.
 *
 * The comparator ALSO keeps consuming these existing i18n keys through the
 * `strings` prop (unchanged, still passed by the Astro shells):
 *   cmp_input_placeholder · cmp_empty_heading · cmp_empty_body · cmp_add_prompt
 *   cmp_no_match · cmp_max_reached · cmp_remove_aria · cmp_data_error
 *   cmp_homicide_row · cmp_homicide_no_data · cmp_case_singular · cmp_case_plural
 *   cmp_composite_label · cmp_what_is_this · cmp_trend_unavailable · cmp_chips_label
 */

export interface ComparatorStrings {
  /** Section title above the per-family chart. */
  cx_profile_heading: string;
  /** Legend label for the dashed national reference line. */
  cx_national_line: string;
  /** Reference-year label, e.g. "Reference year 2024". {year} */
  cx_reference_year: string;
  /** Shown when the selected communes have no common complete year. {years} */
  cx_mixed_years: string;
  /** Caption under the chart. */
  cx_scale_note: string;
  /** Total-rate caption on each headline card. */
  cx_total_rate: string;
  /** National-rank line on each headline card. {rank} */
  cx_rank_line: string;
  /** Distance to the national rate. {pct} */
  cx_above_mean: string;
  cx_below_mean: string;
  cx_at_mean: string;
  /** Plain-language summary. {a} {b} {n} {total} {family} {va} {vb} */
  cx_summary: string;
  /** Appended when a third commune is selected. {c} */
  cx_summary_third: string;
  /** Prompt inside the empty state / add-slot. */
  cx_add_slot: string;
  /** Sort-the-selection button. */
  cx_sort_button: string;
  /** Accessible description of one chart row. {family} {values} */
  cx_row_aria: string;
  /** Low-population tag in the picker list. */
  cx_lowpop_tag: string;
  /** Homicide block heading. */
  cx_homicide_heading: string;
  /** Screen-reader caption for the equivalent data table. */
  cx_table_caption: string;
  cx_th_family: string;
}

export const COMPARATOR_STRINGS_EN: ComparatorStrings = {
  cx_profile_heading: 'Profile by crime type',
  cx_national_line: 'National rate',
  cx_reference_year: 'Reference year {year}',
  cx_mixed_years: 'These communes have no shared complete year; each column uses its own latest complete year ({years}).',
  cx_scale_note: 'Shared scale per row, fitted to the selected communes. Rates per 100,000 inhabitants. Source: CEAD.',
  cx_total_rate: 'reported cases per 100k — all crime types',
  cx_rank_line: 'Rank {rank} of 346 — 1 = highest reported incidence (CEAD)',
  cx_above_mean: '{pct}% above the national rate',
  cx_below_mean: '{pct}% below the national rate',
  cx_at_mean: 'same as the national rate',
  cx_summary: '{a} records a lower reported rate than {b} in {n} of {total} crime families. The widest gap is {family}: {va} vs {vb} cases per 100,000 inhabitants.',
  cx_summary_third: '{c} is shown as a third reference.',
  cx_add_slot: 'Add commune',
  cx_sort_button: 'Order by incidence',
  cx_row_aria: '{family}: {values}',
  cx_lowpop_tag: 'low pop.',
  cx_homicide_heading: 'Homicide',
  cx_table_caption: 'Reported rates per 100,000 inhabitants by crime type and commune. Source: CEAD.',
  cx_th_family: 'Crime type',
};

export const COMPARATOR_STRINGS_ES: ComparatorStrings = {
  cx_profile_heading: 'Perfil por tipo de delito',
  cx_national_line: 'Tasa nacional',
  cx_reference_year: 'Año de referencia {year}',
  cx_mixed_years: 'Estas comunas no tienen un año completo en común; cada columna usa su último año completo ({years}).',
  cx_scale_note: 'Escala común por fila, ajustada a las comunas seleccionadas. Tasas por 100.000 habitantes. Fuente: CEAD.',
  cx_total_rate: 'casos reportados por 100k — todos los delitos',
  cx_rank_line: 'Puesto {rank} de 346 — 1 = mayor incidencia reportada (CEAD)',
  cx_above_mean: '{pct}% sobre la tasa nacional',
  cx_below_mean: '{pct}% bajo la tasa nacional',
  cx_at_mean: 'igual a la tasa nacional',
  cx_summary: '{a} registra una tasa reportada menor que {b} en {n} de {total} familias delictivas. La mayor diferencia está en {family}: {va} frente a {vb} casos por 100.000 habitantes.',
  cx_summary_third: '{c} se muestra como tercera referencia.',
  cx_add_slot: 'Añadir comuna',
  cx_sort_button: 'Ordenar por incidencia',
  cx_row_aria: '{family}: {values}',
  cx_lowpop_tag: 'baja pob.',
  cx_homicide_heading: 'Homicidios',
  cx_table_caption: 'Tasas reportadas por 100.000 habitantes según tipo de delito y comuna. Fuente: CEAD.',
  cx_th_family: 'Tipo de delito',
};

/** Slot accents — one per selected commune. Deliberately outside the 5-step
 *  incidence scale (--s1…--s5) so a slot color is never read as a band color.
 *  All three sit at L≈0.5 on white: AA for 14px+ bold text and for 16px dots. */
export const SLOT_COLORS = [
  'oklch(0.52 0.13 250)',
  'oklch(0.54 0.14 45)',
  'oklch(0.48 0.11 155)',
] as const;
