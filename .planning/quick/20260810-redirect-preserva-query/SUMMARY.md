---
quick_id: 260810-r7q
slug: redirect-preserva-query
date: 2026-08-10
status: complete
---

# SUMMARY — El redirect por idioma perdía el query string

Hallazgo LOW levantado por los revisores Opus del workflow de los chips
(`wf_d6933139-2ab`), fuera del archivo que se estaba corrigiendo.

## Defecto

`site/src/layouts/BaseLayout.astro` — el redirect por idioma de navegador (solo
páginas EN) construía la URL de destino con `esUrl.search` y `esUrl.hash`,
tomados del `<link rel="alternate" hreflang="es">`. Ese link es una ruta
canónica desnuda: nunca lleva query ni fragmento, así que ambos eran siempre
`''`.

Efecto: un visitante con navegador en español que abre
`https://ischilesafe.com/communes/?q=santiago` aterriza en `/es/comunas/` sin
el `?q=` — buscador vacío, 346 filas en vez de 1. Cualquier deep link EN
compartido con query se degradaba en silencio para el público hispanohablante,
que es justo el que el redirect intenta atender.

## Fix

Se toma el `search`/`hash` de `window.location` (el de la página actual), con
`esUrl` como fallback:

```js
var search = window.location.search || esUrl.search;
var hash = window.location.hash || esUrl.hash;
window.location.replace(esUrl.pathname + search + hash);
```

Sin cambios de comportamiento fuera del redirect: sigue gateado a `lang === 'en'`
(verificado: 0 ocurrencias en la página ES construida), sigue respetando
`lang-pref`, sigue dentro del `try/catch`, y sigue sin interpolación `{expr}`
dentro del `<script>`.

## Gates

`astro check` 0 errores · build 834 páginas · 16/16 validators · vitest 59/59 ·
snippet verificado en el HTML construido de `/communes/`.
</content>
</invoke>
