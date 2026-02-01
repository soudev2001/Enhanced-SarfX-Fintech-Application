// SarfX Service Worker - PWA Offline & Push Notifications
// Version: 2.0.0

const CACHE_VERSION = 'v2';
const STATIC_CACHE = `sarfx-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `sarfx-dynamic-${CACHE_VERSION}`;
const API_CACHE = `sarfx-api-${CACHE_VERSION}`;

const OFFLINE_URL = '/offline';
const OFFLINE_IMAGE = '/static/images/offline-placeholder.svg';

// Static assets to pre-cache (shell)
const STATIC_ASSETS = [
    '/',
    '/app/home',
    '/app/converter',
    '/app/wallets',
    '/app/transactions',
    '/offline',
    '/static/css/design-system.css',
    '/static/css/redesign-2026.css',
    '/static/css/app.css',
    '/static/js/notifications-push.js',
    '/static/images/favicon.svg',
    '/static/images/sarfx-logo.png',
    '/static/manifest.json',
];

// API endpoints to cache (with network-first strategy)
const API_CACHE_URLS = [
    '/api/rates',
    '/api/wallets/balances',
];

// Max items in dynamic cache
const DYNAMIC_CACHE_LIMIT = 50;

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker v2.0.0...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Pre-caching app shell');
                return cache.addAll(STATIC_ASSETS).catch(err => {
                    console.warn('[SW] Some assets failed to cache:', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...');

    const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('sarfx-') && !currentCaches.includes(name))
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - smart caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) return;

    // API requests - Network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request, API_CACHE));
        return;
    }

    // HTML pages - Network first, cache fallback with offline page
    if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(networkFirstWithOffline(request));
        return;
    }

    // Static assets - Cache first, network fallback
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
        return;
    }

    // Dynamic content - Stale while revalidate
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
});

// Check if URL is a static asset
function isStaticAsset(pathname) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
    return staticExtensions.some(ext => pathname.endsWith(ext)) || pathname.startsWith('/static/');
}

// Cache first strategy (for static assets)
async function cacheFirstStrategy(request, cacheName) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Cache first failed:', error);
        // Return placeholder for images
        if (request.destination === 'image') {
            return caches.match(OFFLINE_IMAGE);
        }
        return new Response('Offline', { status: 503 });
    }
}

// Network first strategy (for API calls)
async function networkFirstStrategy(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network first - falling back to cache');
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return new Response(JSON.stringify({ error: 'Offline', cached: false }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Network first with offline page fallback (for navigation)
async function networkFirstWithOffline(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            trimCache(DYNAMIC_CACHE, DYNAMIC_CACHE_LIMIT);
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Navigation offline - trying cache');
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return caches.match(OFFLINE_URL) || new Response('Offline', {
            status: 503,
            headers: { 'Content-Type': 'text/html' }
        });
    }
}

// Stale while revalidate strategy
async function staleWhileRevalidate(request, cacheName) {
    const cachedResponse = await caches.match(request);

    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            const cache = caches.open(cacheName);
            cache.then(c => c.put(request, networkResponse.clone()));
            trimCache(cacheName, DYNAMIC_CACHE_LIMIT);
        }
        return networkResponse;
    }).catch(() => cachedResponse);

    return cachedResponse || fetchPromise;
}

// Trim cache to max size
async function trimCache(cacheName, maxItems) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    if (keys.length > maxItems) {
        await cache.delete(keys[0]);
        trimCache(cacheName, maxItems);
    }
}

// Push notification event
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    let data = {
        title: 'SarfX',
        body: 'Vous avez une nouvelle notification',
        icon: '/static/images/favicon.svg',
        badge: '/static/images/badge.png',
        data: { url: '/app/home' }
    };

    if (event.data) {
        try {
            data = { ...data, ...event.data.json() };
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon || '/static/images/favicon.svg',
        badge: data.badge || '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: data.data || {},
        actions: data.actions || [
            { action: 'open', title: 'Ouvrir' },
            { action: 'close', title: 'Fermer' }
        ],
        requireInteraction: data.requireInteraction || false,
        tag: data.tag || 'sarfx-notification',
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked');

    event.notification.close();

    const action = event.action;
    const notificationData = event.notification.data || {};

    if (action === 'close') {
        return;
    }

    // Open or focus the app
    const urlToOpen = notificationData.url || '/app/home';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if there's already a window open
                for (const client of clientList) {
                    if (client.url.includes('/app') && 'focus' in client) {
                        client.navigate(urlToOpen);
                        return client.focus();
                    }
                }

                // Open a new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
    console.log('[SW] Notification closed');

    // Track notification dismissal (optional analytics)
    const notificationData = event.notification.data || {};

    // Could send analytics data here
});

// Background sync event (for offline actions)
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync event:', event.tag);

    if (event.tag === 'sync-notifications') {
        event.waitUntil(syncNotifications());
    }
});

// Sync notifications when back online
async function syncNotifications() {
    try {
        const response = await fetch('/api/notifications/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            console.log('[SW] Notifications synced successfully');
        }
    } catch (error) {
        console.error('[SW] Sync failed:', error);
    }
}

// Message event - communication with main thread
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

console.log('[SW] Service Worker loaded');
