import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useFetch } from "@/hooks/useFetch";
import { useAuth } from "@/context/AuthContext";
import { tienePermiso } from "@/lib/permisos";
import type { Evento } from "@/types";

const MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const DIAS = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"];

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** Franja semanal de calendario (día actual resaltado en azul). Marca días con eventos si el rol puede verlos. */
export default function MiniCalendario() {
  const { usuario } = useAuth();
  const hoy = new Date();
  const [inicio, setInicio] = useState(() => {
    const d = new Date(hoy); const dow = (d.getDay() + 6) % 7; d.setDate(d.getDate() - dow); d.setHours(0,0,0,0); return d;
  });
  const [sel, setSel] = useState(iso(hoy));
  const { data: eventos } = useFetch<Evento[]>(tienePermiso(usuario, "eventos.ver") ? "/eventos" : null);
  const conEvento = new Set((eventos ?? []).map((e) => e.fecha));
  const dias = Array.from({ length: 7 }, (_, i) => { const d = new Date(inicio); d.setDate(inicio.getDate() + i); return d; });
  const mover = (n: number) => { const d = new Date(inicio); d.setDate(d.getDate() + n * 7); setInicio(d); };
  const eventosDia = (eventos ?? []).filter((e) => e.fecha === sel);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">{MESES[inicio.getMonth()]} {inicio.getFullYear()}</h3>
        <div className="flex items-center gap-1">
          <button onClick={() => mover(-1)} className="p-1.5 rounded-full hover:bg-gray-100 text-gray-500"><ChevronLeft className="w-4 h-4" /></button>
          <button onClick={() => mover(1)} className="p-1.5 rounded-full hover:bg-gray-100 text-gray-500"><ChevronRight className="w-4 h-4" /></button>
        </div>
      </div>
      <div className="grid grid-cols-7 gap-2 text-center">
        {dias.map((d, i) => {
          const k = iso(d); const activo = k === sel;
          return (
            <button key={k} onClick={() => setSel(k)} className="flex flex-col items-center gap-2 py-1 group">
              <span className="text-[11px] text-gray-400">{DIAS[i]}</span>
              <span className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition ${
                activo ? "bg-primary-500 text-white shadow-pill" : "text-gray-700 group-hover:bg-gray-100"}`}>
                {d.getDate()}
              </span>
              <span className={`w-1.5 h-1.5 rounded-full ${conEvento.has(k) ? "bg-primary-500" : "bg-transparent"}`} />
            </button>
          );
        })}
      </div>
      {tienePermiso(usuario, "eventos.ver") && (
        <div className="mt-3 pt-3 border-t border-gray-100 text-sm">
          {eventosDia.length ? eventosDia.map((e) => (
            <Link key={e.id} to="/dashboard/eventos" className="flex items-center gap-2 py-1 text-gray-600 hover:text-primary-500">
              <span className="w-2 h-2 rounded-full bg-primary-500" /> {e.titulo}{e.lugar ? ` · ${e.lugar}` : ""}
            </Link>
          )) : <p className="text-gray-400">Sin eventos este día.</p>}
        </div>
      )}
    </div>
  );
}
