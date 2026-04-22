const CACHE_NAME = 'wts-stock-v1';
const assets = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/templates/dashboard.html'
];

self.addEventListener('install', evt => {
  evt.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      cache.addAll(assets);
    })
  );
});

self.addEventListener('fetch', evt => {
  evt.respondWith(
    caches.match(evt.request).then(rec => {
      return rec || fetch(evt.request);
    })
  );
});