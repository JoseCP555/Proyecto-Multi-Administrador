import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Building2,
  Users,
  MapPin,
  Phone,
  Plus,
  Pencil,
  Trash2,
  ArrowRight,
  IdCard,
  Wallet,
  ImagePlus,
  Upload,
  X,
  Palette,
  Check,
} from "lucide-react";
import { useConjunto } from "@/context/ConjuntoContext";
import {
  COLORES_CONJUNTO,
  colorDeConjunto,
  colorSugerido,
  normalizarColor,
  resolverColor,
  type ColorConjunto,
} from "@/lib/coloresConjunto";
import { api, getToken } from "@/lib/api";
import { urlApi, urlLogo } from "@/lib/logo";
import { moneda } from "@/lib/format";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import type { Conjunto } from "@/types";

/**
 * Panel Multi-Administrador: listado de los conjuntos a cargo del usuario.
 * Al hacer clic en uno se entra a trabajar en su contexto (HU-07).
 */
export default function Conjuntos() {
  const { conjuntos, activo, seleccionar, recargar, cargando, puedeCrear, puedeEditar, puedeEliminar } =
    useConjunto();
  const navigate = useNavigate();

  const [editando, setEditando] = useState<Conjunto | null>(null);
  const [formAbierto, setFormAbierto] = useState(false);
  const [aEliminar, setAEliminar] = useState<Conjunto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  // Cifras globales del panel.
  const totalHabitantes = useMemo(
    () => conjuntos.reduce((acc, c) => acc + (c.habitantes || 0), 0),
    [conjuntos],
  );
  const abrir = (c: Conjunto) => {
    seleccionar(c.id);
    navigate("/dashboard/inicio");
  };

  const guardar = async (datos: Partial<Conjunto>) => {
    setGuardando(true);
    setError(null);
    try {
      const payload = {
        nombre: (datos.nombre ?? "").trim(),
        nit: datos.nit,
        direccion: datos.direccion,
        ciudad: datos.ciudad,
        telefono: datos.telefono,
        correo: datos.correo,
        administrador: datos.administrador,
        habitantes: Number(datos.habitantes ?? 0),
        cuota: Number(datos.cuota ?? 0),
        dia_cobro: datos.dia_cobro ? Number(datos.dia_cobro) : null,
        reunion: datos.reunion,
        silencio: datos.silencio,
        // "" = el usuario quitó el logo (el backend lo convierte en NULL).
        logo: datos.logo,
        // "" en color = volver al color automático por posición.
        color: datos.color ?? "",
      };
      if (editando) await api.put(`/conjuntos/${editando.id}`, payload);
      else await api.post("/conjuntos", payload);
      await recargar();
      setFormAbierto(false);
      setEditando(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGuardando(false);
    }
  };

  const confirmarEliminar = async () => {
    if (!aEliminar) return;
    try {
      await api.del(`/conjuntos/${aEliminar.id}`);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAEliminar(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900">
          Panel Multi-Administrador
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-gray-500">
          Selecciona un conjunto residencial para gestionar sus habitantes, finanzas, documentos,
          eventos y más. Cada conjunto mantiene sus propias reglas.
        </p>
      </div>

      {/* Indicadores */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-3xl bg-primary-500 p-6 text-white shadow-pill">
          <p className="text-sm font-medium text-white/80">Conjuntos</p>
          <p className="mt-1 text-4xl font-extrabold tracking-tight">{conjuntos.length}</p>
          <p className="mt-3 text-xs font-medium text-white/90">Copropiedades a tu cargo</p>
        </div>
        <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
          <p className="text-sm font-medium text-gray-500">Total habitantes</p>
          <p className="mt-1 text-4xl font-extrabold tracking-tight text-gray-900">
            {totalHabitantes.toLocaleString("es-CO")}
          </p>
          <p className="mt-3 text-xs font-medium text-emerald-600">En todos tus conjuntos</p>
        </div>
        <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
          <p className="text-sm font-medium text-gray-500">Conjunto activo</p>
          <p className="mt-1 truncate text-2xl font-extrabold tracking-tight text-gray-900">
            {activo?.nombre ?? "—"}
          </p>
          <p className="mt-3 text-xs font-medium text-gray-400">
            {activo ? "Contexto de trabajo actual" : "Selecciona un conjunto"}
          </p>
        </div>
      </div>

      {/* Sección de conjuntos */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Tus conjuntos</h2>
          <p className="text-sm text-gray-400">Haz clic en uno para gestionarlo</p>
        </div>
        {puedeCrear && (
          <button
            onClick={() => {
              setEditando(null);
              setError(null);
              setFormAbierto(true);
            }}
            className="btn btn-primary px-5 py-2.5 text-sm"
          >
            <Plus className="w-4 h-4" /> Agregar conjunto
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {cargando && !conjuntos.length && (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-56 animate-pulse rounded-3xl bg-gray-100" />
          ))}
        </div>
      )}

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {conjuntos.map((c, i) => {
          const color = colorDeConjunto(conjuntos, c.id);
          return (
          <motion.article
            key={c.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className={`group relative rounded-3xl border bg-white p-5 shadow-card transition-all duration-200 hover:shadow-card-hover ${
              activo?.id === c.id ? "border-primary-300 ring-2 ring-primary-100" : "border-gray-100"
            }`}
          >
            {/* Acciones */}
            {(puedeEditar || puedeEliminar) && (
              <div className="absolute right-4 top-4 flex gap-1 opacity-0 transition group-hover:opacity-100">
                {puedeEditar && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditando(c);
                      setError(null);
                      setFormAbierto(true);
                    }}
                    className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-primary-600"
                    title="Editar conjunto"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                )}
                {puedeEliminar && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setAEliminar(c);
                    }}
                    className="rounded-lg p-2 text-gray-400 hover:bg-red-50 hover:text-red-600"
                    title="Eliminar conjunto"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}

            <button onClick={() => abrir(c)} className="block w-full text-left">
              <div className="flex items-center gap-3">
                <AvatarConjunto
                  nombre={c.nombre}
                  logo={c.logo}
                  color={color}
                  className="h-12 w-12 rounded-2xl text-lg"
                />
                <div className="min-w-0 pr-14">
                  <h3 className="truncate text-base font-bold text-gray-900" title={c.nombre}>
                    {c.nombre}
                  </h3>
                  <p className="flex items-center gap-1 truncate text-xs text-gray-400">
                    <MapPin className="w-3 h-3 shrink-0" />
                    {[c.direccion, c.ciudad].filter(Boolean).join(", ") || "Sin dirección"}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-1 text-xs text-gray-500">
                <Phone className="w-3.5 h-3.5 text-gray-400" />
                {c.telefono || "Sin teléfono"}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-2xl px-3 py-2" style={{ background: color.fondo }}>
                  <p className="flex items-center gap-1 text-[11px] font-medium text-gray-400">
                    <Users className="w-3 h-3" /> Habitantes
                  </p>
                  <p className="text-lg font-extrabold text-gray-900">
                    {(c.habitantes || 0).toLocaleString("es-CO")}
                  </p>
                </div>
                <div className="rounded-2xl px-3 py-2" style={{ background: color.fondo }}>
                  <p className="flex items-center gap-1 text-[11px] font-medium text-gray-400">
                    <IdCard className="w-3 h-3" /> ID Conjunto
                  </p>
                  <p className="text-lg font-extrabold text-gray-900">#{c.id}</p>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
                <span className="flex items-center gap-1 text-xs text-gray-400">
                  <Building2 className="w-3.5 h-3.5" /> {c.propiedades} propiedades
                </span>
                <span className="flex items-center gap-1 text-xs text-gray-400">
                  <Wallet className="w-3.5 h-3.5" /> {moneda(c.saldo)}
                </span>
                <span className="inline-flex items-center gap-1 text-xs font-semibold" style={{ color: color.texto }}>
                  Gestionar <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </button>
          </motion.article>
          );
        })}

        {/* Alta rápida */}
        {puedeCrear && (
          <button
            onClick={() => {
              setEditando(null);
              setError(null);
              setFormAbierto(true);
            }}
            className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-gray-200 bg-white/60 p-6 text-center transition hover:border-primary-300 hover:bg-primary-50/40"
          >
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-primary-50 text-primary-600">
              <Plus className="w-6 h-6" />
            </span>
            <span className="text-base font-bold text-gray-800">Agregar nuevo conjunto</span>
            <span className="max-w-[240px] text-xs text-gray-400">
              Añade otra copropiedad con su propio logo y reglas.
            </span>
          </button>
        )}
      </div>

      {!cargando && !conjuntos.length && (
        <div className="rounded-3xl border border-gray-100 bg-white p-10 text-center text-sm text-gray-400">
          No tienes conjuntos asignados. Pide a un super administrador que te asigne uno.
        </div>
      )}

      {/* Formulario alta / edición */}
      <FormularioConjunto
        abierto={formAbierto}
        conjunto={editando}
        onCerrar={() => {
          setFormAbierto(false);
          setEditando(null);
        }}
        onGuardar={guardar}
        guardando={guardando}
        error={error}
        colorInicial={colorSugerido(conjuntos.length)}
      />

      <ConfirmDialog
        abierto={!!aEliminar}
        titulo="¿Eliminar conjunto?"
        mensaje={
          aEliminar
            ? `Se eliminará "${aEliminar.nombre}". Si tiene datos asociados quedará inactivo en vez de borrarse.`
            : ""
        }
        onConfirmar={confirmarEliminar}
        onCancelar={() => setAEliminar(null)}
      />
    </div>
  );
}

/** Avatar de un conjunto: muestra el logo subido o, si no hay (o falla la
 *  carga), la inicial del nombre con el color asignado. */
function AvatarConjunto({
  nombre,
  logo,
  color,
  className,
}: {
  nombre: string;
  logo?: string | null;
  color: ColorConjunto;
  className: string;
}) {
  const [fallo, setFallo] = useState(false);
  useEffect(() => setFallo(false), [logo]);
  const src = urlLogo(logo);
  return (
    <span
      className={`grid shrink-0 place-items-center overflow-hidden font-bold text-white ${className}`}
      style={{ background: color.gradiente }}
    >
      {src && !fallo ? (
        <img
          src={src}
          alt={`Logo de ${nombre}`}
          className="h-full w-full object-cover"
          onError={() => setFallo(true)}
        />
      ) : (
        nombre.charAt(0).toUpperCase()
      )}
    </span>
  );
}

/* ------------------------------------------------------------------------- */
/* Formulario                                                                 */
/* ------------------------------------------------------------------------- */
function FormularioConjunto({
  abierto,
  conjunto,
  onCerrar,
  onGuardar,
  guardando,
  error,
  colorInicial,
}: {
  abierto: boolean;
  conjunto: Conjunto | null;
  onCerrar: () => void;
  onGuardar: (datos: Partial<Conjunto>) => void;
  guardando: boolean;
  error: string | null;
  colorInicial: string;
}) {
  const [f, setF] = useState<Partial<Conjunto>>({});
  const [hexTexto, setHexTexto] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const [errorLogo, setErrorLogo] = useState<string | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const objectUrlRef = useRef<string | null>(null);

  const liberarPreview = () => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };
  useEffect(() => liberarPreview, []);

  // Al abrir (o cambiar de conjunto) se carga el formulario limpio.
  const clave = abierto ? (conjunto ? `e${conjunto.id}` : "nuevo") : "cerrado";
  useEffect(() => {
    if (clave === "cerrado") return;
    liberarPreview();
    const datos = conjunto ?? {
      nombre: "", nit: "", direccion: "", ciudad: "", telefono: "", correo: "",
      administrador: "", habitantes: 0, cuota: 0, dia_cobro: 5, logo: "",
      color: colorInicial,
      reunion: "todos los residentes", silencio: "22:00 - 06:00",
    };
    setF(datos);
    setHexTexto((datos.color ?? "").startsWith("#") ? String(datos.color) : "");
    setArchivo(null);
    setPreview(urlLogo(conjunto?.logo));
    setErrorLogo(null);
    setArrastrando(false);
    if (inputRef.current) inputRef.current.value = "";
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clave]);

  const set = (campo: keyof Conjunto, valor: unknown) => setF((prev) => ({ ...prev, [campo]: valor }));

  // Estado del selector de color.
  const colorValor = (f.color ?? "").trim().toLowerCase();
  const esAutomatico = colorValor === "";
  const colorVista = resolverColor(colorValor, 0);

  const seleccionarArchivo = (file?: File | null) => {
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      setErrorLogo("Formato no permitido. Usa una imagen PNG, JPG o WEBP.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setErrorLogo("La imagen supera el tamaño máximo de 2 MB.");
      return;
    }
    liberarPreview();
    const url = URL.createObjectURL(file);
    objectUrlRef.current = url;
    setArchivo(file);
    setPreview(url);
    setErrorLogo(null);
  };

  const quitarLogo = () => {
    liberarPreview();
    setArchivo(null);
    setPreview(null);
    setErrorLogo(null);
    set("logo", ""); // el backend lo interpreta como "borrar logo"
    if (inputRef.current) inputRef.current.value = "";
  };

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setErrorLogo(null);
    let rutaLogo: string | null = f.logo ?? null;

    // Si se eligió una imagen nueva, se sube ANTES de crear/editar el conjunto.
    if (archivo) {
      setSubiendo(true);
      try {
        const fd = new FormData();
        fd.append("archivo", archivo);
        const res = await fetch(urlApi("subidas/logo"), {
          method: "POST",
          headers: { Authorization: `Bearer ${getToken() ?? ""}` },
          body: fd,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.logo) {
          throw new Error(data.detail || "No se pudo subir el logo.");
        }
        rutaLogo = data.logo as string;
      } catch (err) {
        setErrorLogo((err as Error).message);
        setSubiendo(false);
        return;
      }
      setSubiendo(false);
    }
    onGuardar({ ...f, logo: rutaLogo === null ? undefined : rutaLogo });
  };

  return (
    <Modal abierto={abierto} onCerrar={onCerrar} titulo={conjunto ? "Editar conjunto" : "Agregar conjunto"}>
      <form onSubmit={enviar} className="space-y-4">
        {error && (
          <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div>
          <label className="label">Nombre del conjunto *</label>
          <input
            className="input"
            required
            value={f.nombre ?? ""}
            onChange={(e) => set("nombre", e.target.value)}
            placeholder="Conjunto Residencial Los Pinos"
          />
        </div>

        {/* ---------------- Logo del conjunto ---------------- */}
        <div
          onDragOver={(e) => { e.preventDefault(); setArrastrando(true); }}
          onDragLeave={() => setArrastrando(false)}
          onDrop={(e) => {
            e.preventDefault();
            setArrastrando(false);
            seleccionarArchivo(e.dataTransfer.files?.[0]);
          }}
          className={`rounded-2xl border p-3 transition ${
            arrastrando ? "border-primary-400 bg-primary-50/60" : "border-gray-100 bg-gray-50/70"
          }`}
        >
          <label className="label mb-2">
            Logo del conjunto <span className="font-normal text-gray-400">(opcional)</span>
          </label>
          <div className="flex items-center gap-3">
            <div className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-2xl border border-dashed border-gray-300 bg-white">
              {preview ? (
                <img
                  src={preview}
                  alt="Vista previa del logo"
                  className="h-full w-full object-contain p-1"
                  onError={() => setPreview(null)}
                />
              ) : (
                <ImagePlus className="h-6 w-6 text-gray-300" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <input
                ref={inputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={(e) => seleccionarArchivo(e.target.files?.[0])}
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="btn btn-outline px-3 py-2 text-xs"
                >
                  <Upload className="h-3.5 w-3.5" /> {preview ? "Cambiar logo" : "Subir logo"}
                </button>
                {preview && (
                  <button
                    type="button"
                    onClick={quitarLogo}
                    className="rounded-xl px-3 py-2 text-xs font-medium text-red-500 transition hover:bg-red-50"
                  >
                    <X className="mr-1 inline h-3.5 w-3.5" /> Quitar
                  </button>
                )}
              </div>
              <p className="mt-1.5 text-[11px] leading-snug text-gray-400">
                PNG, JPG o WEBP · máx. 2 MB. Arrastra la imagen aquí o usa el botón.
              </p>
            </div>
          </div>
          {errorLogo && <p className="mt-2 text-xs font-medium text-red-600">{errorLogo}</p>}
        </div>

        {/* ---------------- Color del conjunto ---------------- */}
        <div className="rounded-2xl border border-gray-100 bg-gray-50/70 p-3">
          <label className="label mb-2 flex items-center gap-1.5">
            <Palette className="h-3.5 w-3.5 text-gray-400" />
            Color del conjunto <span className="font-normal text-gray-400">(opcional)</span>
          </label>
          <div className="flex flex-wrap items-center gap-2">
            {COLORES_CONJUNTO.map((opcion) => {
              const elegido = !esAutomatico && colorValor === opcion.id;
              return (
                <button
                  key={opcion.id}
                  type="button"
                  title={opcion.nombre}
                  aria-label={`Color ${opcion.nombre}`}
                  aria-pressed={elegido}
                  onClick={() => { set("color", opcion.id); setHexTexto(""); }}
                  className={`relative grid h-9 w-9 place-items-center rounded-xl text-white shadow-sm transition hover:scale-105 ${
                    elegido ? "ring-2 ring-gray-800 ring-offset-2" : ""
                  }`}
                  style={{ background: opcion.gradiente }}
                >
                  {elegido && <Check className="h-4 w-4" />}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => { set("color", ""); setHexTexto(""); }}
              className={`ml-1 rounded-xl border px-3 py-2 text-xs font-semibold transition ${
                esAutomatico
                  ? "border-gray-800 bg-white text-gray-800"
                  : "border-gray-200 bg-white text-gray-500 hover:border-gray-300"
              }`}
            >
              Automático
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input
              type="color"
              aria-label="Elegir color personalizado"
              value={colorVista.hex}
              onChange={(e) => { set("color", e.target.value); setHexTexto(e.target.value); }}
              className="h-9 w-9 cursor-pointer rounded-lg border border-gray-200 bg-white p-1"
            />
            <input
              className="input max-w-[150px] text-xs"
              value={hexTexto}
              placeholder="#7C3AED"
              aria-label="Color hexadecimal"
              onChange={(e) => {
                setHexTexto(e.target.value);
                const ok = normalizarColor(e.target.value);
                if (ok && ok.startsWith("#")) set("color", ok);
              }}
            />
            <span className="text-[11px] leading-snug text-gray-400">
              Elige un color de la paleta o escribe tu propio hexadecimal.
            </span>
          </div>
          {hexTexto.trim() !== "" && !normalizarColor(hexTexto) && (
            <p className="mt-1.5 text-xs font-medium text-red-600">
              Escribe un color válido, por ejemplo #7C3AED.
            </p>
          )}

          {/* Vista previa en vivo del tema del conjunto */}
          <div className="mt-3 flex items-center gap-3 rounded-2xl p-3" style={{ background: colorVista.fondo }}>
            <span
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-bold text-white"
              style={{ background: colorVista.gradiente }}
            >
              {(f.nombre ?? "C").charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold" style={{ color: colorVista.texto }}>
                {f.nombre || "Mi conjunto"}
              </p>
              <p className="text-[11px] text-gray-500">Así se verá en el panel y dentro del conjunto.</p>
            </div>
            <span
              className="hidden sm:inline-flex rounded-full px-3 py-1.5 text-[11px] font-bold text-white"
              style={{ background: colorVista.sombras[600] }}
            >
              {esAutomatico ? "Automático" : colorVista.nombre}
            </span>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">NIT</label>
            <input className="input" value={f.nit ?? ""} onChange={(e) => set("nit", e.target.value)} />
          </div>
          <div>
            <label className="label">Ciudad / Localidad</label>
            <input
              className="input"
              value={f.ciudad ?? ""}
              onChange={(e) => set("ciudad", e.target.value)}
              placeholder="Bogotá"
            />
          </div>
        </div>

        <div>
          <label className="label">Dirección</label>
          <input
            className="input"
            value={f.direccion ?? ""}
            onChange={(e) => set("direccion", e.target.value)}
            placeholder="Cra 15 #45-67"
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Teléfono</label>
            <input
              className="input"
              value={f.telefono ?? ""}
              onChange={(e) => set("telefono", e.target.value)}
              placeholder="(+57) 601 555 0101"
            />
          </div>
          <div>
            <label className="label">Correo de contacto</label>
            <input
              className="input"
              type="email"
              value={f.correo ?? ""}
              onChange={(e) => set("correo", e.target.value)}
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Administrador</label>
            <input
              className="input"
              value={f.administrador ?? ""}
              onChange={(e) => set("administrador", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Habitantes</label>
            <input
              className="input"
              type="number"
              min={0}
              value={f.habitantes ?? 0}
              onChange={(e) => set("habitantes", e.target.value)}
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Cuota de administración (COP)</label>
            <input
              className="input"
              type="number"
              min={0}
              value={f.cuota ?? 0}
              onChange={(e) => set("cuota", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Día de cobro</label>
            <input
              className="input"
              type="number"
              min={1}
              max={28}
              value={f.dia_cobro ?? ""}
              onChange={(e) => set("dia_cobro", e.target.value)}
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Reuniones</label>
            <select className="input" value={f.reunion ?? ""} onChange={(e) => set("reunion", e.target.value)}>
              <option value="todos los residentes">todos los residentes</option>
              <option value="solo propietarios">solo propietarios</option>
            </select>
          </div>
          <div>
            <label className="label">Horario de silencio</label>
            <input
              className="input"
              value={f.silencio ?? ""}
              onChange={(e) => set("silencio", e.target.value)}
              placeholder="22:00 - 06:00"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onCerrar} className="btn btn-outline px-5 py-2.5 text-sm">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={guardando || subiendo}
            className="btn btn-primary px-5 py-2.5 text-sm disabled:opacity-60"
          >
            {subiendo ? "Subiendo logo..." : guardando ? "Guardando..." : conjunto ? "Guardar cambios" : "Crear conjunto"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
