import { useEffect, useState, type FormEvent } from "react";
import { UserRound, Camera, Save, KeyRound, Activity } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { useFetch } from "@/hooks/useFetch";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { fechaHora, capitalizar } from "@/lib/format";
import type { Perfil as PerfilTipo, Usuario } from "@/types";

interface Actividad {
  id: number;
  accion: string;
  modulo: string;
  detalle?: string | null;
  fecha_creacion: string;
}

/** Datos personales del usuario autenticado — UH-20. */
export default function Perfil() {
  const { usuario, actualizarUsuario } = useAuth();
  const { data: perfil, cargar } = useFetch<PerfilTipo>("/perfil");
  const { data: actividad } = useFetch<Actividad[]>("/perfil/actividad?limite=20");

  const [form, setForm] = useState({ nombre: "", telefono: "", correo: "", foto: "" });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [pass, setPass] = useState({ actual: "", nueva: "", repetir: "" });
  const [passMsg, setPassMsg] = useState("");

  useEffect(() => {
    if (perfil) {
      setForm({
        nombre: perfil.nombre ?? "",
        telefono: perfil.telefono ?? "",
        correo: perfil.correo ?? "",
        foto: perfil.foto ?? "",
      });
    }
  }, [perfil]);

  const elegirFoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    if (archivo.size > 2 * 1024 * 1024) {
      setError("La foto no puede superar 2 MB.");
      return;
    }
    const lector = new FileReader();
    lector.onload = () => setForm((f) => ({ ...f, foto: String(lector.result) }));
    lector.readAsDataURL(archivo);
  };

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setMsg("");
    setGuardando(true);
    try {
      const res = await api.put<{ ok: boolean; mensaje: string; usuario: Usuario }>("/perfil", form);
      setMsg(res.mensaje || "Datos actualizados correctamente.");
      // Refresca de inmediato el contexto de autenticación (barra superior, avatar y menú).
      if (res.usuario) actualizarUsuario(res.usuario);
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setGuardando(false);
    }
  };

  const cambiarPassword = async (e: FormEvent) => {
    e.preventDefault();
    setPassMsg("");
    if (pass.nueva !== pass.repetir) {
      setPassMsg("Las contraseñas nuevas no coinciden.");
      return;
    }
    try {
      const res = await api.put<{ ok: boolean; mensaje: string }>("/perfil/password", {
        actual: pass.actual, nueva: pass.nueva,
      });
      setPassMsg(res.mensaje);
      setPass({ actual: "", nueva: "", repetir: "" });
    } catch (err) {
      setPassMsg((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-lg font-bold text-gray-900 mb-1">Mis datos personales</h2>
        <p className="text-sm text-gray-500 mb-5">
          Mantén tu información de contacto al día para recibir las comunicaciones del conjunto.
        </p>

        <form onSubmit={guardar} className="grid lg:grid-cols-3 gap-6">
          <div className="flex flex-col items-center gap-3">
            <div className="w-28 h-28 rounded-full bg-gray-100 overflow-hidden flex items-center justify-center">
              {form.foto ? (
                <img src={form.foto} alt="Foto de perfil" className="w-full h-full object-cover" />
              ) : (
                <UserRound className="w-12 h-12 text-gray-300" />
              )}
            </div>
            <label className="cursor-pointer text-sm text-primary-600 hover:underline flex items-center gap-1">
              <Camera className="w-4 h-4" /> Cambiar foto
              <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={elegirFoto} />
            </label>
            <p className="text-xs text-gray-400 text-center">JPG/PNG hasta 2 MB</p>
            <div className="text-center">
              <p className="text-xs text-gray-400">Rol</p>
              <p className="text-sm font-semibold text-gray-700 capitalize">
                {perfil?.nombre_rol?.replace("_", " ")}
              </p>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-4">
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="label">Nombre</label>
                <input className="input" value={form.nombre}
                  onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
              </div>
              <div>
                <label className="label">Teléfono</label>
                <input className="input" value={form.telefono}
                  onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
              </div>
            </div>
            <div>
              <label className="label">Correo electrónico</label>
              <input type="email" className="input" value={form.correo}
                onChange={(e) => setForm({ ...form, correo: e.target.value })} />
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button variante="primary" type="submit" disabled={guardando}>
                <Save className="w-4 h-4" /> {guardando ? "Guardando…" : "Guardar cambios"}
              </Button>
              <div className="text-xs text-gray-400">
                Último acceso: {perfil?.ultimo_acceso ? fechaHora(perfil.ultimo_acceso) : "—"}
              </div>
            </div>
            {msg && <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">{msg}</div>}
            {error && <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
          </div>
        </form>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <KeyRound className="w-4 h-4" /> Cambiar contraseña
          </h3>
          <form onSubmit={cambiarPassword} className="space-y-3">
            <div>
              <label className="label">Contraseña actual</label>
              <input type="password" className="input" required value={pass.actual}
                onChange={(e) => setPass({ ...pass, actual: e.target.value })} />
            </div>
            <div>
              <label className="label">Nueva contraseña</label>
              <input type="password" className="input" required minLength={8} value={pass.nueva}
                onChange={(e) => setPass({ ...pass, nueva: e.target.value })} />
            </div>
            <div>
              <label className="label">Repetir nueva contraseña</label>
              <input type="password" className="input" required minLength={8} value={pass.repetir}
                onChange={(e) => setPass({ ...pass, repetir: e.target.value })} />
            </div>
            <Button variante="outline" type="submit">Actualizar contraseña</Button>
            {passMsg && <p className="text-sm text-gray-600">{passMsg}</p>}
          </form>
        </Card>

        <Card>
          <h3 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Mi actividad reciente
          </h3>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {(actividad ?? []).map((a) => (
              <div key={a.id} className="flex items-start justify-between gap-2 border-b border-gray-50 pb-2">
                <div className="min-w-0">
                  <p className="text-sm text-gray-700 truncate">{a.detalle || a.modulo}</p>
                  <p className="text-xs text-gray-400">{fechaHora(a.fecha_creacion)}</p>
                </div>
                <Badge color={a.accion === "eliminar" ? "danger" : a.accion === "crear" ? "success" : "info"}>
                  {capitalizar(a.accion)}
                </Badge>
              </div>
            ))}
            {!actividad?.length && <p className="text-sm text-gray-400">Sin actividad registrada.</p>}
          </div>
        </Card>
      </div>

      {usuario?.correo_verificado === false && (
        <p className="text-xs text-amber-600">Tu correo aún no está verificado; revisa tu bandeja de entrada.</p>
      )}
    </div>
  );
}
