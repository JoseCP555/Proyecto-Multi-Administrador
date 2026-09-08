import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import ChatWidget from "./ChatWidget";

/**
 * Shell del dashboard: fondo degradado lila, contenedor blanco con esquinas
 * muy redondeadas, sidebar negra fija a la izquierda y contenido a la derecha.
 */
export default function DashboardLayout() {
  const [menuAbierto, setMenuAbierto] = useState(false);

  return (
    <div className="min-h-screen p-3 sm:p-5 lg:p-7">
      <div className="mx-auto max-w-[1600px] min-h-[calc(100vh-3.5rem)] bg-white rounded-4xl shadow-shell overflow-hidden flex">
        {/* Sidebar escritorio */}
        <div className="hidden lg:flex shrink-0 self-stretch">
          <Sidebar />
        </div>

        {/* Sidebar móvil (overlay) */}
        {menuAbierto && (
          <div className="lg:hidden fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/40" onClick={() => setMenuAbierto(false)} />
            <div className="absolute left-0 top-0 bottom-0 z-10">
              <Sidebar onNavigate={() => setMenuAbierto(false)} />
            </div>
          </div>
        )}

        {/* Contenido */}
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          <Topbar onToggleSidebar={() => setMenuAbierto(true)} />
          <main className="flex-1 px-4 sm:px-6 lg:px-8 pb-8">
            <Outlet />
          </main>
        </div>
      </div>

      {/* Widget de chatbot */}
      <ChatWidget />
    </div>
  );
}
