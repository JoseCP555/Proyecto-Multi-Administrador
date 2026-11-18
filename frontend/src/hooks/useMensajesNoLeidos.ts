import { useCallback, useEffect, useState } from "react";
import { api, CONJUNTO_EVENT } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { tienePermiso } from "@/lib/permisos";
import type { ResumenNoLeidos } from "@/types";

export const MENSAJES_EVENT = "ma:mensajes-actualizados";

/** Dispara una actualización inmediata del contador de mensajes sin leer. */
export function notificarCambioMensajes() {
  window.dispatchEvent(new Event(MENSAJES_EVENT));
}

/**
 * Mantiene sincronizado el contador de mensajes directos sin leer en Sidebar
 * y Topbar, respetando permisos (`mensajes.ver`) y el conjunto activo.
 */
export function useMensajesNoLeidos() {
  const { token, usuario } = useAuth();
  const puedeVer = Boolean(token) && tienePermiso(usuario, "mensajes.ver");
  const [resumen, setResumen] = useState<ResumenNoLeidos>({
    no_leidos: 0,
    conversaciones_sin_leer: 0,
  });

  const refrescar = useCallback(async () => {
    if (!puedeVer) {
      setResumen({ no_leidos: 0, conversaciones_sin_leer: 0 });
      return;
    }
    try {
      const data = await api.get<ResumenNoLeidos>("/mensajes/no-leidos");
      if (data) setResumen(data);
    } catch {
      // Sin conexión o sin permisos: conservamos el último valor.
    }
  }, [puedeVer]);

  useEffect(() => {
    refrescar();
    if (!puedeVer) return;
    const intervalo = window.setInterval(refrescar, 20_000);
    const alCambiar = () => {
      refrescar();
    };
    window.addEventListener(CONJUNTO_EVENT, alCambiar);
    window.addEventListener(MENSAJES_EVENT, alCambiar);
    window.addEventListener("focus", alCambiar);
    return () => {
      window.clearInterval(intervalo);
      window.removeEventListener(CONJUNTO_EVENT, alCambiar);
      window.removeEventListener(MENSAJES_EVENT, alCambiar);
      window.removeEventListener("focus", alCambiar);
    };
  }, [puedeVer, refrescar]);

  return {
    noLeidos: resumen.no_leidos,
    conversacionesSinLeer: resumen.conversaciones_sin_leer,
    refrescar,
  };
}
