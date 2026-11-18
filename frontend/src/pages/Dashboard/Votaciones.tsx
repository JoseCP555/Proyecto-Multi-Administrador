import { useState, type FormEvent } from "react";
import { Vote, Plus, Lock, Trash2, CheckCircle2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fecha } from "@/lib/format";
import type { Votacion } from "@/types";

/** Votaciones del consejo — UH-25. */
export default function Votaciones() {
  const { puede } = usePermisos();
  const { data: votaciones, cargar, cargando } = useFetch<Votacion[]>("/votaciones");
  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({ titulo: "", descripcion: "", fecha_cierre: "" });
  const [opciones, setOpciones] = useState<string[]>(["", ""]);
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState<Votacion | null>(null);
  const [borrando, setBorrando] = useState(false);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    const validas = opciones.map((o) => o.trim()).filter(Boolean);
    if (validas.length < 2) {
      setError("Agrega al menos dos opciones.");
      return;
    }
    try {
      await api.post("/votaciones", { ...form, opciones: validas });
      setAbierto(false);
      setForm({ titulo: "", descripcion: "", fecha_cierre: "" });
      setOpciones(["", ""]);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const votar = async (v: Votacion, opcion_id: number) => {
    setError("");
    try {
      await api.post(`/votaciones/${v.id}/voto`, { opcion_id });
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const cerrar = async (v: Votacion) => {
    setError("");
    try {
      await api.put(`/votaciones/${v.id}/cerrar`, {});
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/votaciones/${eliminando.id}`);
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
          <h2 className="text-lg font-bold text-gray-900">Votaciones</h2>
          <p className="text-sm text-gray-500">
            {votaciones?.length ?? 0} votación(es) · cada miembro del consejo vota una sola vez
          </p>
        </div>
        {puede("votaciones.crear") && (
          <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
            <Plus className="w-4 h-4" /> Nueva votación
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {(votaciones ?? []).map((v) => (
          <div key={v.id} className="border border-gray-100 bg-gray-50/60 rounded-xl p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-gray-800">{v.titulo}</p>
                  <Badge color={v.estado === "abierta" ? "success" : "neutral"}>{v.estado}</Badge>
                  {v.mi_voto && <Badge color="info">Ya votaste</Badge>}
                </div>
                {v.descripcion && <p className="text-sm text-gray-600 mt-1">{v.descripcion}</p>}
                <p className="text-xs text-gray-400 mt-1">
                  Cierra: {fecha(v.fecha_cierre)} · {v.total_votos} voto(s)
                </p>
              </div>
              <div className="flex gap-1.5">
                {puede("votaciones.cerrar") && v.estado === "abierta" && (
                  <Button variante="outline" tamano="sm" onClick={() => cerrar(v)}>
                    <Lock className="w-3.5 h-3.5" /> Cerrar
                  </Button>
                )}
                {puede("votaciones.crear") && (
                  <button onClick={() => setEliminando(v)} title="Eliminar"
                    className="p-1.5 rounded-full text-danger hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                )}
              </div>
            </div>

            <div className="mt-3 space-y-2">
              {v.opciones.map((o) => {
                const elegida = v.mi_voto === o.id;
                const mostrarResultado = v.estado === "cerrada" || !!v.mi_voto;
                return (
                  <div key={o.id} className="relative">
                    {mostrarResultado && (
                      <div className="absolute inset-0 bg-primary-100/70 rounded-lg" style={{ width: `${o.porcentaje}%` }} />
                    )}
                    <div className="relative flex items-center justify-between px-3 py-2 rounded-lg">
                      <span className={`text-sm ${elegida ? "font-semibold text-primary-700" : "text-gray-700"}`}>
                        {elegida && <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" />}
                        {o.texto}
                      </span>
                      <div className="flex items-center gap-3">
                        {mostrarResultado && (
                          <span className="text-xs text-gray-500">{o.votos} voto(s) · {o.porcentaje}%</span>
                        )}
                        {v.puede_votar && puede("votaciones.votar") && (
                          <Button variante="outline" tamano="sm" onClick={() => votar(v, o.id)}>Votar</Button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        {!votaciones?.length && (
          <div className="py-10 text-center text-gray-400">
            {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><Vote className="w-4 h-4" /> Sin votaciones activas.</span>}
          </div>
        )}
      </div>

      {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nueva votación">
        <form onSubmit={crear} className="space-y-4">
          <div>
            <label className="label">Título</label>
            <input className="input" required value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={3} value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div>
            <label className="label">Fecha de cierre</label>
            <input type="date" className="input" required value={form.fecha_cierre}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) => setForm({ ...form, fecha_cierre: e.target.value })} />
          </div>
          <div>
            <label className="label">Opciones</label>
            <div className="space-y-2">
              {opciones.map((o, i) => (
                <div key={i} className="flex gap-2">
                  <input className="input" value={o} placeholder={`Opción ${i + 1}`}
                    onChange={(e) => setOpciones(opciones.map((x, j) => (j === i ? e.target.value : x)))} />
                  {opciones.length > 2 && (
                    <button type="button" onClick={() => setOpciones(opciones.filter((_, j) => j !== i))}
                      className="px-2 text-danger">✕</button>
                  )}
                </div>
              ))}
            </div>
            <button type="button" onClick={() => setOpciones([...opciones, ""])}
              className="text-sm text-primary-600 mt-2 hover:underline">+ Agregar opción</button>
          </div>
          <Button variante="primary" className="w-full" type="submit">Crear votación</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar la votación "${eliminando?.titulo}"? Se borrarán también sus votos.`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
