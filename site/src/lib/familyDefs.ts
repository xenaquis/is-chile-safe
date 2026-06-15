/**
 * Shared crime-family constants — single source of truth.
 * Hoisted verbatim from site/src/pages/crime/[family].astro and
 * site/src/pages/es/delito/[family].astro. Do NOT alter strings.
 */

export const FAMILY_ORDER = [
  'vida',
  'propiedad',
  'robos_violentos',
  'incivilidades',
  'vif',
  'drogas',
  'armas',
] as const;

// Family display labels (EN)
export const FAMILY_LABELS_EN: Record<string, string> = {
  vida:            'Life Crimes',
  robos_violentos: 'Violent Robbery',
  vif:             'Domestic Violence',
  drogas:          'Drug Crimes',
  armas:           'Weapons Offences',
  propiedad:       'Property Crimes',
  incivilidades:   'Disorder',
};

// Sober one-sentence definition per family (EN)
export const FAMILY_DEFS_EN: Record<string, string> = {
  vida:            'Reported offences against life and physical integrity, including homicide and serious assault, sourced from official CEAD police statistics.',
  robos_violentos: 'Reported violent robbery incidents — theft involving force or intimidation — disaggregated by commune from official CEAD police statistics.',
  vif:             'Reported domestic and intra-family violence incidents disaggregated by commune, sourced from official CEAD police statistics.',
  drogas:          'Reported drug-related offences including possession and trafficking, disaggregated by commune from official CEAD police statistics.',
  armas:           'Reported weapons offences including illegal possession and trafficking, disaggregated by commune from official CEAD police statistics.',
  propiedad:       'Reported property crime incidents — burglary, theft, and fraud — disaggregated by commune from official CEAD police statistics.',
  incivilidades:   'Reported disorder and public nuisance incidents disaggregated by commune from official CEAD police statistics.',
};

// Family display labels (ES)
export const FAMILY_LABELS_ES: Record<string, string> = {
  vida:            'Delitos contra la Vida',
  robos_violentos: 'Robos Violentos',
  vif:             'Violencia Intrafamiliar',
  drogas:          'Drogas',
  armas:           'Armas',
  propiedad:       'Delitos contra la Propiedad',
  incivilidades:   'Incivilidades',
};

// Sober one-sentence definition per family (ES)
export const FAMILY_DEFS_ES: Record<string, string> = {
  vida:            'Delitos reportados contra la vida e integridad física, incluyendo homicidios y lesiones graves, según estadísticas policiales oficiales del CEAD.',
  robos_violentos: 'Robos con violencia o intimidación reportados, desagregados por comuna, según estadísticas policiales oficiales del CEAD.',
  vif:             'Denuncias de violencia doméstica e intrafamiliar desagregadas por comuna, según estadísticas policiales oficiales del CEAD.',
  drogas:          'Delitos de drogas reportados, incluyendo porte y tráfico, desagregados por comuna, según estadísticas policiales oficiales del CEAD.',
  armas:           'Delitos de armas reportados, incluyendo porte ilegal, desagregados por comuna, según estadísticas policiales oficiales del CEAD.',
  propiedad:       'Delitos contra la propiedad reportados — robos, hurtos y fraudes — desagregados por comuna, según estadísticas policiales oficiales del CEAD.',
  incivilidades:   'Incivilidades y alteraciones al orden público reportadas, desagregadas por comuna, según estadísticas policiales oficiales del CEAD.',
};
