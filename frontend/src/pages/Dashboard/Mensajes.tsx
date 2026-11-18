import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { Link } from "react-router-dom";
import {
  Send,
  Paperclip,
  Search,
  Check,
  CheckCheck,
  CheckCircle2,
  RotateCcw,
  Plus,
  X,
  FileText,
  Download,
  Building2,
  Phone,
  Mail,
  Moon,
  UserCog,
  MessageSquare,
  MessageSquareWarning,
  ChevronLeft,
  Wifi,
  WifiOff,
  Home,
  Sparkles,
  Image as ImageIcon,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import { api, API_BASE, getConjuntoActivo, getToken } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useConjunto } from "@/context/ConjuntoContext";
import { usePermisos } from "@/lib/usePermisos";
import { notificarCambioMensajes } from "@/hooks/useMensajesNoLeidos";
import type { ContactoChat, ConversacionDirecta, MensajeDirecto } from "@/types";

type FiltroAdmin = "todas" | "sin_leer" | "abierta" | "resuelta";

interface InfoAdminResidente {
  conjunto: {
    id: number;
    nombre: string;
    administrador?: string | null;
    correo?: string | null;
    telefono?: string | null;
    silencio?: string | null;
  } | null;
  admin_en_linea: boolean;
  administradores: { id: number; nombre: string; correo: string }[];
}

const SUGERENCIAS_RESIDENTE = [
  "Hola, tengo una consulta sobre mi cuota de administración.",
  "Quisiera consultar disponibilidad de las zonas comunes.",
  "Necesito solicitar un certificado de paz y salvo.",
  "Tengo una consulta sobre convivencia en el conjunto.",
];

