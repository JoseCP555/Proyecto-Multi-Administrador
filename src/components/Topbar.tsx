import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { logout } from '../auth'
import NotificationsPanel, { PanelItem } from './NotificationsPanel'
import './Topbar.css'

interface TopbarProps {
  onSearch?: (val: string) => void
  onMenuToggle?: () => void
}

const initialNotifications: PanelItem[] = [
  { id: 1, title: 'Pago recibido', description: 'El apto 302 registró el pago de administración.', time: 'Hace 10 min', icon: 'fa-solid fa-dollar-sign', read: false },
  { id: 2, title: 'Mantenimiento programado', description: 'Revisión del ascensor torre A el viernes.', time: 'Hace 1 hora', icon: 'fa-solid fa-wrench', read: false },
  { id: 3, title: 'Nuevo documento', description: 'Se subió el acta de la última reunión.', time: 'Hace 3 horas', icon: 'fa-solid fa-file', read: false },
  { id: 4, title: 'Solicitud de residente', description: 'El apto 105 reportó una falla en la luz del pasillo.', time: 'Ayer', icon: 'fa-solid fa-lightbulb', read: true },
]

const initialEvents: PanelItem[] = [
  { id: 1, title: 'Reunión de propietarios', description: 'Salón comunal, 6:00 p.m.', time: 'Hoy', icon: 'fa-solid fa-people-group', read: false },
  { id: 2, title: 'Revisión de mantenimiento', description: 'Ascensor torre A', time: 'Viernes', icon: 'fa-solid fa-wrench', read: false },
  { id: 3, title: 'Vencimiento de cuotas', description: 'Fecha límite de pago mensual', time: '30 de junio', icon: 'fa-solid fa-calendar-day', read: true },
]

const initialMessages: PanelItem[] = [
  { id: 1, title: 'María Pérez', description: '¿Podrían confirmar el horario de la reunión?', time: 'Hace 5 min', icon: 'fa-solid fa-user', read: false },
  { id: 2, title: 'Carlos Gómez', description: 'Gracias por la respuesta rápida.', time: 'Hace 2 horas', icon: 'fa-solid fa-user', read: false },
  { id: 3, title: 'Soporte técnico', description: 'Su ticket #245 ha sido resuelto.', time: 'Ayer', icon: 'fa-solid fa-headset', read: true },
]

export default function Topbar({ onSearch, onMenuToggle }: TopbarProps) {
  const navigate = useNavigate()
  const [openPanel, setOpenPanel] = useState<'calendar' | 'notifications' | 'messages' | null>(null)
  const [notifications, setNotifications] = useState(initialNotifications)
  const [events, setEvents] = useState(initialEvents)
  const [messages, setMessages] = useState(initialMessages)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const togglePanel = (panel: 'calendar' | 'notifications' | 'messages') => {
    setOpenPanel(prev => (prev === panel ? null : panel))
  }

  const markAllRead = (list: PanelItem[], setList: (items: PanelItem[]) => void) => {
    setList(list.map(item => ({ ...item, read: true })))
  }

  const markOneRead = (list: PanelItem[], setList: (items: PanelItem[]) => void, item: PanelItem) => {
    setList(list.map(i => (i.id === item.id ? { ...i, read: true } : i)))
  }

  const unreadCount = (list: PanelItem[]) => list.filter(i => !i.read).length

  return (
    <div className="topbar">
      {/* Hamburger button — visible only on mobile */}
      <button className="topbar-hamburger" onClick={onMenuToggle} aria-label="Abrir menú">
        <i className="fa-solid fa-bars"></i>
      </button>

      <div className="topbar-search">
        <i className="fa-solid fa-magnifying-glass"></i>
        <input
          type="text"
          placeholder="Buscar"
          onChange={e => onSearch?.(e.target.value)}
        />
      </div>

      <div className="topbar-icons">
        <div className="icon-wrap" onClick={() => togglePanel('calendar')}>
          <i className="fa-regular fa-calendar" title="Calendario"></i>
          {unreadCount(events) > 0 && <span className="icon-badge">{unreadCount(events)}</span>}
          {openPanel === 'calendar' && (
            <NotificationsPanel
              title="Próximos eventos"
              items={events}
              emptyText="No tienes eventos próximos"
              onClose={() => setOpenPanel(null)}
              onMarkAllRead={() => markAllRead(events, setEvents)}
              onItemClick={item => markOneRead(events, setEvents, item)}
            />
          )}
        </div>

        <div className="icon-wrap" onClick={() => togglePanel('notifications')}>
          <i className="fa-solid fa-bell" title="Notificaciones"></i>
          {unreadCount(notifications) > 0 && <span className="icon-badge">{unreadCount(notifications)}</span>}
          {openPanel === 'notifications' && (
            <NotificationsPanel
              title="Notificaciones"
              items={notifications}
              emptyText="No tienes notificaciones"
              onClose={() => setOpenPanel(null)}
              onMarkAllRead={() => markAllRead(notifications, setNotifications)}
              onItemClick={item => markOneRead(notifications, setNotifications, item)}
            />
          )}
        </div>

        <div className="icon-wrap" onClick={() => togglePanel('messages')}>
          <i className="fa-solid fa-message" title="Mensajes"></i>
          {unreadCount(messages) > 0 && <span className="icon-badge">{unreadCount(messages)}</span>}
          {openPanel === 'messages' && (
            <NotificationsPanel
              title="Mensajes"
              items={messages}
              emptyText="No tienes mensajes"
              onClose={() => setOpenPanel(null)}
              onMarkAllRead={() => markAllRead(messages, setMessages)}
              onItemClick={item => markOneRead(messages, setMessages, item)}
            />
          )}
        </div>

        <div className="topbar-sep"></div>
        <i
          className="fa-solid fa-user"
          title="Perfil"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/perfil')}
        ></i>
        <i
          className="fa-solid fa-arrow-right-from-bracket"
          title="Cerrar sesión"
          style={{ cursor: 'pointer' }}
          onClick={handleLogout}
        ></i>
      </div>
    </div>
  )
}
