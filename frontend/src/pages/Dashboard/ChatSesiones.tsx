import { useState, useEffect, useRef } from "react";
import { MessageCircle, Send, Bot, User, RefreshCw, Inbox } from "lucide-react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { ChatRespuesta, ChatMensaje, ChatEstado } from "@/types";

interface Sesion {
  id: number;
  usuario_id?: number | null;
  titulo: string;
  estado: string;
  fecha_creacion: string;
}

// Historial de conversaciones del asistente del usuario actual.
export default function ChatSesiones() {
  const { usuario } = useAuth();
  const [sesiones, setSesiones] = useState<Sesion[]>([]);
  const [activa, setActiva] = useState<number | null>(null);
  const [mensajes, setMensajes] = useState<ChatMensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [escribiendo, setEscribiendo] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [estadoMotor, setEstadoMotor] = useState<ChatEstado | null>(null);
  const finRef = useRef<HTMLDivElement>(null);

  const cargarEstado = async () => {
    try {
      const est = await api.get<ChatEstado>("/chat/estado");
      setEstadoMotor(est);
    } catch {
      setEstadoMotor(null);
    }
  };

  const cargarSesiones = async () => {
    setCargando(true);
    try {
      const res = await api.get<Sesion[]>(`/chat/sesiones${usuario?.id ? `?usuario_id=${usuario.id}` : ""}`);
      setSesiones(res ?? []);
    } catch {
      setSesiones([]);
    } finally {
      setCargando(false);
    }
  };

  const abrirSesion = async (id: number) => {
    setActiva(id);
    setMensajes([]);
    try {
      const res = await api.get<ChatMensaje[]>(`/chat/sesiones/${id}/mensajes`);
      setMensajes(res ?? []);
    } catch {
      setMensajes([]);
    }
  };

  useEffect(() => {
    cargarSesiones();
    cargarEstado();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Autoscroll.
  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, escribiendo]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    const msg = texto.trim();
    if (!msg || escribiendo) return;
    setTexto("");
    setEscribiendo(true);
    try {
      const res = await api.post<ChatRespuesta>("/chat/ask", { mensaje: msg, sesion_id: activa ?? undefined });
      const nueva = activa ?? res.sesion_id;
      setActiva(nueva);
      await abrirSesion(nueva);
      await cargarSesiones();
    } catch (err) {
      setMensajes((m) => [
        ...m,
        { id: 0, sesion_id: activa ?? 0, rol: "asistente", contenido: `Error: ${(err as Error).message}`, fecha_creacion: "" },
      ]);
    } finally {
      setEscribiendo(false);
    }
  };

  const sesionActiva = sesiones.find((s) => s.id === activa);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Historial del asistente</h2>
          <p className="text-sm text-gray-500">Conversaciones guardadas del chatbot con IA (Ollama) y datos reales del conjunto.</p>
        </div>
        <div className="flex items-center gap-2">
          {estadoMotor && (
            <span
              title={estadoMotor.detalle}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
                estadoMotor.ollama_disponible && estadoMotor.modelo_instalado
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : estadoMotor.ollama_disponible
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-gray-50 text-gray-600 border-gray-200"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  estadoMotor.ollama_disponible && estadoMotor.modelo_instalado
                    ? "bg-emerald-500"
                    : estadoMotor.ollama_disponible
                      ? "bg-amber-500 animate-pulse"
                      : "bg-gray-400"
                }`}
              />
              {estadoMotor.ollama_disponible && estadoMotor.modelo_instalado
                ? `Ollama${estadoMotor.ollama_version ? ` v${estadoMotor.ollama_version}` : ""} · ${estadoMotor.modelo}`
                : estadoMotor.ollama_disponible
                  ? `Preparando ${estadoMotor.modelo}`
                  : estadoMotor.motor_configurado === "ollama"
                    ? "Respaldo local (Ollama desconectado)"
                    : "Motor local"}
            </span>
          )}
          <Button variante="outline" tamano="sm" onClick={() => { cargarSesiones(); cargarEstado(); }}>
            <RefreshCw className="w-4 h-4" /> Actualizar
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Lista de sesiones */}
        <Card className="p-4 h-[520px] overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Inbox className="w-4 h-4 text-primary-500" /> Conversaciones
          </h3>
          {cargando && <p className="text-sm text-gray-400 py-6 text-center">Cargando...</p>}
          {!cargando && !sesiones.length && (
            <p className="text-sm text-gray-400 py-6 text-center">Sin conversaciones aún.</p>
          )}
          <div className="space-y-2">
            {sesiones.map((s) => (
              <button
                key={s.id}
                onClick={() => abrirSesion(s.id)}
                className={`w-full text-left p-3 rounded-xl border transition ${
                  activa === s.id
                    ? "border-primary-300 bg-primary-50"
                    : "border-gray-100 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-primary-500 shrink-0" />
                  <p className="text-sm font-medium text-gray-800 truncate">{s.titulo}</p>
                </div>
                <p className="text-[11px] text-gray-400 mt-1">
                  {new Date(s.fecha_creacion).toLocaleString("es-CO")}
                </p>
              </button>
            ))}
          </div>
        </Card>

        {/* Mensajes + entrada */}
        <div className="lg:col-span-2 flex flex-col">
          <div className="card flex-1 h-[460px] flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-semibold text-gray-800 truncate">
                {sesionActiva?.titulo ?? "Selecciona una conversación"}
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
              {mensajes.length === 0 && activa !== null && (
                <p className="text-sm text-gray-400 text-center py-10">Esta conversación aún no tiene mensajes.</p>
              )}
              {mensajes.map((m) => (
                <div key={m.id} className={`flex gap-2 ${m.rol === "usuario" ? "justify-end" : "justify-start"}`}>
                  {m.rol === "asistente" && (
                    <div className="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm whitespace-pre-line ${
                      m.rol === "usuario"
                        ? "bg-primary-500 text-white rounded-br-sm"
                        : "bg-white border border-gray-200 text-gray-700 rounded-bl-sm"
                    }`}
                  >
                    {m.contenido}
                  </div>
                  {m.rol === "usuario" && (
                    <div className="w-7 h-7 rounded-full bg-gray-300 flex items-center justify-center shrink-0 mt-0.5">
                      <User className="w-4 h-4 text-gray-500" />
                    </div>
                  )}
                </div>
              ))}
              {escribiendo && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white border rounded-2xl px-4 py-2 text-sm text-gray-400">
                    Escribiendo<span className="animate-pulse">...</span>
                  </div>
                </div>
              )}
              <div ref={finRef} />
            </div>
            <form onSubmit={enviar} className="p-3 border-t border-gray-200 bg-white flex gap-2">
              <input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Escribe tu pregunta al asistente..."
                className="input"
              />
              <Button variante="primary" type="submit" disabled={!texto.trim() || escribiendo} className="px-4">
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
