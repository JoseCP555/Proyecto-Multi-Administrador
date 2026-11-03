import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell, X, CalendarDays, Wallet, Wrench, AlarmClock, Check, Trash2,
  Mail, Send, Info, Users, FileText, Building2, Home, Settings2, LucideIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import { useConjunto } from "@/context/ConjuntoContext";
import {
  activarPush, desactivarPush, estadoPush, mostrarAvisoLocal, registrarServiceWorker,
  soportaPush, type ConfigNotificaciones,
} from "@/lib/push";
import type { Notificacion, PreferenciasNotificacion } from "@/types";

// Icono y color por tipo de notificación.
const ICONOS: Record<string, { icon: LucideIcon; color: string; badge: string }> = {
  mora: { icon: Wallet, color: "text-red-600", badge: "bg-red-100 text-red-700" },
  proximo: { icon: AlarmClock, color: "text-amber-600", badge: "bg-amber-100 text-amber-700" },
  pago: { icon: Wallet, color: "text-emerald-600", badge: "bg-emerald-100 text-emerald-700" },
  evento: { icon: CalendarDays, color: "text-primary-600", badge: "bg-blue-100 text-blue-700" },
  mantenimiento: { icon: Wrench, color: "text-orange-600", badge: "bg-orange-100 text-orange-700" },
  documento: { icon: FileText, color: "text-indigo-600", badge: "bg-indigo-100 text-indigo-700" },
  residente: { icon: Users, color: "text-cyan-600", badge: "bg-cyan-100 text-cyan-700" },
  propiedad: { icon: Home, color: "text-teal-600", badge: "bg-teal-100 text-teal-700" },
  usuario: { icon: Settings2, color: "text-violet-600", badge: "bg-violet-100 text-violet-700" },
  conjunto: { icon: Building2, color: "text-fuchsia-600", badge: "bg-fuchsia-100 text-fuchsia-700" },
  prueba: { icon: Info, color: "text-sky-600", badge: "bg-sky-100 text-sky-700" },
  sistema: { icon: Info, color: "text-gray-600", badge: "bg-gray-100 text-gray-700" },
};
const META_DEFECTO = { icon: Bell, color: "text-gray-600", badge: "bg-gray-100 text-gray-700" };

const VISTOS_KEY = "ma_notificaciones_vistas";

function leerVistos(): Set<number> {
  try {
    const raw = localStorage.getItem(VISTOS_KEY);
    return new Set<number>(raw ? (JSON.parse(raw) as number[]) : []);
  } catch {
    return new Set<number>();
  }
}

function hace(iso?: string | null): string {
  if (!iso) return "";
  const ms = new Date(iso).getTime();
  if (Number.isNaN(ms)) return "";
  const s = Math.max(0, Math.floor((Date.now() - ms) / 1000));
  if (s < 60) return "ahora mismo";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  if (s < 172800) return "ayer";
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
}

