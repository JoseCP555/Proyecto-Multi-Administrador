import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser, loginWithAccount, GOOGLE_ACCOUNTS, APPLE_ACCOUNTS } from '../auth'
import AccountPicker from '../components/AccountPicker'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [picker, setPicker] = useState<'google' | 'apple' | null>(null)

  const handleLogin = () => {
    if (!email || !password) {
      setError('Por favor completa todos los campos.')
      return
    }

    const result = loginUser(email, password)
    if (!result.ok) {
      setError(result.error || 'El correo o la contraseña son incorrectos.')
      return
    }

    setError('')
    navigate('/inicio')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleLogin()
  }

  const handleForgot = () => {
    if (!email) {
      setError('Escribe tu correo primero.')
    } else {
      setError('')
      alert(`Se envió un enlace de recuperación a: ${email}`)
    }
  }

  const handleAccountSelected = (account: { name: string; email: string }) => {
    if (!picker) return
    loginWithAccount(picker, account.name, account.email)
    setPicker(null)
    navigate('/inicio')
  }

  return (
    <div className="login-root">
      <div className="login-top-bar">Mul-Admi</div>

      <div className="login-header">
        <h1>Bienvenidos</h1>
        <h2>Multi-Administrador</h2>
      </div>

      <div className="login-container">
        <div className="login-form">
          <button className="google-login-btn" onClick={() => setPicker('google')}>
            <i className="fa-brands fa-google"></i> Entrar con Google
          </button>

          <button className="apple-login-btn" onClick={() => setPicker('apple')}>
            <i className="fa-brands fa-apple"></i> Entrar con Apple
          </button>

          <div className="login-divider"><span>o continúa con correo</span></div>

          {error && <div className="login-error">{error}</div>}

          <label>Correo electrónico</label>
          <input
            type="email"
            placeholder="Ingresa tu correo"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <label>Contraseña</label>
          <input
            type="password"
            placeholder="Ingresa tu contraseña"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyPress={handleKeyPress}
          />

          <span className="forgot-link" onClick={handleForgot}>
            ¿Olvidaste tu contraseña?
          </span>

          <button className="login-btn" onClick={handleLogin}>
            INICIAR SESIÓN
          </button>

          <p className="register-link">
            ¿No tienes cuenta?{' '}
            <span onClick={() => navigate('/bienvenidos')}>Regístrate</span>
          </p>
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
