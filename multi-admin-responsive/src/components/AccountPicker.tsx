import './AccountPicker.css'

interface Account {
  name: string
  email: string
  avatarColor: string
}

interface AccountPickerProps {
  provider: 'google' | 'apple'
  accounts: Account[]
  onSelect: (account: Account) => void
  onClose: () => void
}

export default function AccountPicker({ provider, accounts, onSelect, onClose }: AccountPickerProps) {
  const title = provider === 'google' ? 'Elige una cuenta' : 'Iniciar sesión con Apple ID'
  const subtitle = provider === 'google'
    ? 'para continuar a Multi-Administrador'
    : 'Selecciona el Apple ID que deseas usar'

  return (
    <div className="account-picker-overlay" onClick={onClose}>
      <div className="account-picker-modal" onClick={e => e.stopPropagation()}>
        <div className="account-picker-header">
          {provider === 'google' ? (
            <i className="fa-brands fa-google account-picker-icon google"></i>
          ) : (
            <i className="fa-brands fa-apple account-picker-icon apple"></i>
          )}
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>

        <div className="account-picker-list">
          {accounts.map(acc => (
            <button
              key={acc.email}
              className="account-picker-item"
              onClick={() => onSelect(acc)}
            >
              <div className="account-avatar" style={{ background: acc.avatarColor }}>
                {acc.name.charAt(0).toUpperCase()}
              </div>
              <div className="account-info">
                <span className="account-name">{acc.name}</span>
                <span className="account-email">{acc.email}</span>
              </div>
            </button>
          ))}

          <button className="account-picker-item add-account" onClick={onClose}>
            <div className="account-avatar add-icon">
              <i className="fa-solid fa-plus"></i>
            </div>
            <div className="account-info">
              <span className="account-name">Usar otra cuenta</span>
            </div>
          </button>
        </div>

        <button className="account-picker-cancel" onClick={onClose}>Cancelar</button>
      </div>
    </div>
  )
}
