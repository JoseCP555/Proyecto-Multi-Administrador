import { useEffect, useState } from "react";
import { Download, Share, PlusSquare, X, Smartphone } from "lucide-react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

const DISMISS_KEY = "ma_pwa_install_dismissed_at";
const COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000; // 7 días

function estaInstalada(): boolean {
  if (typeof window === "undefined") return false;
  const nav = window.navigator as Navigator & { standalone?: boolean };
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    nav.standalone === true
  );
}

function esIOS(): boolean {
  if (typeof window === "undefined") return false;
  const ua = window.navigator.userAgent;
  const esDispositivoApple = /iPad|iPhone|iPod/.test(ua);
  const esIPadModerno =
    window.navigator.platform === "MacIntel" && window.navigator.maxTouchPoints > 1;
  return esDispositivoApple || esIPadModerno;
}

function fueDescartadoRecientemente(): boolean {
  try {
    const raw = localStorage.getItem(DISMISS_KEY);
    if (!raw) return false;
    return Date.now() - Number(raw) < COOLDOWN_MS;
  } catch {
    return false;
  }
}

/**
 * Aviso ligero para instalar Multi-Administrador como app (PWA):
 *  - Android (Chrome / Edge / Samsung Internet): botón nativo de 1 toque.
 *  - iPhone / iPad (Safari): instrucciones breves de "Compartir -> Agregar a inicio".
 * Se oculta automáticamente cuando ya está instalada o si el usuario la descarta.
 */
export default function InstalarAppBanner() {
  const [eventoAndroid, setEventoAndroid] = useState<BeforeInstallPromptEvent | null>(null);
  const [mostrarIOS, setMostrarIOS] = useState(false);
  const [guiaIOS, setGuiaIOS] = useState(false);
  const [oculto, setOculto] = useState(true);

  useEffect(() => {
    if (estaInstalada() || fueDescartadoRecientemente()) return;

    if (esIOS()) {
      setMostrarIOS(true);
      setOculto(false);
    }

    const onBeforeInstall = (e: Event) => {
      e.preventDefault();
      setEventoAndroid(e as BeforeInstallPromptEvent);
      setMostrarIOS(false);
      setOculto(false);
    };

    const onInstalled = () => {
      setOculto(true);
      setEventoAndroid(null);
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstall);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (oculto || (!eventoAndroid && !mostrarIOS)) return null;

  const cerrar = () => {
    setOculto(true);
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      /* ignorar si localStorage está bloqueado */
    }
  };

  const instalarAndroid = async () => {
    if (!eventoAndroid) return;
    await eventoAndroid.prompt();
    const res = await eventoAndroid.userChoice;
    if (res.outcome === "accepted") {
      setOculto(true);
      setEventoAndroid(null);
    }
  };

  return (
    <div className="mb-4 rounded-2xl border border-primary-100 bg-primary-50/80 px-3.5 py-3 text-gray-800 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-white border border-primary-100 flex items-center justify-center shrink-0 overflow-hidden shadow-xs">
            <img src="/assets/icon-192.png" alt="Multi-Admin" className="w-8 h-8 object-contain" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
              <Smartphone className="w-3.5 h-3.5 text-primary-600 shrink-0" />
              <span className="truncate">Instala Multi-Admin en tu celular</span>
            </p>
            <p className="text-xs text-gray-600">
              {eventoAndroid
                ? "Ábrela desde tu pantalla de inicio como una app nativa."
                : "Agrégala a tu pantalla de inicio en iPhone para acceso rápido y pantalla completa."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {eventoAndroid ? (
            <button
              type="button"
              onClick={instalarAndroid}
              className="btn btn-primary px-3.5 py-2 text-xs"
            >
              <Download className="w-3.5 h-3.5" /> Instalar
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setGuiaIOS((v) => !v)}
              className="btn btn-primary px-3 py-2 text-xs"
            >
              {guiaIOS ? "Ocultar" : "Cómo"}
            </button>
          )}
          <button
            type="button"
            onClick={cerrar}
            className="p-1.5 rounded-full text-gray-400 hover:text-gray-600 hover:bg-white/70"
            aria-label="Cerrar aviso"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {mostrarIOS && guiaIOS && (
        <ol className="mt-3 pt-3 border-t border-primary-100 space-y-2 text-xs text-gray-700">
          <li className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-500 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
              1
            </span>
            <span>
              En Safari, toca el botón <strong>Compartir</strong>{" "}
              <Share className="inline w-3.5 h-3.5 text-primary-600 -mt-0.5" /> en la barra inferior.
            </span>
          </li>
          <li className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-500 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
              2
            </span>
            <span>
              Desliza hacia abajo y elige{" "}
              <strong>
                Agregar a inicio <PlusSquare className="inline w-3.5 h-3.5 text-primary-600 -mt-0.5" />
              </strong>{" "}
              y luego toca <strong>Agregar</strong>.
            </span>
          </li>
        </ol>
      )}
    </div>
  );
}
