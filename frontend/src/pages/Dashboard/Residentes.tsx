import { useState, type FormEvent } from "react";
import { Plus, UserRound, Pencil, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { rolesAsignables } from "@/lib/permisos";
import { api } from "@/lib/api";
import type { Propiedad, Residente } from "@/types";

const emptyForm = {
  nombre: "",
  correo: "",
  contrasena: "",
  rol_id: 3,
  apartamento: "",
  tipo: "propietario",
  identificacion: "",
  telefono_adicional: "",
  contacto_emergencia: "",
  telefono_emergencia: "",
};

export default function Residentes() {
  const { puede, usuario: yo } = usePermisos();
  const { data: residentes, cargar, cargando } = useFetch<Residente[]>("/residentes");
  const { data: propiedades } = useFetch<Propiedad[]>("/propiedades");
  const roles = rolesAsignables(yo);

  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Residente | null>(null);
  const [eliminando, setEliminando] = useState<Residente | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);

  const abrirNuevo = () => {
    setError("");
    setForm(emptyForm);
    setAbierto(true);
  };

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload: Record<string, unknown> = {
        tipo: form.tipo,
        identificacion: form.identificacion.trim(),
        telefono_adicional: form.telefono_adicional.trim() || null,
        contacto_emergencia: form.contacto_emergencia.trim() || null,
        telefono_emergencia: form.telefono_emergencia.trim() || null,
      };
      if (form.nombre.trim()) payload.nombre = form.nombre.trim();
      if (form.correo.trim()) {
        payload.correo = form.correo.trim();
        payload.rol_id = Number(form.rol_id) || 3;
      }
      if (form.contrasena) payload.contrasena = form.contrasena;
      if (form.apartamento.trim()) payload.apartamento = form.apartamento.trim();

      await api.post("/residentes", payload);
      setAbierto(false);
      setForm(emptyForm);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (r: Residente) => {
    setError("");
    setEditando(r);
    setForm({
      nombre: r.nombre ?? "",
      correo: r.correo ?? "",
      contrasena: "",
      rol_id: r.rol_id ?? 3,
      apartamento: r.apartamento ?? "",
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
      const payload: Record<string, unknown> = {
        tipo: form.tipo,
        identificacion: form.identificacion.trim(),
        telefono_adicional: form.telefono_adicional.trim() || null,
        contacto_emergencia: form.contacto_emergencia.trim() || null,
        telefono_emergencia: form.telefono_emergencia.trim() || null,
        activo: editando.activo,
      };
      if (form.nombre.trim()) payload.nombre = form.nombre.trim();
      if (form.correo.trim()) {
        payload.correo = form.correo.trim();
        payload.rol_id = Number(form.rol_id) || 3;
      }
      if (form.apartamento.trim()) payload.apartamento = form.apartamento.trim();

      await api.put(`/residentes/${editando.id}`, payload);
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
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Residentes</h2>
          <p className="text-sm text-gray-500">
            {residentes?.length ?? 0} registrados · gestión de cuentas, apartamento y rol
          </p>
        </div>
        {puede("residentes.crear") && (
          <Button variante="primary" tamano="sm" onClick={abrirNuevo}>
            <Plus className="w-4 h-4" /> Nuevo residente
          </Button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[780px] text-sm">
          <thead>
            <tr className="text-left">
              <th className="py-2 font-medium">Nombre y correo</th>
              <th className="py-2 font-medium">Apartamento</th>
              <th className="py-2 font-medium">Identificación</th>
              <th className="py-2 font-medium">Rol / Tipo</th>
              <th className="py-2 font-medium">Contacto emergencia</th>
              <th className="py-2 font-medium">Estado</th>
              <th className="py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {residentes?.map((r) => (
              <tr key={r.id}>
                <td className="py-2.5">
                  <p className="font-medium text-gray-800">{r.nombre ?? "Sin cuenta vinculada"}</p>
                  <p className="text-xs text-gray-400">{r.correo ?? "—"}</p>
                </td>
                <td className="py-2.5 text-gray-700 font-medium">{r.apartamento ?? "—"}</td>
                <td className="py-2.5 text-gray-600">{r.identificacion}</td>
                <td className="py-2.5">
                  <div className="flex flex-wrap gap-1">
                    <Badge color={r.tipo === "propietario" ? "info" : "purple"}>{r.tipo}</Badge>
                    {r.nombre_rol && <Badge color="neutral">{r.nombre_rol}</Badge>}
                  </div>
                </td>
                <td className="py-2.5 text-gray-500">
                  {r.contacto_emergencia ?? "—"}{" "}
                  <span className="text-gray-400">({r.telefono_emergencia ?? "—"})</span>
                </td>
                <td className="py-2.5">
                  <Badge color={r.activo ? "success" : "neutral"}>{r.activo ? "Activo" : "Inactivo"}</Badge>
                </td>
                <td className="py-2.5">
                  <div className="flex gap-1">
                    {puede("residentes.editar") && (
                      <button
                        onClick={() => abrirEdicion(r)}
                        title="Editar"
                        className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                    )}
                    {puede("residentes.eliminar") && (
                      <button
                        onClick={() => setEliminando(r)}
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
            {!residentes?.length && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-gray-400">
                  {cargando ? (
                    "Cargando..."
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <UserRound className="w-4 h-4" /> Sin residentes.
                    </span>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Sugerencias de apartamentos ya registrados en el conjunto */}
      <datalist id="lista-apartamentos">
        {(propiedades ?? []).map((p) => (
          <option key={p.id} value={p.apartamento} />
        ))}
      </datalist>

      {/* Modal crear (UH-02: nombre, apartamento, correo, rol + ficha residente) */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nuevo residente">
        <form onSubmit={crear} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Nombre completo</label>
              <input
                className="input"
                placeholder="Ej. Laura Gómez"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Apartamento / Unidad</label>
              <input
                className="input"
                list="lista-apartamentos"
                placeholder="Ej. A-302"
                value={form.apartamento}
                onChange={(e) => setForm({ ...form, apartamento: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Correo electrónico</label>
              <input
                type="email"
                className="input"
                placeholder="residente@correo.com"
                value={form.correo}
                onChange={(e) => setForm({ ...form, correo: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Rol</label>
              <select
                className="input"
                value={form.rol_id}
                onChange={(e) => setForm({ ...form, rol_id: Number(e.target.value) })}
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>
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
              <input
                className="input"
                value={form.identificacion}
                onChange={(e) => setForm({ ...form, identificacion: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Contraseña inicial (opcional)</label>
              <input
                type="password"
                minLength={8}
                placeholder="Mín. 8 caracteres o automática"
                className="input"
                value={form.contrasena}
                onChange={(e) => setForm({ ...form, contrasena: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Teléfono adicional</label>
              <input
                className="input"
                value={form.telefono_adicional}
                onChange={(e) => setForm({ ...form, telefono_adicional: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Contacto emergencia</label>
              <input
                className="input"
                value={form.contacto_emergencia}
                onChange={(e) => setForm({ ...form, contacto_emergencia: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Tel. emergencia</label>
              <input
                className="input"
                value={form.telefono_emergencia}
                onChange={(e) => setForm({ ...form, telefono_emergencia: e.target.value })}
              />
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
              <label className="label">Nombre completo</label>
              <input
                className="input"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Apartamento / Unidad</label>
              <input
                className="input"
                list="lista-apartamentos"
                value={form.apartamento}
                onChange={(e) => setForm({ ...form, apartamento: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Correo electrónico</label>
              <input
                type="email"
                className="input"
                value={form.correo}
                onChange={(e) => setForm({ ...form, correo: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Rol</label>
              <select
                className="input"
                value={form.rol_id}
                onChange={(e) => setForm({ ...form, rol_id: Number(e.target.value) })}
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>
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
              <input
                className="input"
                value={form.identificacion}
                onChange={(e) => setForm({ ...form, identificacion: e.target.value })}
                required
              />
            </div>
          </div>
          <div>
            <label className="label">Teléfono adicional</label>
            <input
              className="input"
              value={form.telefono_adicional}
              onChange={(e) => setForm({ ...form, telefono_adicional: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Contacto emergencia</label>
              <input
                className="input"
                value={form.contacto_emergencia}
                onChange={(e) => setForm({ ...form, contacto_emergencia: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Tel. emergencia</label>
              <input
                className="input"
                value={form.telefono_emergencia}
                onChange={(e) => setForm({ ...form, telefono_emergencia: e.target.value })}
              />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas desactivar al residente "${eliminando?.nombre || eliminando?.identificacion}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
