/// <reference types="astro/client" />

// ROLLOUT_ALL=true env flag overrides rollout.json allowlist to build all 346 commune pages.
// Set this flag in CI when ready to deploy the full site.
// Without the flag, only the 12 priority communes in src/config/rollout.json are built.
interface ImportMetaEnv {
  readonly ROLLOUT_ALL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
