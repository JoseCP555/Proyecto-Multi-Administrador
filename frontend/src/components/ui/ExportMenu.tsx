import { useState, useRef, useEffect } from "react";
import { Download, FileSpreadsheet, FileText, ChevronDown, Loader2 } from "lucide-react";
import { descargarArchivo } from "@/lib/download";

interface Opcion {
  label: string;
  ruta: string;
  tipo: "xlsx" | "pdf";
}

interface Props {
  opciones: Opcion[];
}

const BASE = import.meta.env.VITE_API_URL || "/api";

// Botón desplegable para descargar reportes en Excel/PDF desde el backend.
export default function ExportMenu({ opciones }: Props) {
  const [abierto, setAbierto] = useState(false);
  const [descargando, setDescargando] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const descargar = async (ruta: string) => {
    setDescargando(true);
    try {
      await descargarArchivo(`${BASE}${ruta}`);
    } catch {
      // Silencioso: se muestra si falla el menú.
    } finally {
      setDescargando(false);
      setAbierto(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setAbierto((v) => !v)}
        disabled={descargando}
        className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition"
      >
        {descargando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
        Exportar
        <ChevronDown className="w-3.5 h-3.5" />
      </button>

      {abierto && (
        <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-200 z-50 py-1">
          {opciones.map((o) => (
            <button
              key={o.ruta}
              onClick={() => descargar(o.ruta)}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition"
            >
              {o.tipo === "xlsx" ? (
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              ) : (
                <FileText className="w-4 h-4 text-danger" />
              )}
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
