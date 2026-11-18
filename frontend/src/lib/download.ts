import { getConjuntoActivo, getToken } from "./api";

// Descarga un archivo usando el endpoint del backend (con autenticación y
// contexto del conjunto activo en X-Conjunto-Id).
export async function descargarArchivo(ruta: string, nombreArchivo?: string) {
  const token = getToken();
  const cid = getConjuntoActivo();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (cid) headers["X-Conjunto-Id"] = String(cid);

  const res = await fetch(ruta, { headers });
  if (!res.ok) {
    let detalle = "No se pudo descargar el archivo.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string" && data.detail) detalle = data.detail;
    } catch {
      /* respuesta sin JSON */
    }
    throw new Error(detalle);
  }

  const blob = await res.blob();

  // Intentar obtener el nombre real del header Content-Disposition.
  let nombre = nombreArchivo || "descarga";
  const disp = res.headers.get("Content-Disposition") || "";
  const matchUtf8 = disp.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
  const matchSimple = disp.match(/filename\s*=\s*"?([^";]+)"?/i);
  if (matchUtf8) nombre = decodeURIComponent(matchUtf8[1].trim());
  else if (matchSimple) nombre = decodeURIComponent(matchSimple[1].trim());

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Retardo breve para asegurar compatibilidad en Safari iOS / Android al disparar la descarga.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
