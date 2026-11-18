import { useMemo, useState } from "react";
import { History, Search, ShieldCheck } from "lucide-react";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { fechaHora, capitalizar } from "@/lib/format";
import type { RegistroAuditoria } from "@/types";

const ACCIONES = ["crear", "editar", "eliminar", "login", "logout", "consultar"];

function colorAccion(accion: string) {
  if (accion === "crear") return "success";
  if (accion === "editar") return "warning";
  if (accion === "eliminar") return "danger";
  if (accion === "login" || accion === "logout") return "info";
  return "neutral";
}

/** Historial de auditoría de todas las acciones — UH-29. */
export default function Auditoria() {
  const [modulo, setModulo] = useState("");
  const [accion, setAccion] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [q, setQ] = useState("");

  const consulta = useMemo(() => {
    const p = new URLSearchParams();
    if (modulo) p.set("modulo", modulo);
    if (accion) p.set("accion", accion);
    if (desde) p.set("desde", desde);
    if (hasta) p.set("hasta", hasta);
    if (q) p.set("q", q);
    p.set("limite", "300");
    return `/auditoria?${p.toString()}`;
  }, [modulo, accion, desde, hasta, q]);

  const { data: registros, cargando } = useFetch<RegistroAuditoria[]>(consulta, [consulta]);
  const { data: resumen } = useFetch<{ total: number; por_accion: Record<string, number>; por_modulo: Record<string, number> }>(
    "/auditoria/resumen",
  );

  const modulos = useMemo(
    () => Array.from(new Set((registros ?? []).map((r) => r.modulo))).sort(),
    [registros],
  );

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Historial de auditoría</h2>
            <p className="text-sm text-gray-500">
              {resumen?.total ?? 0} acción(es) registradas · el historial no se puede editar ni eliminar
            </p>
          </div>
          <ExportMenu opciones={[{ label: "Auditoría (Excel)", ruta: "/auditoria/exportar.xlsx", tipo: "xlsx" }]} />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          {Object.entries(resumen?.por_accion ?? {}).slice(0, 4).map(([k, v]) => (
            <div key={k} className="border border-gray-100 rounded-xl p-3">
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> {capitalizar(k)}
              </p>
              <p className="text-lg font-bold text-gray-800">{v}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-end gap-3 mb-4">
          <div>
            <label className="label">Módulo</label>
            <select className="input py-1.5 w-auto" value={modulo} onChange={(e) => setModulo(e.target.value)}>
              <option value="">Todos</option>
              {modulos.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Acción</label>
            <select className="input py-1.5 w-auto" value={accion} onChange={(e) => setAccion(e.target.value)}>
              <option value="">Todas</option>
              {ACCIONES.map((a) => <option key={a} value={a}>{capitalizar(a)}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Desde</label>
            <input type="date" className="input py-1.5 w-auto" value={desde} onChange={(e) => setDesde(e.target.value)} />
          </div>
          <div>
            <label className="label">Hasta</label>
            <input type="date" className="input py-1.5 w-auto" value={hasta} onChange={(e) => setHasta(e.target.value)} />
          </div>
          <div className="flex-1 min-w-[180px]">
            <label className="label">Buscar</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
              <input className="input py-1.5 pl-9" placeholder="Usuario, detalle o ruta"
                value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2 font-medium">Fecha y hora</th>
                <th className="py-2 font-medium">Usuario</th>
                <th className="py-2 font-medium">Acción</th>
                <th className="py-2 font-medium">Módulo</th>
                <th className="py-2 font-medium">Detalle</th>
                <th className="py-2 font-medium">HTTP</th>
              </tr>
            </thead>
            <tbody>
              {(registros ?? []).map((r) => (
                <tr key={r.id} className="border-t border-gray-50">
                  <td className="py-2.5 text-gray-500 whitespace-nowrap">{fechaHora(r.fecha_creacion)}</td>
                  <td className="py-2.5 text-gray-700">{r.usuario_nombre || "Sistema"}</td>
                  <td className="py-2.5"><Badge color={colorAccion(r.accion)}>{r.accion}</Badge></td>
                  <td className="py-2.5 text-gray-500">{r.modulo}</td>
                  <td className="py-2.5 text-gray-600 max-w-[360px] truncate" title={r.detalle ?? ""}>{r.detalle || "—"}</td>
                  <td className="py-2.5 text-gray-400">{r.estado_http ?? "—"}</td>
                </tr>
              ))}
              {!registros?.length && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">
                    {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><History className="w-4 h-4" /> Sin registros para el filtro.</span>}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
