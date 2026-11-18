import { useMemo, useState, type FormEvent } from "react";
import { CalendarClock, Plus, Check, X, Trash2, Users, Clock, Ban } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fecha } from "@/lib/format";
import type { ReservaZona, ZonaComun } from "@/types";

function estadoColor(estado: string) {
  switch (estado) {
    case "aprobada": return "success";
    case "pendiente": return "warning";
    case "rechazada": return "danger";
    case "cancelada": return "neutral";
    default: return "info";
  }
}

/** Zonas comunes y reservas — UH-10 (admin) / UH-14 (residente). */
export default function Reservas() {
  const { puede } = usePermisos();
  const { data: zonas, cargar: cargarZonas } = useFetch<ZonaComun[]>("/reservas/zonas");
  const { data: reservas, cargar, cargando } = useFetch<ReservaZona[]>("/reservas");
  const [error, setError] = useState("");
  const [filtro, setFiltro] = useState("");

  // Nueva reserva
  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({
    zona_id: 0, fecha: "", hora_inicio: "10:00", hora_fin: "12:00", motivo: "", asistentes: 1,
  });
  const [ocupadas, setOcupadas] = useState<{ hora_inicio: string; hora_fin: string; estado: string }[]>([]);

  // Nueva zona
  const [nuevaZona, setNuevaZona] = useState(false);
  const [formZona, setFormZona] = useState({
    nombre: "", descripcion: "", capacidad: 20, hora_apertura: "08:00", hora_cierre: "22:00",
    requiere_aprobacion: true, activo: true,
  });

  const [decision, setDecision] = useState<ReservaZona | null>(null);
  const [motivoDecision, setMotivoDecision] = useState("");
  const [estadoDecision, setEstadoDecision] = useState("aprobada");
  const [eliminando, setEliminando] = useState<ReservaZona | null>(null);
  const [borrando, setBorrando] = useState(false);

  const lista = useMemo(
    () => (reservas ?? []).filter((r) => !filtro || r.estado === filtro),
    [reservas, filtro],
  );

  const consultarDisponibilidad = async (zona_id: number, f: string) => {
    if (!zona_id || !f) return;
    try {
      const res = await api.get<{ ocupadas: { hora_inicio: string; hora_fin: string; estado: string }[] }>(
        `/reservas/disponibilidad?zona_id=${zona_id}&fecha=${f}`,
      );
      setOcupadas(res.ocupadas);
    } catch {
      setOcupadas([]);
    }
  };

  const crearReserva = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/reservas", {
        zona_id: Number(form.zona_id),
        fecha: form.fecha,
        hora_inicio: form.hora_inicio,
        hora_fin: form.hora_fin,
        motivo: form.motivo || undefined,
        asistentes: Number(form.asistentes) || 1,
      });
      setAbierto(false);
      setOcupadas([]);
      setForm({ zona_id: 0, fecha: "", hora_inicio: "10:00", hora_fin: "12:00", motivo: "", asistentes: 1 });
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const crearZona = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/reservas/zonas", formZona);
      setNuevaZona(false);
      setFormZona({ nombre: "", descripcion: "", capacidad: 20, hora_apertura: "08:00", hora_cierre: "22:00", requiere_aprobacion: true, activo: true });
      await cargarZonas();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const decidir = async (e: FormEvent) => {
    e.preventDefault();
    if (!decision) return;
    setError("");
    try {
      await api.put(`/reservas/${decision.id}/decidir`, { estado: estadoDecision, motivo_decision: motivoDecision });
      setDecision(null);
      setMotivoDecision("");
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/reservas/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Zonas comunes</h2>
            <p className="text-sm text-gray-500">{zonas?.length ?? 0} espacios reservables</p>
          </div>
          {puede("zonas.crear") && (
            <Button variante="outline" tamano="sm" onClick={() => setNuevaZona(true)}>
              <Plus className="w-4 h-4" /> Nueva zona
            </Button>
          )}
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {(zonas ?? []).map((z) => (
            <div key={z.id} className="border border-gray-100 bg-gray-50/70 rounded-xl p-4">
              <p className="font-semibold text-gray-800">{z.nombre}</p>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{z.descripcion || "—"}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" />{z.capacidad}</span>
                <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{z.hora_apertura}–{z.hora_cierre}</span>
              </div>
            </div>
          ))}
          {!zonas?.length && <p className="text-sm text-gray-400 col-span-full">Aún no hay zonas comunes registradas.</p>}
        </div>
      </Card>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Reservas</h2>
            <p className="text-sm text-gray-500">{lista.length} reserva(s)</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select className="input py-1.5 w-auto" value={filtro} onChange={(e) => setFiltro(e.target.value)}>
              <option value="">Todas</option>
              <option value="pendiente">Pendientes</option>
              <option value="aprobada">Aprobadas</option>
              <option value="rechazada">Rechazadas</option>
              <option value="cancelada">Canceladas</option>
            </select>
            {puede("reservas.ver") && (
              <ExportMenu opciones={[{ label: "Reservas (Excel)", ruta: "/reportes/exportar/reservas.xlsx", tipo: "xlsx" }]} />
            )}
            {puede("reservas.crear") && (
              <Button variante="primary" tamano="sm" onClick={() => { setAbierto(true); setOcupadas([]); }}>
                <Plus className="w-4 h-4" /> Reservar
              </Button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2 font-medium">Zona</th>
                <th className="py-2 font-medium">Fecha</th>
                <th className="py-2 font-medium">Horario</th>
                <th className="py-2 font-medium">Solicitante</th>
                <th className="py-2 font-medium">Estado</th>
                <th className="py-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((r) => (
                <tr key={r.id} className="border-t border-gray-50">
                  <td className="py-2.5 font-medium text-gray-700">{r.zona_nombre}</td>
                  <td className="py-2.5 text-gray-500">{fecha(r.fecha)}</td>
                  <td className="py-2.5 text-gray-500">{r.hora_inicio} – {r.hora_fin}</td>
                  <td className="py-2.5 text-gray-500">{r.solicitante ?? "—"}</td>
                  <td className="py-2.5"><Badge color={estadoColor(r.estado)}>{r.estado}</Badge></td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap items-center gap-1">
                      {puede("reservas.gestionar") && r.estado === "pendiente" && (
                        <>
                          <button title="Aprobar" onClick={() => { setDecision(r); setEstadoDecision("aprobada"); }}
                            className="p-1.5 rounded-full text-emerald-600 hover:bg-emerald-50"><Check className="w-4 h-4" /></button>
                          <button title="Rechazar" onClick={() => { setDecision(r); setEstadoDecision("rechazada"); }}
                            className="p-1.5 rounded-full text-danger hover:bg-red-50"><X className="w-4 h-4" /></button>
                        </>
                      )}
                      {puede("reservas.gestionar") && r.estado === "aprobada" && (
                        <button title="Cancelar" onClick={() => { setDecision(r); setEstadoDecision("cancelada"); }}
                          className="p-1.5 rounded-full text-amber-600 hover:bg-amber-50"><Ban className="w-4 h-4" /></button>
                      )}
                      {puede("reservas.crear") && (
                        <button title="Eliminar" onClick={() => setEliminando(r)}
                          className="p-1.5 rounded-full text-danger hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!lista.length && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">
                    {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><CalendarClock className="w-4 h-4" /> Sin reservas.</span>}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
      </Card>

      {/* Nueva reserva */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Reservar zona común">
        <form onSubmit={crearReserva} className="space-y-4">
          <div>
            <label className="label">Zona</label>
            <select className="input" required value={form.zona_id}
              onChange={(e) => {
                const id = Number(e.target.value);
                setForm({ ...form, zona_id: id });
                consultarDisponibilidad(id, form.fecha);
              }}>
              <option value={0}>Selecciona una zona…</option>
              {(zonas ?? []).filter((z) => z.activo).map((z) => (
                <option key={z.id} value={z.id}>{z.nombre} (máx. {z.capacidad})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Fecha</label>
            <input type="date" className="input" required value={form.fecha}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) => { setForm({ ...form, fecha: e.target.value }); consultarDisponibilidad(form.zona_id, e.target.value); }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Hora inicio</label>
              <input type="time" className="input" required value={form.hora_inicio}
                onChange={(e) => setForm({ ...form, hora_inicio: e.target.value })} />
            </div>
            <div>
              <label className="label">Hora fin</label>
              <input type="time" className="input" required value={form.hora_fin}
                onChange={(e) => setForm({ ...form, hora_fin: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Motivo</label>
              <input className="input" value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
            </div>
            <div>
              <label className="label">Asistentes</label>
              <input type="number" min={1} className="input" value={form.asistentes}
                onChange={(e) => setForm({ ...form, asistentes: Number(e.target.value) })} />
            </div>
          </div>
          {!!ocupadas.length && (
            <div className="text-xs bg-amber-50 border border-amber-200 text-amber-700 rounded-lg px-3 py-2">
              <p className="font-semibold mb-1">Horarios ya ocupados ese día:</p>
              {ocupadas.map((o, i) => <p key={i}>{o.hora_inicio} – {o.hora_fin}</p>)}
            </div>
          )}
          <p className="text-xs text-gray-400">El sistema evita reservas duplicadas en el mismo horario y espacio.</p>
          <Button variante="primary" className="w-full" type="submit">Confirmar reserva</Button>
        </form>
      </Modal>

      {/* Nueva zona */}
      <Modal abierto={nuevaZona} onCerrar={() => setNuevaZona(false)} titulo="Nueva zona común">
        <form onSubmit={crearZona} className="space-y-4">
          <div>
            <label className="label">Nombre</label>
            <input className="input" required value={formZona.nombre}
              onChange={(e) => setFormZona({ ...formZona, nombre: e.target.value })} />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={2} value={formZona.descripcion}
              onChange={(e) => setFormZona({ ...formZona, descripcion: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label">Capacidad</label>
              <input type="number" min={1} className="input" value={formZona.capacidad}
                onChange={(e) => setFormZona({ ...formZona, capacidad: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Apertura</label>
              <input type="time" className="input" value={formZona.hora_apertura}
                onChange={(e) => setFormZona({ ...formZona, hora_apertura: e.target.value })} />
            </div>
            <div>
              <label className="label">Cierre</label>
              <input type="time" className="input" value={formZona.hora_cierre}
                onChange={(e) => setFormZona({ ...formZona, hora_cierre: e.target.value })} />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input type="checkbox" checked={formZona.requiere_aprobacion}
              onChange={(e) => setFormZona({ ...formZona, requiere_aprobacion: e.target.checked })} />
            Requiere aprobación del administrador
          </label>
          <Button variante="primary" className="w-full" type="submit">Guardar zona</Button>
        </form>
      </Modal>

      {/* Decisión */}
      <Modal abierto={!!decision} onCerrar={() => setDecision(null)} titulo="Decidir reserva">
        <form onSubmit={decidir} className="space-y-4">
          <p className="text-sm text-gray-600">
            {decision?.zona_nombre} · {fecha(decision?.fecha)} · {decision?.hora_inicio}–{decision?.hora_fin}
          </p>
          <div>
            <label className="label">Estado</label>
            <select className="input" value={estadoDecision} onChange={(e) => setEstadoDecision(e.target.value)}>
              <option value="aprobada">Aprobada</option>
              <option value="rechazada">Rechazada</option>
              <option value="cancelada">Cancelada</option>
            </select>
          </div>
          <div>
            <label className="label">Motivo (opcional)</label>
            <textarea className="input" rows={2} value={motivoDecision} onChange={(e) => setMotivoDecision(e.target.value)} />
          </div>
          <Button variante="primary" className="w-full" type="submit">Guardar decisión</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar la reserva de ${eliminando?.zona_nombre ?? "la zona"}?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </div>
  );
}
