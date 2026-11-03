import { useState, useEffect, useCallback } from "react";
import { api, CONJUNTO_EVENT } from "@/lib/api";

// Hook genérico de carga de datos con estado (cargando, error, recargar).
// Si `path` es null, no consulta nada (útil para omitir endpoints según permisos).
export function useFetch<T>(path: string | null, dependencias: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Al cambiar de conjunto todos los datos en pantalla se recargan solos.
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const alCambiar = () => setVersion((v) => v + 1);
    window.addEventListener(CONJUNTO_EVENT, alCambiar);
    return () => window.removeEventListener(CONJUNTO_EVENT, alCambiar);
  }, []);

  const cargar = useCallback(async () => {
    if (!path) {
      setCargando(false);
      setData(null);
      return;
    }
    setCargando(true);
    setError(null);
    try {
      const res = await api.get<T>(path);
      setData(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  }, [path]);

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargar, version, ...dependencias]);

  return { data, setData, cargar, cargando, error };
}
