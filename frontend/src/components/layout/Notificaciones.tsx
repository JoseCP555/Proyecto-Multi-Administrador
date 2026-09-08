import { useState, useEffect, useRef } from "react";
import { Bell, X, CalendarDays, Wallet, Wrench, AlarmClock } from "lucide-react";
import { api } from "@/lib/api";
import type { Notificacion } from "@/types";

// Icono y color por tipo de notificación.
const ICONOS: Record<Notificacion["tipo"], { icon: typeof Bell; color: string; badge: string }> = {
  mora: { icon: Wallet, color: "text-danger", badge: "bg-red-100 text-red-700" },
  proximo: { icon: AlarmClock, color: "text-amber-500", badge: "bg-amber-100 text-amber-700" },
  evento: { icon: CalendarDays, color: "text-primary-500", badge: "bg-blue-100 text-blue-700" },
  mantenimiento: { icon: Wrench, color: "text-warning", badge: "bg-amber-100 text-amber-700" },
};

export default function Notificaciones() {
  const [abierto, setAbierto] = useState(false);
  const [items, setItems] = useState<Notificacion[]>([]);
  const [cargando, setCargando] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const cargar = async () => {
    setCargando(true);
    try {
      const res = await api.get<Notificacion[]>("/notificaciones");
      setItems(res ?? []);
    } catch {
      setItems([]);
    } finally {
      setCargando(false);
    }
  };

  // Carga al montar y al abrir.
  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cerrar al hacer clic fuera.
  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const altas = items.filter((i) => i.severidad === "alta").length;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => {
          setAbierto((v) => !v);
          if (!abierto) cargar();
        }}
        className="p-2 relative rounded-full text-primary-500 hover:bg-primary-50"
        aria-label="Notificaciones"
      >
        <Bell className="w-5 h-5" />
        {altas > 0 && (
          <span className="absolute top-1 right-1 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[10px] font-bold">
            {altas}
          </span>
        )}
      </button>

      {abierto && (
        <div className="absolute right-0 mt-2 w-[330px] max-h-[440px] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-gray-100 z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <div>
              <p className="text-sm font-semibold text-gray-800">Notificaciones</p>
              <p className="text-xs text-gray-400">{items.length} recordatorios</p>
            </div>
            <button onClick={() => setAbierto(false)} className="p-1 rounded-lg hover:bg-gray-100 text-gray-400">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="divide-y divide-gray-50">
            {cargando && <p className="text-sm text-gray-400 text-center py-8">Cargando...</p>}
            {!cargando && !items.length && (
              <p className="text-sm text-gray-400 text-center py-8">No hay notificaciones.</p>
            )}
            {items.map((n, i) => {
              const meta = ICONOS[n.tipo];
              const Icono = meta.icon;
              return (
                <div key={i} className="flex gap-3 px-4 py-3 hover:bg-gray-50 transition">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${meta.badge}`}>
                    <Icono className={`w-4 h-4 ${meta.color}`} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[13px] font-semibold text-gray-800">{n.titulo}</p>
                    <p className="text-xs text-gray-500 leading-snug mt-0.5">{n.mensaje}</p>
                    {n.fecha && <p className="text-[11px] text-gray-400 mt-1">{n.fecha}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
