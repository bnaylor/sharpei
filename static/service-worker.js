const CACHE_NAME = 'sharpei-v2';
const ASSETS = [
  '/',
  '/static/app.js',
  '/static/style.css',
  '/assets/icon_large.jpg',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/alpinejs@3.14.3/dist/cdn.min.js',
  'https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js',
  'https://cdn.jsdelivr.net/npm/marked@15.0.6/marked.min.js',
  'https://cdn.jsdelivr.net/npm/dompurify@3.2.3/dist/purify.min.js'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Force the waiting service worker to become the active service worker immediately
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('activate', event => {
  // Clear old caches that don't match the current CACHE_NAME
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('ServiceWorker: Clearing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // Take control of all pages immediately
  );
});

self.addEventListener('fetch', event => {
  // For API calls, always go to network
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME)
      .then(cache => cache.match(event.request))
      .then(response => response || fetch(event.request))
      .catch(() => {
        // Fallback or just let it fail gracefully
        return new Response('Network error occurred', {
          status: 408,
          statusText: 'Network error occurred'
        });
      })
  );
});
