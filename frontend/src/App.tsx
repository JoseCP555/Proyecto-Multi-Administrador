import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import LandingPage from "@/pages/LandingPage";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Recuperar from "@/pages/Recuperar";
import RestablecerPassword from "@/pages/RestablecerPassword";
import VerificarCorreo from "@/pages/VerificarCorreo";
import VerificarCodigo from "@/pages/VerificarCodigo";
import DashboardLayout from "@/components/layout/DashboardLayout";
import Inicio from "@/pages/Dashboard/Inicio";
import Usuarios from "@/pages/Dashboard/Usuarios";
import Residentes from "@/pages/Dashboard/Residentes";
import Propiedades from "@/pages/Dashboard/Propiedades";
import Finanzas from "@/pages/Dashboard/Finanzas";
import Mantenimiento from "@/pages/Dashboard/Mantenimiento";
import Documentos from "@/pages/Dashboard/Documentos";
import Eventos from "@/pages/Dashboard/Eventos";
import ChatSesiones from "@/pages/Dashboard/ChatSesiones";
import Configuracion from "@/pages/Dashboard/Configuracion";
import { useAuth } from "@/context/AuthContext";
import { puedeVerModulo, tienePermiso } from "@/lib/permisos";
import SinPermiso from "@/pages/Dashboard/SinPermiso";
import CookieBanner from "./components/CookieBanner";
import TerminosCondiciones from "@/pages/TerminosCondiciones";



// Ruta protegida: exige sesión iniciada.
function Protegida({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
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

export default function App() {
  const location = useLocation();

  return (
    <>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Rutas públicas */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
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
            <Route index element={<ConPermiso modulo="dashboard"><Inicio /></ConPermiso>} />
            <Route path="usuarios" element={<ConPermiso modulo="usuarios"><Usuarios /></ConPermiso>} />
            <Route path="residentes" element={<ConPermiso modulo="residentes"><Residentes /></ConPermiso>} />
            <Route path="propiedades" element={<ConPermiso modulo="propiedades"><Propiedades /></ConPermiso>} />
            <Route path="finanzas" element={<ConPermiso modulo="finanzas"><Finanzas /></ConPermiso>} />
            <Route path="mantenimiento" element={<ConPermiso modulo="mantenimiento"><Mantenimiento /></ConPermiso>} />
            <Route path="documentos" element={<ConPermiso modulo="documentos"><Documentos /></ConPermiso>} />
            <Route path="eventos" element={<ConPermiso modulo="eventos"><Eventos /></ConPermiso>} />
            <Route path="chat" element={<RequierePermiso codigo="chat.usar"><ChatSesiones /></RequierePermiso>} />
            <Route path="configuracion" element={<ConPermiso modulo="config"><Configuracion /></ConPermiso>} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

      </AnimatePresence>

      <CookieBanner />

    </>
    
  );
}
