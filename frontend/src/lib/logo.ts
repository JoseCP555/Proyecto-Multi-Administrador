// Logo oficial empaquetado por Vite (funciona en dev, build y Docker sin depender de /public).
import logoUrl from "@/assets/logo.png";
import { API_BASE } from "@/lib/api";

export default logoUrl;

const BASE = API_BASE.replace(/\/+$/, "");

/** Construye una URL de la API respetando `/api` (proxy) o una URL absoluta. */
export function urlApi(ruta: string): string {
  return `${BASE}/${ruta.replace(/^\/+/, "")}`;
}

/**
 * Resuelve el valor guardado en `conjuntos.logo` a algo que un <img> pueda
 * mostrar. Acepta rutas relativas del backend (`archivos/logos/x.png`), URLs
 * absolutas y data URIs (por si en el futuro se guarda la imagen en la BD).
 */
export function urlLogo(logo?: string | null): string | null {
  if (!logo) return null;
  if (/^(https?:\/\/|data:|blob:)/i.test(logo)) return logo;
  return urlApi(logo);
}
