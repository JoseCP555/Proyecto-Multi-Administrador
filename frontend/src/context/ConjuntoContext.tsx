import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { api, setConjuntoActivo, getConjuntoActivo } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { Conjunto } from "@/types";

interface ConjuntoContextValue {
  /** Todos los conjuntos a cargo del usuario (CA-07.1). */
  conjuntos: Conjunto[];
  /** Conjunto seleccionado en este momento (contexto de trabajo). */
  activo: Conjunto | null;
  cargando: boolean;
  error: string | null;
  recargar: () => Promise<void>;
  /** Cambia de conjunto sin cerrar sesión (CA-07.2). */
  seleccionar: (id: number) => void;
  /** ¿Puede crear/editar/eliminar conjuntos? */
  puedeCrear: boolean;
  puedeEditar: boolean;
  puedeEliminar: boolean;
}

const ConjuntoContext = createContext<ConjuntoContextValue | undefined>(undefined);

export function ConjuntoProvider({ children }: { children: ReactNode }) {
  const { token, usuario } = useAuth();
  const [conjuntos, setConjuntos] = useState<Conjunto[]>([]);
  const [activo, setActivo] = useState<Conjunto | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    if (!token) {
      setConjuntos([]);
      setActivo(null);
      return;
    }
    setCargando(true);
    setError(null);
    try {
      const lista = await api.get<Conjunto[]>("/conjuntos");
      setConjuntos(lista);

      // Se respeta el conjunto guardado en el navegador (persistencia al
      // navegar entre módulos, CA-07.6) siempre que siga disponible.
      const guardado = getConjuntoActivo();
      const encontrado =
        (guardado && lista.find((c) => c.id === guardado)) ||
        lista.find((c) => c.id === (usuario as { id_conjunto?: number } | null)?.id_conjunto) ||
        lista[0] ||
        null;
      setActivo(encontrado);
      setConjuntoActivo(encontrado ? encontrado.id : null);
    } catch (e) {
      setError((e as Error).message);
      setConjuntos([]);
      setActivo(null);
    } finally {
      setCargando(false);
    }
  }, [token, usuario]);

  // Cargar al iniciar sesión / al montar con sesión activa.
  useEffect(() => {
    recargar();
  }, [recargar]);

  const seleccionar = useCallback(
    (id: number) => {
      const destino = conjuntos.find((c) => c.id === id);
      if (!destino) return;
      setActivo(destino);
      setConjuntoActivo(destino.id); // dispara la recarga de datos en pantalla
    },
    [conjuntos],
  );

  const permisos = usuario?.permisos ?? [];

  return (
    <ConjuntoContext.Provider
      value={{
        conjuntos,
        activo,
        cargando,
        error,
        recargar,
        seleccionar,
        puedeCrear: permisos.includes("conjuntos.crear"),
        puedeEditar: permisos.includes("conjuntos.editar"),
        puedeEliminar: permisos.includes("conjuntos.eliminar"),
      }}
    >
      {children}
    </ConjuntoContext.Provider>
  );
}

export function useConjunto(): ConjuntoContextValue {
  const ctx = useContext(ConjuntoContext);
  if (!ctx) throw new Error("useConjunto debe usarse dentro de ConjuntoProvider");
  return ctx;
}
