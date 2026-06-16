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
  homicidios:      'Homicide',
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
  homicidios:      'Reported homicide cases disaggregated by commune, sourced from CEAD official police statistics (subgroup 101 within the Life Crimes family).',
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
  homicidios:      'Homicidios',
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
  homicidios:      'Casos de homicidio reportados desagregados por comuna, según estadísticas policiales oficiales del CEAD (subgrupo 101 dentro de Delitos contra la Vida).',
};

// Extended methodology notes for crime-ranking pages
export const RANKING_METHODOLOGY_EN: Record<string, string> = {
  homicidios:      'Reported homicide incidence per 100,000 inhabitants by commune. Includes homicide, femicide, parricide, infanticide, and related offences (CEAD subgroup 101 within the Life Crimes family). Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  robos_violentos: 'Reported violent robbery incidence per 100,000 inhabitants by commune. Includes robbery with violence and robbery with intimidation. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  drogas:          'Reported drug offence incidence per 100,000 inhabitants by commune. Includes possession (porte) and trafficking (tráfico and microtráfico). Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  propiedad:       'Reported property crime incidence per 100,000 inhabitants by commune. Includes burglary, theft (hurto), and fraud — the full CEAD "Delitos contra la Propiedad" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  vif:             'Reported domestic and intra-family violence incidence per 100,000 inhabitants by commune. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  armas:           'Reported weapons offence incidence per 100,000 inhabitants by commune. Includes illegal possession and trafficking of firearms. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  incivilidades:   'Reported public disorder incidence per 100,000 inhabitants by commune. Includes the full CEAD "Incivilidades" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  vida:            'Reported life crimes incidence per 100,000 inhabitants by commune. Includes all offences against life and physical integrity in the CEAD "Delitos contra la Vida" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
};

export const RANKING_METHODOLOGY_ES: Record<string, string> = {
  homicidios:      'Incidencia reportada de homicidios por 100.000 habitantes por comuna. Incluye homicidio, femicidio, parricidio, infanticidio y delitos relacionados (subgrupo CEAD 101 dentro de Delitos contra la Vida). Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  robos_violentos: 'Incidencia reportada de robos violentos por 100.000 habitantes por comuna. Incluye robo con violencia y robo con intimidación. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  drogas:          'Incidencia reportada de delitos de drogas por 100.000 habitantes por comuna. Incluye porte y tráfico (tráfico y microtráfico). Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  propiedad:       'Incidencia reportada de delitos contra la propiedad por 100.000 habitantes por comuna. Incluye robos en lugar habitado, hurtos y fraudes — el total de la familia CEAD "Delitos contra la Propiedad". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  vif:             'Incidencia reportada de violencia intrafamiliar por 100.000 habitantes por comuna. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  armas:           'Incidencia reportada de delitos de armas por 100.000 habitantes por comuna. Incluye porte ilegal y tráfico de armas de fuego. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  incivilidades:   'Incidencia reportada de incivilidades por 100.000 habitantes por comuna. Incluye el total de la familia CEAD "Incivilidades". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  vida:            'Incidencia reportada de delitos contra la vida por 100.000 habitantes por comuna. Incluye todos los delitos contra la vida e integridad física de la familia CEAD "Delitos contra la Vida". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
};
