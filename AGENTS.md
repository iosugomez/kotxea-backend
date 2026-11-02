# AGENTS.md — Guía para agentes de IA

Notas sobre este repositorio para agentes que vayan a hacer cambios.

## Qué es este repo

- PWA "Kotxea" para gestionar viajes en coche y pagos entre conductores (euskera/castellano).
- Todo el frontend está en un único archivo: `index.html` (HTML + CSS + JS inline). No hay build ni bundler.
- Se publica en GitHub Pages (repo `iosugomez/kotxea-backend`): lo que se pushea a `main` se despliega tal cual.
- El backend de datos está en Render (`kotxea-backend.onrender.com`).
- `datos/` contiene CSVs (`viajes.csv`, `dinero.csv`) que el backend sincroniza con commits automáticos ("Add registro", "Update ..."). No tocar a mano.
- `tests/test_remuneration_checkbox.py` es un test de **pytest** (asserts sobre strings literales de `index.html`); `save_to_github.py` es el script de sincronización del backend; `requirements.txt` es del backend (flask, pygithub, flask-cors), NO de los tests.

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

## Flujo de trabajo: push y verificación en GitHub Pages

1. **Commit y push a `main`** — no hay build ni CI: el push ES el despliegue (Pages despliega desde la rama, sin workflows de Actions).
2. **Ojo con el push rechazado**: el backend de Render commitea CSVs automáticamente a este repo ("Add registro", "Update dinero.csv", ...), así que el remoto puede tener commits nuevos. Si el push es rechazado (`! [rejected] ... fetch first`), hacer `git pull --rebase origin main` y reintentar. No suele haber conflictos porque los commits automáticos solo tocan `datos/`.
3. **Esperar el deploy de Pages**: tarda de 1 a 5 minutos aproximadamente. No hay forma de consultarlo por Actions (no existen workflows); para verificarlo, hacer fetch de la URL pública y comprobar que el cambio está presente.
4. **URL pública**: https://iosugomez.github.io/kotxea-backend/
5. **Visibilidad del cambio**:
   - Navegador: recargar la página tras el deploy (la caché HTTP de Pages puede retener la versión vieja hasta ~10 min).
   - PWA instalada en móvil: ver tabla del SW arriba — para `index.html`, al siguiente arranque de la app.

## Prueba local

- `index.html` se puede abrir directamente en el navegador: la UI funciona porque las llamadas al backend van a la URL absoluta de Render.
- El service worker NO se registra en `file://`: para probar el SW, usar la URL desplegada o un servidor local (`python -m http.server`).
- El backend de Render está en free tier y **duerme con inactividad**: el primer arranque tras un rato sin tráfico tarda ~1 min (cold start). Si un fetch a `/datos` falla o va lento al probar, reintentar antes de asumir que hay un bug.

## Tests

- Ejecutar con `pytest tests/` (requiere `pip install pytest`; NO está en `requirements.txt`, que es del backend).
- Los tests hacen asserts sobre strings literales de `index.html` (`checkboxDinero`, `registro-remuneracion-check`, `normalizarMarcadoHistorico`, ...). Si se refactoriza esa lógica, actualizar también los tests o fallarán.

## Estilo de commits

Conventional commits con prefijo `feat:`/`fix:`, descripción en euskera o castellano. Ejemplos reales:

- `feat: paginazio-kontrolak gehitu historialaren behealdean`
- `fix: SW fallback path uses scope`
- `fix: subir version de cache SW a v2 para refrescar index.html en PWA`
