import { useNavigate, useLocation } from 'react-router-dom'
import './Sidebar.css'

const menuItems = [
  { label: 'Inicio', path: '/inicio', icon: 'fa-solid fa-house-chimney' },
  { label: 'Propiedades', path: '/propiedades', icon: 'fa-solid fa-house' },
  { label: 'Residentes', path: '/residentes', icon: 'fa-solid fa-users' },
  { label: 'Finanzas', path: '/finanzas', icon: 'fa-solid fa-dollar-sign' },
  { label: 'Mantenimiento', path: '/mantenimiento', icon: 'fa-solid fa-wrench' },
  { label: 'Documentos', path: '/documentos', icon: 'fa-solid fa-folder' },
  { label: 'Reportes', path: '/reportes', icon: 'fa-solid fa-chart-column' },
  { label: 'Configuración', path: '/configuracion', icon: 'fa-solid fa-gear' },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleNav = (path: string) => {
    navigate(path)
    onClose()
  }

  return (
    <>
      {/* Overlay for mobile */}
      {open && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar${open ? ' sidebar-open' : ''}`}>
        <div>
          <div className="sidebar-logo-wrap">
            <img
              src="https://plain-enam-prod-public.komododecks.com/202606/15/g3zWGd73sqvsxskJFMJ1/image.png"
              alt="Multi-Administrador logo"
              className="sidebar-logo-img"
            />
          </div>
          <div className="sidebar-brand">Multi-Administrador</div>
          <div className="menu-label">MENU</div>
          <nav className="sidebar-menu">
            {menuItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path)
              return (
                <button
                  key={item.path}
                  className={`sidebar-btn ${isActive ? 'active' : ''}`}
                  onClick={() => handleNav(item.path)}
                >
                  <span>
                    <i className={item.icon}></i>
                    {item.label}
                  </span>
                  <i className="fa-solid fa-angle-down chevron"></i>
                </button>
              )
            })}
          </nav>
        </div>
        <div className="sidebar-footer">
          <p><i className="fa-solid fa-headset"></i> Soporte Técnico</p>
          <p><i className="fa-regular fa-circle-question"></i> Centro de Ayuda</p>
        </div>
      </aside>
    </>
  )
}
