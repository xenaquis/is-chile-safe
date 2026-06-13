import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', es: 'es' },
      },
      // Permissive filter — rollout-aware filtering added in plan 02-06
      filter: (_url) => true,
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
