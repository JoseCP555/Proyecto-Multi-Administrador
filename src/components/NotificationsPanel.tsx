import './NotificationsPanel.css'

export interface PanelItem {
  id: number
  title: string
  description: string
  time: string
  icon: string
  read: boolean
}

interface NotificationsPanelProps {
  title: string
  items: PanelItem[]
  emptyText: string
  onClose: () => void
  onMarkAllRead?: () => void
  onItemClick?: (item: PanelItem) => void
}

export default function NotificationsPanel({
  title,
  items,
  emptyText,
  onClose,
  onMarkAllRead,
  onItemClick,
}: NotificationsPanelProps) {
  return (
    <>
      <div className="panel-overlay" onClick={onClose}></div>
      <div className="notif-panel">
        <div className="notif-panel-header">
          <h4>{title}</h4>
          {onMarkAllRead && items.some(i => !i.read) && (
            <button className="notif-mark-read" onClick={onMarkAllRead}>
              Marcar todo como leído
            </button>
          )}
        </div>

        <div className="notif-panel-list">
          {items.length === 0 ? (
            <div className="notif-empty">{emptyText}</div>
          ) : (
            items.map(item => (
              <div
                key={item.id}
                className={`notif-item ${!item.read ? 'unread' : ''}`}
                onClick={() => onItemClick?.(item)}
              >
                <div className="notif-icon">
                  <i className={item.icon}></i>
                </div>
                <div className="notif-content">
                  <span className="notif-title">{item.title}</span>
                  <span className="notif-desc">{item.description}</span>
                  <span className="notif-time">{item.time}</span>
                </div>
                {!item.read && <div className="notif-dot"></div>}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}
