import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2, Check, Eye, EyeOff, X } from "lucide-react";
import AuthShell from "@/components/ui/AuthShell";
import Button from "@/components/ui/Button";
import CodigoInput from "@/components/ui/CodigoInput";
import { api } from "@/lib/api";
import type { Usuario } from "@/types";

/** Requisitos que se muestran en vivo: verde si se cumple, rojo si no. */
function useReglasPassword(contrasena: string, confirmar: string) {
  return useMemo(
    () => [
      { texto: "Al menos 8 caracteres", ok: contrasena.length >= 8 },
      { texto: "Una letra mayúscula", ok: /[A-ZÁÉÍÓÚÑ]/.test(contrasena) },
      { texto: "Una letra minúscula", ok: /[a-záéíóúñ]/.test(contrasena) },
      { texto: "Al menos un número", ok: /\d/.test(contrasena) },
      { texto: "Las contraseñas coinciden", ok: confirmar.length > 0 && contrasena === confirmar },
    ],
    [contrasena, confirmar],
  );
}

function Regla({
  ok,
  tocado,
  className = "",
  children,
}: {
  ok: boolean;
  tocado: boolean;
  className?: string;
  children: ReactNode;
}) {
  const color = ok ? "text-emerald-600" : tocado ? "text-red-500" : "text-gray-400";
  const borde = ok
    ? "border-emerald-500 bg-emerald-50"
    : tocado
      ? "border-red-300 bg-red-50"
      : "border-gray-300 bg-white";
  return (
    <li className={`flex items-center gap-2 text-xs font-medium transition-colors ${color} ${className}`}>
      <span className={`grid h-4 w-4 shrink-0 place-items-center rounded-full border ${borde}`}>
        {ok ? (
          <Check className="h-2.5 w-2.5" strokeWidth={3.5} />
        ) : tocado ? (
          <X className="h-2.5 w-2.5" strokeWidth={3.5} />
        ) : null}
      </span>
      {children}
    </li>
  );
}

