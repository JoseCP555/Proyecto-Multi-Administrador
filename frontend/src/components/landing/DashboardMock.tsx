import { motion } from "framer-motion";
import { Bell, Bot, Building2, Home, LayoutDashboard, MessagesSquare, Users, Wallet, Wrench } from "lucide-react";
import { useCountUp } from "@/hooks/useCountUp";
import logoUrl from "@/lib/logo";

/** Mockup animado del dashboard real (sidebar negra, píldoras azules, gráfico de área). */
function Kpi({ label, valor, sufijo = "", delta }: { label: string; valor: number; sufijo?: string; delta: string }) {
  const { ref, valor: v } = useCountUp(valor);
  return (
    <span ref={ref} className="block rounded-2xl bg-white border border-gray-100 p-3 shadow-card">
      <p className="text-[10px] text-gray-400 font-medium">{label}</p>
      <p className="text-sm sm:text-lg font-extrabold text-dark-100 leading-tight truncate">{sufijo}{v.toLocaleString("es-CO")}</p>
      <p className="text-[10px] font-semibold text-emerald-600">{delta}</p>
    </span>
  );
}

const ruta = "M0,70 C40,60 60,30 100,38 C140,46 160,20 200,26 C240,32 260,12 300,10 L300,90 L0,90 Z";
const linea = "M0,70 C40,60 60,30 100,38 C140,46 160,20 200,26 C240,32 260,12 300,10";

export default function DashboardMock({ compacto = false }: { compacto?: boolean }) {
  const menu = [
    { i: LayoutDashboard, on: true }, { i: Users }, { i: Building2 }, { i: Wallet }, { i: Wrench }, { i: MessagesSquare },
  ];
  return (
    <div className={`rounded-[28px] bg-[#ECE7FB] p-2 ${compacto ? "" : "sm:p-3"} shadow-shell ring-1 ring-black/5`}>
      <div className="rounded-[22px] bg-surface overflow-hidden flex" style={{ minHeight: compacto ? 300 : 360 }}>
        {/* Sidebar */}
        <div className="w-12 sm:w-14 bg-dark-100 flex flex-col items-center py-4 gap-3 shrink-0">
          <img src={logoUrl} alt="" className="w-8 h-8 rounded-full bg-white p-0.5" />
          <div className="mt-2 flex flex-col gap-2">
            {menu.map(({ i: I, on }, k) => (
              <span key={k} className={`w-8 h-8 rounded-xl flex items-center justify-center ${on ? "bg-primary-500 text-white" : "text-gray-500"}`}>
                <I className="w-4 h-4" />
              </span>
            ))}
          </div>
        </div>
        {/* Contenido */}
        <div className="flex-1 p-2.5 sm:p-4 min-w-0 overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-[10px] text-gray-400">Buenos días,</p>
              <p className="text-sm font-bold text-dark-100">Panel de administración</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden sm:flex h-7 px-3 rounded-full bg-white border border-gray-100 text-[10px] text-gray-400 items-center">Buscar…</span>
              <span className="relative w-7 h-7 rounded-full bg-white border border-gray-100 flex items-center justify-center">
                <Bell className="w-3.5 h-3.5 text-gray-500" />
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-danger" />
              </span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-1.5 sm:gap-2 mb-3">
            <Kpi label="Residentes" valor={1248} delta="+4.2%" />
            <Kpi label="Propiedades" valor={520} delta="+12" />
            <Kpi label="Recaudo" valor={3940} sufijo="$" delta="+8% (miles)" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
            <div className="sm:col-span-3 rounded-2xl bg-white border border-gray-100 p-3 shadow-card">
              <div className="flex items-center justify-between mb-1">
                <p className="text-[11px] font-semibold text-dark-100">Ingresos</p>
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-primary-50 text-primary-600 font-semibold">2026</span>
              </div>
              <svg viewBox="0 0 300 90" className="w-full h-20" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="gArea" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#2563EB" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <motion.path d={ruta} fill="url(#gArea)" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: 1, duration: 0.8 }} />
                <motion.path d={linea} fill="none" stroke="#2563EB" strokeWidth="3" strokeLinecap="round"
                  initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 1.6, ease: "easeInOut", delay: 0.3 }} />
              </svg>
            </div>
            <div className="sm:col-span-2 rounded-2xl bg-white border border-gray-100 p-3 shadow-card flex flex-col items-center justify-center">
              <p className="text-[11px] font-semibold text-dark-100 self-start mb-1">Cartera</p>
              <svg viewBox="0 0 80 80" className="w-16 h-16 -rotate-90">
                <circle cx="40" cy="40" r="30" stroke="#E5E7EB" strokeWidth="10" fill="none" />
                <motion.circle cx="40" cy="40" r="30" stroke="#2563EB" strokeWidth="10" fill="none" strokeLinecap="round"
                  strokeDasharray="188.5" initial={{ strokeDashoffset: 188.5 }} whileInView={{ strokeDashoffset: 188.5 * 0.22 }}
                  viewport={{ once: true }} transition={{ duration: 1.4, delay: 0.5, ease: "easeOut" }} />
              </svg>
              <p className="text-[10px] text-gray-500 -mt-1">78% al día</p>
            </div>
          </div>
          {!compacto && (
            <div className="mt-2 rounded-2xl bg-white border border-gray-100 p-3 shadow-card flex items-center gap-2">
              <span className="w-7 h-7 rounded-full bg-primary-500 text-white flex items-center justify-center"><Bot className="w-4 h-4" /></span>
              <p className="text-[11px] text-gray-600 truncate">“Hay <b>12 pagos pendientes</b> y 3 mantenimientos abiertos en Torre B.”</p>
              <Home className="w-3.5 h-3.5 text-gray-300 ml-auto shrink-0" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
