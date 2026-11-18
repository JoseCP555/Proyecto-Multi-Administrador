import { NavLink } from "react-router-dom";
import {
  Home,
  MessageCircleMore,
  MessageSquareWarning,
  Wallet,
  CreditCard,
  CalendarDays,
  Menu,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { puedeVerModulo } from "@/lib/permisos";
import { useMensajesNoLeidos } from "@/hooks/useMensajesNoLeidos";

interface TabItem {
  label: string;
  path: string;
  icon: typeof Home;
  badge?: number;
}

/**
 * Barra de navegación inferior exclusiva para celulares (`md:hidden`).
 * Respeta el área segura de iPhone (`env(safe-area-inset-bottom)`) y los
 * permisos RBAC de cada rol.
 */
export default function MobileBottomNav({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { usuario } = useAuth();
  const { noLeidos } = useMensajesNoLeidos();

  const tabs: TabItem[] = [];

  if (puedeVerModulo(usuario, "dashboard")) {
    tabs.push({ label: "Inicio", path: "/dashboard/inicio", icon: Home });
  }
  if (puedeVerModulo(usuario, "mensajes")) {
    tabs.push({
      label: "Mensajes",
      path: "/dashboard/mensajes",
      icon: MessageCircleMore,
      badge: noLeidos,
    });
  }
  if (puedeVerModulo(usuario, "pqrs")) {
    tabs.push({ label: "PQRS", path: "/dashboard/pqrs", icon: MessageSquareWarning });
  } else if (puedeVerModulo(usuario, "eventos")) {
    tabs.push({ label: "Eventos", path: "/dashboard/eventos", icon: CalendarDays });
  }

  if (puedeVerModulo(usuario, "finanzas")) {
    tabs.push({ label: "Finanzas", path: "/dashboard/finanzas", icon: Wallet });
  } else if (puedeVerModulo(usuario, "pagos")) {
    tabs.push({ label: "Pagos", path: "/dashboard/pagos", icon: CreditCard });
  } else if (puedeVerModulo(usuario, "eventos") && !tabs.some((t) => t.path === "/dashboard/eventos")) {
    tabs.push({ label: "Eventos", path: "/dashboard/eventos", icon: CalendarDays });
  }

  const visibles = tabs.slice(0, 4);

  return (
    <nav
      aria-label="Navegación móvil"
      className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur-md border-t border-gray-200 shadow-[0_-4px_20px_rgba(15,23,42,0.06)] pb-[env(safe-area-inset-bottom)]"
    >
      <div className="flex items-stretch justify-around h-16 px-1">
        {visibles.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              `relative flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${
                isActive ? "text-primary-600" : "text-gray-500 active:text-primary-600"
              }`
            }
          >
            <span className="relative">
              <tab.icon className="w-5 h-5" />
              {!!tab.badge && tab.badge > 0 && (
                <span className="absolute -top-1.5 -right-2.5 min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[9px] font-bold flex items-center justify-center">
                  {tab.badge > 99 ? "99+" : tab.badge}
                </span>
              )}
            </span>
            <span className="truncate max-w-[72px]">{tab.label}</span>
          </NavLink>
        ))}

        <button
          type="button"
          onClick={onOpenMenu}
          className="flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium text-gray-500 active:text-primary-600"
          aria-label="Abrir menú completo"
        >
          <Menu className="w-5 h-5" />
          <span>Menú</span>
        </button>
      </div>
    </nav>
  );
}
