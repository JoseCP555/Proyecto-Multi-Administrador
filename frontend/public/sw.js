/* Multi-Administrador · Service Worker de notificaciones push.
 *
 * Se registra desde src/lib/push.ts. Recibe los mensajes Web Push que envía
 * el backend con pywebpush/VAPID y los muestra aunque la pestaña esté en
 * segundo plano. Al hacer clic abre (o enfoca) la ruta indicada.
 */
self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
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
    icon: "/assets/logo.png",
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
