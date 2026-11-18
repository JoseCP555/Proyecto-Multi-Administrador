import { useState, type FormEvent } from "react";
import { Megaphone, Plus, Pencil, Trash2, Pin } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { fechaHora, capitalizar } from "@/lib/format";
import type { Comunicado } from "@/types";

const CATEGORIAS = ["informativo", "normas", "evento", "urgente"];
const PRIORIDADES = ["baja", "media", "alta"];

const vacio = { titulo: "", contenido: "", categoria: "informativo", prioridad: "media", fijado: false };

/** Comunicados y circulares masivas — UH-11 / UH-18. */
export default function Comunicados() {
  const { puede } = usePermisos();
  const { data: comunicados, cargar, cargando } = useFetch<Comunicado[]>("/comunicados");
  const [categoria, setCategoria] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [editando, setEditando] = useState<Comunicado | null>(null);
  const [eliminando, setEliminando] = useState<Comunicado | null>(null);
  const [borrando, setBorrando] = useState(false);
  const [form, setForm] = useState(vacio);
  const [error, setError] = useState("");

  const lista = (comunicados ?? []).filter((c) => !categoria || c.categoria === categoria);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/comunicados", form);
      setAbierto(false);
      setForm(vacio);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const abrirEdicion = (c: Comunicado) => {
    setEditando(c);
    setForm({
      titulo: c.titulo, contenido: c.contenido, categoria: c.categoria,
      prioridad: c.prioridad, fijado: c.fijado,
    });
  };

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/comunicados/${editando.id}`, form);
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
      await api.del(`/comunicados/${eliminando.id}`);
      setEliminando(null);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBorrando(false);
    }
  };

  const formCampos = (
    <>
      <div>
        <label className="label">Título</label>
        <input className="input" required value={form.titulo}
          onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
      </div>
      <div>
        <label className="label">Contenido</label>
        <textarea className="input" rows={5} required value={form.contenido}
          onChange={(e) => setForm({ ...form, contenido: e.target.value })} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Categoría</label>
          <select className="input" value={form.categoria}
            onChange={(e) => setForm({ ...form, categoria: e.target.value })}>
            {CATEGORIAS.map((c) => <option key={c} value={c}>{capitalizar(c)}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Prioridad</label>
          <select className="input" value={form.prioridad}
            onChange={(e) => setForm({ ...form, prioridad: e.target.value })}>
            {PRIORIDADES.map((p) => <option key={p} value={p}>{capitalizar(p)}</option>)}
          </select>
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm text-gray-600">
        <input type="checkbox" checked={form.fijado}
          onChange={(e) => setForm({ ...form, fijado: e.target.checked })} />
        Fijar en la parte superior
      </label>
    </>
  );

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Comunicados</h2>
          <p className="text-sm text-gray-500">
            {lista.length} publicado(s) · se envían por notificación y correo a los residentes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input py-1.5 w-auto" value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            <option value="">Todas las categorías</option>
            {CATEGORIAS.map((c) => <option key={c} value={c}>{capitalizar(c)}</option>)}
          </select>
          {puede("comunicados.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
              <Plus className="w-4 h-4" /> Nuevo comunicado
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {lista.map((c) => (
          <div key={c.id} className={`border rounded-xl p-4 ${c.fijado ? "border-primary-200 bg-blue-50/40" : "border-gray-100 bg-gray-50/60"}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  {c.fijado && <Pin className="w-3.5 h-3.5 text-primary-500" />}
                  <p className="font-semibold text-gray-800">{c.titulo}</p>
                  <Badge color={c.prioridad === "alta" ? "danger" : c.prioridad === "baja" ? "neutral" : "info"}>
                    {c.categoria}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mt-2 whitespace-pre-line">{c.contenido}</p>
                <p className="text-xs text-gray-400 mt-2">{fechaHora(c.fecha_creacion)} · {c.autor}</p>
              </div>
              <div className="flex gap-1 shrink-0">
                {puede("comunicados.editar") && (
                  <button onClick={() => abrirEdicion(c)} title="Editar"
                    className="p-1.5 rounded-full text-primary-600 hover:bg-blue-50"><Pencil className="w-4 h-4" /></button>
                )}
                {puede("comunicados.eliminar") && (
                  <button onClick={() => setEliminando(c)} title="Eliminar"
                    className="p-1.5 rounded-full text-danger hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                )}
              </div>
            </div>
          </div>
        ))}
        {!lista.length && (
          <div className="py-10 text-center text-gray-400">
            {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><Megaphone className="w-4 h-4" /> Sin comunicados publicados.</span>}
          </div>
        )}
      </div>

      {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Nuevo comunicado">
        <form onSubmit={crear} className="space-y-4">
          {formCampos}
          <Button variante="primary" className="w-full" type="submit">Publicar y notificar</Button>
        </form>
      </Modal>

      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar comunicado">
        <form onSubmit={guardar} className="space-y-4">
          {formCampos}
          <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
        </form>
      </Modal>

      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Eliminar el comunicado "${eliminando?.titulo}"?`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
