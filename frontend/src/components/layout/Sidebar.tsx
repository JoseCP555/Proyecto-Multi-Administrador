import { NavLink, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import {
  LayoutDashboard,
  Home,
  Users,
  UserRound,
  Building2,
  Wallet,
  Wrench,
  FileText,
  CalendarDays,
  LogOut,
  MessagesSquare,
  MessageCircleMore,
  Settings,
  MessageSquareWarning,
  CalendarClock,
  Megaphone,
  DoorOpen,
  CreditCard,
  Vote,
  ClipboardCheck,
  ShieldCheck,
  UserCog,
  Scale,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { puedeVerModulo, tienePermiso } from "@/lib/permisos";
import logoUrl from "@/lib/logo";
import { useConjunto } from "@/context/ConjuntoContext";
import { useMensajesNoLeidos } from "@/hooks/useMensajesNoLeidos";

// Ítems del menú (estilo exacto del dashboard). Cada uno declara el permiso
// (módulo) necesario para VERLO; se filtran según el rol del usuario (RBAC).
interface ItemMenu {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  modulo?: string;
  badge?: number;
}
const items: ItemMenu[] = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard, end: true, modulo: "dashboard" as const },
  { label: "Inicio", path: "/dashboard/inicio", icon: Home, end: true, modulo: "dashboard" as const },
  { label: "Usuarios", path: "/dashboard/usuarios", icon: Users, modulo: "usuarios" as const },
  { label: "Residentes", path: "/dashboard/residentes", icon: UserRound, modulo: "residentes" as const },
  { label: "Propiedades", path: "/dashboard/propiedades", icon: Building2, modulo: "propiedades" as const },
  { label: "Finanzas", path: "/dashboard/finanzas", icon: Wallet, modulo: "finanzas" as const },
  { label: "Mantenimiento", path: "/dashboard/mantenimiento", icon: Wrench, modulo: "mantenimiento" as const },
  { label: "Documentos", path: "/dashboard/documentos", icon: FileText, modulo: "documentos" as const },
  { label: "Eventos", path: "/dashboard/eventos", icon: CalendarDays, modulo: "eventos" as const },
  // Historias de usuario UH-09 a UH-32 (se filtran por permisos del rol).
  { label: "PQRS", path: "/dashboard/pqrs", icon: MessageSquareWarning, modulo: "pqrs" as const },
  { label: "Reservas", path: "/dashboard/reservas", icon: CalendarClock, modulo: "reservas" as const },
  { label: "Comunicados", path: "/dashboard/comunicados", icon: Megaphone, modulo: "comunicados" as const },
  { label: "Pagos", path: "/dashboard/pagos", icon: CreditCard, modulo: "pagos" as const },
  { label: "Visitantes", path: "/dashboard/visitantes", icon: DoorOpen, modulo: "visitantes" as const },
  { label: "Votaciones", path: "/dashboard/votaciones", icon: Vote, modulo: "votaciones" as const },
  { label: "Aprobaciones", path: "/dashboard/aprobaciones", icon: ClipboardCheck, modulo: "aprobaciones" as const },
];

