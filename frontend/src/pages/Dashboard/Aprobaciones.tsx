import { useState, type FormEvent } from "react";
import { ClipboardCheck, Plus, ThumbsUp, ThumbsDown, Trash2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { moneda, fechaHora, capitalizar } from "@/lib/format";
import type { Aprobacion } from "@/types";

const CATEGORIAS = ["gasto", "contrato", "presupuesto", "otro"];

/** Solicitudes del administrador que decide el consejo — UH-24. */
export default function Aprobaciones() {
  const { puede } = usePermisos();
  const { data: solicitudes, cargar, cargando } = useFetch<Aprobacion[]>("/aprobaciones");
  const [estado, setEstado] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({ titulo: "", descripcion: "", monto: 0, categoria: "gasto" });
  const [error, setError] = useState("");
  const [decidiendo, setDecidiendo] = useState<Aprobacion | null>(null);
  const [decision, setDecision] = useState("aprobada");
  const [motivo, setMotivo] = useState("");
  const [eliminando, setEliminando] = useState<Aprobacion | null>(null);
  const [borrando, setBorrando] = useState(false);

  const lista = (solicitudes ?? []).filter((s) => !estado || s.estado === estado);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/aprobaciones", { ...form, monto: Number(form.monto) || 0 });
      setAbierto(false);
      setForm({ titulo: "", descripcion: "", monto: 0, categoria: "gasto" });
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const decidir = async (e: FormEvent) => {
    e.preventDefault();
    if (!decidiendo) return;
    setError("");
    try {
      await api.put(`/aprobaciones/${decidiendo.id}/decidir`, { estado: decision, motivo_decision: motivo });
      setDecidiendo(null);
      setMotivo("");
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/aprobaciones/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  const pendientes = (solicitudes ?? []).filter((s) => s.estado === "pendiente").length;

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Aprobaciones del consejo</h2>
          <p className="text-sm text-gray-500">{pendientes} pendiente(s) de decisión</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input py-1.5 w-auto" value={estado} onChange={(e) => setEstado(e.target.value)}>
            <option value="">Todas</option>
            <option value="pendiente">Pendientes</option>
            <option value="aprobada">Aprobadas</option>
            <option value="rechazada">Rechazadas</option>
          </select>
          {puede("aprobaciones.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
              <Plus className="w-4 h-4" /> Nueva solicitud
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {lista.map((s) => (
          <div key={s.id} className="border border-gray-100 bg-gray-50/60 rounded-xl p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-gray-800">{s.titulo}</p>
                  <Badge color={s.estado === "aprobada" ? "success" : s.estado === "rechazada" ? "danger" : "warning"}>
                    {s.estado}
                  </Badge>
                  <Badge color="neutral">{capitalizar(s.categoria)}</Badge>
                  <span className="text-sm font-semibold text-gray-700">{moneda(s.monto)}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{s.descripcion}</p>
                <p className="text-xs text-gray-400 mt-2">
                  Enviada por {s.creado_por_nombre ?? "—"} · {fechaHora(s.fecha_creacion)}
                </p>
                {s.fecha_decision && (
                  <p className="text-xs text-gray-500 mt-1">
                    {s.estado === "aprobada" ? "Aprobada" : "Rechazada"} por {s.decidido_por_nombre ?? "—"} el{" "}
                    {fechaHora(s.fecha_decision)}
                    {s.motivo_decision ? ` · ${s.motivo_decision}` : ""}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {puede("aprobaciones.decidir") && s.estado === "pendiente" && (
                  <>
                    <Button variante="outline" tamano="sm"
                      onClick={() => { setDecidiendo(s); setDecision("aprobada"); }}>
                      <ThumbsUp className="w-3.5 h-3.5" /> Aprobar
                    </Button>
                    <Button variante="outline" tamano="sm"
                      onClick={() => { setDecidiendo(s); setDecision("rechazada"); }}>
                      <ThumbsDown className="w-3.5 h-3.5" /> Rechazar
                    </Button>
                  </>
                )}
                {puede("aprobaciones.crear") && (
                  <button onClick={() => setEliminando(s)} title="Eliminar"
                    className="p-1.5 rounded-full text-danger hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                )}
              </div>
            </div>
          </div>
        ))}
        {!lista.length && (
          <div className="py-10 text-center text-gray-400">
            {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><ClipboardCheck className="w-4 h-4" /> Sin solicitudes.</span>}
          </div>
        )}
      </div>

      {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nueva solicitud al consejo">
        <form onSubmit={crear} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" required value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={3} required value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Monto</label>
              <input type="number" min={0} step="0.01" className="input" value={form.monto}
                onChange={(e) => setForm({ ...form, monto: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Categoría</label>
              <select className="input" value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value })}>
                {CATEGORIAS.map((c) => <option key={c} value={c}>{capitalizar(c)}</option>)}
              </select>
            </div>
          </div>
          <Button variante="primary" className="w-full" type="submit">Enviar al consejo</Button>
        </form>
      </Modal>

      <Modal abierto={!!decidiendo} onCerrar={() => setDecidiendo(null)} titulo="Decisión del consejo">
        <form onSubmit={decidir} className="space-y-4">
          <p className="text-sm text-gray-600">{decidiendo?.titulo} · {moneda(decidiendo?.monto ?? 0)}</p>
          <div>
            <label className="label">Decisión</label>
            <select className="input" value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="aprobada">Aprobar</option>
              <option value="rechazada">Rechazar</option>
            </select>
          </div>
          <div>
            <label className="label">Motivo / observación</label>
            <textarea className="input" rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </div>
          <p className="text-xs text-gray-400">
            La decisión queda registrada con fecha, hora y el miembro que la tomó.
          </p>
          <Button variante="primary" className="w-full" type="submit">Registrar decisión</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar la solicitud "${eliminando?.titulo}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