// ---------------------------------------------------------------------------
// Utilidades de formato, WebSocket y adjuntos autenticados
// ---------------------------------------------------------------------------
function construirUrlWs(token: string): string {
  const qs = `token=${encodeURIComponent(token)}`;
  if (API_BASE.startsWith("http://") || API_BASE.startsWith("https://")) {
    const base = API_BASE.replace(/^http/, "ws").replace(/\/$/, "");
    return `${base}/mensajes/ws?${qs}`;
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const prefijo = API_BASE.startsWith("/") ? API_BASE : `/${API_BASE}`;
  return `${proto}//${window.location.host}${prefijo.replace(/\/$/, "")}/mensajes/ws?${qs}`;
}

async function fetchAdjuntoBlob(mensajeId: number): Promise<{ blob: Blob; url: string }> {
  const token = getToken();
  const cid = getConjuntoActivo();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (cid) headers["X-Conjunto-Id"] = String(cid);

  const res = await fetch(`${API_BASE}/mensajes/adjunto/${mensajeId}`, { headers });
  if (!res.ok) throw new Error("No se pudo cargar el archivo adjunto.");
  const blob = await res.blob();
  return { blob, url: URL.createObjectURL(blob) };
}

function esImagen(mime?: string | null, nombre?: string | null): boolean {
  if (mime && mime.startsWith("image/")) return true;
  if (!nombre) return false;
  return /\.(png|jpe?g|webp|gif)$/i.test(nombre);
}

function horaCorta(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

function horaLista(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const ahora = new Date();
  const hoy = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
  const fechaMsg = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDias = Math.round((hoy.getTime() - fechaMsg.getTime()) / 86_400_000);
  if (diffDias === 0) return horaCorta(iso);
  if (diffDias === 1) return "Ayer";
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
}

function claveDia(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

function etiquetaDia(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const ahora = new Date();
  const hoy = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
  const fechaMsg = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDias = Math.round((hoy.getTime() - fechaMsg.getTime()) / 86_400_000);
  if (diffDias === 0) return "Hoy";
  if (diffDias === 1) return "Ayer";
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "long", year: "numeric" });
}

function agregarMensajeUnico(lista: MensajeDirecto[], nuevo: MensajeDirecto): MensajeDirecto[] {
  const idx = lista.findIndex((m) => m.id === nuevo.id);
  if (idx >= 0) {
    const copia = [...lista];
    copia[idx] = nuevo;
    return copia;
  }
  return [...lista, nuevo];
}

// ---------------------------------------------------------------------------
// Subcomponentes visuales
// ---------------------------------------------------------------------------
function Avatar({
  nombre,
  foto,
  tamano = "md",
  oscuro = false,
}: {
  nombre?: string | null;
  foto?: string | null;
  tamano?: "sm" | "md" | "lg";
  oscuro?: boolean;
}) {
  const dims =
    tamano === "sm"
      ? "w-8 h-8 text-xs"
      : tamano === "lg"
        ? "w-11 h-11 text-base"
        : "w-10 h-10 text-sm";

  if (foto) {
    return (
      <img
        src={foto}
        alt={nombre || "Avatar"}
        className={`${dims} rounded-full object-cover shrink-0 ring-2 ring-white`}
      />
    );
  }
  const inicial = (nombre || "U").trim().charAt(0).toUpperCase();
  return (
    <div
      className={`${dims} rounded-full shrink-0 flex items-center justify-center font-bold ${
        oscuro ? "bg-dark-100 text-white" : "bg-primary-500 text-white"
      }`}
    >
      {inicial}
    </div>
  );
}

function ImagenAdjunta({
  mensajeId,
  nombre,
  onAmpliar,
}: {
  mensajeId: number;
  nombre?: string | null;
  onAmpliar: (url: string, nombre: string) => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelado = false;
    let creada: string | null = null;
    fetchAdjuntoBlob(mensajeId)
      .then(({ url: objUrl }) => {
        if (cancelado) {
          URL.revokeObjectURL(objUrl);
        } else {
          creada = objUrl;
          setUrl(objUrl);
        }
      })
      .catch(() => {
        if (!cancelado) setError(true);
      });
    return () => {
      cancelado = true;
      if (creada) URL.revokeObjectURL(creada);
    };
  }, [mensajeId]);

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-black/10 px-3 py-2 text-xs">
        <ImageIcon className="w-4 h-4 shrink-0" />
        <span className="truncate">{nombre || "Imagen adjunta"}</span>
      </div>
    );
  }
  if (!url) {
    return <div className="h-36 w-52 animate-pulse rounded-xl bg-black/10" />;
  }
  return (
    <button
      type="button"
      onClick={() => onAmpliar(url, nombre || "Imagen")}
      className="block overflow-hidden rounded-xl border border-black/10 focus:outline-none"
    >
      <img
        src={url}
        alt={nombre || "Imagen adjunta"}
        className="max-h-56 max-w-full rounded-xl object-cover hover:opacity-95 transition"
      />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Componente principal: Chat Residente <-> Administración
// ---------------------------------------------------------------------------
export default function Mensajes() {
  const { usuario, token } = useAuth();
  const { activo: conjunto } = useConjunto();
  const { puede } = usePermisos();

  const esAdmin = puede("mensajes.gestionar");
  const puedeEnviar = puede("mensajes.enviar");
  const conjuntoId = conjunto?.id ?? null;

  const [conversaciones, setConversaciones] = useState<ConversacionDirecta[]>([]);
  const [activaId, setActivaId] = useState<number | null>(null);
  const [mensajes, setMensajes] = useState<MensajeDirecto[]>([]);
  const [cargandoConvs, setCargandoConvs] = useState(true);
  const [cargandoMsgs, setCargandoMsgs] = useState(false);

  const [filtro, setFiltro] = useState<FiltroAdmin>("todas");
  const [buscar, setBuscar] = useState("");
  const [texto, setTexto] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  // Modal "Nuevo chat" (admin) e info de administración (residente).
  const [modalNuevo, setModalNuevo] = useState(false);
  const [contactos, setContactos] = useState<ContactoChat[]>([]);
  const [buscarContacto, setBuscarContacto] = useState("");
  const [infoAdmin, setInfoAdmin] = useState<InfoAdminResidente | null>(null);

  // Lightbox para ver imágenes en grande.
  const [lightbox, setLightbox] = useState<{ url: string; nombre: string } | null>(null);

  // Estado de tiempo real (WebSocket + indicador de escritura).
  const [wsConectado, setWsConectado] = useState(false);
  const [otroEscribiendo, setOtroEscribiendo] = useState<{
    convId: number;
    nombre: string;
  } | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const activaIdRef = useRef<number | null>(null);
  const conjuntoIdRef = useRef<number | null>(null);
  const finRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const typingTimeoutRef = useRef<number | null>(null);
  const typingOtroTimeoutRef = useRef<number | null>(null);
  const enviandoTypingRef = useRef(false);

  useEffect(() => {
    activaIdRef.current = activaId;
  }, [activaId]);

  useEffect(() => {
    conjuntoIdRef.current = conjuntoId;
  }, [conjuntoId]);

  const conversacionActiva = useMemo(
    () => conversaciones.find((c) => c.id === activaId) ?? null,
    [conversaciones, activaId],
  );

  // ---- Carga de conversaciones y contactos -------------------------------
  const cargarConversaciones = useCallback(
    async (silencioso = false) => {
      if (!silencioso) setCargandoConvs(true);
      try {
        const lista = await api.get<ConversacionDirecta[]>("/mensajes/conversaciones");
        const seguras = Array.isArray(lista) ? lista : [];
        setConversaciones(seguras);

        // Para residente: seleccionamos automáticamente su conversación si existe.
        if (!esAdmin) {
          setActivaId(seguras[0]?.id ?? null);
        } else {
          // Para admin: si la conversación seleccionada ya no está en este conjunto, limpiar.
          setActivaId((actual) => {
            if (actual && seguras.some((c) => c.id === actual)) return actual;
            return window.innerWidth >= 1024 ? (seguras[0]?.id ?? null) : null;
          });
        }
      } catch (e) {
        if (!silencioso) setError((e as Error).message);
      } finally {
        if (!silencioso) setCargandoConvs(false);
      }
    },
    [esAdmin],
  );

  const cargarContactos = useCallback(async () => {
    try {
      const res = await api.get<
        | { modo: "admin"; contactos: ContactoChat[] }
        | ({ modo: "residente" } & InfoAdminResidente)
      >("/mensajes/contactos");
      if (res.modo === "admin") {
        setContactos(res.contactos ?? []);
      } else {
        setInfoAdmin({
          conjunto: res.conjunto,
          admin_en_linea: res.admin_en_linea,
          administradores: res.administradores ?? [],
        });
      }
    } catch {
      // No crítico
    }
  }, []);

  const marcarLeida = useCallback(async (convId: number) => {
    try {
      const r = await api.post<{ ok: boolean; marcados: number }>(
        `/mensajes/conversaciones/${convId}/leer`,
      );
      if (r?.marcados > 0) {
        setConversaciones((prev) =>
          prev.map((c) => (c.id === convId ? { ...c, no_leidos: 0 } : c)),
        );
        notificarCambioMensajes();
      }
    } catch {
      // No crítico
    }
  }, []);

  const cargarMensajes = useCallback(
    async (convId: number, silencioso = false) => {
      if (!silencioso) setCargandoMsgs(true);
      try {
        const lista = await api.get<MensajeDirecto[]>(
          `/mensajes/conversaciones/${convId}/mensajes`,
        );
        setMensajes(Array.isArray(lista) ? lista : []);
        await marcarLeida(convId);
      } catch (e) {
        if (!silencioso) setError((e as Error).message);
      } finally {
        if (!silencioso) setCargandoMsgs(false);
      }
    },
    [marcarLeida],
  );

  // Recargar al montar o al cambiar de conjunto activo.
  useEffect(() => {
    setActivaId(null);
    setMensajes([]);
    setError("");
    cargarConversaciones(false);
    cargarContactos();
  }, [conjuntoId, cargarConversaciones, cargarContactos]);

  // Cargar mensajes al seleccionar conversación.
  useEffect(() => {
    if (activaId) {
      cargarMensajes(activaId, false);
    } else {
      setMensajes([]);
    }
  }, [activaId, cargarMensajes]);

  // Autoscroll al final al llegar mensajes nuevos.
  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes.length, otroEscribiendo]);

  // ---- Conexión WebSocket en tiempo real + reconexión automática ---------
  useEffect(() => {
    if (!token) return;
    let cerradoManual = false;
    let intento = 0;
    let timerReconexion: number | null = null;
    let timerPing: number | null = null;

    const conectar = () => {
      if (cerradoManual) return;
      try {
        const ws = new WebSocket(construirUrlWs(token));
        wsRef.current = ws;

        ws.onopen = () => {
          intento = 0;
          setWsConectado(true);
          timerPing = window.setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ tipo: "ping" }));
            }
          }, 25_000);
        };

        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data);
            // Ignorar eventos de otro conjunto distinto al actualmente seleccionado.
            if (
              conjuntoIdRef.current &&
              data.id_conjunto &&
              Number(data.id_conjunto) !== conjuntoIdRef.current
            ) {
              return;
            }
            if (data.tipo === "nuevo_mensaje" && data.mensaje) {
              const msg = data.mensaje as MensajeDirecto;
              const convId = Number(data.conversacion_id);
              const esPropio = esAdmin
                ? msg.rol_remitente === "admin"
                : msg.rol_remitente === "residente";

              if (activaIdRef.current === convId) {
                setMensajes((prev) => agregarMensajeUnico(prev, msg));
                if (!esPropio) {
                  marcarLeida(convId);
                }
              }

              // Actualizar lista de conversaciones (o recargar si es nueva).
              setConversaciones((prev) => {
                const existe = prev.some((c) => c.id === convId);
                if (!existe) {
                  cargarConversaciones(true);
                  return prev;
                }
                const vistaPrevia =
                  msg.contenido || (msg.adjunto_nombre ? `📎 ${msg.adjunto_nombre}` : "Adjunto");
                const actualizadas = prev.map((c) =>
                  c.id === convId
                    ? {
                        ...c,
                        estado: data.estado || c.estado,
                        ultimo_mensaje: vistaPrevia,
                        ultimo_mensaje_en: msg.fecha_creacion,
                        ultimo_remitente_rol: msg.rol_remitente,
                        total_mensajes: c.total_mensajes + 1,
                        no_leidos:
                          !esPropio && activaIdRef.current !== convId
                            ? c.no_leidos + 1
                            : c.no_leidos,
                      }
                    : c,
                );
                return actualizadas.sort((a, b) =>
                  (b.ultimo_mensaje_en || b.fecha_creacion).localeCompare(
                    a.ultimo_mensaje_en || a.fecha_creacion,
                  ),
                );
              });

              // Limpiar indicador de escritura si quien escribía ya mandó mensaje.
              setOtroEscribiendo((prev) => (prev && prev.convId === convId ? null : prev));
              notificarCambioMensajes();
            } else if (data.tipo === "mensajes_leidos") {
              const convId = Number(data.conversacion_id);
              const lectorRol = data.lector_rol as string;
              // Si leyó el otro lado, nuestros mensajes pasan a `leido = true`.
              const misMensajesSon = esAdmin ? "admin" : "residente";
              if (lectorRol !== misMensajesSon && activaIdRef.current === convId) {
                setMensajes((prev) =>
                  prev.map((m) =>
                    m.rol_remitente === misMensajesSon
                      ? { ...m, leido: true, fecha_lectura: data.fecha_lectura }
                      : m,
                  ),
                );
              }
            } else if (data.tipo === "escribiendo") {
              const convId = Number(data.conversacion_id);
              if (data.activo) {
                setOtroEscribiendo({
                  convId,
                  nombre: data.remitente_nombre || (esAdmin ? "Residente" : "Administración"),
                });
                if (typingOtroTimeoutRef.current) {
                  window.clearTimeout(typingOtroTimeoutRef.current);
                }
                typingOtroTimeoutRef.current = window.setTimeout(() => {
                  setOtroEscribiendo(null);
                }, 4000);
              } else {
                setOtroEscribiendo((prev) => (prev && prev.convId === convId ? null : prev));
              }
            } else if (data.tipo === "conversacion_actualizada") {
              const convId = Number(data.conversacion_id);
              setConversaciones((prev) =>
                prev.map((c) => (c.id === convId ? { ...c, estado: data.estado } : c)),
              );
            }
          } catch {
            // Mensaje WS malformado: ignorar.
          }
        };

        ws.onclose = () => {
          setWsConectado(false);
          if (timerPing) window.clearInterval(timerPing);
          if (!cerradoManual) {
            const espera = Math.min(15_000, 2000 * Math.pow(1.6, intento++));
            timerReconexion = window.setTimeout(conectar, espera);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        setWsConectado(false);
      }
    };

    conectar();

    return () => {
      cerradoManual = true;
      if (timerReconexion) window.clearTimeout(timerReconexion);
      if (timerPing) window.clearInterval(timerPing);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [token, esAdmin, cargarConversaciones, marcarLeida]);

  // Respaldo por sondeo suave si el WebSocket no está conectado.
  useEffect(() => {
    if (wsConectado) return;
    const id = window.setInterval(() => {
      cargarConversaciones(true);
      if (activaIdRef.current) {
        cargarMensajes(activaIdRef.current, true);
      }
    }, 6_000);
    return () => window.clearInterval(id);
  }, [wsConectado, cargarConversaciones, cargarMensajes]);

  // ---- Indicador de escritura saliente -----------------------------------
  const emitirEscribiendo = useCallback((activo: boolean, convId?: number | null) => {
    const target = convId ?? activaIdRef.current;
    if (!target || wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(
      JSON.stringify({ tipo: "escribiendo", conversacion_id: target, activo }),
    );
  }, []);

  const manejarCambioTexto = (valor: string) => {
    setTexto(valor);
    if (!activaId) return;
    if (!enviandoTypingRef.current && valor.trim()) {
      enviandoTypingRef.current = true;
      emitirEscribiendo(true, activaId);
    }
    if (typingTimeoutRef.current) window.clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = window.setTimeout(() => {
      enviandoTypingRef.current = false;
      emitirEscribiendo(false, activaId);
    }, 2200);
  };

  // ---- Envío de mensajes y adjuntos --------------------------------------
  const asegurarConversacionResidente = async (): Promise<number> => {
    if (activaId) return activaId;
    const creada = await api.post<ConversacionDirecta>("/mensajes/conversaciones", {});
    setConversaciones((prev) =>
      prev.some((c) => c.id === creada.id) ? prev : [creada, ...prev],
    );
    setActivaId(creada.id);
    return creada.id;
  };

  const enviar = async (textoRapido?: string) => {
    if (!puedeEnviar || enviando) return;
    const contenido = (textoRapido ?? texto).trim();
    const archivoActual = textoRapido ? null : archivo;
    if (!contenido && !archivoActual) return;

    setError("");
    setEnviando(true);
    try {
      const convId = esAdmin ? activaId : await asegurarConversacionResidente();
      if (!convId) return;

      enviandoTypingRef.current = false;
      emitirEscribiendo(false, convId);

      let nuevoMsg: MensajeDirecto;
      if (archivoActual) {
        const fd = new FormData();
        fd.append("contenido", contenido);
        fd.append("archivo", archivoActual);
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const cid = getConjuntoActivo();
        if (cid) headers["X-Conjunto-Id"] = String(cid);

        const res = await fetch(`${API_BASE}/mensajes/conversaciones/${convId}/adjunto`, {
          method: "POST",
          headers,
          body: fd,
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error((data as { detail?: string }).detail || "No se pudo subir el adjunto.");
        }
        nuevoMsg = (await res.json()) as MensajeDirecto;
      } else {
        nuevoMsg = await api.post<MensajeDirecto>(
          `/mensajes/conversaciones/${convId}/mensajes`,
          { contenido },
        );
      }

      setMensajes((prev) => agregarMensajeUnico(prev, nuevoMsg));
      if (!textoRapido) {
        setTexto("");
        setArchivo(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }

      const vistaPrevia =
        nuevoMsg.contenido ||
        (nuevoMsg.adjunto_nombre ? `📎 ${nuevoMsg.adjunto_nombre}` : "Archivo adjunto");

      setConversaciones((prev) =>
        prev
          .map((c) =>
            c.id === convId
              ? {
                  ...c,
                  estado: "abierta",
                  ultimo_mensaje: vistaPrevia,
                  ultimo_mensaje_en: nuevoMsg.fecha_creacion,
                  ultimo_remitente_rol: nuevoMsg.rol_remitente,
                  total_mensajes: c.total_mensajes + 1,
                }
              : c,
          )
          .sort((a, b) =>
            (b.ultimo_mensaje_en || b.fecha_creacion).localeCompare(
              a.ultimo_mensaje_en || a.fecha_creacion,
            ),
          ),
      );
      notificarCambioMensajes();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  const manejarSubmit = (e: FormEvent) => {
    e.preventDefault();
    enviar();
  };

  const manejarTecla = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  const seleccionarArchivo = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) {
      setError("El archivo supera el máximo permitido de 10 MB.");
      e.target.value = "";
      return;
    }
    setError("");
    setArchivo(f);
  };

  const descargarPdf = async (mensajeId: number, nombre: string) => {
    try {
      const { url } = await fetchAdjuntoBlob(mensajeId);
      const a = document.createElement("a");
      a.href = url;
      a.download = nombre || "adjunto.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const alternarEstado = async () => {
    if (!conversacionActiva || !esAdmin) return;
    const nuevoEstado = conversacionActiva.estado === "resuelta" ? "abierta" : "resuelta";
    try {
      const act = await api.put<ConversacionDirecta>(
        `/mensajes/conversaciones/${conversacionActiva.id}/estado`,
        { estado: nuevoEstado },
      );
      setConversaciones((prev) => prev.map((c) => (c.id === act.id ? act : c)));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const abrirChatConResidente = async (contacto: ContactoChat) => {
    setError("");
    try {
      const conv = await api.post<ConversacionDirecta>("/mensajes/conversaciones", {
        residente_usuario_id: contacto.usuario_id,
      });
      setConversaciones((prev) =>
        prev.some((c) => c.id === conv.id) ? prev : [conv, ...prev],
      );
      setActivaId(conv.id);
      setModalNuevo(false);
      setBuscarContacto("");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  // ---- Filtros del panel de administración -------------------------------
  const totalNoLeidos = useMemo(
    () => conversaciones.reduce((acc, c) => acc + (c.no_leidos || 0), 0),
    [conversaciones],
  );

  const conversacionesFiltradas = useMemo(() => {
    const q = buscar.trim().toLowerCase();
    return conversaciones.filter((c) => {
      if (filtro === "sin_leer" && c.no_leidos <= 0) return false;
      if (filtro === "abierta" && c.estado !== "abierta") return false;
      if (filtro === "resuelta" && c.estado !== "resuelta") return false;
      if (!q) return true;
      return (
        (c.residente_nombre || "").toLowerCase().includes(q) ||
        (c.residente_correo || "").toLowerCase().includes(q) ||
        (c.apartamento || "").toLowerCase().includes(q) ||
        (c.ultimo_mensaje || "").toLowerCase().includes(q)
      );
    });
  }, [conversaciones, filtro, buscar]);

  const contactosFiltrados = useMemo(() => {
    const q = buscarContacto.trim().toLowerCase();
    if (!q) return contactos;
    return contactos.filter(
      (c) =>
        c.nombre.toLowerCase().includes(q) ||
        c.correo.toLowerCase().includes(q) ||
        (c.apartamento || "").toLowerCase().includes(q),
    );
  }, [contactos, buscarContacto]);

  // ---- Bloque reutilizable de burbujas + compositor ----------------------
  const renderMensajes = () => {
    if (cargandoMsgs && mensajes.length === 0) {
      return (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="space-y-3 w-full max-w-md">
            <div className="h-12 w-2/3 rounded-2xl bg-gray-200/70 animate-pulse" />
            <div className="h-12 w-1/2 ml-auto rounded-2xl bg-primary-200/60 animate-pulse" />
            <div className="h-16 w-3/4 rounded-2xl bg-gray-200/70 animate-pulse" />
          </div>
        </div>
      );
    }

    if (mensajes.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-10 text-center">
          <div className="w-16 h-16 rounded-3xl bg-primary-50 text-primary-500 flex items-center justify-center mb-4">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-gray-900">
            {esAdmin
              ? `Conversación con ${conversacionActiva?.residente_nombre}`
              : `Comunícate con la Administración`}
          </h3>
          <p className="text-sm text-gray-500 max-w-md mt-1">
            {esAdmin
              ? "Aún no hay mensajes en este chat. Escribe un mensaje para iniciar la conversación con el residente."
              : `Envía un mensaje directo a la administración de ${conjunto?.nombre || "tu conjunto"}. Te responderán por este mismo canal.`}
          </p>

          {!esAdmin && puedeEnviar && (
            <div className="mt-6 w-full max-w-lg">
              <p className="text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2.5 flex items-center justify-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-primary-500" /> Mensajes rápidos para iniciar
              </p>
              <div className="grid sm:grid-cols-2 gap-2">
                {SUGERENCIAS_RESIDENTE.map((s) => (
                  <button
                    key={s}
                    type="button"
                    disabled={enviando}
                    onClick={() => enviar(s)}
                    className="text-left text-xs px-3.5 py-2.5 rounded-2xl bg-white border border-gray-200 text-gray-700 hover:border-primary-300 hover:bg-primary-50/60 hover:text-primary-700 transition shadow-sm"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    let diaAnterior = "";
    return (
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 space-y-3 bg-gray-50/80">
        {mensajes.map((m) => {
          const diaActual = claveDia(m.fecha_creacion);
          const mostrarSeparador = diaActual !== diaAnterior;
          diaAnterior = diaActual;

          const esMio = esAdmin
            ? m.rol_remitente === "admin"
            : m.rol_remitente === "residente";
          const etiquetaAutor = esMio
            ? m.remitente_id === usuario?.id
              ? "Tú"
              : `${m.remitente_nombre || "Administración"}`
            : m.rol_remitente === "admin"
              ? `Administración · ${m.remitente_nombre || "Admin"}`
              : m.remitente_nombre || "Residente";

          const adjImagen = Boolean(m.adjunto && esImagen(m.adjunto_mime, m.adjunto_nombre));

          return (
            <div key={m.id} className="space-y-3">
              {mostrarSeparador && (
                <div className="flex justify-center my-2">
                  <span className="px-3 py-1 rounded-full bg-white border border-gray-200/80 text-[11px] font-semibold text-gray-500 shadow-sm">
                    {etiquetaDia(m.fecha_creacion)}
                  </span>
                </div>
              )}

              <div className={`flex items-end gap-2 ${esMio ? "justify-end" : "justify-start"}`}>
                {!esMio && (
                  <Avatar
                    nombre={m.remitente_nombre}
                    foto={m.remitente_foto}
                    tamano="sm"
                    oscuro={m.rol_remitente === "admin"}
                  />
                )}

                <div
                  className={`max-w-[82%] sm:max-w-[70%] rounded-2xl px-4 py-2.5 shadow-sm ${
                    esMio
                      ? "bg-primary-500 text-white rounded-br-sm"
                      : "bg-white border border-gray-200/80 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  <p
                    className={`text-[11px] font-semibold mb-1 ${
                      esMio ? "text-white/80" : "text-primary-600"
                    }`}
                  >
                    {etiquetaAutor}
                  </p>

                  {m.adjunto && (
                    <div className="mb-2">
                      {adjImagen ? (
                        <ImagenAdjunta
                          mensajeId={m.id}
                          nombre={m.adjunto_nombre}
                          onAmpliar={(url, nombre) => setLightbox({ url, nombre })}
                        />
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            descargarPdf(m.id, m.adjunto_nombre || "documento.pdf")
                          }
                          className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-left text-xs font-medium transition w-full ${
                            esMio
                              ? "bg-white/15 hover:bg-white/25 text-white"
                              : "bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-200"
                          }`}
                        >
                          <FileText className="w-4 h-4 shrink-0" />
                          <span className="truncate flex-1">
                            {m.adjunto_nombre || "Archivo adjunto"}
                          </span>
                          <Download className="w-3.5 h-3.5 shrink-0 opacity-80" />
                        </button>
                      )}
                    </div>
                  )}

                  {m.contenido && (
                    <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
                      {m.contenido}
                    </p>
                  )}

                  <div
                    className={`mt-1 flex items-center justify-end gap-1 text-[10px] ${
                      esMio ? "text-white/75" : "text-gray-400"
                    }`}
                  >
                    <span>{horaCorta(m.fecha_creacion)}</span>
                    {esMio && (
                      <span title={m.leido ? "Leído" : "Enviado"}>
                        {m.leido ? (
                          <CheckCheck className="w-3.5 h-3.5 text-sky-200" />
                        ) : (
                          <Check className="w-3.5 h-3.5 text-white/70" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {otroEscribiendo && otroEscribiendo.convId === activaId && (
          <div className="flex items-center gap-2 text-xs text-gray-500 pl-10">
            <span className="inline-flex gap-1 items-center bg-white border border-gray-200 rounded-full px-3 py-1.5 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce" />
              <span
                className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce"
                style={{ animationDelay: "120ms" }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce"
                style={{ animationDelay: "240ms" }}
              />
              <span className="ml-1.5 font-medium">
                {otroEscribiendo.nombre} está escribiendo…
              </span>
            </span>
          </div>
        )}
        <div ref={finRef} />
      </div>
    );
  };

  const renderCompositor = () => (
    <form
      onSubmit={manejarSubmit}
      className="border-t border-gray-100 bg-white px-4 py-3 shrink-0 space-y-2"
    >
      {archivo && (
        <div className="flex items-center justify-between gap-2 rounded-2xl bg-primary-50 border border-primary-100 px-3.5 py-2 text-xs text-primary-700">
          <div className="flex items-center gap-2 min-w-0">
            {esImagen(archivo.type, archivo.name) ? (
              <ImageIcon className="w-4 h-4 shrink-0" />
            ) : (
              <FileText className="w-4 h-4 shrink-0" />
            )}
            <span className="truncate font-medium">{archivo.name}</span>
            <span className="text-primary-500 shrink-0">
              ({(archivo.size / 1024).toFixed(0)} KB)
            </span>
          </div>
          <button
            type="button"
            onClick={() => {
              setArchivo(null);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
            className="p-1 rounded-full hover:bg-primary-100"
            aria-label="Quitar adjunto"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {conversacionActiva?.estado === "resuelta" && !esAdmin && (
        <p className="text-[11px] text-amber-600 bg-amber-50 border border-amber-100 rounded-xl px-3 py-1.5">
          Esta conversación fue marcada como resuelta. Si escribes un nuevo mensaje se reabrirá automáticamente.
        </p>
      )}

      <div className="flex items-end gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.webp,.gif,.pdf"
          onChange={seleccionarArchivo}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={!puedeEnviar || enviando}
          title="Adjuntar imagen o PDF (máx. 10 MB)"
          className="p-3 rounded-2xl border border-gray-200 text-gray-500 hover:bg-gray-50 hover:text-primary-600 transition shrink-0 disabled:opacity-50"
          aria-label="Adjuntar archivo"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        <textarea
          rows={1}
          value={texto}
          onChange={(e) => manejarCambioTexto(e.target.value)}
          onKeyDown={manejarTecla}
          placeholder={
            esAdmin
              ? "Escribe una respuesta al residente... (Enter para enviar)"
              : "Escribe un mensaje a la administración... (Enter para enviar)"
          }
          disabled={!puedeEnviar || enviando}
          className="input resize-none min-h-[44px] max-h-28 py-2.5 leading-snug"
        />

        <Button
          type="submit"
          variante="primary"
          disabled={!puedeEnviar || enviando || (!texto.trim() && !archivo)}
          className="px-4 py-3 shrink-0"
          aria-label="Enviar mensaje"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">{enviando ? "Enviando…" : "Enviar"}</span>
        </Button>
      </div>
    </form>
  );

  // =========================================================================
  // VISTA RESIDENTE: Chat directo inmediato + tarjeta de info de administración
  // =========================================================================
  if (!esAdmin) {
    const infoConj = infoAdmin?.conjunto ?? conjunto;
    return (
      <div className="space-y-4">
        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError("")} className="text-red-500 hover:text-red-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="grid lg:grid-cols-[1fr_300px] gap-5 items-stretch">
          {/* Panel principal del chat */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-card overflow-hidden flex flex-col h-[calc(100dvh-14rem)] md:h-[calc(100vh-12.5rem)] min-h-[420px] md:min-h-[520px]">
            {/* Header */}
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3 bg-white shrink-0">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-11 h-11 rounded-2xl bg-primary-500 text-white flex items-center justify-center shrink-0 shadow-pill">
                  <Building2 className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-base font-bold text-gray-900 truncate">
                    Administración · {infoConj?.nombre || "Tu conjunto"}
                  </h2>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    {wsConectado ? (
                      <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        Chat en tiempo real
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-600 font-medium">
                        <WifiOff className="w-3 h-3" /> Sincronización automática
                      </span>
                    )}
                    {infoConj?.administrador && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span className="truncate">{infoConj.administrador}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {conversacionActiva && (
                <Badge color={conversacionActiva.estado === "resuelta" ? "success" : "info"}>
                  {conversacionActiva.estado === "resuelta" ? "Resuelta" : "Activa"}
                </Badge>
              )}
            </div>

            {cargandoConvs && !conversacionActiva ? (
              <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
                Cargando conversación…
              </div>
            ) : (
              renderMensajes()
            )}

            {renderCompositor()}
          </div>

          {/* Columna lateral de contexto */}
          <div className="space-y-4">
            <div className="card space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center">
                  <UserCog className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900">Administración</h3>
                  <p className="text-xs text-gray-400">Canal directo del conjunto</p>
                </div>
              </div>

              <div className="space-y-2.5 text-sm">
                <div className="flex items-center gap-2.5 text-gray-600">
                  <Building2 className="w-4 h-4 text-primary-500 shrink-0" />
                  <span className="truncate font-medium">
                    {infoConj?.nombre || "Conjunto residencial"}
                  </span>
                </div>
                {infoConj?.administrador && (
                  <div className="flex items-center gap-2.5 text-gray-600">
                    <UserCog className="w-4 h-4 text-primary-500 shrink-0" />
                    <span className="truncate">{infoConj.administrador}</span>
                  </div>
                )}
                {infoConj?.correo && (
                  <div className="flex items-center gap-2.5 text-gray-600">
                    <Mail className="w-4 h-4 text-primary-500 shrink-0" />
                    <span className="truncate">{infoConj.correo}</span>
                  </div>
                )}
                {infoConj?.telefono && (
                  <div className="flex items-center gap-2.5 text-gray-600">
                    <Phone className="w-4 h-4 text-primary-500 shrink-0" />
                    <span className="truncate">{infoConj.telefono}</span>
                  </div>
                )}
                {infoConj?.silencio && (
                  <div className="flex items-center gap-2.5 text-gray-500 text-xs pt-1 border-t border-gray-100">
                    <Moon className="w-4 h-4 text-primary-500 shrink-0" />
                    <span>Horario de silencio: {infoConj.silencio}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="card bg-primary-50/50 border-primary-100 space-y-2.5">
              <div className="flex items-center gap-2 text-primary-700 font-bold text-sm">
                <MessageSquareWarning className="w-4 h-4" />
                <span>¿Requieres un radicado formal?</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">
                Usa este chat para consultas rápidas o coordinación directa. Si necesitas dejar una petición, queja o reclamo oficial con número de radicado, radícala en PQRS.
              </p>
              <Link
                to="/dashboard/pqrs"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-primary-600 hover:text-primary-700 pt-1"
              >
                Ir a PQRS →
              </Link>
            </div>
          </div>
        </div>

        {/* Lightbox de imagen */}
        {lightbox && (
          <div
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
            onClick={() => setLightbox(null)}
          >
            <div
              className="relative max-w-4xl max-h-[90vh] flex flex-col items-center gap-3"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setLightbox(null)}
                className="self-end p-2 rounded-full bg-white/15 text-white hover:bg-white/25"
                aria-label="Cerrar vista previa"
              >
                <X className="w-5 h-5" />
              </button>
              <img
                src={lightbox.url}
                alt={lightbox.nombre}
                className="max-h-[80vh] max-w-full rounded-2xl shadow-2xl object-contain"
              />
              <p className="text-xs text-white/80">{lightbox.nombre}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // VISTA ADMINISTRADOR: Bandeja dividida (Inbox + Hilo activo)
  // =========================================================================
  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError("")} className="text-red-500 hover:text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="bg-white rounded-3xl border border-gray-100 shadow-card overflow-hidden grid lg:grid-cols-[340px_1fr] h-[calc(100dvh-14rem)] md:h-[calc(100vh-12.5rem)] min-h-[440px] md:min-h-[540px]">
        {/* Panel izquierdo: lista de residentes / conversaciones */}
        <div
          className={`border-r border-gray-100 flex flex-col min-h-0 bg-white ${
            activaId ? "hidden lg:flex" : "flex"
          }`}
        >
          {/* Header de la bandeja */}
          <div className="p-4 border-b border-gray-100 space-y-3 shrink-0">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-gray-900 truncate">
                    Chat residentes
                  </h2>
                  {totalNoLeidos > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-danger text-white text-[11px] font-bold">
                      {totalNoLeidos}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-gray-400 flex items-center gap-1 mt-0.5">
                  {wsConectado ? (
                    <>
                      <Wifi className="w-3 h-3 text-emerald-500" />
                      <span className="text-emerald-600 font-medium">En tiempo real</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-3 h-3 text-amber-500" />
                      <span>Sincronizando…</span>
                    </>
                  )}
                </p>
              </div>

              <Button
                variante="primary"
                tamano="sm"
                onClick={() => {
                  cargarContactos();
                  setModalNuevo(true);
                }}
              >
                <Plus className="w-4 h-4" /> Nuevo
              </Button>
            </div>

            {/* Buscador */}
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                value={buscar}
                onChange={(e) => setBuscar(e.target.value)}
                placeholder="Buscar residente, apto o mensaje…"
                className="input pl-10 py-2 text-xs"
              />
            </div>

            {/* Pestañas de filtro */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
              {(
                [
                  { id: "todas", label: "Todas" },
                  {
                    id: "sin_leer",
                    label: `Sin leer${totalNoLeidos > 0 ? ` (${totalNoLeidos})` : ""}`,
                  },
                  { id: "abierta", label: "Abiertas" },
                  { id: "resuelta", label: "Resueltas" },
                ] as { id: FiltroAdmin; label: string }[]
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFiltro(tab.id)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                    filtro === tab.id
                      ? "bg-primary-500 text-white shadow-sm"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200/70"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Lista scrollable de conversaciones */}
          <div className="flex-1 overflow-y-auto divide-y divide-gray-50">
            {cargandoConvs && conversaciones.length === 0 && (
              <div className="p-4 space-y-3">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="h-16 rounded-2xl bg-gray-100 animate-pulse" />
                ))}
              </div>
            )}

            {!cargandoConvs && conversacionesFiltradas.length === 0 && (
              <div className="text-center px-6 py-12">
                <MessageSquare className="w-9 h-9 mx-auto text-gray-200 mb-2" />
                <p className="text-sm font-semibold text-gray-600">
                  {conversaciones.length === 0
                    ? "Sin conversaciones aún"
                    : "Sin resultados para este filtro"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {conversaciones.length === 0
                    ? "Inicia un chat con un residente o espera sus mensajes aquí."
                    : "Prueba cambiando el filtro o limpiando la búsqueda."}
                </p>
                {conversaciones.length === 0 && (
                  <Button
                    variante="outline"
                    tamano="sm"
                    className="mt-4"
                    onClick={() => {
                      cargarContactos();
                      setModalNuevo(true);
                    }}
                  >
                    <Plus className="w-4 h-4" /> Iniciar chat
                  </Button>
                )}
              </div>
            )}

            {conversacionesFiltradas.map((c) => {
              const seleccionada = c.id === activaId;
              const prefijo = c.ultimo_remitente_rol === "admin" ? "Tú: " : "";
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setActivaId(c.id)}
                  className={`w-full text-left px-4 py-3.5 flex items-start gap-3 transition relative ${
                    seleccionada
                      ? "bg-primary-50/75"
                      : c.no_leidos > 0
                        ? "bg-white hover:bg-gray-50"
                        : "bg-white hover:bg-gray-50"
                  }`}
                >
                  {seleccionada && (
                    <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-primary-500" />
                  )}
                  <Avatar nombre={c.residente_nombre} foto={c.residente_foto} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={`text-sm truncate ${
                          c.no_leidos > 0
                            ? "font-bold text-gray-900"
                            : "font-semibold text-gray-800"
                        }`}
                      >
                        {c.residente_nombre}
                      </p>
                      <span className="text-[11px] text-gray-400 shrink-0">
                        {horaLista(c.ultimo_mensaje_en || c.fecha_creacion)}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 mt-0.5">
                      {c.apartamento && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-gray-100 text-gray-600">
                          <Home className="w-2.5 h-2.5" /> {c.apartamento}
                        </span>
                      )}
                      {c.estado === "resuelta" && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700">
                          Resuelta
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between gap-2 mt-1">
                      <p
                        className={`text-xs truncate ${
                          c.no_leidos > 0
                            ? "font-semibold text-gray-800"
                            : "text-gray-500"
                        }`}
                      >
                        {c.ultimo_mensaje ? `${prefijo}${c.ultimo_mensaje}` : "Conversación iniciada"}
                      </p>
                      {c.no_leidos > 0 && (
                        <span className="min-w-[20px] h-5 px-1.5 rounded-full bg-primary-500 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                          {c.no_leidos > 99 ? "99+" : c.no_leidos}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Panel derecho: hilo de conversación activo */}
        <div
          className={`flex flex-col min-h-0 bg-white ${
            activaId ? "flex" : "hidden lg:flex"
          }`}
        >
          {!conversacionActiva ? (
            <div className="flex-1 flex flex-col items-center justify-center p-10 text-center bg-gray-50/40">
              <div className="w-16 h-16 rounded-3xl bg-primary-50 text-primary-500 flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-gray-800">
                Selecciona una conversación
              </h3>
              <p className="text-sm text-gray-500 max-w-sm mt-1">
                Elige un residente de la lista izquierda para leer su historial y responder en tiempo real, o inicia un chat nuevo.
              </p>
              <Button
                variante="primary"
                tamano="sm"
                className="mt-5"
                onClick={() => {
                  cargarContactos();
                  setModalNuevo(true);
                }}
              >
                <Plus className="w-4 h-4" /> Nuevo chat con residente
              </Button>
            </div>
          ) : (
            <>
              {/* Cabecera del hilo */}
              <div className="px-4 sm:px-6 py-3.5 border-b border-gray-100 flex items-center justify-between gap-3 shrink-0 bg-white">
                <div className="flex items-center gap-3 min-w-0">
                  <button
                    type="button"
                    onClick={() => setActivaId(null)}
                    className="lg:hidden p-1.5 rounded-full text-gray-500 hover:bg-gray-100"
                    aria-label="Volver a la lista"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <Avatar
                    nombre={conversacionActiva.residente_nombre}
                    foto={conversacionActiva.residente_foto}
                    tamano="lg"
                  />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm sm:text-base font-bold text-gray-900 truncate">
                        {conversacionActiva.residente_nombre}
                      </h3>
                      {conversacionActiva.apartamento && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary-50 text-primary-700">
                          <Home className="w-3 h-3" /> {conversacionActiva.apartamento}
                        </span>
                      )}
                      <Badge
                        color={conversacionActiva.estado === "resuelta" ? "success" : "info"}
                      >
                        {conversacionActiva.estado === "resuelta" ? "Resuelta" : "Abierta"}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400 truncate mt-0.5">
                      {[
                        conversacionActiva.residente_correo,
                        conversacionActiva.residente_telefono,
                      ]
                        .filter(Boolean)
                        .join(" · ") || "Residente del conjunto"}
                    </p>
                  </div>
                </div>

                <Button
                  variante="outline"
                  tamano="sm"
                  onClick={alternarEstado}
                  className="shrink-0"
                >
                  {conversacionActiva.estado === "resuelta" ? (
                    <>
                      <RotateCcw className="w-3.5 h-3.5" /> Reabrir
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="hidden sm:inline">Marcar resuelta</span>
                    </>
                  )}
                </Button>
              </div>

              {renderMensajes()}
              {renderCompositor()}
            </>
          )}
        </div>
      </div>

      {/* Modal: iniciar conversación con cualquier residente del conjunto */}
      <Modal
        abierto={modalNuevo}
        onCerrar={() => {
          setModalNuevo(false);
          setBuscarContacto("");
        }}
        titulo="Iniciar chat con residente"
      >
        <div className="space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              value={buscarContacto}
              onChange={(e) => setBuscarContacto(e.target.value)}
              placeholder="Buscar por nombre, correo o apartamento…"
              className="input pl-10"
              autoFocus
            />
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-gray-100 rounded-2xl border border-gray-100">
            {contactosFiltrados.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8 px-4">
                No se encontraron residentes activos en este conjunto.
              </p>
            ) : (
              contactosFiltrados.map((c) => (
                <button
                  key={c.usuario_id}
                  type="button"
                  onClick={() => abrirChatConResidente(c)}
                  className="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-primary-50/50 transition text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Avatar nombre={c.nombre} foto={c.foto} tamano="sm" />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-800 truncate">
                        {c.nombre}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {[c.apartamento ? `Apto ${c.apartamento}` : null, c.correo]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold text-primary-600 shrink-0">
                    {c.conversacion_id ? "Abrir chat →" : "Iniciar →"}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      </Modal>

      {/* Lightbox de imagen */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setLightbox(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] flex flex-col items-center gap-3"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setLightbox(null)}
              className="self-end p-2 rounded-full bg-white/15 text-white hover:bg-white/25"
              aria-label="Cerrar vista previa"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={lightbox.url}
              alt={lightbox.nombre}
              className="max-h-[80vh] max-w-full rounded-2xl shadow-2xl object-contain"
            />
            <p className="text-xs text-white/80">{lightbox.nombre}</p>
          </div>
        </div>
      )}
    </div>
  );
}
