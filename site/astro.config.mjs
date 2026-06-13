import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Rollout-gated sitemap filter (SEO-02, T-02-16, T-02-17)
// ---------------------------------------------------------------------------
// Build an ENABLED_SLUGS set by joining rollout.json CUT codes with index.json slugs.
// When ROLLOUT_ALL=true, all URLs are included (full 346-commune build gate).
// ---------------------------------------------------------------------------

const rolloutPath = path.resolve(__dirname, 'src', 'config', 'rollout.json');
const rollout = JSON.parse(readFileSync(rolloutPath, 'utf-8'));
const enabledCuts = new Set(rollout.enabled); // e.g. Set { '13101', '13119', ... }

const indexPath = path.resolve(__dirname, '..', 'data', 'cead', 'meta', 'index.json');
const indexEntries = JSON.parse(readFileSync(indexPath, 'utf-8'));

/** Slugs for rollout-enabled communes */
const ENABLED_SLUGS = new Set(
  indexEntries
    .filter((c) => enabledCuts.has(c.cut))
    .map((c) => c.slug)
);

const ROLLOUT_ALL = process.env.ROLLOUT_ALL === 'true';

/**
 * Sitemap filter — called with a full URL string by @astrojs/sitemap.
 *
 * Include:
 *   - home pages (/ and /es/)
 *   - all region pages (/region/* and /es/region/*)
 *   - all crime-type pages (/crime/* and /es/delito/*)
 *   - commune pages only when their slug is in ENABLED_SLUGS
 *     (or when ROLLOUT_ALL=true)
 *
 * Exclude:
 *   - non-rollout commune pages (true 404 per D-26; filter protects crawl budget)
 */
function sitemapFilter(url) {
  if (ROLLOUT_ALL) return true;

  // Home pages
  if (url === 'https://ischilesafe.com/' || url === 'https://ischilesafe.com/es/') {
    return true;
  }

  // Region pages: /region/{slug}/ or /es/region/{slug}/
  if (/\/region\/[^/]+\/$/.test(url)) return true;

  // Crime pages: /crime/{slug}/ or /es/delito/{slug}/
  if (/\/(crime|delito)\/[^/]+\/$/.test(url)) return true;

  // Commune pages: extract slug from /commune/{slug}/ or /es/comuna/{slug}/
  const communeMatch = url.match(/\/(commune|comuna)\/([^/]+)\//);
  if (communeMatch) {
    const slug = communeMatch[2];
    return ENABLED_SLUGS.has(slug);
  }

  // Map pages always included
  if (/\/map\/$/.test(url) || /\/es\/mapa\/$/.test(url)) return true;

  // All other pages included by default (404, etc.)
  return true;
}

export default defineConfig({
  site: 'https://ischilesafe.com',
  i18n: {
    locales: ['en', 'es'],
    defaultLocale: 'en',
    routing: {
      prefixDefaultLocale: false,
    },
  },
  integrations: [
    react(),
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', es: 'es' },
      },
      filter: sitemapFilter,
    }),
  ],
  vite: {
    resolve: {
      alias: {
        '@data': path.resolve(__dirname, '..', 'data'),
      },
    },
  },
});
