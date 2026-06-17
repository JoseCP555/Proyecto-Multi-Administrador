import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerUser, loginWithAccount, GOOGLE_ACCOUNTS, APPLE_ACCOUNTS } from '../auth'
import AccountPicker from '../components/AccountPicker'
import './Bienvenidos.css'

export default function Bienvenidos() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [picker, setPicker] = useState<'google' | 'apple' | null>(null)

  const handleRegister = () => {
    setSuccess('')

    if (!name || !email || !password || !confirmPassword) {
      setError('Por favor completa todos los campos.')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Ingresa un correo electrónico válido.')
      return
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.')
      return
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }

    const result = registerUser(name, email, password)
    if (!result.ok) {
      setError(result.error || 'No se pudo crear la cuenta.')
      return
    }

    setError('')
    setSuccess('¡Cuenta creada con éxito! Redirigiendo a iniciar sesión...')
    setTimeout(() => navigate('/login'), 1200)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRegister()
  }

  const handleAccountSelected = (account: { name: string; email: string }) => {
    if (!picker) return
    loginWithAccount(picker, account.name, account.email)
    setPicker(null)
    navigate('/inicio')
  }

  return (
    <div className="bienvenidos-root">
      <div className="bienvenidos-top">Mul-Admi</div>

      <div className="bienvenidos-header">
        <h1>Bienvenidos</h1>
        <h2>Multi-Administrador</h2>
      </div>

      <div className="bienvenidos-container">
        <div className="bienvenidos-form">
          {error && <div className="bienvenidos-error">{error}</div>}
          {success && <div className="bienvenidos-success">{success}</div>}

          <input
            type="text"
            placeholder="Nombre completo"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <input
            type="email"
            placeholder="Correo electrónico"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <input
            type="password"
            placeholder="Confirmar contraseña"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <button className="bienvenidos-btn primary-btn" onClick={handleRegister}>
            Registrarse
          </button>

          <button
            className="bienvenidos-btn"
            onClick={() => navigate('/login')}
          >
            ¿Ya tienes cuenta? Inicia sesión
          </button>

          <button className="bienvenidos-btn google-btn" onClick={() => setPicker('google')}>
            <i className="fa-brands fa-google"></i> Entrar con Google
          </button>

          <button className="bienvenidos-btn apple-btn" onClick={() => setPicker('apple')}>
            <i className="fa-brands fa-apple"></i> Entrar con Apple
          </button>
        </div>
      </div>

      {picker && (
        <AccountPicker
          provider={picker}
          accounts={picker === 'google' ? GOOGLE_ACCOUNTS : APPLE_ACCOUNTS}
          onSelect={handleAccountSelected}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  )
}
