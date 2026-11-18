import { useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import LandingPage from "@/pages/LandingPage";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import RegistroAdmin from "@/pages/RegistroAdmin";
import Recuperar from "@/pages/Recuperar";
import RestablecerPassword from "@/pages/RestablecerPassword";
import VerificarCorreo from "@/pages/VerificarCorreo";
import VerificarCodigo from "@/pages/VerificarCodigo";
import DashboardLayout from "@/components/layout/DashboardLayout";
import Inicio from "@/pages/Dashboard/Inicio";
import Conjuntos from "@/pages/Dashboard/Conjuntos";
import { useConjunto } from "@/context/ConjuntoContext";
import { setConjuntoActivo } from "@/lib/api";
import Usuarios from "@/pages/Dashboard/Usuarios";
import Residentes from "@/pages/Dashboard/Residentes";
import Propiedades from "@/pages/Dashboard/Propiedades";
import Finanzas from "@/pages/Dashboard/Finanzas";
import Mantenimiento from "@/pages/Dashboard/Mantenimiento";
import Documentos from "@/pages/Dashboard/Documentos";
import Eventos from "@/pages/Dashboard/Eventos";
import ChatSesiones from "@/pages/Dashboard/ChatSesiones";
import Configuracion from "@/pages/Dashboard/Configuracion";
// Módulos de las historias UH-01 a UH-32
import PQRS from "@/pages/Dashboard/PQRS";
import Reservas from "@/pages/Dashboard/Reservas";
import Comunicados from "@/pages/Dashboard/Comunicados";
import Visitantes from "@/pages/Dashboard/Visitantes";
import Pagos from "@/pages/Dashboard/Pagos";
import Votaciones from "@/pages/Dashboard/Votaciones";
import Aprobaciones from "@/pages/Dashboard/Aprobaciones";
import Auditoria from "@/pages/Dashboard/Auditoria";
import Perfil from "@/pages/Dashboard/Perfil";
import Consejo from "@/pages/Dashboard/Consejo";
import Mensajes from "@/pages/Dashboard/Mensajes";
import { useAuth } from "@/context/AuthContext";
import { puedeVerModulo, tienePermiso } from "@/lib/permisos";
import SinPermiso from "@/pages/Dashboard/SinPermiso";
import CookieBanner from "./components/CookieBanner";
import TerminosCondiciones from "@/pages/TerminosCondiciones";



// Ruta protegida: exige sesión iniciada y conserva el destino (p. ej. al abrir
// "Ver en la aplicación" desde un correo de notificación).
function Protegida({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const location = useLocation();
  if (!token) {
    const destino = `${location.pathname}${location.search}`;
    const qs = destino && destino !== "/dashboard" ? `?next=${encodeURIComponent(destino)}` : "";
    return <Navigate to={`/login${qs}`} replace />;
  }
  return <>{children}</>;
}

/** Exige un permiso concreto; si falta, muestra la página "Sin permiso"
 *  (en vez de redirigir en silencio, para que el usuario entienda qué pasó). */
function RequierePermiso({ codigo, children }: { codigo: string; children: React.ReactNode }) {
  const { usuario } = useAuth();
  if (!tienePermiso(usuario, codigo)) return <SinPermiso permiso={codigo} />;
  return <>{children}</>;
}

/** Ruta protegida + permiso de módulo (`<modulo>.ver`). */
function ConPermiso({ modulo, children }: { modulo: string; children: React.ReactNode }) {
  const { usuario } = useAuth();
  if (!puedeVerModulo(usuario, modulo)) return <SinPermiso permiso={`${modulo}.ver`} />;
  return <>{children}</>;
}

/**
 * Ruta inicial del dashboard:
 * · Si el usuario administra VARIOS conjuntos → Panel Multi-Administrador
 *   (selector de conjuntos, como en la maqueta).
 * · Si sólo tiene uno → entra directo al Inicio de ese conjunto, que es el
 *   comportamiento que ya tenía la app.
 */
function RutaInicial() {
  const { conjuntos, cargando } = useConjunto();
  if (cargando && !conjuntos.length) {
    return <div className="h-64 animate-pulse rounded-3xl bg-gray-100" />;
  }
  if (conjuntos.length === 1) return <Navigate to="/dashboard/inicio" replace />;
  return <Conjuntos />;
}

export default function App() {
  const location = useLocation();

  // Si el enlace de un correo trae `?conjunto=ID`, selecciona automáticamente
  // ese conjunto al abrir la aplicación en el navegador.
  useEffect(() => {
    const cidParam = new URLSearchParams(location.search).get("conjunto");
    const cid = cidParam ? Number(cidParam) : NaN;
    if (Number.isInteger(cid) && cid > 0) {
      setConjuntoActivo(cid);
    }
  }, [location.search]);

  return (
    <>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Rutas públicas */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/registro-administrador" element={<RegistroAdmin />} />
          <Route path="/recuperar" element={<Recuperar />} />
          <Route path="/restablecer/:token" element={<RestablecerPassword />} />
          <Route path="/verificar/:token" element={<VerificarCorreo />} />
          <Route path="/verificar-codigo" element={<VerificarCodigo />} />
          <Route path="/terminos-condiciones" element={<TerminosCondiciones />} />



          {/* Rutas protegidas del dashboard */}
          <Route
            path="/dashboard"
            element={
              <Protegida>
                <DashboardLayout />
              </Protegida>
            }
          >
            <Route index element={<ConPermiso modulo="dashboard"><RutaInicial /></ConPermiso>} />
            <Route path="inicio" element={<ConPermiso modulo="dashboard"><Inicio /></ConPermiso>} />
            <Route
              path="conjuntos"
              element={
                <RequierePermiso codigo="conjuntos.ver">
                  <Conjuntos />
                </RequierePermiso>
              }
            />
            <Route path="usuarios" element={<ConPermiso modulo="usuarios"><Usuarios /></ConPermiso>} />
            <Route path="residentes" element={<ConPermiso modulo="residentes"><Residentes /></ConPermiso>} />
            <Route path="propiedades" element={<ConPermiso modulo="propiedades"><Propiedades /></ConPermiso>} />
            <Route path="finanzas" element={<ConPermiso modulo="finanzas"><Finanzas /></ConPermiso>} />
            <Route path="mantenimiento" element={<ConPermiso modulo="mantenimiento"><Mantenimiento /></ConPermiso>} />
            <Route path="documentos" element={<ConPermiso modulo="documentos"><Documentos /></ConPermiso>} />
            <Route path="eventos" element={<ConPermiso modulo="eventos"><Eventos /></ConPermiso>} />
            <Route path="chat" element={<RequierePermiso codigo="chat.usar"><ChatSesiones /></RequierePermiso>} />
            <Route path="configuracion" element={<ConPermiso modulo="config"><Configuracion /></ConPermiso>} />
            {/* Historias de usuario UH-09 a UH-32 */}
            <Route path="pqrs" element={<ConPermiso modulo="pqrs"><PQRS /></ConPermiso>} />
            <Route path="reservas" element={<ConPermiso modulo="reservas"><Reservas /></ConPermiso>} />
            <Route path="comunicados" element={<ConPermiso modulo="comunicados"><Comunicados /></ConPermiso>} />
            <Route path="visitantes" element={<ConPermiso modulo="visitantes"><Visitantes /></ConPermiso>} />
            <Route path="pagos" element={<ConPermiso modulo="pagos"><Pagos /></ConPermiso>} />
            <Route path="votaciones" element={<ConPermiso modulo="votaciones"><Votaciones /></ConPermiso>} />
            <Route path="aprobaciones" element={<ConPermiso modulo="aprobaciones"><Aprobaciones /></ConPermiso>} />
            <Route path="auditoria" element={<RequierePermiso codigo="auditoria.ver"><Auditoria /></RequierePermiso>} />
            <Route path="consejo" element={<RequierePermiso codigo="reportes.ver"><Consejo /></RequierePermiso>} />
            <Route path="perfil" element={<RequierePermiso codigo="perfil.ver"><Perfil /></RequierePermiso>} />
            <Route path="mensajes" element={<ConPermiso modulo="mensajes"><Mensajes /></ConPermiso>} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

      </AnimatePresence>

      <CookieBanner />

    </>
    
  );
}
