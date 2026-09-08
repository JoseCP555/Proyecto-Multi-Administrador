import { NavLink, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import {
  LayoutDashboard,
  Users,
  UserRound,
  Building2,
  Wallet,
  Wrench,
  FileText,
  CalendarDays,
  LogOut,
  MessagesSquare,
  Settings,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { puedeVerModulo, tienePermiso } from "@/lib/permisos";
import logoUrl from "@/lib/logo";

// Ítems del menú (estilo exacto del dashboard). Cada uno declara el permiso
// (módulo) necesario para VERLO; se filtran según el rol del usuario (RBAC).
interface ItemMenu {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  modulo?: string;
}
const items: ItemMenu[] = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard, end: true, modulo: "dashboard" as const },
  { label: "Usuarios", path: "/dashboard/usuarios", icon: Users, modulo: "usuarios" as const },
  { label: "Residentes", path: "/dashboard/residentes", icon: UserRound, modulo: "residentes" as const },
  { label: "Propiedades", path: "/dashboard/propiedades", icon: Building2, modulo: "propiedades" as const },
  { label: "Finanzas", path: "/dashboard/finanzas", icon: Wallet, modulo: "finanzas" as const },
  { label: "Mantenimiento", path: "/dashboard/mantenimiento", icon: Wrench, modulo: "mantenimiento" as const },
  { label: "Documentos", path: "/dashboard/documentos", icon: FileText, modulo: "documentos" as const },
  { label: "Eventos", path: "/dashboard/eventos", icon: CalendarDays, modulo: "eventos" as const },
];

export default function Sidebar({ onNavigate }: { onNavigate?: () => void } = {}) {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();

  // Solo se muestran los módulos para los que el rol tiene el permiso <modulo>.ver.
  const itemsVisibles: ItemMenu[] = items.filter((i) => i.modulo && puedeVerModulo(usuario, i.modulo));

  // El historial de chat solo es visible si el rol tiene el permiso chat.usar.
  if (tienePermiso(usuario, "chat.usar")) {
    itemsVisibles.push({ label: "Chat asistente", path: "/dashboard/chat", icon: MessagesSquare });
  }
  // Configuración solo es visible si el rol puede verla (config.ver).
  if (tienePermiso(usuario, "config.ver")) {
    itemsVisibles.push({ label: "Configuración", path: "/dashboard/configuracion", icon: Settings });
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
    <aside className="w-[250px] bg-dark-100 text-white flex flex-col min-h-screen lg:min-h-full lg:sticky lg:top-0 lg:h-screen lg:max-h-screen">
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
            <span>{item.label}</span>
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
