import { useMemo, useState, type FormEvent } from "react";
import { FileText, Download, Plus, Pencil, Trash2, Upload, ChevronDown, Filter, ArrowUpDown, FolderOpen } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api, API_BASE, getConjuntoActivo, getToken } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";
import { fecha, tamano, capitalizar } from "@/lib/format";
import type { Documento } from "@/types";

const CATEGORIAS_BASE = ["reglamento", "acta", "manual", "contrato", "financiero"];

// Formulario compartido para crear/editar.
const emptyForm = {
  titulo: "",
  descripcion: "",
  tipo_documento: "",
  publico: false,
};

function etiquetaCategoria(cat?: string | null): string {
  const limpia = (cat ?? "").trim().toLowerCase();
  if (!limpia) return "Otros documentos";
  const mapa: Record<string, string> = {
    reglamento: "Reglamentos",
    acta: "Actas",
    asamblea: "Actas de asamblea",
    manual: "Manuales",
    contrato: "Contratos",
    financiero: "Financiero",
    transcripcion: "Transcripciones",
  };
  return mapa[limpia] ?? capitalizar(limpia);
}

export default function Documentos() {
  const { puede } = usePermisos();
  const [categoriaFiltro, setCategoriaFiltro] = useState("");
  const [ordenFecha, setOrdenFecha] = useState<"fecha_desc" | "fecha_asc">("fecha_desc");
  const [agruparPorCategoria, setAgruparPorCategoria] = useState(true);

  const query = `?orden=${ordenFecha}${categoriaFiltro ? `&categoria=${encodeURIComponent(categoriaFiltro)}` : ""}`;
  const { data: docs, cargar, cargando } = useFetch<Documento[]>(`/documentos${query}`, [query]);

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

  const categoriasDisponibles = useMemo(() => {
    const set = new Set<string>(CATEGORIAS_BASE);
    (docs ?? []).forEach((d) => {
      const c = (d.tipo_documento ?? "").trim().toLowerCase();
      if (c) set.add(c);
    });
    return Array.from(set);
  }, [docs]);

  // UH-19: organiza los documentos por categoría, respetando el orden por fecha de publicación.
  const grupos = useMemo(() => {
    const lista = docs ?? [];
    const mapa = new Map<string, Documento[]>();
    for (const d of lista) {
      const clave = (d.tipo_documento ?? "").trim().toLowerCase() || "otros";
      const arr = mapa.get(clave) ?? [];
      arr.push(d);
      mapa.set(clave, arr);
    }
    return Array.from(mapa.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [docs]);

  const cargarDocumento = async () => {
    await cargar();
  };

  const alElegir = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError("");
    const f = e.target.files?.[0];
    if (!f) return;
    // UH-03: PDF o Word, hasta 20 MB.
    const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
    const permitidas = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".txt", ".csv"];
    if (!permitidas.includes(ext)) {
      setError("Formato no permitido. Sube un archivo PDF o Word (.pdf, .doc, .docx).");
      e.target.value = "";
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      setError("El archivo supera el máximo de 20 MB permitido.");
      e.target.value = "";
      return;
    }
    setArchivo(f);
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

      const token = getToken();
      const cid = getConjuntoActivo();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (cid) headers["X-Conjunto-Id"] = String(cid);
      const res = await fetch(`${API_BASE}/documentos/upload`, {
        method: "POST",
        headers,
        body: fd,
      });
      if (!res.ok) {
        let detalle = "No se pudo subir el documento.";
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") detalle = j.detail;
        } catch { /* respuesta sin JSON */ }
        throw new Error(detalle);
      }

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
      const base = API_BASE;
      const extMatch = (d.ruta_archivo || "").match(/(\.[a-z0-9]{2,5})$/i);
      const ext = extMatch ? extMatch[1].toLowerCase() : ".pdf";
      const nombre = d.titulo.toLowerCase().endsWith(ext) ? d.titulo : `${d.titulo}${ext}`;
      await descargarArchivo(`${base}/documentos/${d.id}/descargar`, nombre);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const renderTarjeta = (d: Documento) => (
    <div key={d.id} className="bg-gray-50 border border-gray-100 rounded-xl p-4 hover:shadow-card-hover transition">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-50 text-primary-600 flex items-center justify-center shrink-0">
          <FileText className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-gray-800 truncate">{d.titulo}</p>
          <p className="text-xs text-gray-400">
            {capitalizar(d.tipo_documento || "documento")} · {tamano(d.tamano)}
          </p>
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-3 line-clamp-2">{d.descripcion ?? "Sin descripción."}</p>
      <div className="flex items-center justify-between mt-4">
        <div className="flex gap-1.5">
          <Badge color={d.publico ? "info" : "neutral"}>{d.publico ? "Público" : "Privado"}</Badge>
          <span className="text-[11px] text-gray-400 self-center">{fecha(d.fecha_creacion)}</span>
        </div>
        <div className="flex gap-1">
          {puede("documentos.descargar") && (
            <button
              onClick={() => descargar(d)}
              title="Descargar"
              className="p-1.5 rounded-full btn btn-ghost text-gray-500 hover:bg-gray-100"
            >
              <Download className="w-4 h-4" />
            </button>
          )}
          {puede("documentos.editar") && (
            <button
              onClick={() => setEditando(d)}
              title="Editar"
              className="p-1.5 rounded-full btn btn-ghost text-primary-600 hover:bg-blue-50"
            >
              <Pencil className="w-4 h-4" />
            </button>
          )}
          {puede("documentos.eliminar") && (
            <button
              onClick={() => setEliminando(d)}
              title="Eliminar"
              className="p-1.5 rounded-full btn btn-ghost text-danger hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Documentos</h2>
          <p className="text-sm text-gray-500">
            {docs?.length ?? 0} documentos · organizados por categoría y fecha de publicación
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <Filter className="w-4 h-4 shrink-0" />
            <select
              className="input py-1.5 w-auto text-sm"
              aria-label="Filtrar por categoría"
              value={categoriaFiltro}
              onChange={(e) => setCategoriaFiltro(e.target.value)}
            >
              <option value="">Todas las categorías</option>
              {categoriasDisponibles.map((cat) => (
                <option key={cat} value={cat}>{etiquetaCategoria(cat)}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <ArrowUpDown className="w-4 h-4 shrink-0" />
            <select
              className="input py-1.5 w-auto text-sm"
              aria-label="Ordenar por fecha de publicación"
              value={ordenFecha}
              onChange={(e) => setOrdenFecha(e.target.value as "fecha_desc" | "fecha_asc")}
            >
              <option value="fecha_desc">Más recientes primero</option>
              <option value="fecha_asc">Más antiguos primero</option>
            </select>
          </div>
          <button
            type="button"
            onClick={() => setAgruparPorCategoria((v) => !v)}
            className="btn btn-outline py-1.5 px-3 text-xs flex items-center gap-1.5"
            title="Alternar vista agrupada por categoría"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            {agruparPorCategoria ? "Por categoría" : "Vista lista"}
          </button>
          {puede("documentos.crear") && (
            <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
              <Plus className="w-4 h-4" /> Subir documento
            </Button>
          )}
        </div>
      </div>

      {!docs?.length ? (
        <div className="py-10 text-center text-gray-400">
          {cargando ? (
            "Cargando..."
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FileText className="w-4 h-4" /> Sin documentos.
            </span>
          )}
        </div>
      ) : agruparPorCategoria && !categoriaFiltro ? (
        <div className="space-y-6">
          {grupos.map(([cat, items]) => (
            <section key={cat}>
              <div className="flex items-center justify-between border-b border-gray-100 pb-2 mb-3">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-primary-600" />
                  {etiquetaCategoria(cat === "otros" ? "" : cat)}
                </h3>
                <span className="text-xs text-gray-400">{items.length} documento(s)</span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map(renderTarjeta)}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {docs.map(renderTarjeta)}
        </div>
      )}

      {/* Modal subir */}
      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Subir documento">
        <form onSubmit={crear} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <div className="relative">
                <select
                  className="input appearance-none pr-10 cursor-pointer"
                  value={form.tipo_documento}
                  onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}
                  aria-label="Tipo de documento"
                >
                  <option value="">Seleccionar tipo…</option>
                  <option value="reglamento">Reglamento</option>
                  <option value="acta">Acta</option>
                  <option value="manual">Manual</option>
                  <option value="contrato">Contrato</option>
                  <option value="financiero">Financiero</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 w-4 h-4 -translate-y-1/2 text-gray-400" />
              </div>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input type="checkbox" checked={form.publico} onChange={(e) => setForm({ ...form, publico: e.target.checked })} />
                Público
              </label>
            </div>
          </div>
          <div>
            <label className="label">Título</label>
            <input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required />
          </div>
          <div>
            <label className="label">Descripción</label>
            <textarea className="input" rows={2} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div>
            <label className="label">Archivo</label>
            <label className="btn btn-outline w-full flex items-center justify-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" />
              {archivo ? archivo.name : "Seleccionar archivo"}
              <input
                type="file"
                className="hidden"
                onChange={alElegir}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.txt,.csv"
                required
              />
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
