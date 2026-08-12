import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AccountPicker from '../components/AccountPicker'
import {loginWithAccount,GOOGLE_ACCOUNTS,APPLE_ACCOUNTS} from "../auth"
import API_URL from '../api'
import './Bienvenidos.css'

// Detecta secuencias consecutivas (ej: "abc", "123", "xyz")
function hasConsecutiveChars(str: string): boolean {
  for (let i = 0; i < str.length - 2; i++) {
    const a = str.charCodeAt(i)
    const b = str.charCodeAt(i + 1)
    const c = str.charCodeAt(i + 2)
    // Ascendente (abc, 123) o descendente (cba, 321)
    if ((b === a + 1 && c === b + 1) || (b === a - 1 && c === b - 1)) {
      return true
    }
  }
  return false
}

interface PasswordCheck {
  label: string
  ok: boolean
}

function evaluatePassword(pwd: string): { checks: PasswordCheck[]; score: number; label: string; color: string } {
  const checks: PasswordCheck[] = [
    { label: 'Mínimo 9 caracteres',          ok: pwd.length >= 9 },
    { label: 'Al menos una letra mayúscula',  ok: /[A-Z]/.test(pwd) },
    { label: 'Al menos un carácter especial', ok: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pwd) },
    { label: 'Sin secuencias consecutivas',   ok: !hasConsecutiveChars(pwd) },
  ]

  const passed = checks.filter(c => c.ok).length
  const score = passed / checks.length

  let label = ''
  let color = ''
  if (pwd.length === 0) { label = ''; color = '' }
  else if (score <= 0.25) { label = 'Muy débil'; color = '#ef4444' }
  else if (score <= 0.5)  { label = 'Débil';     color = '#f97316' }
  else if (score <= 0.75) { label = 'Regular';   color = '#eab308' }
  else                    { label = 'Segura';     color = '#22c55e' }

  return { checks, score, label, color }
}

export default function Bienvenidos() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [picker, setPicker] = useState<'google' | 'apple' | null>(null)
  const [showChecks, setShowChecks] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const pwdEval = evaluatePassword(password)

  const handleRegister = async () => {
    setError("")
    setSuccess("")

    if (!name || !email || !password || !confirmPassword) {
      setError("Por favor completa todos los campos.")
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Ingresa un correo electrónico válido.")
      return
    }

    const failedChecks = pwdEval.checks.filter(c => !c.ok)

    if (failedChecks.length > 0) {
      setError(
        "La contraseña no es segura: " +
        failedChecks.map(c => c.label.toLowerCase()).join(", ") +
        "."
      )
      return
    }

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.")
      return
    }

    try {
      const response = await fetch(`${API_URL}/crear_usuarios`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre: name,
          telefono: "",
          correo: email,
          contrasena_hash: password,
          id_rol: 1,
          activo: true,
          id_copropiedad: 2,
        }),
      })

      if (!response.ok) {
        const error = await response.text()
        console.error(error)
        throw new Error(error)
      }

      setError("")
      setSuccess("¡Cuenta creada con éxito!")

      setTimeout(() => {
        navigate("/login")
      }, 1200)

    } catch (error) {
      console.error(error)
      setError("Error al conectar con el servidor.")
    }
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

          {/* Campo contraseña con indicador */}
          <div className="pwd-input-wrapper">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Contraseña"
              value={password}
              onChange={e => { setPassword(e.target.value); setShowChecks(true) }}
              onFocus={() => setShowChecks(true)}
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

          {/* Barra de fortaleza + etiqueta */}
          {showChecks && password.length > 0 && (
            <div className="pwd-strength-wrapper">
              <div className="pwd-strength-bar-bg">
                <div
                  className="pwd-strength-bar-fill"
                  style={{
                    width: `${pwdEval.score * 100}%`,
                    background: pwdEval.color,
                  }}
                />
              </div>
              <span className="pwd-strength-label" style={{ color: pwdEval.color }}>
                {pwdEval.label}
              </span>

              {/* Lista de requisitos */}
              <ul className="pwd-checks">
                {pwdEval.checks.map((c, i) => (
                  <li key={i} className={c.ok ? 'pwd-check-ok' : 'pwd-check-fail'}>
                    {c.ok ? '✔' : '✖'} {c.label}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="pwd-input-wrapper">
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Confirmar contraseña"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              type="button"
              className="pwd-toggle-btn"
              onClick={() => setShowConfirmPassword(v => !v)}
              aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            >
              <i className={showConfirmPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'}></i>
            </button>
          </div>

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
