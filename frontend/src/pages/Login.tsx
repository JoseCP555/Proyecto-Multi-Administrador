import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

export default function Login() {
  const { login, cargando } = useAuth();
  const navigate = useNavigate();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [noVerificado, setNoVerificado] = useState(false);
  const [reenviado, setReenviado] = useState("");

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setNoVerificado(false);
    setReenviado("");
    try {
      await login(correo, password);
      navigate("/dashboard");
    } catch (err) {
      const m = (err as Error).message;
      if (m.toLowerCase().includes("verificar tu correo")) setNoVerificado(true);
      setError(m.includes("incorrect") ? "Correo o contraseña incorrectos." : m);
    }
  };

  const reenviar = async () => {
    try {
      const r = await api.postPublico<{ mensaje: string }>("/reenviar-verificacion", { correo });
      setReenviado(r.mensaje);
    } catch (err) {
      setReenviado((err as Error).message);
    }
  };

  return (
    <AuthShell
      titulo="Iniciar Sesión"
      subtitulo="Accede a tu panel de administración"
      footer={
        <>
          ¿No tienes cuenta?{" "}
          <Link to="/register" className="text-primary-600 font-medium hover:underline">
            Regístrate
          </Link>
        </>
      }
    >
      <form onSubmit={enviar} className="space-y-4">
        <div>
          <label className="label">Correo electrónico</label>
          <input
            type="email"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            className="input"
            placeholder="tu@correo.com"
            required
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="label mb-0">Contraseña</label>
            <Link to="/recuperar" className="text-xs text-gray-400 hover:text-primary-600">
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            placeholder="••••••••"
            required
          />
        </div>

        {noVerificado && (
          <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-2xl px-3 py-2 space-y-1">
            <p>Tu cuenta aún no está verificada.</p>
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
              <Link to={`/verificar-codigo?correo=${encodeURIComponent(correo)}`} className="text-primary-600 font-semibold hover:underline">
                Ingresar código
              </Link>
              {reenviado ? <span className="break-all">{reenviado}</span> : (
                <button type="button" onClick={reenviar} className="text-primary-600 font-semibold hover:underline">Reenviar correo</button>
              )}
            </div>
          </div>
        )}
        {error && !noVerificado && (
          <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <Button variante="primary" tamano="lg" className="w-full" disabled={cargando}>
          {cargando ? "Entrando..." : "Ingresar"}
        </Button>

        <p className="text-xs text-gray-400 text-center">
          Demo: admin@multiadmin.com / Admin2026!
        </p>
      </form>
    </AuthShell>
  );
}
