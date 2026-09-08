import { useState, type FormEvent } from "react";
import { Plus, UserRound, Pencil, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import type { Residente } from "@/types";

const emptyForm = { tipo: "propietario", identificacion: "", telefono_adicional: "", contacto_emergencia: "", telefono_emergencia: "" };

export default function Residentes() {
  const { puede } = usePermisos();
  const { data: residentes, cargar, cargando } = useFetch<Residente[]>("/residentes");
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Residente | null>(null);
  const [eliminando, setEliminando] = useState<Residente | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/residentes", form);
      setAbierto(false);
      setForm(emptyForm);
      cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (r: Residente) => {
    setEditando(r);
    setForm({
      tipo: r.tipo,
      identificacion: r.identificacion,
      telefono_adicional: r.telefono_adicional ?? "",
      contacto_emergencia: r.contacto_emergencia ?? "",
      telefono_emergencia: r.telefono_emergencia ?? "",
    });
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/residentes/${editando.id}`, form);
      setEditando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/residentes/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Residentes</h2>
          <p className="text-sm text-gray-500">{residentes?.length ?? 0} registrados</p>
        </div>
        {puede("residentes.crear") && (<Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
          <Plus className="w-4 h-4" /> Nuevo residente
        </Button>)}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="py-2 font-medium">Identificación</th>
              <th className="py-2 font-medium">Tipo</th>
              <th className="py-2 font-medium">Contacto emergencia</th>
              <th className="py-2 font-medium">Estado</th>
              <th className="py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {residentes?.map((r) => (
              <tr key={r.id} className="">
                <td className="py-2.5 font-medium text-gray-700">{r.identificacion}</td>
                <td className="py-2.5"><Badge color={r.tipo === "propietario" ? "info" : "purple"}>{r.tipo}</Badge></td>
                <td className="py-2.5 text-gray-500">{r.contacto_emergencia ?? "—"} <span className="text-gray-400">({r.telefono_emergencia ?? "—"})</span></td>
                <td className="py-2.5"><Badge color={r.activo ? "success" : "neutral"}>{r.activo ? "Activo" : "Inactivo"}</Badge></td>
                <td className="py-2.5">
                  <div className="flex gap-1">
                    {puede("residentes.editar") && (<button onClick={() => abrirEdicion(r)} title="Editar"
                      className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                      <Pencil className="w-4 h-4" />
                    </button>)}
                    {puede("residentes.eliminar") && (<button onClick={() => setEliminando(r)} title="Eliminar"
                      className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                      <Trash2 className="w-4 h-4" />
                    </button>)}
                  </div>
                </td>
              </tr>
            ))}
            {!residentes?.length && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-400">
                  {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><UserRound className="w-4 h-4" /> Sin residentes.</span>}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nuevo residente">
        <form onSubmit={crear} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                <option value="propietario">Propietario</option>
                <option value="inquilino">Inquilino</option>
              </select>
            </div>
            <div>
              <label className="label">Identificación</label>
              <input className="input" value={form.identificacion} onChange={(e) => setForm({ ...form, identificacion: e.target.value })} required />
            </div>
          </div>
          <div>
            <label className="label">Teléfono adicional</label>
            <input className="input" value={form.telefono_adicional} onChange={(e) => setForm({ ...form, telefono_adicional: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Contacto emergencia</label>
              <input className="input" value={form.contacto_emergencia} onChange={(e) => setForm({ ...form, contacto_emergencia: e.target.value })} />
            </div>
            <div>
              <label className="label">Tel. emergencia</label>
              <input className="input" value={form.telefono_emergencia} onChange={(e) => setForm({ ...form, telefono_emergencia: e.target.value })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar residente">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                <option value="propietario">Propietario</option>
                <option value="inquilino">Inquilino</option>
              </select>
            </div>
            <div>
              <label className="label">Identificación</label>
              <input className="input" value={form.identificacion} onChange={(e) => setForm({ ...form, identificacion: e.target.value })} required />
            </div>
          </div>
          <div>
            <label className="label">Teléfono adicional</label>
            <input className="input" value={form.telefono_adicional} onChange={(e) => setForm({ ...form, telefono_adicional: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Contacto emergencia</label>
              <input className="input" value={form.contacto_emergencia} onChange={(e) => setForm({ ...form, contacto_emergencia: e.target.value })} />
            </div>
            <div>
              <label className="label">Tel. emergencia</label>
              <input className="input" value={form.telefono_emergencia} onChange={(e) => setForm({ ...form, telefono_emergencia: e.target.value })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar al residente con identificación "${eliminando?.identificacion}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
