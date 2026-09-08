import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import CodigoInput from "@/components/ui/CodigoInput";
import { api } from "@/lib/api";

/** Verificación de cuenta con el código de 6 dígitos (para quien cerró la pantalla de registro). */
export default function VerificarCodigo() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [correo, setCorreo] = useState(params.get("correo") ?? "");
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState("");
  const [reenviado, setReenviado] = useState("");
  const [cargando, setCargando] = useState(false);
  const [ok, setOk] = useState(false);

  const verificar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (codigo.length !== 6) { setError("Ingresa los 6 dígitos del código."); return; }
    setCargando(true);
    try {
      const r = await api.postPublico<{ ok: boolean; mensaje: string }>("/verificar-codigo", { correo, codigo });
      if (!r.ok) { setError(r.mensaje); return; }
      setOk(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      const d = (err as { detail?: string }).detail;
      setError(d || (err as Error).message);
    } finally {
      setCargando(false);
    }
  };

  const reenviar = async () => {
    if (!correo) { setError("Escribe tu correo para reenviar el código."); return; }
    setReenviado("");
    try {
      const r = await api.postPublico<{ mensaje: string }>("/reenviar-verificacion", { correo });
      setReenviado(r.mensaje);
      setCodigo("");
    } catch (err) {
      setReenviado((err as Error).message);
    }
  };

  return (
    <AuthShell
      titulo="Verificar cuenta"
      subtitulo="Ingresa el código de 6 dígitos que te enviamos por correo"
      footer={<Link to="/login" className="text-primary-600 font-medium hover:underline">Ir a iniciar sesión</Link>}
    >
      {ok ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">✅</div>
          <p className="text-lg font-semibold text-gray-800">¡Correo verificado!</p>
          <p className="text-sm text-gray-500 mt-1">Redirigiendo al inicio de sesión...</p>
        </div>
      ) : (
        <form onSubmit={verificar} className="space-y-4">
          <div>
            <label className="label">Correo electrónico</label>
            <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} className="input" placeholder="tu@correo.com" required />
          </div>
          <div>
            <label className="label text-center block">Código</label>
            <CodigoInput value={codigo} onChange={setCodigo} disabled={cargando} />
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando || codigo.length !== 6}>
            {cargando ? "Verificando..." : "Verificar"}
          </Button>
          <p className="text-xs text-gray-400 text-center">
            {reenviado ? reenviado : (
              <button type="button" onClick={reenviar} className="text-primary-600 font-semibold hover:underline">
                Reenviar código
              </button>
            )}
          </p>
        </form>
      )}
    </AuthShell>
  );
}
