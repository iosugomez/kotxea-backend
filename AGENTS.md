# AGENTS.md — Guía para agentes de IA

Notas sobre este repositorio para agentes que vayan a hacer cambios.

## Qué es este repo

- PWA "Kotxea" para gestionar viajes en coche y pagos entre conductores (euskera/castellano).
- Todo el frontend está en un único archivo: `index.html` (HTML + CSS + JS inline). No hay build ni bundler.
- Se publica en GitHub Pages (repo `iosugomez/kotxea-backend`): lo que se pushea a `main` se despliega tal cual.
- El backend de datos está en Render (`kotxea-backend.onrender.com`).
- `datos/` contiene CSVs (`viajes.csv`, `dinero.csv`) que el backend sincroniza con commits automáticos ("Add registro", "Update ..."). No tocar a mano.
- `tests/test_remuneration_checkbox.py` es un test de Playwright; `save_to_github.py` es el script de sincronización del backend.

## Service Worker (`sw.js`) — IMPORTANTE

La app se instala en móviles como PWA y `sw.js` controla la caché. Reglas al hacer cambios:

| Archivo cambiado | ¿Hay que tocar `sw.js`? | Motivo |
|---|---|---|
| `index.html` | **NO** | Estrategia *network-first* con `cache: 'no-cache'`: los móviles descargan la versión nueva la próxima vez que abran la app |
| `manifest.json`, `icons/` | **SÍ: subir `CACHE_NAME`** (p. ej. `'kotxea-cache-v3'` → `'kotxea-cache-v4'`) | Estrategia *cache-first*: sin bump de versión, los móviles seguirían mostrando los iconos viejos indefinidamente |
| El propio `sw.js` | — | Los usuarios deben abrir la app, cerrarla del todo y volver a abrirla para que se instale el SW nuevo. `skipWaiting()` y `clients.claim()` ya fuerzan la activación inmediata, no hace falta más |

Otras notas del SW:

- Las peticiones al backend de Render SIEMPRE van a la red (nunca cache); sin conexión devuelven un 503.
- El `activate` borra todas las cachés cuyo nombre no sea `CACHE_NAME` actual — de ahí que el bump de versión refresque todo.
- Historial del problema: antes `index.html` era cache-first y cada cambio quedaba invisible en los móviles hasta subir la versión de caché (ver commits `0eaec92` y `a2b66d3`). Se resolvió con red-first para HTML.

## Despliegue

- Sin build: push a `main` = deploy en GitHub Pages.
- GitHub Pages cachea HTTP ~10 minutos, pero el SW ya lo evita con `cache: 'no-cache'` para el HTML. Los cambios en `index.html` son visibles en el móvil al siguiente arranque de la app (esperando el deploy de Pages).

## Estilo de commits

Conventional commits con prefijo `feat:`/`fix:`, descripción en euskera o castellano. Ejemplos reales:

- `feat: paginazio-kontrolak gehitu historialaren behealdean`
- `fix: SW fallback path uses scope`
- `fix: subir version de cache SW a v2 para refrescar index.html en PWA`
