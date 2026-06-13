/**
 * sync-data.mjs — copy the static CEAD data tree into site/public so the
 * client-side map island can fetch it at runtime.
 *
 * WHY: Phase-2 pages read /data/cead/* at BUILD time (getStaticPaths via fs),
 * so the data never had to be served. The Phase-3 Leaflet island fetches
 * `/data/cead/geo/communes.topo.json`, `/data/cead/map-payload*.json`,
 * `/data/cead/meta/index.json`, and `/data/cead/comunas/{cut}.json` at RUNTIME
 * in the browser. Astro serves `public/` at the site root, so the data must
 * physically live under `public/data/` to be reachable in `astro dev` and in
 * the static `dist/` deployed to Cloudflare Pages.
 *
 * Runs as predev + prebuild (see package.json). `public/data/` is gitignored
 * and regenerated on every build (including Cloudflare's build), so the data
 * is never duplicated in version control — git keeps the single source of
 * truth at repo-root `data/`.
 *
 * Plain recursive copy (fs.cpSync) — no symlinks, which are unreliable on
 * Windows / OneDrive.
 */
import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// site/scripts -> repo-root/data/cead
const SRC = path.resolve(__dirname, '..', '..', 'data', 'cead');
// site/scripts -> site/public/data/cead
const DEST = path.resolve(__dirname, '..', 'public', 'data', 'cead');

if (!existsSync(SRC)) {
  console.error(`[sync-data] FATAL: source data tree not found at ${SRC}`);
  process.exit(1);
}

// Start clean so removed/renamed source files don't linger in public/.
rmSync(DEST, { recursive: true, force: true });
mkdirSync(path.dirname(DEST), { recursive: true });
cpSync(SRC, DEST, { recursive: true });

// Optional incidents layer (Phase 5). Copy if present; absence is fine —
// the map island handles a 404 with a graceful empty state.
const INCIDENTS_SRC = path.resolve(__dirname, '..', '..', 'data', 'incidents');
if (existsSync(INCIDENTS_SRC)) {
  const INCIDENTS_DEST = path.resolve(__dirname, '..', 'public', 'data', 'incidents');
  rmSync(INCIDENTS_DEST, { recursive: true, force: true });
  cpSync(INCIDENTS_SRC, INCIDENTS_DEST, { recursive: true });
  console.log('[sync-data] copied data/incidents -> public/data/incidents');
}

console.log(`[sync-data] copied data/cead -> public/data/cead`);