export default function Sidebar({ onNavigate }: { onNavigate?: () => void } = {}) {
  const { usuario, logout } = useAuth();
  const { conjuntos } = useConjunto();
  const { noLeidos: mensajesNoLeidos } = useMensajesNoLeidos();
  const navigate = useNavigate();

  // Solo se muestran los módulos para los que el rol tiene el permiso <modulo>.ver.
  const itemsVisibles: ItemMenu[] = items.filter(
    (i) =>
      i.modulo &&
      puedeVerModulo(usuario, i.modulo) &&
      // El panel "Dashboard" (selector de conjuntos) sólo aporta cuando el
      // usuario administra más de un conjunto; con uno solo se entra directo
      // al "Inicio" de ese conjunto.
      (i.path !== "/dashboard" || conjuntos.length > 1),
  );

  // Chat directo entre residentes y administración.
  if (puedeVerModulo(usuario, "mensajes")) {
    const esGestor = tienePermiso(usuario, "mensajes.gestionar");
    itemsVisibles.push({
      label: esGestor ? "Chat residentes" : "Chat con Admin",
      path: "/dashboard/mensajes",
      icon: MessageCircleMore,
      badge: mensajesNoLeidos,
    });
  }
  // El historial de chat solo es visible si el rol tiene el permiso chat.usar.
  if (tienePermiso(usuario, "chat.usar")) {
    itemsVisibles.push({ label: "Chat asistente", path: "/dashboard/chat", icon: MessagesSquare });
  }
  // Panel del consejo (actas + reportes) para quien puede ver reportes.
  if (tienePermiso(usuario, "reportes.ver")) {
    itemsVisibles.push({ label: "Consejo", path: "/dashboard/consejo", icon: Scale });
  }
  // Auditoría solo para quien tiene auditoria.ver (UH-29).
  if (tienePermiso(usuario, "auditoria.ver")) {
    itemsVisibles.push({ label: "Auditoría", path: "/dashboard/auditoria", icon: ShieldCheck });
  }
  // Configuración solo es visible si el rol puede verla (config.ver).
  if (tienePermiso(usuario, "config.ver")) {
    itemsVisibles.push({ label: "Configuración", path: "/dashboard/configuracion", icon: Settings });
  }
  // Mi perfil (UH-20).
  if (tienePermiso(usuario, "perfil.ver")) {
    itemsVisibles.push({ label: "Mi perfil", path: "/dashboard/perfil", icon: UserCog });
  }

  // Cierra sesión en el backend (revoca el token en Redis) y limpia el cliente.
  const cerrar = async () => {
    try {
      await api.post("/logout");
    } catch {
      // Siguemos igual aunque el backend no esté disponible.
    }
    logout();
    navigate("/login");
  };

  return (
    <aside className="w-[260px] max-w-[85vw] bg-dark-100 text-white flex flex-col h-[100dvh] lg:min-h-full lg:sticky lg:top-0 lg:h-screen lg:max-h-screen pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
      {/* Logo */}
      <div className="px-6 pt-7 pb-5 flex items-center gap-3">
        <div className="w-11 h-11 rounded-2xl bg-white flex items-center justify-center overflow-hidden shrink-0">
          <img src={logoUrl} alt="Multi-Admin" className="w-9 h-9 object-contain" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-extrabold tracking-tight leading-tight">Multi-Admin</h1>
          <p className="text-[11px] text-gray-400 truncate">Gestión de copropiedades</p>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 px-4 py-2 space-y-1.5 overflow-y-auto">
        {itemsVisibles.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-3 rounded-full transition-all duration-200 text-sm font-medium ${
                isActive
                  ? "bg-primary-500 text-white shadow-pill"
                  : "text-gray-400 hover:bg-white/10 hover:text-white"
              }`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            <span className="flex-1 truncate">{item.label}</span>
            {!!item.badge && item.badge > 0 && (
              <span className="min-w-[20px] h-5 px-1.5 rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                {item.badge > 99 ? "99+" : item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Usuario + logout */}
      <div className="p-4 pb-6 space-y-3">
        <div className="flex items-center gap-3 px-3">
          <div className="w-9 h-9 rounded-full bg-primary-500 flex items-center justify-center text-sm font-bold shrink-0">
            {usuario?.nombre?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{usuario?.nombre}</p>
            <p className="text-[11px] text-gray-400 truncate capitalize">{usuario?.nombre_rol?.replace("_", " ")}</p>
          </div>
        </div>
        <button
          onClick={cerrar}
          className="flex items-center justify-center gap-2 px-5 py-3 w-full rounded-full bg-primary-500 hover:bg-primary-600 text-white text-sm font-bold tracking-wide shadow-pill transition-all duration-200"
        >
          <LogOut className="w-5 h-5" />
          <span>CERRAR SESIÓN</span>
        </button>
      </div>
    </aside>
  );
}
