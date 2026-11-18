import { useState, type FormEvent } from "react";
import { Plus, Wallet, Pencil, Trash2, FileText, FileSpreadsheet, Building2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge, { estadoColor } from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api, API_BASE } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";
import { moneda, fecha } from "@/lib/format";
import type { Movimiento, Concepto, Propiedad, CarteraResumen } from "@/types";

function colorEstadoCartera(estado: string) {
  if (estado === "al_dia") return "success";
  if (estado === "en_mora") return "danger";
  return "warning";
}

function etiquetaEstadoCartera(estado: string) {
  if (estado === "al_dia") return "Al día";
  if (estado === "en_mora") return "En mora";
  return "Pendiente";
}

export default function Finanzas() {
  const { puede, puedeAlguno } = usePermisos();
  const [estado, setEstado] = useState("");
  const [periodoCartera, setPeriodoCartera] = useState("");
  const queryPeriodo = periodoCartera ? `?periodo=${encodeURIComponent(periodoCartera)}` : "";

  const { data: movs, cargar, cargando } = useFetch<Movimiento[]>(
    `/finanzas${estado ? `?estado=${estado}` : ""}`,
    [estado]
  );
  const { data: resumen, cargar: cargarResumen } = useFetch<{
    ingresos: number;
    gastos: number;
    saldo: number;
    pendiente: number;
  }>("/finanzas/resumen");
  const { data: cartera, cargar: cargarCartera, cargando: cargandoCartera } = useFetch<CarteraResumen>(
    `/reportes/cartera${queryPeriodo}`,
    [queryPeriodo]
  );
  const { data: conceptos } = useFetch<Concepto[]>("/finanzas/conceptos");
  const { data: propiedades } = useFetch<Propiedad[]>("/propiedades");

  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Movimiento | null>(null);
  const [eliminando, setEliminando] = useState<Movimiento | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [form, setForm] = useState({
    concepto_id: "",
    propiedad_id: "",
    monto: "",
    fecha_vencimiento: "",
    estado: "pendiente",
  });
  const [error, setError] = useState("");

  // UH-05: refresca tabla, balance en tiempo real y cartera por unidad.
  const cargarTodo = async () => {
    await Promise.all([cargar(), cargarResumen(), cargarCartera()]);
  };

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/finanzas", {
        concepto_id: Number(form.concepto_id),
        propiedad_id: form.propiedad_id ? Number(form.propiedad_id) : null,
        monto: Number(form.monto),
        fecha_vencimiento: form.fecha_vencimiento,
        estado: form.estado,
      });
      setAbierto(false);
      setForm({ concepto_id: "", propiedad_id: "", monto: "", fecha_vencimiento: "", estado: "pendiente" });
      await cargarTodo();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (m: Movimiento) => {
    setEditando(m);
    setForm({
      concepto_id: String(m.concepto_id),
      propiedad_id: m.propiedad_id ? String(m.propiedad_id) : "",
      monto: String(m.monto),
      fecha_vencimiento: m.fecha_vencimiento,
      estado: m.estado,
    });
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/finanzas/${editando.id}`, {
        concepto_id: Number(form.concepto_id),
        propiedad_id: form.propiedad_id ? Number(form.propiedad_id) : null,
        monto: Number(form.monto),
        fecha_vencimiento: form.fecha_vencimiento,
        estado: form.estado,
      });
      setEditando(null);
      await cargarTodo();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/finanzas/${eliminando.id}`);
      setEliminando(null);
      await cargarTodo();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Resumen en tiempo real (UH-05) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { t: "Ingresos", v: moneda(resumen?.ingresos), c: "text-success" },
          { t: "Gastos", v: moneda(resumen?.gastos), c: "text-danger" },
          { t: "Saldo", v: moneda(resumen?.saldo), c: "text-primary-600" },
          { t: "Pendiente", v: moneda(resumen?.pendiente), c: "text-warning" },
        ].map((s) => (
          <Card key={s.t}>
            <p className="text-sm text-gray-500">{s.t}</p>
            <p className={`text-2xl font-bold mt-1 ${s.c}`}>{s.v}</p>
          </Card>
        ))}
      </div>

      {/* Movimientos financieros */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Movimientos</h2>
            <p className="text-sm text-gray-500">{movs?.length ?? 0} registros</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select value={estado} onChange={(e) => setEstado(e.target.value)} className="input w-auto">
              <option value="">Todos</option>
              <option value="pendiente">Pendiente</option>
              <option value="pagado">Pagado</option>
              <option value="vencido">Vencido</option>
            </select>
            {puedeAlguno("reportes.ver", "finanzas.ver") && (
              <ExportMenu
                opciones={[
                  { label: "Cartera por unidad (PDF)", ruta: `/reportes/exportar/cartera.pdf${queryPeriodo}`, tipo: "pdf" },
                  { label: "Cartera por unidad (Excel)", ruta: `/reportes/exportar/cartera.xlsx${queryPeriodo}`, tipo: "xlsx" },
                  { label: "Finanzas (Excel)", ruta: "/reportes/exportar/finanzas.xlsx", tipo: "xlsx" },
                  { label: "Resumen financiero (PDF)", ruta: "/reportes/exportar/finanzas.pdf", tipo: "pdf" },
                  { label: "Pagos en mora (Excel)", ruta: `/reportes/exportar/pagos.xlsx${queryPeriodo}`, tipo: "xlsx" },
                  { label: "Pagos en mora (PDF)", ruta: `/reportes/exportar/pagos.pdf${queryPeriodo}`, tipo: "pdf" },
                  { label: "Reporte del consejo (PDF)", ruta: "/reportes/exportar/consejo.pdf", tipo: "pdf" },
                  { label: "Reporte del consejo (Excel)", ruta: "/reportes/exportar/consejo.xlsx", tipo: "xlsx" },
                ]}
              />
            )}
            {puede("finanzas.crear") && (
              <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
                <Plus className="w-4 h-4" /> Nuevo
              </Button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2 font-medium">Concepto</th>
                <th className="py-2 font-medium">Propiedad</th>
                <th className="py-2 font-medium">Vencimiento</th>
                <th className="py-2 font-medium">Monto</th>
                <th className="py-2 font-medium">Estado</th>
                <th className="py-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {movs?.map((m) => (
                <tr key={m.id}>
                  <td className="py-2.5 font-medium text-gray-700">{m.concepto_nombre}</td>
                  <td className="py-2.5 text-gray-500">{m.propiedad_desc ?? "—"}</td>
                  <td className="py-2.5 text-gray-500">{fecha(m.fecha_vencimiento)}</td>
                  <td className="py-2.5 font-semibold">{moneda(m.monto)}</td>
                  <td className="py-2.5"><Badge color={estadoColor(m.estado)}>{m.estado}</Badge></td>
                  <td className="py-2.5">
                    <div className="flex gap-1">
                      {puede("finanzas.editar") && (
                        <button
                          onClick={() => abrirEdicion(m)}
                          title="Editar"
                          className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                      )}
                      {puede("finanzas.eliminar") && (
                        <button
                          onClick={() => setEliminando(m)}
                          title="Eliminar"
                          className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!movs?.length && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">
                    {cargando ? (
                      "Cargando..."
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        <Wallet className="w-4 h-4" /> Sin movimientos.
                      </span>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* UH-06: Reporte de pagos pendientes y al día por unidad con filtro por período */}
      {puedeAlguno("reportes.ver", "finanzas.ver") && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Reporte de pagos por unidad</h2>
              <p className="text-sm text-gray-500">
                Unidades al día y con pagos pendientes · Período: <span className="font-medium text-gray-700">{cartera?.periodo ?? "Histórico completo"}</span>
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="month"
                aria-label="Filtrar cartera por mes"
                className="input py-1.5 w-auto text-sm"
                value={periodoCartera}
                onChange={(e) => setPeriodoCartera(e.target.value)}
              />
              {periodoCartera && (
                <Button variante="outline" tamano="sm" onClick={() => setPeriodoCartera("")}>
                  Ver todo
                </Button>
              )}
              <Button
                variante="outline"
                tamano="sm"
                onClick={() =>
                  descargarArchivo(
                    `${API_BASE}/reportes/exportar/cartera.pdf${queryPeriodo}`,
                    `cartera_unidades${periodoCartera ? `_${periodoCartera}` : ""}.pdf`
                  )
                }
              >
                <FileText className="w-4 h-4 text-red-500" /> PDF
              </Button>
              <Button
                variante="outline"
                tamano="sm"
                onClick={() =>
                  descargarArchivo(
                    `${API_BASE}/reportes/exportar/cartera.xlsx${queryPeriodo}`,
                    `cartera_unidades${periodoCartera ? `_${periodoCartera}` : ""}.xlsx`
                  )
                }
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" /> Excel
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="border border-emerald-100 bg-emerald-50/50 rounded-xl p-3">
              <p className="text-xs text-emerald-700">Unidades al día</p>
              <p className="text-lg font-bold text-emerald-700">{cartera?.al_dia ?? 0}</p>
            </div>
            <div className="border border-amber-100 bg-amber-50/50 rounded-xl p-3">
              <p className="text-xs text-amber-700">Con pago pendiente / mora</p>
              <p className="text-lg font-bold text-amber-700">{cartera?.con_saldo ?? 0}</p>
            </div>
            <div className="border border-gray-100 rounded-xl p-3">
              <p className="text-xs text-gray-500">Total pendiente del período</p>
              <p className="text-lg font-bold text-gray-800">{moneda(cartera?.total_pendiente ?? 0)}</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-2 font-medium">Unidad</th>
                  <th className="py-2 font-medium">Residente</th>
                  <th className="py-2 font-medium text-right">Facturado</th>
                  <th className="py-2 font-medium text-right">Pagado</th>
                  <th className="py-2 font-medium text-right">Pendiente</th>
                  <th className="py-2 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody>
                {(cartera?.unidades ?? []).map((u) => (
                  <tr key={u.propiedad_id} className="border-t border-gray-50">
                    <td className="py-2 font-medium text-gray-800">
                      {u.apartamento}
                      {(u.torre || u.bloque) && (
                        <span className="text-xs text-gray-400 ml-1.5">
                          {[u.torre, u.bloque].filter(Boolean).join(" · ")}
                        </span>
                      )}
                    </td>
                    <td className="py-2 text-gray-600">{u.residente_nombre ?? "Sin asignar"}</td>
                    <td className="py-2 text-right text-gray-600">{moneda(u.facturado)}</td>
                    <td className="py-2 text-right text-emerald-700">{moneda(u.pagado)}</td>
                    <td className="py-2 text-right font-semibold text-gray-800">{moneda(u.pendiente)}</td>
                    <td className="py-2">
                      <Badge color={colorEstadoCartera(u.estado_pago)}>
                        {etiquetaEstadoCartera(u.estado_pago)}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {!cartera?.unidades?.length && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-gray-400">
                      {cargandoCartera ? (
                        "Cargando reporte de cartera..."
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <Building2 className="w-4 h-4" /> Sin unidades registradas.
                        </span>
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Modal crear */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nuevo movimiento">
        <form onSubmit={crear} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Concepto</label>
              <select className="input" value={form.concepto_id} onChange={(e) => setForm({ ...form, concepto_id: e.target.value })} required>
                <option value="">Selecciona...</option>
                {conceptos?.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Propiedad (opcional)</label>
              <select className="input" value={form.propiedad_id} onChange={(e) => setForm({ ...form, propiedad_id: e.target.value })}>
                <option value="">General del conjunto</option>
                {propiedades?.map((p) => <option key={p.id} value={p.id}>{p.apartamento}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Monto</label>
              <input type="number" className="input" value={form.monto} onChange={(e) => setForm({ ...form, monto: e.target.value })} required />
            </div>
            <div>
              <label className="label">Vencimiento</label>
              <input type="date" className="input" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} required />
            </div>
          </div>
          <div>
            <label className="label">Estado</label>
            <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
              <option value="pendiente">Pendiente</option>
              <option value="pagado">Pagado</option>
              <option value="vencido">Vencido</option>
            </select>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar movimiento">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Concepto</label>
              <select className="input" value={form.concepto_id} onChange={(e) => setForm({ ...form, concepto_id: e.target.value })} required>
                {conceptos?.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Propiedad (opcional)</label>
              <select className="input" value={form.propiedad_id} onChange={(e) => setForm({ ...form, propiedad_id: e.target.value })}>
                <option value="">General del conjunto</option>
                {propiedades?.map((p) => <option key={p.id} value={p.id}>{p.apartamento}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Monto</label>
              <input type="number" className="input" value={form.monto} onChange={(e) => setForm({ ...form, monto: e.target.value })} required />
            </div>
            <div>
              <label className="label">Vencimiento</label>
              <input type="date" className="input" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} required />
            </div>
          </div>
          <div>
            <label className="label">Estado</label>
            <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
              <option value="pendiente">Pendiente</option>
              <option value="pagado">Pagado</option>
              <option value="vencido">Vencido</option>
            </select>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar el movimiento de ${moneda(eliminando?.monto)}?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </div>
  );
}
