import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { feature as topoFeature } from 'topojson-client';
import {
  MAP_MAX_ZOOM,
  MAP_MIN_ZOOM,
  REGIONAL_CAPITAL_CUTS,
  ANCHOR_CITY_CUTS,
  CONTEXT_LABELS,
  MAX_COMMUNE_LABELS,
  CAPITAL_LABEL_POINTS,
  labelAnchor,
  communeLabelCandidates,
  contextLabelsForZoom,
  cullCollisions,
  estimateLabelWidth,
  type CommuneLabelSource,
  type LabelBox,
} from './basemapLabels';

const SITE = process.cwd();
const MAP_DIR = path.join(SITE, 'src', 'components', 'map');
const REPO = path.resolve(SITE, '..');

const c = (cut: string, name: string, population: number, lat = -33, lng = -70.6): CommuneLabelSource => ({
  cut, name, population, lat, lng,
});

describe('zoom cap (no tile layer => the cap must live on the map)', () => {
  it('caps zoom at 13 and keeps min zoom 4', () => {
    expect(MAP_MAX_ZOOM).toBe(13);
    expect(MAP_MIN_ZOOM).toBe(4);
  });

  it('MapIsland passes the cap to L.map()', () => {
    const src = readFileSync(path.join(MAP_DIR, 'MapIsland.tsx'), 'utf8');
    expect(src).toMatch(/maxZoom:\s*MAP_MAX_ZOOM/);
    expect(src).toMatch(/minZoom:\s*MAP_MIN_ZOOM/);
  });
});

describe('no third-party tile host in the map source', () => {
  it('has no tileLayer call and no tile URL template', () => {
    const offenders: string[] = [];
    for (const f of readdirSync(MAP_DIR)) {
      if (!/\.(tsx?|css)$/.test(f)) continue;
      const src = readFileSync(path.join(MAP_DIR, f), 'utf8');
      if (/\b(?:tileLayer|gridLayer|imageOverlay|videoOverlay)\b|cartocdn|tile\.openstreetmap|\{z\}|\/\{x\}\/\{y\}/i.test(src)) offenders.push(f);
    }
    expect(offenders).toEqual([]);
  });
});

describe('label data', () => {
  const index = JSON.parse(
    readFileSync(path.join(REPO, 'data', 'cead', 'meta', 'index.json'), 'utf8')
  ) as Array<{ cut: string }>;
  const cuts = new Set(index.map((e) => e.cut));

  it('16 distinct regional capitals, all present in index.json', () => {
    expect(new Set(REGIONAL_CAPITAL_CUTS).size).toBe(16);
    expect(REGIONAL_CAPITAL_CUTS.filter((cut) => !cuts.has(cut))).toEqual([]);
  });

  it('anchor cities are regional capitals', () => {
    expect(ANCHOR_CITY_CUTS.filter((cut) => !REGIONAL_CAPITAL_CUTS.includes(cut))).toEqual([]);
  });

  it('context labels are bilingual and carry no evaluative wording', () => {
    for (const l of CONTEXT_LABELS) {
      expect(l.en.length).toBeGreaterThan(0);
      expect(l.es.length).toBeGreaterThan(0);
    }
    expect(CONTEXT_LABELS.some((l) => /falkland|malvinas|antar/i.test(l.en + l.es))).toBe(false);
  });

  it('context labels only on the overview', () => {
    expect(contextLabelsForZoom(4).length).toBe(CONTEXT_LABELS.length);
    expect(contextLabelsForZoom(6).length).toBe(CONTEXT_LABELS.length);
    expect(contextLabelsForZoom(7)).toEqual([]);
  });
});

