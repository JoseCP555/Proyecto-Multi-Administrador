import { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Evento } from "@/types";

// Nombres de meses y días en español.
const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];
const DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

interface Props {
  eventos: Evento[];
  /** Se dispara al hacer clic en un día con eventos. Recibe el día (YYYY-MM-DD). */
  onSeleccionarDia: (dia: string) => void;
  dniSeleccionado?: string | null;
}

/** Convierte "YYYY-MM-DD" a Date local (sin desfase de zona horaria). */
function aDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toISO(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dia}`;
}

export default function CalendarioEventos({
  eventos,
  onSeleccionarDia,
  dniSeleccionado = null,
}: Props) {
  const hoy = new Date();
  const [mes, setMes] = useState(
    () => new Date(hoy.getFullYear(), hoy.getMonth(), 1),
  );

  // Mapa fecha -> eventos de ese día.
  const porDia = useMemo(() => {
    const map = new Map<string, Evento[]>();
    for (const ev of eventos ?? []) {
      if (!ev.fecha) continue;
      const k = ev.fecha.slice(0, 10);
      const arr = map.get(k) ?? [];
      arr.push(ev);
      map.set(k, arr);
    }
    return map;
  }, [eventos]);

  // Celdas del mes: días vacíos antes del primer día + días del mes.
  const celdas = useMemo(() => {
    const anio = mes.getFullYear();
    const mesIdx = mes.getMonth();
    const primerDia = new Date(anio, mesIdx, 1);
    const diasEnMes = new Date(anio, mesIdx + 1, 0).getDate();
    // offset: lunes=0 ... domingo=6
    let offset = (primerDia.getDay() + 6) % 7;
    const celdas: (Date | null)[] = [];
    for (let i = 0; i < offset; i++) celdas.push(null);
    for (let d = 1; d <= diasEnMes; d++) celdas.push(new Date(anio, mesIdx, d));
    return celdas;
  }, [mes]);

  const cambiarMes = (delta: number) => {
    setMes((m) => new Date(m.getFullYear(), m.getMonth() + delta, 1));
  };

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4">
      {/* Encabezado: mes y navegación */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-800">
          {MESES[mes.getMonth()]} {mes.getFullYear()}
        </h3>
        <div className="flex gap-1">
          <button
            onClick={() => cambiarMes(-1)}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
            aria-label="Mes anterior"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => setMes(new Date(hoy.getFullYear(), hoy.getMonth(), 1))}
            className="px-3 py-1.5 text-xs font-medium rounded-lg hover:bg-gray-100 text-gray-600"
          >
            Hoy
          </button>
          <button
            onClick={() => cambiarMes(1)}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
            aria-label="Mes siguiente"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Encabezado de días */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {DIAS_SEMANA.map((d) => (
          <div key={d} className="text-center text-[11px] font-medium text-gray-400 py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Celdas */}
      <div className="grid grid-cols-7 gap-1">
        {celdas.map((d, i) => {
          if (!d) return <div key={`v-${i}`} className="min-h-[64px] bg-gray-50/40 rounded-lg" />;
          const iso = toISO(d);
          const delDia = porDia.get(iso) ?? [];
          const esHoy = iso === toISO(hoy);
          const seleccionado = iso === dniSeleccionado;
          const esFinDeSemana = d.getDay() === 0 || d.getDay() === 6;
          return (
            <button
              key={iso}
              onClick={() => delDia.length && onSeleccionarDia(iso)}
              className={`relative min-h-[64px] rounded-lg p-1 text-left transition border
                ${seleccionado ? "border-primary-500 bg-primary-50 ring-1 ring-primary-300"
                  : delDia.length ? "border-primary-200 bg-primary-50/60 hover:bg-primary-100 cursor-pointer"
                  : esHoy ? "border-blue-200 bg-blue-50/50"
                  : `border-gray-100 ${esFinDeSemana ? "bg-gray-50/50" : "bg-white"}`}`}
            >
              <span
                className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${
                  esHoy ? "bg-primary-500 text-white" : "text-gray-500"
                }`}
              >
                {d.getDate()}
              </span>
              {/* Pastillas de eventos */}
              <div className="mt-1 space-y-0.5">
                {delDia.slice(0, 2).map((ev) => (
                  <div
                    key={ev.id}
                    className="text-[10px] leading-tight truncate rounded px-1 py-0.5 bg-primary-500 text-white"
                    title={ev.titulo}
                  >
                    {ev.titulo}
                  </div>
                ))}
                {delDia.length > 2 && (
                  <div className="text-[10px] text-primary-600 font-medium px-1">
                    +{delDia.length - 2} más
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
