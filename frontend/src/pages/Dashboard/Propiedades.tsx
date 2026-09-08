import { useState, type FormEvent } from "react";
import { Building2, Plus, Pencil, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge, { estadoColor } from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import type { Propiedad } from "@/types";

const emptyForm = { bloque: "", torre: "", apartamento: "", estado: "ocupado", estrato: 2, area: 60 };

export default function Propiedades() {
  const { puede } = usePermisos();
  const [estado, setEstado] = useState("");
  const { data: propiedades, cargar, cargando } = useFetch<Propiedad[]>(
    `/propiedades${estado ? `?estado=${estado}` : ""}`,
    [estado]
  );
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Propiedad | null>(null);
  const [eliminando, setEliminando] = useState<Propiedad | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/propiedades", form);
      setAbierto(false);
      setForm(emptyForm);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (p: Propiedad) => {
    setEditando(p);
    setForm({
      bloque: p.bloque ?? "", torre: p.torre ?? "", apartamento: p.apartamento,
      estado: p.estado, estrato: p.estrato ?? 2, area: p.area ?? 60,
    });
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/propiedades/${editando.id}`, form);
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
      await api.del(`/propiedades/${eliminando.id}`);
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
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Propiedades</h2>
          <p className="text-sm text-gray-500">{propiedades?.length ?? 0} unidades</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={estado} onChange={(e) => setEstado(e.target.value)} className="input w-auto">
            <option value="">Todos los estados</option>
            <option value="ocupado">Ocupado</option>
            <option value="vacio">Vacío</option>
            <option value="mantenimiento">Mantenimiento</option>
          </select>
          {puede("propiedades.crear") && (<Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
            <Plus className="w-4 h-4" /> Nueva
          </Button>)}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="py-2 font-medium">Apartamento</th>
              <th className="py-2 font-medium">Bloque/Torre</th>
              <th className="py-2 font-medium">Área</th>
              <th className="py-2 font-medium">Estrato</th>
              <th className="py-2 font-medium">Estado</th>
              <th className="py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {propiedades?.map((p) => (
              <tr key={p.id} className="">
                <td className="py-2.5 font-medium text-gray-700">{p.apartamento}</td>
                <td className="py-2.5 text-gray-500">{p.bloque}/{p.torre}</td>
                <td className="py-2.5 text-gray-500">{p.area ?? "—"} m²</td>
                <td className="py-2.5 text-gray-500">{p.estrato ?? "—"}</td>
                <td className="py-2.5"><Badge color={estadoColor(p.estado)}>{p.estado}</Badge></td>
                <td className="py-2.5">
                  <div className="flex gap-1">
                    {puede("propiedades.editar") && (<button onClick={() => abrirEdicion(p)} title="Editar"
                      className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                      <Pencil className="w-4 h-4" />
                    </button>)}
                    {puede("propiedades.eliminar") && (<button onClick={() => setEliminando(p)} title="Eliminar"
                      className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                      <Trash2 className="w-4 h-4" />
                    </button>)}
                  </div>
                </td>
              </tr>
            ))}
            {!propiedades?.length && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-400">
                  {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><Building2 className="w-4 h-4" /> Sin propiedades.</span>}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal crear */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nueva propiedad">
        <form onSubmit={crear} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Bloque</label>
              <input className="input" value={form.bloque} onChange={(e) => setForm({ ...form, bloque: e.target.value })} />
            </div>
            <div>
              <label className="label">Torre</label>
              <input className="input" value={form.torre} onChange={(e) => setForm({ ...form, torre: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Apartamento</label>
            <input className="input" value={form.apartamento} onChange={(e) => setForm({ ...form, apartamento: e.target.value })} required />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label">Estado</label>
              <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="ocupado">Ocupado</option>
                <option value="vacio">Vacío</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
            </div>
            <div>
              <label className="label">Estrato</label>
              <input type="number" className="input" value={form.estrato} onChange={(e) => setForm({ ...form, estrato: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Área (m²)</label>
              <input type="number" className="input" value={form.area} onChange={(e) => setForm({ ...form, area: Number(e.target.value) })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar propiedad">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Bloque</label>
              <input className="input" value={form.bloque} onChange={(e) => setForm({ ...form, bloque: e.target.value })} />
            </div>
            <div>
              <label className="label">Torre</label>
              <input className="input" value={form.torre} onChange={(e) => setForm({ ...form, torre: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Apartamento</label>
            <input className="input" value={form.apartamento} onChange={(e) => setForm({ ...form, apartamento: e.target.value })} required />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label">Estado</label>
              <select className="input" value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="ocupado">Ocupado</option>
                <option value="vacio">Vacío</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
            </div>
            <div>
              <label className="label">Estrato</label>
              <input type="number" className="input" value={form.estrato} onChange={(e) => setForm({ ...form, estrato: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Área (m²)</label>
              <input type="number" className="input" value={form.area} onChange={(e) => setForm({ ...form, area: Number(e.target.value) })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar la propiedad "${eliminando?.apartamento}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