/** Botón del "ojito" para mostrar/ocultar la contraseña. */
function BotonOjo({ visible, onCambiar }: { visible: boolean; onCambiar: () => void }) {
  return (
    <button
      type="button"
      onClick={onCambiar}
      aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
      title={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500/30"
    >
      {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
    </button>
  );
}

export default function Register() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [correo, setCorreo] = useState("");
  // Conjuntos activos para el desplegable (cargados al montar la pantalla).
  const [conjuntos, setConjuntos] = useState<{ id: number; nombre: string }[]>([]);
  const [cargandoConjuntos, setCargandoConjuntos] = useState(true);
  const [errorConjuntos, setErrorConjuntos] = useState("");
  const [idConjunto, setIdConjunto] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [verContrasena, setVerContrasena] = useState(false);
  const [verConfirmar, setVerConfirmar] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState<{ mensaje: string } | null>(null);
  const [cargando, setCargando] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [errorCodigo, setErrorCodigo] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [verificado, setVerificado] = useState(false);
  const [reenviado, setReenviado] = useState("");

  // Desplegable de conjuntos: lista pública (sin sesión) de conjuntos activos.
  useEffect(() => {
    let vigente = true;
    const cargar = async () => {
      setCargandoConjuntos(true);
      setErrorConjuntos("");
      try {
        const lista = await api.getPublico<{ id: number; nombre: string }[]>("/conjuntos/publicos");
        if (vigente) setConjuntos(Array.isArray(lista) ? lista : []);
      } catch {
        if (vigente) {
          setErrorConjuntos("No se pudieron cargar los conjuntos.");
          setConjuntos([]);
        }
      } finally {
        if (vigente) setCargandoConjuntos(false);
      }
    };
    cargar();
    return () => {
      vigente = false;
    };
  }, []);

  const reglas = useReglasPassword(contrasena, confirmar);
  const todasCumplidas = reglas.every((r) => r.ok);
  const tocado = contrasena.length > 0 || confirmar.length > 0;
  const fuerza = reglas.slice(0, 4).filter((r) => r.ok).length;
  const colorFuerza = [
    "bg-gray-200",
    "bg-red-400",
    "bg-amber-400",
    "bg-primary-500",
    "bg-emerald-500",
  ][fuerza];
  const textoFuerza = ["Sin evaluar", "Débil", "Regular", "Buena", "Fuerte"][fuerza];

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
    if (!todasCumplidas) {
      setError("La contraseña no cumple todos los requisitos o no coincide.");
      return;
    }
    // Si hay conjuntos disponibles, el residente debe elegir el suyo.
    if (conjuntos.length > 0 && !idConjunto) {
      setError("Selecciona el conjunto al que perteneces.");
      return;
    }
    setCargando(true);
    try {
      // Esta pantalla es EXCLUSIVA para residentes (rol residente).
      // El alta de administradores vive en su propia pantalla (/registro-administrador),
      // que usa la ruta /register/admin del servidor.
      const r = await api.postPublico<Usuario & { verificacion?: { mensaje: string } }>("/register", {
        nombre,
        telefono,
        correo,
        contrasena,
        rol_id: 3,
        id_conjunto: idConjunto ? Number(idConjunto) : undefined,
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
      subtitulo="Regístrate como residente y accede a la información de tu conjunto"
      footer={
        <>
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">
            Inicia sesión
          </Link>
          <br />
          ¿Administras una copropiedad?{" "}
          <Link to="/registro-administrador" className="text-primary-600 font-medium hover:underline">
            Regístrate como administrador
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
            <label className="label" htmlFor="reg-nombre">Nombre completo</label>
            <input id="reg-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} className="input" required />
          </div>
          <div>
            <label className="label" htmlFor="reg-telefono">Teléfono</label>
            <input id="reg-telefono" value={telefono} onChange={(e) => setTelefono(e.target.value)} className="input" placeholder="3001234567" />
          </div>
          <div>
            <label className="label" htmlFor="reg-correo">Correo electrónico</label>
            <input id="reg-correo" type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} className="input" required />
          </div>

          {/* Desplegable de conjuntos: el residente elige su copropiedad */}
          <div>
            <label className="label" htmlFor="reg-conjunto">
              <span className="inline-flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-gray-400" />
                Conjunto
              </span>
            </label>
            <select
              id="reg-conjunto"
              className="input"
              value={idConjunto}
              onChange={(e) => setIdConjunto(e.target.value)}
              disabled={cargandoConjuntos}
              required={conjuntos.length > 0}
            >
              <option value="">
                {cargandoConjuntos
                  ? "Cargando conjuntos..."
                  : conjuntos.length > 0
                    ? "Selecciona tu conjunto"
                    : "No hay conjuntos disponibles"}
              </option>
              {conjuntos.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.nombre}
                </option>
              ))}
            </select>
            {errorConjuntos ? (
              <p className="mt-1.5 text-xs text-red-500">
                {errorConjuntos}{" "}
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="font-semibold underline"
                >
                  Reintentar
                </button>
              </p>
            ) : (
              <p className="mt-1.5 text-xs text-gray-400">
                Elige la copropiedad a la que perteneces. Si no aparece, pide a su administrador que te comparta el nombre exacto.
              </p>
            )}
          </div>

          {/* Contraseña con ojito */}
          <div>
            <label className="label" htmlFor="reg-pass">Contraseña</label>
            <div className="relative">
              <input
                id="reg-pass"
                type={verContrasena ? "text" : "password"}
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                className="input"
                style={{ paddingRight: 44 }}
                placeholder="Mínimo 8 caracteres"
                autoComplete="new-password"
                required
              />
              <BotonOjo visible={verContrasena} onCambiar={() => setVerContrasena((v) => !v)} />
            </div>
          </div>

          {/* Requisitos en vivo */}
          <div className="rounded-2xl border border-gray-100 bg-gray-50/70 px-3.5 py-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                Requisitos de la contraseña
              </p>
              <span className={`text-[11px] font-semibold ${fuerza === 4 ? "text-emerald-600" : "text-gray-400"}`}>
                {textoFuerza}
              </span>
            </div>
            <ul className="grid gap-1.5 sm:grid-cols-2">
              {reglas.map((r, i) => (
                <Regla key={r.texto} ok={r.ok} tocado={tocado} className={i === 4 ? "sm:col-span-2" : ""}>
                  {r.texto}
                </Regla>
              ))}
            </ul>
            <div className="mt-3 flex gap-1" aria-hidden="true">
              {[0, 1, 2, 3].map((i) => (
                <span
                  key={i}
                  className={`h-1.5 flex-1 rounded-full transition-colors ${i < fuerza ? colorFuerza : "bg-gray-200"}`}
                />
              ))}
            </div>
          </div>

          {/* Confirmación con ojito + coincidencia */}
          <div>
            <label className="label" htmlFor="reg-confirmar">Confirmar contraseña</label>
            <div className="relative">
              <input
                id="reg-confirmar"
                type={verConfirmar ? "text" : "password"}
                value={confirmar}
                onChange={(e) => setConfirmar(e.target.value)}
                className={`input ${tocado && reglas[4].ok ? "border-emerald-400" : ""} ${confirmar.length > 0 && contrasena !== confirmar ? "border-red-300" : ""}`}
                style={{ paddingRight: 44 }}
                autoComplete="new-password"
                required
              />
              <BotonOjo visible={verConfirmar} onCambiar={() => setVerConfirmar((v) => !v)} />
            </div>
            {confirmar.length > 0 && (
              <p className={`mt-1.5 flex items-center gap-1 text-xs font-medium ${reglas[4].ok ? "text-emerald-600" : "text-red-500"}`}>
                {reglas[4].ok ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
                {reglas[4].ok ? "Las contraseñas coinciden" : "Las contraseñas no coinciden"}
              </p>
            )}
          </div>

          {error && (
            <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>
          )}

          <Button
            variante="primary"
            tamano="lg"
            className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={cargando || !todasCumplidas}
          >
            {cargando ? "Creando..." : "Registrarse"}
          </Button>
          <p className="text-center text-[11px] text-gray-400">
            Todas las cuentas deben verificar su correo antes de iniciar sesión.
          </p>
        </form>
      )}
    </AuthShell>
  );
}
