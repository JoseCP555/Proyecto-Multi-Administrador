import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import { api } from "@/lib/api";

export default function RestablecerPassword() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);
  const [tokenValido, setTokenValido] = useState<boolean | null>(null);

  useEffect(() => {
    api.get<{ valido: boolean }>(`/validar-token-recuperacion/${token}`)
      .then((r) => setTokenValido(r.valido))
      .catch(() => setTokenValido(false));
  }, [token]);

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (password !== confirmar) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setCargando(true);
    try {
      const res = await api.postPublico<{ ok: boolean; mensaje: string }>("/restablecer-password", {
        token,
        nueva_password: password,
      });
      if (!res.ok) { setError(res.mensaje); return; }
      setMensaje(res.mensaje || "Contraseña actualizada.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <AuthShell
      titulo="Restablecer contraseña"
      subtitulo="Define una nueva contraseña para tu cuenta"
      footer={
        <Link to="/login" className="text-primary-600 font-medium hover:underline">
          Volver a iniciar sesión
        </Link>
      }
    >
      {tokenValido === false && !mensaje ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">⌛</div>
          <p className="text-lg font-semibold text-gray-800">Este enlace es inválido o ya expiró.</p>
          <p className="text-sm text-gray-500 mt-1">Los enlaces duran 30 minutos.</p>
          <Link to="/recuperar" className="btn btn-primary px-6 py-3 mt-5 inline-flex">Solicitar uno nuevo</Link>
        </div>
      ) : mensaje ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">🔐</div>
          <p className="text-lg font-semibold text-gray-800">{mensaje}</p>
          <Link to="/login" className="mt-3 inline-block text-primary-600 font-medium hover:underline">
            Ir a iniciar sesión
          </Link>
        </div>
      ) : (
        <form onSubmit={enviar} className="space-y-4">
          <div>
            <label className="label">Nueva contraseña</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" placeholder="Mínimo 8 caracteres" required />
          </div>
          <div>
            <label className="label">Confirmar contraseña</label>
            <input type="password" value={confirmar} onChange={(e) => setConfirmar(e.target.value)} className="input" required />
          </div>
          {error && (
            <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>
          )}
          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando}>
            {cargando ? "Guardando..." : "Guardar contraseña"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
