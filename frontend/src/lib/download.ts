import { getToken } from "./api";

// Descarga un archivo usando el endpoint del backend (con autenticación).
// Si el endpoint es público (no requiere token), igual se envía si hay sesión.
export async function descargarArchivo(ruta: string, nombreArchivo?: string) {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(ruta, { headers });
  if (!res.ok) throw new Error("No se pudo descargar el archivo.");

  const blob = await res.blob();

  // Intentar obtener el nombre del header Content-Disposition.
  let nombre = nombreArchivo || "descarga";
  const disp = res.headers.get("Content-Disposition") || "";
  const match = disp.match(/filename\*?=(?:UTF-8''|")?([^";]+)/i);
  if (match) nombre = decodeURIComponent(match[1]).replace(/"/g, "");

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
