// Cliente HTTP simple sobre fetch, con manejo de token y errores.

// Resuelve la URL base de la API de forma segura tanto en escritorio como en
// celulares (Android / iPhone). Si el bundle se compiló con VITE_API_URL apuntando
// a localhost/127.0.0.1 pero el usuario abre la app desde una IP de la red Wi-Fi
// o un dominio HTTPS en su celular, se usa automáticamente "/api" (proxy de nginx).
function resolverApiBase(): string {
  const envUrl = ((import.meta.env.VITE_API_URL as string) || "").trim().replace(/\/+$/, "");
  if (!envUrl) return "/api";
  if (typeof window !== "undefined") {
    const hostActual = window.location.hostname;
    const esHostLocal = hostActual === "localhost" || hostActual === "127.0.0.1" || hostActual === "::1";
    const envEsLocal = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(envUrl);
    if (!esHostLocal && envEsLocal) {
      return "/api";
    }
  }
  return envUrl;
}

/** Base de la API. Se exporta para que todos los módulos (subidas multipart,
 *  descargas, logos y WebSockets) usen la misma URL compatible con móvil. */
export const API_BASE: string = resolverApiBase();

// Clave usada en localStorage para el token JWT.
export const TOKEN_KEY = "ma_token";
export const USER_KEY = "ma_usuario";
export const CONJUNTO_KEY = "ma_conjunto";

// --- Conjunto activo (multi-copropiedad) --------------------------------
// Se envía al backend en la cabecera `X-Conjunto-Id` de TODAS las peticiones,
// de modo que cada módulo devuelve solo los datos del conjunto seleccionado.
// Cambiarlo no requiere volver a iniciar sesión (HU-07 / CA-07.2).
let conjuntoActivoId: number | null = (() => {
  const guardado = typeof localStorage !== "undefined" ? localStorage.getItem(CONJUNTO_KEY) : null;
  return guardado ? Number(guardado) || null : null;
})();

export const CONJUNTO_EVENT = "ma:conjunto-cambiado";

export function getConjuntoActivo(): number | null {
  return conjuntoActivoId;
}

export function setConjuntoActivo(id: number | null) {
  conjuntoActivoId = id;
  if (id === null) localStorage.removeItem(CONJUNTO_KEY);
  else localStorage.setItem(CONJUNTO_KEY, String(id));
  // Avisa a la app para que los datos en pantalla se vuelvan a consultar.
  window.dispatchEvent(new Event(CONJUNTO_EVENT));
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setAuth(token: string, usuario: unknown) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(usuario));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(method: string, path: string, body?: unknown, opciones?: { sinAuth?: boolean }): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = opciones?.sinAuth ? null : getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  // Contexto de trabajo: el backend filtra por este conjunto.
  if (!opciones?.sinAuth && conjuntoActivoId) headers["X-Conjunto-Id"] = String(conjuntoActivoId);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    // fetch lanza TypeError cuando no hay conexión, CORS o backend caído.
    throw new ApiError(
      "No se pudo conectar con el servidor. Verifica que el backend esté en marcha y que VITE_API_URL apunte al puerto correcto.",
      0
    );
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (res.status === 401) {
    clearAuth();
  }
  if (res.status === 403 && !opciones?.sinAuth && typeof window !== "undefined") {
    // UH-08: si cambiaron los permisos del rol en el backend, sincronizamos /me al instante.
    window.dispatchEvent(new Event("ma:auth-sync"));
  }
  if (!res.ok) {
    const detail =
      (data as { detail?: string })?.detail ||
      (data as { mensaje?: string })?.mensaje ||
      `Error ${res.status}`;
    throw new ApiError(detail, res.status);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  /** POST sin enviar el token de sesión (flujos públicos: registro, login, códigos). */
  postPublico: <T>(path: string, body?: unknown) => request<T>("POST", path, body, { sinAuth: true }),
  /** GET sin enviar el token de sesión (flujos públicos: listar conjuntos en el registro). */
  getPublico: <T>(path: string) => request<T>("GET", path, undefined, { sinAuth: true }),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
};
