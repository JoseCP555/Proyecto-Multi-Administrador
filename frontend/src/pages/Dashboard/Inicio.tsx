import {
  Users,
  Building2,
  Wallet,
  Wrench,
  FileText,
  TrendingUp,
  TrendingDown,
  CalendarDays,
} from "lucide-react";
import StatCard from "@/components/ui/StatCard";
import AreaChart from "@/components/dashboard/AreaChart";
import DonutChart from "@/components/dashboard/DonutChart";
import MiniCalendario from "@/components/dashboard/MiniCalendario";
import BarrasProgreso from "@/components/dashboard/BarrasProgreso";
import Badge, { estadoColor } from "@/components/ui/Badge";
import { useFetch } from "@/hooks/useFetch";
import { moneda, fecha } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";
import { tienePermiso } from "@/lib/permisos";
import type { DashboardStats, Movimiento } from "@/types";
import logoUrl from "@/lib/logo";

export default function Inicio() {
  const { usuario } = useAuth();

  // RBAC: los reportes/finanzas solo se consultan si el rol lo permite.
  const puedeVerReportes = tienePermiso(usuario, "reportes.ver");
  const puedeVerFinanzas = tienePermiso(usuario, "finanzas.ver");

  const { data: stats, cargando } = useFetch<DashboardStats>(
    puedeVerReportes ? "/reportes/dashboard" : null,
  );
  const { data: serie } = useFetch<{ mes: string; valor: number }[]>(
    puedeVerReportes ? "/reportes/finanzas-por-mes" : null,
  );
  const { data: movs } = useFetch<Movimiento[]>(
    puedeVerFinanzas ? "/finanzas" : null,
  );
  // Contadores no financieros para roles sin reportes (filtrados por permisos en el backend).
  const { data: basico } = useFetch<Partial<DashboardStats> & { eventos_proximos?: number }>(
    !puedeVerReportes ? "/reportes/resumen-basico" : null,
  );
  const ve = (m: string) => tienePermiso(usuario, `${m}.ver`);

  const ultimos = movs?.slice(0, 6) ?? [];

  // Crecimiento del último mes respecto al anterior (para la etiqueta del gráfico).
  const crecimiento = (() => {
    if (!serie || serie.length < 2) return null;
    const a = serie[serie.length - 2].valor, b = serie[serie.length - 1].valor;
    if (!a) return null;
    return ((b - a) / a) * 100;
  })();

  // Distribución de movimientos por estado (donut).
  const porEstado = (movs ?? []).reduce<Record<string, number>>((acc, m) => {
    acc[m.estado] = (acc[m.estado] ?? 0) + 1;
    return acc;
  }, {});
  const totalMovs = movs?.length ?? 0;
  const segmentos = [
    { label: "Pagados", valor: porEstado.pagado ?? 0, color: "#2563EB" },
    { label: "Pendientes", valor: porEstado.pendiente ?? 0, color: "#111111" },
    { label: "Vencidos", valor: porEstado.vencido ?? 0, color: "#9CA3AF" },
  ];

  // Composición de ingresos por concepto (barras).
  const porConcepto = (movs ?? [])
    .filter((m) => m.estado === "pagado")
    .reduce<Record<string, number>>((acc, m) => {
      acc[m.concepto_nombre] = (acc[m.concepto_nombre] ?? 0) + Number(m.monto);
      return acc;
    }, {});
  const totalConcepto = Object.values(porConcepto).reduce((a, b) => a + b, 0) || 1;
  const barras = Object.entries(porConcepto)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([label, v], i) => ({
      label,
      porcentaje: Math.round((v / totalConcepto) * 100),
      color: i === 0 ? "gradient" : i === 1 ? "#9CA3AF" : "#4B5563",
    }));

  // Vista para roles sin acceso a reportes/finanzas (residente, seguridad...).
  if (!puedeVerReportes) {
    return (
      <div className="space-y-6">
        <div className="rounded-3xl bg-primary-500 text-white p-8 sm:p-10 shadow-pill relative overflow-hidden">
          <div className="absolute -right-10 -top-10 w-56 h-56 rounded-full bg-white/10" />
          <div className="absolute right-24 -bottom-16 w-40 h-40 rounded-full bg-white/10" />
          <div className="relative flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-white flex items-center justify-center shrink-0 overflow-hidden">
              <img src={logoUrl} alt="" className="w-12 h-12 object-contain" />
            </div>
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                ¡Bienvenido, {usuario?.nombre?.split(" ")[0] ?? "vecino"}!
              </h2>
              <p className="text-white/85 mt-1 text-sm sm:text-base">
                Tu rol <span className="inline-flex px-2.5 py-0.5 rounded-full bg-white/20 text-white text-xs font-semibold capitalize">{usuario?.nombre_rol?.replace("_", " ")}</span> tiene acceso
                a los módulos del menú lateral. Los datos financieros solo son visibles para roles autorizados.
              </p>
            </div>
          </div>
        </div>

        {/* Indicadores: solo de los módulos que el rol puede ver */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {ve("propiedades") && (
            <StatCard titulo="Propiedades" valor={`${basico?.propiedades ?? 0}`} icono={Building2} color="success" indicador="Unidades" />
          )}
          {ve("residentes") && (
            <StatCard titulo="Residentes" valor={`${basico?.residentes ?? 0}`} icono={Users} color="primary" indicador="Activos" />
          )}
          {ve("mantenimiento") && (
            <StatCard titulo="Mantenimientos" valor={`${basico?.mantenimientos_pendientes ?? 0}`} icono={Wrench} color="danger" indicador="Pendientes" subida={false} />
          )}
          {ve("documentos") && (
            <StatCard titulo="Documentos" valor={`${basico?.documentos ?? 0}`} icono={FileText} color="primary" indicador="Publicados" />
          )}
          {ve("eventos") && (
            <StatCard titulo="Eventos" valor={`${basico?.eventos_proximos ?? 0}`} icono={CalendarDays} color="warning" indicador="Próximos" />
          )}
        </div>

        <div className="grid lg:grid-cols-2 gap-5">
        <div className="card">
          <MiniCalendario />
        </div>
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-3">Dónde encontrar cada cosa</h3>
          <ul className="text-sm text-gray-500 space-y-2">
            {ve("eventos") && (<li className="flex items-center gap-2">
              <CalendarDays className="w-4 h-4 text-primary-500" /> Eventos y novedades del conjunto en "Eventos".
            </li>)}
            {ve("mantenimiento") && (<li className="flex items-center gap-2">
              <Wrench className="w-4 h-4 text-primary-500" /> {tienePermiso(usuario, "mantenimiento.crear") ? "Reporta fallas y solicitudes" : "Consulta las órdenes"} en "Mantenimiento".
            </li>)}
            {ve("documentos") && (<li className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary-500" /> Descarga documentos (actas, contratos) en "Documentos".
            </li>)}
            {ve("residentes") && (<li className="flex items-center gap-2">
              <Users className="w-4 h-4 text-primary-500" /> Consulta el directorio en "Residentes".
            </li>)}
          </ul>
        </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métricas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <StatCard titulo="Residentes" valor={`${stats?.residentes ?? 0}`} icono={Users} color="primary" indicador={`${stats?.propiedades ?? 0} propiedades registradas`} />
        <StatCard titulo="Pagos" valor={`${stats?.pagos_pagados ?? 0}`} icono={TrendingUp} color="success" indicador={`${stats?.pagos_pendientes ?? 0} pendientes`} subida={(stats?.pagos_pendientes ?? 0) === 0} />
        <StatCard titulo="Saldo" valor={moneda(stats?.saldo)} icono={Wallet} destacada indicador={stats && stats.saldo < 0 ? "En déficit" : "En superávit"} subida={(stats?.saldo ?? 0) >= 0} />
      </div>

      <div className="grid xl:grid-cols-3 gap-5">
        {/* Columna izquierda: gráfico + calendario */}
        <div className="xl:col-span-2 space-y-5">
          <div className="card">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Ingresos por mes</h3>
                <p className="text-xs text-gray-400">Recaudo mensual del conjunto</p>
              </div>
              <Badge color="info">Últimos meses</Badge>
            </div>
            <AreaChart
              datos={serie ?? []}
              etiqueta={crecimiento !== null ? `${crecimiento >= 0 ? "+" : ""}${crecimiento.toFixed(2)}%` : undefined}
              cargando={cargando}
            />
          </div>

          <div className="card">
            <MiniCalendario />
          </div>
        </div>

        {/* Columna derecha: donut + barras */}
        <div className="space-y-5">
          <div className="card">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Estado de pagos</h3>
            <DonutChart segmentos={segmentos} total={totalMovs} etiquetaTotal="Movimientos" />
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Ingresos por concepto</h3>
            <BarrasProgreso items={barras} vacio={cargando ? "Cargando..." : "Sin ingresos registrados."} />
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Resumen financiero</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-emerald-500" /> Ingresos</span>
                <span className="font-bold text-emerald-600">{moneda(stats?.ingresos)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 flex items-center gap-2"><TrendingDown className="w-4 h-4 text-red-500" /> Gastos</span>
                <span className="font-bold text-red-500">{moneda(stats?.gastos)}</span>
              </div>
              <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                <span className="text-sm text-gray-500 flex items-center gap-2"><FileText className="w-4 h-4 text-primary-500" /> Documentos</span>
                <span className="font-bold text-gray-800">{stats?.documentos ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 flex items-center gap-2"><Wrench className="w-4 h-4 text-amber-500" /> Mantenimientos pendientes</span>
                <span className="font-bold text-gray-800">{stats?.mantenimientos_pendientes ?? 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Últimos movimientos */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Últimos movimientos</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2 font-medium">Concepto</th>
                <th className="py-2 font-medium">Propiedad</th>
                <th className="py-2 font-medium">Vencimiento</th>
                <th className="py-2 font-medium">Monto</th>
                <th className="py-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {ultimos.map((m) => (
                <tr key={m.id}>
                  <td className="py-3 font-medium text-gray-800">{m.concepto_nombre}</td>
                  <td className="py-3 text-gray-500">{m.propiedad_desc ?? "—"}</td>
                  <td className="py-3 text-gray-500">{fecha(m.fecha_vencimiento)}</td>
                  <td className="py-3 font-bold text-gray-900">{moneda(m.monto)}</td>
                  <td className="py-3"><Badge color={estadoColor(m.estado)}>{m.estado}</Badge></td>
                </tr>
              ))}
              {!ultimos.length && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-400">
                    {cargando ? "Cargando..." : "Sin movimientos registrados."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