export default function Notificaciones() {
  const navigate = useNavigate();
  const { activo, seleccionar } = useConjunto();
  const [abierto, setAbierto] = useState(false);
  const [items, setItems] = useState<Notificacion[]>([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const [cargando, setCargando] = useState(false);
  const [prefs, setPrefs] = useState<PreferenciasNotificacion | null>(null);
  const [config, setConfig] = useState<ConfigNotificaciones | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [probando, setProbando] = useState(false);
  const [pushActivo, setPushActivo] = useState(false);

  const ref = useRef<HTMLDivElement>(null);
  const vistos = useRef<Set<number>>(leerVistos());
  const primeraCarga = useRef(true);
  const pushRef = useRef(false);
  const autoPush = useRef(false);

  const guardarVistos = () => {
    try {
      // Solo los últimos 300 para que localStorage no crezca sin límite.
      localStorage.setItem(VISTOS_KEY, JSON.stringify([...vistos.current].slice(-300)));
    } catch { /* almacenamiento lleno: no es crítico */ }
  };

  const cargar = useCallback(async (avisarNuevos = false) => {
    try {
      const [lista, preferencias, cfg] = await Promise.all([
        api.get<Notificacion[]>("/notificaciones"),
        api.get<PreferenciasNotificacion>("/notificaciones/preferencias"),
        api.get<ConfigNotificaciones>("/notificaciones/config"),
      ]);
      const seguros = Array.isArray(lista) ? lista : [];
      setItems(seguros);
      setNoLeidas(seguros.filter((n) => !n.leida).length);
      setPrefs(preferencias);
      setConfig(cfg);

      if (avisarNuevos) {
        if (primeraCarga.current) {
          // La primera vez solo se "aprende" el estado, no se dispara nada.
          seguros.forEach((n) => vistos.current.add(n.id));
          guardarVistos();
          primeraCarga.current = false;
        } else {
          const nuevos = seguros.filter((n) => !n.leida && !vistos.current.has(n.id));
          if (nuevos.length) {
            // Si ya hay Web Push activo, el service worker se encarga; si no,
            // mostramos un aviso local mientras la pestaña esté abierta.
            if (!pushRef.current && soportaPush()) {
              const n = nuevos[0];
              mostrarAvisoLocal(n.titulo, n.mensaje, n.url || "/dashboard/inicio");
            }
            nuevos.forEach((n) => vistos.current.add(n.id));
            guardarVistos();
          }
        }
      }
    } catch {
      // Sin conexión: se conserva lo ya mostrado.
    } finally {
      setCargando(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Carga inicial + sondeo cada 30 s + al volver a la pestaña.
  useEffect(() => {
    setCargando(true);
    cargar(true);
    const id = window.setInterval(() => cargar(true), 30_000);
    const alVolver = () => cargar(true);
    window.addEventListener("focus", alVolver);
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("focus", alVolver);
      document.removeEventListener("visibilitychange", alVolver);
    };
  }, [cargar]);

  // Registra el service worker y consulta el estado real de la suscripción.
  useEffect(() => {
    registrarServiceWorker().finally(() => {
      estadoPush().then((e) => {
        setPushActivo(e.suscrito);
        pushRef.current = e.suscrito;
      });
    });
  }, []);

  // Si el usuario ya dio permiso en otra sesión, se re-suscribe solo.
  useEffect(() => {
    if (autoPush.current || !prefs?.push || !config?.vapid_publico) return;
    if (!soportaPush() || Notification.permission !== "granted" || pushActivo) return;
    autoPush.current = true;
    activarPush(config.vapid_publico).then(async () => {
      const e = await estadoPush();
      setPushActivo(e.suscrito);
      pushRef.current = e.suscrito;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefs?.push, config?.vapid_publico]);

  // Cerrar al hacer clic fuera.
  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const abrirNotificacion = async (n: Notificacion) => {
    if (!n.leida) {
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, leida: true } : x)));
      setNoLeidas((v) => Math.max(0, v - 1));
      try { await api.post(`/notificaciones/${n.id}/leer`); } catch { /* no crítico */ }
    }
    if (n.id_conjunto && n.id_conjunto !== activo?.id) seleccionar(n.id_conjunto);
    if (n.url) navigate(n.url);
    setAbierto(false);
  };

  const descartar = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    const era = items.find((n) => n.id === id);
    setItems((prev) => prev.filter((x) => x.id !== id));
    if (era && !era.leida) setNoLeidas((v) => Math.max(0, v - 1));
    try { await api.del(`/notificaciones/${id}`); } catch { /* no crítico */ }
  };

  const leerTodas = async () => {
    setItems((prev) => prev.map((n) => ({ ...n, leida: true })));
    setNoLeidas(0);
    try { await api.post("/notificaciones/leer-todas"); } catch { /* no crítico */ }
  };

  const alternarCorreo = async () => {
    const nuevo = !prefs?.correo;
    setPrefs((p) => (p ? { ...p, correo: nuevo } : p));
    try {
      await api.put("/notificaciones/preferencias", { correo: nuevo });
      setAviso(nuevo ? "Avisos por correo activados." : "Avisos por correo desactivados.");
    } catch { /* no crítico */ }
  };

  const alternarPush = async () => {
    const nuevo = !prefs?.push;
    if (nuevo) {
      const r = await activarPush(config?.vapid_publico ?? "");
      setAviso(r.mensaje);
      if (!r.ok) return;
    } else {
      await desactivarPush();
      setAviso("Avisos del navegador desactivados.");
    }
    setPrefs((p) => (p ? { ...p, push: nuevo } : p));
    try { await api.put("/notificaciones/preferencias", { push: nuevo }); } catch { /* no crítico */ }
    const e = await estadoPush();
    setPushActivo(e.suscrito);
    pushRef.current = e.suscrito;
  };

  const enviarPrueba = async () => {
    setProbando(true);
    setAviso(null);
    try {
      const r = await api.post<{
        ok: boolean;
        correo: { enviado: boolean; omitido?: boolean; error?: string };
        push: number;
        suscripciones: number;
      }>("/notificaciones/probar", { canal: "todos" });
      const correo = r.correo?.enviado
        ? (r.correo.omitido ? "correo omitido (dominio de prueba)" : "correo enviado ✅")
        : `correo no enviado (${r.correo?.error ?? "sin configurar"})`;
      const push = r.suscripciones
        ? `${r.push}/${r.suscripciones} push entregados`
        : "sin suscripciones push activas";
      setAviso(`Aviso creado e incluido en la lista · ${correo} · ${push}`);
      await cargar(false);
    } catch (e) {
      setAviso(`No se pudo enviar la prueba: ${(e as Error).message}`);
    } finally {
      setProbando(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => {
          setAbierto((v) => !v);
          if (!abierto) cargar(false);
        }}
        className="p-2 relative rounded-full text-primary-500 hover:bg-primary-50"
        aria-label="Notificaciones"
      >
        <Bell className="w-5 h-5" />
        {noLeidas > 0 && (
          <span className="absolute top-1 right-1 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[10px] font-bold">
            {noLeidas > 99 ? "99+" : noLeidas}
          </span>
        )}
      </button>

      {abierto && (
        <div className="absolute right-0 mt-2 w-[360px] max-w-[calc(100vw-24px)] max-h-[560px] flex flex-col bg-white rounded-3xl shadow-2xl border border-gray-100 z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
            <div>
              <p className="text-sm font-semibold text-gray-800">Notificaciones</p>
              <p className="text-xs text-gray-400">
                {noLeidas > 0 ? `${noLeidas} sin leer · ` : ""}{items.length} en total
              </p>
            </div>
            <div className="flex items-center gap-1">
              {noLeidas > 0 && (
                <button
                  onClick={leerTodas}
                  className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold text-primary-600 hover:bg-primary-50"
                  title="Marcar todas como leídas"
                >
                  <Check className="w-3.5 h-3.5" /> Marcar leídas
                </button>
              )}
              <button onClick={() => setAbierto(false)} className="p-1 rounded-lg hover:bg-gray-100 text-gray-400" aria-label="Cerrar">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-gray-50 min-h-[120px]">
            {cargando && !items.length && (
              <p className="text-sm text-gray-400 text-center py-8">Cargando...</p>
            )}
            {!cargando && !items.length && (
              <div className="text-center py-10 px-6">
                <Bell className="w-8 h-8 mx-auto text-gray-200" />
                <p className="mt-2 text-sm font-medium text-gray-500">Todo al día</p>
                <p className="text-xs text-gray-400">No tienes notificaciones pendientes.</p>
              </div>
            )}
            {items.map((n) => {
              const meta = ICONOS[n.tipo] ?? META_DEFECTO;
              const Icono = meta.icon;
              return (
                <button
                  key={n.id}
                  onClick={() => abrirNotificacion(n)}
                  className={`group relative flex w-full gap-3 px-4 py-3 text-left transition hover:bg-gray-50 ${
                    n.leida ? "opacity-70" : "bg-white"
                  }`}
                >
                  {!n.leida && (
                    <span className="absolute left-0 top-0 bottom-0 w-[3px] bg-primary-500" />
                  )}
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${meta.badge}`}>
                    <Icono className={`w-4 h-4 ${meta.color}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-[13px] font-semibold text-gray-800 ${n.leida ? "" : "font-bold"}`}>
                        {n.titulo}
                      </p>
                      <span
                        role="button"
                        tabIndex={0}
                        aria-label="Descartar notificación"
                        onClick={(e) => descartar(e, n.id)}
                        onKeyDown={(e) => { if (e.key === "Enter") descartar(e as unknown as React.MouseEvent, n.id); }}
                        className="opacity-0 group-hover:opacity-100 shrink-0 p-0.5 rounded text-gray-300 hover:text-red-500 hover:bg-red-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 leading-snug mt-0.5">{n.mensaje}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-gray-400">
                      <span>{hace(n.fecha_creacion)}</span>
                      {n.nombre_conjunto && (
                        <span className="rounded-full bg-gray-100 px-1.5 py-0.5 truncate max-w-[160px]">
                          {n.nombre_conjunto}
                        </span>
                      )}
                      {n.url && <span className="text-primary-500">Ver módulo →</span>}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Preferencias de entrega */}
          <div className="shrink-0 border-t border-gray-100 px-4 py-3 bg-gray-50/70 rounded-b-3xl">
            <p className="text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2">
              Cómo quieres recibirlos
            </p>
            <div className="flex flex-col gap-1.5">
              <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  className="accent-primary-600"
                  checked={!!prefs?.correo}
                  onChange={alternarCorreo}
                />
                <Mail className="w-3.5 h-3.5 text-gray-400" />
                Avisos por correo
                {!config?.correo_configurado && (
                  <span className="ml-auto text-[10px] text-amber-600">SMTP sin configurar</span>
                )}
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  className="accent-primary-600"
                  checked={!!prefs?.push}
                  onChange={alternarPush}
                />
                <Bell className="w-3.5 h-3.5 text-gray-400" />
                Notificaciones del navegador
                {pushActivo && <span className="ml-auto text-[10px] text-emerald-600">activo</span>}
                {!config?.push_configurado && (
                  <span className="ml-auto text-[10px] text-amber-600">sin claves VAPID</span>
                )}
              </label>
            </div>
            <button
              onClick={enviarPrueba}
              disabled={probando}
              className="mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-[11px] font-semibold text-gray-600 hover:bg-gray-50 disabled:opacity-60"
            >
              <Send className="w-3.5 h-3.5" />
              {probando ? "Enviando..." : "Enviar aviso de prueba"}
            </button>
            {aviso && (
              <p className="mt-2 rounded-lg bg-white px-2.5 py-2 text-[11px] leading-snug text-gray-600 border border-gray-100">
                {aviso}
              </p>
            )}
            <p className="mt-2 text-[10px] leading-snug text-gray-400">
              Se actualizan solas cada 30 s. Los avisos nacen de pagos, eventos,
              mantenimientos, documentos y residentes reales.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
