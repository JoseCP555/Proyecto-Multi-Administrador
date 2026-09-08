import { useState, type FormEvent } from "react";
import { Plus, CalendarDays, MapPin, Pencil, Trash2, List } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import CalendarioEventos from "@/components/dashboard/CalendarioEventos";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fecha } from "@/lib/format";
import type { Evento } from "@/types";

export default function Eventos() {
  const { puede } = usePermisos();
  const { data: eventos, cargar, cargando } = useFetch<Evento[]>("/eventos");
  const [vista, setVista] = useState<"calendario" | "lista">("calendario");
  const [diaSel, setDiaSel] = useState<string | null>(null);
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Evento | null>(null);
  const [eliminando, setEliminando] = useState<Evento | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ titulo: "", descripcion: "", fecha: "", lugar: "" });

  // Eventos del día seleccionado en el calendario.
  const eventosDelDia = eventos?.filter((ev) => ev.fecha?.slice(0, 10) === diaSel) ?? [];
  const diaEtiqueta = diaSel ? fecha(diaSel) : "";

  // Fecha mínima permitida: mañana (los eventos deben ser posteriores al día actual).
  const manana = (() => {
    const d = new Date(); d.setDate(d.getDate() + 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  })();
  const fechaInvalida = (f: string) => !!f && f < manana;

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (fechaInvalida(form.fecha)) { setError("La fecha del evento debe ser posterior al día de hoy."); return; }
    try {
      await api.post("/eventos", form);
      setAbierto(false);
      setForm({ titulo: "", descripcion: "", fecha: "", lugar: "" });
      cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (ev: Evento) => {
    setEditando(ev);
    setForm({ titulo: ev.titulo, descripcion: ev.descripcion ?? "", fecha: ev.fecha, lugar: ev.lugar ?? "" });
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    if (form.fecha !== editando.fecha && fechaInvalida(form.fecha)) { setError("La fecha del evento debe ser posterior al día de hoy."); return; }
    try {
      await api.put(`/eventos/${editando.id}`, form);
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
      await api.del(`/eventos/${eliminando.id}`);
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
      {/* Encabezado: título + tabs + botón nuevo */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Eventos</h2>
          <p className="text-sm text-gray-500">{eventos?.length ?? 0} programados</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Toggle Calendario / Lista */}
          <div className="flex rounded-lg border border-gray-200 p-0.5 bg-white">
            <button
              onClick={() => setVista("calendario")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition ${
                vista === "calendario" ? "bg-primary-500 text-white" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <CalendarDays className="w-4 h-4" /> Calendario
            </button>
            <button
              onClick={() => setVista("lista")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition ${
                vista === "lista" ? "bg-primary-500 text-white" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <List className="w-4 h-4" /> Lista
            </button>
          </div>
          {puede("eventos.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
              <Plus className="w-4 h-4" /> Nuevo
            </Button>
          )}
        </div>
      </div>

      {/* Vista calendario */}
      {vista === "calendario" ? (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <CalendarioEventos
              eventos={eventos ?? []}
              onSeleccionarDia={(d) => setDiaSel(d)}
              dniSeleccionado={diaSel}
            />
          </div>
          {/* Panel de eventos del día seleccionado */}
          <div className="card p-4">
            <h3 className="text-base font-semibold text-gray-800 mb-3">
              {diaEtiqueta || "Selecciona un día del calendario"}
            </h3>
            {diaSel ? (
              eventosDelDia.length ? (
                <div className="space-y-3">
                  {eventosDelDia.map((ev) => (
                    <div key={ev.id} className="bg-blue-50/60 border border-blue-100 rounded-xl p-3">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-semibold text-gray-800 text-sm">{ev.titulo}</p>
                        <div className="flex gap-1 shrink-0">
                          {puede("eventos.editar") && (
                            <button onClick={() => abrirEdicion(ev)} title="Editar"
                              className="p-1 rounded-lg text-primary-600 hover:bg-blue-100">
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {puede("eventos.eliminar") && (
                            <button onClick={() => setEliminando(ev)} title="Eliminar"
                              className="p-1 rounded-lg text-danger hover:bg-red-50">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{ev.descripcion ?? ""}</p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                        <span>{fecha(ev.fecha)}</span>
                        {ev.lugar && (
                          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{ev.lugar}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No hay eventos en este día.</p>
              )
            ) : (
              <p className="text-sm text-gray-400">
                Haz clic en un día marcado en azul para ver sus eventos.
              </p>
            )}
          </div>
        </div>
      ) : (
        /* Vista lista */
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {eventos?.map((ev) => (
            <div key={ev.id} className="bg-gray-50 border border-gray-100 rounded-xl p-4 hover:shadow-card-hover transition">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 text-primary-600 flex items-center justify-center shrink-0">
                    <CalendarDays className="w-5 h-5" />
                  </div>
                  <p className="font-semibold text-gray-800">{ev.titulo}</p>
                </div>
                <div className="flex gap-1">
                  {puede("eventos.editar") && (<button onClick={() => abrirEdicion(ev)} title="Editar"
                    className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                    <Pencil className="w-4 h-4" />
                  </button>)}
                  {puede("eventos.eliminar") && (<button onClick={() => setEliminando(ev)} title="Eliminar"
                    className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                    <Trash2 className="w-4 h-4" />
                  </button>)}
                </div>
              </div>
              <p className="text-sm text-gray-500">{ev.descripcion ?? ""}</p>
              <div className="flex items-center gap-2 mt-3 text-xs text-gray-400">
                <span>{fecha(ev.fecha)}</span>
                {ev.lugar && (
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{ev.lugar}</span>
                )}
              </div>
            </div>
          ))}
          {!eventos?.length && (
            <div className="col-span-full py-10 text-center text-gray-400">
              {cargando ? "Cargando..." : "Sin eventos programados."}
            </div>
          )}
        </div>
      )}

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nuevo evento">
        <form onSubmit={crear} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={2} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Fecha</label>
              <input type="date" className="input" min={manana} value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} required />
              <p className="text-xs text-gray-400 mt-1">Solo se permiten fechas posteriores a hoy.</p>
            </div>
            <div>
              <label className="label">Lugar</label>
              <input className="input" value={form.lugar} onChange={(e) => setForm({ ...form, lugar: e.target.value })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar</Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar evento">
        <form onSubmit={guardarEdicion} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={2} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Fecha</label>
              <input type="date" className="input" min={manana} value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} required />
              <p className="text-xs text-gray-400 mt-1">Solo se permiten fechas posteriores a hoy.</p>
            </div>
            <div>
              <label className="label">Lugar</label>
              <input className="input" value={form.lugar} onChange={(e) => setForm({ ...form, lugar: e.target.value })} />
            </div>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar el evento "${eliminando?.titulo}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
