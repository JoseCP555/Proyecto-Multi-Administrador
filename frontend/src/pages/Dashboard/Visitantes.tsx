import { useState, type FormEvent } from "react";
import { DoorOpen, LogOut, Plus, Trash2, Search } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fechaHora } from "@/lib/format";
import type { Visitante } from "@/types";

const vacio = { nombre: "", documento: "", telefono: "", apartamento: "", motivo: "", observaciones: "" };

/** Registro y control de acceso de visitantes — UH-12. */
export default function Visitantes() {
  const { puede } = usePermisos();
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [estado, setEstado] = useState("");
  const [q, setQ] = useState("");

  const consulta = (() => {
    const p = new URLSearchParams();
    if (desde) p.set("desde", desde);
    if (hasta) p.set("hasta", hasta);
    if (estado) p.set("estado", estado);
    if (q) p.set("q", q);
    const s = p.toString();
    return `/visitantes${s ? `?${s}` : ""}`;
  })();
  const { data: visitantes, cargar, cargando } = useFetch<Visitante[]>(consulta, [consulta]);

  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState(vacio);
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState<Visitante | null>(null);
  const [borrando, setBorrando] = useState(false);

  const registrar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/visitantes", form);
      setAbierto(false);
      setForm(vacio);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const salida = async (v: Visitante) => {
    try {
      await api.put(`/visitantes/${v.id}/salida`, {});
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/visitantes/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  const dentro = (visitantes ?? []).filter((v) => v.estado === "dentro").length;

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Control de visitantes</h2>
          <p className="text-sm text-gray-500">
            {visitantes?.length ?? 0} registro(s) · {dentro} actualmente dentro
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {puede("visitantes.ver") && (
            <ExportMenu opciones={[{ label: "Visitantes (Excel)", ruta: "/visitantes/exportar.xlsx", tipo: "xlsx" }]} />
          )}
          {puede("visitantes.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
              <Plus className="w-4 h-4" /> Registrar ingreso
            </Button>
          )}
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="label">Desde</label>
          <input type="date" className="input py-1.5 w-auto" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </div>
        <div>
          <label className="label">Hasta</label>
          <input type="date" className="input py-1.5 w-auto" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </div>
        <div>
          <label className="label">Estado</label>
          <select className="input py-1.5 w-auto" value={estado} onChange={(e) => setEstado(e.target.value)}>
            <option value="">Todos</option>
            <option value="dentro">Dentro</option>
            <option value="salio">Salió</option>
          </select>
        </div>
        <div className="flex-1 min-w-[180px]">
          <label className="label">Buscar</label>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
            <input className="input py-1.5 pl-9" placeholder="Nombre o documento"
              value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500">
              <th className="py-2 font-medium">Visitante</th>
              <th className="py-2 font-medium">Documento</th>
              <th className="py-2 font-medium">Apartamento</th>
              <th className="py-2 font-medium">Ingreso</th>
              <th className="py-2 font-medium">Salida</th>
              <th className="py-2 font-medium">Estado</th>
              <th className="py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {(visitantes ?? []).map((v) => (
              <tr key={v.id} className="border-t border-gray-50">
                <td className="py-2.5">
                  <p className="font-medium text-gray-700">{v.nombre}</p>
                  <p className="text-xs text-gray-400">{v.motivo || "—"}</p>
                </td>
                <td className="py-2.5 text-gray-500">{v.documento}</td>
                <td className="py-2.5 text-gray-500">{v.apartamento}</td>
                <td className="py-2.5 text-gray-500">{fechaHora(v.hora_ingreso)}</td>
                <td className="py-2.5 text-gray-500">{v.hora_salida ? fechaHora(v.hora_salida) : "—"}</td>
                <td className="py-2.5">
                  <Badge color={v.estado === "dentro" ? "warning" : "success"}>{v.estado}</Badge>
                </td>
                <td className="py-2.5">
                  <div className="flex items-center gap-1">
                    {puede("visitantes.editar") && v.estado === "dentro" && (
                      <Button variante="outline" tamano="sm" onClick={() => salida(v)}>
                        <LogOut className="w-3.5 h-3.5" /> Salida
                      </Button>
                    )}
                    {puede("visitantes.eliminar") && (
                      <button onClick={() => setEliminando(v)} title="Eliminar"
                        className="p-1.5 rounded-full text-danger hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!visitantes?.length && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-gray-400">
                  {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><DoorOpen className="w-4 h-4" /> Sin registros para el filtro.</span>}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Registrar ingreso de visitante">
        <form onSubmit={registrar} className="space-y-4">
          <div>
            <label className="label">Nombre completo</label>
            <input className="input" required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Documento</label>
              <input className="input" required value={form.documento} onChange={(e) => setForm({ ...form, documento: e.target.value })} />
            </div>
            <div>
              <label className="label">Teléfono</label>
              <input className="input" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Apartamento visitado</label>
              <input className="input" required value={form.apartamento} onChange={(e) => setForm({ ...form, apartamento: e.target.value })} />
            </div>
            <div>
              <label className="label">Motivo</label>
              <input className="input" value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Observaciones</label>
            <textarea className="input" rows={2} value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} />
          </div>
          <p className="text-xs text-gray-400">La hora de ingreso se registra automáticamente al guardar.</p>
          <Button variante="primary" className="w-full" type="submit">Registrar ingreso</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar el registro de ${eliminando?.nombre}?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
