// Cliente HTTP simple sobre fetch, con manejo de token y errores.

// En producción (Docker) se inyecta la URL completa de la API vía VITE_API_URL.
// En desarrollo se usa "/api" y Vite lo redirige (proxy) al backend.
const BASE_URL: string = (import.meta.env.VITE_API_URL as string) || "/api";

// Clave usada en localStorage para el token JWT.
export const TOKEN_KEY = "ma_token";
export const USER_KEY = "ma_usuario";

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

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
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
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
};
