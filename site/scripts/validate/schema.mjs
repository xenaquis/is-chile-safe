/**
 * schema.mjs — Validate Schema.org JSON-LD in built HTML pages.
 * Stub: exits 0. Full assertions added in plan 02-06.
 *
 * When complete this will assert:
 * - Commune and region pages have <script type="application/ld+json"> with @type containing "Dataset"
 * - Place spatialCoverage is present on commune/region pages
 * - Crime-type pages have Dataset @type (no Place)
 * - temporalCoverage matches latestCompleteYear (not 2026 partial year)
 * - No XSS via commune names containing </script>
 */
console.log('schema: stub (full assertions added in plan 02-06)');