describe('label anchors (names must sit on the place they name)', () => {
  const topo = JSON.parse(readFileSync(path.join(REPO, 'data', 'cead', 'geo', 'communes.topo.json'), 'utf8'));
  const fc = topoFeature(topo, topo.objects[Object.keys(topo.objects)[0]]) as unknown as GeoJSON.FeatureCollection;
  type Ring = number[][];
  const ringHas = (ring: Ring, x: number, y: number) => {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  };
  const polysByCut = new Map<string, Ring[][]>();
  for (const f of fc.features) {
    const g = f.geometry;
    if (g.type === 'Polygon') polysByCut.set(String(f.properties?.id), [g.coordinates as Ring[]]);
    else if (g.type === 'MultiPolygon') polysByCut.set(String(f.properties?.id), g.coordinates as Ring[][]);
  }
  const inCommune = (cut: string, lat: number, lng: number) =>
    (polysByCut.get(cut) ?? []).some((p) => ringHas(p[0], lng, lat) && !p.slice(1).some((h) => ringHas(h, lng, lat)));

  it('every one of the 346 communes has an anchor inside its own polygon', () => {
    expect(polysByCut.size).toBe(346);
    const outside: string[] = [];
    for (const cut of polysByCut.keys()) {
      const a = labelAnchor(cut);
      if (!a || !inCommune(cut, a.lat, a.lng)) outside.push(cut);
    }
    expect(outside).toEqual([]);
  });

  it('each regional capital is anchored on the city, inside its own commune', () => {
    expect(Object.keys(CAPITAL_LABEL_POINTS).sort()).toEqual([...REGIONAL_CAPITAL_CUTS].sort());
    for (const cut of REGIONAL_CAPITAL_CUTS) {
      const [lat, lng] = CAPITAL_LABEL_POINTS[cut];
      expect(inCommune(cut, lat, lng), `capital ${cut}`).toBe(true);
      expect(labelAnchor(cut)).toEqual({ lat, lng });
    }
  });

  it('known city positions (independent reference, 10 km tolerance)', () => {
    // Plaza de Armas of each city, from general reference — NOT copied from the table.
    const ref: Record<string, [number, number]> = {
      '12101': [-53.163, -70.908], // Punta Arenas
      '2101': [-23.646, -70.398],  // Antofagasta
      '1101': [-20.214, -70.152],  // Iquique
      '15101': [-18.478, -70.321], // Arica
      '10101': [-41.472, -72.937], // Puerto Montt
      '14101': [-39.814, -73.246], // Valdivia
      '3101': [-27.366, -70.332],  // Copiapó
    };
    for (const [cut, [rlat, rlng]] of Object.entries(ref)) {
      const a = labelAnchor(cut)!;
      const km = 111.32 * Math.hypot(a.lat - rlat, (a.lng - rlng) * Math.cos((rlat * Math.PI) / 180));
      expect(km, `capital ${cut}`).toBeLessThan(10);
    }
  });

  it('unknown CUT has no anchor (caller falls back to the dot centroid)', () => {
    expect(labelAnchor('99999')).toBeNull();
  });
});

describe('communeLabelCandidates', () => {
  const communes = [
    c('13101', 'Santiago', 500_000),
    c('13201', 'Puente Alto', 650_000),
    c('13102', 'Cerrillos', 90_000),
    c('5101', 'Valparaíso', 300_000),
    c('12202', 'Antártica', 151, -63.2, -68.2),
    c('5201', 'Isla de Pascua', 8_000, -27.1, -109.4),
    c('2101', 'Antofagasta', 400_000),
  ];

  it('z4-5: anchor cities only', () => {
    expect(communeLabelCandidates(4, communes).map((x) => x.cut)).toEqual(['2101', '13101']);
  });

  it('z6-7: regional capitals only', () => {
    expect(communeLabelCandidates(7, communes).map((x) => x.cut).sort()).toEqual(['13101', '2101', '5101']);
  });

  it('z8-9: capitals first, then >=100k by population', () => {
    const got = communeLabelCandidates(9, communes).map((x) => x.cut);
    expect(got.slice(-1)).toEqual(['13201']);
    expect(got).not.toContain('13102');
  });

  it('z10+: every commune, capitals first, never Antártica / Isla de Pascua', () => {
    const got = communeLabelCandidates(10, communes).map((x) => x.cut);
    expect(got).toContain('13102');
    expect(got).not.toContain('12202');
    expect(got).not.toContain('5201');
    expect(got.indexOf('13101')).toBeLessThan(got.indexOf('13201'));
  });

  it('works without population data (index.json failed to load)', () => {
    const noPop = communes.map((x) => ({ ...x, population: 0 }));
    expect(communeLabelCandidates(9, noPop).length).toBe(3);
    expect(communeLabelCandidates(12, noPop).length).toBe(5);
  });
});

describe('cullCollisions', () => {
  const box = (id: string, x: number, y: number, w = 60): LabelBox => ({ id, x, y, w, h: 14, align: 'center' });

  it('keeps the earlier (higher priority) of two overlapping boxes', () => {
    expect(cullCollisions([box('a', 100, 100), box('b', 120, 104), box('c', 300, 100)])).toEqual(['a', 'c']);
  });

  it('respects the cap', () => {
    const many = Array.from({ length: 100 }, (_, i) => box(`n${i}`, i * 200, 0));
    expect(cullCollisions(many, MAX_COMMUNE_LABELS).length).toBe(MAX_COMMUNE_LABELS);
  });

  it('right-aligned boxes start beside the anchor', () => {
    const a: LabelBox = { id: 'a', x: 100, y: 100, w: 50, h: 14, align: 'right', dx: 12 };
    const b: LabelBox = { id: 'b', x: 60, y: 100, w: 50, h: 14, align: 'center' }; // 35..85 vs 112..162
    expect(cullCollisions([a, b])).toEqual(['a', 'b']);
  });

  it('estimateLabelWidth uses the longest line', () => {
    expect(estimateLabelWidth('Pacific\nOcean')).toBe(estimateLabelWidth('Pacific'));
    expect(estimateLabelWidth('Santiago')).toBeGreaterThan(estimateLabelWidth('Arica'));
  });
});
