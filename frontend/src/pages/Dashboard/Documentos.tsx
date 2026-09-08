import { useState, type FormEvent } from "react";
import { FileText, Download, Plus, Pencil, Trash2, Upload } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";
import { fecha, tamano } from "@/lib/format";
import type { Documento } from "@/types";

// Formulario compartido para crear/editar.
const emptyForm = {
  titulo: "",
  descripcion: "",
  tipo_documento: "",
  publico: false,
};

export default function Documentos() {
  const { puede } = usePermisos();
  const { data: docs, cargar, cargando } = useFetch<Documento[]>("/documentos");

  // Crear / subir
  const [abierto, setAbierto] = useState(false);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");

  // Editar
  const [editando, setEditando] = useState<Documento | null>(null);

  // Eliminar
  const [eliminando, setEliminando] = useState<Documento | null>(null);
  const [borrando, setBorrando] = useState(false);

  const cargarDocumento = async () => {
    await cargar();
  };

  const alElegir = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setArchivo(e.target.files[0]);
  };

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!archivo) {
      setError("Selecciona un archivo para subir.");
      return;
    }
    setSubiendo(true);
    try {
      const fd = new FormData();
      fd.append("titulo", form.titulo);
      fd.append("descripcion", form.descripcion);
      fd.append("tipo_documento", form.tipo_documento);
      fd.append("publico", String(form.publico));
      fd.append("archivo", archivo);

      const token = localStorage.getItem("ma_token");
      const res = await fetch(`${import.meta.env.VITE_API_URL || "/api"}/documentos/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) throw new Error("No se pudo subir el documento.");

      setAbierto(false);
      setForm(emptyForm);
      setArchivo(null);
      await cargarDocumento();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubiendo(false);
    }
  };

  const guardarEdicion = async (e: FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setError("");
    try {
      await api.put(`/documentos/${editando.id}`, {
        titulo: editando.titulo,
        descripcion: editando.descripcion,
        ruta_archivo: editando.ruta_archivo,
        tipo_documento: editando.tipo_documento,
        mime: editando.mime,
        tamano: editando.tamano,
        propiedad_id: editando.propiedad_id,
        publico: editando.publico,
      });
      setEditando(null);
      await cargarDocumento();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const confirmarEliminar = async () => {
    if (!eliminando) return;
    setBorrando(true);
    try {
      await api.del(`/documentos/${eliminando.id}`);
      setEliminando(null);
      await cargarDocumento();
    } catch (err) {
      alert(err);
    } finally {
      setBorrando(false);
    }
  };

  const descargar = async (d: Documento) => {
    try {
      const base = import.meta.env.VITE_API_URL || "/api";
      await descargarArchivo(`${base}/documentos/${d.id}/descargar`, `${d.titulo}.pdf`);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Documentos</h2>
          <p className="text-sm text-gray-500">{docs?.length ?? 0} documentos</p>
        </div>
        {puede("documentos.crear") && (<Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
          <Plus className="w-4 h-4" /> Subir documento
        </Button>)}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {docs?.map((d) => (
          <div key={d.id} className="bg-gray-50 border border-gray-100 rounded-xl p-4 hover:shadow-card-hover transition">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-primary-600 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-800 truncate">{d.titulo}</p>
                <p className="text-xs text-gray-400">{d.tipo_documento ?? "documento"} · {tamano(d.tamano)}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3 line-clamp-2">{d.descripcion ?? "Sin descripción."}</p>
            <div className="flex items-center justify-between mt-4">
              <div className="flex gap-1.5">
                <Badge color={d.publico ? "info" : "neutral"}>{d.publico ? "Público" : "Privado"}</Badge>
                <span className="text-[11px] text-gray-400 self-center">{fecha(d.fecha_creacion)}</span>
              </div>
              <div className="flex gap-1">
                {puede("documentos.descargar") && (<button onClick={() => descargar(d)} title="Descargar"
                  className="p-1.5 rounded-full btn btn-ghost text-gray-500 hover:bg-gray-100">
                  <Download className="w-4 h-4" />
                </button>)}
                {puede("documentos.editar") && (<button onClick={() => setEditando(d)} title="Editar"
                  className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50">
                  <Pencil className="w-4 h-4" />
                </button>)}
                {puede("documentos.eliminar") && (<button onClick={() => setEliminando(d)} title="Eliminar"
                  className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50">
                  <Trash2 className="w-4 h-4" />
                </button>)}
              </div>
            </div>
          </div>
        ))}
        {!docs?.length && (
          <div className="col-span-full py-10 text-center text-gray-400">
            {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><FileText className="w-4 h-4" /> Sin documentos.</span>}
          </div>
        )}
      </div>

      {/* Modal subir */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Subir documento">
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
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo_documento} onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}>
                <option value="">—</option>
                <option value="reglamento">Reglamento</option>
                <option value="acta">Acta</option>
                <option value="manual">Manual</option>
                <option value="contrato">Contrato</option>
                <option value="financiero">Financiero</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input type="checkbox" checked={form.publico} onChange={(e) => setForm({ ...form, publico: e.target.checked })} />
                Público
              </label>
            </div>
          </div>
          <div>
            <label className="label">Archivo</label>
            <label className="btn btn-outline w-full flex items-center justify-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" />
              {archivo ? archivo.name : "Seleccionar archivo"}
              <input type="file" className="hidden" onChange={alElegir} required />
            </label>
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" className="w-full" type="submit" disabled={subiendo}>
            {subiendo ? "Subiendo..." : "Subir documento"}
          </Button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal abierto={!!editando} onCerrar={() => setEditando(null)} titulo="Editar documento">
        {editando && (
          <form onSubmit={guardarEdicion} className="space-y-4">
            <div>
              <label className="label">Título</label>
              <input className="input" value={editando.titulo} onChange={(e) => setEditando({ ...editando, titulo: e.target.value })} required />
            </div>
            <div>
              <label className="label">Descripción</label>
              <textarea className="input" rows={2} value={editando.descripcion ?? ""} onChange={(e) => setEditando({ ...editando, descripcion: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Tipo</label>
                <select className="input" value={editando.tipo_documento ?? ""} onChange={(e) => setEditando({ ...editando, tipo_documento: e.target.value })}>
                  <option value="">—</option>
                  <option value="reglamento">Reglamento</option>
                  <option value="acta">Acta</option>
                  <option value="manual">Manual</option>
                  <option value="contrato">Contrato</option>
                  <option value="financiero">Financiero</option>
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <input type="checkbox" checked={editando.publico} onChange={(e) => setEditando({ ...editando, publico: e.target.checked })} />
                  Público
                </label>
              </div>
            </div>
            {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
            <Button variante="primary" className="w-full" type="submit">Guardar cambios</Button>
          </form>
        )}
      </Modal>

      {/* Confirmación de borrado */}
      <ConfirmDialog
        abierto={!!eliminando}
        mensaje={`¿Deseas eliminar el documento "${eliminando?.titulo}"? Esta acción no se puede deshacer.`}
        onCancelar={() => setEliminando(null)}
        onConfirmar={confirmarEliminar}
        cargando={borrando}
      />
    </Card>
  );
}
