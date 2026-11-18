import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { api, getToken, getStoredUser, setAuth, clearAuth } from "@/lib/api";
import type { Usuario } from "@/types";

interface AuthContextValue {
  usuario: Usuario | null;
  token: string | null;
  cargando: boolean;
  login: (correo: string, password: string) => Promise<Usuario>;
  logout: () => void;
  /** Actualiza inmediatamente el usuario en memoria y localStorage (UH-20). */
  actualizarUsuario: (u: Usuario) => void;
  /** Consulta /me para sincronizar rol y permisos vigentes (UH-08). */
  refrescarUsuario: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface LoginResponse {
  ok: boolean;
  access_token: string;
  usuario: Usuario;
  mensaje?: string;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(() => getStoredUser());
  const [token, setToken] = useState<string | null>(() => getToken());
  const [cargando, setCargando] = useState(false);
  const ultimaSincRef = useRef(0);

  const login = useCallback(async (correo: string, password: string) => {
    setCargando(true);
    try {
      const res = await api.post<LoginResponse>("/login", { correo, password });
      if (!res.ok) {
        throw new Error(res.mensaje || "Credenciales incorrectas.");
      }
      setAuth(res.access_token, res.usuario);
      setToken(res.access_token);
      setUsuario(res.usuario);
      return res.usuario;
    } finally {
      setCargando(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setToken(null);
    setUsuario(null);
  }, []);

  const actualizarUsuario = useCallback((actualizado: Usuario) => {
    const tk = getToken();
    if (tk) {
      setAuth(tk, actualizado);
    }
    setUsuario(actualizado);
  }, []);

  const refrescarUsuario = useCallback(async () => {
    const tk = getToken();
    if (!tk) return;
    ultimaSincRef.current = Date.now();
    try {
      const actualizado = await api.get<Usuario>("/me");
      if (getToken() === tk) {
        setAuth(tk, actualizado);
        setUsuario(actualizado);
      }
    } catch {
      // Si el token ya no es válido (401 limpia localStorage), cerramos sesión local.
      if (!getToken()) {
        setToken(null);
        setUsuario(null);
      }
    }
  }, []);

  // UH-27: la sesión expira tras 30 minutos de inactividad. Cualquier
  // interacción del usuario reinicia el contador; al agotarse se cierra la
  // sesión y se vuelve al login avisando el motivo.
  useEffect(() => {
    if (!token) return;

    const LIMITE_MS = 30 * 60 * 1000; // 30 minutos
    let temporizador: number;

    const expirar = () => {
      try {
        api.post("/logout").catch(() => undefined);
      } catch {
        // Sin conexión: igual se limpia la sesión local.
      }
      clearAuth();
      setToken(null);
      setUsuario(null);
      window.location.href = "/login?sesion=expirada";
    };

    const reiniciar = () => {
      window.clearTimeout(temporizador);
      temporizador = window.setTimeout(expirar, LIMITE_MS);
    };

    const eventos: (keyof WindowEventMap)[] = [
      "mousemove", "mousedown", "keydown", "scroll", "touchstart", "click",
    ];
    eventos.forEach((e) => window.addEventListener(e, reiniciar, { passive: true }));
    reiniciar();

    return () => {
      window.clearTimeout(temporizador);
      eventos.forEach((e) => window.removeEventListener(e, reiniciar));
    };
  }, [token]);

  // UH-08: sincroniza usuario, rol y permisos desde /me al montar, al volver a
  // la pestaña, cada 30 s y ante cualquier 403 (`ma:auth-sync`).
  useEffect(() => {
    if (!token) return;

    refrescarUsuario();

    const sincronizarSiToca = () => {
      if (document.visibilityState === "hidden") return;
      if (Date.now() - ultimaSincRef.current < 10_000) return;
      refrescarUsuario();
    };

    const forzarSinc = () => {
      refrescarUsuario();
    };

    const intervalo = window.setInterval(sincronizarSiToca, 30_000);
    window.addEventListener("focus", sincronizarSiToca);
    document.addEventListener("visibilitychange", sincronizarSiToca);
    window.addEventListener("ma:auth-sync", forzarSinc);

    return () => {
      window.clearInterval(intervalo);
      window.removeEventListener("focus", sincronizarSiToca);
      document.removeEventListener("visibilitychange", sincronizarSiToca);
      window.removeEventListener("ma:auth-sync", forzarSinc);
    };
  }, [token, refrescarUsuario]);

  return (
    <AuthContext.Provider
      value={{ usuario, token, cargando, login, logout, actualizarUsuario, refrescarUsuario }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
