import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
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

  // Al montar (si hay sesión activa), refresca el usuario y sus permisos
  // desde el backend (/me) para mantenerlos alineados al rol vigente.
  useEffect(() => {
    if (!token) return;
    api
      .get<Usuario>("/me")
      .then((actualizado) => {
        // conserva el token y actualiza usuario+permisos en localStorage.
        setAuth(token, actualizado);
        setUsuario(actualizado);
      })
      .catch(() => {
        // Si el token ya no es válido, se cierra sesión.
        if (getToken() === token) logout();
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AuthContext.Provider value={{ usuario, token, cargando, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
