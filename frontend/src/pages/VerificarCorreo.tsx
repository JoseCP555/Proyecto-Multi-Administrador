import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2, MailCheck, MailWarning } from "lucide-react";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import { api } from "@/lib/api";

type Estado = "cargando" | "ok" | "expirado" | "invalido";

/** Confirma el correo con el token del enlace y permite reenviar si expiró. */
export default function VerificarCorreo() {
  const { token } = useParams<{ token: string }>();
  const [estado, setEstado] = useState<Estado>("cargando");
  const [mensaje, setMensaje] = useState("");
  const [correo, setCorreo] = useState("");
  const [reenviado, setReenviado] = useState("");
  const [enviando, setEnviando] = useState(false);

  const verificado = useRef<string | null>(null);

  useEffect(() => {
    if (!token || verificado.current === token) return; // evita la doble llamada de StrictMode
    verificado.current = token;
    api
      .get<{ ok: boolean; estado: Estado; mensaje: string }>(`/verificar-correo/${token}`)
      .then((r) => { setEstado(r.estado); setMensaje(r.mensaje); })
      .catch((e) => { setEstado("invalido"); setMensaje((e as Error).message); });
  }, [token]);

  const reenviar = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    try {
      const r = await api.postPublico<{ mensaje: string }>("/reenviar-verificacion", { correo });
      setReenviado(r.mensaje);
    } catch (err) {
      setReenviado((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthShell
      titulo="Verificación de correo"
      footer={<Link to="/login" className="text-primary-600 font-medium hover:underline">Ir a iniciar sesión</Link>}
    >
      <div className="text-center py-4">
        {estado === "cargando" && (
          <>
            <Loader2 className="w-10 h-10 mx-auto text-primary-500 animate-spin" />
            <p className="text-sm text-gray-500 mt-3">Verificando tu correo...</p>
          </>
        )}
        {estado === "ok" && (
          <>
            <div className="mx-auto w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center">
              <MailCheck className="w-8 h-8 text-emerald-600" />
            </div>
            <p className="text-lg font-bold text-gray-900 mt-4">{mensaje}</p>
            <Link to="/login" className="btn btn-primary px-6 py-3 mt-5 inline-flex">Iniciar sesión</Link>
          </>
        )}
        {(estado === "expirado" || estado === "invalido") && (
          <>
            <div className="mx-auto w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
              <MailWarning className="w-8 h-8 text-red-500" />
            </div>
            <p className="text-lg font-bold text-gray-900 mt-4">{mensaje}</p>
            {!reenviado ? (
              <form onSubmit={reenviar} className="mt-5 space-y-3 text-left">
                <label className="label">Reenviar enlace de verificación a:</label>
                <input type="email" className="input" value={correo} onChange={(e) => setCorreo(e.target.value)} placeholder="tu@correo.com" required />
                <Button variante="primary" className="w-full" disabled={enviando}>{enviando ? "Enviando..." : "Reenviar verificación"}</Button>
              </form>
            ) : (
              <p className="text-sm text-gray-600 mt-4 break-all">{reenviado}</p>
            )}
          </>
        )}
      </div>
    </AuthShell>
  );
}
