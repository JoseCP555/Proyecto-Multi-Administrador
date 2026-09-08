import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import CodigoInput from "@/components/ui/CodigoInput";
import { api } from "@/lib/api";
import type { Usuario } from "@/types";

export default function Register() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");
  const [exito, setExito] = useState<{ mensaje: string } | null>(null);
  const [cargando, setCargando] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [errorCodigo, setErrorCodigo] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [verificado, setVerificado] = useState(false);
  const [reenviado, setReenviado] = useState("");

  const verificarCodigo = async (e: FormEvent) => {
    e.preventDefault();
    setErrorCodigo("");
    if (codigo.length !== 6) { setErrorCodigo("Ingresa los 6 dígitos del código."); return; }
    setVerificando(true);
    try {
      const r = await api.postPublico<{ ok: boolean; mensaje: string }>("/verificar-codigo", { correo, codigo });
      if (!r.ok) { setErrorCodigo(r.mensaje); return; }
      setVerificado(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      const d = (err as { detail?: string }).detail;
      setErrorCodigo(d || (err as Error).message);
    } finally {
      setVerificando(false);
    }
  };

  const reenviar = async () => {
    setReenviado("");
    try {
      const r = await api.postPublico<{ mensaje: string }>("/reenviar-verificacion", { correo });
      setReenviado(r.mensaje);
      setCodigo("");
    } catch (err) {
      setReenviado((err as Error).message);
    }
  };

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (contrasena.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (contrasena !== confirmar) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setCargando(true);
    try {
      const r = await api.postPublico<Usuario & { verificacion?: { mensaje: string } }>("/register", {
        nombre,
        telefono,
        correo,
        contrasena,
        rol_id: 3, // residente por defecto
      });
      if (r.verificacion) {
        setExito({ mensaje: r.verificacion.mensaje });
      } else {
        setExito({ mensaje: "Redirigiendo al inicio de sesión..." });
        setTimeout(() => navigate("/login"), 1500);
      }
    } catch (err) {
      const d = (err as { detail?: string }).detail;
      const m = (err as Error).message;
      setError(d || m);
    } finally {
      setCargando(false);
    }
  };

  return (
    <AuthShell
      titulo="Crear cuenta"
      subtitulo="Comienza a administrar tu copropiedad"
      footer={
        <>
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">
            Inicia sesión
          </Link>
        </>
      }
    >
      {verificado ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">✅</div>
          <p className="text-lg font-semibold text-gray-800">¡Correo verificado!</p>
          <p className="text-sm text-gray-500 mt-2">Tu cuenta está activa. Redirigiendo al inicio de sesión...</p>
          <Link to="/login" className="mt-5 inline-block text-primary-600 font-medium hover:underline">Ir a iniciar sesión</Link>
        </div>
      ) : exito ? (
        <form onSubmit={verificarCodigo} className="text-center py-4 space-y-4">
          <div className="text-5xl">📬</div>
          <p className="text-lg font-semibold text-gray-800">¡Cuenta creada!</p>
          <p className="text-sm text-gray-500">
            Te enviamos un <span className="font-semibold text-gray-700">código de 6 dígitos</span> a{" "}
            <span className="font-medium text-gray-700">{correo}</span>. Escríbelo aquí para activar tu cuenta.
          </p>
          <CodigoInput value={codigo} onChange={setCodigo} disabled={verificando} />
          {errorCodigo && (
            <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-left">{errorCodigo}</div>
          )}
          <Button variante="primary" tamano="lg" className="w-full" disabled={verificando || codigo.length !== 6}>
            {verificando ? "Verificando..." : "Verificar código"}
          </Button>
          <div className="text-xs text-gray-400 space-y-1">
            <p>También puedes usar el botón del correo. Revisa la carpeta de spam si no lo ves.</p>
            {reenviado ? (
              <p className="text-gray-600">{reenviado}</p>
            ) : (
              <button type="button" onClick={reenviar} className="text-primary-600 font-semibold hover:underline">
                Reenviar código
              </button>
            )}
          </div>
        </form>
      ) : (
        <form onSubmit={enviar} className="space-y-4">
          <div>
            <label className="label">Nombre completo</label>
            <input value={nombre} onChange={(e) => setNombre(e.target.value)} className="input" required />
          </div>
          <div>
            <label className="label">Teléfono</label>
            <input value={telefono} onChange={(e) => setTelefono(e.target.value)} className="input" placeholder="3001234567" />
          </div>
          <div>
            <label className="label">Correo electrónico</label>
            <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} className="input" required />
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input type="password" value={contrasena} onChange={(e) => setContrasena(e.target.value)} className="input" placeholder="Mínimo 8 caracteres" required />
          </div>
          <div>
            <label className="label">Confirmar contraseña</label>
            <input type="password" value={confirmar} onChange={(e) => setConfirmar(e.target.value)} className="input" required />
          </div>

          {error && (
            <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>
          )}

          <Button variante="primary" tamano="lg" className="w-full" disabled={cargando}>
            {cargando ? "Creando..." : "Registrarse"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
