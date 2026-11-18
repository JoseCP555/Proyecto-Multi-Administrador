/* Multi-Administrador · Service Worker (PWA Android/iPhone + Web Push VAPID).
 *
 * 1. Habilita la instalación como PWA en Android (Chrome/Edge) y iPhone (Safari).
 * 2. Nunca cachea rutas `/api/` ni WebSockets para garantizar datos en tiempo real.
 * 3. Ofrece una pantalla limpia sin conexión si el celular pierde señal.
 * 4. Recibe y muestra notificaciones Web Push (VAPID) incluso en segundo plano.
 */
const CACHE_NAME = "multiadmin-pwa-v1";
const PRECACHE_URLS = [
  "/manifest.webmanifest",
  "/assets/icon-192.png",
  "/assets/icon-512.png",
  "/assets/apple-touch-icon.png",
  "/assets/favicon.png",
];

const OFFLINE_HTML = `<!doctype html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>Sin conexión · Multi-Administrador</title>
  <style>
    body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
      font-family:system-ui,-apple-system,sans-serif;background:#f8fafc;color:#0f172a;padding:24px;}
    .box{max-width:360px;background:#fff;border-radius:24px;padding:28px;text-align:center;
      box-shadow:0 12px 32px rgba(15,23,42,.08);border:1px solid #e2e8f0;}
    h1{font-size:18px;margin:0 0 8px;}
    p{font-size:14px;color:#475569;margin:0 0 20px;line-height:1.5;}
    button{background:#2563eb;color:#fff;border:0;border-radius:999px;padding:11px 22px;
      font-weight:600;font-size:14px;cursor:pointer;}
  </style>
</head>
<body>
  <div class="box">
    <h1>Sin conexión a internet</h1>
    <p>Verifica tu Wi-Fi o datos móviles e intenta de nuevo para conectar con Multi-Administrador.</p>
    <button onclick="location.reload()">Reintentar</button>
  </div>
</body>
</html>`;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  // Nunca interceptar llamadas a la API, orígenes externos ni WebSockets.
  if (url.origin !== self.location.origin || url.pathname.startsWith("/api/")) {
    return;
  }

  // Navegaciones SPA: network-first con respaldo sin conexión.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(
        () =>
          new Response(OFFLINE_HTML, {
            status: 503,
            headers: { "Content-Type": "text/html; charset=utf-8" },
          }),
      ),
    );
    return;
  }

  // Estáticos propios (/assets/*): cache-first con actualización en segundo plano.
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const net = fetch(request)
          .then((resp) => {
            if (resp && resp.ok) {
              const copia = resp.clone();
              caches.open(CACHE_NAME).then((c) => c.put(request, copia)).catch(() => undefined);
            }
            return resp;
          })
          .catch(() => cached);
        return cached || net;
      }),
    );
  }
});

self.addEventListener("push", (event) => {
  let datos = {};
  try {
    datos = event.data ? event.data.json() : {};
  } catch (_) {
    datos = { titulo: "Multi-Administrador", mensaje: event.data ? event.data.text() : "" };
  }
  const titulo = datos.titulo || "Multi-Administrador";
  const opciones = {
    body: datos.mensaje || "Tienes una nueva notificación.",
    icon: "/assets/icon-192.png",
    badge: "/assets/favicon.png",
    tag: `ma-notif-${datos.id || Date.now()}`,
    renotify: true,
    data: { url: datos.url || "/dashboard/inicio", id: datos.id || null },
  };
  event.waitUntil(self.registration.showNotification(titulo, opciones));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/dashboard/inicio";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientes) => {
      for (const cliente of clientes) {
        if (new URL(cliente.url).origin === self.location.origin) {
          cliente.navigate(url);
          return cliente.focus();
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});
