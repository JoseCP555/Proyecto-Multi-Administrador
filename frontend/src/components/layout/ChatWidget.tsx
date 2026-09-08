import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, User, Bot, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import type { ChatRespuesta, ChatMensaje } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { usePermisos } from "@/lib/usePermisos";

interface Msg {
  rol: "usuario" | "asistente";
  contenido: string;
}

const SUGERENCIAS = [
  "¿Cuál es el saldo?",
  "¿Hay pagos pendientes?",
  "¿Cuántas propiedades hay?",
  "Lista los próximos eventos",
];

// Guarda/lee la sesión de chat entre recargas para conservar el historial.
const SESSION_KEY = "ma_chat_sesion";

export default function ChatWidget() {
  const { token } = useAuth();
  const { puede } = usePermisos();
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<Msg[]>([
    {
      rol: "asistente",
      contenido:
        "¡Hola! 👋 Soy el asistente de Multi-Administrador. Pregúntame sobre finanzas, pagos, mantenimiento, propiedades, documentos o eventos.",
    },
  ]);
  const [texto, setTexto] = useState("");
  const [escribiendo, setEscribiendo] = useState(false);
  const [sesionId, setSesionId] = useState<number | undefined>(() => {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? Number(raw) : undefined;
  });
  const finRef = useRef<HTMLDivElement>(null);

  // Al abrir, si existe una sesión guardada, restaura su historial.
  useEffect(() => {
    if (!abierto || !token || !sesionId) return;
    api
      .get<ChatMensaje[]>(`/chat/sesiones/${sesionId}/mensajes`)
      .then((hist) => {
        if (hist?.length) {
          setMensajes(
            hist.map((m) => ({
              rol: (m.rol === "usuario" || m.rol === "asistente" ? m.rol : "asistente") as Msg["rol"],
              contenido: m.contenido,
            })),
          );
        }
      })
      .catch(() => {
        // La sesión pudo expirar; se inicia una nueva conversación.
        setSesionId(undefined);
        localStorage.removeItem(SESSION_KEY);
      });
  }, [abierto, token, sesionId]);

  // Autoscroll al final cuando hay nuevos mensajes.
  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, escribiendo]);

  const nuevaSesion = () => {
    setSesionId(undefined);
    localStorage.removeItem(SESSION_KEY);
    setMensajes([
      {
        rol: "asistente",
        contenido:
          "¡Hola! 👋 Soy el asistente de Multi-Administrador. Pregúntame sobre finanzas, pagos, mantenimiento, propiedades, documentos o eventos.",
      },
    ]);
  };

  const enviar = async (textoArg?: string) => {
    const mensaje = (textoArg ?? texto).trim();
    if (!mensaje || escribiendo) return;
    setMensajes((m) => [...m, { rol: "usuario", contenido: mensaje }]);
    setTexto("");
    setEscribiendo(true);
    try {
      const res = await api.post<ChatRespuesta>("/chat/ask", {
        mensaje,
        sesion_id: sesionId,
      });
      setSesionId(res.sesion_id);
      localStorage.setItem(SESSION_KEY, String(res.sesion_id));
      setMensajes((m) => [...m, { rol: "asistente", contenido: res.respuesta }]);
    } catch (e) {
      const err = e as Error;
      setMensajes((m) => [
        ...m,
        {
          rol: "asistente",
          contenido: `No pude conectar con el asistente: ${err.message}. Verifica que el backend esté activo.`,
        },
      ]);
    } finally {
      setEscribiendo(false);
    }
  };

  // Si el rol no tiene el permiso chat.usar, no se muestra el widget.
  if (!puede("chat.usar")) return null;

  return (
    <>
      {/* Botón flotante */}
      {!abierto && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setAbierto(true)}
          className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-primary-500 text-white shadow-lg flex items-center justify-center"
          aria-label="Abrir chat"
        >
          <MessageCircle className="w-6 h-6" />
        </motion.button>
      )}

      {/* Panel del chat */}
      <AnimatePresence>
        {abierto && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            className="fixed bottom-6 right-6 z-40 w-[94vw] max-w-sm h-[520px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200"
          >
            {/* Encabezado */}
            <div className="bg-dark-100 text-white px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">Asistente Multi-Admin</p>
                  <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> En línea
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={nuevaSesion}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-gray-300"
                  title="Nueva conversación"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button onClick={() => setAbierto(false)} className="p-1.5 rounded-lg hover:bg-white/10">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Mensajes */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
              {mensajes.map((m, i) => (
                <div
                  key={i}
                  className={`flex gap-2 ${m.rol === "usuario" ? "justify-end" : "justify-start"}`}
                >
                  {m.rol === "asistente" && (
                    <div className="w-7 h-7 rounded-full bg-primary-500 shrink-0 flex items-center justify-center mt-0.5">
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
                    <div className="w-7 h-7 rounded-full bg-gray-300 shrink-0 flex items-center justify-center mt-0.5">
                      <User className="w-4 h-4 text-gray-500" />
                    </div>
                  )}
                </div>
              ))}

              {/* Sugerencias rápidas */}
              {mensajes.length <= 1 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {SUGERENCIAS.map((s) => (
                    <button
                      key={s}
                      onClick={() => enviar(s)}
                      className="text-xs px-3 py-1.5 rounded-full bg-white border border-primary-200 text-primary-600 hover:bg-blue-50 transition"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {escribiendo && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2 text-sm text-gray-400">
                    Escribiendo<span className="animate-pulse">...</span>
                  </div>
                </div>
              )}
              <div ref={finRef} />
            </div>

            {/* Entrada */}
            <div className="p-3 border-t border-gray-200 bg-white">
              <div className="flex items-center gap-2">
                <input
                  value={texto}
                  onChange={(e) => setTexto(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && enviar()}
                  placeholder="Escribe tu pregunta..."
                  className="input"
                  disabled={!token}
                />
                <button
                  onClick={() => enviar()}
                  disabled={!texto.trim() || escribiendo}
                  className="btn btn-primary p-3"
                  aria-label="Enviar"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
