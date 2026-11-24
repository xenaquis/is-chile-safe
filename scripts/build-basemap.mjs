/**
 * build-basemap.mjs — Offline pipeline to produce data/cead/geo/basemap.topo.json
 *
 * WHY: the interactive map used a third-party raster tile service (CARTO
 * Positron). On 2026-11-24 that service started answering every tile with an
 * "API KEY REQUIRED" watermark. The map now draws its OWN basemap, so no
 * external tile/basemap host and no API key can ever break it again:
 *   - ocean            = background colour of the Leaflet container (CSS)
 *   - Chile            = the 346 commune polygons (communes.topo.json) plus a
 *                        runtime silhouette merged from that same topology
 *   - everything else  = THIS file: one dissolved "non-Chile land" geometry
 *
 * Source dataset: Natural Earth — Admin 0 Countries, 1:10m (PUBLIC DOMAIN)
 *   https://www.naturalearthdata.com/  ·  mirror github.com/nvkelso/natural-earth-vector
 *   Pinned: tag v5.1.2, sha256 below. Fetched to the OS temp dir (13 MB, NEVER
 *   committed, NEVER written under data/ — sync-data publishes that whole tree).
 *
 * Pipeline (mapshaper CLI):
 *   1. chile-union  = dissolve of data/cead/geo/communes.topo.json (the exact
 *                     simplified geometry the browser renders)
 *   2. inner points of every NON-Chile Natural Earth polygon (used in step 4)
 *   3. land         = ALL countries (incl. CHL + the "SPI" Southern Patagonian
 *                     Ice Field feature) clipped to a WORLD-CONTEXT bbox,
 *                     dissolved to one mass, simplified, small islands dropped,
 *                     then  -erase chile-union
 *   4. -explode, keep only pieces containing a step-2 point → drops the detached
 *      Natural-Earth-Chile coast slivers/islands (no double coast) while border
 *      slivers stay because they are fused to Argentina/Bolivia/Peru (no ocean
 *      coloured gaps along the Andes). Dissolve again → ONE geometry, object "land".
 *   5. Write TopoJSON (quantization 1e7 ≈ 2.5 m grid; simplify happens BEFORE
 *      the erase and never after it, or hairline gaps re-open on the border).
 *   6. Inject `meta` (source URL/tag/hash + sha256 of communes.topo.json).
 *      site/scripts/validate/map.mjs fails the build when that hash is stale.
 *   7. Assert BEFORE writing the output: Topology, budget, point probes (Chile
 *      OUT, neighbours IN), bbox coverage, and the residual-gap gate: every
 *      enclosed sea-coloured pocket between the neighbour land and the commune
 *      union, along the WHOLE border, must be <= 0.5 km2 and <= 5 km2 in total
 *      (exit 1 otherwise). The measured figures are stored in meta.gaps and
 *      re-checked by site/scripts/validate/map.mjs.
 *   8. Label anchors: one interior point per commune (mapshaper `-points inner`
 *      on the same communes.topo.json) -> site/src/data/commune-label-points.json.
 *      Each point is asserted to lie inside its own commune. The map's place
 *      names use these instead of a vertex average, which fell outside the
 *      commune for 16 of 346 (e.g. "Chillan" was drawn on Chillan Viejo).
 *
 * Design decisions:
 *   - Clip bbox is NOT the map's maxBounds: Leaflet keeps the view inside
 *     maxBounds only while the view is smaller than them; once the viewport is
 *     larger (always the case at min zoom 4) the centre is pinned and the view
 *     overhangs on every side. A 1920 px viewport then shows ~169 deg of
 *     longitude, so the land must cover the Americas, Antarctica and west
 *     Africa or the continent would end in a ruler-straight cut.
 *     KNOWN LIMIT (accepted): the north edge (14 N) enters the canvas once the
 *     map stage is taller than ~1340 px at zoom 4, but the opaque map topbar
 *     covers the top 225-350 px of the stage, so the cut only becomes visible
 *     on viewports taller than roughly 1850 px. Raising min zoom there was
 *     tried and reverted: with the view pinned to maxBounds it left northern
 *     Chile stuck under the topbar. Extending the clip north is the real fix
 *     if it ever matters (budget: 150 KB raw).
 *   - Antarctica is included as plain unlabeled land. No country borders are
 *     drawn anywhere (single dissolved mass): outlines are illustrative context,
 *     not authoritative boundaries. Disputed features (FLK, SPI, BRI) are plain land.
 *   - Filter on ADM0_A3 only (ISO_A3 is '-99' for France and others).
 *
 * Re-runnable: `node scripts/build-basemap.mjs`  (offline once the download is cached)
 * Requires: mapshaper installed globally (`npm install -g mapshaper`), Node >= 22.
 * NOT part of CI/prebuild (the runner has no mapshaper) — the output is committed.
 * MUST be re-run whenever scripts/build-topojson.mjs regenerates communes.topo.json.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// Pinned source
// ---------------------------------------------------------------------------
const NE_TAG = 'v5.1.2';
const NE_URL = `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/${NE_TAG}/geojson/ne_10m_admin_0_countries.geojson`;
const NE_SHA256 = '239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255';

// ---------------------------------------------------------------------------
// Knobs (explicit — no silent fallback configs)
// ---------------------------------------------------------------------------
const CLIP_BBOX = '-180,-85,45,14';      // world context, see header
const SIMPLIFY_PCT = '12%';              // weighted Visvalingam, BEFORE the erase
const MIN_ISLAND = '30km2';
const QUANTIZATION = '1e7';
const RAW_MAX_BYTES = 153600;            // 150 KB raw ceiling (same value in validate/map.mjs)
const GZIP_MAX_BYTES = 61440;            // 60 KB gzip ceiling

// ---------------------------------------------------------------------------
// Paths — every intermediate lives in the OS temp dir
// ---------------------------------------------------------------------------
const COMMUNES_TOPO = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes.topo.json');
const OUTPUT = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'basemap.topo.json');
const TMP = path.join(os.tmpdir(), 'ischilesafe-basemap');
const NE_FILE = path.join(TMP, 'ne_10m_admin_0_countries.geojson');
const CHILE_UNION = path.join(TMP, 'chile-union.geojson');
const NE_POINTS = path.join(TMP, 'non-chile-points.geojson');
const TMP_OUT = path.join(TMP, 'land.topo.json');
const TMP_HOLES = path.join(TMP, 'holes.geojson');
const TMP_LABELS = path.join(TMP, 'label-points.geojson');
const LABEL_POINTS_OUT = path.join(REPO_ROOT, 'site', 'src', 'data', 'commune-label-points.json');

// Residual-gap gate (step 7). Same thresholds in site/scripts/validate/map.mjs.
const GAP_RECT = [-82, -62, -58, -12];   // covers the whole Chile border, coast to coast
const GAP_MAX_PIECE_KM2 = 0.5;
const GAP_MAX_TOTAL_KM2 = 5;

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');

// Windows: build ONE command string and double-quote every path/expression.
// (Passing an args array with shell:true lets cmd.exe mangle `>` and `&&`.)
const q = (s) => `"${s}"`;
function mapshaper(parts, label) {
  console.log(`\n[mapshaper] ${label}`);
  const r = spawnSync(['mapshaper', ...parts].join(' '), { shell: true, stdio: 'inherit' });
  if (r.status !== 0) {
    console.error(`FATAL: mapshaper failed at "${label}" — is it installed globally? npm install -g mapshaper`);
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Step 0: inputs
// ---------------------------------------------------------------------------
if (!existsSync(COMMUNES_TOPO)) {
  console.error('FATAL: data/cead/geo/communes.topo.json not found — run scripts/build-topojson.mjs first.');
  process.exit(1);
}
mkdirSync(TMP, { recursive: true });
const communesSha = sha256(readFileSync(COMMUNES_TOPO));

if (existsSync(NE_FILE) && sha256(readFileSync(NE_FILE)) === NE_SHA256) {
  console.log(`Natural Earth ${NE_TAG}: cached copy OK (${NE_FILE})`);
} else {
  console.log(`Downloading Natural Earth ${NE_TAG} admin-0 countries (13 MB)...`);
  const res = await fetch(NE_URL);
  if (!res.ok) {
    console.error(`FATAL: download failed (${res.status}) — ${NE_URL}`);
    process.exit(1);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  const got = sha256(buf);
  if (got !== NE_SHA256) {
    console.error(`FATAL: sha256 mismatch for the Natural Earth download.\n  expected ${NE_SHA256}\n  got      ${got}`);
    process.exit(1);
  }
  writeFileSync(NE_FILE, buf);
  console.log(`  saved ${buf.length} bytes, sha256 verified`);
}

// ---------------------------------------------------------------------------
// Steps 1-5: geometry
// ---------------------------------------------------------------------------
mapshaper([q(COMMUNES_TOPO), '-dissolve', '-o', q(CHILE_UNION)], 'commune union');

mapshaper(
  [
    q(NE_FILE),
    '-filter', q("ADM0_A3!='CHL'"),
    '-clip', `bbox=${CLIP_BBOX}`,
    '-dissolve', '-explode',
    '-points', 'inner',
    '-o', q(NE_POINTS),
  ],
  'inner points of non-Chile land'
);

mapshaper(
  [
    q(NE_FILE),
    '-filter-fields', 'ADM0_A3',
    '-clip', `bbox=${CLIP_BBOX}`,
    '-dissolve',
    '-simplify', 'visvalingam', 'weighted', `percentage=${SIMPLIFY_PCT}`, 'keep-shapes',
    '-filter-islands', `min-area=${MIN_ISLAND}`,
    '-erase', q(CHILE_UNION),
    '-explode',
    '-join', q(NE_POINTS), q('calc=n=count()'),
    '-filter', q('n>0'),
    '-dissolve',
    '-rename-layers', 'land',
    '-o', 'format=topojson', `quantization=${QUANTIZATION}`, q(TMP_OUT),
  ],
  `land = all countries - commune union (simplify ${SIMPLIFY_PCT}, quantization ${QUANTIZATION})`
);

// ---------------------------------------------------------------------------
// Step 6: inject meta, write compact JSON
// ---------------------------------------------------------------------------
const topo = JSON.parse(readFileSync(TMP_OUT, 'utf8'));
if (topo.type !== 'Topology' || !topo.objects || !topo.objects.land) {
  console.error('FATAL: output is not a TopoJSON Topology with a "land" object');
  process.exit(1);
}
for (const g of topo.objects.land.geometries ?? [topo.objects.land]) delete g.properties;
topo.meta = {
  source: 'Natural Earth — Admin 0 Countries 1:10m (public domain)',
  sourceUrl: NE_URL,
  sourceTag: NE_TAG,
  sourceSha256: NE_SHA256,
  communesSha256: communesSha,
  clipBbox: CLIP_BBOX,
  simplify: `visvalingam weighted ${SIMPLIFY_PCT}`,
  note: 'Non-Chile land for visual context only. Outlines are illustrative, not authoritative boundaries. Built by scripts/build-basemap.mjs.',
};
const outBuf = Buffer.from(JSON.stringify(topo));

// ---------------------------------------------------------------------------
// Step 7: assertions
// ---------------------------------------------------------------------------
const raw = outBuf.length;
const gz = gzipSync(outBuf).length;
console.log(`\nRaw:  ${raw} bytes (${(raw / 1024).toFixed(1)} KB)`);
console.log(`Gzip: ${gz} bytes (${(gz / 1024).toFixed(1)} KB)`);
if (raw > RAW_MAX_BYTES || gz > GZIP_MAX_BYTES) {
  console.error(`FATAL: basemap exceeds budget (raw ${raw}/${RAW_MAX_BYTES}, gzip ${gz}/${GZIP_MAX_BYTES})`);
  process.exit(1);
}

// topojson-client lives in site/node_modules (already a site dependency)
const require = createRequire(path.join(REPO_ROOT, 'site', 'package.json'));
const { feature } = require('topojson-client');
const land = feature(topo, topo.objects.land);
const polys = [];
for (const f of land.type === 'FeatureCollection' ? land.features : [land]) {
  if (!f.geometry) continue;
  if (f.geometry.type === 'Polygon') polys.push(f.geometry.coordinates);
  else if (f.geometry.type === 'MultiPolygon') polys.push(...f.geometry.coordinates);
}
function ringHas(ring, x, y) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
const inLand = (lng, lat) =>
  polys.some((p) => ringHas(p[0], lng, lat) && !p.slice(1).some((h) => ringHas(h, lng, lat)));

let bad = 0;
const MUST_BE_OUT = { Santiago: [-70.65, -33.45], Antofagasta: [-69.6, -23.65], Temuco: [-72.6, -38.74], 'Punta Arenas (inland)': [-71.2, -53.0], 'Pacific': [-85, -30] };
const MUST_BE_IN = { Mendoza: [-68.84, -32.89], 'La Paz': [-68.13, -16.5], Lima: [-76.9, -12.0], 'Buenos Aires (W)': [-59.0, -34.8], Brasilia: [-47.9, -15.8], 'Antarctica': [-60, -80] };
for (const [name, [x, y]] of Object.entries(MUST_BE_OUT)) {
  if (inLand(x, y)) { console.error(`FATAL: ${name} is INSIDE the basemap land (Chile/ocean must not be)`); bad++; }
}
for (const [name, [x, y]] of Object.entries(MUST_BE_IN)) {
  if (!inLand(x, y)) { console.error(`FATAL: ${name} is NOT inside the basemap land`); bad++; }
}
let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, pts = 0;
for (const p of polys) for (const [x, y] of p[0]) {
  pts++;
  if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
}
console.log(`Polygons: ${polys.length}, outer-ring points: ${pts}, bbox: [${minX.toFixed(2)}, ${minY.toFixed(2)}, ${maxX.toFixed(2)}, ${maxY.toFixed(2)}]`);
if (minX > -134 || maxX < -8 || minY > -70 || maxY < 5) {
  console.error('FATAL: basemap bbox does not cover the min-zoom viewport (need lng -134..-8, lat -70..5)');
  bad++;
}
if (bad) process.exit(1);

// ---------------------------------------------------------------------------
// Residual-gap gate — runs against the TEMP output, before anything is written.
// rectangle - land - commune union = every sea-coloured area near Chile. After
// -explode each piece is one of:
//   open water   : touches the rectangle edge (Pacific/Atlantic, estuaries cut
//                  by the edge)                                   -> ignored
//   Chile water  : enclosed, but shares no vertex with the neighbour land —
//                  fjord pockets and lakes inside the commune union, or water
//                  ringed by Chilean islands that touch at a point  -> ignored
//   land water   : inside a hole of the neighbour land itself     -> ignored
//   BORDER GAP   : enclosed AND touching the neighbour land, i.e. caught
//                  between the neighbour land and the communes. These would
//                  show as sea-coloured slivers along the border.
// ---------------------------------------------------------------------------
mapshaper(
  [
    '-rectangle', `bbox=${GAP_RECT.join(',')}`, 'name=r',
    '-erase', q(TMP_OUT),
    '-erase', q(CHILE_UNION),
    '-explode',
    '-each', q('km2=this.area/1e6,ix=this.innerX,iy=this.innerY,x0=this.bounds[0],y0=this.bounds[1],x1=this.bounds[2],y1=this.bounds[3]'),
    '-o', q(TMP_HOLES),
  ],
  'residual gap check (whole border)'
);
if (!existsSync(TMP_HOLES) || statSync(TMP_HOLES).size === 0) {
  console.error('FATAL: residual gap check produced no output (expected at least the open-sea piece)');
  process.exit(1);
}
// Vertex key on a 1e-6 deg grid (~0.1 m), far finer than the 2.25e-5 deg
// quantization step, so shared vertices compare equal across both decoders.
const vkey = ([x, y]) => `${Math.round(x * 1e6)},${Math.round(y * 1e6)}`;
const landVertices = new Set();
for (const p of polys) for (const ring of p) for (const pt of ring) landVertices.add(vkey(pt));
const pieces = (JSON.parse(readFileSync(TMP_HOLES, 'utf8')).features ?? []).map((f) => {
  const g = f.geometry;
  const rings = !g ? [] : g.type === 'Polygon' ? g.coordinates : g.coordinates.flat();
  return { ...f.properties, touchesLand: rings.some((r) => r.some((pt) => landVertices.has(vkey(pt)))) };
});
const chileUnion = JSON.parse(readFileSync(CHILE_UNION, 'utf8'));
const chileHoles = [];
// mapshaper writes a dissolved layer without attributes as a GeometryCollection.
const chileGeoms = chileUnion.geometries ?? (chileUnion.features ?? []).map((f) => f.geometry);
for (const g of chileGeoms) {
  if (!g || (g.type !== 'Polygon' && g.type !== 'MultiPolygon')) continue;
  for (const poly of g.type === 'Polygon' ? [g.coordinates] : g.coordinates) chileHoles.push(...poly.slice(1));
}
if (chileGeoms.length === 0) {
  console.error('FATAL: could not read the commune union geometry for the gap classification');
  process.exit(1);
}
const landHoles = polys.flatMap((p) => p.slice(1));
const EDGE = 1e-6;
const touchesRect = (h) =>
  h.x0 <= GAP_RECT[0] + EDGE || h.y0 <= GAP_RECT[1] + EDGE || h.x1 >= GAP_RECT[2] - EDGE || h.y1 >= GAP_RECT[3] - EDGE;
const openWater = pieces.filter(touchesRect);
if (!openWater.some((h) => h.km2 > 1e6)) {
  console.error('FATAL: residual gap check found no open-sea piece — the classification cannot be trusted');
  process.exit(1);
}
const enclosed = pieces.filter((h) => !touchesRect(h));
const inAny = (rings, h) => rings.some((r) => ringHas(r, h.ix, h.iy));
const landWater = enclosed.filter((h) => inAny(landHoles, h));
const chileWater = enclosed.filter((h) => !inAny(landHoles, h) && !h.touchesLand);
const gaps = enclosed.filter((h) => !inAny(landHoles, h) && h.touchesLand).sort((a, b) => b.km2 - a.km2);
// Cross-check of the classification: a hole of the commune union can never touch the land.
const contradictions = gaps.filter((h) => inAny(chileHoles, h));
if (contradictions.length) {
  console.error(`FATAL: ${contradictions.length} piece(s) classified as border gap lie inside a hole of the commune union`);
  process.exit(1);
}
const gapTotal = gaps.reduce((s, h) => s + h.km2, 0);
const gapMax = gaps.length ? gaps[0].km2 : 0;
console.log(
  `Sea-coloured pieces near Chile: ${pieces.length} — open water ${openWater.length}, ` +
    `Chile water ${chileWater.length}, land water ${landWater.length}, BORDER GAPS ${gaps.length}`
);
console.log(`Border gaps: ${gaps.length} piece(s), ${gapTotal.toFixed(3)} km2 total, largest ${gapMax.toFixed(4)} km2`);
for (const h of gaps.slice(0, 8)) console.log(`  ${h.km2.toFixed(4)} km2 at ${h.ix.toFixed(3)},${h.iy.toFixed(3)}`);
for (const h of [...chileWater, ...landWater].sort((a, b) => b.km2 - a.km2).slice(0, 5)) {
  console.log(`  (ignored water pocket ${h.km2.toFixed(2)} km2 at ${h.ix.toFixed(3)},${h.iy.toFixed(3)})`);
}
if (gapMax > GAP_MAX_PIECE_KM2 || gapTotal > GAP_MAX_TOTAL_KM2) {
  console.error(
    `FATAL: border gaps exceed the limit (largest ${gapMax.toFixed(3)} > ${GAP_MAX_PIECE_KM2} km2 or ` +
      `total ${gapTotal.toFixed(3)} > ${GAP_MAX_TOTAL_KM2} km2) — sea-coloured slivers would show along the border. Nothing written.`
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Step 8: label anchors (interior point of each commune's largest polygon)
// ---------------------------------------------------------------------------
mapshaper([q(COMMUNES_TOPO), '-points', 'inner', '-o', q(TMP_LABELS)], 'commune label anchors (inner points)');
const communesTopo = JSON.parse(readFileSync(COMMUNES_TOPO, 'utf8'));
const communeFc = feature(communesTopo, communesTopo.objects[Object.keys(communesTopo.objects)[0]]);
const communePolys = new Map();
for (const f of communeFc.features) {
  const g = f.geometry;
  if (!g || !f.properties?.id) continue;
  communePolys.set(String(f.properties.id), g.type === 'Polygon' ? [g.coordinates] : g.coordinates);
}
const inCommune = (cut, lng, lat) =>
  (communePolys.get(cut) ?? []).some((p) => ringHas(p[0], lng, lat) && !p.slice(1).some((h) => ringHas(h, lng, lat)));
const labelPoints = {};
let badLabels = 0;
for (const f of JSON.parse(readFileSync(TMP_LABELS, 'utf8')).features ?? []) {
  const cut = f.properties?.id != null ? String(f.properties.id) : null;
  if (!cut || !f.geometry) continue;
  const [lng, lat] = f.geometry.coordinates;
  const pt = [Number(lat.toFixed(4)), Number(lng.toFixed(4))];
  if (!inCommune(cut, pt[1], pt[0])) { console.error(`FATAL: label anchor of commune ${cut} is outside its own polygon`); badLabels++; }
  labelPoints[cut] = pt; // [lat, lng]
}
const missingLabels = [...communePolys.keys()].filter((cut) => !labelPoints[cut]);
if (missingLabels.length) { console.error(`FATAL: no label anchor for ${missingLabels.length} commune(s): ${missingLabels.slice(0, 6).join(', ')}`); badLabels++; }
if (badLabels) process.exit(1);

// ---------------------------------------------------------------------------
// All gates passed — write the outputs
// ---------------------------------------------------------------------------
topo.meta.gaps = {
  pieces: gaps.length,
  totalKm2: Number(gapTotal.toFixed(3)),
  maxKm2: Number(gapMax.toFixed(4)),
  limitPieceKm2: GAP_MAX_PIECE_KM2,
  limitTotalKm2: GAP_MAX_TOTAL_KM2,
};
const finalBuf = Buffer.from(JSON.stringify(topo));
const finalGz = gzipSync(finalBuf).length;
if (finalBuf.length > RAW_MAX_BYTES || finalGz > GZIP_MAX_BYTES) {
  console.error(`FATAL: basemap exceeds budget after meta (raw ${finalBuf.length}/${RAW_MAX_BYTES}, gzip ${finalGz}/${GZIP_MAX_BYTES})`);
  process.exit(1);
}
writeFileSync(OUTPUT, finalBuf);
const sortedPoints = Object.fromEntries(Object.keys(labelPoints).sort((a, b) => Number(a) - Number(b)).map((k) => [k, labelPoints[k]]));
writeFileSync(
  LABEL_POINTS_OUT,
  JSON.stringify({
    note: 'Interior label anchor [lat, lng] per commune CUT. Built by scripts/build-basemap.mjs from communes.topo.json. Do not edit by hand.',
    communesSha256: communesSha,
    points: sortedPoints,
  }) + '\n'
);

console.log(`\nSUCCESS: ${OUTPUT}`);
console.log(`  ${finalBuf.length} bytes raw / ${finalGz} gzip — communes sha256 ${communesSha.slice(0, 12)}…`);
console.log(`SUCCESS: ${LABEL_POINTS_OUT} (${Object.keys(labelPoints).length} anchors)`);
