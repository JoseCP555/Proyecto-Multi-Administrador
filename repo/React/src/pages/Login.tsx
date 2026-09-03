import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  loginWithAccount,
  GOOGLE_ACCOUNTS,
  APPLE_ACCOUNTS,
  saveAuthSession
} from '../auth'
import AccountPicker from '../components/AccountPicker'
import API_URL from '../api'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [picker, setPicker] = useState<'google' | 'apple' | null>(null)

  const handleLogin = async () => {

    if (!email || !password) {
      setError("Por favor completa todos los campos.")
      return
    }

    try {

      const response = await fetch(
        `${API_URL}/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            correo: email,
            password: password,
          }),
        }
      )

      const data = await response.json()

      if (!data.ok) {
        setError(data.mensaje)
        return
      }

      saveAuthSession(data.usuario, data.access_token)

      setError('')
      navigate('/inicio')



    } catch (error) {

      console.error(error)

      setError("No fue posible conectar con el servidor.")

    }

  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleLogin()
  }

  const handleForgot = async () => {
    if (!email) {
      setError("Escribe tu correo primero.")
      return
    }

    try {
      const response = await fetch(
        `${API_URL}/recuperar-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            correo: email,
          }),
        }
      )

      const data = await response.json()

      // Si el correo SE ENVIO a Gmail (enviado=true), avisamos al usuario
      // que revise su bandeja.
      if (data.correo_enviado === true) {
        alert("Te enviamos un correo a " + email + ". Revisa tu bandeja de entrada (y la carpeta de spam).")
      } else if (data.link_debug) {
        // El backend genero el link pero Gmail fallo. Mostramos el error y el link.
        const errorInfo = data.error_smtp ? "\n\nError SMTP: " + data.error_smtp : ""
        const abrir = window.confirm(
          "Gmail rechazo el envio del correo (revisar configuracion SMTP)." + errorInfo +
          "\n\nComo respaldo, puedes abrir este link directamente para cambiar tu contrasena:\n\n" +
          data.link_debug + "\n\nDeseas abrirlo ahora?"
        )
        if (abrir) {
          window.location.href = data.link_debug
        }
      } else {
        alert(data.mensaje || "Si el correo existe, se enviara un enlace.")
      }

      setError("")
    } catch (err) {
      console.error(err)
      setError("No fue posible enviar el correo.")
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
      <div className="login-top-bar">Multi-Admin</div>

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
          <div className="pwd-input-wrapper">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Ingresa tu contraseña"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              type="button"
              className="pwd-toggle-btn"
              onClick={() => setShowPassword(v => !v)}
              aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            >
              <i className={showPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'}></i>
            </button>
          </div>

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
