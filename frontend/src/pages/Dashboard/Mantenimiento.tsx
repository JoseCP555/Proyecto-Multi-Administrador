import { useState, type FormEvent } from "react";
import { Plus, Wrench, Pencil, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge, { estadoColor } from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fecha } from "@/lib/format";
import type { TareaMantenimiento } from "@/types";

function prioridadColor(p: string) {
  if (p === "critica") return "danger";
  if (p === "alta") return "warning";
  if (p === "media") return "info";
  return "neutral";
}

export default function Mantenimiento() {
  const { puede, puedeAlguno } = usePermisos();
  const { data: tareas, cargar, cargando } = useFetch<TareaMantenimiento[]>("/mantenimiento");
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<TareaMantenimiento | null>(null);
  const [eliminando, setEliminando] = useState<TareaMantenimiento | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ titulo: "", descripcion: "", prioridad: "media", estado: "pendiente" });
  const [fechaProgramada, setFechaProgramada] = useState("");

  const cargarTareas = () => cargar();

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/mantenimiento", { ...form, fecha_programada: fechaProgramada || undefined });
      setAbierto(false);
      setForm({ titulo: "", descripcion: "", prioridad: "media", estado: "pendiente" });
      setFechaProgramada("");
      await cargarTareas();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (t: TareaMantenimiento) => {
    setEditando(t);
    setForm({ titulo: t.titulo, descripcion: t.descripcion, prioridad: t.prioridad, estado: t.estado });
    setFechaProgramada(t.fecha_programada ?? "");
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/mantenimiento/${editando.id}`, {
        propiedad_id: editando.propiedad_id, residente_id: editando.residente_id,
        titulo: form.titulo, descripcion: form.descripcion, prioridad: form.prioridad,
        estado: form.estado, asignado_a: editando.asignado_a,
        costo_estimado: editando.costo_estimado, fecha_programada: fechaProgramada || undefined,
      });
      setEditando(null);
      await cargarTareas();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/mantenimiento/${eliminando.id}`);
      setEliminando(null);
      await cargarTareas();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  const marcarCompletada = async (t: TareaMantenimiento) => {
    await api.put(`/mantenimiento/${t.id}`, {
      propiedad_id: t.propiedad_id, residente_id: t.residente_id, titulo: t.titulo,
      descripcion: t.descripcion, prioridad: t.prioridad, estado: "completada",
      asignado_a: t.asignado_a, costo_estimado: t.costo_estimado, fecha_programada: t.fecha_programada,
    });
    await cargarTareas();
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Mantenimiento</h2>
          <p className="text-sm text-gray-500">{tareas?.length ?? 0} órdenes</p>
        </div>
        <div className="flex items-center gap-2">
          {puedeAlguno("reportes.ver", "mantenimiento.ver") && (<ExportMenu
            opciones={[
              { label: "Mantenimiento (Excel)", ruta: "/reportes/exportar/mantenimiento.xlsx", tipo: "xlsx" },
            ]}
          />)}
          {puede("mantenimiento.crear") && (<Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
            <Plus className="w-4 h-4" /> Nueva tarea
          </Button>)}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="py-2 font-medium">Título</th>
              <th className="py-2 font-medium">Prioridad</th>
              <th className="py-2 font-medium">Estado</th>
                <th className="py-2 font-medium">Programada</th>
                <th className="py-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {tareas?.map((t) => (
                <tr key={t.id} className="">
                  <td className="py-2.5">
                    <p className="font-medium text-gray-700">{t.titulo}</p>
                    <p className="text-xs text-gray-400">{t.descripcion.slice(0, 50)}...</p>
                  </td>
                  <td className="py-2.5"><Badge color={prioridadColor(t.prioridad)}>{t.prioridad}</Badge></td>
                  <td className="py-2.5"><Badge color={estadoColor(t.estado)}>{t.estado}</Badge></td>
                  <td className="py-2.5 text-gray-500">{fecha(t.fecha_programada)}</td>
                  <td className="py-2.5">
                    <div className="flex gap-1 items-center">
                      {t.estado !== "completada" && puede("mantenimiento.editar") && (
                        <Button variante="outline" tamano="sm" onClick={() => marcarCompletada(t)}>
                          Completar
                        </Button>
                      )}
                      {puede("mantenimiento.editar") && (<button onClick={() => abrirEdicion(t)} title="Editar"
                        className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                        <Pencil className="w-4 h-4" />
                      </button>)}
                      {puede("mantenimiento.eliminar") && (<button onClick={() => setEliminando(t)} title="Eliminar"
                        className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                        <Trash2 className="w-4 h-4" />
                      </button>)}
                    </div>
                  </td>
                </tr>
              ))}
            {!tareas?.length && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-400">
                  {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><Wrench className="w-4 h-4" /> Sin tareas.</span>}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nueva tarea de mantenimiento">
        <form onSubmit={crear} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={3} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Prioridad</label>
              <select className="input" value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value })}>
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="critica">Crítica</option>
              </select>
            </div>
            <div>
              <label className="label">Estado</label>
              <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En proceso</option>
                <option value="completada">Completada</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Fecha programada</label>
            <input type="date" className="input" value={fechaProgramada} onChange={(e) => setFechaProgramada(e.target.value)} />
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar tarea">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={3} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Prioridad</label>
              <select className="input" value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value })}>
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="critica">Crítica</option>
              </select>
            </div>
            <div>
              <label className="label">Estado</label>
              <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En proceso</option>
                <option value="completada">Completada</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Fecha programada</label>
            <input type="date" className="input" value={fechaProgramada} onChange={(e) => setFechaProgramada(e.target.value)} />
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar la tarea "${eliminando?.titulo}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
