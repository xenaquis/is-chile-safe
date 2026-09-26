/**
 * 19. news-dedup.mjs — FID-05 0 drops over current.json (single rule source:
 * pipeline/news/dedup.py; no JS re-implementation)
 *
 * Thin wrapper: spawns pipeline/validate_news_dedup.py (stdlib +
 * pipeline.news.dedup only) over the payload and exits with its status.
 *
 * Env override (test-only):
 *   NEWS_DEDUP_CURRENT_JSON — payload path (else
 *     site/public/data/incidents/current.json — the prebuild sync-data copy
 *     the pages read; resolved from this script's dir, not cwd).
 *
 * Exit codes: 0 PASS, 1 FAIL (drops > 0 or no python interpreter),
 * 2 missing/malformed payload (from the Python script).
 *
 * NOT registered in all.mjs until 36-09 has observed a post-ship live run at
 * 0 drops.
 */
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..', '..', '..');
const payload =
  process.env.NEWS_DEDUP_CURRENT_JSON ||
  path.join(repoRoot, 'site', 'public', 'data', 'incidents', 'current.json');
const pyScript = path.join(repoRoot, 'pipeline', 'validate_news_dedup.py');

let result = null;
for (const exe of ['python3', 'python']) {
  const r = spawnSync(exe, [pyScript, payload], { stdio: 'inherit' });
  if (r.error && r.error.code === 'ENOENT') continue;
  // Windows Store "python3" alias stub: exits 9009 without running anything.
  if (process.platform === 'win32' && r.status === 9009) continue;
  result = r;
  break;
}

if (result === null) {
  console.error('news-dedup: FAIL — no python3/python interpreter found');
  process.exit(1);
}
if (result.error) {
  console.error(`news-dedup: FAIL — could not run validator: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
