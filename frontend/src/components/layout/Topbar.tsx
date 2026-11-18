import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Menu, Search, X, ChevronDown, Home, MessagesSquare, MessageCircleMore, MoreHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { tienePermiso } from "@/lib/permisos";
import Notificaciones from "@/components/layout/Notificaciones";
import SelectorConjunto from "@/components/layout/SelectorConjunto";
import { useConjunto } from "@/context/ConjuntoContext";
import { useMensajesNoLeidos } from "@/hooks/useMensajesNoLeidos";

const TITULOS: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/inicio": "Inicio",
  "/dashboard/usuarios": "Usuarios",
  "/dashboard/residentes": "Residentes",
  "/dashboard/propiedades": "Propiedades",
  "/dashboard/finanzas": "Finanzas",
  "/dashboard/mantenimiento": "Mantenimiento",
  "/dashboard/documentos": "Documentos",
  "/dashboard/eventos": "Eventos",
  "/dashboard/chat": "Chat asistente",
  "/dashboard/mensajes": "Chat con Administración",
  "/dashboard/configuracion": "Configuración",
  "/dashboard/pqrs": "PQRS",
  "/dashboard/reservas": "Reservas",
  "/dashboard/comunicados": "Comunicados",
  "/dashboard/pagos": "Pagos",
  "/dashboard/visitantes": "Visitantes",
  "/dashboard/votaciones": "Votaciones",
  "/dashboard/aprobaciones": "Aprobaciones",
  "/dashboard/consejo": "Consejo",
  "/dashboard/auditoria": "Auditoría",
  "/dashboard/perfil": "Mi perfil",
};

export default function Topbar({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  const { usuario } = useAuth();
  const { pathname } = useLocation();
  const { activo: conjunto, conjuntos } = useConjunto();
  const { noLeidos: mensajesNoLeidos } = useMensajesNoLeidos();
  const [buscar, setBuscar] = useState("");
  const esGestorMensajes = tienePermiso(usuario, "mensajes.gestionar");
  const titulo =
    pathname === "/dashboard/mensajes"
      ? esGestorMensajes
        ? "Chat con residentes"
        : "Chat con Administración"
      : (TITULOS[pathname] ?? "Panel");
  const subtitulo =
    pathname === "/dashboard"
      ? "Panel Multi-Administrador"
      : conjunto
        ? `Gestionando ${conjunto.nombre}`
        : undefined;

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md px-4 sm:px-6 lg:px-8 pt-[max(1.25rem,env(safe-area-inset-top))] pb-4 flex items-center justify-between gap-4">
      {/* Menú móvil + título */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-full text-gray-600 hover:bg-gray-100"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="min-w-0">
          <h2 className="text-xl font-bold text-gray-900 truncate">{titulo}</h2>
          <p className="text-xs text-gray-400 hidden sm:block">
            {subtitulo ?? `Bienvenido de nuevo, ${usuario?.nombre?.split(" ")[0] ?? ""}`}
          </p>
        </div>
      </div>

      {/* Búsqueda (píldora azul) */}
      <div className="flex-1 max-w-md relative hidden sm:block">
        <Search className="w-4 h-4 text-white/80 absolute left-4 top-1/2 -translate-y-1/2" />
        <input
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
          placeholder="Buscar"
          className="w-full bg-primary-500 text-white placeholder:text-white/70 rounded-full pl-11 pr-10 py-2.5 text-sm outline-none focus:ring-4 focus:ring-primary-500/25 shadow-pill transition"
        />
        {buscar && (
          <button onClick={() => setBuscar("")} className="absolute right-4 top-1/2 -translate-y-1/2 text-white/80 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Acciones + perfil */}
      <div className="flex items-center gap-1 sm:gap-2">
        <button className="hidden md:inline-flex p-2 rounded-full text-primary-500 hover:bg-primary-50" aria-label="Más">
          <MoreHorizontal className="w-5 h-5" />
        </button>
        {tienePermiso(usuario, "mensajes.ver") && (
          <Link
            to="/dashboard/mensajes"
            className="relative inline-flex p-2 rounded-full text-primary-500 hover:bg-primary-50"
            aria-label={esGestorMensajes ? "Chat con residentes" : "Chat con Administración"}
            title={esGestorMensajes ? "Chat con residentes" : "Chat con Administración"}
          >
            <MessageCircleMore className="w-5 h-5" />
            {mensajesNoLeidos > 0 && (
              <span className="absolute top-1 right-1 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[10px] font-bold">
                {mensajesNoLeidos > 99 ? "99+" : mensajesNoLeidos}
              </span>
            )}
          </Link>
        )}
        {tienePermiso(usuario, "chat.usar") && (
          <Link to="/dashboard/chat" className="hidden md:inline-flex p-2 rounded-full text-primary-500 hover:bg-primary-50" aria-label="Asistente" title="Chat asistente">
            <MessagesSquare className="w-5 h-5" />
          </Link>
        )}
        <Link to="/dashboard" className="hidden md:inline-flex p-2 rounded-full text-primary-500 hover:bg-primary-50" aria-label="Inicio">
          <Home className="w-5 h-5" />
        </Link>
        <Notificaciones />
        {conjuntos.length > 0 && (
          <>
            <span className="hidden md:block w-px h-7 bg-gray-200 mx-1" />
            <SelectorConjunto variante="topbar" />
          </>
        )}
        <span className="hidden md:block w-px h-7 bg-gray-200 mx-1" />
        <Link to="/dashboard/perfil" className="flex items-center gap-2 pl-1 group" title="Mi perfil">
          <div className="hidden md:block text-right">
            <p className="text-sm font-bold text-gray-900 uppercase tracking-wide leading-tight group-hover:text-primary-600 transition">
              {usuario?.nombre}
            </p>
            <p className="text-[11px] text-gray-400 capitalize">{usuario?.nombre_rol?.replace("_", " ")}</p>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400 hidden md:block" />
          <div className="w-10 h-10 rounded-full bg-primary-500 text-white flex items-center justify-center text-sm font-bold ring-4 ring-primary-100 overflow-hidden shrink-0">
            {usuario?.foto ? (
              <img src={usuario.foto} alt={usuario.nombre} className="w-full h-full object-cover" />
            ) : (
              usuario?.nombre?.charAt(0)?.toUpperCase() || "U"
            )}
          </div>
        </Link>
      </div>
    </header>
  );
}
