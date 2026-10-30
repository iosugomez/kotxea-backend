// Service Worker para Kotxea PWA
// Cachea archivos estaticos para funcionamiento offline
// Las peticiones al backend de Render SIEMPRE van a red

const CACHE_NAME = 'kotxea-cache-v1';

// Obtener el path base desde el scope del Service Worker
// Si la app esta en /kotxea-backend/, el scope es /kotxea-backend/
const SW_SCOPE = self.registration.scope;

const STATIC_ASSETS = [
  SW_SCOPE,
  SW_SCOPE + 'index.html',
  SW_SCOPE + 'manifest.json',
  SW_SCOPE + 'icons/icon-192.png',
  SW_SCOPE + 'icons/icon-512.png',
  SW_SCOPE + 'icons/icon-apple.png',
  SW_SCOPE + 'icons/icon-favicon.ico'
];

const BACKEND_URL = 'kotxea-backend.onrender.com';

// ===== INSTALACION: precarga archivos estaticos =====
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).catch((err) => {
      // Si falla la precarga, el SW aun se instala
      console.log('SW install: some assets not cached', err);
    })
  );
  // Forzar activacion inmediata
  self.skipWaiting();
});

// ===== ACTIVACION: limpia caches viejos =====
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
      );
    })
  );
  // Tomar control inmediato de las paginas abiertas
  self.clients.claim();
});

// ===== FETCH: estrategia inteligente =====
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Las peticiones al backend SIEMPRE van a red (nunca cache)
  if (url.hostname.includes(BACKEND_URL)) {
    event.respondWith(
      fetch(event.request).catch(() => {
        // Si no hay red, devolver respuesta vacia de error
        return new Response(JSON.stringify({ error: 'Sin conexion' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Para archivos estaticos: cache-first con fallback a red
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Solo cachear respuestas validas y del mismo origen
        if (response && response.status === 200 && response.type === 'basic') {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      });
    }).catch(() => {
      // Si todo falla, servir la pagina principal para rutas SPA
      return caches.match(SW_SCOPE + 'index.html');
    })
  );
});
