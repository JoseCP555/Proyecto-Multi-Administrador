import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { MessageSquareWarning, Plus, Paperclip, CheckCircle2, Trash2, Filter, X } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api, API_BASE, getConjuntoActivo, getToken } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";
import { fechaHora, capitalizar } from "@/lib/format";
import type { Pqrs } from "@/types";

const BASE = API_BASE;

const TIPOS = ["peticion", "queja", "reclamo", "sugerencia"];
const CATEGORIAS = ["zonas_comunes", "administracion", "convivencia", "finanzas", "otra"];

function estadoColor(estado: string) {
  if (estado === "cerrada") return "success";
  if (estado === "en_proceso") return "warning";
  return "info";
}

/** PQRS: radicar (residente), responder y cerrar (administración) — UH-09/16/32. */
export default function PQRS() {
  const { puede, puedeAlguno, usuario } = usePermisos();
  const { data: pqrs, cargar, cargando } = useFetch<Pqrs[]>("/pqrs");
  const [searchParams, setSearchParams] = useSearchParams();
  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState("");
  const [error, setError] = useState("");
  const [confirmacion, setConfirmacion] = useState<Pqrs | null>(null);

  // UH-32: enlace directo desde notificación (?id=123) resalta y enfoca el caso.
  const idDestacado = Number(searchParams.get("id") || 0) || null;

  const [nueva, setNueva] = useState(false);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [form, setForm] = useState({
    tipo: "peticion",
    categoria: "administracion",
    asunto: "",
    descripcion: "",
  });

  const [respondiendo, setRespondiendo] = useState<Pqrs | null>(null);
  const [respuesta, setRespuesta] = useState("");
  const [nuevoEstado, setNuevoEstado] = useState("en_proceso");
  const [eliminando, setEliminando] = useState<Pqrs | null>(null);
  const [borrando, setBorrando] = useState(false);

  const esStaff = puedeAlguno("pqrs.responder", "pqrs.cerrar", "pqrs.eliminar");

  const filtradas = useMemo(
    () =>
      (pqrs ?? []).filter(
        (p) => (!estado || p.estado === estado) && (!tipo || p.tipo === tipo),
      ),
    [pqrs, estado, tipo],
  );

  // Si venimos de una notificación con ?id=..., aseguramos visibilidad y desplazamos hacia el caso.
  useEffect(() => {
    if (!idDestacado || !pqrs?.length) return;
    if (pqrs.some((p) => p.id === idDestacado)) {
      const el = document.getElementById(`pqrs-caso-${idDestacado}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [idDestacado, pqrs]);

  const radicar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      let creada: Pqrs;
      if (archivo) {
        const fd = new FormData();
        fd.append("tipo", form.tipo);
        fd.append("categoria", form.categoria);
        fd.append("asunto", form.asunto);
        fd.append("descripcion", form.descripcion);
        fd.append("archivo", archivo);
        const token = getToken();
        const cid = getConjuntoActivo();
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;
        if (cid) headers["X-Conjunto-Id"] = String(cid);
        const res = await fetch(`${BASE}/pqrs/con-adjunto`, {
          method: "POST",
          headers,
          body: fd,
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error((data as { detail?: string }).detail || "No se pudo radicar la PQRS.");
        }
        creada = (await res.json()) as Pqrs;
      } else {
        creada = await api.post<Pqrs>("/pqrs", form);
      }
      setNueva(false);
      setArchivo(null);
      setForm({ tipo: "peticion", categoria: "administracion", asunto: "", descripcion: "" });
      setConfirmacion(creada);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirRespuesta = (p: Pqrs) => {
    setRespondiendo(p);
    setRespuesta(p.respuesta ?? "");
    setNuevoEstado(p.estado === "pendiente" ? "en_proceso" : p.estado);
  };

  const guardarRespuesta = async (e: FormEvent) => {
    e.preventDefault();
    if (!respondiendo) return;
    setError("");
    try {
      await api.put(`/pqrs/${respondiendo.id}/responder`, { estado: nuevoEstado, respuesta });
      setRespondiendo(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const cerrarCaso = async (p: Pqrs) => {
    try {
      await api.put(`/pqrs/${p.id}/cerrar`, { respuesta: p.respuesta ?? "Atendida por la administración." });
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/pqrs/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  const limpiarDestacado = () => {
    const next = new URLSearchParams(searchParams);
    next.delete("id");
    setSearchParams(next, { replace: true });
  };

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">PQRS</h2>
          <p className="text-sm text-gray-500">
            {filtradas.length} solicitud(es) · peticiones, quejas, reclamos y sugerencias
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-wrap items-center gap-1 text-sm text-gray-500 max-w-full">
            <Filter className="w-4 h-4" />
            <select className="input py-1.5 w-auto" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="">Todos los estados</option>
              <option value="pendiente">Pendiente</option>
              <option value="en_proceso">En proceso</option>
              <option value="cerrada">Cerrada</option>
            </select>
            <select className="input py-1.5 w-auto" value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="">Todos los tipos</option>
              {TIPOS.map((t) => (
                <option key={t} value={t}>{capitalizar(t)}</option>
              ))}
            </select>
          </div>
          {puedeAlguno("pqrs.ver", "reportes.ver") && (
            <ExportMenu
              opciones={[{ label: "PQRS (Excel)", ruta: "/reportes/exportar/pqrs.xlsx", tipo: "xlsx" }]}
            />
          )}
          {puede("pqrs.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setNueva(true)}>
              <Plus className="w-4 h-4" /> Radicar PQRS
            </Button>
          )}
        </div>
      </div>

      {/* UH-16: confirmación visible con número de radicado al enviar */}
      {confirmacion && (
        <div className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">
                PQRS radicada correctamente · Radicado <span className="font-mono">{confirmacion.radicado}</span>
              </p>
              <p className="text-xs text-emerald-800 mt-0.5">
                «{confirmacion.asunto}» quedó registrada en estado pendiente. Puedes hacer seguimiento desde esta pantalla.
                {confirmacion.categoria === "zonas_comunes"
                  ? " Además, se notificó al consejo de administración por corresponder a zonas comunes."
                  : ""}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setConfirmacion(null)}
            className="text-emerald-700 hover:text-emerald-900 p-1 rounded"
            aria-label="Cerrar confirmación"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {idDestacado && (
        <div className="mb-4 flex items-center justify-between gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-800">
          <span>Mostrando el caso enlazado desde la notificación (#{idDestacado}).</span>
          <button type="button" onClick={limpiarDestacado} className="font-medium underline">
            Quitar resaltado
          </button>
        </div>
      )}

      <div className="space-y-3">
        {filtradas.map((p) => {
          const resaltada = idDestacado === p.id || confirmacion?.id === p.id;
          return (
            <div
              key={p.id}
              id={`pqrs-caso-${p.id}`}
              className={`border rounded-xl p-4 transition ${
                resaltada
                  ? "border-primary-500 bg-blue-50/50 ring-2 ring-primary-200"
                  : "border-gray-100 bg-gray-50/60"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">{p.radicado}</span>
                    <Badge color={estadoColor(p.estado)}>{p.estado.replace("_", " ")}</Badge>
                    <Badge color="neutral">{capitalizar(p.tipo)}</Badge>
                    <Badge color={p.categoria === "zonas_comunes" ? "purple" : "info"}>
                      {p.categoria.replace("_", " ")}
                    </Badge>
                  </div>
                  <p className="font-semibold text-gray-800 mt-1.5">{p.asunto}</p>
                  <p className="text-sm text-gray-500 mt-1 whitespace-pre-line">{p.descripcion}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {fechaHora(p.fecha_creacion)}
                    {esStaff && p.solicitante ? ` · ${p.solicitante}` : ""}
                    {p.apartamento ? ` · Apto ${p.apartamento}` : ""}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  {p.adjunto && (
                    <button
                      onClick={() => descargarArchivo(`${BASE}/pqrs/${p.id}/adjunto`)}
                      className="flex items-center gap-1 text-xs text-primary-600 hover:underline"
                    >
                      <Paperclip className="w-3.5 h-3.5" /> Adjunto
                    </button>
                  )}
                  <div className="flex flex-wrap items-center gap-1.5 justify-end">
                    {puede("pqrs.responder") && p.estado !== "cerrada" && (
                      <Button variante="outline" tamano="sm" onClick={() => abrirRespuesta(p)}>
                        Responder
                      </Button>
                    )}
                    {puede("pqrs.cerrar") && p.estado !== "cerrada" && (
                      <Button variante="primary" tamano="sm" onClick={() => cerrarCaso(p)}>
                        <CheckCircle2 className="w-4 h-4" /> Cerrar
                      </Button>
                    )}
                    {puede("pqrs.eliminar") && (
                      <button
                        onClick={() => setEliminando(p)}
                        title="Eliminar"
                        className="p-1.5 rounded-full text-danger hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {p.respuesta && (
                <div className="mt-3 bg-white border border-blue-100 rounded-lg p-3">
                  <p className="text-xs font-semibold text-primary-600 mb-1">
                    Respuesta {p.respondido_por_nombre ? `· ${p.respondido_por_nombre}` : ""}
                    {p.fecha_respuesta ? ` · ${fechaHora(p.fecha_respuesta)}` : ""}
                  </p>
                  <p className="text-sm text-gray-600 whitespace-pre-line">{p.respuesta}</p>
                </div>
              )}
            </div>
          );
        })}

        {!filtradas.length && (
          <div className="py-10 text-center text-gray-400">
            {cargando ? (
              "Cargando..."
            ) : (
              <span className="flex items-center justify-center gap-2">
                <MessageSquareWarning className="w-4 h-4" />
                {esStaff ? "No hay PQRS registradas." : "Aún no has radicado PQRS."}
              </span>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Radicar */}
      <Modal abierto={nueva} onCerrar={() => setNueva(false)} titulo="Radicar PQRS">
        <form onSubmit={radicar} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                {TIPOS.map((t) => (
                  <option key={t} value={t}>{capitalizar(t)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Categoría</label>
              <select className="input" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })}>
                {CATEGORIAS.map((c) => (
                  <option key={c} value={c}>{capitalizar(c.replace("_", " "))}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Asunto</label>
            <input className="input" value={form.asunto} minLength={3} maxLength={200} required
              onChange={(e) => setForm({ ...form, asunto: e.target.value })} />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={4} required minLength={5} value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div>
            <label className="label">Adjunto (opcional, PDF o imagen)</label>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="input py-2"
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)} />
          </div>
          <p className="text-xs text-gray-400">
            Al radicar recibirás un número de radicado y podrás consultar el estado de tu caso.
            {usuario?.nombre_rol === "residente" && form.categoria === "zonas_comunes"
              ? " El consejo recibirá una notificación por ser de zona común."
              : ""}
          </p>
          <Button variante="primary" className="w-full" type="submit">Radicar</Button>
        </form>
      </Modal>

      {/* Responder */}
      <Modal abierto={!!respondiendo} onCerrar={() => setRespondiendo(null)} titulo={`Responder ${respondiendo?.radicado ?? ""}`}>
        <form onSubmit={guardarRespuesta} className="space-y-4">
          <div>
            <label className="label">Estado</label>
            <select className="input" value={nuevoEstado} onChange={(e) => setNuevoEstado(e.target.value)}>
              <option value="pendiente">Pendiente</option>
              <option value="en_proceso">En proceso</option>
              <option value="cerrada">Cerrada</option>
            </select>
          </div>
          <div>
            <label className="label">Respuesta</label>
            <textarea className="input" rows={5} value={respuesta} onChange={(e) => setRespuesta(e.target.value)} />
          </div>
          <Button variante="primary" className="w-full" type="submit">Guardar respuesta</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar la PQRS "${eliminando?.asunto}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
