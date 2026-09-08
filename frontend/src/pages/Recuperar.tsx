import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import CodigoInput from "@/components/ui/CodigoInput";
import { api } from "@/lib/api";

type Paso = "correo" | "codigo" | "password" | "listo";

// Recuperación de contraseña en 3 pasos: correo → código de 6 dígitos → nueva contraseña.
// (El correo también incluye un enlace directo, por si el usuario prefiere hacer clic.)
export default function Recuperar() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState<Paso>("correo");
  const [correo, setCorreo] = useState("");
  const [codigo, setCodigo] = useState("");
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviarCorreo = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setInfo(""); setCargando(true);
    try {
      const res = await api.postPublico<{ mensaje: string }>("/recuperar-password", { correo });
      setInfo(res.mensaje);
      setCodigo("");
      setPaso("codigo");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCargando(false);
    }
  };

  const validarCodigo = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (codigo.length !== 6) { setError("Ingresa los 6 dígitos del código."); return; }
    setCargando(true);
    try {
      const res = await api.postPublico<{ valido: boolean; token?: string; mensaje?: string }>(
        "/validar-codigo-recuperacion",
        { correo, codigo },
      );
      if (!res.valido || !res.token) { setError(res.mensaje || "El código es incorrecto o ya expiró."); return; }
      setToken(res.token);
      setPaso("password");
    } catch (err) {
      const d = (err as { detail?: string }).detail;
      setError(d || (err as Error).message);
    } finally {
      setCargando(false);
    }
  };

  const guardarPassword = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) { setError("La contraseña debe tener al menos 8 caracteres."); return; }
    if (password !== confirmar) { setError("Las contraseñas no coinciden."); return; }
    setCargando(true);
    try {
      const res = await api.postPublico<{ ok: boolean; mensaje: string }>("/restablecer-password", {
        token,
        nueva_password: password,
      });
      if (!res.ok) { setError(res.mensaje); return; }
      setPaso("listo");
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCargando(false);
    }
  };

  const subtitulos: Record<Paso, string> = {
    correo: "Te enviaremos un código para restablecerla",
    codigo: "Ingresa el código que te enviamos",
    password: "Define tu nueva contraseña",
    listo: "Contraseña actualizada",
  };

  return (
    <AuthShell
      titulo="Recuperar contraseña"
      subtitulo={subtitulos[paso]}
      footer={<Link to="/login" className="text-primary-600 font-medium hover:underline">Volver a iniciar sesión</Link>}
    >
      {paso === "correo" && (
        <form onSubmit={enviarCorreo} className="space-y-4">
          <div>
            <label className="label">Correo electrónico</label>
            <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} className="input" placeholder="tu@correo.com" required />
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando}>
            {cargando ? "Enviando..." : "Enviar código"}
          </Button>
        </form>
      )}

      {paso === "codigo" && (
        <form onSubmit={validarCodigo} className="text-center space-y-4 py-2">
          <div className="text-5xl">📬</div>
          <p className="text-sm text-gray-600">{info}</p>
          <p className="text-xs text-gray-400">
            Código de 6 dígitos enviado a <span className="font-medium text-gray-600">{correo}</span>. Revisa también el spam.
          </p>
          <CodigoInput value={codigo} onChange={setCodigo} disabled={cargando} />
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-left">{error}</div>}
          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando || codigo.length !== 6}>
            {cargando ? "Validando..." : "Continuar"}
          </Button>
          <button
            type="button"
            onClick={() => { setPaso("correo"); setError(""); }}
            className="text-xs text-primary-600 font-semibold hover:underline"
          >
            Cambiar correo o reenviar código
          </button>
        </form>
      )}

      {paso === "password" && (
        <form onSubmit={guardarPassword} className="space-y-4">
          <div>
            <label className="label">Nueva contraseña</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" placeholder="Mínimo 8 caracteres" required />
          </div>
          <div>
            <label className="label">Confirmar contraseña</label>
            <input type="password" value={confirmar} onChange={(e) => setConfirmar(e.target.value)} className="input" required />
          </div>
          {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando}>
            {cargando ? "Guardando..." : "Guardar contraseña"}
          </Button>
        </form>
      )}

      {paso === "listo" && (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">🔐</div>
          <p className="text-lg font-semibold text-gray-800">Contraseña actualizada correctamente.</p>
          <p className="text-sm text-gray-500 mt-1">Redirigiendo al inicio de sesión...</p>
        </div>
      )}
    </AuthShell>
  );
}
