import { useState, type FormEvent } from "react";
import { Plus, Users, Pencil, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { rolesAsignables, ROL_SUPER_ADMIN } from "@/lib/permisos";
import { api } from "@/lib/api";
import type { Usuario } from "@/types";

const emptyForm = { nombre: "", correo: "", contrasena: "", telefono: "", rol_id: 3 };

export default function Usuarios() {
  const { puede, esSuper, usuario: yo } = usePermisos();
  const { data: usuarios, cargar, cargando } = useFetch<Usuario[]>("/usuarios");
  const roles = rolesAsignables(yo);
  // Un admin normal no puede tocar cuentas super_admin; nadie se elimina a sí mismo.
  const puedeGestionar = (u: Usuario) => esSuper() || u.rol_id !== ROL_SUPER_ADMIN;
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Usuario | null>(null);
  const [eliminando, setEliminando] = useState<Usuario | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/register", { ...form });
      setAbierto(false);
      setForm(emptyForm);
      await cargar();
    } catch (err) {
      const d = (err as { detail?: string }).detail;
      setError(d || (err as Error).message);
    }
  };

  const abrirEdicion = (u: Usuario) => {
    setEditando(u);
    setForm({ nombre: u.nombre, correo: u.correo, contrasena: "", telefono: u.telefono ?? "", rol_id: u.rol_id });
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/usuarios/${editando.id}`, {
        nombre: form.nombre, correo: form.correo, telefono: form.telefono, rol_id: form.rol_id,
      });
      setEditando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const alternarEstado = async (u: Usuario) => {
    if (!puede("usuarios.editar") || !puedeGestionar(u) || u.id === yo?.id) return;
    setError("");
    try {
      await api.put(`/usuarios/${u.id}`, { activo: !u.activo });
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/usuarios/${eliminando.id}`);
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
          <h2 className="text-lg font-bold text-gray-900">Usuarios del sistema</h2>
          <p className="text-sm text-gray-500">{usuarios?.length ?? 0} registrados</p>
        </div>
        {puede("usuarios.crear") && (<Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
          <Plus className="w-4 h-4" /> Nuevo usuario
        </Button>)}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="py-2 font-medium">Nombre</th>
              <th className="py-2 font-medium">Correo</th>
              <th className="py-2 font-medium">Rol</th>
              <th className="py-2 font-medium">Estado</th>
              <th className="py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {usuarios?.map((u) => (
              <tr key={u.id} className="">
                <td className="py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-50 text-primary-600 flex items-center justify-center text-xs font-bold">
                      {u.nombre.charAt(0)}
                    </div>
                    <span className="font-medium text-gray-700">{u.nombre}</span>
                  </div>
                </td>
                <td className="py-2.5 text-gray-500">{u.correo}</td>
                <td className="py-2.5"><Badge color="info">{u.nombre_rol}</Badge></td>
                <td className="py-2.5">
                  {puede("usuarios.editar") && puedeGestionar(u) && u.id !== yo?.id ? (
                    <button onClick={() => alternarEstado(u)} title={u.activo ? "Desactivar" : "Activar"}>
                      <Badge color={u.activo ? "success" : "neutral"}>{u.activo ? "Activo" : "Inactivo"}</Badge>
                    </button>
                  ) : (
                    <Badge color={u.activo ? "success" : "neutral"}>{u.activo ? "Activo" : "Inactivo"}</Badge>
                  )}
                </td>
                <td className="py-2.5">
                  <div className="flex gap-1">
                    {puede("usuarios.editar") && puedeGestionar(u) && (<button onClick={() => abrirEdicion(u)} title="Editar"
                      className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                      <Pencil className="w-4 h-4" />
                    </button>)}
                    {puede("usuarios.eliminar") && puedeGestionar(u) && u.id !== yo?.id && (<button onClick={() => setEliminando(u)} title="Eliminar"
                      className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                      <Trash2 className="w-4 h-4" />
                    </button>)}
                  </div>
                </td>
              </tr>
            ))}
            {!usuarios?.length && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-400">
                  {cargando ? "Cargando..." : (
                    <span className="flex items-center justify-center gap-2"><Users className="w-4 h-4" /> Sin usuarios.</span>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal crear */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Crear usuario">
        <form onSubmit={crear} className="space-y-4">
          <div>
            <label className="label">Nombre completo</label>
            <input className="input" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          </div>
          <div>
            <label className="label">Correo</label>
            <input type="email" className="input" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input type="password" className="input" value={form.contrasena} onChange={(e) => setForm({ ...form, contrasena: e.target.value })} required placeholder="Mínimo 8 caracteres" />
          </div>
          <div>
            <label className="label">Teléfono</label>
            <input className="input" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
          </div>
          <div>
            <label className="label">Rol</label>
            <select className="input" value={form.rol_id} onChange={(e) => setForm({ ...form, rol_id: Number(e.target.value) })}>
              {roles.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
            </select>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Crear usuario</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar usuario">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div>
            <label className="label">Nombre completo</label>
            <input className="input" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          </div>
          <div>
            <label className="label">Correo</label>
            <input type="email" className="input" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Teléfono</label>
            <input className="input" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
          </div>
          <div>
            <label className="label">Rol</label>
            <select className="input" value={form.rol_id} disabled={editando?.id === yo?.id}
              onChange={(e) => setForm({ ...form, rol_id: Number(e.target.value) })}>
              {roles.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
            </select>
            {editando?.id === yo?.id && <p className="text-xs text-gray-400 mt-1">No puedes cambiar tu propio rol.</p>}
          </div>
          <p className="text-xs text-gray-400">Para cambiar la contraseña usa la opción de recuperación.</p>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar al usuario "${eliminando?.nombre}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
