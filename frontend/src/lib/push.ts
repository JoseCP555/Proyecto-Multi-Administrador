/** Registro del service worker y suscripción Web Push (VAPID). */
import { api } from "@/lib/api";

export interface ConfigNotificaciones {
  vapid_publico: string | null;
  push_configurado: boolean;
  correo_configurado: boolean;
}

export function soportaPush(): boolean {
  return typeof window !== "undefined"
    && "serviceWorker" in navigator
    && "PushManager" in window
    && "Notification" in window;
}

/** Convierte la clave pública VAPID (base64url) al formato que pide PushManager. */
export function urlBase64AUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const crudo = atob(base64);
  const salida = new Uint8Array(crudo.length);
  for (let i = 0; i < crudo.length; i += 1) salida[i] = crudo.charCodeAt(i);
  return salida;
}

export async function registrarServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) return null;
  try {
    return await navigator.serviceWorker.register("/sw.js", { scope: "/" });
  } catch (e) {
    console.warn("[push] no se pudo registrar el service worker", e);
    return null;
  }
}

export async function estadoPush(): Promise<{
  permitido: boolean;
  suscrito: boolean;
  endpoint: string | null;
}> {
  if (!soportaPush()) return { permitido: false, suscrito: false, endpoint: null };
  const permitido = Notification.permission === "granted";
  try {
    // getRegistration() en vez de ready: `ready` queda pendiente para siempre
    // si todavía no hay service worker registrado.
    const reg = await navigator.serviceWorker.getRegistration();
    const sub = reg ? await reg.pushManager.getSubscription() : null;
    return { permitido, suscrito: !!sub, endpoint: sub?.endpoint ?? null };
  } catch {
    return { permitido, suscrito: false, endpoint: null };
  }
}

/** Pide permiso, se suscribe y guarda la suscripción en el backend. */
export async function activarPush(clavePublica: string): Promise<{ ok: boolean; mensaje: string }> {
  if (!soportaPush()) return { ok: false, mensaje: "Este navegador no admite notificaciones push." };
  if (!clavePublica) return { ok: false, mensaje: "Falta la clave VAPID pública en el servidor." };

  const permiso = await Notification.requestPermission();
  if (permiso !== "granted") {
    return { ok: false, mensaje: "Permiso denegado. Actívalo en los ajustes del navegador." };
  }
  try {
    await registrarServiceWorker();
    // Esperar a que el SW esté ACTIVO: `pushManager.subscribe` falla con
    // "no active Service Worker" si se llama justo después de register().
    await Promise.race([
      navigator.serviceWorker.ready,
      new Promise((resolver) => setTimeout(resolver, 4000)),
    ]);
    const reg = await navigator.serviceWorker.getRegistration();
    if (!reg) return { ok: false, mensaje: "No se pudo registrar el service worker." };
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64AUint8Array(clavePublica),
      });
    } else {
      // Si la clave VAPID cambió, hay que renovar la suscripción.
      const claveActual = sub.options?.applicationServerKey;
      if (claveActual) {
        const esperada = urlBase64AUint8Array(clavePublica);
        const actual = new Uint8Array(claveActual);
        if (actual.length !== esperada.length || actual.some((b, i) => b !== esperada[i])) {
          await sub.unsubscribe();
          sub = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: esperada,
          });
        }
      }
    }
    await api.post("/notificaciones/suscripcion", sub.toJSON());
    return { ok: true, mensaje: "Avisos del navegador activados." };
  } catch (e) {
    return { ok: false, mensaje: `No se pudo activar: ${(e as Error).message}` };
  }
}

/** Cancela la suscripción local y la del servidor. */
export async function desactivarPush(): Promise<void> {
  if (!soportaPush()) return;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    if (!reg) return;
    const sub = await reg.pushManager.getSubscription();
    if (sub) {
      const endpoint = sub.endpoint;
      await sub.unsubscribe();
      await api.post("/notificaciones/suscripcion/desactivar", { endpoint });
    }
  } catch (e) {
    console.warn("[push] no se pudo desactivar", e);
  }
}

/**
 * Aviso en pantalla cuando NO hay suscripción Web Push activa. Así, incluso
 * sin VAPID configurado, el usuario recibe algo real mientras tiene la
 * pestaña abierta. El service worker se encarga cuando sí hay suscripción.
 */
export function mostrarAvisoLocal(titulo: string, mensaje: string, url: string): void {
  if (!soportaPush() || Notification.permission !== "granted") return;
  try {
    const n = new Notification(titulo, {
      body: mensaje,
      icon: "/assets/logo.png",
      tag: `ma-local-${Date.now()}`,
    });
    n.onclick = () => {
      window.focus();
      window.location.href = url;
      n.close();
    };
  } catch {
    /* Algunos navegadores exigen usar registration.showNotification. */
    navigator.serviceWorker?.getRegistration().then((reg) =>
      reg?.showNotification(titulo, { body: mensaje, icon: "/assets/logo.png", data: { url } }),
    );
  }
}
