import { Routes, Route, Navigate } from 'react-router-dom'
import Bienvenidos from './pages/Bienvenidos'
import Login from './pages/Login'
import Inicio from './pages/Inicio'
import Propiedades from './pages/Propiedades'
import Residentes from './pages/Residentes'
import Finanzas from './pages/Finanzas'
import FinanzasCopropiedades from './pages/FinanzasCopropiedades'
import Mantenimiento from './pages/Mantenimiento'
import Documentos from './pages/Documentos'
import Actas from './pages/Actas'
import Reportes from './pages/Reportes'
import Perfil from './pages/Perfil'
import Configuracion from './pages/Configuracion'
import { isAuthenticated } from './auth'
import RestablecerPassword from './pages/RestablecerPassword'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/bienvenidos" element={<Bienvenidos />} />
      <Route path="/login" element={<Login />} />
      <Route path="/restablecer/:token" element={<RestablecerPassword />} />
      <Route path="/inicio" element={<ProtectedRoute><Inicio /></ProtectedRoute>} />
      <Route path="/propiedades" element={<ProtectedRoute><Propiedades /></ProtectedRoute>} />
      <Route path="/residentes" element={<ProtectedRoute><Residentes /></ProtectedRoute>} />
      <Route path="/finanzas" element={<ProtectedRoute><Finanzas /></ProtectedRoute>} />
      <Route path="/finanzas/copropiedades" element={<ProtectedRoute><FinanzasCopropiedades /></ProtectedRoute>} />
      <Route path="/mantenimiento" element={<ProtectedRoute><Mantenimiento /></ProtectedRoute>} />
      <Route path="/documentos" element={<ProtectedRoute><Documentos /></ProtectedRoute>} />
      <Route path="/documentos/actas" element={<ProtectedRoute><Actas /></ProtectedRoute>} />
      <Route path="/reportes" element={<ProtectedRoute><Reportes /></ProtectedRoute>} />
      <Route path="/perfil" element={<ProtectedRoute><Perfil /></ProtectedRoute>} />
      <Route path="/configuracion" element={<ProtectedRoute><Configuracion /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
