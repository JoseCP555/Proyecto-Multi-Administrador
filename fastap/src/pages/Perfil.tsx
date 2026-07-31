import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { getSession } from '../auth'
import './Perfil.css'

const settingsItems = [
  'Información personal','Optimización','Privacidad',
  'Rendimiento','Accesibilidad','Monitoreo','Registros DNS','Ajustes'
]

export default function Perfil() {
  const [active, setActive] = useState('Ajustes')
  const session = getSession()

  const reset = () => alert('Configuración restablecida')

  return (
    <DashboardLayout>
      <div className="perfil-header">
        <div>
          <h2>Hola, {session?.name || 'Administrador'}</h2>
          <p className="perfil-sub">Configuración de perfil y ajustes</p>
        </div>
        <div className="perfil-filters">
          <select><option>Copropiedad</option></select>
          <select><option>Conjuntos</option></select>
          <button className="design-btn">Diseño de Página</button>
        </div>
      </div>

      <div className="perfil-grid">
        {settingsItems.map(item => (
          <div
            key={item}
            className={`setting-box ${active === item ? 'active-setting' : ''}`}
            onClick={() => setActive(item)}
          >
            {item}
            <i className="fa-solid fa-angle-down"></i>
          </div>
        ))}
      </div>

      <div className="reset-container">
        <button className="reset-btn" onClick={reset}>
          <i className="fa-solid fa-rotate-left"></i> Restablecimiento
        </button>
      </div>
    </DashboardLayout>
  )
}
