import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Check, Search, Repeat2, LayoutGrid, MapPin, Users } from "lucide-react";
import { useConjunto } from "@/context/ConjuntoContext";
import { urlLogo } from "@/lib/logo";
import { colorDeConjunto } from "@/lib/coloresConjunto";
import type { Conjunto } from "@/types";

/**
 * Selector "Cambiar de conjunto".
 *
 * Despliega **todos** los conjuntos a cargo del usuario y permite cambiar el
 * contexto de trabajo desde ahí mismo, sin cerrar sesión (CA-07.2) y sin salir
 * de la pantalla actual (salvo que estemos en el panel, donde conviene entrar
 * al conjunto elegido).
 */
export default function SelectorConjunto({
  variante = "banner",
  className = "",
}: {
  variante?: "banner" | "topbar";
  className?: string;
}) {
  const { conjuntos, activo, seleccionar } = useConjunto();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [abierto, setAbierto] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const cajaRef = useRef<HTMLDivElement>(null);

  // Cerrar al hacer clic fuera o pulsar Escape.
  useEffect(() => {
    if (!abierto) return;
    const alClicar = (e: MouseEvent) => {
      if (cajaRef.current && !cajaRef.current.contains(e.target as Node)) setAbierto(false);
    };
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAbierto(false);
    };
    document.addEventListener("mousedown", alClicar);
    document.addEventListener("keydown", alTeclear);
    return () => {
      document.removeEventListener("mousedown", alClicar);
      document.removeEventListener("keydown", alTeclear);
    };
  }, [abierto]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return conjuntos;
    return conjuntos.filter(
      (c) =>
        c.nombre.toLowerCase().includes(q) ||
        (c.ciudad ?? "").toLowerCase().includes(q) ||
        (c.direccion ?? "").toLowerCase().includes(q),
    );
  }, [conjuntos, busqueda]);

  const elegir = (c: Conjunto) => {
    seleccionar(c.id);
    setAbierto(false);
    setBusqueda("");
    // Desde el panel de conjuntos entramos directo al conjunto elegido.
    if (pathname === "/dashboard") navigate("/dashboard/inicio");
  };

  const enPanel = pathname === "/dashboard";

  const boton =
    variante === "banner" ? (
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className={`inline-flex items-center gap-2 rounded-full bg-white border border-primary-100 px-4 py-2 text-sm font-semibold text-primary-600 shadow-sm hover:bg-primary-50 transition ${className}`}
        aria-haspopup="listbox"
        aria-expanded={abierto}
        title="Seleccionar otro conjunto"
      >
        <Repeat2 className="w-4 h-4" />
        Cambiar conjunto
        <ChevronDown className={`w-4 h-4 transition-transform ${abierto ? "rotate-180" : ""}`} />
      </button>
    ) : (
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className={`hidden md:inline-flex items-center gap-2 max-w-[240px] rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition ${className}`}
        aria-haspopup="listbox"
        aria-expanded={abierto}
        title="Cambiar de conjunto"
      >
        <LayoutGrid className="w-3.5 h-3.5 text-primary-500 shrink-0" />
        <span className="truncate">{activo ? activo.nombre : "Sin conjunto"}</span>
        <ChevronDown className={`w-3.5 h-3.5 shrink-0 transition-transform ${abierto ? "rotate-180" : ""}`} />
      </button>
    );

  return (
    <div className="relative" ref={cajaRef}>
      {boton}

      <AnimatePresence>
        {abierto && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 sm:left-0 sm:right-auto z-50 mt-2 w-[min(92vw,380px)] overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-2xl"
            role="listbox"
          >
            <div className="border-b border-gray-100 px-4 py-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                Seleccionar otro conjunto
              </p>
              {conjuntos.length > 5 && (
                <div className="mt-2 flex items-center gap-2 rounded-full bg-gray-50 px-3 py-1.5">
                  <Search className="w-3.5 h-3.5 text-gray-400" />
                  <input
                    autoFocus
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    placeholder="Buscar conjunto..."
                    className="w-full bg-transparent text-sm outline-none"
                  />
                </div>
              )}
            </div>

            <div className="max-h-[320px] overflow-y-auto p-2">
              {filtrados.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-gray-400">
                  Sin conjuntos que coincidan con la búsqueda.
                </p>
              )}

              {filtrados.map((c) => {
                const esActivo = activo?.id === c.id;
                const color = colorDeConjunto(conjuntos, c.id);
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => elegir(c)}
                    role="option"
                    aria-selected={esActivo}
                    className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition ${
                      esActivo ? "bg-primary-50" : "hover:bg-gray-50"
                    }`}
                  >
                    <span
                      className={`relative grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-xl text-sm font-bold ${
                        esActivo ? "bg-primary-500 text-white" : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {c.nombre.charAt(0).toUpperCase()}
                      {urlLogo(c.logo) && (
                        <img
                          src={urlLogo(c.logo) as string}
                          alt=""
                          className="absolute inset-0 h-full w-full bg-white object-cover"
                          onError={(e) => { e.currentTarget.style.display = "none"; }}
                        />
                      )}
                      {/* Punto con el color propio del conjunto. */}
                      <span
                        className="absolute bottom-0 right-0 h-2.5 w-2.5 translate-x-[2px] translate-y-[2px] rounded-full border-2 border-white"
                        style={{ background: color.hex }}
                        title={color.nombre}
                      />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span
                        className={`block truncate text-sm font-semibold ${
                          esActivo ? "text-primary-700" : "text-gray-800"
                        }`}
                      >
                        {c.nombre}
                      </span>
                      <span className="flex items-center gap-1 text-[11px] text-gray-400">
                        <MapPin className="w-3 h-3" />
                        <span className="truncate">
                          {[c.direccion, c.ciudad].filter(Boolean).join(", ") || "Sin dirección"}
                        </span>
                        <span className="mx-1">·</span>
                        <Users className="w-3 h-3" />
                        {c.habitantes.toLocaleString("es-CO")}
                      </span>
                    </span>
                    {esActivo && <Check className="w-4 h-4 shrink-0 text-primary-600" />}
                  </button>
                );
              })}
            </div>

            <div className="border-t border-gray-100 p-2">
              <button
                type="button"
                onClick={() => {
                  setAbierto(false);
                  navigate("/dashboard");
                }}
                disabled={enPanel}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-semibold text-gray-600 transition hover:bg-gray-50 disabled:opacity-40"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gray-100">
                  <LayoutGrid className="w-4 h-4 text-gray-500" />
                </span>
                Ver todos los conjuntos
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
